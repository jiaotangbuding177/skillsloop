"""Safe tool-result diagnostics, excluding model text and image payloads."""
import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=json.loads((root/'reports/pipeline_status.json').read_text())
r=subprocess.run(['docker','exec','rw238-'+s['attempt'],'cat','/workspace/recreation/trajectory.jsonl'],capture_output=True,text=True)
rows=[json.loads(x) for x in r.stdout.splitlines() if x.startswith('{')]
names={}; counts={}; categories={}
for row in rows:
 for b in row.get('message',{}).get('content',[]):
  if not isinstance(b,dict): continue
  if b.get('type')=='tool_use': names[b['id']]=b['name']
  if b.get('type')!='tool_result': continue
  name=names.get(b.get('tool_use_id'),'unknown'); counts[name]=counts.get(name,0)+1
  c=b.get('content',[]); text=c if isinstance(c,str) else '\n'.join(x.get('text','') for x in c if isinstance(x,dict))
  for category,pattern in [('unknown_tool','No such tool'),('tool_error','is_error'),('hook_block','blocked'),('timeout','Timeout')]:
   if (category=='tool_error' and b.get('is_error')) or (category!='tool_error' and pattern.lower() in text.lower()):
    key=name+':'+category; categories[key]=categories.get(key,0)+1
out={'tool_results_by_name':counts,'error_categories':categories,'payloads_not_exported':True}
(root/'reports/tool_health.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out))
