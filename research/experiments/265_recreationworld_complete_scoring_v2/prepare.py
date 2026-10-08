"""Independent scorer environment repair; old complete score remains immutable."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent; prior=root.parent/'251_recreationworld_complete_scoring_v1'
assert not (root/'reports/current_run.json').exists()
for name in ['reports','runs','private']: (root/name).mkdir(parents=True,exist_ok=True)
for name in ['launch.py','eval_entry.py','observe_runner.py']: shutil.copy2(prior/name,root/name)
for name in ['native_judge_admission.json','observer_admission.json','dependency_repair_admission.json','check_scoring.py','qualify_completed.py']: shutil.copy2(prior/'reports'/name,root/'reports'/name)
p=root/'launch.py'; t=p.read_text(); start=t.index("choices=["); end=t.index('],required=True)',start)+1
t=t[:start]+"choices=['264_recreationworld_public_interactions_v16']"+t[end:]
t=t.replace('rw_web_complete_scoring_v1','rw_web_complete_scoring_v2').replace('skillloop-rw-score:251-','skillloop-rw-score:265-').replace("'rw251-'+label","'rw265-'+label")
t=t.replace("assert json.loads((root/'reports/observer_admission.json').read_text())['passed']","assert json.loads((root/'reports/observer_admission.json').read_text())['passed']\nassert json.loads((root/'reports/dependency_repair_admission.json').read_text())['passed']")
p.write_text(t)
p=root/'eval_entry.py'; t=p.read_text().replace('rw_web_complete_scoring_v1','rw_web_complete_scoring_v2').replace('http://127.0.0.1:8166/251_recreationworld/complete_scoring/v1','http://127.0.0.1:8172/265_recreationworld/complete_scoring/v2')
t=t.replace("before=source_hashes();", "# Restore the exact immutable runtime prepared by the official worker before its cleanup.\ntemplate=scripts/'web/template'; lock_sha=hashlib.sha256((template/'package-lock.json').read_bytes()).hexdigest()\nseed=Path('/workspace/shared/mockweb-template-deps')/lock_sha/'node_modules'\nassert seed.is_dir() and (seed.parent/'.complete').is_file(),'Official pinned runtime absent'\nassert hashlib.sha256((workspace/'package-lock.json').read_bytes()).hexdigest()==lock_sha,'Dependency graph changed'\nassert json.loads((workspace/'package.json').read_text())['dependencies']==json.loads((template/'package.json').read_text())['dependencies']\nassert not (workspace/'node_modules').exists()\n(workspace/'node_modules').symlink_to(seed,target_is_directory=True)\n(results/'dependency_runtime.json').write_text(json.dumps({'lock_sha256':lock_sha,'official_seed_directory':str(seed),'restored_link_only':True,'network_called':False},indent=2))\nbefore=source_hashes();")
t=t.replace("after=source_hashes();", "native=json.loads((results/'run.json').read_text()) if rc==0 else {}\nbuild_status=native.get('build_result',{}).get('status')\nafter=source_hashes();")
t=t.replace("'official_rebuild':True", "'official_rebuild':build_status=='success','native_build_status':build_status")
t=t.replace("'finished_epoch':time.time()", "'finished_epoch':time.time(),'native_build_status':build_status")
p.write_text(t)
p=root/'reports/check_scoring.py'; t=p.read_text().replace('250_recreationworld_observation_guard_v10','264_recreationworld_public_interactions_v16').replace('/251_recreationworld/complete_scoring/v1','/265_recreationworld/complete_scoring/v2'); p.write_text(t)
p=root/'reports/qualify_completed.py'; t=p.read_text().replace('257_recreationworld_route_semantics_v15','264_recreationworld_public_interactions_v16').replace('rw_complete_trajectory_qualification_v1','rw_complete_trajectory_qualification_v2')
t=t.replace("scores.get('vlm_enabled') is True])", "scores.get('vlm_enabled') is True,build_status=='success'])")
t=t.replace("official_rebuild_verified=False if build_status=='install_failed' else None", "official_rebuild_verified=build_status=='success'")
t=t.replace("scoring_scope='Native scoring of preserved model-built artifact; independent rebuild failed offline dependency installation'", "scoring_scope='Native complete scoring after exact official pinned-runtime restoration and source-unchanged rebuild'")
p.write_text(t)
for name in ['launch.py','eval_entry.py','observe_runner.py','reports/check_scoring.py','reports/qualify_completed.py']: compile((root/name).read_text(),name,'exec')
(root/'reports/preparation_manifest.json').write_text(json.dumps({'version':'rw_web_complete_scoring_v2','previous_score_preserved':True,'repair_scope':'Restore original official pinned dependency link removed by worker artifact cleanup; no source/vendor/score changes','repair_admission':json.loads((root/'reports/dependency_repair_admission.json').read_text()),'files':[{'path':n,'sha256':hashlib.sha256((root/n).read_bytes()).hexdigest()} for n in ['launch.py','eval_entry.py','observe_runner.py']]},indent=2))
print(json.dumps({'prepared':True,'source_experiment':'264_recreationworld_public_interactions_v16','runtime_repair_admitted':True,'agent_or_judge_launched':False}))
