import json,os,tarfile,subprocess,time,shutil
from pathlib import Path

out=Path('/publish');root=Path('/native-build');root.mkdir()
with tarfile.open('/input.tar') as tf:tf.extractall(root)
# Windows tar cannot preserve Linux package-bin links. Restore the declared
# dependency entrypoints; package contents and pinned versions are unchanged.
bins=0
for package in root.joinpath('node_modules').rglob('package.json'):
 try:
  obj=json.loads(package.read_text());decl=obj.get('bin',{})
  if isinstance(decl,str):decl={obj['name'].rsplit('/',1)[-1]:decl}
  if not isinstance(decl,dict):continue
  mod=package.parent;parts=mod.parts;idx=len(parts)-1-list(reversed(parts)).index('node_modules');nm=Path(*parts[:idx+1]);bd=nm/'.bin';bd.mkdir(exist_ok=True)
  for name,target in decl.items():
   actual=mod/target
   if not actual.is_file():continue
   link=bd/name
   if link.exists() or link.is_symlink():link.unlink()
   link.symlink_to(os.path.relpath(actual,bd));actual.chmod(actual.stat().st_mode|0o111);bins+=1
 except (ValueError,KeyError,json.JSONDecodeError):continue
env=dict(os.environ,PATH=str(root/'node_modules/.bin')+':'+os.environ['PATH'],NODE_OPTIONS='--max-old-space-size=768',HUSKY='0',CI='true')
record={'started_epoch':time.time(),'network':'none','source_commit':'e8d35e0fb66eb16eff6fe8fc773eabcbb7128de3','restored_package_bins':bins,'model_called':False}
with (out/'native_build_v2.log').open('w') as log:
 rc=subprocess.call(['npm','run','build'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
record.update(returncode=rc,ended_epoch=time.time(),index_exists=(root/'build/index.html').is_file())
if rc==0 and record['index_exists']:
 assert not (out/'site').exists()
 shutil.copytree(root/'build',out/'site');record['published_files']=sum(p.is_file() for p in (out/'site').rglob('*'))
(out/'native_build_v2_status.json').write_text(json.dumps(record,indent=2));print(json.dumps(record));raise SystemExit(rc)
