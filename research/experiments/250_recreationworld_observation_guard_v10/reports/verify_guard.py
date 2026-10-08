import importlib.util,json,py_compile,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('guard',root/'observation_guard.py'); g=importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
cases=[('Bash',{'command':'curl -s http://localhost:35963/about/'},True),('Bash',{'command':'python3 -c "import urllib.request; urllib.request.urlopen(url)"'},True),('Bash',{'command':'npm run build'},False),('Bash',{'command':'curl http://localhost:4173/about/'},False),('Bash',{'command':'python3 /opt/rw218/asset_fetch.py http://localhost:35963/logo.png /workspace/recreation/public/logo.png'},False),('mcp__playwright__browser_evaluate',{'function':'()=>document.body.innerHTML'},True),('mcp__playwright__browser_run_code',{'code':'async page=>page.evaluate(()=>document.body)'},True),('mcp__playwright__browser_navigate',{'url':'http://localhost:35963/'},False),('mcp__playwright__browser_take_screenshot',{},False),('Write',{'file_path':'/workspace/recreation/src/App.tsx','content':'app'},False)]
results=[]
for name,inp,blocked in cases:
 actual=bool(g.decide({'hook_event_name':'PreToolUse','tool_name':name,'tool_input':inp}))
 assert actual==blocked,(name,inp)
 results.append({'tool':name,'expected_blocked':blocked,'passed':True})
for p in root.glob('*.py'): py_compile.compile(str(p),doraise=True)
(root/'reports/guard_fixture_admission.json').write_text(json.dumps({'passed':True,'cases':results},indent=2))
print(json.dumps({'passed':True,'cases':len(results)}))
