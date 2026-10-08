"""Read-only observer: distinguish real native activity from controller liveness."""
import hashlib,json,os,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'288_rw_parallel_evolution_collection'
def write(name,data):
 p=ROOT/'reports'/name;t=p.with_suffix('.tmp');t.write_text(json.dumps(data,indent=2));t.replace(p)
def alive(j):
 try:return Path('/proc/sys/kernel/random/boot_id').read_text().strip()==j['boot_id'] and Path(f"/proc/{j['pid']}/stat").read_text().split(') ',1)[1].split()[19]==j['start_ticks']
 except (FileNotFoundError,KeyError):return False
PROBE='''import json,collections
from pathlib import Path
cp=Path('/workspace/recreation/.counted_correction_restored')
session=json.loads(cp.read_text()) if cp.exists() else None
p=Path('/home/agent/.claude/projects/-workspace-recreation')/((session or {}).get('session_id','missing')+'.jsonl')
result={'restored_round':session}
if p.exists():
 b=p.read_bytes();types=collections.Counter();tools=collections.Counter();bad=0;images=0
 for line in b.splitlines():
  try:j=json.loads(line)
  except Exception:bad+=1;continue
  types[j.get('type','unknown')]+=1
  content=(j.get('message') or {}).get('content',[])
  if not isinstance(content,list):continue
  for block in content:
   if not isinstance(block,dict):continue
   if block.get('type')=='tool_use':tools[block.get('name','unknown')]+=1
   if block.get('type')=='tool_result' and isinstance(block.get('content'),list):images+=sum(x.get('type')=='image' for x in block['content'] if isinstance(x,dict))
 result['native_session']={'bytes':len(b),'lines':b.count(b'\\n'),'mtime':p.stat().st_mtime,'invalid_or_partial_lines':bad,'types':dict(types),'tool_calls':dict(tools),'inline_image_blocks':images,'includes_inherited_history':True}
root=Path('/workspace/recreation/src');files=[p for p in root.rglob('*') if p.is_file()] if root.exists() else []
result['candidate_source']={'files':len(files),'latest_mtime':max((p.stat().st_mtime for p in files),default=None)}
print(json.dumps(result))'''
def snapshot():
 actor=json.loads((ROOT/'reports/active/squoosh.json').read_text());j={'epoch':time.time(),'actor':actor,'controller_alive':alive(actor),'skills_learning_started':False,'benchmark_250_evaluation_started':False}
 r=subprocess.run(['docker','inspect',actor['container']],capture_output=True,text=True)
 if r.returncode==0:
  c=json.loads(r.stdout)[0];j['container']={k:c['State'].get(k) for k in ('Status','Pid','OOMKilled','ExitCode')};j['limits']={k:c['HostConfig'].get(k) for k in ('Memory','MemorySwap','NanoCpus')}
  if c['State']['Running']:
   r=subprocess.run(['docker','exec',actor['container'],'python3','-c',PROBE],capture_output=True,text=True,timeout=30)
   j['native_activity']=json.loads(r.stdout) if r.returncode==0 else {'probe_returncode':r.returncode}
 receipts=[]
 for p in (OLD/'ledger').glob('*.json'):
  try:x=json.loads(p.read_text())
  except (FileNotFoundError,json.JSONDecodeError):continue
  if x.get('route','').startswith('/293/'+actor['attempt']+'/'):receipts.append(x)
 j['api']={'requests':len(receipts),'complete':sum(bool(x.get('response_complete')) for x in receipts),'failed':sum(x.get('api_outcome')=='transport_or_protocol_failure' for x in receipts),'pending':sum(x.get('api_outcome')=='in_progress' for x in receipts),'recovered_image_blocks_accumulated':sum(x.get('image_transport',{}).get('recovered_image_blocks',0) for x in receipts),'accumulated_images_include_history_replay':True}
 mem={k:int(v.split()[0]) for k,v in (line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())};j['available_mib']=mem['MemAvailable']//1024
 write('current_health.json',j)
 return j
def main():
 identity={'pid':os.getpid(),'start_ticks':Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()[19],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'interval_seconds':30,'read_only_actor':True}
 write('current_observer_identity.json',identity)
 while True:
  try:
   state=snapshot()
   if not state['controller_alive'] and (ROOT/'reports/continuation_status.json').exists():
    status=json.loads((ROOT/'reports/continuation_status.json').read_text())
    if status['state']!='waiting_resource':return
  except Exception as exc:write('current_observer_error.json',{'epoch':time.time(),'error_class':type(exc).__name__})
  time.sleep(30)
if __name__=='__main__':main()
