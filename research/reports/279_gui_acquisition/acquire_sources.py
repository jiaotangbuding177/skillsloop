"""Acquire pinned public source archives without running upstream code."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
import hashlib
import json
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parent
MAX_ARCHIVE_BYTES = 150 * 1024 * 1024
MAX_EXPANDED_BYTES = 600 * 1024 * 1024
PREVIOUS = {}
previous_manifest = ROOT / "source_acquisition_manifest.json"
if previous_manifest.exists():
    for previous in json.loads(previous_manifest.read_text(encoding="utf-8"))["applications"]:
        PREVIOUS[(canonical := previous["repo"].lower().rstrip("/"), previous["commit"])] = previous

def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def canonical_repo(url):
    return url.removesuffix(".git").rstrip("/").lower()

def acquire(candidate):
    repo = candidate["repo"].rstrip("/").removesuffix(".git")
    owner, name = repo.split("github.com/", 1)[1].split("/")
    commit = candidate["commit"]
    assert len(commit) == 40 and all(c in "0123456789abcdef" for c in commit.lower())
    previous = PREVIOUS.get((repo.lower(), commit))
    if previous and previous.get("status") == "source_acquired_not_executed":
        if sha256(Path(previous["archive"])) == previous["archive_sha256"] and sha256(Path(previous["inventory"])) == previous["inventory_sha256"]:
            return previous
    key = f"{candidate['platform']}--{owner}--{name}"
    archive = ROOT / "archives" / f"{key}--{commit}.tar.gz"
    source_root = (ROOT / "sources" / f"{key}--{commit[:12]}").resolve()
    archive.parent.mkdir(parents=True, exist_ok=True)
    source_root.mkdir(parents=True, exist_ok=True)
    url = f"https://codeload.github.com/{owner}/{name}/tar.gz/{commit}"
    result = {"application_id": key, "platform": candidate["platform"], "repo": repo, "commit": commit, "source_url": url}
    try:
        if not archive.exists():
            pending = archive.with_suffix(".pending")
            size = 0
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "skillloop-source-acquisition"}), timeout=60) as response, pending.open("wb") as output:
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    size += len(block)
                    if size > MAX_ARCHIVE_BYTES:
                        raise ValueError("archive exceeds per-source acquisition limit")
                    output.write(block)
            pending.replace(archive)
        files = []
        skipped_links = []
        expanded_bytes = 0
        with tarfile.open(archive, "r:gz") as package:
            for member in package:
                parts = PurePosixPath(member.name).parts
                relative = Path(*parts[1:])
                if not parts or len(parts) < 2 or any(p in ("..", ".") for p in parts) or parts[0].startswith("/"):
                    if member.isdir():
                        continue
                    raise ValueError("unsafe archive path")
                target = (source_root / relative).resolve()
                if not target.is_relative_to(source_root):
                    raise ValueError("archive path escapes intended source directory")
                if member.issym() or member.islnk():
                    skipped_links.append(str(relative).replace("\\", "/"))
                    continue
                if not member.isfile():
                    continue
                expanded_bytes += member.size
                if expanded_bytes > MAX_EXPANDED_BYTES:
                    raise ValueError("expanded source exceeds acquisition limit")
                target.parent.mkdir(parents=True, exist_ok=True)
                content = package.extractfile(member)
                h = hashlib.sha256()
                with target.open("wb") as output:
                    for block in iter(lambda: content.read(1024 * 1024), b""):
                        h.update(block)
                        output.write(block)
                files.append({"path": str(relative).replace("\\", "/"), "bytes": member.size, "sha256": h.hexdigest()})
        inventory_path = ROOT / "inventories" / f"{key}--{commit[:12]}.json"
        inventory_path.parent.mkdir(parents=True, exist_ok=True)
        inventory_path.write_text(json.dumps({"repo": repo, "commit": commit, "files": files, "skipped_links": skipped_links}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result.update({"status": "source_acquired_not_executed", "archive": str(archive), "archive_bytes": archive.stat().st_size, "archive_sha256": sha256(archive), "source_directory": str(source_root), "regular_files": len(files), "expanded_bytes": expanded_bytes, "skipped_links": len(skipped_links), "inventory": str(inventory_path), "inventory_sha256": sha256(inventory_path), "runtime_accepted": False})
    except Exception as error:
        result.update({"status": "acquisition_failed", "error": f"{type(error).__name__}: {error}"})
    return result

if __name__ == "__main__":
    candidates = json.loads((ROOT / "selected_candidates.json").read_text(encoding="utf-8"))
    if isinstance(candidates, dict):
        candidates = candidates["candidates"]
    bench = json.loads((ROOT / "bench_source_catalog.json").read_text(encoding="utf-8"))
    forbidden = {canonical_repo(row["repo"]) for row in bench["tasks"] if row.get("repo")}
    candidate_repos = [canonical_repo(row["repo"]) for row in candidates]
    assert len(set(candidate_repos)) == len(candidate_repos), "duplicate application family in selected pool"
    assert not set(candidate_repos) & forbidden, "selected source appears in held-out benchmark"
    with ThreadPoolExecutor(max_workers=4) as pool:
        acquired = list(pool.map(acquire, candidates))
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "purpose": "paper-inspired independent application source pool; no model rollout", "benchmark_revision": bench["revision"], "canonical_repo_overlap_with_200_native_sources": [], "web_snapshot_alias_review": "see selection report; web metadata has no repository values", "applications": acquired, "summary": {"selected": len(candidates), "acquired": sum(r["status"] == "source_acquired_not_executed" for r in acquired), "archive_bytes": sum(r.get("archive_bytes", 0) for r in acquired), "regular_files": sum(r.get("regular_files", 0) for r in acquired)}}
    (ROOT / "source_acquisition_manifest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"]))
    for item in acquired:
        print(json.dumps({k: item[k] for k in ["application_id", "status", "archive_bytes", "regular_files", "error"] if k in item}))
