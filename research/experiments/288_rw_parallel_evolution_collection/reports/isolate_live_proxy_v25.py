import json,subprocess,time,socket,hashlib,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1];attempt='minipaint_recreation_eval_1791129685783416430';name='rw288-'+attempt
j=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0];assert j['State']['Running'] and j['Id']=='c7a6ed9cc851e1cf70f68f2cee7ade9bec495455fee6fe53b580f4f82035c726'
pid=j['State']['Pid'];cg=Path(f'/proc/{pid}/cgroup').read_text().strip().split('0::',1)[1].lstrip('/');assert cg=='system.slice/docker-'+j['Id']+'.scope'
target=root/'reports/live_transport_v25_manifest.json';assert not target.exists()
with socket.socket() as s:s.bind(('127.0.0.1',8791))
proxy='rw288-minipaint-proxy-v25'
cmd=['docker','run','-d','--name',proxy,'--network','host','--memory','256m','--memory-swap','256m','--cpus','.5','-e','UPSTREAM_BASE_URL=http://127.0.0.1:8193/288/'+attempt+'/v1/chat/completions','-e','UPSTREAM_API_KEY=local','-e','GATEWAY_API_KEY=local','-e','DEFAULT_UPSTREAM_MODEL=deepseek-v4-flash-vision-exp','-e','FORCE_UPSTREAM_MODEL=true','-e','HOST=127.0.0.1','-e','PORT=8791','-e','UPSTREAM_TIMEOUT_SECONDS=1800','-e','LOG_PAYLOAD_MAX_CHARS=0','-e','PRETTY_LOGS=false','sha256:603d4b4f22fc32a7d0bb2e034db9f9afc1d5597f6116cfb35d2fa1e244d34c3d','/usr/local/bin/rb-claude-code-proxy']
rule=['-t','nat','-A','OUTPUT','-p','tcp','-d','127.0.0.1','--dport','8788','-m','cgroup','--path',cg,'-j','REDIRECT','--to-ports','8791']
manifest={'version':'rw_live_transport_isolation_v2.5','reason':'v24 second host-network proxy failed EADDRINUSE; readiness hit existing stateless proxy and route labels shared. Actor contexts/candidates and provider/model unchanged. Prevent first worker termination stopping second worker model channel.','attempt':attempt,'container_id':j['Id'],'controller_pid':129731,'controller_start_ticks':'1650539','full_model_round':3,'new_full_round':False,'actor_restart':False,'frozen_code_prompt_or_input_modified':False,'root_rule_only_matches_this_exact_container_cgroup_and_loopback_model_port':cg,'old_8788_proxy_and_other_experiments_untouched':True,'new_proxy_port':8791,'iptables_rule':rule,'rollback_rule':['-t','nat','-D',*rule[3:]],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'created_epoch':time.time(),'state':'prepared','existing_tcp_connections_not_killed':True}
target.write_text(json.dumps(manifest,indent=2));subprocess.run(cmd,check=True)
for _ in range(50):
 try:
  with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8791/v1/models',headers={'Authorization':'Bearer local'}),timeout=1) as r:assert r.status==200
  break
 except Exception:time.sleep(.2)
else:raise RuntimeError('Isolated proxy readiness failed; no rule applied')
subprocess.run(['iptables',*rule],check=True)
manifest.update(state='new_connections_isolated',applied_epoch=time.time());target.write_text(json.dumps(manifest,indent=2));print(json.dumps({'applied':True,'cgroup':cg,'proxy_port':8791,'actor_restarted':False,'full_round_remains':3,'existing_connections_drain_naturally':True}))
