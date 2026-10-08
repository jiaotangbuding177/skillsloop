"""One native stage, restricted to this independent training application."""
import json,subprocess,time,os,sys,fcntl
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 stage=sys.argv[1];assert stage in ('setup','eval','recreation_eval')
 lock=(ROOT/'private/native.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 if (ROOT/'private/STOP').exists():raise RuntimeError('User STOP')
 freeze=ROOT/'reports/phase_manifest.json'
 if stage=='recreation_eval':
  import hashlib
  m=json.loads(freeze.read_text())
  for name,digest in m['files'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
  acceptance=json.loads((ROOT/'reports/model_acceptance.json').read_text());assert acceptance['vision_ready'] and acceptance['tools_ready']
  gate=json.loads((ROOT/'reports/reference_acceptance.json').read_text());assert gate['accepted']
  if (ROOT/'private/minipaint_rounds.json').exists():raise RuntimeError('First round already allocated; no automatic repetition')
  (ROOT/'private/minipaint_rounds.json').write_text(json.dumps({'family':'minipaint','rounds_started':1,'max_rounds':3,'allocated_at':time.time(),'reset_allowed':False}))
 label=stage+'_'+str(time.time_ns());out=ROOT/'runs'/label;out.mkdir(parents=True)
 image=json.loads(subprocess.check_output(['docker','image','inspect','skillloop-rw-web:218-v2'],text=True))[0]['Id']
 if stage=='recreation_eval':assert image==m['runtime_image_id']
 cmd=['docker','run','--name','rw285-'+label,'--network','host','--memory','3g','--cpus','2','--pids-limit','768','--cap-add','SYS_ADMIN','--cap-add','NET_ADMIN','--security-opt','seccomp=unconfined','--mount',f'type=bind,src={ROOT}/datasets,dst=/var/lib/mockweb-scorer/download,readonly','--mount',f'type=bind,src={ROOT}/scripts/container_entry.py,dst=/opt/rw285/container_entry.py,readonly','--mount',f'type=bind,src={out},dst=/results','-e','RB_ARTIFACT_ROOT=/var/lib/mockweb-scorer/download','-e','RB_ARTIFACT_BACKEND=filesystem','-e','RB_UNIFIED_PREFIX=released','-e','RB_SCRIPTS_DIR=/workspace/RecreationBench/scripts','-e','RB_MODEL_API_KEY=local','-e','USE_VLM_JUDGE=false',image,'python3','/opt/rw285/container_entry.py','--platform','web','--task-id','minipaint.training','--stage',stage,'--agent-cli','claude','--api-mode','openai','--model','deepseek-v4-flash-vision-exp','--model-base-url','http://127.0.0.1:8190/285/'+label+'/v1','--capture-tool-use-screenshots','true','--output-dir','/results']
 if stage=='eval':cmd.extend(['--eval-target','reference'])
 record={'stage':stage,'attempt':label,'pid':os.getpid(),'start_ticks':Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'state':'running','started_epoch':time.time(),'container':'rw285-'+label,'image_id':image,'round':1 if stage=='recreation_eval' else None,'model_rounds_max':3,'output':str(out)}
 report=ROOT/'reports'/('active_rollout.json' if stage=='recreation_eval' else stage+'_status.json');report.write_text(json.dumps(record,indent=2))
 with (out/'controller.log').open('w') as log:rc=subprocess.call(cmd,stdout=log,stderr=subprocess.STDOUT)
 record.update(returncode=rc,state='native_finished' if rc==0 else 'native_failure',ended_epoch=time.time());report.write_text(json.dumps(record,indent=2));print(json.dumps(record))
if __name__=='__main__':main()
