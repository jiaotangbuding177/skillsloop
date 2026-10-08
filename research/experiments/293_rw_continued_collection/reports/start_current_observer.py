import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert not(ROOT/'reports/current_observer_identity.json').exists()
p=subprocess.Popen(['python3',str(ROOT/'reports/observe_current.py')],stdin=subprocess.DEVNULL,stdout=(ROOT/'reports/current_observer.log').open('ab'),stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'read_only_observer_pid':p.pid,'no_model_calls_from_observer':True}))
