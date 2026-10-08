import hashlib,json,os,py_compile,socket,subprocess,sys,time,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
old=ROOT.parent/'246_recreationworld_clean_delivery_v9'; status=json.loads((old/'reports/pipeline_status.json').read_text()); name='rw238-'+status['attempt']
assert subprocess.check_output(['docker','inspect','--format','{{.State.Running}}',name],text=True).strip()=='false'
for port in [8796]:
 with socket.socket() as s:
  if s.connect_ex(('127.0.0.1',port))==0: raise RuntimeError('Port occupied')
identity=json.loads((ROOT/'reports/relay_identity.json').read_text())
assert str(ROOT/'relay.py') in Path('/proc/'+str(identity['pid'])+'/cmdline').read_text()
assert json.loads((ROOT/'reports/native_hook_admission.json').read_text())['passed']
assert json.loads((ROOT/'reports/guard_fixture_admission.json').read_text())['passed']
files=['relay.py','vision_bridge.py','run_canary.py','container_entry.py','resume_cli.py','execution_guidance.txt','model_resource.json','observation_guard.py','asset_fetch.py','managed-settings.json']
for f in files:
 if f.endswith('.py'): py_compile.compile(str(ROOT/f),doraise=True)
assert json.loads((ROOT/'reports/full_image_path_admission.json').read_text())['passed']
manifest={'version':'rw_web_deepseek_observation_guard_v10','fresh_clean_scaffold':True,'restored_prior_source':False,'restored_prior_session':False,'additional_guidance':True,'declared_tool_policy_change':'native managed PreToolUse observation restriction and Stop artifact freshness/summary gate; binary-only helper','official_vendor_and_score_unchanged':True,'canary_excluded':True,'prior_agent_failure':'v9 reference HTML nav-group harvesting, official score_passed false; retained negative','files':[{'path':x,'sha256':hashlib.sha256((ROOT/x).read_bytes()).hexdigest()} for x in files]}
(ROOT/'reports/phase_manifest.json').write_text(json.dumps(manifest,indent=2))
for _ in range(40):
 try:
  with urllib.request.urlopen('http://127.0.0.1:8166/health',timeout=1): break
 except Exception: time.sleep(.25)
else: raise RuntimeError('Relay unavailable')
print(json.dumps({'relay_pid':identity['pid'],'freeze_files':len(files),'old_agent_stopped':True,'clean_scaffold':True,'native_hook_admission_passed':True}),flush=True)
os.execv(sys.executable,[sys.executable,str(ROOT/'run_canary.py')])
