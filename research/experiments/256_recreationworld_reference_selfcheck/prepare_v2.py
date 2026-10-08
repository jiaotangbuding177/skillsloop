import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
p=root/'entry.py'; text=p.read_text().replace("workspace=Path('/workspace/reference_selfcheck_256')","workspace=Path('/workspace/reference_selfcheck_256_v2')")
text=text.replace("cmd=['python3'","assert Path('/opt/mockweb-bench/batch_run/node_modules/@playwright/test/package.json').is_file()\ncmd=['python3'")
text=text.replace("'PYTHONPATH':'/workspace/RecreationBench/scripts'","'PYTHONPATH':'/workspace/RecreationBench/scripts','MOCKWEB_NODE_MODULES':'/opt/mockweb-bench/batch_run/node_modules'")
(root/'entry_v2.py').write_text(text); compile(text,'entry_v2.py','exec')
manifest=json.loads((root/'phase_manifest.json').read_text()); manifest.update(version='reference_selfcheck_v2',old_v1_setup_failure_preserved=True,official_worker_environment_restored=True,entry_sha256=hashlib.sha256((root/'entry_v2.py').read_bytes()).hexdigest())
(root/'phase_manifest_v2.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'version':manifest['version'],'model_called':False}))
