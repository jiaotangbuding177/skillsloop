"""Official reference-candidate self-check; no agent, VLM, or source edits."""
import json,shutil,subprocess,time
from pathlib import Path
root=Path('/results'); workspace=Path('/workspace/reference_selfcheck_256_v2'); workspace.mkdir(exist_ok=True)
assert Path('/opt/mockweb-bench/batch_run/node_modules/@playwright/test/package.json').is_file()
cmd=['python3','-m','runner.run_agent','--dataset','/workspace/dataset','--domain','corravale.example','--workspace',str(workspace),'--reference-candidate','--browser-mcp','playwright']
(root/'status.json').write_text(json.dumps({'state':'running','agent_launched':False,'vlm_enabled':False,'diagnostic_only':True,'started':time.time()},indent=2))
with (root/'run.json').open('w') as out,(root/'scorer.log').open('w') as log:
 rc=subprocess.call(cmd,cwd='/workspace/RecreationBench/scripts/web',stdout=out,stderr=log,env={**__import__('os').environ,'PYTHONPATH':'/workspace/RecreationBench/scripts','MOCKWEB_NODE_MODULES':'/opt/mockweb-bench/batch_run/node_modules'})
if (workspace/'eval_results').exists(): shutil.copytree(workspace/'eval_results',root/'eval_results',dirs_exist_ok=True)
(root/'status.json').write_text(json.dumps({'state':'finished' if rc==0 else 'failed','returncode':rc,'agent_launched':False,'vlm_enabled':False,'diagnostic_only':True,'finished':time.time()},indent=2))
print(json.dumps({'returncode':rc,'reference_candidate_only':True}))
