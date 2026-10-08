"""Restore only agent-produced source; start a declared fresh native context."""
import json, os, shutil, sys, tempfile
from pathlib import Path
args=sys.argv[1:]
if '-p' in args:
 snapshot=Path('/recovery'); meta=json.loads((snapshot/'recovery_manifest.json').read_text())
 for item in meta['workspace_items']:
  source=snapshot/'workspace'/item; dest=Path.cwd()/item
  if source.is_dir(): shutil.copytree(source,dest,dirs_exist_ok=True)
  else: shutil.copy2(source,dest)
 guidance=b"Infrastructure checkpoint recovery: src/public contain your existing implementation from the interrupted run. Preserve it. Inspect the current source, run the build and concise browser checks, fix only actual issues, and deliver the required output/index.html. Do not restart reference exploration or rebuild from scratch. This is a fresh context after recorded provider failures.\n\n"
 stream=tempfile.TemporaryFile(); stream.write(guidance+sys.stdin.buffer.read()); stream.seek(0); os.dup2(stream.fileno(),0)
os.execv('/usr/local/bin/claude-original',['claude',*args])
