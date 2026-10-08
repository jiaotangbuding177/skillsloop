"""Acquire bounded public source documentation at explicitly selected Git commits."""
import concurrent.futures as cf
import hashlib
import json
import pathlib
import urllib.request
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent
CANDIDATES = [
    ("HexFiend/HexFiend", "v2.18.1", "e2f91f1b7aff9a473c3b5aaf7c2e0cf3cb9e027e", ["README.md", "License.txt", "Makefile", ".gitmodules", "HexFiend.xcodeproj/project.pbxproj"]),
    ("sindresorhus/Gifski", "v2.23.0", "6fd12595617d1854c59f4ddca8e068fefa66c397", ["readme.md", "license", "contributing.md", "Gifski.xcodeproj/project.pbxproj"]),
    ("MacPass/MacPass", "0.8.2", "3256bc93ea94eb20b618c155e6a1b08e6fabe663", ["README.md", "LICENSE.txt", ".gitmodules", "Cartfile.resolved", "MacPass.xcodeproj/project.pbxproj"]),
    ("FossifyOrg/Gallery", "1.13.1", "b28299dc33821eee8d108a9880ce87876cf31443", ["README.md", "LICENSE", "app/build.gradle.kts", "app/src/main/AndroidManifest.xml"]),
    ("ramack/ActivityDiary", "v1.4.2", "22593ca02b897132c5649f1219aa93448dc18b06", ["README.md", "LICENSE", "app/build.gradle", "app/src/main/AndroidManifest.xml", "Privacy-Policy.md"]),
    ("michelesalvador/FamilyGem", "v1.3", "fc460b58fa4006df39501344c2c9ef0f34ec7aaf", ["README.md", "LICENSE.txt", "app/build.gradle", "app/src/main/AndroidManifest.xml"]),
]

def collect(candidate):
    repo, ref, sha, paths = candidate
    dest = ROOT / repo.replace("/", "__")
    dest.mkdir(parents=True, exist_ok=True)
    out = {"repo": repo, "repo_url": "https://github.com/" + repo, "selected_ref": ref, "fixed_sha": sha, "commit_source": "git ls-remote; annotated tags peeled to commit", "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "docs": []}
    for path in paths:
        url = "https://raw.githubusercontent.com/" + repo + "/" + sha + "/" + path
        item = {"source_path": path, "url": url}
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "skillloop-public-gui-research"})
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read(2 * 1024 * 1024 + 1)
            if len(body) > 2 * 1024 * 1024:
                raise ValueError("Documentation response exceeds bounded size")
            local = dest / path.replace("/", "__")
            local.write_bytes(body)
            item.update({"local_path": str(local), "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()})
        except Exception as error:
            item["error"] = type(error).__name__ + ": " + str(error)
        out["docs"].append(item)
    (dest / "fixed_docs_manifest.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"repo": repo, "sha": sha, "docs_ok": sum("sha256" in item for item in out["docs"]), "docs_total": len(paths)}), flush=True)
    return out

if __name__ == "__main__":
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(collect, CANDIDATES))
    (ROOT / "fixed_docs_manifest.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
