import hashlib,json,os,py_compile,socket,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for port in [8162,8792]:
 with socket.socket() as s:
  if s.connect_ex(('127.0.0.1',port))==0: raise RuntimeError('Port already occupied')
for f in ['relay.py','run_canary.py','container_entry.py','resume_cli.py']: py_compile.compile(str(ROOT/f),doraise=True)
meta=json.loads((ROOT/'private/recovery/recovery_manifest.json').read_text())
assert all(hashlib.sha256((ROOT/'private/recovery'/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in meta['files'])
assert json.loads((ROOT/'reports/stream_vision_admission.json').read_text())['passed']
files=['relay.py','run_canary.py','container_entry.py','resume_cli.py','execution_guidance.txt','model_resource.json']
manifest={'version':'rw_web_deepseek_checkpoint_v6','fresh_context':True,'source_checkpoint':meta['source_attempt'],'old_results_preserved':True,'official_vendor_and_score_unchanged':True,'not_unconditional_baseline':True,'files':[{'path':x,'sha256':hashlib.sha256((ROOT/x).read_bytes()).hexdigest()} for x in files],'recovery_manifest_sha256':hashlib.sha256((ROOT/'private/recovery/recovery_manifest.json').read_bytes()).hexdigest()}
(ROOT/'reports/phase_manifest.json').write_text(json.dumps(manifest,indent=2))
p=subprocess.Popen([sys.executable,str(ROOT/'relay.py')],stdin=subprocess.DEVNULL,stdout=open(ROOT/'reports/relay.log','w'),stderr=subprocess.STDOUT,start_new_session=True)
for _ in range(40):
 try:
  with urllib.request.urlopen('http://127.0.0.1:8162/health',timeout=1): break
 except Exception: time.sleep(.25)
else: raise RuntimeError('Relay unavailable')
print(json.dumps({'relay_pid':p.pid,'freeze_files':len(files),'checkpoint_files':len(meta['files'])}),flush=True)
os.execv(sys.executable,[sys.executable,str(ROOT/'run_canary.py')])
