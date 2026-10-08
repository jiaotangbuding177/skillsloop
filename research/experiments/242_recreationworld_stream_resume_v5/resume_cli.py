"""One explicit deployment recovery after recorded HTTP524; native CLI untouched."""
import json
import os
from pathlib import Path
import shutil
import sys
args=sys.argv[1:]
if '-p' in args:
    snapshot=Path('/recovery')
    meta=json.loads((snapshot/'recovery_manifest.json').read_text())
    workspace=Path.cwd()
    for item in meta['workspace_items']:
        source=snapshot/'workspace'/item
        dest=workspace/item
        if source.is_dir(): shutil.copytree(source,dest,dirs_exist_ok=True)
        else: shutil.copy2(source,dest)
    projects=Path.home()/'.claude/projects'
    shutil.copytree(snapshot/'projects',projects,dirs_exist_ok=True)
    if '--name' in args:
        index=args.index('--name'); del args[index:index+2]
    args=['--resume',meta['session_id'],*args]
os.execv('/usr/local/bin/claude-original',['claude',*args])
