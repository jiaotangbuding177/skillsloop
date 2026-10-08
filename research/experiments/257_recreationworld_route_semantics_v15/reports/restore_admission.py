import json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
cmd=['docker','run','--rm','--user','1002:1002','--network','none','--mount',f'type=bind,src={root}/execution_guidance.txt,dst=/results/skill_context.md,readonly','--mount',f'type=bind,src={root}/private/recovery,dst=/recovery,readonly','--mount',f'type=bind,src={root}/resume_cli.py,dst=/admission/resume_cli.py,readonly','--mount',f'type=bind,src={root}/reports/restore_fixture.py,dst=/admission/restore_fixture.py,readonly','skillloop-rw-web:218-v2','python3','/admission/restore_fixture.py']
r=subprocess.run(cmd,capture_output=True,text=True); assert r.returncode==0,r.stderr
value=json.loads(r.stdout); (root/'reports/restore_admission.json').write_text(json.dumps(value,indent=2)); print(json.dumps(value))
