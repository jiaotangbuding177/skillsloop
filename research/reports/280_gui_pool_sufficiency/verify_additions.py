"""Check acquired source hashes, without executing any upstream application."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / "279_gui_acquisition"

def io_path(value):
    path = Path(value).absolute()
    return Path("\\\\?\\" + str(path)) if os.name == "nt" and not str(path).startswith("\\\\?\\") else path

def sha256(path):
    h = hashlib.sha256()
    with io_path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def canonical(value):
    return value.removesuffix(".git").rstrip("/").lower()

if __name__ == "__main__":
    manifest_path = ROOT / "source_acquisition_manifest.json"
    manifest_sha = sha256(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    prior = json.loads((ORIGINAL / "source_integrity_verification.json").read_text(encoding="utf-8"))
    original = json.loads((ORIGINAL / "source_acquisition_manifest.json").read_text(encoding="utf-8"))
    catalog = json.loads((ORIGINAL / "bench_source_catalog.json").read_text(encoding="utf-8"))
    results = []
    for app in manifest["applications"]:
        assert app["status"] == "source_acquired_not_executed"
        inventory_path = io_path(app["inventory"])
        inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
        source = io_path(app["source_directory"]).resolve()
        failures = []
        for record in inventory["files"]:
            path = (source / record["path"]).resolve()
            assert path.is_relative_to(source)
            if not path.is_file() or path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
                failures.append(record["path"])
        gitmodules = source / ".gitmodules"
        declared_submodules = []
        if gitmodules.is_file():
            declared_submodules = [line.strip() for line in gitmodules.read_text(encoding="utf-8").splitlines() if line.strip().startswith("url")]
        results.append({"application_id": app["application_id"], "commit": app["commit"], "files_checked": len(inventory["files"]), "file_hash_failures": failures, "archive_hash_ok": sha256(app["archive"]) == app["archive_sha256"], "inventory_hash_ok": sha256(inventory_path) == app["inventory_sha256"], "declared_submodule_urls": declared_submodules, "submodules_acquired": False, "runtime_accepted": False})
        print(json.dumps({"verified": app["application_id"], "files": len(inventory["files"]), "failures": len(failures)}), flush=True)
    selected_repos = [canonical(app["repo"]) for app in original["applications"] + manifest["applications"]]
    native = {canonical(row["repo"]) for row in catalog["tasks"] if row.get("repo")}
    overlap = sorted(set(selected_repos) & native)
    preserved_prior = prior["passed"] and sha256(ORIGINAL / "source_acquisition_manifest.json") == prior["source_manifest_sha256"]
    passed = preserved_prior and all(row["archive_hash_ok"] and row["inventory_hash_ok"] and not row["file_hash_failures"] for row in results) and not overlap and len(set(selected_repos)) == len(selected_repos)
    assert sha256(manifest_path) == manifest_sha, "source manifest changed during verification"
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "scope": "additional archive/inventory/regular-file integrity and exact repository deduplication only; no build, model, or runtime execution", "passed": passed, "original_16_integrity_preserved_by_manifest_hash": preserved_prior, "original_integrity_report_sha256": sha256(ORIGINAL / "source_integrity_verification.json"), "source_manifest_sha256": manifest_sha, "additional_applications": len(results), "files_checked": sum(row["files_checked"] for row in results), "native_benchmark_rows": 200, "native_unique_repos": len(native), "exact_native_repository_overlap": overlap, "full_family_or_template_overlap_exclusion_proven": False, "applications": results}
    (ROOT / "source_integrity_verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("passed", "additional_applications", "files_checked", "exact_native_repository_overlap")}))
    assert passed
