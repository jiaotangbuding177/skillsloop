import hashlib,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent; out=root/'v2'; out.mkdir(exist_ok=True)
assert not (out/'status.json').exists(),'Diagnostic v2 already launched'
assert subprocess.check_output(['docker','inspect','--format','{{.State.Running}}','rw256-reference-selfcheck'],text=True).strip()=='false'
m=json.loads((root/'phase_manifest_v2.json').read_text()); assert hashlib.sha256((root/'entry_v2.py').read_bytes()).hexdigest()==m['entry_sha256']
raise SystemExit(subprocess.call(['docker','run','--name','rw256-reference-selfcheck-v2','--network','none','--mount',f'type=bind,src={root}/entry_v2.py,dst=/entry.py,readonly','--mount',f'type=bind,src={out},dst=/results',m['image'],'python3','/entry.py']))
