"""Check public tool receipts for blocked reference scripting/network attempts."""
import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]; s=json.loads((root/'reports/pipeline_status.json').read_text())
code=r'''
import json
from pathlib import Path
rows=[json.loads(x) for x in Path('/workspace/recreation/trajectory.jsonl').read_text().splitlines() if x]
uses=[]; pending={}
for row in rows:
 blocks=row.get('message',{}).get('content',[])
 if not isinstance(blocks,list): continue
 for b in blocks:
  if not isinstance(b,dict): continue
  if b.get('type')=='tool_use':
   name=b.get('name',''); command=b.get('input',{}).get('command','')
   if name.endswith('browser_evaluate') or name.endswith('browser_run_code') or (name=='Bash' and ('curl ' in command or 'wget ' in command)):
    item={'tool_id':b['id'],'name':name,'header_only':bool('curl ' in command and ' -I ' in command),'own_preview':('localhost:4173' in command or 'localhost:5173' in command),'command':command[:250]}; uses.append(item); pending[b['id']]=item
  if b.get('type')=='tool_result':
   content=b.get('content',''); texts=[content] if isinstance(content,str) else [x.get('text','') for x in content if isinstance(x,dict)] if isinstance(content,list) else []
   if b['tool_use_id'] in pending:
    pending.pop(b['tool_use_id']).update(is_error=b.get('is_error',False),receipt='\n'.join(texts)[:750])
print(json.dumps(uses))
'''
r=subprocess.run(['docker','exec','rw238-'+s['attempt'],'python3','-c',code],capture_output=True,text=True)
assert r.returncode==0,r.stderr[-500:]
data=json.loads(r.stdout); (root/'reports/blocked_call_receipts.json').write_text(json.dumps(data,indent=2))
print(json.dumps({'calls':len(data),'all_non_preview_denied':all(x['own_preview'] or 'disabled' in x.get('receipt','') or 'hook error' in x.get('receipt','').lower() for x in data)}))
