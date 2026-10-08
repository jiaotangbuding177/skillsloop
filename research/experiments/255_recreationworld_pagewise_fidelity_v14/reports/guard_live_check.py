import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]; s=json.loads((root/'reports/pipeline_status.json').read_text())
name='rw238-'+s['attempt']
r=subprocess.run(['docker','exec',name,'cat','/workspace/recreation/observation_guard_events.jsonl'],capture_output=True,text=True)
events=[json.loads(x) for x in r.stdout.splitlines() if x.startswith('{')]
rs=[json.loads(p.read_text()) for p in (root/'ledger').glob('*.json')]; rs=[x for x in rs if s['attempt'] in x.get('route','')]
result={'events':len(events),'pretool':sum(x['event']=='PreToolUse' for x in events),'blocked_tools':sum(x['event']=='PreToolUse' and x['blocked'] for x in events),'stop_blocks':sum(x['event']=='Stop' and x['blocked'] for x in events),'blocked_reasons':list(dict.fromkeys(x['reason'] for x in events if x['blocked'])),'actual_image_receipts':sum(x.get('image_transport',{}).get('recovered_image_blocks',0)>0 for x in rs),'last_request_complete':rs[-1].get('response_complete') if rs else None}
(root/'reports/guard_live_snapshot.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result))
