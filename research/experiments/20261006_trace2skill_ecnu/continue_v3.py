"""One explicit transport-only retry, preserving all prior calls and unknown usage."""
from copy import deepcopy
import argparse, hashlib, json, shutil
from pathlib import Path
import run_experiment as v1
import continue_v2 as v2

HERE = v1.HERE
OLD = HERE / "private/run_v2"
ROOT = HERE / "private/run_v3"
v2.OLD = OLD
v1.CONFIG = deepcopy(v1.CONFIG)
v1.CONFIG["timeout_seconds"] = 600

def protocol():
    original = json.loads((HERE / "private/frozen_protocol.json").read_text(encoding="utf-8"))
    if original["source_hashes"] != v1.hashes():
        raise ValueError("Original frozen source changed")
    ledger = json.loads((OLD / "requests_ledger.json").read_text(encoding="utf-8"))
    failures = [r for r in ledger["requests"] if r["status"] == "FAILED"]
    if len(failures) != 1 or failures[0].get("error_type") != "TimeoutError":
        raise ValueError("v3 permits exactly the known transport timeout, no other retry")
    failed = failures[0]
    if failed["stage"] != "B.recovery.conv_d2c84054d91a" or failed.get("usage"):
        raise ValueError("Unexpected failed stage or receipt")
    if (OLD / "requests" / f"{failed['index']:03d}_response.json").exists():
        raise ValueError("A full response already exists; no selecting repeated output")
    return {"version": "v3-transport-timeout-only", "base_protocol": original,
        "configuration": v1.CONFIG, "v2_protocol_sha256": v1.sha(HERE / "private/frozen_protocol_v2.json"),
        "script_sha256": v1.sha(Path(__file__)), "v2_adapter_sha256": v1.sha(Path(v2.__file__)),
        "prior_run_sha256": v1.sha(OLD / "run.json"), "prior_ledger_sha256": v1.sha(OLD / "requests_ledger.json"),
        "prior_response_sha256": {p.name: v1.sha(p) for p in (OLD / "requests").glob("*_response.json")},
        "explicit_retry": {"prior_index": failed["index"], "stage": failed["stage"],
            "request_sha256": failed["request_sha256"], "reason": "No complete response within 120 seconds"},
        "change": "Client read timeout 120 to 600 seconds; no request payload or semantic change",
        "cost": "Prior failed request and unknown reservation retained; one explicit retry billed separately",
        "stop": "Any further failure ends this batch; no v4 retry", "no_consumer": True}

def prepare():
    candidate = protocol()
    views = json.loads((HERE / "private/model_views.json").read_text(encoding="utf-8"))
    v1.source_checks(views)
    view = next(x for x in views if x["session_id"] == "conv_d2c84054d91a")
    payload = {"model": v1.CONFIG["requested_model"], "messages": [
        {"role": "system", "content": v1.PROMPTS["recovery"]},
        {"role": "user", "content": v1.canonical(view)}],
        "temperature": 0, "max_tokens": 10000, "stream": False}
    actual = hashlib.sha256(v1.canonical(payload).encode()).hexdigest()
    if actual != candidate["explicit_retry"]["request_sha256"]:
        raise ValueError("Timeout-only retry payload changed")
    frozen = HERE / "private/frozen_protocol_v3.json"
    if frozen.exists() and json.loads(frozen.read_text(encoding="utf-8")) != candidate:
        raise ValueError("v3 freeze differs")
    v1.dump(frozen, candidate)
    print(json.dumps({"status": "PREPARED_V3", "real_api_calls": 0,
        "retry_payload_sha_unchanged": True, "timeout_seconds": 600}))

class TransportBudget(v2.ReplayBudget):
    def __init__(self, root, frozen):
        super().__init__(root)
        self.explicit_retry = frozen["explicit_retry"]
        self.retried = False
    def call(self, system, user, stage, max_tokens):
        if stage == self.explicit_retry["stage"]:
            if self.retried:
                raise ValueError("Only one explicit transport retry allowed")
            payload = {"model": v1.CONFIG["requested_model"], "messages": [
                {"role": "system", "content": system}, {"role": "user", "content": user}],
                "temperature": 0, "max_tokens": max_tokens, "stream": False}
            digest = hashlib.sha256(v1.canonical(payload).encode()).hexdigest()
            if digest != self.explicit_retry["request_sha256"]:
                raise ValueError("Explicit timeout retry changed payload")
            self.retried = True
            v1.dump(self.root / "explicit_transport_retry.json", {**self.explicit_retry,
                "new_request_index": self.started + 1, "timeout_seconds": 600,
                "prior_usage_known": False, "prior_cost_not_zeroed": True})
        return super().call(system, user, stage, max_tokens)

def run():
    frozen = json.loads((HERE / "private/frozen_protocol_v3.json").read_text(encoding="utf-8"))
    if frozen != protocol():
        raise ValueError("v3 freeze changed")
    if ROOT.exists():
        raise ValueError("Existing v3 preserved")
    views = json.loads((HERE / "private/model_views.json").read_text(encoding="utf-8"))
    if v1.sha(HERE / "private/model_views.json") != frozen["base_protocol"]["model_views_sha256"]:
        raise ValueError("Model inputs changed")
    v1.source_checks(views)
    ROOT.mkdir()
    v1.dump(ROOT / "protocol.json", frozen)
    shutil.copytree(OLD / "source_snapshot", ROOT / "source_snapshot")
    shutil.copy2(Path(__file__), ROOT / "source_snapshot/continue_v3.py")
    shutil.copytree(OLD / "requests", ROOT / "requests")
    shutil.copytree(OLD / "A", ROOT / "A")
    prior = json.loads((OLD / "run.json").read_text(encoding="utf-8"))
    a = deepcopy(prior["arms"]["A"])
    a["skill_path"] = str(ROOT / "A/skills/spreadsheet-generation-audit")
    state = {"status": "RUNNING_V3", "configuration": v1.CONFIG, "arms": {"A": a},
        "previous_runs": ["run_v1 contract failure retained", "run_v2 timeout retained"],
        "consumer_experiment": False}
    v1.dump(ROOT / "run.json", state)
    budget = TransportBudget(ROOT, frozen)
    folder = ROOT / "B"
    folder.mkdir()
    records = []
    try:
        for view in views:
            text = budget.call(v1.PROMPTS["recovery"], v1.canonical(view), "B.recovery." + view["session_id"], 10000)
            raw = v1.parse_json(text)
            v1.dump(folder / "recovery_raw" / (view["session_id"] + ".json"), raw)
            graph, normalization = v2.compile_v2(raw, view)
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
        state["status"] = "PARTIAL_OR_FAILED_V3"
        state["arms"]["B"] = {"status": "FAILED", "error_type": type(exc).__name__,
            "error": str(exc).replace(budget.key, "[REDACTED]"), "completed_analysis_records": len(records)}
        v1.dump(folder / "failure.json", state["arms"]["B"])
    finally:
        state["requests_started"] = budget.started
        state["new_requests_v3"] = budget.started - budget.initial_started
        state["known_total_tokens_including_calibration"] = budget.known_tokens
        state["unknown_usage_reservation_tokens"] = budget.reserved_unknown_tokens
        budget.save()
        v1.dump(ROOT / "run.json", state)
        files = {str(p.relative_to(ROOT)): v1.sha(p) for arm in ("A", "B")
            for p in (ROOT / arm / "skills").rglob("*") if p.is_file()}
        v1.dump(ROOT / "candidate_manifest.json", {"status": state["status"], "files": files,
            "protocol_sha256": v1.sha(HERE / "private/frozen_protocol_v3.json"),
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
