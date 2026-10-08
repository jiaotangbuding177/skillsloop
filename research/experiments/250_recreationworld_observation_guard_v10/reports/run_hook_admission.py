import json,subprocess,sys,time,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parents[1]
try: urllib.request.urlopen('http://127.0.0.1:8166/health',timeout=1).close()
except Exception:
 p=subprocess.Popen([sys.executable,str(root/'relay.py')],stdin=subprocess.DEVNULL,stdout=open(root/'reports/relay.log','w'),stderr=subprocess.STDOUT,start_new_session=True)
 for _ in range(40):
  try: urllib.request.urlopen('http://127.0.0.1:8166/health',timeout=1).close(); break
  except Exception: time.sleep(.25)
 else: raise RuntimeError('relay unavailable')
cmd=['docker','run','--rm','--name','rw250-hook-admission','--network','host']
for src,dest in [(root/'managed-settings.json','/opt/rw218/managed-settings.json'),(root/'observation_guard.py','/opt/rw218/observation_guard.py'),(root/'reports/native_hook_admission_entry.py','/opt/rw218/admission.py')]:
 cmd+=['--mount',f'type=bind,src={src},dst={dest},readonly']
cmd+=['--mount',f'type=bind,src={root}/reports,dst=/results','skillloop-rw-web:218-v2','python3','/opt/rw218/admission.py']
raise SystemExit(subprocess.call(cmd))
