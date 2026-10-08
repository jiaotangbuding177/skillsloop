import subprocess,json
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=subprocess.Popen(['python3',str(root/'reports/observe_parallel.py')],stdin=subprocess.DEVNULL,stdout=(root/'reports/observer.log').open('ab'),stderr=subprocess.STDOUT,start_new_session=True);print(json.dumps({'observer_launched_pid':p.pid,'interval_seconds':30,'no_model_rounds_generated':True}))
