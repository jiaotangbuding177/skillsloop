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
before=source_hashes(); (results/'candidate_source_before.json').write_text(json.dumps(before,indent=2))
node_modules=Path('/opt/mockweb-bench/batch_run/node_modules')
assert (node_modules/'@playwright/test/package.json').is_file(),'Pinned native functional runtime unavailable'
env=os.environ.copy(); env.update(PYTHONPATH=str(scripts),MOCKWEB_NODE_MODULES=str(node_modules),MOCKWEB_AGENT_UID='1002',MOCKWEB_AGENT_GID='1002',MOCKWEB_AGENT_RUN_PREFIX='setpriv --reuid=agent --regid=agent --clear-groups -- env HOME=/home/agent')
cmd=['python3','/opt/rw251/observe_runner.py','--dataset','/workspace/dataset','--domain','corravale.example','--model','deepseek-v4-flash-vision-exp','--workspace',str(workspace),'--browser-mcp','playwright','--skip-agent','--vlm-judge','--vlm-model','deepseek-v4-flash-vision-exp','--vlm-backend','openai-compatible','--vlm-base-url','http://127.0.0.1:8166/251_recreationworld/complete_scoring/v1','--vlm-api-key','local','--vlm-mode','assertion','--vlm-max-concurrency','2']
(results/'evaluation_status.json').write_text(json.dumps({'version':'rw_web_complete_scoring_v1','state':'running','agent_launched':False,'vlm_judge_enabled':True,'source_hash_count':len(before),'started_epoch':time.time()},indent=2))
with (results/'run.json').open('w') as out, (results/'scorer.log').open('w') as log:
 rc=subprocess.call(cmd,cwd=scripts/'web',env=env,stdout=out,stderr=log)
after=source_hashes(); (results/'candidate_source_after.json').write_text(json.dumps(after,indent=2))
subprocess.check_call(['cp','-a',str(workspace/'eval_results'),str(results/'eval_results')])
if (workspace/'output/index.html').is_file():
 shutil.copy2(workspace/'output/index.html',results/'scored_index.html')
 (results/'scored_artifact_sha256.json').write_text(json.dumps({'index_html_sha256':hashlib.sha256((results/'scored_index.html').read_bytes()).hexdigest(),'official_rebuild':True,'model_source_unchanged':before==after},indent=2))
(results/'evaluation_status.json').write_text(json.dumps({'version':'rw_web_complete_scoring_v1','state':'native_finished' if rc==0 else 'failed','returncode':rc,'agent_launched':False,'vlm_judge_enabled':True,'source_unchanged':before==after,'source_hash_count':len(before),'finished_epoch':time.time()},indent=2))
print(json.dumps({'returncode':rc,'source_unchanged':before==after}))
