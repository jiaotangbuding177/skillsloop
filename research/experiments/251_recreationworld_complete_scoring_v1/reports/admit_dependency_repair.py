"""Verify official pinned dependencies rebuild unchanged source without network/API."""
import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]; current=json.loads((root/'reports/current_run.json').read_text()); out=Path(current['path'])
meta=json.loads((out/'phase_manifest.json').read_text())
code=r'''
import asyncio,hashlib,json,os,sys
from pathlib import Path
ws=Path('/workspace/recreation'); template=Path('/workspace/RecreationBench/scripts/web/template')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
lock=sha(template/'package-lock.json'); seed=Path('/workspace/shared/mockweb-template-deps')/lock/'node_modules'
assert seed.is_dir() and (seed.parent/'.complete').is_file()
assert sha(ws/'package-lock.json')==lock,'Candidate dependency graph differs from pinned template'
assert json.loads((ws/'package.json').read_text())['dependencies']==json.loads((template/'package.json').read_text())['dependencies']
before={str(p.relative_to(ws)):sha(p) for p in (ws/'src').rglob('*') if p.is_file()}
(ws/'node_modules').symlink_to(seed,target_is_directory=True)
os.environ.update(PYTHONPATH='/workspace/RecreationBench/scripts',MOCKWEB_AGENT_UID='1002',MOCKWEB_AGENT_GID='1002',MOCKWEB_AGENT_RUN_PREFIX='setpriv --reuid=agent --regid=agent --clear-groups -- env HOME=/home/agent')
sys.path.insert(0,'/workspace/RecreationBench/scripts/web'); sys.path.insert(0,'/workspace/RecreationBench/scripts')
from runner.run_agent import build_agent_output
result=asyncio.run(build_agent_output(ws))
after={str(p.relative_to(ws)):sha(p) for p in (ws/'src').rglob('*') if p.is_file()}
assert result['status']=='success',result
assert before==after
print(json.dumps({'passed':True,'native_build_status':result['status'],'pinned_lock_sha256':lock,'source_unchanged':True,'network_or_model_called':False,'artifact_sha256':sha(ws/'output/index.html')}))
'''
r=subprocess.run(['docker','run','--rm','--network','none','--cap-add','SYS_ADMIN','--cap-add','NET_ADMIN','--security-opt','seccomp=unconfined','--entrypoint','python3',meta['frozen_image_id'],'-c',code],capture_output=True,text=True)
assert r.returncode==0,r.stderr[-2500:]
value=json.loads(r.stdout); (root/'reports/dependency_repair_admission.json').write_text(json.dumps(value,indent=2)); print(json.dumps(value))
