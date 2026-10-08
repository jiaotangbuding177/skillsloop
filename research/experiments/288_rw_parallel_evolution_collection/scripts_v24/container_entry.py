import os,sys,subprocess,time,urllib.request,json,shutil,hashlib
from pathlib import Path
env=os.environ.copy();base=sys.argv[sys.argv.index('--model-base-url')+1];model=sys.argv[sys.argv.index('--model')+1];stage=sys.argv[sys.argv.index('--stage')+1]
env.update(UPSTREAM_BASE_URL=base.rstrip('/')+'/chat/completions',UPSTREAM_API_KEY='local',GATEWAY_API_KEY='local',DEFAULT_UPSTREAM_MODEL=model,FORCE_UPSTREAM_MODEL='true',HOST='127.0.0.1',PORT='8788',UPSTREAM_TIMEOUT_SECONDS='1800',LOG_PAYLOAD_MAX_CHARS='0',PRETTY_LOGS='false',RB_AGENT_BASE_URL='http://127.0.0.1:8788',RB_AGENT_API_KEY='local',NODE_OPTIONS='--max-old-space-size=384')
Path('/var/lib/mockweb-scorer').mkdir(exist_ok=True,parents=True);Path('/var/lib/mockweb-scorer').chmod(0o700)
checkpoint=Path('/previous-round')
if stage=='recreation_eval' and checkpoint.exists():
 cli=Path('/usr/local/bin/claude');cli.rename('/usr/local/bin/claude-native');cli.write_text('#!/bin/sh\nexec python3 /opt/rw288/round_cli.py "$@"\n');cli.chmod(0o755)
proxy=None
try:
 if stage=='recreation_eval':
  proxy=subprocess.Popen(['/usr/local/bin/rb-claude-code-proxy'],env=env,stdout=open('/results/model_proxy.log','w'),stderr=subprocess.STDOUT)
  for _ in range(60):
   if proxy.poll() is not None:raise RuntimeError('Proxy exited')
   try:
    with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8788/v1/models',headers={'Authorization':'Bearer local'}),timeout=1):break
   except Exception:time.sleep(.5)
  else:raise RuntimeError('Proxy readiness failure')
 rc=subprocess.call(['python3','/workspace/RecreationBench/scripts/core/pipeline.py',*sys.argv[1:]],env=env)
finally:
 root=Path('/home/agent/.claude/projects');out=Path('/results/private_raw_sessions');out.mkdir(exist_ok=True);out.chmod(0o700);manifest=[]
 if root.exists():
  for src in root.rglob('*'):
   if not src.is_file():continue
   dst=out/src.relative_to(root);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
   a=hashlib.sha256(src.read_bytes()).hexdigest();b=hashlib.sha256(dst.read_bytes()).hexdigest();assert a==b
   manifest.append({'file':str(src.relative_to(root)),'bytes':src.stat().st_size,'source_sha256':a,'copied_sha256':b})
 (out/'copy_manifest.json').write_text(json.dumps({'files':manifest,'size_cap':None,'raw_private_not_learning_input':True},indent=2))
 if proxy:proxy.terminate()
sys.exit(rc)
