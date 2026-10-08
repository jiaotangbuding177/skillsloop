"""Read public compatibility metadata without running any source."""
import hashlib, json, pathlib, urllib.request
ROOT = pathlib.Path(__file__).resolve().parent
SOURCES = [
    ("michelesalvador/FamilyGem", "v1.1", "a1d460657a93a535b5e32c7b466e5c2037db93d7", ["README.md", "LICENSE.txt", "app/build.gradle", "build.gradle", "app/src/main/AndroidManifest.xml"]),
    ("michelesalvador/FamilyGem", "v1.2", "3aeb97f00cfe6b8f8efbb5c0164529f0a0e16c62", ["README.md", "LICENSE.txt", "app/build.gradle", "build.gradle", "app/src/main/AndroidManifest.xml"]),
    ("FossifyOrg/Gallery", "1.13.1", "b28299dc33821eee8d108a9880ce87876cf31443", ["gradle/libs.versions.toml", "gradle.properties"]),
    ("HexFiend/HexFiend", "v2.18.1", "e2f91f1b7aff9a473c3b5aaf7c2e0cf3cb9e027e", ["Hex Fiend.xcodeproj/project.pbxproj", ".github/workflows/CI.yml"]),
]
records=[]
for repo, tag, sha, paths in SOURCES:
    dest=ROOT/(repo.replace("/", "__")+"__"+tag)
    dest.mkdir(parents=True,exist_ok=True)
    record={"repo":repo,"selected_ref":tag,"fixed_sha":sha,"docs":[]}
    for path in paths:
        url="https://raw.githubusercontent.com/"+repo+"/"+sha+"/"+path.replace(" ","%20")
        item={"source_path":path,"url":url}
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"skillloop-public-gui-research"}),timeout=30) as response: body=response.read(2*1024*1024+1)
            if len(body)>2*1024*1024: raise ValueError("too large")
            local=dest/path.replace("/","__")
            local.write_bytes(body)
            item.update({"local_path":str(local),"bytes":len(body),"sha256":hashlib.sha256(body).hexdigest()})
        except Exception as error: item["error"]=str(error)
        record["docs"].append(item)
    records.append(record)
    print(json.dumps({"repo":repo,"tag":tag,"docs_ok":sum("sha256" in d for d in record["docs"])}),flush=True)
(ROOT/"compatibility_docs_manifest.json").write_text(json.dumps(records,indent=2),encoding="utf-8")
