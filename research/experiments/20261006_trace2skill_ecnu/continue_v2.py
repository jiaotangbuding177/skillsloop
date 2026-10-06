"""Versioned continuation: replay paid responses; derive only redundant edge provenance."""
from copy import deepcopy
import argparse, hashlib, json, shutil
from pathlib import Path
import run_experiment as v1

HERE = v1.HERE
OLD = HERE / "private/run_v1"
ROOT = HERE / "private/run_v2"

def compile_v2(raw, source):
    value = deepcopy(raw)
    messages = {m["id"] for m in source["messages"]}
    normalization = []
    for row in value.get("relations", []):
        src = row.get("source")
        for opt in row.get("options", []):
            target = opt.get("target")
            if target is None or src not in messages or target not in messages:
                continue  # Original compiler still rejects invalid real endpoints.
            if "source_ids" not in opt:
                opt["source_ids"] = [src, target]
                normalization.append({"source": src, "target": target, "added_ids": [src, target],
                    "basis": "existing structural endpoints; not new semantic evidence"})
    return v1.compile_recovery(value, source), normalization

def protocol():
    base = json.loads((HERE / "private/frozen_protocol.json").read_text(encoding="utf-8"))
    if base["source_hashes"] != v1.hashes():
        raise ValueError("Original frozen inputs/code changed")
    return {"version": "v2-endpoint-provenance-normalization", "base_protocol": base,
        "continuation_sha256": v1.sha(Path(__file__)),
        "old_run_sha256": v1.sha(OLD / "run.json"),
        "old_ledger_sha256": v1.sha(OLD / "requests_ledger.json"),
        "change": "Program derives missing source_ids only from already proposed real edge endpoints",
        "preserved": "Prompts, inputs, official core, semantic choices, A candidate, global budget",
        "replay": "Exact request hash must match; reused responses incur no new API request",
        "no_consumer": True}

def prepare():
    views = json.loads((HERE / "private/model_views.json").read_text(encoding="utf-8"))
    v1.source_checks(views)
    checks = []
    for view in views:
        raw_path = OLD / "B/recovery_raw" / (view["session_id"] + ".json")
        if not raw_path.exists():
            continue
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        compiled, added = compile_v2(raw, view)
        checks.append({"session_id": view["session_id"], "tasks": len(compiled["tasks"]),
            "normalization": added})
        bad = deepcopy(raw)
        bad["tasks"][0]["outcome"] = "SUCCESS"
        try:
            compile_v2(bad, view)
        except ValueError:
            pass
        else:
            raise ValueError("False success control failed")
        bad = deepcopy(raw)
        bad["relations"] = [{"source": view["messages"][-1]["id"], "kind": "RESPONDS_TO",
            "options": [{"target": "nonexistent", "score": 1, "reason": "invalid source control"}]}]
        try:
            compile_v2(bad, view)
        except ValueError:
            pass
        else:
            raise ValueError("Missing endpoint control failed")
        # A cached analysis can be reused only if the entire derived graph is unchanged.
        first = OLD / "B/analyses" / (view["session_id"] + ".json")
        if first.exists():
            value = deepcopy(view)
            value["recovery"] = compiled
            payload = {"model": v1.CONFIG["requested_model"], "messages": [
                {"role": "system", "content": v1.PROMPTS["analysis"]},
                {"role": "user", "content": v1.canonical(value)}],
                "temperature": 0, "max_tokens": 3000, "stream": False}
            expected = hashlib.sha256(v1.canonical(payload).encode()).hexdigest()
            ledger = json.loads((OLD / "requests_ledger.json").read_text(encoding="utf-8"))
            if not any(r["stage"] == "B.analysis." + view["session_id"] and
                       r["request_sha256"] == expected for r in ledger["requests"]):
                raise ValueError("Cached first analysis input differs")
    v1.dump(HERE / "private/v2_preflight.json", {"status": "PASS", "real_api_calls": 0,
        "checks": checks, "invalid_endpoint_and_false_success_controls": "PASS"})
    frozen = HERE / "private/frozen_protocol_v2.json"
    candidate = protocol()
    if frozen.exists() and json.loads(frozen.read_text(encoding="utf-8")) != candidate:
        raise ValueError("v2 freeze changed; do not overwrite")
    v1.dump(frozen, candidate)
    print(json.dumps({"status": "PREPARED_V2", "cached_recovery_records": len(checks),
        "real_api_calls": 0}, ensure_ascii=False))

