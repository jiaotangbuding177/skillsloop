"""Read-only safe progress inspection; no model payloads or credentials."""
import json
import subprocess
from urllib.parse import urlsplit
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
s = json.loads((ROOT / 'reports/pipeline_status.json').read_text())
name = 'rw238-' + s['attempt']
r = subprocess.run(['docker', 'exec', name, 'cat', '/workspace/recreation/trajectory.jsonl'], capture_output=True, text=True)
rows = [json.loads(x) for x in r.stdout.splitlines() if x.startswith('{')]
tools = [{'name': b.get('name'), 'description': b.get('input', {}).get('description', ''), 'file': b.get('input', {}).get('file_path', '')} for x in rows for b in x.get('message', {}).get('content', []) if isinstance(b, dict) and b.get('type') == 'tool_use']
sizes = subprocess.run(['docker', 'exec', name, 'stat', '-c', '%n %s', '/workspace/recreation/src/App.tsx', '/workspace/recreation/output/index.html'], capture_output=True, text=True)
rs = []; transient_reads=0
for receipt in (ROOT/'ledger').glob('*.json'):
 try: rs.append(json.loads(receipt.read_text()))
 except (FileNotFoundError,json.JSONDecodeError): transient_reads+=1
rs = [x for x in rs if s['attempt'] in x.get('route', '')]
navigation_paths=set(); edits=0
for row in rows:
 for block in row.get('message',{}).get('content',[]):
  if not isinstance(block,dict) or block.get('type')!='tool_use': continue
  if block.get('name') in ['Edit','Write']: edits+=1
  if block.get('name','').endswith('browser_navigate'):
   url=urlsplit(block.get('input',{}).get('url',''))
   if url.hostname in ['localhost','127.0.0.1'] and url.port not in [4173,5173]: navigation_paths.add(url.path)
out = {'state': s['state'], 'records': len(rows), 'last_tools': tools[-3:], 'reference_navigation_paths_attempted':sorted(navigation_paths),'write_edit_actions':edits,'sizes': sizes.stdout.strip(), 'requests': len(rs), 'complete': sum(x.get('response_complete', False) for x in rs), 'empty_visible_responses': sum(x.get('empty_visible_response', False) for x in rs), 'terminal': [{'subtype': x.get('subtype'), 'is_error': x.get('is_error'), 'result_characters': len(x.get('result') or ''), 'summary_output': '<summary>' in (x.get('result') or '')} for x in rows if x.get('type') == 'result']}
out['transient_receipt_reads']=transient_reads
(ROOT / 'reports/live_snapshot.json').write_text(json.dumps(out, ensure_ascii=False, indent=2))
print(json.dumps(out, ensure_ascii=False))
