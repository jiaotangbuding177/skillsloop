"""Launch only after original candidate run has ended; preserve its complete results."""
import argparse,fcntl,hashlib,importlib.util,json,subprocess,sys,time
from pathlib import Path
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(); parser.add_argument('--source-experiment',choices=['264_recreationworld_public_interactions_v16'],required=True)
source=root.parent/parser.parse_args().source_experiment
lock=(root/'reports/launch.lock').open('a')
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
assert not (root/'private/STOP').exists()
assert not (root/'reports/current_run.json').exists(),'Scoring already launched; inspect existing run instead'
s=json.loads((source/'reports/pipeline_status.json').read_text()); assert s['state']=='native_finished',s['state']
metrics=json.loads((source/'runs'/s['attempt']/'metrics.json').read_text())
assert metrics['stage_recreation']=='succeeded'
assert metrics['program_score']>=0.5,'Even perfect visual score cannot meet official threshold; preserve candidate as failure without redundant judging'
assert not (source/'private/STOP').exists()
assert json.loads((root/'reports/native_judge_admission.json').read_text())['passed']
assert json.loads((root/'reports/observer_admission.json').read_text())['passed']
assert json.loads((root/'reports/dependency_repair_admission.json').read_text())['passed']
name='rw238-'+s['attempt']; assert subprocess.check_output(['docker','inspect','--format','{{.State.Running}}',name],text=True).strip()=='false'
for f in json.loads((source/'reports/phase_manifest.json').read_text())['files']:
 assert hashlib.sha256((source/f['path']).read_bytes()).hexdigest()==f['sha256'],f['path']
original=root.parent/'218_recreationworld_glm_pipeline/scripts/pipeline.py'
spec=importlib.util.spec_from_file_location('rw_original',original); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.check()
label='full_visual_'+str(time.time_ns()); out=root/'runs'/label; out.mkdir(parents=True)
image='skillloop-rw-score:265-'+str(time.time_ns())
image_id=subprocess.check_output(['docker','commit',name,image],text=True).strip()
manifest={'version':'rw_web_complete_scoring_v2','source_version':s['version'],'source_attempt':s['attempt'],'source_container':name,'frozen_image_id':image_id,'agent_launched':False,'old_scores_preserved':True,'judge_requested_model':'deepseek-v4-flash-vision-exp','same_provider_self_judge':True,'exact_backend_unverified':True,'vlm_mode':'assertion','judge_concurrency':2,'missing_ssim_not_visual_failure':True,'canary_excluded':True,'official_vendor_and_algorithm_unchanged':True,'files':[{'path':x,'sha256':hashlib.sha256((root/x).read_bytes()).hexdigest()} for x in ['launch.py','eval_entry.py','observe_runner.py']]}
(out/'phase_manifest.json').write_text(json.dumps(manifest,indent=2)); (root/'reports/current_run.json').write_text(json.dumps({'run':label,'path':str(out),'source_attempt':s['attempt']},indent=2))
cmd=['docker','run','--name','rw265-'+label,'--network','host','--cap-add','SYS_ADMIN','--cap-add','NET_ADMIN','--security-opt','seccomp=unconfined','--mount',f'type=bind,src={root}/eval_entry.py,dst=/opt/rw251/eval_entry.py,readonly','--mount',f'type=bind,src={root}/observe_runner.py,dst=/opt/rw251/observe_runner.py,readonly','--mount',f'type=bind,src={out},dst=/results',image,'python3','/opt/rw251/eval_entry.py']
raise SystemExit(subprocess.call(cmd))
