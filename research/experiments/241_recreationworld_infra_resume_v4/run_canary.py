"""Explicit new baseline canary, preserving old 218 run and its freeze."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import time

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'218_recreationworld_glm_pipeline'
CFG=json.loads((ROOT/'model_resource.json').read_text())

def main():
    import fcntl
    lock=(ROOT/'pipeline.lock').open('a'); fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    if (ROOT/'private/STOP').exists() or (OLD/'private/STOP').exists(): raise RuntimeError('User STOP present')
    acceptance=json.loads((ROOT/'reports/model_acceptance.json').read_text())
    if not acceptance['vision_ready'] or not acceptance['tools_ready']: raise RuntimeError('Provider admission failed')
    spec=importlib.util.spec_from_file_location('rw218',OLD/'scripts/pipeline.py'); original=importlib.util.module_from_spec(spec); spec.loader.exec_module(original)
    original.check()
    label='recreation_eval_baseline_'+str(time.time_ns()); out=ROOT/'runs'/label; out.mkdir(parents=True)
    (out/'skill_context.md').write_text((ROOT/'execution_guidance.txt').read_text())
    host=subprocess.check_output(['ip','route','show','default'],text=True).split()[2]
    base='http://127.0.0.1:8160/241_recreationworld/'+label+'/v1'
    task=json.loads((OLD/'reports/dataset_manifest.json').read_text())['task_id']
    cmd=['docker','run','--name','rw238-'+label,'--network','host','--cap-add','SYS_ADMIN','--cap-add','NET_ADMIN',
        '--security-opt','seccomp=unconfined','--mount',f'type=bind,src={original.DATA},dst=/var/lib/mockweb-scorer/download,readonly',
        '--mount',f'type=bind,src={ROOT}/container_entry.py,dst=/opt/rw218/container_entry.py,readonly',
        '--mount',f'type=bind,src={ROOT}/resume_cli.py,dst=/opt/rw218/resume_cli.py,readonly',
        '--mount',f'type=bind,src={ROOT}/private/recovery,dst=/recovery,readonly',
        '--mount',f'type=bind,src={out},dst=/results','-e','RB_ARTIFACT_ROOT=/var/lib/mockweb-scorer/download',
        '-e','RB_ARTIFACT_BACKEND=filesystem','-e','RB_UNIFIED_PREFIX=released','-e','RB_SCRIPTS_DIR=/workspace/RecreationBench/scripts',
        '-e','RB_MODEL_API_KEY=local','-e','USE_VLM_JUDGE=false',original.IMAGE,'python3','/opt/rw218/container_entry.py',
        '--platform','web','--task-id',task,'--stage','recreation_eval','--agent-cli','claude','--api-mode','openai',
        '--model',CFG['model_id'],'--model-base-url',base,'--capture-tool-use-screenshots','true','--output-dir','/results']
    def status(state,**extra):
        (ROOT/'reports/pipeline_status.json').write_text(json.dumps({'version':CFG['version'],'attempt':label,'model':CFG['model_id'],
            'state':state,'task_id':task,'baseline':False,'additional_execution_guidance':True,'judge_enabled':False,'canary_excluded':True,**extra},indent=2))
    status('running',started_epoch=time.time(),controller_pid=__import__('os').getpid())
    with (out/'controller.log').open('w') as log: rc=subprocess.call(cmd,stdout=log,stderr=subprocess.STDOUT)
    receipts=[json.loads(p.read_text()) for p in (ROOT/'ledger').glob('*.json')]
    scoped=[r for r in receipts if label in r.get('route','')]
    failures=[r for r in scoped if not r.get('response_complete')]
    metrics=out/'metrics.json'
    status('transport_failure' if failures else ('native_finished' if rc==0 and metrics.exists() else 'infrastructure_failure'),
        returncode=rc,requests=len(scoped),incomplete_requests=len(failures),native_metrics=str(metrics),
        formal_baseline_accepted=False,reason='Native finish is not delivery acceptance; inspect unchanged official artifacts')

if __name__=='__main__': main()
