import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; old=ROOT.parent/'243_recreationworld_checkpoint_v6'
s=json.loads((old/'reports/pipeline_status.json').read_text()); name='rw238-'+s['attempt']
assert subprocess.check_output(['docker','inspect','--format','{{.State.Running}}',name],text=True).strip()=='false'
rec=ROOT/'private/recovery'; ws=rec/'workspace'; ws.mkdir(parents=True)
# Preserve actual latest agent source even though interrupted native export may be absent.
subprocess.run(['docker','cp',name+':/workspace/recreation/.',str(rec/'retained_failed_workspace')],check=True)
source=rec/'retained_failed_workspace'
items=[x for x in ['src','public','package.json','package-lock.json','index.html','vite.config.ts','tsconfig.json'] if (source/x).exists()]
for x in items:
 if (source/x).is_dir(): shutil.copytree(source/x,ws/x)
 else: shutil.copy2(source/x,ws/x)
files=[{'path':str(p.relative_to(rec)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in ws.rglob('*') if p.is_file()]
(rec/'recovery_manifest.json').write_text(json.dumps({'source_attempt':s['attempt'],'source_version':s['version'],'reason':'verified official adapter image serialization bug; source preserved','workspace_items':items,'files':files},indent=2))
for p in ws.rglob('*'): p.chmod(0o755 if p.is_dir() else 0o644)
print(json.dumps({'old_stopped':True,'source_files':len(files),'workspace_items':items}))
