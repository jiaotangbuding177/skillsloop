import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]; s=json.loads((root/'reports/pipeline_status.json').read_text()); run=root/'runs'/s['attempt']
rows=[json.loads(x) for x in (run/'trajectory.jsonl').read_text().splitlines()]
tools=[{'name':b.get('name'),'description':b.get('input',{}).get('description'),'file':b.get('input',{}).get('file_path'),'url':b.get('input',{}).get('url')} for r in rows for b in r.get('message',{}).get('content',[]) if isinstance(b,dict) and b.get('type')=='tool_use']
errors=[{'type':r.get('type'),'subtype':r.get('subtype'),'is_error':r.get('is_error'),'characters':len(r.get('result') or '')} for r in rows if r.get('type')=='result']
print(json.dumps({'tools':tools[-25:],'terminal':errors,'records':len(rows)}))
