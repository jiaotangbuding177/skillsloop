"""Fixed-release public Vite docs evidence only; no app/build executed."""
import hashlib,json,pathlib,urllib.request
OUT=pathlib.Path(__file__).resolve().parent/"evidence"
repo="vitejs/vite"; sha="fdb2e6f63894d8c458c1778f3df77afe537f2bb2"; label="vitejs__vite"
record={"repo":repo,"commit":sha,"tag":"v8.0.7","tag_object":"c586b86831463860faecab589d8f4de283eae7de","sha_evidence":"git ls-remote public refs/tags/v8.0.7 peeled commit, exit 0","model_called":False,"application_executed":False,"files":[]}
for name in ["README.md","LICENSE","package.json","pnpm-workspace.yaml","docs/package.json","docs/.vitepress/config.ts","docs/.vitepress/config.mts","docs/index.md"]:
 url="https://raw.githubusercontent.com/"+repo+"/"+sha+"/"+name
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"skillloop-public-research"}),timeout=30) as r:data=r.read()
  path=OUT/(label+"__"+name.replace("/","__"));path.write_bytes(data)
  record["files"].append({"name":name,"url":url,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest(),"path":str(path)})
 except Exception as error:record.setdefault("file_errors",[]).append({"name":name,"error_type":type(error).__name__})
(OUT/(label+"__metadata.json")).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(record,ensure_ascii=False,indent=2))
