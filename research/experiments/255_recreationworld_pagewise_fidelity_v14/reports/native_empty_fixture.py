"""Synthetic local server + official CLI admission; no provider or benchmark task."""
import hashlib,importlib.util,json,os,subprocess,threading,time,urllib.request
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
calls=[]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args): pass
 def do_GET(self):
  data=json.dumps({'object':'list','data':[{'id':'deepseek-v4-flash-vision-exp','object':'model'}]}).encode(); self.send_response(200); self.end_headers(); self.wfile.write(data)
 def do_POST(self):
  body=json.loads(self.rfile.read(int(self.headers.get('Content-Length',0)))); main='ADMISSION_EMPTY_RECOVERY' in json.dumps(body.get('messages',[]))
  index=sum(x['main'] for x in calls); content='' if main and index==0 else 'Admission fixture complete.'
  sha=hashlib.sha256(json.dumps(body,sort_keys=True).encode()).hexdigest()
  calls.append({'main':main,'empty':not bool(content),'request_hash':sha,'same_as_previous':bool(calls and calls[-1]['request_hash']==sha)})
  result={'id':'admission','object':'chat.completion','model':'deepseek-v4-flash-vision-exp','choices':[{'index':0,'message':{'role':'assistant','content':content},'finish_reason':'stop'}],'usage':{'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}}
  self.send_response(200)
  if body.get('stream'):
   self.send_header('Content-Type','text/event-stream'); self.end_headers()
   chunk={'id':'admission','object':'chat.completion.chunk','model':result['model'],'choices':[{'index':0,'delta':{'role':'assistant','content':content},'finish_reason':None}]}
   payload='data: '+json.dumps(chunk)+'\n\n'; chunk['choices']=[{'index':0,'delta':{},'finish_reason':'stop'}]; payload+='data: '+json.dumps(chunk)+'\n\ndata: [DONE]\n\n'; self.wfile.write(payload.encode())
  else: self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(json.dumps(result).encode())
server=ThreadingHTTPServer(('127.0.0.1',18169),Handler); threading.Thread(target=server.serve_forever,daemon=True).start()
policy=Path('/etc/claude-code/managed-settings.json'); policy.parent.mkdir(parents=True,exist_ok=True); policy.write_bytes(Path('/opt/rw218/managed-settings.json').read_bytes())
w=Path('/workspace/recreation'); (w/'src').mkdir(parents=True,exist_ok=True); (w/'output').mkdir(exist_ok=True)
(w/'src/App.tsx').write_text('// synthetic admission only; never benchmark candidate\n'); (w/'output/index.html').write_text('<html>synthetic admission only</html>'); subprocess.check_call(['chown','-R','1002:1002',str(w)])
env=os.environ.copy(); env.update(UPSTREAM_BASE_URL='http://127.0.0.1:18169/chat/completions',UPSTREAM_API_KEY='local',GATEWAY_API_KEY='local',DEFAULT_UPSTREAM_MODEL='deepseek-v4-flash-vision-exp',FORCE_UPSTREAM_MODEL='true',HOST='127.0.0.1',PORT='8800',UPSTREAM_TIMEOUT_SECONDS='60',LOG_PAYLOAD_MAX_CHARS='0',PRETTY_LOGS='false')
proxy=subprocess.Popen(['/usr/local/bin/rb-claude-code-proxy'],env=env,stdout=open('/results/empty_fixture_proxy.log','w'),stderr=subprocess.STDOUT)
try:
 for _ in range(60):
  try: urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8800/v1/models',headers={'Authorization':'Bearer local'}),timeout=1).close(); break
  except Exception: time.sleep(.5)
 else: raise RuntimeError('proxy unavailable')
 cmd=['runuser','-u','agent','--','env','HOME=/home/agent','ANTHROPIC_BASE_URL=http://127.0.0.1:8800','ANTHROPIC_AUTH_TOKEN=local','claude','-p','--model','deepseek-v4-flash-vision-exp','--dangerously-skip-permissions','--output-format','stream-json','--verbose']
 with open('/results/native_empty_raw.jsonl','w') as out: rc=subprocess.run(cmd,input='ADMISSION_EMPTY_RECOVERY: isolated synthetic protocol admission. Finish with a concise statement. Do not run tools or modify files.',text=True,stdout=out,stderr=subprocess.STDOUT,cwd=w,timeout=120).returncode
 logs=[json.loads(x) for x in (w/'observation_guard_events.jsonl').read_text().splitlines()]
 rows=[json.loads(x) for x in Path('/results/native_empty_raw.jsonl').read_text().splitlines() if x.startswith('{')]
 blocked=any(x['event']=='Stop' and x['blocked'] and 'empty end-turn' in (x.get('reason') or '') for x in logs)
 result=next((x for x in reversed(rows) if x.get('type')=='result'),{})
 spec=importlib.util.spec_from_file_location('guard_fixture','/opt/rw218/observation_guard.py'); guard=importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
 empty_decision=guard.decide({'hook_event_name':'Stop','last_assistant_message':''})
 recovered=rc==0 and any(x['empty'] for x in calls) and len(calls)>=2 and bool(result.get('result')) and not result.get('is_error')
 Path('/results/native_empty_events.json').write_text(json.dumps(logs,indent=2))
 value={'passed':recovered and bool(empty_decision),'native_cli_recovered_empty':recovered,'separate_stop_empty_unit_blocked':bool(empty_decision),'returncode':rc,'native_stop_blocked_first_empty':blocked,'native_stop_events':sum(x['event']=='Stop' for x in logs),'synthetic_server_calls':calls,'nonempty_final_result':bool(result.get('result')),'provider_called':False,'synthetic_never_benchmark':True}
 Path('/results/native_empty_admission.json').write_text(json.dumps(value,indent=2)); print(json.dumps(value))
finally: proxy.terminate(); server.shutdown()
