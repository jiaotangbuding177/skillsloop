import json,hashlib,time,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];old=root.parent/'285_rw_evolution_collection'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
for base,manifest in [(old,old/'reports/phase_manifest.json')]+[(root,p) for p in (root/'reports').glob('freeze_*.json')]:
 j=json.loads(manifest.read_text());bad=[]
 for n,h in j['files'].items():
  p=base/n.replace('\\','/')
  if not p.is_file() or sha(p)!=h:bad.append(n)
 checks[str(manifest.relative_to(root.parent))]={'files':len(j['files']),'mismatches':bad,'manifest_sha256':sha(manifest)}
prior=old/'runs/recreation_eval_1791121638371741570';score=prior/'recreation/eval_results/scores.json'
raw=prior/'private_raw_sessions/copy_manifest.json';jm=json.loads(raw.read_text());rawchecks=[]
for f in jm['files']:
 p=raw.parent/f['file'].replace('\\','/');rawchecks.append({'file':f['file'],'bytes':f['bytes'],'copy_sha_verified':sha(p)==f['copied_sha256']==f['source_sha256']})
round_source={'family':'minipaint','completed_model_rounds_before_parallel':1,'previous_scores':json.loads(score.read_text()),'score_sha256':sha(score),'raw_files':rawchecks,'not_verified_success':True,'observer_original_score_null_is_path_mismatch':True,'original_results_not_modified':True}
effective={'version':'rw_parallel_evolution_v2.2','maximum_active_model_workers':2,'memory_mib_each':1280,'cpu_each':1,'additional_container_swap':0,'start_gate_host_available_mib':2560,'source_pool':26,'per_canonical_family_full_rounds_max':3,'provisional_parallel_config_retained':True,'effective_limits_authority':'frozen scripts_v22/worker.py and actual Docker HostConfig; older planning values 1g/2300 are not runtime values','model_resource_unchanged':True,'model_requested':'deepseek-v4-flash-vision-exp','model_reported':'deepseek-v4.1-flash','physical_checkpoint_unknown':True,'vendor_commit':'b5cda868f44932dc84ea68e3b3053bc418621aa3','round_corrections':'miniPaint round2 restores original own candidate and original session plus real round1 failures; Squoosh round1 clean independent session','no_cross_application_candidate_or_context':True,'skills_learning_started':False,'benchmark_250_evaluation_started':False,'prior_full_round':round_source,'sha_checks':checks,'created_epoch':time.time()}
assert all(not x['mismatches'] for x in checks.values());assert all(x['copy_sha_verified'] for x in rawchecks)
target=root/'reports/current_phase_manifest.json';assert not target.exists();target.write_text(json.dumps(effective,indent=2));print(json.dumps({'passed':True,'freeze_checks':checks,'previous_model_rounds':1,'prior_raw_files':len(rawchecks)}))
