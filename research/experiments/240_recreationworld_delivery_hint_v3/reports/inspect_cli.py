import json
import subprocess
from pathlib import Path
root = Path(__file__).resolve().parents[1]
s = json.loads((root / 'reports/pipeline_status.json').read_text())
code = """from pathlib import Path
p=Path('/usr/local/bin/claude').resolve()
b=p.read_bytes()
i=b.find(b'[Tool use interrupted]')
print(p, len(b), i)
if i>=0: print(b[max(0,i-180):i+240].decode('utf8','replace'))
"""
r = subprocess.run(['docker', 'exec', 'rw238-'+s['attempt'], 'python3', '-c', code], capture_output=True, text=True)
print(r.stdout)
print(r.stderr[:300])
