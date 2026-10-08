"""Read-only safe progress inspection; no model payloads or credentials."""
import json
import subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
s = json.loads((ROOT / 'reports/pipeline_status.json').read_text())
name = 'rw238-' + s['attempt']
r = subprocess.run(['docker', 'exec', name, 'cat', '/workspace/recreation/trajectory.jsonl'], capture_output=True, text=True)
rows = [json.loads(x) for x in r.stdout.splitlines() if x.startswith('{')]
tools = [{'name': b.get('name'), 'description': b.get('input', {}).get('description', ''), 'file': b.get('input', {}).get('file_path', '')} for x in rows for b in x.get('message', {}).get('content', []) if isinstance(b, dict) and b.get('type') == 'tool_use']
sizes = subprocess.run(['docker', 'exec', name, 'stat', '-c', '%n %s', '/workspace/recreation/src/App.tsx', '/workspace/recreation/output/index.html'], capture_output=True, text=True)
rs = [json.loads(x.read_text()) for x in (ROOT / 'ledger').glob('*.json')]
rs = [x for x in rs if s['attempt'] in x.get('route', '')]
out = {'state': s['state'], 'records': len(rows), 'last_tools': tools[-3:], 'sizes': sizes.stdout.strip(), 'requests': len(rs), 'complete': sum(x.get('response_complete', False) for x in rs), 'terminal': [{k: x.get(k) for k in ('subtype', 'is_error', 'result')} for x in rows if x.get('type') == 'result']}
(ROOT / 'reports/live_snapshot.json').write_text(json.dumps(out, ensure_ascii=False, indent=2))
print(json.dumps(out, ensure_ascii=False))