class ReplayBudget(v1.BudgetClient):
    def __init__(self, root):
        super().__init__(root)
        old = json.loads((OLD / "requests_ledger.json").read_text(encoding="utf-8"))
        self.rows = deepcopy(old["requests"])
        self.started = old["requests_started"]
        self.known_tokens = old["known_total_tokens"]
        self.reserved_unknown_tokens = old["unknown_usage_reservation_tokens"]
        self.errors = old["errors"]
        self.cached = {(r["stage"], r["request_sha256"]): r for r in self.rows if r["status"] == "COMPLETED"}
        self.replayed = []
        self.initial_started = self.started
        self.save()
    def call(self, system, user, stage, max_tokens):
        payload = {"model": v1.CONFIG["requested_model"], "messages": [
            {"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0, "max_tokens": max_tokens, "stream": False}
        digest = hashlib.sha256(v1.canonical(payload).encode()).hexdigest()
        row = self.cached.get((stage, digest))
        if row:
            response = json.loads((OLD / "requests" / f"{row['index']:03d}_response.json").read_text(encoding="utf-8"))
            self.replayed.append({"stage": stage, "original_request_index": row["index"],
                "request_sha256": digest, "new_api_calls": 0})
            v1.dump(self.root / "response_replay.json", self.replayed)
            print(json.dumps({"stage": stage, "replayed": True, "new_api_calls": 0}), flush=True)
            return response["choices"][0]["message"]["content"]
        if any(r["stage"] == stage for r in self.cached.values()):
            raise ValueError("Cached stage request differs; no silent paid retry")
        return super().call(system, user, stage, max_tokens)

def run():
    frozen = json.loads((HERE / "private/frozen_protocol_v2.json").read_text(encoding="utf-8"))
    if frozen != protocol():
        raise ValueError("v2 code/base changed after freeze")
    if ROOT.exists():
        raise ValueError("Existing v2 preserved; no retry/overwrite")
    views = json.loads((HERE / "private/model_views.json").read_text(encoding="utf-8"))
    if v1.sha(HERE / "private/model_views.json") != frozen["base_protocol"]["model_views_sha256"]:
        raise ValueError("Model inputs changed")
    v1.source_checks(views)
    ROOT.mkdir()
    v1.dump(ROOT / "protocol.json", frozen)
    shutil.copytree(OLD / "source_snapshot", ROOT / "source_snapshot")
    shutil.copy2(Path(__file__), ROOT / "source_snapshot/continue_v2.py")
    shutil.copytree(OLD / "requests", ROOT / "requests")
    shutil.copytree(OLD / "A", ROOT / "A")
    previous = json.loads((OLD / "run.json").read_text(encoding="utf-8"))
    a = deepcopy(previous["arms"]["A"])
    a["origin"] = "unchanged candidate copied from run_v1; zero new API calls"
    a["skill_path"] = str(ROOT / "A/skills/spreadsheet-generation-audit")
    state = {"status": "RUNNING_V2", "configuration": v1.CONFIG, "arms": {"A": a},
        "previous_run": "run_v1 retained with failed B", "consumer_experiment": False}
    v1.dump(ROOT / "run.json", state)
    budget = ReplayBudget(ROOT)
    folder = ROOT / "B"
    folder.mkdir()
    records = []
    try:
        for view in views:
            text = budget.call(v1.PROMPTS["recovery"], v1.canonical(view), "B.recovery." + view["session_id"], 10000)
            raw = v1.parse_json(text)
            v1.dump(folder / "recovery_raw" / (view["session_id"] + ".json"), raw)
            graph, normalization = compile_v2(raw, view)
            v1.dump(folder / "recovered" / (view["session_id"] + ".json"), graph)
            v1.dump(folder / "normalization" / (view["session_id"] + ".json"), normalization)
            record = v1.analyze(budget, view, "B", graph)
            records.append(record)
            v1.dump(folder / "analyses" / (view["session_id"] + ".json"), record)
        v1.dump(folder / "analysis_records.json", records)
        state["arms"]["B"] = v1.evolve(budget, records, folder, "B")
        state["arms"]["B"]["analysis_item_count"] = sum(len(r["items"]) for r in records)
        state["arms"]["B"]["analysis_records"] = len(records)
        state["status"] = "COMPLETED_GENERATION"
    except Exception as exc:
        state["status"] = "PARTIAL_OR_FAILED_V2"
        state["arms"]["B"] = {"status": "FAILED", "error_type": type(exc).__name__,
            "error": str(exc).replace(budget.key, "[REDACTED]"), "completed_analysis_records": len(records)}
        v1.dump(folder / "failure.json", state["arms"]["B"])
    finally:
        state["requests_started"] = budget.started
        state["new_requests_v2"] = budget.started - budget.initial_started
        state["known_total_tokens_including_calibration"] = budget.known_tokens
        state["unknown_usage_reservation_tokens"] = budget.reserved_unknown_tokens
        budget.save()
        v1.dump(ROOT / "run.json", state)
        files = {str(p.relative_to(ROOT)): v1.sha(p) for arm in ("A", "B")
            for p in (ROOT / arm / "skills").rglob("*") if p.is_file()}
        v1.dump(ROOT / "candidate_manifest.json", {"status": state["status"], "files": files,
            "protocol_sha256": v1.sha(HERE / "private/frozen_protocol_v2.json"),
            "semantic_status": "CANDIDATE_NOT_GOLD", "task_benefit": "NOT_EVALUATED"})
    print(json.dumps(state, ensure_ascii=False))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--run", action="store_true")
    args = parser.parse_args()
    if args.prepare:
        prepare()
    elif args.run:
        run()
    else:
        parser.error("Choose --prepare or --run")
