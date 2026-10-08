import json,subprocess,sys,time,os,fcntl,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 task=sys.argv[1];stage=sys.argv[2] if len(sys.argv)>2 else 'recreation_eval';assert task in ('minipaint','squoosh');assert stage in ('setup','eval','recreation_eval')
 lock=(ROOT/'private'/f'{task}.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (ROOT/'private/STOP').exists():raise RuntimeError('User STOP')
 cfg=json.loads((ROOT/'parallel_config.json').read_text());freeze=json.loads((ROOT/'reports'/f'freeze_{task}_v21.json').read_text())
 for n,d in freeze['files'].items():assert hashlib.sha256((ROOT/n).read_bytes()).hexdigest()==d,n
 active=ROOT/'reports/active';active.mkdir(exist_ok=True)
 if stage=='recreation_eval':
  for _ in range(7200):
   mem={k:int(v.split()[0]) for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())}
   others=[json.loads(p.read_text()) for p in active.glob('*.json')]
   if sum(x.get('state')=='running' for x in others)<2 and mem['MemAvailable']//1024>=2560:break
   time.sleep(5)
  else:raise RuntimeError('Resource gate timed out before model; no round allocated')
  budgetfile=ROOT/'private'/f'{task}_family_budget.json'
  if budgetfile.exists():
   assert task=='minipaint'
   proof=json.loads((ROOT/'reports/preagent_retry_proof.json').read_text());assert proof['safe_retry_same_round']
   token=ROOT/'private/minipaint_preagent_retry_once'
   fd=os.open(token,os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
  previous=1 if task=='minipaint' else 0;round_no=previous+1
  (ROOT/'private'/f'{task}_family_budget_v21.json').write_text(json.dumps({'family':task,'inherited_completed_rounds':previous,'round_allocated':round_no,'maximum_rounds':3,'allocated_epoch':time.time(),'no_reset_by_version':True}))
 else:round_no=None
 label=task+'_'+stage+'_'+str(time.time_ns());out=ROOT/'runs'/label;out.mkdir()
 image=cfg['runtime_image_id'];instance=task+'.training'
 cmd=['docker','run','--name','rw288-'+label,'--network','host','--memory','1280m','--memory-swap','1280m','--cpus','1','--pids-limit','640','--cap-add','SYS_ADMIN','--cap-add','NET_ADMIN','--security-opt','seccomp=unconfined','--mount',f'type=bind,src={ROOT}/datasets,dst=/var/lib/mockweb-scorer/download,readonly','--mount',f'type=bind,src={ROOT}/scripts_v21/container_entry.py,dst=/opt/rw288/container_entry.py,readonly','--mount',f'type=bind,src={ROOT}/scripts_v21/round_cli.py,dst=/opt/rw288/round_cli.py,readonly','--mount',f'type=bind,src={out},dst=/results','-e','RB_ARTIFACT_ROOT=/var/lib/mockweb-scorer/download','-e','RB_ARTIFACT_BACKEND=filesystem','-e','RB_UNIFIED_PREFIX=released','-e','RB_SCRIPTS_DIR=/workspace/RecreationBench/scripts','-e','RB_MODEL_API_KEY=local','-e','USE_VLM_JUDGE=false']
 if task=='minipaint' and stage=='recreation_eval':cmd.extend(['--mount',f'type=bind,src={ROOT}/checkpoints/minipaint/round1,dst=/previous-round,readonly'])
 cmd.extend([image,'python3','/opt/rw288/container_entry.py','--platform','web','--task-id',instance,'--stage',stage,'--agent-cli','claude','--api-mode','openai','--model',cfg['model_id'] if 'model_id' in cfg else 'deepseek-v4-flash-vision-exp','--model-base-url','http://127.0.0.1:8193/288/'+label+'/v1','--capture-tool-use-screenshots','true','--output-dir','/results'])
 if stage=='eval':cmd.extend(['--eval-target','reference'])
 record={'task':task,'stage':stage,'round':round_no,'attempt':label,'state':'running','pid':os.getpid(),'start_ticks':Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'container':'rw288-'+label,'memory_limit_mib':1280,'started_epoch':time.time(),'output':str(out)}
 report=(active/f'{task}.json') if stage=='recreation_eval' else ROOT/'reports'/f'{task}_{stage}.json';report.write_text(json.dumps(record,indent=2))
 with (out/'controller.log').open('w') as log:rc=subprocess.call(cmd,stdout=log,stderr=subprocess.STDOUT)
 scorefile=out/'recreation/eval_results/scores.json'
 if not scorefile.exists():scorefile=out/'eval_results/scores.json'
 scores=json.loads(scorefile.read_text()).get('scores',{}) if scorefile.exists() else None
 record.update(state='native_finished' if rc==0 else 'native_failure',returncode=rc,ended_epoch=time.time(),actual_score_file=str(scorefile) if scores else None,scores=scores,full_trajectory_acceptance='pending audit')
 report.write_text(json.dumps(record,indent=2));print(json.dumps(record))
if __name__=='__main__':main()
