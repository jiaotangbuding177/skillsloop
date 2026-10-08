import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
run=json.loads((root/'reports/current_run.json').read_text()); out=Path(run['path'])
meta=json.loads((out/'phase_manifest.json').read_text())
code="import os,json; from pathlib import Path; p=Path('/workspace/recreation/node_modules'); print(json.dumps({'link':os.readlink(p) if p.is_symlink() else None,'exists':p.is_dir(),'dependency_complete_markers':[str(x) for x in Path('/workspace/shared').glob('mockweb-template-deps/*/.complete')],'template_lock_present':Path('/workspace/RecreationBench/scripts/web/template/package-lock.json').is_file()}))"
r=subprocess.run(['docker','run','--rm','--network','none','--entrypoint','python3',meta['frozen_image_id'],'-c',code],capture_output=True,text=True,check=True)
value=json.loads(r.stdout); (root/'reports/build_dependency_diagnosis.json').write_text(json.dumps(value,indent=2)); print(json.dumps(value))
