"""Reuse admitted native full scoring for a new, source-changed demonstration."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent; prior=root.parent/'265_recreationworld_complete_scoring_v2'
assert not (root/'reports/current_run.json').exists()
for name in ['reports','runs','private']: (root/name).mkdir(parents=True,exist_ok=True)
for name in ['launch.py','eval_entry.py','observe_runner.py']: shutil.copy2(prior/name,root/name)
for name in ['native_judge_admission.json','observer_admission.json','dependency_repair_admission.json','check_scoring.py','qualify_completed.py']: shutil.copy2(prior/'reports'/name,root/'reports'/name)
for name in ['launch.py','eval_entry.py','reports/check_scoring.py','reports/qualify_completed.py']:
 p=root/name; t=p.read_text().replace('264_recreationworld_public_interactions_v16','267_recreationworld_public_content_v17').replace('rw_web_complete_scoring_v2','rw_web_complete_scoring_v3').replace('rw_complete_trajectory_qualification_v2','rw_complete_trajectory_qualification_v3').replace('skillloop-rw-score:265-','skillloop-rw-score:268-').replace("'rw265-'+label","'rw268-'+label").replace('http://127.0.0.1:8172/265_recreationworld/complete_scoring/v2','http://127.0.0.1:8173/268_recreationworld/complete_scoring/v3').replace('/265_recreationworld/complete_scoring/v2','/268_recreationworld/complete_scoring/v3')
 p.write_text(t); compile(t,name,'exec')
value={'version':'rw_web_complete_scoring_v3','source_experiment':'267_recreationworld_public_content_v17','previous_scores_preserved':True,'scoring_algorithm_unchanged':True,'only_version_source_route_identity_changed':True,'admitted_dependency_restoration_unchanged':True,'agent_or_judge_launched':False,'files':[{'path':n,'sha256':hashlib.sha256((root/n).read_bytes()).hexdigest()} for n in ['launch.py','eval_entry.py','observe_runner.py']]}
(root/'reports/preparation_manifest.json').write_text(json.dumps(value,indent=2)); print(json.dumps(value))
