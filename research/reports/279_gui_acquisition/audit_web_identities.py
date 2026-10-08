"""Inspect public reference landing-page identity only, never hidden tests."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from html.parser import HTMLParser
from datetime import datetime, timezone
import hashlib
import json
import urllib.request

ROOT = Path(__file__).resolve().parent
REV = "284341f8fc3d6680dd57ca5414fed92a0fe33b95"
PREVIOUS = {}
previous_report = ROOT / "web_bench_identity_audit.json"
if previous_report.exists():
    for item in json.loads(previous_report.read_text(encoding="utf-8"))["identities"]:
        if item["status"] == "identity_inspected":
            PREVIOUS[item["task_id"]] = item

class IdentityParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = []
        self.identity_links = []
        self.github_links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "link" and attrs.get("rel") == "canonical":
            self.identity_links.append(attrs.get("href", ""))
        if tag == "meta" and attrs.get("property") in ("og:url", "og:site_name"):
            self.identity_links.append(attrs.get("content", ""))
        if tag == "a" and "github.com/" in attrs.get("href", ""):
            self.github_links.append(attrs["href"])
    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)

def inspect(row):
    task_id = row["instance_id"].removeprefix("web/")
    if task_id in PREVIOUS:
        return PREVIOUS[task_id]
    relative = f"web/{task_id}/reference/site/index.html"
    url = f"https://huggingface.co/datasets/Qwen/RecreationBench/resolve/{REV}/{relative}"
    result = {"task_id": task_id, "public_source_url": url, "scope": "identity from public landing page only"}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "skillloop-public-source-identity-audit"}), timeout=30) as response:
            data = response.read(32 * 1024 * 1024 + 1)
        if len(data) > 32 * 1024 * 1024:
            raise ValueError("public landing page over identity inspection limit")
        parser = IdentityParser()
        parser.feed(data.decode("utf-8", errors="replace"))
        result.update({"status": "identity_inspected", "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "title": " ".join(parser.title).strip(), "identity_links": sorted(set(parser.identity_links)), "github_links": sorted(set(parser.github_links))})
    except Exception as error:
        result.update({"status": "identity_unresolved", "error": f"{type(error).__name__}: {error}"})
    return result

if __name__ == "__main__":
    catalog = json.loads((ROOT / "bench_source_catalog.json").read_text(encoding="utf-8"))
    rows = [r for r in catalog["tasks"] if r["platform"] == "web"]
    filenames = {s["rfilename"] for s in json.loads((ROOT.parents[0] / "233_trajectory_audit" / "hf_dataset_info.json").read_text(encoding="utf-8"))["siblings"]}
    assert all(f"web/{r['instance_id'].removeprefix('web/')}/reference/site/index.html" in filenames for r in rows)
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(inspect, rows))
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "revision": REV, "evaluation_assets_accessed": False, "full_html_persisted": False, "identities": results, "summary": {"total": len(rows), "inspected": sum(r["status"] == "identity_inspected" for r in results)}}
    (ROOT / "web_bench_identity_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"]))
    for result in results:
        print(json.dumps({k:result[k] for k in ["task_id", "status", "title", "identity_links", "github_links", "error"] if k in result}, ensure_ascii=False))
