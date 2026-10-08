import hashlib,json,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parent
assert not (root/'status.json').exists(),'Diagnostic already launched'
name='rw238-recreation_eval_baseline_1791074955547341645'
assert subprocess.check_output(['docker','inspect','--format','{{.State.Running}}',name],text=True).strip()=='false'
image='skillloop-rw-reference:256-'+str(time.time_ns())
image_id=subprocess.check_output(['docker','commit',name,image],text=True).strip()
(root/'phase_manifest.json').write_text(json.dumps({'diagnostic_only':True,'official_reference_candidate':True,'agent_launched':False,'vlm_enabled':False,'network_disabled':True,'old_results_unchanged':True,'image':image_id,'entry_sha256':hashlib.sha256((root/'entry.py').read_bytes()).hexdigest()},indent=2))
raise SystemExit(subprocess.call(['docker','run','--name','rw256-reference-selfcheck','--network','none','--mount',f'type=bind,src={root}/entry.py,dst=/entry.py,readonly','--mount',f'type=bind,src={root},dst=/results',image,'python3','/entry.py']))
