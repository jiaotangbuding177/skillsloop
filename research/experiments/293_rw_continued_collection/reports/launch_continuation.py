import subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
assert not(ROOT/'reports/supervisor_identity.json').exists(),'Do not launch duplicate supervisor'
p=subprocess.Popen(['python3',str(ROOT/'reports/supervise_squoosh.py')],stdin=subprocess.DEVNULL,stdout=(ROOT/'reports/supervisor.log').open('ab'),stderr=subprocess.STDOUT,start_new_session=True)
print(json.dumps({'supervisor_launched_pid':p.pid,'remaining_scope':'Squoosh rounds2-3, max3 total','real_agent_start_requires_runtime_verification':True}))
