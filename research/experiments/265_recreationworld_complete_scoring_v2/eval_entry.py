"""Official scorer-only invocation on a frozen clone; no agent is launched."""
import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
workspace=Path('/workspace/recreation'); scripts=Path('/workspace/RecreationBench/scripts'); results=Path('/results')
def source_hashes():
 paths=[]
 for name in ['src','public']:
  paths.extend(p for p in (workspace/name).rglob('*') if p.is_file())
 paths.extend(workspace/name for name in ['index.html','package-lock.json','package.json','tsconfig.json','vite.config.ts','tailwind.config.js','tailwind.config.ts','postcss.config.js','postcss.config.cjs'] if (workspace/name).is_file())
 return {str(p.relative_to(workspace)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
# Restore the exact immutable runtime prepared by the official worker before its cleanup.
template=scripts/'web/template'; lock_sha=hashlib.sha256((template/'package-lock.json').read_bytes()).hexdigest()
seed=Path('/workspace/shared/mockweb-template-deps')/lock_sha/'node_modules'
assert seed.is_dir() and (seed.parent/'.complete').is_file(),'Official pinned runtime absent'
assert hashlib.sha256((workspace/'package-lock.json').read_bytes()).hexdigest()==lock_sha,'Dependency graph changed'
assert json.loads((workspace/'package.json').read_text())['dependencies']==json.loads((template/'package.json').read_text())['dependencies']
assert not (workspace/'node_modules').exists()
(workspace/'node_modules').symlink_to(seed,target_is_directory=True)
(results/'dependency_runtime.json').write_text(json.dumps({'lock_sha256':lock_sha,'official_seed_directory':str(seed),'restored_link_only':True,'network_called':False},indent=2))
before=source_hashes(); (results/'candidate_source_before.json').write_text(json.dumps(before,indent=2))
node_modules=Path('/opt/mockweb-bench/batch_run/node_modules')
assert (node_modules/'@playwright/test/package.json').is_file(),'Pinned native functional runtime unavailable'
env=os.environ.copy(); env.update(PYTHONPATH=str(scripts),MOCKWEB_NODE_MODULES=str(node_modules),MOCKWEB_AGENT_UID='1002',MOCKWEB_AGENT_GID='1002',MOCKWEB_AGENT_RUN_PREFIX='setpriv --reuid=agent --regid=agent --clear-groups -- env HOME=/home/agent')
cmd=['python3','/opt/rw251/observe_runner.py','--dataset','/workspace/dataset','--domain','corravale.example','--model','deepseek-v4-flash-vision-exp','--workspace',str(workspace),'--browser-mcp','playwright','--skip-agent','--vlm-judge','--vlm-model','deepseek-v4-flash-vision-exp','--vlm-backend','openai-compatible','--vlm-base-url','http://127.0.0.1:8172/265_recreationworld/complete_scoring/v2','--vlm-api-key','local','--vlm-mode','assertion','--vlm-max-concurrency','2']
(results/'evaluation_status.json').write_text(json.dumps({'version':'rw_web_complete_scoring_v2','state':'running','agent_launched':False,'vlm_judge_enabled':True,'source_hash_count':len(before),'started_epoch':time.time()},indent=2))
with (results/'run.json').open('w') as out, (results/'scorer.log').open('w') as log:
 rc=subprocess.call(cmd,cwd=scripts/'web',env=env,stdout=out,stderr=log)
native=json.loads((results/'run.json').read_text()) if rc==0 else {}
build_status=native.get('build_result',{}).get('status')
after=source_hashes(); (results/'candidate_source_after.json').write_text(json.dumps(after,indent=2))
subprocess.check_call(['cp','-a',str(workspace/'eval_results'),str(results/'eval_results')])
if (workspace/'output/index.html').is_file():
 shutil.copy2(workspace/'output/index.html',results/'scored_index.html')
 (results/'scored_artifact_sha256.json').write_text(json.dumps({'index_html_sha256':hashlib.sha256((results/'scored_index.html').read_bytes()).hexdigest(),'official_rebuild':build_status=='success','native_build_status':build_status,'model_source_unchanged':before==after},indent=2))
(results/'evaluation_status.json').write_text(json.dumps({'version':'rw_web_complete_scoring_v2','state':'native_finished' if rc==0 else 'failed','returncode':rc,'agent_launched':False,'vlm_judge_enabled':True,'source_unchanged':before==after,'source_hash_count':len(before),'finished_epoch':time.time(),'native_build_status':build_status},indent=2))
print(json.dumps({'returncode':rc,'source_unchanged':before==after}))
