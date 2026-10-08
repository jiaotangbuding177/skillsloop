import hashlib,json,shutil,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 a=ROOT/'admission/minipaint'
 assert json.loads((a/'verifier/admission.json').read_text())['accepted']
 out=ROOT/'datasets/released/web/minipaint.training'
 if out.exists():raise RuntimeError('Retain existing package; do not overwrite')
 (out/'reference').mkdir(parents=True);(out/'tests/static').mkdir(parents=True)
 with tarfile.open(out/'reference/reference.tar.gz','w:gz') as tf:tf.add(a/'reference/site',arcname='site')
 task={'task_id':'minipaint.training','version':'rw_evolution_collection_v1','domain':'minipaint.training','input':{'site_url':'runtime-provided','template':'react-vite'},'constraints':{'target_pages':['homepage'],'max_pages':1,'required_features':['interactive_drawing','editor_menus','document_export'],'delivery_format':{'framework':'react','build_tool':'vite','entry_point':'src/App.tsx','build_command':'npm run build','output_dir':'dist/'}},'time_limit_seconds':7200}
 (out/'reference/task.json').write_text(json.dumps(task,indent=2));(out/'reference/site_meta.json').write_text(json.dumps({'pages':[{'id':'homepage','path':'/'}]}))
 shutil.copy2(ROOT/'scripts/functional.spec.ts',out/'tests/static/content.scripted.spec.ts')
 (out/'tests/gt').mkdir()
 for name in ['gt_screenshots','gt_layout','gt_regions','gt_dom']:shutil.copytree(a/'gt'/name,out/'tests/gt'/name)
 (out/'tests/eval_config.json').write_text(json.dumps({'vlm_judge':{'enabled':False}},indent=2))
 (out/'instance.json').write_text(json.dumps({'id':'minipaint.training','platform':'web','split':'independent_evolution','source_commit':'a79733eb803fc97084ef0ee4faa96b031e69e1c0','benchmark_250_tests_read':False,'verifier_cases':6,'visual_method':'official SSIM/LPIPS with real paired screenshots, not VLM','max_full_rounds':3},indent=2))
 contract={'version':'rw_evolution_collection_v1','source_pool':26,'first_task':'minipaint.training','max_full_agent_rounds_per_family':3,'stop_on_success':True,'no_batch_claim_before_admission':True,'agent_prompt':'unchanged official web render','correction_rounds':'only new counted round; preserve previous result; no covert retries','verified_success':{'functional_pass_rate':1.0,'functional_total':6,'visual_score_minimum':0.85,'build':'success','originality_audit':'passed'},'visual_method':'Official SSIM/LPIPS with own desktop/mobile GT; VLM not part of this training acceptance','official_benchmark_score_not_claimed':True,'learning_started':False,'evaluation_250_started':False}
 (ROOT/'collection_contract.json').write_text(json.dumps(contract,indent=2));print(json.dumps({'packaged':True,'task':'minipaint.training','new_reference_admitted':1,'verifier_reference':'6/6','static_negative':'0/6'}))
if __name__=='__main__':main()
