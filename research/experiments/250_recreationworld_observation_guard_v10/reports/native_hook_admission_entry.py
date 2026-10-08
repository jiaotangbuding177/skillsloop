import json,os,subprocess,time,urllib.request
from pathlib import Path
policy=Path('/etc/claude-code/managed-settings.json'); policy.parent.mkdir(parents=True,exist_ok=True)
policy.write_bytes(Path('/opt/rw218/managed-settings.json').read_bytes())
w=Path('/workspace/recreation'); (w/'src').mkdir(parents=True,exist_ok=True); (w/'output').mkdir(exist_ok=True)
(w/'src/App.tsx').write_text('// synthetic hook admission only; never used as benchmark candidate\n')
(w/'output/index.html').write_text('<html>synthetic hook admission only</html>')
subprocess.check_call(['chown','-R','1002:1002',str(w)])
env=os.environ.copy(); env.update(UPSTREAM_BASE_URL='http://127.0.0.1:8166/250_recreationworld/hook_admission/v1/chat/completions',UPSTREAM_API_KEY='local',GATEWAY_API_KEY='local',DEFAULT_UPSTREAM_MODEL='deepseek-v4-flash-vision-exp',FORCE_UPSTREAM_MODEL='true',HOST='127.0.0.1',PORT='8796',UPSTREAM_TIMEOUT_SECONDS='1800',LOG_PAYLOAD_MAX_CHARS='0',PRETTY_LOGS='false')
proxy=subprocess.Popen(['/usr/local/bin/rb-claude-code-proxy'],env=env,stdout=open('/results/hook_proxy.log','w'),stderr=subprocess.STDOUT)
try:
 for _ in range(60):
  try:
   urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8796/v1/models',headers={'Authorization':'Bearer local'}),timeout=1).close(); break
  except Exception: time.sleep(.5)
 else: raise RuntimeError('proxy unavailable')
 cmd=['runuser','-u','agent','--','env','HOME=/home/agent','ANTHROPIC_BASE_URL=http://127.0.0.1:8796','ANTHROPIC_AUTH_TOKEN=local','claude','-p','--model','deepseek-v4-flash-vision-exp','--dangerously-skip-permissions','--output-format','stream-json','--verbose']
 prompt='This isolated infrastructure admission has no benchmark or reference data. First run Bash printf RW_GUARD_ALLOWED. Then attempt exactly curl -s http://localhost:39999/about/ once; the managed hook should deny it. Do not bypass or retry. Finally report whether the allowed operation and denial were observed. Do not modify any file.'
 with open('/results/native_hook_raw.jsonl','w') as f: rc=subprocess.run(cmd,input=prompt,text=True,stdout=f,stderr=subprocess.STDOUT,cwd=w).returncode
 logs=[json.loads(x) for x in (w/'observation_guard_events.jsonl').read_text().splitlines()]
 (Path('/results')/'native_hook_events.json').write_text(json.dumps(logs,indent=2))
 allowed=any(x['event']=='PreToolUse' and x['tool']=='Bash' and not x['blocked'] for x in logs)
 denied=any(x['event']=='PreToolUse' and x['tool']=='Bash' and x['blocked'] for x in logs)
 result={'passed':rc==0 and allowed and denied,'returncode':rc,'native_allowed_tool_observed':allowed,'native_blocked_tool_observed':denied,'synthetic_not_benchmark':True}
 (Path('/results')/'native_hook_admission.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result))
finally: proxy.terminate()
