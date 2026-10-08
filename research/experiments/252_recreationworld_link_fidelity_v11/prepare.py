"""New declared corrective demonstration; preserve all previous results."""
import hashlib,json,shutil
from pathlib import Path
root=Path(__file__).resolve().parent; prior=root.parent/'250_recreationworld_observation_guard_v10'
s=json.loads((prior/'reports/pipeline_status.json').read_text()); assert s['state']=='native_finished'
for name in ('reports','ledger','runs','private/recovery/workspace'): (root/name).mkdir(parents=True,exist_ok=True)
names=['relay.py','vision_bridge.py','run_canary.py','container_entry.py','resume_cli.py','execution_guidance.txt','model_resource.json','observation_guard.py','asset_fetch.py','managed-settings.json']
for name in names: shutil.copy2(prior/name,root/name)
for name in ['live_check.py','guard_live_check.py','scorer_progress.py','audit_attempt.py','export_observable.py','reference_action_review.py','authorship_review.py']:
 shutil.copy2(prior/'reports'/name,root/'reports'/name)
for name in ['model_acceptance.json','guard_fixture_admission.json','native_hook_admission.json']: shutil.copy2(prior/'reports'/name,root/'reports'/name)
workspace=prior/'runs'/s['attempt']/'recreation'; recovery=root/'private/recovery'
items=['src','public']+[name for name in ['index.html','package-lock.json','package.json','tsconfig.json','vite.config.ts','tailwind.config.js','tailwind.config.ts','postcss.config.js','postcss.config.cjs'] if (workspace/name).is_file()]
for name in ['recreation_manifest.json','task.json']:
 p=recovery/'workspace'/name
 if p.exists(): p.unlink()
assert 'src' in items and 'public' in items
for item in items:
 p=workspace/item; dest=recovery/'workspace'/item
 if p.is_dir(): shutil.copytree(p,dest,dirs_exist_ok=True)
 else: shutil.copy2(p,dest)
hashes={str(p.relative_to(recovery/'workspace')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (recovery/'workspace').rglob('*') if p.is_file()}
(recovery/'recovery_manifest.json').write_text(json.dumps({'source_attempt':s['attempt'],'source_version':s['version'],'workspace_items':items,'files':hashes,'no_sessions_or_evaluation_data':True,'model_authored_source_only':True},indent=2))
cfg=json.loads((root/'model_resource.json').read_text()); cfg.update(version='rw_web_deepseek_link_fidelity_v11',local_port=8167,fresh_clean_scaffold=False,source_checkpoint=s['attempt'],recovery=False,corrective_demonstration=True)
(root/'model_resource.json').write_text(json.dumps(cfg,indent=2))
for name,old,new in [('run_canary.py','8166/250_recreationworld','8167/252_recreationworld'),('container_entry.py','8796','8797')]:
 p=root/name; p.write_text(p.read_text().replace(old,new))
p=root/'run_canary.py'; text=p.read_text(); text=text.replace("'--mount',f'type=bind,src={out},dst=/results'", "'--mount',f'type=bind,src={ROOT}/private/recovery,dst=/recovery,readonly','--mount',f'type=bind,src={out},dst=/results'")
p.write_text(text)
p=root/'resume_cli.py'; p.write_text('''import hashlib,json,os,shutil,sys,tempfile
from pathlib import Path
args=sys.argv[1:]
if '-p' in args:
 snapshot=Path('/recovery'); meta=json.loads((snapshot/'recovery_manifest.json').read_text())
 for name,sha in meta['files'].items():
  assert hashlib.sha256((snapshot/'workspace'/name).read_bytes()).hexdigest()==sha,name
 for item in meta['workspace_items']:
  source=snapshot/'workspace'/item; dest=Path.cwd()/item
  if source.is_dir(): shutil.copytree(source,dest,dirs_exist_ok=True)
  else: shutil.copy2(source,dest)
 original=sys.stdin.buffer.read(); guidance=Path('/results/skill_context.md').read_bytes()
 stream=tempfile.TemporaryFile(); stream.write(original+b"\\n\\n"+guidance); stream.seek(0); os.dup2(stream.fileno(),0)
os.execv('/usr/local/bin/claude-original',['claude',*args])
''')
p=root/'execution_guidance.txt'; text=p.read_text().replace('After the first homepage screenshot and accessibility snapshot, implement a working homepage and BUILD immediately. Then add internal pages incrementally.', 'The workspace contains the previous model-authored application, restored without any session, tests or evaluation data. Inspect and improve that implementation rather than rebuilding it from scratch.')
text+='\nFunctional fidelity reminder from the visible candidate source: the Link component currently replaces many destinations with # and prevents navigation. Inspect that behavior. Verify actual link text and destinations through the allowed reference snapshots and ordinary interactions; implement the observed behavior rather than placeholder links or guessed/paraphrased labels. Verify internal routes, external or offline target behavior, navigation menus, search and contact links in the candidate. Do not inspect any evaluation files or optimize against private tests. This is a declared corrective continuation demonstration, not an independent baseline.\n'
p.write_text(text)
for name in names: compile((root/name).read_text(),name,'exec') if name.endswith('.py') else None
manifest={'version':cfg['version'],'previous_attempt':s['attempt'],'previous_frozen_results_preserved':True,'source_only_corrective_continuation':True,'score_feedback_or_private_tests_given_to_agent':False,'original_vendor_and_scorer_unchanged':True,'canary_excluded':True,'files':[{'path':name,'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest()} for name in names],'source_checkpoint_hashes':hashes}
(root/'reports/phase_manifest.json').write_text(json.dumps(manifest,indent=2))
(root/'README.md').write_text('# RW 单题纠正演示 v11\n\n从250模型生成的src/public和构建配置恢复，原分/失败/轨迹完整保留。不恢复会话或evaluation；原生agent、任务、评分不改。只纠正自身源码可见的占位链接，并通过允许的公开观察验证，不给模型私有测试或分数。非独立baseline，canary排除headline。\n')
print(json.dumps({'version':cfg['version'],'runtime_hashes':len(names),'source_hashes':len(hashes),'source_items':items}))
