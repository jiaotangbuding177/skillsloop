"""Declared source-only corrective demonstration; no score or gold feedback."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent
prior=root.parent/'254_recreationworld_native_empty_recovery_v13'
s=json.loads((prior/'reports/pipeline_status.json').read_text()); assert s['state']=='native_finished'
for name in ['reports','ledger','runs','private/recovery/workspace']: (root/name).mkdir(parents=True,exist_ok=True)
names=['relay.py','vision_bridge.py','run_canary.py','container_entry.py','resume_cli.py','execution_guidance.txt','model_resource.json','observation_guard.py','asset_fetch.py','managed-settings.json']
for name in names: shutil.copy2(prior/name,root/name)
for p in (prior/'reports').glob('*.py'): shutil.copy2(p,root/'reports'/p.name)
for name in ['model_acceptance.json','guard_fixture_admission.json','native_hook_admission.json','native_empty_admission.json']: shutil.copy2(prior/'reports'/name,root/'reports'/name)
workspace=prior/'runs'/s['attempt']/'recreation'; recovery=root/'private/recovery'
items=['src','public']+[name for name in ['index.html','package-lock.json','package.json','tsconfig.json','vite.config.ts','tailwind.config.js','tailwind.config.ts','postcss.config.js','postcss.config.cjs'] if (workspace/name).is_file()]
for item in items:
 p=workspace/item; dest=recovery/'workspace'/item
 if p.is_dir(): shutil.copytree(p,dest,dirs_exist_ok=True)
 else: shutil.copy2(p,dest)
hashes={str(p.relative_to(recovery/'workspace')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (recovery/'workspace').rglob('*') if p.is_file()}
(recovery/'recovery_manifest.json').write_text(json.dumps({'source_attempt':s['attempt'],'source_version':s['version'],'workspace_items':items,'files':hashes,'no_sessions_or_evaluation_data':True,'model_authored_source_only':True},indent=2))
cfg=json.loads((root/'model_resource.json').read_text()); cfg.update(version='rw_web_deepseek_pagewise_fidelity_v14',local_port=8170,source_checkpoint=s['attempt'])
(root/'model_resource.json').write_text(json.dumps(cfg,indent=2))
for name,old,new in [('run_canary.py','8169/254_recreationworld','8170/255_recreationworld'),('container_entry.py','8799','8800')]:
 p=root/name; p.write_text(p.read_text().replace(old,new))
p=root/'reports/launch.py'; t=p.read_text().replace("old=root.parent/'253_recreationworld_protocol_diagnostics_v12'","old=root.parent/'254_recreationworld_native_empty_recovery_v13'").replace("status['state']=='transport_failure'","status['state']=='native_finished'").replace('8169','8170').replace('8799','8800'); p.write_text(t)
p=root/'execution_guidance.txt'; t=p.read_text(); t+='''
Use a complete page-by-page fidelity pass, not a cosmetic pass. First inventory the pages using ordinary reference navigation. For EACH page, record its current public accessibility snapshot, open its visible menus, exercise search/contact/navigation interactions, and compare the corresponding candidate page side by side through ordinary browser tools. Correct discrepancies in your own code immediately before moving to the next page. Preserve visible text exactly: do not paraphrase headings, menu labels, department names or stories. Do not guess a destination, replace it with #, or suppress an interaction without first observing the reference behavior. Preserve the semantics of visible heading levels, header/nav/main/footer and link names using your own components; this is not permission to extract DOM or source. In your own source, audit placeholder links, preventDefault-only forms, mislabeled controls and inconsistent routes. Verify ordinary click/navigation behavior, not only appearance. Only finish after all observed pages have been checked and the final artifact rebuilt. No private tests, gold, scores or prior evaluator messages are available; use only the original public task and your own source/UI observations.
'''; p.write_text(t)
for name in names:
 if name.endswith('.py'): compile((root/name).read_text(),name,'exec')
manifest={'version':cfg['version'],'previous_attempt':s['attempt'],'previous_frozen_results_preserved':True,'source_only_corrective_continuation':True,'score_feedback_or_private_tests_given_to_agent':False,'official_vendor_and_scorer_unchanged':True,'canary_excluded':True,'files':[{'path':name,'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest()} for name in names],'source_checkpoint_hashes':hashes}
(root/'reports/phase_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'version':cfg['version'],'runtime_hashes':len(names),'source_hashes':len(hashes)}))
