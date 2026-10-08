import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; rec=ROOT/'private/recovery'
m=json.loads((rec/'recovery_manifest.json').read_text()); assert all(hashlib.sha256((rec/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in m['files'])
for p in (rec/'workspace').rglob('*'): p.chmod(0o755 if p.is_dir() else 0o644)
print(json.dumps({'checkpoint_sha_verified':len(m['files'])}))
