"""Provision the official pinned Anthropic/OpenAI proxy, then enter official RB.

Transport composition only; no replacement agent or scorer. No production key.
"""
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

env=os.environ.copy()
base=sys.argv[sys.argv.index('--model-base-url')+1]
model=sys.argv[sys.argv.index('--model')+1]
env.update(UPSTREAM_BASE_URL=base.rstrip('/')+'/chat/completions',
    UPSTREAM_API_KEY='local', GATEWAY_API_KEY='local', DEFAULT_UPSTREAM_MODEL=model,
    FORCE_UPSTREAM_MODEL='true',HOST='127.0.0.1',PORT='8788',
    UPSTREAM_TIMEOUT_SECONDS='240',LOG_PAYLOAD_MAX_CHARS='0',PRETTY_LOGS='false',
    RB_AGENT_BASE_URL='http://127.0.0.1:8788',RB_AGENT_API_KEY='local')
# The source mount is root-only even before dataset materialization begins.
Path('/var/lib/mockweb-scorer').mkdir(parents=True,exist_ok=True)
Path('/var/lib/mockweb-scorer').chmod(0o700)
stage=sys.argv[sys.argv.index('--stage')+1]
if stage=='recreation_eval':
    context=Path('/results/skill_context.md')
    if not context.is_file(): raise RuntimeError('Declared treatment context missing')
    target=Path('/home/agent/.claude/CLAUDE.md')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(context.read_text(),encoding='utf-8')
proxy=None
try:
    if stage=='recreation_eval':
        log=open('/results/model_proxy.log','w')
        proxy=subprocess.Popen(['/usr/local/bin/rb-claude-code-proxy'],env=env,stdout=log,stderr=subprocess.STDOUT)
        for _ in range(60):
            if proxy.poll() is not None: raise RuntimeError('Official protocol proxy exited')
            try:
                req=urllib.request.Request('http://127.0.0.1:8788/v1/models',headers={'Authorization':'Bearer local'})
                with urllib.request.urlopen(req,timeout=1): break
            except Exception: time.sleep(0.5)
        else: raise RuntimeError('Official protocol proxy not ready')
    rc=subprocess.call(['python3','/workspace/RecreationBench/scripts/core/pipeline.py',*sys.argv[1:]],env=env)
    sys.exit(rc)
finally:
    if proxy is not None:
        proxy.terminate()
        try: proxy.wait(timeout=10)
        except subprocess.TimeoutExpired: proxy.kill()
