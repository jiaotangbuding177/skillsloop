import sys,subprocess,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];task=sys.argv[1]
if (ROOT/'private'/f'{task}_family_budget_v23.json').exists():raise RuntimeError('Already allocated')
p=subprocess.Popen(['python3',str(ROOT/'scripts_v23/worker.py'),task],stdin=subprocess.DEVNULL,stdout=(ROOT/'reports'/f'{task}_launcher.log').open('ab'),stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'worker_controller_launched':task,'pid':p.pid,'max_parallel':2,'may_wait_for_memory_before_allocating_round':True}))
