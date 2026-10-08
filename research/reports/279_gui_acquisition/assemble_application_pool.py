"""Assemble researched application candidates and acquired-source evidence."""
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
import json
import re

ROOT = Path(__file__).resolve().parent

def canonical(url):
    return url.removesuffix(".git").rstrip("/").lower()

def items(path):
    document = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(document, list):
        return document
    for key in ("selected_candidates", "candidates", "applications"):
        if key in document:
            return document[key]
    raise ValueError(f"no candidate list in {path}")

if __name__ == "__main__":
    selected = items(ROOT / "selected_candidates.json")
    details = [item for area in ("desktop", "mac_android", "web") for item in items(ROOT / area / "selected_candidates.json")]
    details = {(canonical(item["repo"]), item["commit"]): item for item in details}
    acquired = json.loads((ROOT / "source_acquisition_manifest.json").read_text(encoding="utf-8"))
    acquisition = {(canonical(item["repo"]), item["commit"]): item for item in acquired["applications"]}
    candidates = []
    for item in selected:
        key = (canonical(item["repo"]), item["commit"])
        assert key in details and key in acquisition, f"missing evidence {key}"
        record = dict(details[key])
        record.update({"source_acquisition": acquisition[key], "runtime_accepted": False, "trajectory_count": 0, "verified_skill_count": 0, "max_corrective_rounds_including_first": 3})
        assert record.get("workflows"), f"missing observable workflows {key}"
        assert record.get("bench_correspondence"), f"missing capability correspondence {key}"
        candidates.append(record)
    counts = Counter(c["platform"] for c in candidates)
    catalog = json.loads((ROOT / "bench_source_catalog.json").read_text(encoding="utf-8"))
    task_ids = {r["instance_id"].lower() for r in catalog["tasks"]}
    referenced = sorted({task for c in candidates for task in re.findall(r"(?:ubuntu|macos|windows|android|web)/[A-Za-z0-9_.-]+", json.dumps(c["bench_correspondence"], ensure_ascii=False))})
    invalid = [task for task in referenced if task.lower() not in task_ids]
    assert not invalid, f"nonexistent benchmark correspondence IDs {invalid}"
    correspondence = {"scope": "existence of public task IDs, not causal transfer or private-test coverage", "referenced_task_ids": referenced, "referenced_task_id_count": len(referenced), "nonexistent_task_ids": invalid, "actual_skill_transfer_measured": False}
    (ROOT / "bench_correspondence_audit.json").write_text(json.dumps(correspondence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    report = {"schema": "skillloop.paper_inspired_gui_application_source_pool.v1", "created_at_utc": datetime.now(timezone.utc).isoformat(), "paper": "https://arxiv.org/html/2609.22000v1#S3.SS1", "official_training_pool": False, "task_form": "running reference observation -> independent implementation -> build/run/behavioral and visual verification", "phase": "sources_acquired_runtime_admission_pending", "platform_counts": dict(counts), "application_count": len(candidates), "proposed_public_workflow_count": sum(len(c["workflows"]) for c in candidates), "model_calls_this_acquisition": 0, "runtime_accepted_count": 0, "trajectory_count": 0, "verified_skill_count": 0, "exact_native_source_deduplication": "source_integrity_verification.json", "web_identity_scope": "50 public landing-page identity summaries; anonymized origins and full fork graph remain unresolved", "standing_rw_stop_preserved": True, "legacy_five_seed_245_plan_repartitioned": False, "automatic_evaluation_authorized": False, "applications": candidates}
    report["bench_correspondence_id_validation"] = correspondence
    (ROOT / "application_pool.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k:report[k] for k in ["application_count", "platform_counts", "proposed_public_workflow_count", "runtime_accepted_count", "trajectory_count"]}))
