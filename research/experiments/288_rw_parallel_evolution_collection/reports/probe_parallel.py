import json,hashlib,time,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
def alive(pid,ticks):
 try:return Path(f'/proc/{pid}/stat').read_text().split(') ',1)[1].split()[19]==str(ticks)
 except FileNotFoundError:return False
records=[]
for p in (root/'reports/active').glob('*.json'):
 j=json.loads(p.read_text());j['identity_alive']=alive(j['pid'],j['start_ticks']);r=subprocess.run(['docker','inspect',j['container']],capture_output=True,text=True)
 if r.returncode==0:
  x=json.loads(r.stdout)[0];j['container_state']={k:x['State'].get(k) for k in ['Status','Pid','OOMKilled','ExitCode']};j['actual_limits']={k:x['HostConfig'].get(k) for k in ['Memory','MemorySwap','NanoCpus']}
 records.append(j)
counts={}
for p in (root/'ledger').glob('*.json'):
 j=json.loads(p.read_text());a=counts.setdefault(j['route'],{'requests':0,'complete':0,'failed':0,'pending':0,'latest_started':None,'latest_complete':None});a['requests']+=1;done=bool(j.get('response_complete'));a['complete']+=done;a['failed']+=not done and j.get('api_outcome') not in (None,'started','in_progress','pending');a['pending']+=not done and j.get('api_outcome') in (None,'started','in_progress','pending');a['latest_started']=j.get('started_at')
 if done:a['latest_complete']=j.get('upstream_last_frame_at')
freezes={}
for p in (root/'reports').glob('freeze_*v2[234].json'):
 j=json.loads(p.read_text());bad=[n for n,h in j['files'].items() if not (root/n).is_file() or hashlib.sha256((root/n).read_bytes()).hexdigest()!=h];freezes[p.name]={'files':len(j['files']),'mismatches':bad}
mem={k:int(v.split()[0]) for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())}
report={'epoch':time.time(),'phase':'rw_parallel_evolution_v2.4','active':records,'api_routes':counts,'freeze_checks':freezes,'wsl_available_mib':mem['MemAvailable']//1024,'wsl_swap_used_mib':(mem['SwapTotal']-mem['SwapFree'])//1024,'maximum_workers':2,'per_family_rounds_max':3,'skills_learning_started':False,'benchmark_250_evaluation_started':False}
path=root/'reports/parallel_health_state.json';path.write_text(json.dumps(report,indent=2));(root/'reports/health_snapshots').mkdir(exist_ok=True);(root/'reports/health_snapshots'/f'{time.time_ns()}.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
