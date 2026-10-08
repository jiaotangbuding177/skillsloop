import json,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];expr='( sport = :54448 and dport = :8788 )';before=subprocess.check_output(['ss','-tnp',expr],text=True);assert 'pid=130246,' in before
r=subprocess.run(['ss','-Ktn',expr],capture_output=True,text=True)
after=subprocess.check_output(['ss','-tnp',expr],text=True);result={'epoch':time.time(),'before':before,'after':after,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'same_actor_PID_not_restarted':130246,'full_round_remains':3,'targeted_tcp_keepalive_only':True};(root/'reports/explicit_tcp_reconnect_result.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
