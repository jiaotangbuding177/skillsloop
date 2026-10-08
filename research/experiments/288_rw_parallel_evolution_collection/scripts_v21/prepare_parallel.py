import json,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'285_rw_evolution_collection'
def main():
 m=json.loads((OLD/'reports/phase_manifest.json').read_text())
 for n,h in m['files'].items():assert hashlib.sha256((OLD/n).read_bytes()).hexdigest()==h,n
 a=json.loads((OLD/'reports/active_rollout.json').read_text());assert a['state']=='native_finished'
 prior=OLD/'runs'/a['attempt'];candidate=prior/'recreation'
 score=json.loads((candidate/'eval_results/scores.json').read_text());details=json.loads((candidate/'eval_results/test_details.json').read_text())
 target=ROOT/'datasets/released/web/minipaint.training'
 if target.exists():raise RuntimeError('Preparation already done; do not overwrite')
 shutil.copytree(OLD/'datasets/released/web/minipaint.training',target)
 checkpoint=ROOT/'checkpoints/minipaint/round1';checkpoint.mkdir(parents=True)
 files={}
 for name in ['src','public','index.html','package.json','package-lock.json','vite.config.ts','tsconfig.json']:
  src=candidate/name;dst=checkpoint/'candidate'/name
  if not src.exists():continue
  dst.parent.mkdir(parents=True,exist_ok=True)
  if src.is_dir():shutil.copytree(src,dst)
  else:shutil.copy2(src,dst)
 for p in (checkpoint/'candidate').rglob('*'):
  if p.is_file():files[str(p.relative_to(checkpoint))]=hashlib.sha256(p.read_bytes()).hexdigest()
 manifest=json.loads((prior/'private_raw_sessions/copy_manifest.json').read_text());assert len(manifest['files'])==1
 session=manifest['files'][0];source=prior/'private_raw_sessions'/session['file'];assert hashlib.sha256(source.read_bytes()).hexdigest()==session['source_sha256']
 dst=checkpoint/'sessions'/session['file'];dst.parent.mkdir(parents=True);shutil.copy2(source,dst);files[str(dst.relative_to(checkpoint))]=hashlib.sha256(dst.read_bytes()).hexdigest()
 session_id=source.stem
 failures=[t['title'] for t in details['test_details']['functional'] if t['status']!='passed']
 feedback={'family':'minipaint','round':2,'parent_attempt':a['attempt'],'session_id':session_id,'prior_functional':'3/6','prior_visual_ssim':score['scores']['visual_ssim_score'],'failed_behavior_checks':failures,'not_private_verifier_source':True,'maximum_full_rounds':3}
 (checkpoint/'feedback.json').write_text(json.dumps(feedback,indent=2));(checkpoint/'checkpoint_manifest.json').write_text(json.dumps({'files':files,'parent_attempt':a['attempt']},indent=2))
 for name in ['relay.py','vision_bridge.py','bootstrap_relay.py']:
  t=(OLD/'scripts'/name).read_text();t=t.replace('8190','8193');(ROOT/'scripts'/name).write_text(t)
 cfg=json.loads((OLD/'model_resource.json').read_text());cfg.update(version='rw_parallel_evolution_v2',local_port=8193);(ROOT/'model_resource.json').write_text(json.dumps(cfg,indent=2))
 (ROOT/'parallel_config.json').write_text(json.dumps({'version':'rw_parallel_evolution_v2','maximum_active_workers':2,'memory_limit_per_worker':'1g','cpus_per_worker':1,'minimum_host_available_mib_for_start':2300,'source_pool':26,'per_family_max_full_rounds':3,'correction_keeps_session_and_candidate':True,'first_rounds_no_cross_application_context':True,'model_resource_unchanged':True,'old_freeze_preserved':str(OLD/'reports/phase_manifest.json'),'planned_first_two':['minipaint:round2','squoosh:round1'],'vendor_commit':m['vendor_commit'],'runtime_image_id':m['runtime_image_id']},indent=2))
 print(json.dumps({'prepared':True,'miniPaint_parent_score':score['scores']['final_score'],'failed_checks':failures,'checkpoint_files':len(files),'max_parallel':2}))
if __name__=='__main__':main()
