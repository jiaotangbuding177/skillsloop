import json
import subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=json.loads((root/'reports/pipeline_status.json').read_text())
code=r"""from pathlib import Path
p=Path('/workspace/recreation/src')
print('\n'.join(str(x.relative_to(p)) for x in p.rglob('*.tsx')))
print((p/'App.tsx').read_text())
"""
r=subprocess.run(['docker','exec','rw238-'+s['attempt'],'python3','-c',code],capture_output=True,text=True)
print(r.stdout[:6000])
print(r.stderr[:500])
