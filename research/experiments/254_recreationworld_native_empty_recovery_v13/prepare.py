"""Keep protocol completion separate from native task delivery validation."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent; prior=root.parent/'253_recreationworld_protocol_diagnostics_v12'
for name in ['reports','ledger','runs','private/recovery']: (root/name).mkdir(parents=True,exist_ok=True)
names=['relay.py','vision_bridge.py','run_canary.py','container_entry.py','resume_cli.py','execution_guidance.txt','model_resource.json','observation_guard.py','asset_fetch.py','managed-settings.json']
for name in names: shutil.copy2(prior/name,root/name)
shutil.copytree(prior/'private/recovery',root/'private/recovery',dirs_exist_ok=True)
for name in ['live_check.py','guard_live_check.py','scorer_progress.py','audit_attempt.py','export_observable.py','reference_action_review.py','authorship_review.py','finished_tools.py','restore_fixture.py','restore_admission.py','launch.py','model_acceptance.json','guard_fixture_admission.json','native_hook_admission.json']:
 shutil.copy2(prior/'reports'/name,root/'reports'/name)
cfg=json.loads((root/'model_resource.json').read_text()); cfg.update(version='rw_web_deepseek_native_empty_recovery_v13',local_port=8169,native_empty_endturn_feedback=True)
(root/'model_resource.json').write_text(json.dumps(cfg,indent=2))
for name,old,new in [('run_canary.py','8168/253_recreationworld','8169/254_recreationworld'),('container_entry.py','8798','8799')]:
 p=root/name; p.write_text(p.read_text().replace(old,new))
p=root/'reports/launch.py'; text=p.read_text().replace("old=root.parent/'252_recreationworld_link_fidelity_v11'","old=root.parent/'253_recreationworld_protocol_diagnostics_v12'").replace('8168','8169').replace('8798','8799'); text=text.replace("assert json.loads((root/'reports/restore_admission.json').read_text())['passed']", "assert json.loads((root/'reports/restore_admission.json').read_text())['passed']\nassert json.loads((root/'reports/native_empty_admission.json').read_text())['passed']"); p.write_text(text)
p=root/'relay.py'; text=p.read_text(); text=text.replace("    if not all(c['message'].get('tool_calls') or str(c['message'].get('content') or '').strip() for c in choices):\n        raise ValueError('Empty visible assistant response')\n",'')
text=text.replace("record.update(api_outcome='completed',response_complete=True,model_reported=result.get('model'),", "record.update(api_outcome='completed',response_complete=True,empty_visible_response=not any(c['message'].get('tool_calls') or str(c['message'].get('content') or '').strip() for c in result['choices']),model_reported=result.get('model'),")
text=text.replace("            payload['messages'], image_audit=repair_messages", "            record['request_semantic_sha256']=__import__('hashlib').sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()\n            payload['messages'], image_audit=repair_messages")
text=text.replace("            receipt(label,record)\n            if not downstream_stream:", "            if record['empty_visible_response']: record['api_outcome']='completed_empty_visible'\n            receipt(label,record)\n            if not downstream_stream:")
p.write_text(text)
p=root/'observation_guard.py'; text=p.read_text().replace(" if event.get('hook_event_name')=='Stop':", " if event.get('hook_event_name')=='Stop':\n  if not str(event.get('last_assistant_message') or '').strip():\n   return 'An empty end-turn is not task delivery. Continue the actual task, build output/index.html, then provide a concise nonempty delivery statement.'",1)
p.write_text(text)
for name in names:
 if name.endswith('.py'): compile((root/name).read_text(),name,'exec')
meta=json.loads((root/'private/recovery/recovery_manifest.json').read_text()); manifest={'version':cfg['version'],'prior_protocol_failure_preserved':True,'valid_empty_stop_is_not_task_success':True,'native_stop_feedback_requires_nonempty_delivered_artifact':True,'no_generated_answer_or_reasoning_conversion':True,'adapter_no_extra_resampling':True,'official_cli_native_empty_retry_retained':True,'canary_excluded':True,'source_only_corrective_continuation':True,'official_vendor_and_scorer_unchanged':True,'files':[{'path':name,'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest()} for name in names],'source_checkpoint_hashes':meta['files']}
(root/'reports/phase_manifest.json').write_text(json.dumps(manifest,indent=2)); print(json.dumps({'version':cfg['version'],'source_files':len(meta['files']),'runtime_hashes':len(names)}))
