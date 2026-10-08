"""Source-only extension of 279; preserves existing archives and candidates."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
import json
import os
from collections import Counter

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / "279_gui_acquisition"

if __name__ == "__main__":
    spec = importlib.util.spec_from_file_location("source_only_acquisition", ORIGINAL / "acquire_sources.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Windows extended paths preserve upstream long filenames verbatim.
    module.ROOT = Path("\\\\?\\" + str(ROOT)) if os.name == "nt" else ROOT
    original = json.loads((ORIGINAL / "source_acquisition_manifest.json").read_text(encoding="utf-8"))
    previous = ROOT / "source_acquisition_manifest.json"
    if previous.exists():
        for app in json.loads(previous.read_text(encoding="utf-8"))["applications"]:
            module.PREVIOUS[(app["repo"].lower().rstrip("/"), app["commit"])] = app
    additions = json.loads((ROOT / "selected_additions.json").read_text(encoding="utf-8"))
    if isinstance(additions, dict):
        additions = additions["candidates"]
    catalog = json.loads((ORIGINAL / "bench_source_catalog.json").read_text(encoding="utf-8"))
    forbidden = {module.canonical_repo(r["repo"]) for r in catalog["tasks"] if r.get("repo")}
    original_repos = {module.canonical_repo(r["repo"]) for r in original["applications"]}
    chosen_repos = [module.canonical_repo(r["repo"]) for r in additions]
    assert len(set(chosen_repos)) == len(chosen_repos)
    assert not set(chosen_repos) & forbidden
    assert not set(chosen_repos) & original_repos
    with ThreadPoolExecutor(max_workers=4) as pool:
        acquired = list(pool.map(module.acquire, additions))
    for app in acquired:
        for key in ("archive", "source_directory", "inventory"):
            if key in app:
                app[key] = app[key].removeprefix("\\\\?\\")
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "scope": "additional public source acquisition only; no model or application execution", "original_manifest": str(ORIGINAL / "source_acquisition_manifest.json"), "benchmark_revision": catalog["revision"], "applications": acquired, "summary": {"selected_additions": len(additions), "acquired": sum(a["status"] == "source_acquired_not_executed" for a in acquired), "archive_bytes": sum(a.get("archive_bytes", 0) for a in acquired), "regular_files": sum(a.get("regular_files", 0) for a in acquired), "platform_counts": dict(Counter(a["platform"] for a in acquired))}}
    (ROOT / "source_acquisition_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"]), flush=True)
    for app in acquired:
        print(json.dumps({k:app[k] for k in ("application_id", "status", "archive_bytes", "regular_files", "error") if k in app}), flush=True)
