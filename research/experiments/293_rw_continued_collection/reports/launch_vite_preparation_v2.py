import subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert not(ROOT/'reports/vite_reference_v2_preparation_manifest.json').exists()
p=subprocess.Popen(['python3',str(ROOT/'reports/prepare_vite_reference_v2.py')],stdin=subprocess.DEVNULL,stdout=(ROOT/'reports/vite_preparation_v2.log').open('ab'),stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'reference_preparation_v2_pid':p.pid,'minimum_available_mib':6144,'no_model_calls':True,'original_failure_preserved':True}))
