import os,sys,tempfile
from pathlib import Path
args=sys.argv[1:]
if '-p' in args:
 original=sys.stdin.buffer.read(); guidance=Path('/results/skill_context.md').read_bytes()
 stream=tempfile.TemporaryFile(); stream.write(original+b"\n\n"+guidance); stream.seek(0); os.dup2(stream.fileno(),0)
os.execv('/usr/local/bin/claude-original',['claude',*args])
