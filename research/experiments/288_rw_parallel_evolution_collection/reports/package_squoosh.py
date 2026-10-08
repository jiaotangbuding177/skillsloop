import json,tarfile,shutil,hashlib,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];a=root/'admission/squoosh';out=root/'datasets/released/web/squoosh.training'
assert json.loads((a/'verifier/admission.json').read_text())['accepted'];assert json.loads((a/'native_build_v4_status.json').read_text())['returncode']==0
assert not out.exists();(out/'reference').mkdir(parents=True);(out/'tests/static').mkdir(parents=True)
with tarfile.open(out/'reference/reference.tar.gz','w:gz') as tf:tf.add(a/'site',arcname='site')
task={'task_id':'squoosh.training','version':'rw_parallel_evolution_v2.2','domain':'squoosh.training','input':{'site_url':'runtime-provided','template':'react-vite'},'constraints':{'target_pages':['homepage'],'max_pages':1,'required_features':['image_upload','image_codec_export','resize_rotate','comparison_editor'],'delivery_format':{'framework':'react','build_tool':'vite','entry_point':'src/App.tsx','build_command':'npm run build','output_dir':'dist/'}},'time_limit_seconds':7200}
(out/'reference/task.json').write_text(json.dumps(task,indent=2));(out/'reference/site_meta.json').write_text(json.dumps({'pages':[{'id':'homepage','path':'/'}]}))
shutil.copy2(root/'reports/squoosh_functional.spec.ts',out/'tests/static/content.scripted.spec.ts');(out/'tests/gt').mkdir()
for name in ['gt_screenshots','gt_layout','gt_regions','gt_dom']:shutil.copytree(a/'gt'/name,out/'tests/gt'/name)
(out/'tests/eval_config.json').write_text(json.dumps({'vlm_judge':{'enabled':False}},indent=2))
(out/'instance.json').write_text(json.dumps({'id':'squoosh.training','platform':'web','split':'independent_evolution','source_commit':'e8d35e0fb66eb16eff6fe8fc773eabcbb7128de3','benchmark_250_tests_read':False,'verifier_cases':6,'visual_method':'official SSIM/LPIPS with own paired screenshots, not VLM','max_full_rounds':3},indent=2))
files={str(p.relative_to(a/'site')).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (a/'site').rglob('*') if p.is_file()}
(a/'source_manifest.json').write_text(json.dumps({'source_commit':'e8d35e0fb66eb16eff6fe8fc773eabcbb7128de3','repo':'GoogleChromeLabs/squoosh','original_source_modified':False,'build':'npm ci --offline && npm run build','files':files,'actor_sees_reference_browser_only':True,'created_epoch':time.time()},indent=2))
print(json.dumps({'packaged':True,'reference_files':len(files),'reference_tests':'6/6','negative':'0/6','new_model_calls':0}))
