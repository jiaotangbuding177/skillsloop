import json,shutil,hashlib,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];prior=root/'runs/minipaint_recreation_eval_1791126784363902808';cp=root/'checkpoints/minipaint/round2';assert not cp.exists();(cp/'candidate').mkdir(parents=True)
status=json.loads((prior/'run_agent_only.json').read_text());assert status['rollout']['native_returncode']==0 and status['submitted'] and status['build_result']['status']=='success'
for name in ['src','public','index.html','package.json','package-lock.json','vite.config.ts','tsconfig.json']:
 p=prior/'recreation'/name
 if not p.exists():continue
 d=cp/'candidate'/name
 if p.is_dir():shutil.copytree(p,d)
 else:shutil.copy2(p,d)
raw=prior/'private_raw_sessions';manifest=json.loads((raw/'copy_manifest.json').read_text())
for f in manifest['files']:
 src=raw/f['file'];assert hashlib.sha256(src.read_bytes()).hexdigest()==f['source_sha256']==f['copied_sha256'];dst=cp/'sessions'/f['file'];dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
score=root/'runs/score_only_minipaint_1791129424129760714/eval_results/scores.json';j=json.loads(score.read_text());details=json.loads(score.with_name('test_details.json').read_text())['test_details']['functional']
feedback={'round':3,'maximum_full_rounds':3,'parent_attempt':prior.name,'session_id':'528b7477-cbe7-458a-9cfe-6ffb6f57c66f','prior_passed':j['scores']['dimension_details']['functional']['passed'],'prior_total':6,'prior_visual_ssim':j['scores']['visual_ssim_score'],'prior_official_final_score':j['scores']['final_score'],'integrity_reasons_retained':j['scores'].get('integrity_reasons',[]),'failed_behavior_checks':[d['title'] for d in details if d['status']=='failed'],'score_recovery_not_a_model_round':True,'score_source':str(score),'created_epoch':time.time()}
(cp/'feedback.json').write_text(json.dumps(feedback,indent=2));files={str(p.relative_to(cp)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in cp.rglob('*') if p.is_file()};(cp/'checkpoint_manifest.json').write_text(json.dumps({'files':files,'source_raw_hash_verified':True,'only_own_candidate_and_session':True,'no_evaluator_or_reference_source':True},indent=2));print(json.dumps({'round3_checkpoint_ready':True,'files':len(files),'functional':f"{feedback['prior_passed']}/6",'final_score_retained':feedback['prior_official_final_score']}))
