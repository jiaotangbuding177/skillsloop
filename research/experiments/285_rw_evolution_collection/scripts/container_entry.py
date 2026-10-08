"""Native first rollout; no old task guidance, CLI replacement, or score changes."""
import os,subprocess,sys,time,urllib.request,shutil,json,hashlib
from pathlib import Path
env=os.environ.copy()
base=sys.argv[sys.argv.index('--model-base-url')+1]
model=sys.argv[sys.argv.index('--model')+1]
stage=sys.argv[sys.argv.index('--stage')+1]
env.update(UPSTREAM_BASE_URL=base.rstrip('/')+'/chat/completions',UPSTREAM_API_KEY='local',GATEWAY_API_KEY='local',DEFAULT_UPSTREAM_MODEL=model,FORCE_UPSTREAM_MODEL='true',HOST='127.0.0.1',PORT='8788',UPSTREAM_TIMEOUT_SECONDS='1800',LOG_PAYLOAD_MAX_CHARS='0',PRETTY_LOGS='false',RB_AGENT_BASE_URL='http://127.0.0.1:8788',RB_AGENT_API_KEY='local')
Path('/var/lib/mockweb-scorer').mkdir(parents=True,exist_ok=True);Path('/var/lib/mockweb-scorer').chmod(0o700)
proxy=None
try:
 if stage=='recreation_eval':
  # Empty fresh actor state: no corravale sessions, code or corrective hints.
  target=Path('/home/agent/.claude/CLAUDE.md')
  if target.exists():raise RuntimeError('Unexpected actor guidance in clean image')
  proxy=subprocess.Popen(['/usr/local/bin/rb-claude-code-proxy'],env=env,stdout=open('/results/model_proxy.log','w'),stderr=subprocess.STDOUT)
  for _ in range(60):
   if proxy.poll() is not None:raise RuntimeError('Official protocol proxy exited')
   try:
    req=urllib.request.Request('http://127.0.0.1:8788/v1/models',headers={'Authorization':'Bearer local'})
    with urllib.request.urlopen(req,timeout=1):break
   except Exception:time.sleep(.5)
  else:raise RuntimeError('Proxy not ready')
 rc=subprocess.call(['python3','/workspace/RecreationBench/scripts/core/pipeline.py',*sys.argv[1:]],env=env)
finally:
 # Official 64MiB collection cap must not silently discard a long raw session.
 root=Path('/home/agent/.claude/projects');out=Path('/results/private_raw_sessions');out.mkdir(exist_ok=True);out.chmod(0o700)
 manifest=[]
 if root.exists():
  for p in root.rglob('*'):
   if not p.is_file():continue
   dst=out/p.relative_to(root);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
   a=hashlib.sha256(p.read_bytes()).hexdigest();b=hashlib.sha256(dst.read_bytes()).hexdigest();assert a==b
   manifest.append({'file':str(p.relative_to(root)),'bytes':p.stat().st_size,'source_sha256':a,'copied_sha256':b})
 (out/'copy_manifest.json').write_text(json.dumps({'files':manifest,'size_cap':None,'raw_private_not_learning_input':True},indent=2))
 if proxy is not None:proxy.terminate()
sys.exit(rc)
