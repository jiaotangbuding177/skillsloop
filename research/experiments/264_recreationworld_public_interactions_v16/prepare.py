"""Source-only corrective demonstration; public behavior, no score/test feedback."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent; prior=root.parent/'257_recreationworld_route_semantics_v15'
s=json.loads((prior/'reports/pipeline_status.json').read_text()); assert s['state']=='native_finished'
assert not (root/'reports/pipeline_status.json').exists(),'Do not overwrite an existing attempt'
for name in ['reports','ledger','runs','private/recovery/workspace']: (root/name).mkdir(parents=True,exist_ok=True)
names=['relay.py','vision_bridge.py','run_canary.py','container_entry.py','resume_cli.py','execution_guidance.txt','model_resource.json','observation_guard.py','asset_fetch.py','managed-settings.json']
for name in names: shutil.copy2(prior/name,root/name)
for name in ['live_check.py','guard_live_check.py','scorer_progress.py','audit_attempt.py','export_observable.py','authorship_review.py','restore_fixture.py','restore_admission.py','launch.py']:
 shutil.copy2(prior/'reports'/name,root/'reports'/name)
for name in ['model_acceptance.json','guard_fixture_admission.json','native_hook_admission.json','native_empty_admission.json']:
 shutil.copy2(prior/'reports'/name,root/'reports'/name)
workspace=prior/'runs'/s['attempt']/'recreation'; recovery=root/'private/recovery'
items=['src','public']+[name for name in ['index.html','package-lock.json','package.json','tsconfig.json','vite.config.ts','tailwind.config.js','tailwind.config.ts','postcss.config.js','postcss.config.cjs'] if (workspace/name).is_file()]
for item in items:
 p=workspace/item; dest=recovery/'workspace'/item
 if p.is_dir(): shutil.copytree(p,dest,dirs_exist_ok=True)
 else: shutil.copy2(p,dest)
hashes={str(p.relative_to(recovery/'workspace')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (recovery/'workspace').rglob('*') if p.is_file()}
(recovery/'recovery_manifest.json').write_text(json.dumps({'source_attempt':s['attempt'],'source_version':s['version'],'workspace_items':items,'files':hashes,'no_sessions_or_evaluation_data':True,'model_authored_source_only':True},indent=2))
cfg=json.loads((root/'model_resource.json').read_text()); cfg.update(version='rw_web_deepseek_public_interactions_v16',local_port=8172,source_checkpoint=s['attempt'])
(root/'model_resource.json').write_text(json.dumps(cfg,indent=2))
for name,old,new in [('run_canary.py','8171/257_recreationworld','8172/264_recreationworld'),('container_entry.py','8801','8802')]:
 p=root/name; p.write_text(p.read_text().replace(old,new))
p=root/'reports/launch.py'; p.write_text(p.read_text().replace("old=root.parent/'255_recreationworld_pagewise_fidelity_v14'","old=root.parent/'257_recreationworld_route_semantics_v15'").replace('8171','8172').replace('8801','8802'))
(root/'execution_guidance.txt').write_text('''This is a source-only corrective demonstration, not an independent baseline. Your previous model-authored source is restored, without sessions, tests, scores or evaluator feedback. Original task and originality rules apply. Reference access: screenshots, accessibility snapshots, ordinary clicks/navigation and explicit binary assets only. No reference DOM/HTML/CSS harvesting, evaluate/run_code, private tests or gold. Implement your own source; never replay reference nodes or screenshots as backgrounds.

Prioritize real public interactions. Your OWN existing SearchPage currently prevents form submission with no further effect. Your OWN PrivacyPage links to /about/privacy-statement/ but App.routeFor has no such case. Inspect these existing source issues, observe the corresponding public reference behavior with ordinary browser tools, and fix your own implementation. Do not assume links to unobserved pages should be #, a generic offline page, or the home page. Implement the actual observed destination and page, including query and fragment behavior. If public external links resolve to the offline page, reproduce that OBSERVED navigation behavior precisely; do not guess or invent functionality.

Keep a compact public_behavior_checklist.md in your workspace. Inventory publicly visible navigation and reachable subpages. For each distinct interaction type, FIRST perform the reference action and record its resulting URL, public accessible state or visible result; THEN perform the same action on your candidate, compare, repair immediately and recheck. Cover header dropdown open/close/hover and keyboard, desktop and mobile menu/search toggles, search Enter and button submission/query change, footer links, in-page anchors, contact controls, direct route/reload/back navigation, and any visible accordion/show-more/gallery controls. Do not replace a form with a no-op, a missing route with home, interactive elements with plain spans, or link destinations with placeholders. Preserve observed accessible names, roles and visible text exactly using original components, without DOM extraction. Observe the additional privacy overview page reachable from your own source link and the public reference.

Avoid repeated cosmetic inspection while actionable behavior gaps remain. Reuse your current visual design, implement and verify each missing behavior first. Then do a focused screenshot comparison and repair materially different layouts. Test the actual self-contained output/index.html on your own preview, build after your last edit, and provide a concise nonempty final delivery statement describing completed public behavior checks. A context summary is not delivery. There is no private score or expected-answer feedback in this request.

Binary asset helper: python3 /opt/rw218/asset_fetch.py URL /workspace/recreation/public/FILE. Own preview ports 4173 or 5173 are allowed. Do not hand off the default template or omit the complete artifact.
''')
for name in names:
 if name.endswith('.py'): compile((root/name).read_text(),name,'exec')
manifest={'version':cfg['version'],'previous_attempt':s['attempt'],'previous_frozen_results_preserved':True,'source_only_corrective_continuation':True,'score_feedback_or_private_tests_given_to_agent':False,'guidance_basis':'Observed defects in model-owned SearchPage and routeFor; agent must independently observe public reference behavior','official_vendor_and_scorer_unchanged':True,'canary_excluded':True,'files':[{'path':name,'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest()} for name in names],'source_checkpoint_hashes':hashes}
(root/'reports/phase_manifest.json').write_text(json.dumps(manifest,indent=2)); print(json.dumps({'version':cfg['version'],'runtime_hashes':len(names),'source_hashes':len(hashes)}))
