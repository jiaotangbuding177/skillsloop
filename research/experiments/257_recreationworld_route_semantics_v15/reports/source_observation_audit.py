"""Read only observable file/tool paths; never extract private thinking."""
import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]; s=json.loads((root/'reports/pipeline_status.json').read_text())
raw=subprocess.check_output(['docker','exec','rw238-'+s['attempt'],'cat','/workspace/recreation/trajectory.jsonl'],text=True)
rows=[json.loads(x) for x in raw.splitlines()]
results={b.get('tool_use_id'):b for r in rows for b in r.get('message',{}).get('content',[]) if isinstance(b,dict) and b.get('type')=='tool_result'}
items=[]
for i,r in enumerate(rows):
 for b in r.get('message',{}).get('content',[]):
  if not isinstance(b,dict) or b.get('type')!='tool_use': continue
  inp=b.get('input',{}); c=inp.get('command','')
  if b.get('name')=='Bash' and any(x in inp.get('description','').lower() for x in ['read contact','read executive','text content','quick links']):
   items.append({'record':i,'description':inp.get('description'),'command':c,'blocked':bool(results.get(b.get('id'),{}).get('is_error'))})
(root/'reports/source_observation_audit.json').write_text(json.dumps(items,indent=2))
print(json.dumps(items))
