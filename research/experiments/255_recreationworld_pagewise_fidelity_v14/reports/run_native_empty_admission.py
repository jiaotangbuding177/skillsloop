import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]; cmd=['docker','run','--rm','--name','rw254-empty-admission','--network','host']
for src,dest in [(root/'managed-settings.json','/opt/rw218/managed-settings.json'),(root/'observation_guard.py','/opt/rw218/observation_guard.py'),(root/'reports/native_empty_fixture.py','/opt/rw218/admission.py')]: cmd+=['--mount',f'type=bind,src={src},dst={dest},readonly']
cmd+=['--mount',f'type=bind,src={root}/reports,dst=/results','skillloop-rw-web:218-v2','python3','/opt/rw218/admission.py']
raise SystemExit(subprocess.call(cmd))
