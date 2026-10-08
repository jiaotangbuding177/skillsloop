import subprocess,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if (ROOT/'reports/completion_observer_identity.json').exists():raise RuntimeError('Observer already started')
p=subprocess.Popen(['python3',str(ROOT/'reports/watch_completion.py')],stdin=subprocess.DEVNULL,stdout=(ROOT/'reports/completion_observer.log').open('ab'),stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'observer_started':True,'pid':p.pid,'does_not_start_agent':True}))
