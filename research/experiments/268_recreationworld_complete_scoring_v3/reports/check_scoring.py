"""Read-only safe scoring and gateway progress summary."""
import json,time
from datetime import datetime
from pathlib import Path
root=Path(__file__).resolve().parents[1]
run=json.loads((root/'reports/current_run.json').read_text()); out=Path(run['path'])
status=json.loads((out/'evaluation_status.json').read_text()) if (out/'evaluation_status.json').exists() else {'state':'preparing'}
rows=[]
for p in (root.parent/'267_recreationworld_public_content_v17/ledger').glob('*.json'):
 try: r=json.loads(p.read_text())
 except (FileNotFoundError,json.JSONDecodeError): continue
 if '/268_recreationworld/complete_scoring/v3' not in r.get('route',''): continue
 if datetime.fromisoformat(r['started_at']).timestamp()<status.get('started_epoch',int(run['run'].rsplit('_',1)[1])/1e9): continue
 rows.append(r)
markers=[]
if (out/'scorer.log').exists():
 markers=[x for x in (out/'scorer.log').read_text().splitlines() if any(k in x for k in ['Dimension','VLM','ERROR','Server started','Server stopped'])][-8:]
value={'run':run['run'],'state':status['state'],'source_unchanged':status.get('source_unchanged'),'requests':len(rows),'complete':sum(bool(x.get('response_complete')) for x in rows),'failed':sum(x.get('api_outcome')=='transport_or_protocol_failure' for x in rows),'in_progress':sum(x.get('api_outcome')=='in_progress' for x in rows),'log_markers':markers,'native_result_available':(out/'native_vlm_result.json').exists()}
(root/'reports/scoring_snapshot.json').write_text(json.dumps(value,indent=2)); print(json.dumps(value))
