"""Add safe response diagnostics only; preserve prior protocol failures."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent; prior=root.parent/'252_recreationworld_link_fidelity_v11'
for name in ['reports','ledger','runs','private/recovery']: (root/name).mkdir(parents=True,exist_ok=True)
names=['relay.py','vision_bridge.py','run_canary.py','container_entry.py','resume_cli.py','execution_guidance.txt','model_resource.json','observation_guard.py','asset_fetch.py','managed-settings.json']
for name in names: shutil.copy2(prior/name,root/name)
shutil.copytree(prior/'private/recovery',root/'private/recovery',dirs_exist_ok=True)
for name in ['live_check.py','guard_live_check.py','scorer_progress.py','audit_attempt.py','export_observable.py','reference_action_review.py','authorship_review.py','finished_tools.py','restore_fixture.py','restore_admission.py','launch.py','model_acceptance.json','guard_fixture_admission.json','native_hook_admission.json']:
 shutil.copy2(prior/'reports'/name,root/'reports'/name)
cfg=json.loads((root/'model_resource.json').read_text()); cfg.update(version='rw_web_deepseek_protocol_diagnostics_v12',local_port=8168)
(root/'model_resource.json').write_text(json.dumps(cfg,indent=2))
for name,old,new in [('run_canary.py','8167/252_recreationworld','8168/253_recreationworld'),('container_entry.py','8797','8798')]:
 p=root/name; p.write_text(p.read_text().replace(old,new))
p=root/'reports/launch.py'; text=p.read_text().replace("old=root.parent/'250_recreationworld_observation_guard_v10'","old=root.parent/'252_recreationworld_link_fidelity_v11'").replace("assert status['state']=='native_finished'","assert status['state']=='transport_failure'").replace('8167','8168').replace('8797','8798'); p.write_text(text)
p=root/'relay.py'; text=p.read_text().replace('def complete(result):','def complete(result, record=None):')
text=text.replace("    if not isinstance(result,dict) or result.get('error'): raise ValueError('Provider error or invalid object')", "    if record is not None and isinstance(result,dict):\n        record['response_shape']={'reported_model':result.get('model'),'choices':[{'finish_reason':c.get('finish_reason'),'content_characters':len(c.get('message',{}).get('content') or ''),'reasoning_characters':len(c.get('message',{}).get('reasoning_content') or ''),'tool_calls':len(c.get('message',{}).get('tool_calls') or [])} for c in result.get('choices') or []],'usage':result.get('usage')}\n    if not isinstance(result,dict) or result.get('error'): raise ValueError('Provider error or invalid object')")
text=text.replace('return complete(json.load(response))','return complete(json.load(response), record)')
text=text.replace("return complete({'id':result_id or label,'object':'chat.completion','model':model,'choices':output,'usage':usage})", "return complete({'id':result_id or label,'object':'chat.completion','model':model,'choices':output,'usage':usage}, record)")
text=text.replace('            receipt(label,record)\n            try: self.send(502', "            if isinstance(exc,ValueError) and str(exc) in ['Provider error or invalid object','Response incomplete, truncated or filtered','Empty visible assistant response','Provider stream error','Provider SSE ended without DONE']: record['protocol_error_reason']=str(exc)\n            receipt(label,record)\n            try: self.send(502")
p.write_text(text)
for name in names:
 if name.endswith('.py'): compile((root/name).read_text(),name,'exec')
meta=json.loads((root/'private/recovery/recovery_manifest.json').read_text())
manifest={'version':cfg['version'],'prior_failed_attempt':json.loads((prior/'reports/pipeline_status.json').read_text())['attempt'],'all_prior_errors_preserved':True,'diagnostic_fields_only_no_payload_or_reasoning_text':True,'gate_behavior_unchanged':True,'original_vendor_and_scorer_unchanged':True,'source_only_corrective_continuation':True,'score_feedback_given_to_agent':False,'canary_excluded':True,'files':[{'path':name,'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest()} for name in names],'source_checkpoint_hashes':meta['files']}
(root/'reports/phase_manifest.json').write_text(json.dumps(manifest,indent=2)); print(json.dumps({'version':cfg['version'],'source_files':len(meta['files']),'runtime_hashes':len(names)}))
