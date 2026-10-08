import hashlib,json,os,py_compile,socket,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
old=ROOT.parent/'244_recreationworld_vision_bridge_v7'; status=json.loads((old/'reports/pipeline_status.json').read_text()); name='rw238-'+status['attempt']
assert subprocess.check_output(['docker','inspect','--format','{{.State.Running}}',name],text=True).strip()=='false'
for port in [8164,8794]:
 with socket.socket() as s:
  if s.connect_ex(('127.0.0.1',port))==0: raise RuntimeError('Port occupied')
files=['relay.py','vision_bridge.py','run_canary.py','container_entry.py','resume_cli.py','execution_guidance.txt','model_resource.json']
for f in files:
 if f.endswith('.py'): py_compile.compile(str(ROOT/f),doraise=True)
assert json.loads((ROOT/'reports/full_image_path_admission.json').read_text())['passed']
manifest={'version':'rw_web_deepseek_clean_vision_v8','fresh_clean_scaffold':True,'restored_prior_source':False,'restored_prior_session':False,'additional_guidance':True,'official_vendor_and_score_unchanged':True,'canary_excluded':True,'prior_agent_failure':'reference DOM harvesting/original class reuse, retained negative','files':[{'path':x,'sha256':hashlib.sha256((ROOT/x).read_bytes()).hexdigest()} for x in files]}
(ROOT/'reports/phase_manifest.json').write_text(json.dumps(manifest,indent=2))
p=subprocess.Popen([sys.executable,str(ROOT/'relay.py')],stdin=subprocess.DEVNULL,stdout=open(ROOT/'reports/relay.log','w'),stderr=subprocess.STDOUT,start_new_session=True)
for _ in range(40):
 try:
  with urllib.request.urlopen('http://127.0.0.1:8164/health',timeout=1): break
 except Exception: time.sleep(.25)
else: raise RuntimeError('Relay unavailable')
print(json.dumps({'relay_pid':p.pid,'freeze_files':len(files),'old_agent_stopped':True,'clean_scaffold':True}),flush=True)
os.execv(sys.executable,[sys.executable,str(ROOT/'run_canary.py')])
