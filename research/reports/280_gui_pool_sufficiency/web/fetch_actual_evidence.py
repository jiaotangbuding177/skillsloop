"""Fetch pinned public source documentation only, with bounded reads and hashes."""
import concurrent.futures, hashlib, json, pathlib, urllib.request
ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "evidence"; OUT.mkdir(exist_ok=True)
SHA = "59fe126f637d858c061e1eeedbef5436c8f2225a"
files = ["README.md", "LICENSE.txt", "LICENSE", "package.json", "CONTRIBUTING.md", "packages/desktop-client/package.json", "packages/loot-core/package.json", "packages/desktop-client/src/browser.tsx", "packages/desktop-client/src/components/ServerURL.tsx", "packages/desktop-client/src/components/modals/AddLocalAccountModal.tsx"]
def fetch(path):
    url = f"https://raw.githubusercontent.com/actualbudget/actual/{SHA}/{path}"
    result = {"path":path,"url":url}
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"PublicSourceResearch/1.0"}),timeout=30) as response: b=response.read(256*1024+1)
        if len(b)>256*1024: raise ValueError("public file exceeds read bound")
        saved = OUT / ("actualbudget__actual__"+path.replace("/","__"))
        saved.write_bytes(b)
        result.update({"status":"fetched","bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),"evidence":str(saved)})
    except Exception as e: result.update({"status":"read_failed","error_type":type(e).__name__})
    return result
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: results=list(pool.map(fetch,files))
(ROOT/"actual_fixed_source_evidence.json").write_text(json.dumps({"repo":"https://github.com/actualbudget/actual","release":"v26.9.0","commit":SHA,"model_called":False,"source_executed":False,"records":results},ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(results,ensure_ascii=False,indent=2))
