import hashlib,json,os,socket,subprocess,sys,time,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]; old=root.parent/'250_recreationworld_observation_guard_v10'
assert not (root/'private/STOP').exists()
status=json.loads((old/'reports/pipeline_status.json').read_text()); assert status['state']=='native_finished'
assert subprocess.check_output(['docker','inspect','--format','{{.State.Running}}','rw238-'+status['attempt']],text=True).strip()=='false'
assert json.loads((root/'reports/restore_admission.json').read_text())['passed']
manifest=json.loads((root/'reports/phase_manifest.json').read_text())
for f in manifest['files']: assert hashlib.sha256((root/f['path']).read_bytes()).hexdigest()==f['sha256']
for name,sha in manifest['source_checkpoint_hashes'].items(): assert hashlib.sha256((root/'private/recovery/workspace'/name).read_bytes()).hexdigest()==sha
for port in [8167,8797]:
 with socket.socket() as s: assert s.connect_ex(('127.0.0.1',port))!=0,'Port occupied'
relay=subprocess.Popen([sys.executable,str(root/'relay.py')],stdin=subprocess.DEVNULL,stdout=(root/'reports/relay_stdout.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
ticks=Path(f'/proc/{relay.pid}/stat').read_text().rsplit(')',1)[1].split()[19]
(root/'reports/relay_identity.json').write_text(json.dumps({'pid':relay.pid,'start_ticks':ticks,'loopback_port':8167},indent=2))
for _ in range(40):
 try:
  with urllib.request.urlopen('http://127.0.0.1:8167/health',timeout=1): break
 except Exception: time.sleep(.25)
else: raise RuntimeError('Relay unavailable')
print(json.dumps({'freeze_files':len(manifest['files']),'source_files':len(manifest['source_checkpoint_hashes']),'relay_pid':relay.pid,'old_controller_finished':True}),flush=True)
os.execv(sys.executable,[sys.executable,str(root/'run_canary.py')])
