"""Frozen enterprise-history pilot. Official Trace2Skill core, explicit neutral/event-bag adapters."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import asdict, is_dataclass
import argparse, hashlib, importlib.metadata, json, logging, os, re, shutil, subprocess, sys, threading, time, urllib.request, urllib.error
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
BASELINE = PROJECT / "research/baselines/Trace2Skill"
DEMO = PROJECT / "enginering/demo"
sys.path.insert(0, str(DEMO))
sys.path.insert(0, str(BASELINE / ".runtime/deps"))
sys.path.insert(0, str(BASELINE))
from skill_evolver.parallel_evolving_agent import ParallelSkillEvolver, _MAP_OUTPUT_FORMAT, MERGE_SYSTEM_PROMPT, chunk_list
import skill_evolver.skill_evolving_agent as official_apply
from src.react_agent.models import Message, ModelSettings
from recovery_adapter import compile_recovery

PROMPTS = json.loads((HERE/"prompts.json").read_text(encoding="utf-8"))
CHECKER = DEMO / ".runtime/node_modules/openclaw/skills/skill-creator/scripts/quick_validate.py"
PACKAGER = CHECKER.parent / "package_skill.py"
COMMIT = "3d0b52a140f002a512930252b613c49048f7d5ac"
CONFIG = {"requested_model":"ecnu-plus", "base_url":"https://chat.ecnu.edu.cn/open/api/v1",
 "temperature":0, "seed_sent":False, "rounds":1, "max_requests":40,
 "max_total_reported_tokens":1000000, "max_concurrent_http":1,
 "timeout_seconds":120, "retry_count":0,
 "output_tokens":{"recovery":10000,"analysis":3000,"patch":6000},
 "official":{"batch_size":2,"merge_batch_size":5,"max_workers":2,"max_merge_levels":2,
 "max_skill_lines":500,"max_references":5,"max_verification_rounds":0,
 "skip_translation":True,"patch_pipeline":"json","enable_json_format_self_fix":False,
 "max_continuations":0},
 "scope":"generation-only; no consumer or new business task execution",
 "method":"official Trace2Skill core plus neutral history and event-bag recovery adapters"}
def dump(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def simple(value):
    if is_dataclass(value):return simple(asdict(value))
    if isinstance(value,dict):return {str(k):simple(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [simple(v) for v in value]
    if isinstance(value,Path):return str(value)
    return value
def parse_json(text):
    s=text.strip()
    if s.startswith("```"):
        s=re.sub(r"^\s*```(?:json)?\s*", "",s)
        s=re.sub(r"\s*```\s*$","",s)
    value=json.loads(s)
    if not isinstance(value,dict):raise ValueError("Expected JSON object")
    return value
def model_views():
    source=json.loads((HERE/"private/frozen_source.json").read_text(encoding="utf-8"))
    views=[];aliases=[]
    for session in source["sessions"]:
        sid=session["session_id"];msgs=[]
        for i,m in enumerate(session["messages"],1):
            local=f"m{i:03d}"
            msgs.append({"id":local,"role":m["role"],"content":m["content"],
                "source_occurrences":deepcopy(m.get("source_occurrences",[])),
                "source_order_is_chronology":False})
            aliases.append({"session_id":sid,"local_id":local,"group_id":m["group_id"],
                "source_group_ids":m.get("source_group_ids",[]),
                "content_sha256":hashlib.sha256(m["content"].encode()).hexdigest()})
        tools=[]
        for i,row in enumerate((r for r in source["tool_records"] if r["session_id"]==sid),1):
            local=f"tool{i:03d}"
            tools.append({"id":local,"record":deepcopy(row),"snapshot_is_execution_sequence":False})
            aliases.append({"session_id":sid,"local_id":local,"record_id":row["record_id"]})
        views.append({"session_id":sid,"messages":msgs,"tools":tools,
            "chronology_verified":False,"task_outcome":"UNKNOWN",
            "attachments_available":False,"missing_skill_implementation":"not inferred from skill names",
            "research_labels_included":False})
    return views,aliases
def hashes():
    files=["run_experiment.py","recovery_adapter.py","prompts.json","initial_skill.md","export_inputs.py",
        "private/frozen_source.json","private/ecv_input.json","private/input_manifest.json","private/input_integrity.json"]
    result={n:sha(HERE/n) for n in files}
    result["checker"]=sha(CHECKER);result["packager"]=sha(PACKAGER)
    for name in ("relational","intake","pipeline","library_pipeline"):
        result["demo/"+name+".py"]=sha(DEMO/"skilldemo"/(name+".py"))
    result["official_source_manifest"]=sha(BASELINE/"_codex_preparation/source_manifest.json")
    return result
def source_checks(views):
    if len(views)!=6 or sum(len(s["messages"]) for s in views)!=129:
        raise ValueError("Frozen source coverage differs from planned six-session corpus")
    if sum(len(m["content"]) for s in views for m in s["messages"])!=30603:
        raise ValueError("Frozen source text changed")
    if sum(len(s["tools"]) for s in views)!=11:raise ValueError("Tool records incomplete")
    for s in views:
        ids=[m["id"] for m in s["messages"]]
        if len(ids)!=len(set(ids)):raise ValueError("Duplicate source alias")
        if s["task_outcome"]!="UNKNOWN" or s["chronology_verified"]:raise ValueError("False outcome/time certification")
    probe=json.loads((BASELINE/"_codex_preparation/offline_probe_result.json").read_text(encoding="utf-8"))
    if probe.get("status")!="passed":raise ValueError("Official offline mechanism precheck not passed")
    commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=BASELINE,text=True).strip()
    if commit!=COMMIT:raise ValueError("Official commit changed")
    changed=subprocess.check_output(["git","diff","--name-only"],cwd=BASELINE,text=True).strip()
    if changed:raise ValueError("Official tracked source modified")
    official_apply.QUICK_VALIDATE_SCRIPT=CHECKER

class BudgetClient:
    def __init__(self,root):
        self.root=Path(root);self.lock=threading.RLock();self.rows=[]
        self.known_tokens=36;self.started=0;self.errors=0
        self.reserved_unknown_tokens=0
        self.key=os.environ.get("ECNU_API_KEY")
        if not self.key:raise RuntimeError("Missing runtime ECNU_API_KEY")
    def save(self):
        dump(self.root/"requests_ledger.json",{"requests":self.rows,"calibration_tokens":36,
            "requests_started":self.started,"known_total_tokens":self.known_tokens,
            "unknown_usage_reservation_tokens":self.reserved_unknown_tokens,"errors":self.errors,
            "calibration_file":"private/calibration/api_probe.json","cost_currency":None})
    def call(self,system,user,stage,max_tokens):
        # Serialized network reservation makes the conservative byte-bound budget auditable.
        with self.lock:
            if self.started>=CONFIG["max_requests"]-1:raise RuntimeError("REQUEST_BUDGET_EXHAUSTED")
            payload={"model":CONFIG["requested_model"],"messages":[{"role":"system","content":system},
                {"role":"user","content":user}],"temperature":0,"max_tokens":max_tokens,"stream":False}
            estimated_upper=len(json.dumps(payload,ensure_ascii=False).encode())+max_tokens
            if self.known_tokens+self.reserved_unknown_tokens+estimated_upper>CONFIG["max_total_reported_tokens"]:
                raise RuntimeError("TOKEN_BUDGET_RESERVATION_EXHAUSTED")
            self.started+=1;seq=self.started
            row={"index":seq,"stage":stage,"request_sha256":hashlib.sha256(canonical(payload).encode()).hexdigest(),
                "status":"STARTED","input_upper_bound_bytes":estimated_upper-max_tokens,
                "max_output_tokens":max_tokens,"requested_model":CONFIG["requested_model"]}
            self.rows.append(row);dump(self.root/"requests"/f"{seq:03d}_request.json",payload);self.save()
            req=urllib.request.Request(CONFIG["base_url"]+"/chat/completions",
                data=json.dumps(payload,ensure_ascii=False).encode(),
                headers={"Authorization":"Bearer "+self.key,"Content-Type":"application/json"})
            begin=time.monotonic()
            try:
                with urllib.request.urlopen(req,timeout=CONFIG["timeout_seconds"]) as resp:
                    response=json.loads(resp.read())
                dump(self.root/"requests"/f"{seq:03d}_response.json",response)
                choice=response["choices"][0]
                row.update(status="RETURNED",served_model=response.get("model"),usage=response.get("usage"),
                    finish_reason=choice.get("finish_reason"))
                usage=response.get("usage") or {}
                tokens=usage.get("total_tokens")
                if isinstance(tokens,int):self.known_tokens+=tokens
                else:self.reserved_unknown_tokens+=estimated_upper
                content=choice["message"].get("content")
                if not isinstance(content,str) or not content.strip():raise ValueError("EMPTY_RESPONSE")
                if choice.get("finish_reason")=="length":raise ValueError("OUTPUT_INCOMPLETE_LENGTH")
                if self.known_tokens>CONFIG["max_total_reported_tokens"]:raise RuntimeError("TOKEN_BUDGET_EXCEEDED")
                row["status"]="COMPLETED"
                print(json.dumps({"request":seq,"stage":stage,"usage":usage,"served_model":response.get("model")}),flush=True)
                return content
            except Exception as exc:
                self.errors+=1;row.update(status="FAILED",error_type=type(exc).__name__,
                    error=str(exc).replace(self.key,"[REDACTED]"))
                if isinstance(exc,urllib.error.HTTPError):
                    row["http_status"]=exc.code
                    row["error_body"]=exc.read().decode("utf-8",errors="replace").replace(self.key,"[REDACTED]")
                if not row.get("usage"):self.reserved_unknown_tokens+=estimated_upper
                print(json.dumps({"request":seq,"stage":stage,"status":"FAILED","error_type":type(exc).__name__}),flush=True)
                raise
            finally:
                row["elapsed_seconds"]=round(time.monotonic()-begin,3);self.save()

class OfficialClient:
    def __init__(self,budget,arm):self.budget=budget;self.arm=arm
    def chat(self,messages,settings):
        system=messages[0].content
        user="\n".join(m.content for m in messages[1:])
        phase="merge" if "skill edit coordinator" in system else "map"
        return self.budget.call(system,user,self.arm+".trace2skill."+phase,settings.max_tokens or 6000)

class NeutralEvolver(ParallelSkillEvolver):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._merge_system_prompt=MERGE_SYSTEM_PROMPT.replace("different failures","different experiences")+"\n"+PROMPTS["neutral"]
    def _build_map_system_prompt(self):
        fmt=_MAP_OUTPUT_FORMAT.replace("what failures you see and what changes address them",
            "what grounded experiences you see and what bounded changes they support")
        return PROMPTS["map"]+"\n"+fmt
    def _build_map_user_message(self,state,records,batch_idx,total_batches):
        return canonical({"initial_skill_files":state,"records":records,"batch_index":batch_idx,
            "batch_count":total_batches,"max_skill_lines":self.max_skill_lines})
    def _call_llm(self,system_prompt,user_message,max_continuations=0,tag="editting",expect_semantic=False):
        return super()._call_llm(system_prompt,user_message,max_continuations=0,tag=tag,expect_semantic=expect_semantic)
    def _sanitize_translated_edits(self,state,edits):
        result=super()._sanitize_translated_edits(state,edits)
        for e in result:
            if not (e.file=="SKILL.md" or re.fullmatch(r"references/[\w.-]+\.md",e.file)):
                raise ValueError("Unexpected skill resource path")
        return result

def analyze(budget,view,arm,recovery=None):
    value=deepcopy(view)
    if recovery is not None:value["recovery"]=recovery
    text=budget.call(PROMPTS["analysis"],canonical(value),arm+".analysis."+view["session_id"],3000)
    obj=parse_json(text)
    if obj.get("instance_id")!=view["session_id"] or obj.get("task_outcome")!="UNKNOWN":
        raise ValueError("Analysis changed instance/outcome")
    ids={m["id"] for m in view["messages"]}|{t["id"] for t in view["tools"]}
    if not isinstance(obj.get("items"),list) or len(obj["items"])>8:raise ValueError("Analysis item budget/schema invalid")
    for item in obj["items"]:
        if not item.get("content") or not item.get("source_ids") or any(i not in ids for i in item["source_ids"]):
            raise ValueError("Analysis missing real source reference")
        if item.get("evidence_status") not in ("USER_REQUIREMENT","VISIBLE_METHOD_UNVERIFIED","OBSERVED_LOCAL_FAILURE","VERIFIED_LOCAL_RESULT"):
            raise ValueError("Analysis evidence status invalid")
    return obj

def evolve(budget,records,folder,arm):
    skill=folder/"skills/spreadsheet-generation-audit"
    skill.mkdir(parents=True);(skill/"SKILL.md").write_bytes((HERE/"initial_skill.md").read_bytes())
    settings=deepcopy(CONFIG["official"])
    settings.pop("max_continuations")
    error_start=budget.errors
    evolver=NeutralEvolver(client=OfficialClient(budget,arm),skill_dir=skill,temperature=0,max_tokens=6000,
        verbose=False,dry_run=False,output_dir=folder/"official_intermediates",
        parse_failure_dir=folder/"parse_failures",**settings)
    result=evolver.run(records,input_mode="records")
    dump(folder/"official_result.json",simple(result))
    expected=len(chunk_list(records,2))
    if len(result.get("patches",[]))!=expected or budget.errors!=error_start:
        raise ValueError("Official MAP coverage incomplete or failed request swallowed")
    if list((folder/"parse_failures").glob("**/*")):
        raise ValueError("Official parsing failures occurred")
    if result.get("final_patch") is None:raise ValueError("Official merge did not complete")
    check=subprocess.run([sys.executable,str(CHECKER),str(skill)],capture_output=True,text=True)
    dump(folder/"format_validation.json",{"returncode":check.returncode,"stdout":check.stdout,"stderr":check.stderr,
        "checker_sha256":sha(CHECKER)})
    if check.returncode:raise ValueError("Generated skill format invalid")
    missing=[]
    for p in skill.rglob("*.md"):
        for rel in re.findall(r"\]\((references/[^)]+)\)",p.read_text(encoding="utf-8")):
            if not (skill/rel).is_file():missing.append(rel)
    if missing:raise ValueError("Missing skill resources: "+",".join(missing))
    packages=folder/"packages";packages.mkdir()
    pkg=subprocess.run([sys.executable,str(PACKAGER),str(skill),str(packages)],capture_output=True,text=True)
    dump(folder/"package_validation.json",{"returncode":pkg.returncode,"stdout":pkg.stdout,"stderr":pkg.stderr})
    if pkg.returncode or not list(packages.glob("*.skill")):raise ValueError("Official OpenClaw packaging failed")
    return {"status":"GENERATED_CANDIDATE" if result.get("edits") else "NO_LEARNED_CHANGE",
        "map_patch_count":len(result["patches"]),"applied_files":len(result.get("edits",[])),
        "skill_path":str(skill),"skill_sha256":sha(skill/"SKILL.md"),
        "line_count":len((skill/"SKILL.md").read_text(encoding="utf-8").splitlines()),
        "package_count":len(list(packages.glob("*.skill"))),"task_benefit":"NOT_EVALUATED"}

def prepare():
    views,aliases=model_views();source_checks(views)
    dump(HERE/"private/model_views.json",views);dump(HERE/"private/source_aliases.json",aliases)
    # Free schema controls validate candidate choice, response edge and unknown outcome.
    synthetic={"session_id":"synthetic","messages":[{"id":"m001","role":"user","content":"write notice"},
        {"id":"m002","role":"assistant","content":"draft"}],"tools":[]}
    raw={"session_id":"synthetic","tasks":[{"id":"t1","goal":"notice","object":"notice","anchor_message":"m001","outcome":"UNKNOWN"}],
        "memberships":[{"message_id":m,"kind":"REQUEST","options":[{"task_ids":["t1"],"score":1,"reason":"known control"}]} for m in ("m001","m002")],
        "relations":[{"source":"m002","kind":"RESPONDS_TO","options":[{"target":"m001","score":1,"reason":"known control","source_ids":["m001","m002"]}]}],
        "requirements":[],"uncertainties":[]}
    compiled=compile_recovery(raw,synthetic)
    if len(compiled["tasks"])!=1 or len(compiled["tasks"][0]["relations"])!=1:raise ValueError("Recovery adapter control failed")
    bad=deepcopy(raw);bad["tasks"][0]["outcome"]="SUCCESS"
    try:compile_recovery(bad,synthetic)
    except ValueError:pass
    else:raise ValueError("Unknown-outcome control failed")
    marker={"status":"PREPARED","configuration":CONFIG,"official_commit":COMMIT,
        "source_hashes":hashes(),"model_views_sha256":sha(HERE/"private/model_views.json"),
        "source_aliases_sha256":sha(HERE/"private/source_aliases.json"),
        "session_count":len(views),"message_count":sum(len(s["messages"]) for s in views),
        "message_characters":sum(len(m["content"]) for s in views for m in s["messages"]),
        "tool_record_count":sum(len(s["tools"]) for s in views),
        "session_input_characters":{v["session_id"]:len(canonical(v)) for v in views},
        "source_and_adapter_controls":"PASS; not semantic gold",
        "calibration_model_field":"qwen3.8-flash","consumer_experiment":False}
    target=HERE/"private/frozen_protocol.json"
    if target.exists() and json.loads(target.read_text(encoding="utf-8"))!=marker:
        raise ValueError("Prepared protocol differs; use new experiment version")
    dump(target,marker);print(json.dumps({k:marker[k] for k in ("status","session_count","message_count","message_characters","tool_record_count","session_input_characters")}))
    return marker

def run():
    protocol=json.loads((HERE/"private/frozen_protocol.json").read_text(encoding="utf-8"))
    if protocol["source_hashes"]!=hashes():raise ValueError("Code/input changed after freeze")
    views=json.loads((HERE/"private/model_views.json").read_text(encoding="utf-8"))
    if sha(HERE/"private/model_views.json")!=protocol["model_views_sha256"]:raise ValueError("Model inputs changed")
    source_checks(views)
    root=HERE/"private/run_v1"
    if root.exists():raise ValueError("Existing run preserved; no silent retry/overwrite")
    root.mkdir();dump(root/"protocol.json",protocol)
    snap=root/"source_snapshot";snap.mkdir()
    for n in ("run_experiment.py","recovery_adapter.py","prompts.json","initial_skill.md","export_inputs.py"):
        shutil.copy2(HERE/n,snap/n)
    state={"status":"RUNNING","configuration":CONFIG,"arms":{},"consumer_experiment":False}
    dump(root/"run.json",state)
    budget=BudgetClient(root)
    try:
        for arm in ("A","B"):
            folder=root/arm;folder.mkdir();records=[]
            try:
                for view in views:
                    graph=None
                    if arm=="B":
                        text=budget.call(PROMPTS["recovery"],canonical(view),"B.recovery."+view["session_id"],10000)
                        raw=parse_json(text);dump(folder/"recovery_raw"/(view["session_id"]+".json"),raw)
                        graph=compile_recovery(raw,view)
                        dump(folder/"recovered"/(view["session_id"]+".json"),graph)
                    record=analyze(budget,view,arm,graph)
                    records.append(record);dump(folder/"analyses"/(view["session_id"]+".json"),record)
                dump(folder/"analysis_records.json",records)
                state["arms"][arm]=evolve(budget,records,folder,arm)
                state["arms"][arm]["analysis_item_count"]=sum(len(r["items"]) for r in records)
                state["arms"][arm]["analysis_records"]=len(records)
            except Exception as exc:
                state["arms"][arm]={"status":"FAILED","error_type":type(exc).__name__,
                    "error":str(exc).replace(budget.key,"[REDACTED]"),"completed_analysis_records":len(records)}
                dump(folder/"failure.json",state["arms"][arm])
            dump(root/"run.json",state)
        successful=all(state["arms"].get(a,{}).get("status") in ("GENERATED_CANDIDATE","NO_LEARNED_CHANGE") for a in ("A","B"))
        state["status"]="COMPLETED_GENERATION" if successful else "PARTIAL_OR_FAILED"
        state["requests_started"]=budget.started;state["known_total_tokens_including_calibration"]=budget.known_tokens
        state["unknown_usage_reservation_tokens"]=budget.reserved_unknown_tokens
        files={str(p.relative_to(root)):sha(p) for a in ("A","B") for p in (root/a/"skills").rglob("*") if p.is_file()}
        dump(root/"candidate_manifest.json",{"status":state["status"],"files":files,
            "protocol_sha256":sha(HERE/"private/frozen_protocol.json"),
            "semantic_status":"CANDIDATE_NOT_GOLD","task_benefit":"NOT_EVALUATED"})
    finally:
        budget.save();dump(root/"run.json",state)
    print(json.dumps(state,ensure_ascii=False))

if __name__=="__main__":
    logging.basicConfig(level=logging.WARNING)
    parser=argparse.ArgumentParser();parser.add_argument("--prepare",action="store_true");parser.add_argument("--run",action="store_true")
    args=parser.parse_args()
    if args.prepare:prepare()
    elif args.run:run()
    else:parser.error("Choose --prepare or --run")

