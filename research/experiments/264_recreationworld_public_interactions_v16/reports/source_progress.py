"""Read model-owned source and public checklist only, never evaluator files."""
import hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]; s=json.loads((root/'reports/pipeline_status.json').read_text())
code="import hashlib,json; from pathlib import Path; w=Path('/workspace/recreation'); print(json.dumps({'files':{str(p.relative_to(w)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (w/'src').rglob('*') if p.is_file()},'checklist':(w/'public_behavior_checklist.md').read_text() if (w/'public_behavior_checklist.md').is_file() else None}))"
r=subprocess.run(['docker','exec','rw238-'+s['attempt'],'python3','-c',code],capture_output=True,text=True)
if r.returncode: print(json.dumps({'running':False})); raise SystemExit()
data=json.loads(r.stdout); before=json.loads((root/'private/recovery/recovery_manifest.json').read_text())['files']
changes=[n for n,sha in data['files'].items() if before.get(n)!=sha]
value={'attempt':s['attempt'],'changed_source_files':changes,'source_hashes':data['files'],'public_checklist_available':data['checklist'] is not None}
(root/'reports/source_progress.json').write_text(json.dumps(value,indent=2))
if data['checklist']: (root/'reports/public_behavior_checklist_observed.md').write_text(data['checklist'])
print(json.dumps({'changed_source_files':changes,'public_checklist_available':value['public_checklist_available']}))
