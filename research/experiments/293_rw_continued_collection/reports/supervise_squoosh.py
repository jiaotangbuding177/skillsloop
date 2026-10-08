"""Continue only Squoosh's remaining budget; persist read-only health evidence."""
import fcntl, hashlib, json, os, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'288_rw_parallel_evolution_collection'
def write(name,data):
 p=ROOT/'reports'/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(data,indent=2));t.replace(p)
def snapshot(round_no):
 path=ROOT/'reports/active/squoosh.json'
 if not path.exists():return
 j=json.loads(path.read_text());out=Path(j['output']);trace=out/'recreation/trajectory.jsonl'
 view={'epoch':time.time(),'round':round_no,'actor':j,'skills_learning_started':False,'benchmark_250_evaluation_started':False}
 if trace.exists():
  b=trace.read_bytes();view['trace']={'bytes':len(b),'lines':b.count(b'\n'),'mtime':trace.stat().st_mtime,'trailing_partial':bool(b and not b.endswith(b'\n'))}
 r=subprocess.run(['docker','inspect',j['container']],capture_output=True,text=True)
 if r.returncode==0:
  c=json.loads(r.stdout)[0];view['container']={k:c['State'].get(k) for k in ('Status','Pid','OOMKilled','ExitCode')};view['limits']={k:c['HostConfig'].get(k) for k in ('Memory','MemorySwap','NanoCpus')}
 records=[]
 for p in (OLD/'ledger').glob('*.json'):
  try:x=json.loads(p.read_text())
  except (FileNotFoundError,json.JSONDecodeError):continue
  if x.get('route','').startswith('/293/'+j['attempt']+'/'):records.append(x)
 view['api']={'requests':len(records),'complete':sum(bool(x.get('response_complete')) for x in records),
 'failed':sum(x.get('api_outcome')=='transport_or_protocol_failure' for x in records),
 'pending':sum(x.get('api_outcome')=='in_progress' for x in records),
 'image_transport_blocks':sum(x.get('image_transport',{}).get('recovered_image_blocks',0) for x in records)}
 write('health_state.json',view)
def main():
 lock=(ROOT/'private/supervisor.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 write('supervisor_identity.json',{'pid':os.getpid(),'start_ticks':Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'started_epoch':time.time(),'scope':'Squoosh rounds2-3 only; no fourth round, no learning, no250 evaluation'})
 for round_no in (2,3):
  if (ROOT/'private/STOP').exists() or (OLD/'private/STOP').exists():raise RuntimeError('STOP')
  if round_no==3:
   prior=json.loads((ROOT/'reports/active/squoosh.json').read_text());s=prior.get('scores')
   if prior['state']!='native_finished' or not s:
    write('continuation_status.json',{'state':'waiting_terminal_admission','actor':prior,'no_automatic_retry':True});return
   if s['dimension_details']['functional']['passed']==6 and s['visual_ssim_score']>=.85:
    write('continuation_status.json',{'state':'verifier_metrics_sufficient_pending_final_audit','actor':prior,'no_further_round':True});return
   subprocess.run(['python3',str(ROOT/'scripts/prepare_checkpoint.py'),prior['output'],'3'],check=True)
   subprocess.run(['python3',str(ROOT/'scripts/prepare_phase.py'),'3'],check=True)
  for _ in range(7200):
   if (ROOT/'private/STOP').exists() or (OLD/'private/STOP').exists():raise RuntimeError('STOP')
   mem={k:int(v.split()[0]) for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())}
   if mem['MemAvailable']//1024>=5120:break
   write('continuation_status.json',{'epoch':time.time(),'state':'waiting_resource','next_round':round_no,'available_mib':mem['MemAvailable']//1024});time.sleep(30)
  else:raise RuntimeError('Resource wait exhausted; no extra round allocated')
  with (ROOT/'reports'/f'round{round_no}_controller.log').open('a') as log:
   p=subprocess.Popen(['python3',str(ROOT/'scripts/worker.py'),str(round_no)],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
   while p.poll() is None:
    try:snapshot(round_no)
    except Exception as exc:write('observer_last_error.json',{'epoch':time.time(),'error_class':type(exc).__name__})
    time.sleep(30)
  snapshot(round_no)
  if p.returncode!=0:
   write('continuation_status.json',{'epoch':time.time(),'state':'worker_failed_no_automatic_retry','round':round_no,'returncode':p.returncode});return
 write('continuation_status.json',{'epoch':time.time(),'state':'three_round_budget_exhausted','last_actor':json.loads((ROOT/'reports/active/squoosh.json').read_text()),'no_fourth_round':True,'canonical_audit':'pending'})
if __name__=='__main__':
 try:main()
 except Exception as exc:
  write('continuation_status.json',{'epoch':time.time(),'state':'supervisor_failure_preserved','error_class':type(exc).__name__,'no_automatic_retry':True});raise
