import hashlib,io,json,os,runpy,sys
from pathlib import Path
target=Path('/tmp/candidate'); target.mkdir(); os.chdir(target)
sys.argv=['resume_cli.py','-p']; sys.stdin=io.TextIOWrapper(io.BytesIO(b'Public task fixture'))
calls=[]; original_exec=os.execv; os.execv=lambda path,args:calls.append((path,args))
runpy.run_path('/admission/resume_cli.py',run_name='__main__'); os.execv=original_exec
meta=json.loads(Path('/recovery/recovery_manifest.json').read_text())
for name,sha in meta['files'].items(): assert hashlib.sha256((target/name).read_bytes()).hexdigest()==sha
assert not any((target/name).exists() for name in ['task.json','recreation_manifest.json','evaluation','trajectory.jsonl','.claude'])
assert calls and calls[0][0]=='/usr/local/bin/claude-original'
print(json.dumps({'passed':True,'uid':os.getuid(),'verified_source_files':len(meta['files']),'model_called':False,'evaluation_or_sessions_restored':False}))
