import hashlib,json,os,shutil,sys,tempfile
from pathlib import Path
args=sys.argv[1:]
if '-p' in args:
 snapshot=Path('/recovery'); meta=json.loads((snapshot/'recovery_manifest.json').read_text())
 for name,sha in meta['files'].items():
  assert hashlib.sha256((snapshot/'workspace'/name).read_bytes()).hexdigest()==sha,name
 for item in meta['workspace_items']:
  source=snapshot/'workspace'/item; dest=Path.cwd()/item
  if source.is_dir(): shutil.copytree(source,dest,dirs_exist_ok=True)
  else: shutil.copy2(source,dest)
 original=sys.stdin.buffer.read(); guidance=Path('/results/skill_context.md').read_bytes()
 stream=tempfile.TemporaryFile(); stream.write(original+b"\n\n"+guidance); stream.seek(0); os.dup2(stream.fileno(),0)
os.execv('/usr/local/bin/claude-original',['claude',*args])
