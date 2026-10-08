import json,subprocess,sys,time,hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];task=sys.argv[1];assert task in ('minipaint','squoosh')
prior='minipaint_recreation_eval_1791126784363902808' if task=='minipaint' else 'squoosh_eval_1791128738283803882'
native=Path('/var/tmp')/('rw288-score-'+task+'-'+str(time.time_ns()));native.mkdir()
subprocess.run(['docker','cp','rw288-'+prior+':/workspace/dataset',str(native/'dataset')],check=True)
cache=native/'torch';cache.mkdir();subprocess.run(['docker','cp','rw288-'+prior+':/root/.cache/torch/.',str(cache)],check=True)
out=root/'runs'/('score_only_'+task+'_'+str(time.time_ns()));out.mkdir();candidate=root/'runs'/prior/'recreation/output'
cmd=['docker','run','--name','rw288-'+out.name,'--network','none','--memory','2048m','--memory-swap','2048m','--cpus','2','--pids-limit','640','--mount',f'type=bind,src={native}/dataset,dst=/data,readonly','--mount',f'type=bind,src={cache},dst=/root/.cache/torch','--mount',f'type=bind,src={out},dst=/results','--mount',f'type=bind,src={root}/reports/score_saved.py,dst=/score_saved.py,readonly','-e','USE_VLM_JUDGE=false','-e','MOCKWEB_NODE_MODULES=/opt/mockweb-bench/batch_run/node_modules']
if task=='minipaint':cmd.extend(['--mount',f'type=bind,src={candidate},dst=/candidate,readonly'])
cmd.extend(['sha256:603d4b4f22fc32a7d0bb2e034db9f9afc1d5597f6116cfb35d2fa1e244d34c3d','python3','/score_saved.py',task])
manifest={'version':'rw_saved_candidate_scoring_v1','task':task,'parent_attempt':prior,'not_a_model_round':True,'model_calls':0,'input_candidate_unchanged':True,'memory_mib':2048,'cpus':2,'official_vendor_unchanged':True,'output':str(out),'started_epoch':time.time()}
manifest['scorer_sha256']=hashlib.sha256((root/'reports/score_saved.py').read_bytes()).hexdigest()
if candidate.is_dir():manifest['candidate_files']={str(p.relative_to(candidate)):hashlib.sha256(p.read_bytes()).hexdigest() for p in candidate.rglob('*') if p.is_file()}
(out/'score_phase_manifest.json').write_text(json.dumps(manifest,indent=2))
with (out/'score.log').open('w') as log:rc=subprocess.call(cmd,stdout=log,stderr=subprocess.STDOUT)
manifest.update(returncode=rc,ended_epoch=time.time());(root/'reports'/f'{task}_saved_score_status.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest));raise SystemExit(rc)
