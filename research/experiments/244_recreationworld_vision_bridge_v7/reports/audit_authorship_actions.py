import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; s=json.loads((ROOT/'reports/pipeline_status.json').read_text())
raw=subprocess.check_output(['docker','exec','rw238-'+s['attempt'],'cat','/workspace/recreation/trajectory.jsonl'],text=True)
rows=[json.loads(x) for x in raw.splitlines()]; flagged=[]
for i,row in enumerate(rows):
 for b in row.get('message',{}).get('content',[]):
  if not isinstance(b,dict) or b.get('type')!='tool_use': continue
  value=json.dumps(b.get('input',{})); patterns=[x for x in ['outerHTML','innerHTML','className','getComputedStyle','getBoundingClientRect','querySelectorAll'] if x in value]
  if patterns: flagged.append({'record':i,'tool':b['name'],'patterns':patterns,'input':b.get('input')})
(ROOT/'reports/authorship_action_audit.json').write_text(json.dumps({'review_required':True,'flagged':flagged},indent=2))
print(json.dumps({'flagged_tools':len(flagged),'last_code':[x for x in flagged[-3:]]},ensure_ascii=False))
