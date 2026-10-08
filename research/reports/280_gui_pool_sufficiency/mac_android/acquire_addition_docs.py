from pathlib import Path
import json,urllib.request,hashlib,concurrent.futures
from datetime import datetime,timezone
BASE=Path(__file__).resolve().parent
items=[
{"id":"macos_today","repo":"trozware/To-Day","commit":"7d98f4ca02d630474cab88233b2d80b476ba6ca1","tag":"release-2.0","files":["README.md","LICENSE.md","Today.xcodeproj/project.pbxproj"]},
{"id":"android_opencalc","repo":"clementwzk/OpenCalc","commit":"e80aef9452992ce46b3931edd562cae567bb7a6f","tag":"v3.2.1","files":["README.md","LICENSE","app/build.gradle.kts","build.gradle.kts",".github/workflows/build.yml",".github/workflows/android.yml"]},
{"id":"android_shattered_pixel_dungeon","repo":"00-Evan/shattered-pixel-dungeon","commit":"e9defd0444c96d2fce3de5ec297c3398be8b7c55","tag":"v4.0.1","files":["README.md","LICENSE.txt","build.gradle","android/build.gradle","docs/getting-started-android.md","docs/getting-started-desktop.md"]},
{"id":"android_package_manager_v7","repo":"SmartPack/PackageManager","commit":"f13008b9204ce916fc9773b8ae52376db585457b","tag":"v7.0","files":["README.md","LICENSE","Credits.md","app/build.gradle","build.gradle","app/src/main/AndroidManifest.xml"]}
]
def fetch(task):
    row,path=task
    url=f'https://raw.githubusercontent.com/{row["repo"]}/{row["commit"]}/{path}'
    result={"candidate_id":row["id"],"repo":row["repo"],"commit":row["commit"],"tag":row["tag"],"source_path":path,"url":url}
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Public-Research-Source-Audit/1.0"})
        with urllib.request.urlopen(req,timeout=15) as response: content=response.read(2097153)
        if len(content)>2097152: raise ValueError("bounded public doc too large")
        dst=BASE/"addition_evidence"/row["id"]/path.replace("/","__")
        dst.parent.mkdir(parents=True,exist_ok=True)
        dst.write_bytes(content)
        result.update({"local_path":str(dst),"sha256":hashlib.sha256(content).hexdigest(),"bytes":len(content),"status":"acquired"})
    except Exception as e: result.update({"status":"unavailable","error":str(e)})
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
    results=list(pool.map(fetch,[(r,p) for r in items for p in r["files"]]))
(BASE/"addition_docs_manifest.json").write_text(json.dumps({"created_utc":datetime.now(timezone.utc).isoformat(),"items":items,"docs":results},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps({"docs":len(results),"acquired":sum(r["status"]=="acquired" for r in results),"failed":[{"id":r["candidate_id"],"path":r["source_path"],"error":r.get("error")} for r in results if r["status"]!="acquired"]},ensure_ascii=False))
