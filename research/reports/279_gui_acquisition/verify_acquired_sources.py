"""Verify source acquisition integrity; not application runtime testing."""
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter
import hashlib
import json

ROOT = Path(__file__).resolve().parent

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

if __name__ == "__main__":
    manifest = json.loads((ROOT / "source_acquisition_manifest.json").read_text(encoding="utf-8"))
    results = []
    for app in manifest["applications"]:
        assert app["status"] == "source_acquired_not_executed"
        inventory_file = Path(app["inventory"])
        inventory = json.loads(inventory_file.read_text(encoding="utf-8"))
        source = Path(app["source_directory"]).resolve()
        failed = []
        for item in inventory["files"]:
            path = (source / item["path"]).resolve()
            assert path.is_relative_to(source)
            if not path.is_file() or path.stat().st_size != item["bytes"] or digest(path) != item["sha256"]:
                failed.append(item["path"])
        archive_ok = digest(Path(app["archive"])) == app["archive_sha256"]
        inventory_ok = digest(inventory_file) == app["inventory_sha256"]
        gitmodules = source / ".gitmodules"
        results.append({"application_id": app["application_id"], "commit": app["commit"], "archive_hash_ok": archive_ok, "inventory_hash_ok": inventory_ok, "files_checked": len(inventory["files"]), "file_hash_failures": failed, "has_gitmodules": gitmodules.exists(), "submodules_acquired": False, "runtime_accepted": False})
    catalog = json.loads((ROOT / "bench_source_catalog.json").read_text(encoding="utf-8"))
    normalize = lambda s: s.rstrip("/").removesuffix(".git").lower()
    native_sources = {normalize(r["repo"]) for r in catalog["tasks"] if r.get("repo")}
    overlap = sorted({normalize(r["repo"]) for r in manifest["applications"]} & native_sources)
    platforms = Counter(a["platform"] for a in manifest["applications"])
    passed = all(r["archive_hash_ok"] and r["inventory_hash_ok"] and not r["file_hash_failures"] for r in results) and not overlap and set(platforms) == {"ubuntu", "macos", "windows", "android", "web"}
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "scope": "archive/inventory/extracted source hashes and exact canonical repository identity only", "passed": passed, "platform_counts": dict(platforms), "native_benchmark_rows_checked": 200, "native_benchmark_unique_repo_count": len(native_sources), "exact_repository_overlap": overlap, "web_snapshot_identity_audit": "web_bench_identity_audit.json", "full_fork_and_anonymized_origin_exclusion_proven": False, "source_manifest_sha256": digest(ROOT / "source_acquisition_manifest.json"), "files_checked": sum(r["files_checked"] for r in results), "applications": results}
    (ROOT / "source_integrity_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ["passed", "platform_counts", "files_checked", "exact_repository_overlap"]}))
    assert passed
