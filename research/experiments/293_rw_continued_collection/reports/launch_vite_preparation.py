import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert not(ROOT/'admission/vite_docs/preparation_identity.json').exists()
p=subprocess.Popen(['python3',str(ROOT/'reports/prepare_vite_reference.py')],stdin=subprocess.DEVNULL,stdout=(ROOT/'reports/vite_preparation.log').open('ab'),stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'reference_preparation_pid':p.pid,'minimum_available_mib':6144,'no_agent_or_model_calls':True}))
