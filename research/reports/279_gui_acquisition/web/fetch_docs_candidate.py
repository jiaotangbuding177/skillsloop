"""Acquire fixed Vue docs public metadata/documents only, not runtime."""
import hashlib,json,pathlib,urllib.request
OUT=pathlib.Path(__file__).resolve().parent/"evidence"
def get(url):
 with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"skillloop-public-research"}),timeout=35) as r:return r.read()
repo="vuejs/docs"; label=repo.replace("/","__")
sha="40aa88af0094f7bab4aaf786e55c748a6a251d88"
record={"repo":repo,"sha":sha,"default_branch":"main","sha_evidence":"git ls-remote https://github.com/vuejs/docs.git refs/heads/main, exit 0","metadata_limitation":"GitHub unauthenticated API rate limited, use public git advertised SHA and raw fixed-commit files","model_called":False,"application_executed":False,"files":[]}
for name in ["README.md","LICENSE","LICENSE.md","package.json",".vitepress/config.ts"]:
 url="https://raw.githubusercontent.com/"+repo+"/"+sha+"/"+name
 try:
  data=get(url); path=OUT/(label+"__"+name.replace("/","__"));path.write_bytes(data)
  record["files"].append({"name":name,"url":url,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"path":str(path)})
 except Exception as error:record.setdefault("file_errors",[]).append({"name":name,"error_type":type(error).__name__})
(OUT/(label+"__metadata.json")).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(record,ensure_ascii=False,indent=2))
