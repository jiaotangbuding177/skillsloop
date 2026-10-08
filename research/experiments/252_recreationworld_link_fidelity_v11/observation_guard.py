"""Declared canary observation policy using native Claude Code hooks."""
import hashlib,json,re,shlex,sys,time
from pathlib import Path

def decide(event):
 name=event.get('tool_name',''); inp=event.get('tool_input',{})
 if event.get('hook_event_name')=='Stop':
  app=Path('/workspace/recreation/src/App.tsx'); out=Path('/workspace/recreation/output/index.html')
  if not out.exists() or not app.exists() or 'Ready to build' in app.read_text():
   return 'Build and deliver the actual application, including output/index.html, before finishing.'
  if '<summary>' in event.get('last_assistant_message',''):
   return 'A context summary is not final delivery. Continue the task, rebuild if needed, and provide a concise final delivery statement.'
  newest=max((p.stat().st_mtime for p in Path('/workspace/recreation/src').rglob('*') if p.is_file()),default=0)
  if newest>out.stat().st_mtime+1:
   return 'Source changed after the delivered build. Rebuild and copy the new self-contained output/index.html before finishing.'
  return None
 if name.endswith('browser_evaluate') or name.endswith('browser_run_code'):
  return 'This declared variant uses screenshots, accessibility snapshots, ordinary interactions and network asset names. Scripted DOM/HTML/CSS/geometry harvesting is disabled.'
 if name!='Bash': return None
 c=inp.get('command','')
 try: args=shlex.split(c)
 except ValueError: args=[]
 if len(args)==4 and args[:2]==['python3','/opt/rw218/asset_fetch.py']: return None
 network=re.search(r'\b(curl|wget)\b|urllib|requests\.|httpx|http\.client|fetch\s*\(|https?://',c)
 if not network: return None
 urls=re.findall(r'https?://[^\s\"\'<>]+',c)
 if urls and all(re.match(r'https?://(localhost|127\.0\.0\.1):(4173|5173)(/|$)',u) for u in urls): return None
 return 'Reference HTML/CSS/text scraping is disabled. Observe with Playwright screenshots/snapshots/interactions. Download an explicit image/font URL only with: python3 /opt/rw218/asset_fetch.py URL /workspace/recreation/public/FILE. Local preview ports 4173 and 5173 remain available.'

def main():
 event=json.load(sys.stdin); reason=decide(event)
 try:
  with Path('/workspace/recreation/observation_guard_events.jsonl').open('a') as f:
   f.write(json.dumps({'time':time.time(),'event':event.get('hook_event_name'),'tool':event.get('tool_name'),'blocked':bool(reason),'input_sha256':hashlib.sha256(json.dumps(event.get('tool_input',{}),sort_keys=True).encode()).hexdigest(),'reason':reason})+'\n')
 except OSError: pass
 if reason:
  if event.get('hook_event_name')=='Stop': print(json.dumps({'decision':'block','reason':reason})); return
  print(reason,file=sys.stderr); sys.exit(2)
if __name__=='__main__': main()
