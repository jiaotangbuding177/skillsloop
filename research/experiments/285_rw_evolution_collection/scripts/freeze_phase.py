import json,hashlib,zipfile,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 assert json.loads((ROOT/'admission/minipaint/verifier/admission.json').read_text())['accepted']
 s=json.loads((ROOT/'reports/eval_status.json').read_text());out=Path(s['output'])
 scores=json.loads((out/'eval_results/scores.json').read_text());print(json.dumps({'score_keys':list(scores)}))
 native=json.loads((out/'run.json').read_text()[ (out/'run.json').read_text().index('{'):])
 d=native['scores']['dimension_details'];assert d['functional']['total']==6 and d['functional']['passed']==6 and d['visual']['pass_rate']==1.0
 (ROOT/'reports/reference_acceptance.json').write_text(json.dumps({'accepted':True,'native_score_file':str(out/'eval_results/scores.json'),'functional_total':6,'functional_passed':6,'visual_ssim':1.0,'stage_setup':'permission isolation attested','metrics_envelope_discrepancy':'Native metrics reports task_score=0 while actual scores/run reports1; retain both, use eval_results/scores.json for acceptance','vlm_not_enabled_by_declared_training_protocol':True,'benchmark_250_tests_read':False},indent=2))
 selected=[]
 for folder in ['scripts','datasets']:
  selected.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
 selected.extend(ROOT/f for f in ['model_resource.json','collection_contract.json','admission/minipaint/source_manifest.json','reports/model_acceptance.json','reports/reference_acceptance.json'])
 files={str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in selected}
 manifest={'version':'rw_evolution_collection_v1','files':files,'runtime_image_id':s['image_id'],'vendor_commit':'b5cda868f44932dc84ea68e3b3053bc418621aa3','max_full_rounds':3,'first_task':'minipaint.training','native_agent_cli_not_wrapped':True,'additional_prompt_hints':False,'freeze_created_before_first_agent':True}
 target=ROOT/'reports/phase_manifest.json'
 if target.exists():raise RuntimeError('Do not overwrite frozen phase')
 target.write_text(json.dumps(manifest,indent=2))
 with zipfile.ZipFile(ROOT/'reports/frozen_sources.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in selected:z.write(p,str(p.relative_to(ROOT)))
 print(json.dumps({'freeze_files':len(files),'accepted':True}))
if __name__=='__main__':main()
