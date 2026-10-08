import subprocess,json,time,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1]
expr='( sport = :54448 and dport = :8788 )'
def sockets():return subprocess.check_output(['ss','-tnp',expr],text=True)
before=sockets();assert 'pid=130246' in before
cg='system.slice/docker-c7a6ed9cc851e1cf70f68f2cee7ade9bec495455fee6fe53b580f4f82035c726.scope'
assert cg in Path('/proc/130246/cgroup').read_text()
rule=['OUTPUT','-p','tcp','-d','127.0.0.1','--sport','54448','--dport','8788','-m','cgroup','--path',cg,'-j','REJECT','--reject-with','tcp-reset']
p=root/'reports/connection_reset_v251.json';assert not p.exists()
r={'version':'external_transport_v2.5.1','epoch':time.time(),'before_socket':before,'rule':rule,'reason':'ss -K returned zero but did not close socket; exact old connection to shared proxy is reset once, subsequent connections already have verified per-container NAT8791. No actor restart or new full round.','actor_restart':False,'model_round':3,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'state':'prepared'}
p.write_text(json.dumps(r,indent=2))
subprocess.run(['iptables','-A']+rule,check=True)
try:
    deadline=time.time()+50
    while time.time()<deadline and 'pid=130246' in sockets():time.sleep(.5)
    r.update(after_socket=sockets(),closed='pid=130246' not in sockets(),state='finished',epoch_end=time.time())
finally:
    subprocess.run(['iptables','-D']+rule,check=True)
    r['temporary_rule_removed']=True;p.write_text(json.dumps(r,indent=2))
print(json.dumps({'closed':r.get('closed'),'temporary_rule_removed':True,'actor_restart':False}))
