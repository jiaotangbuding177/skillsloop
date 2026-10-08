"""Independent proxy and full raw archive around unchanged official pipeline."""
import os,sys,subprocess,time,urllib.request,json,shutil,hashlib,socket
from pathlib import Path
env=os.environ.copy();base=sys.argv[sys.argv.index('--model-base-url')+1];model=sys.argv[sys.argv.index('--model')+1];port=8793
with socket.socket() as sock:sock.bind(('127.0.0.1',port))
env.update(UPSTREAM_BASE_URL=base.rstrip('/')+'/chat/completions',UPSTREAM_API_KEY='local',GATEWAY_API_KEY='local',DEFAULT_UPSTREAM_MODEL=model,FORCE_UPSTREAM_MODEL='true',HOST='127.0.0.1',PORT=str(port),UPSTREAM_TIMEOUT_SECONDS='1800',LOG_PAYLOAD_MAX_CHARS='0',PRETTY_LOGS='false',RB_AGENT_BASE_URL=f'http://127.0.0.1:{port}',RB_AGENT_API_KEY='local',NODE_OPTIONS='--max-old-space-size=512')
Path('/var/lib/mockweb-scorer').mkdir(exist_ok=True,parents=True);Path('/var/lib/mockweb-scorer').chmod(0o700)
cli=Path('/usr/local/bin/claude');cli.rename('/usr/local/bin/claude-native');cli.write_text('#!/bin/sh\nexec python3 /opt/rw293/round_cli.py "$@"\n');cli.chmod(0o755)
proxy=None;rc=1
try:
 proxy=subprocess.Popen(['/usr/local/bin/rb-claude-code-proxy'],env=env,stdout=open('/results/model_proxy.log','w'),stderr=subprocess.STDOUT)
 for _ in range(60):
  assert proxy.poll() is None,'Own proxy exited'
  try:
   with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}/v1/models',headers={'Authorization':'Bearer local'}),timeout=1):
    assert proxy.poll() is None
    break
  except Exception:time.sleep(.5)
 else:raise RuntimeError('Own proxy not ready')
 rc=subprocess.call(['python3','/workspace/RecreationBench/scripts/core/pipeline.py',*sys.argv[1:]],env=env)
finally:
 source=Path('/home/agent/.claude/projects');dest=Path('/results/private_raw_sessions');dest.mkdir(exist_ok=True);dest.chmod(0o700);manifest=[]
 if source.exists():
  for src in source.rglob('*'):
   if not src.is_file():continue
   dst=dest/src.relative_to(source);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
   a=hashlib.sha256(src.read_bytes()).hexdigest();b=hashlib.sha256(dst.read_bytes()).hexdigest();assert a==b
   manifest.append({'file':str(src.relative_to(source)),'bytes':src.stat().st_size,'source_sha256':a,'copied_sha256':b})
 (dest/'copy_manifest.json').write_text(json.dumps({'files':manifest,'size_cap':None,'raw_private_not_learning_input':True},indent=2))
 if proxy:proxy.terminate()
sys.exit(rc)
