import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; s=json.loads((ROOT/'reports/pipeline_status.json').read_text()); raw=subprocess.check_output(['docker','exec','rw238-'+s['attempt'],'cat','/workspace/recreation/trajectory.jsonl'],text=True)
tools=[b for line in raw.splitlines() for b in json.loads(line).get('message',{}).get('content',[]) if isinstance(b,dict) and b.get('type')=='tool_use']
bash=[{'description':x.get('input',{}).get('description'),'command':x.get('input',{}).get('command','')[:1500]} for x in tools if x.get('name')=='Bash']
unsafe=[x for x in tools if any(t in x.get('name','') for t in ('browser_evaluate','browser_run_code'))]
print(json.dumps({'last_bash':bash[-3:],'scripted_browser_tools':len(unsafe)},ensure_ascii=False))
