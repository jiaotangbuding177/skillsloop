"""One Squoosh correction round with cross-version canonical budget guard."""
import fcntl,hashlib,json,os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'288_rw_parallel_evolution_collection'
def alive(j):
 try:return Path('/proc/sys/kernel/random/boot_id').read_text().strip()==j['boot_id'] and Path(f"/proc/{j['pid']}/stat").read_text().split(') ',1)[1].split()[19]==j['start_ticks']
 except (FileNotFoundError,KeyError):return False
def main():
 round_no=int(sys.argv[1]);assert round_no in (2,3),'Only remaining Squoosh rounds permitted'
 lock=(OLD/'private/squoosh.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not(OLD/'private/STOP').exists() and not(ROOT/'private/STOP').exists()
 freeze_path=ROOT/'reports'/f'freeze_squoosh_round{round_no}.json';freeze=json.loads(freeze_path.read_text())
 for p,d in freeze['files'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==d,p
 budgets=[json.loads(p.read_text())['round_allocated'] for r in (OLD,ROOT) for p in (r/'private').glob('squoosh_family_budget*.json')]
 previous=max(budgets,default=0);assert previous==round_no-1 and previous<3,'No duplicate or version reset'
 cp=ROOT/'checkpoints/squoosh'/f'round{previous}';feedback=json.loads((cp/'feedback.json').read_text());assert feedback['round']==round_no
 for n,d in json.loads((cp/'checkpoint_manifest.json').read_text())['files'].items():assert hashlib.sha256((cp/n).read_bytes()).hexdigest()==d
 with socket.socket() as sock:sock.bind(('127.0.0.1',8793))
 health=json.load(urllib.request.urlopen('http://127.0.0.1:8193/health',timeout=3));assert health['model']=='deepseek-v4-flash-vision-exp'
 records=[json.loads(p.read_text()) for r in (OLD,ROOT) for p in (r/'reports/active').glob('*.json')]
 assert sum(alive(j) for j in records)<2,'Maximum two live workers'
 mem={k:int(v.split()[0]) for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())}
 assert mem['MemAvailable']//1024>=5120,'Need 5GiB available for 3GiB worker'
 (ROOT/'private'/f'squoosh_family_budget_round{round_no}.json').write_text(json.dumps({'family':'squoosh','inherited_completed_rounds':previous,'round_allocated':round_no,'maximum_rounds':3,'allocated_epoch':time.time(),'no_reset_by_version':True}))
 label='squoosh_recreation_eval_'+str(time.time_ns());out=ROOT/'runs'/label;out.mkdir(parents=True)
 cfg=json.loads((OLD/'parallel_config.json').read_text())
 cmd=['docker','run','--name','rw293-'+label,'--network','host','--memory','3072m','--memory-swap','3072m','--cpus','2','--pids-limit','640','--cap-add','SYS_ADMIN','--cap-add','NET_ADMIN','--security-opt','seccomp=unconfined']
 for src,dst,ro in ((OLD/'datasets_v23','/var/lib/mockweb-scorer/download',True),(ROOT/'scripts/container_entry.py','/opt/rw293/container_entry.py',True),(ROOT/'scripts/round_cli.py','/opt/rw293/round_cli.py',True),(cp,'/previous-round',True),(out,'/results',False)):
  cmd+=['--mount',f'type=bind,src={src},dst={dst}'+(',readonly' if ro else '')]
 for option in ('RB_ARTIFACT_ROOT=/var/lib/mockweb-scorer/download','RB_ARTIFACT_BACKEND=filesystem','RB_UNIFIED_PREFIX=released','RB_SCRIPTS_DIR=/workspace/RecreationBench/scripts','RB_MODEL_API_KEY=local','USE_VLM_JUDGE=false'):cmd+=['-e',option]
 cmd+=[cfg['runtime_image_id'],'python3','/opt/rw293/container_entry.py','--platform','web','--task-id','squoosh.training','--stage','recreation_eval','--agent-cli','claude','--api-mode','openai','--model','deepseek-v4-flash-vision-exp','--model-base-url','http://127.0.0.1:8193/293/'+label+'/v1','--capture-tool-use-screenshots','true','--output-dir','/results']
 record={'task':'squoosh','round':round_no,'parent_attempt':feedback['parent_attempt'],'attempt':label,'state':'running','pid':os.getpid(),'start_ticks':Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'container':'rw293-'+label,'started_epoch':time.time(),'output':str(out),'memory_limit_mib':3072,'model_proxy_port':8793,'freeze':str(freeze_path)}
 active=ROOT/'reports/active';active.mkdir(exist_ok=True);target=active/'squoosh.json';target.write_text(json.dumps(record,indent=2))
 with (out/'controller.log').open('w') as log:rc=subprocess.call(cmd,stdout=log,stderr=subprocess.STDOUT)
 sf=out/'recreation/eval_results/scores.json';scores=json.loads(sf.read_text()).get('scores') if sf.exists() else None
 record.update(state='native_finished' if rc==0 else 'native_failure',returncode=rc,ended_epoch=time.time(),actual_score_file=str(sf) if scores else None,scores=scores,full_trajectory_acceptance='pending audit')
 target.write_text(json.dumps(record,indent=2));(out/'controller_result.json').write_text(json.dumps(record,indent=2));print(json.dumps(record))
if __name__=='__main__':main()
