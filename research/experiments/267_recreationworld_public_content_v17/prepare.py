"""Source-only corrective demonstration; public behavior, no score/test feedback."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent; prior=root.parent/'264_recreationworld_public_interactions_v16'
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
cfg=json.loads((root/'model_resource.json').read_text()); cfg.update(version='rw_web_deepseek_public_content_v17',local_port=8173,source_checkpoint=s['attempt'])
(root/'model_resource.json').write_text(json.dumps(cfg,indent=2))
for name,old,new in [('run_canary.py','8172/264_recreationworld','8173/267_recreationworld'),('container_entry.py','8802','8803')]:
 p=root/name; p.write_text(p.read_text().replace(old,new))
p=root/'reports/launch.py'; p.write_text(p.read_text().replace("old=root.parent/'257_recreationworld_route_semantics_v15'","old=root.parent/'264_recreationworld_public_interactions_v16'").replace('8172','8173').replace('8802','8803'))
(root/'execution_guidance.txt').write_text('''This is a source-only corrective demonstration, not an independent baseline. Your previous model-authored source is restored, without sessions, tests, scores or evaluator feedback. Original task and originality rules apply. Reference access: screenshots, accessibility snapshots, ordinary clicks/navigation and explicit binary assets only. No reference DOM/HTML/CSS harvesting, evaluate/run_code, private tests or gold. Implement your own source; never replay reference nodes or screenshots as backgrounds.

Prioritize fidelity of PUBLIC content and controls, not summaries. Your OWN ContactPage currently displays department telephone numbers and emails as plain spans. Your OWN HomeGallery marks items cursor-pointer but has no click behavior. Your OWN prose contains generalized descriptions and some unobserved destinations are all mapped to /_404.html. These are source observations, not evaluation feedback. Independently observe their public reference counterparts using accessibility snapshots, screenshots and ordinary actions, then implement the exact OBSERVED text, accessible names, real href/form destinations and behavior. Do not assume a generic offline destination or invent links. A visually similar paragraph rewritten in your own words does not recreate the displayed content; original implementation means your own code, not paraphrasing public text.

For EVERY publicly reachable page, compare its reference accessibility snapshot to your candidate snapshot: exact page title, headings, labels, main visible text, lists, links and their destinations, images with observed alt text, phone/email controls, and missing sections. Record actual public evidence in public_behavior_checklist.md, repair discrepancies immediately, then recheck. No invented text, generic substitutes, guessed statistics or extra controls. Use full-page screenshots to check all sections below the fold and the desktop/mobile layouts. Do not inspect private evaluation data or extract reference HTML/DOM/style. Browser accessibility snapshots and ordinary clicks are the allowed source of public text and behavior.

Do not merely restate your previous checklist as verification. Test actual public reference actions and candidate results, including galleries, contact controls, footer and in-page links, quick-links/menu/search toggles, fragment changes and browser back/reload. Compare real resulting URLs and accessible states. Rebuild after the LAST edit, inspect the actual self-contained output/index.html on your own preview, and deliver a nonempty concise statement describing observed checks. A context summary is not delivery. No private scores, assertions or expected-answer feedback are provided.

Binary asset helper: python3 /opt/rw218/asset_fetch.py URL /workspace/recreation/public/FILE. Own preview ports 4173 or 5173 are allowed. Do not hand off the default template or omit the complete artifact.
''')
for name in names:
 if name.endswith('.py'): compile((root/name).read_text(),name,'exec')
manifest={'version':cfg['version'],'previous_attempt':s['attempt'],'previous_frozen_results_preserved':True,'source_only_corrective_continuation':True,'score_feedback_or_private_tests_given_to_agent':False,'guidance_basis':'Model-owned ContactPage plain spans, HomeGallery inert controls and generalized prose; independently verify public content and behavior','official_vendor_and_scorer_unchanged':True,'canary_excluded':True,'files':[{'path':name,'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest()} for name in names],'source_checkpoint_hashes':hashes}
(root/'reports/phase_manifest.json').write_text(json.dumps(manifest,indent=2)); print(json.dumps({'version':cfg['version'],'runtime_hashes':len(names),'source_hashes':len(hashes)}))
