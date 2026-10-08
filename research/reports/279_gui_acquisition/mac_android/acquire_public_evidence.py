"""Public GitHub metadata/docs only; no build, install, or model call."""
import concurrent.futures as cf
import hashlib
import json
import pathlib
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
CANDIDATES = [
    ("coteditor/CotEditor", "5.0.9", ["README.md", "LICENSE", "Configurations/CodeSigning.xcconfig"]),
    ("HexFiend/HexFiend", None, ["README.md", "License.txt", "Makefile", ".gitmodules"]),
    ("sindresorhus/Gifski", "v2.23.0", ["readme.md", "license", "contributing.md"]),
    ("FossifyOrg/Gallery", None, ["README.md", "LICENSE", "app/build.gradle.kts", "app/src/main/AndroidManifest.xml"]),
    ("ramack/ActivityDiary", None, ["README.md", "LICENSE", "app/build.gradle", "app/src/main/AndroidManifest.xml", "Privacy-Policy.md"]),
    ("mtotschnig/MyExpenses", None, ["README.md", "LICENSE", "myExpenses/build.gradle.kts"]),
    ("michelesalvador/FamilyGem", None, ["README.md", "LICENSE.txt", "app/build.gradle", "app/src/main/AndroidManifest.xml"]),
]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "skillloop-public-gui-research", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()

def api(endpoint):
    return json.loads(fetch("https://api.github.com/" + endpoint))

def collect(candidate):
    repo, tag, docs = candidate
    dest = ROOT / repo.replace("/", "__")
    dest.mkdir(parents=True, exist_ok=True)
    out = {"repo": repo, "queried_at_utc": datetime.now(timezone.utc).isoformat(), "mode": "public_metadata_documents_only", "docs": []}
    try:
        meta = api("repos/" + repo)
        out.update({"canonical_repo": meta["full_name"], "repo_url": meta["html_url"], "fork": meta["fork"], "parent_repo": meta.get("parent", {}).get("full_name"), "source_repo": meta.get("source", {}).get("full_name"), "archived": meta["archived"], "repo_size_kib": meta["size"], "default_branch": meta["default_branch"], "pushed_at": meta["pushed_at"], "license_api": meta.get("license"), "language": meta["language"]})
        try:
            release = api("repos/" + repo + "/releases/" + ("tags/" + tag if tag else "latest"))
            chosen_ref = release["tag_name"]
            out["release"] = {key: release.get(key) for key in ["tag_name", "published_at", "html_url", "body"]}
            out["release_assets"] = [{key: a[key] for key in ["name", "size", "browser_download_url"]} for a in release.get("assets", [])]
        except Exception as error:
            chosen_ref = tag or meta["default_branch"]
            out["release_error"] = type(error).__name__ + ": " + str(error)
        commit = api("repos/" + repo + "/commits/" + chosen_ref)
        sha = commit["sha"]
        out.update({"selected_ref": chosen_ref, "fixed_sha": sha, "commit_url": commit["html_url"], "commit_date": commit["commit"]["committer"]["date"]})
        for doc in docs:
            url = "https://raw.githubusercontent.com/" + repo + "/" + sha + "/" + doc
            record = {"source_path": doc, "url": url}
            try:
                body = fetch(url)
                local = dest / doc.replace("/", "__")
                local.write_bytes(body)
                record.update({"local_file": str(local), "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
            except Exception as error:
                record["error"] = type(error).__name__ + ": " + str(error)
            out["docs"].append(record)
    except Exception as error:
        out["error"] = type(error).__name__ + ": " + str(error)
    (dest / "metadata.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: out.get(key) for key in ["repo", "fixed_sha", "selected_ref", "repo_size_kib", "archived", "error"]}), flush=True)
    return out

if __name__ == "__main__":
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(collect, CANDIDATES))
    (ROOT / "public_metadata_manifest.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
