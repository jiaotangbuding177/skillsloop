"""Fetch fixed-commit public files and public source tree metadata only."""
import concurrent.futures, hashlib, json, pathlib, urllib.request
OUT = pathlib.Path(__file__).resolve().parent / "evidence"
JOBS = {
 "viliusle/miniPaint": {"sha":"a79733eb803fc97084ef0ee4faa96b031e69e1c0", "paths":["MIT-LICENSE.txt", "index.html", "webpack.config.js", "service-worker.js"]},
 "benweet/stackedit": {"sha":"6dce2a5e36b755a0c244522b48a06c91a2df0f59", "paths":["src/services/localDbSvc.js", "src/services/fileSvc.js", "src/services/workspaceSvc.js", "src/services/storageSvc.js", "config/index.js", "build/build.js"]},
 "GoogleChromeLabs/squoosh": {"sha":"e8d35e0fb66eb16eff6fe8fc773eabcbb7128de3", "paths":[".nvmrc", "lib/move-output.js", "src/sw.ts", "src/features/analytics.ts"]},
}
def request(url):
 with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"skillloop-public-research"}), timeout=35) as r: return r.read()
def one(item):
 repo, job = item; label=repo.replace("/","__"); records=[]
 for name in job["paths"]:
  url="https://raw.githubusercontent.com/"+repo+"/"+job["sha"]+"/"+name
  try:
   data=request(url); path=OUT/(label+"__"+name.replace("/","__")); path.write_bytes(data)
   records.append({"name":name,"url":url,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"path":str(path)})
  except Exception as error: records.append({"name":name,"error_type":type(error).__name__})
 try:
  tree=json.loads(request("https://api.github.com/repos/"+repo+"/git/trees/"+job["sha"]+"?recursive=1"))
  (OUT/(label+"__tree.json")).write_text(json.dumps(tree,ensure_ascii=False,indent=2),encoding="utf-8")
 except Exception as error: records.append({"tree_error":type(error).__name__})
 (OUT/(label+"__extra_manifest.json")).write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
 return {"repo":repo,"files":records}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: print(json.dumps(list(pool.map(one,JOBS.items())),ensure_ascii=False,indent=2))
