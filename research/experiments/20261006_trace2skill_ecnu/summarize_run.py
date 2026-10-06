"""Offline result accounting; no model/API access and no source mutation."""
import argparse, csv, hashlib, json, re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent
RUN=ROOT/"private/run_v1"
def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    state=read(RUN/"run.json");ledger=read(RUN/"requests_ledger.json")
    stages={}
    for row in ledger["requests"]:
        parts=row["stage"].split(".")
        key=".".join(parts[:3]) if "trace2skill" in parts else ".".join(parts[:2])
        a=stages.setdefault(key,{"requests":0,"completed":0,"prompt_tokens":0,"completion_tokens":0,
            "reported_total_tokens":0,"unknown_usage_receipts":0,"elapsed_seconds":0})
        a["requests"]+=1;a["completed"]+=row["status"]=="COMPLETED"
        u=row.get("usage") or {}
        if isinstance(u.get("total_tokens"),int):
            a["reported_total_tokens"]+=u["total_tokens"]
            a["prompt_tokens"]+=u.get("prompt_tokens",0);a["completion_tokens"]+=u.get("completion_tokens",0)
        else:a["unknown_usage_receipts"]+=1
        a["elapsed_seconds"]+=row.get("elapsed_seconds",0)
    arms={}
    for arm in ("A","B"):
        folder=RUN/arm;files=list((folder/"analyses").glob("*.json"))
        analyses=[read(p) for p in files];items=[i for r in analyses for i in r["items"]]
        statuses=Counter(i["evidence_status"] for i in items)
        rec=[read(p) for p in (folder/"recovered").glob("*.json")]
        skills=list((folder/"skills").glob("*/SKILL.md"))
        arms[arm]={"state":state["arms"].get(arm,{}),"analysis_records":len(analyses),"analysis_items":len(items),
            "evidence_status_distribution":dict(statuses),"recovered_sessions":len(rec),
            "recovered_task_candidates":sum(len(r["tasks"]) for r in rec),
            "selected_relation_memberships":sum(sum(len(t["relations"]) for t in r["tasks"]) for r in rec),
            "unique_selected_relations":sum(len({(x["source"],x["target"],x["kind"]) for t in r["tasks"] for x in t["relations"]}) for r in rec),
            "unresolved_memberships":sum(len(r["unresolved_memberships"]) for r in rec),
            "unresolved_relation_records":sum(len(r["unresolved_relations"]) for r in rec),
            "skill_files":[{"path":str(p.relative_to(ROOT)),"sha256":digest(p),
                "characters":len(p.read_text(encoding="utf-8")),"lines":len(p.read_text(encoding="utf-8").splitlines()),
                "differs_from_initial":digest(p)!=digest(ROOT/"initial_skill.md")} for p in skills]}
    report={"status":state["status"],"run_name":RUN.name,"source_sessions":6,"source_messages":129,"source_body_characters":30603,
        "tool_records":11,"tool_payload_serialized_characters":120596,"stages":stages,"arms":arms,
        "requests_including_calibration":ledger["requests_started"]+1,
        "reported_tokens_including_calibration":ledger["known_total_tokens"],
        "unknown_usage_reservation_tokens":ledger["unknown_usage_reservation_tokens"],
        "response_model_fields":sorted({r.get("served_model") for r in ledger["requests"] if r.get("served_model")}),
        "calibration_tokens":ledger["calibration_tokens"],"task_benefit":"NOT_EVALUATED","gold_quality":"NOT_CERTIFIED",
        "new_requests_in_run":state.get("new_requests_v3",state.get("new_requests_v2",state.get("requests_started"))),
        "replayed_requests":read(RUN/"response_replay.json") if (RUN/"response_replay.json").exists() else []}
    (RUN/"accounting_summary.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with (RUN/"generation_costs.csv").open("w",encoding="utf-8-sig",newline="") as f:
        names=["stage","requests","completed","prompt_tokens","completion_tokens","reported_total_tokens","unknown_usage_receipts","elapsed_seconds"]
        w=csv.DictWriter(f,fieldnames=names);w.writeheader()
        for name,row in stages.items():w.writerow({"stage":name,**row})
        w.writerow({"stage":"calibration","requests":1,"completed":1,"prompt_tokens":30,"completion_tokens":6,"reported_total_tokens":36,"unknown_usage_receipts":0,"elapsed_seconds":0.651})
    print(json.dumps(report,ensure_ascii=False))
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--run-name",choices=("run_v1","run_v2","run_v3"),default="run_v1")
    args=parser.parse_args()
    RUN=ROOT/"private"/args.run_name
    main()
