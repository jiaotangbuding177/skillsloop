import json,os,tarfile,subprocess,time,shutil
from pathlib import Path
out=Path('/publish');root=Path('/native-build');root.mkdir()
with tarfile.open('/source.tar') as tf:tf.extractall(root)
env=dict(os.environ,NODE_OPTIONS='--max-old-space-size=768',HUSKY='0',CI='true',npm_config_cache='/cache')
record={'started_epoch':time.time(),'network':'none','source_commit':'e8d35e0fb66eb16eff6fe8fc773eabcbb7128de3','model_called':False,'dependency_install':'npm ci --offline from original retained builder cache'}
with (out/'native_build_v3.log').open('w') as log:
 rc=subprocess.call(['npm','ci','--offline','--no-audit','--no-fund'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
 record['install_returncode']=rc
 if rc==0:rc=subprocess.call(['npm','run','build'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
record.update(returncode=rc,ended_epoch=time.time(),index_exists=(root/'build/index.html').is_file())
if rc==0 and record['index_exists']:
 assert not (out/'site').exists();shutil.copytree(root/'build',out/'site');record['published_files']=sum(p.is_file() for p in (out/'site').rglob('*'))
(out/'native_build_v3_status.json').write_text(json.dumps(record,indent=2));print(json.dumps(record));raise SystemExit(rc)
