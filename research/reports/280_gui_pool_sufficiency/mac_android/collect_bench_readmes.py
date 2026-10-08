"""Collect public README evidence only. Never retrieves tests/evaluators or runs apps."""
from pathlib import Path
import json, urllib.request, hashlib, concurrent.futures
from datetime import datetime, timezone
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[1]
catalog=json.loads((ROOT/"279_gui_acquisition/bench_source_catalog.json").read_text(encoding="utf-8"))
rows=[t for t in catalog["tasks"] if t["platform"] in ("macos","android")]
def get(t):
    result={k:t[k] for k in ("instance_id","platform","repo","commit")}
    slug=t["repo"].removeprefix("https://github.com/").rstrip("/")
    errors=[]
    for filename in ["README.md","Readme.md","readme.md","README"]:
        url=f'https://raw.githubusercontent.com/{slug}/{t["commit"]}/{filename}'
        try:
            request=urllib.request.Request(url,headers={"User-Agent":"Public-Research-Source-Audit/1.0"})
            with urllib.request.urlopen(request,timeout=10) as response:
                content=response.read(524289)
            if len(content)>524288: raise ValueError("README exceeds bounded limit")
            out=BASE/"bench_readme_evidence"/(t["instance_id"].replace("/","__")+".md")
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_bytes(content)
            result.update({"readme_url":url,"readme_path":str(out),"readme_sha256":hashlib.sha256(content).hexdigest(),"bytes":len(content),"status":"readme_acquired"})
            return result
        except Exception as e:
            errors.append({"url":url,"error":str(e)})
            if "404" not in str(e): break
    result.update({"status":"public_readme_unavailable","errors":errors})
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    results=list(pool.map(get,rows))
out={"created_utc":datetime.now(timezone.utc).isoformat(),"scope":"Public source README documentation only; no private tests/evaluators","rows":results}
(BASE/"bench_readme_manifest.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"rows":len(results),"readmes":sum(r["status"]=="readme_acquired" for r in results),"unknown":sum(r["status"]!="readme_acquired" for r in results)},ensure_ascii=False))

