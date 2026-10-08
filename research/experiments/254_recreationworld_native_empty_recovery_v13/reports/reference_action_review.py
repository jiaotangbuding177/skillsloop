"""Read-only public tool-action review; does not read private reasoning."""
import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=json.loads((root/'reports/pipeline_status.json').read_text())
raw=subprocess.check_output(['docker','exec','rw238-'+s['attempt'],'cat','/workspace/recreation/trajectory.jsonl'],text=True)
found=[]
for i,line in enumerate(raw.splitlines()):
 for b in json.loads(line).get('message',{}).get('content',[]):
  if not isinstance(b,dict) or b.get('type')!='tool_use' or b.get('name')!='Bash': continue
  inp=b.get('input',{}); c=inp.get('command','')
  if any(x in c for x in ['http://','https://','curl','wget','urllib','requests','httpx','fetch(','/tmp/styles.css','/tmp/ref','re.compile','BeautifulSoup','querySelector','outerHTML','innerHTML']):
   found.append({'record':i,'description':inp.get('description'),'command':c})
(root/'reports/reference_action_review.json').write_text(json.dumps(found,ensure_ascii=False,indent=2))
print(json.dumps({'review_actions':len(found),'descriptions':[x['description'] for x in found]},ensure_ascii=False))
