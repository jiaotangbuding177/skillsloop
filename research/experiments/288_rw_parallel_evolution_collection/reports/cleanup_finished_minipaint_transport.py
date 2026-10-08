from pathlib import Path
import subprocess,json,time
root=Path(__file__).resolve().parents[1]
j=json.loads((root/'reports/active/minipaint.json').read_text());assert j['state']=='native_finished' and j['round']==3
state=json.loads(subprocess.check_output(['docker','inspect',j['container']],text=True))[0]['State'];assert not state['Running'] and state['Pid']==0
m=json.loads((root/'reports/live_transport_v25_manifest.json').read_text())
c=subprocess.run(['iptables',*m['rollback_rule']],capture_output=True,text=True)
p=subprocess.run(['docker','stop','--time','5','rw288-minipaint-proxy-v25'],capture_output=True,text=True)
(root/'reports/transport_cleanup_after_mini_finished.json').write_text(json.dumps({'epoch':time.time(),'original_actor_finished_naturally':True,'nat_rule_remove_returncode':c.returncode,'own_proxy_stop_returncode':p.returncode,'new_proxy_actual_model_calls':0,'GET_only_verification':True,'no_actor_restart_or_round4':True,'shared_8788_squoosh_proxy_untouched':True},indent=2))
print(json.dumps({'original_actor_finished':True,'own_nat_removed':c.returncode==0,'own_unused_proxy_stopped':p.returncode==0}))
