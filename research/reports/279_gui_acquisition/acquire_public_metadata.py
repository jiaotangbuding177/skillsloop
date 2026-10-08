"""Fetch only public RecreationBench source metadata, never evaluation assets."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parent
REV = "284341f8fc3d6680dd57ca5414fed92a0fe33b95"
PLATFORMS = ["ubuntu", "macos", "windows", "android", "web"]

def fetch(platform):
    url = f"https://huggingface.co/datasets/Qwen/RecreationBench/resolve/{REV}/metadata/{platform}.jsonl"
    request = urllib.request.Request(url, headers={"User-Agent": "skillloop-public-source-audit"})
    data = urllib.request.urlopen(request, timeout=45).read()
    rows = [json.loads(line) for line in data.splitlines() if line.strip()]
    assert len(rows) == 50
    output = []
    for row in rows:
        # Only source identity and public task identifiers; no evaluation paths.
        output.append({k: row[k] for k in ["instance_id", "platform", "difficulty", "repo", "commit"] if k in row})
    return platform, output, {"url": url, "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data), "rows": len(rows)}

if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(fetch, PLATFORMS))
    catalog = {"dataset": "Qwen/RecreationBench", "revision": REV, "scope": "public source identities only", "sources": {p: info for p, _, info in results}, "tasks": [row for _, rows, _ in results for row in rows]}
    assert len(catalog["tasks"]) == 250
    (ROOT / "bench_source_catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"tasks": 250, "output": str(ROOT / "bench_source_catalog.json"), "repo_values": sum(bool(r.get("repo")) for r in catalog["tasks"])}))
