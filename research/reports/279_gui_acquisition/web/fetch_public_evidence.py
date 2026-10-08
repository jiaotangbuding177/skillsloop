"""Fetch public repository metadata and selected documentation only. No app execution."""
import concurrent.futures
import hashlib
import json
import pathlib
import urllib.request

OUT = pathlib.Path(__file__).resolve().parent / "evidence"
OUT.mkdir(parents=True, exist_ok=True)
REPOS = ["GoogleChromeLabs/squoosh", "Laverna/laverna", "parthlashkari/taskflow", "gchq/CyberChef", "benweet/stackedit", "viliusle/miniPaint"]

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "skillloop-public-research", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=35) as response:
        return response.read()

def one(repo):
    label = repo.replace("/", "__")
    record = {"repo": repo, "model_called": False, "application_executed": False, "files": []}
    try:
        meta = json.loads(get("https://api.github.com/repos/" + repo))
        commit = json.loads(get("https://api.github.com/repos/" + repo + "/commits/" + meta["default_branch"]))
        sha = commit["sha"]
        record.update({"sha": sha, "default_branch": meta["default_branch"], "github_size_kib": meta["size"], "license_metadata": meta.get("license"), "stars_at_fetch": meta.get("stargazers_count"), "commit_date": commit["commit"]["committer"]["date"], "archived": meta["archived"]})
        for name in ["README.md", "LICENSE", "LICENSE.txt", "package.json", "CONTRIBUTING.md"]:
            url = "https://raw.githubusercontent.com/" + repo + "/" + sha + "/" + name
            try:
                data = get(url)
                destination = OUT / (label + "__" + name.replace("/", "__"))
                destination.write_bytes(data)
                record["files"].append({"name": name, "url": url, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(), "path": str(destination)})
            except Exception as error:
                record.setdefault("file_errors", []).append({"name": name, "error_type": type(error).__name__})
    except Exception as error:
        record["error_type"] = type(error).__name__
        record["error"] = str(error)
    (OUT / (label + "__metadata.json")).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return {key: record.get(key) for key in ["repo", "sha", "github_size_kib", "stars_at_fetch", "archived", "license_metadata", "error_type"]}

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    results = list(pool.map(one, REPOS))
print(json.dumps(results, ensure_ascii=False, indent=2))
