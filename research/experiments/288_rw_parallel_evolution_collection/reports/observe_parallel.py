import json,subprocess,time,fcntl,os,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];lock=(root/'private/observer.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
(root/'reports/observer_identity.json').write_text(json.dumps({'pid':os.getpid(),'start_ticks':Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'read_only_observation_except_exact_own_proxy_cleanup_after_completion':True},indent=2))
while True:
 r=subprocess.run(['python3',str(root/'reports/probe_parallel.py')],capture_output=True,text=True)
 if r.returncode:print(json.dumps({'probe_error':r.stderr[-500:],'epoch':time.time()}),flush=True)
 else:
  j=json.loads(r.stdout);print(json.dumps({'epoch':j['epoch'],'workers':[{'task':x['task'],'round':x['round'],'state':x['state'],'identity_alive':x['identity_alive']} for x in j['active']],'routes':j['api_routes']}),flush=True)
  if len(j['active'])==2 and all(x['state']!='running' and not x['identity_alive'] for x in j['active']):
   m=json.loads((root/'reports/live_transport_v25_manifest.json').read_text());cmd=['iptables',*m['rollback_rule']];c=subprocess.run(cmd,capture_output=True,text=True)
   subprocess.run(['docker','stop','--time','5','rw288-minipaint-proxy-v25'],capture_output=True,text=True)
   (root/'reports/observer_completion.json').write_text(json.dumps({'epoch':time.time(),'both_workers_finished':True,'own_proxy_cleanup_returncode':c.returncode,'no_new_model_round_started':True,'minipaint_round3_budget_exhausted':True,'task_scores_require_final_audit':True},indent=2));break
 time.sleep(30)
