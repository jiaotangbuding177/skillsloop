"""New-version transport composition; official agent and scorer unchanged."""
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

env=os.environ.copy()
base=sys.argv[sys.argv.index('--model-base-url')+1]
model=sys.argv[sys.argv.index('--model')+1]
env.update(UPSTREAM_BASE_URL=base.rstrip('/')+'/chat/completions', UPSTREAM_API_KEY='local',
    GATEWAY_API_KEY='local',DEFAULT_UPSTREAM_MODEL=model,FORCE_UPSTREAM_MODEL='true',
    HOST='127.0.0.1',PORT='8794',UPSTREAM_TIMEOUT_SECONDS='1800',LOG_PAYLOAD_MAX_CHARS='0',
    PRETTY_LOGS='false',RB_AGENT_BASE_URL='http://127.0.0.1:8794',RB_AGENT_API_KEY='local')
Path('/var/lib/mockweb-scorer').mkdir(parents=True,exist_ok=True)
Path('/var/lib/mockweb-scorer').chmod(0o700)
context=Path('/results/skill_context.md')
target=Path('/home/agent/.claude/CLAUDE.md'); target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(context.read_text())
cli=Path('/usr/local/bin/claude')
cli.rename('/usr/local/bin/claude-original')
cli.write_text('#!/bin/sh\nexec python3 /opt/rw218/resume_cli.py "$@"\n')
cli.chmod(0o755)
proxy=subprocess.Popen(['/usr/local/bin/rb-claude-code-proxy'],env=env,stdout=open('/results/model_proxy.log','w'),stderr=subprocess.STDOUT)
try:
    for _ in range(60):
        if proxy.poll() is not None: raise RuntimeError('Official proxy exited')
        try:
            with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8794/v1/models',headers={'Authorization':'Bearer local'}),timeout=1): break
        except Exception: time.sleep(.5)
    else: raise RuntimeError('Proxy not ready')
    sys.exit(subprocess.call(['python3','/workspace/RecreationBench/scripts/core/pipeline.py',*sys.argv[1:]],env=env))
finally:
    proxy.terminate()
