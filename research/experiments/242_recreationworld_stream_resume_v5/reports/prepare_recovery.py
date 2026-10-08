"""Preserve failed snapshot; prepare exact native session/source recovery."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
ROOT=Path(__file__).resolve().parents[1]
old=ROOT.parent/'241_recreationworld_infra_resume_v4'
s=json.loads((old/'reports/pipeline_status.json').read_text())
if s['state']!='transport_failure': raise RuntimeError('Only infrastructure failure eligible')
label=s['attempt']; native=json.loads((old/'runs'/label/'metrics.json').read_text())
if native['outcome_class']!='infra_error': raise RuntimeError('Not an infrastructure retry')
name='rw238-'+label
running=subprocess.check_output(['docker','inspect','--format','{{.State.Running}}',name],text=True).strip()
if running!='false': raise RuntimeError('Old container still active')
rec=ROOT/'private/recovery'; ws=rec/'workspace'; ws.mkdir(parents=True,exist_ok=True)
source=old/'runs'/label/'recreation'
items=[x for x in ['src','public','package.json','package-lock.json','index.html','vite.config.ts','tsconfig.json','tsconfig.app.json','tsconfig.node.json','components.json'] if (source/x).exists()]
for x in items:
    if (source/x).is_dir(): shutil.copytree(source/x,ws/x,dirs_exist_ok=True)
    else: shutil.copy2(source/x,ws/x)
subprocess.run(['docker','cp',name+':/home/agent/.claude/projects',str(rec/'projects')],check=True)
sessions=list((source/'sessions').glob('recreation_agent_main_*.jsonl'))
if len(sessions)!=1: raise RuntimeError('Ambiguous native session')
session=sessions[0].stem.removeprefix('recreation_agent_main_')
files=[{'path':str(p.relative_to(rec)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in rec.rglob('*') if p.is_file()]
(rec/'recovery_manifest.json').write_text(json.dumps({'source_attempt':label,'source_version':s['version'],'reason':'recorded HTTP524 / infra_error','session_id':session,'workspace_items':items,'files':files},indent=2))
c=json.loads((ROOT/'model_resource.json').read_text()); c.update(version='rw_web_deepseek_stream_resume_v5',local_port=8161,transport_infrastructure='self',recovery=True,upstream_stream=True)
(ROOT/'model_resource.json').write_text(json.dumps(c,indent=2))
for p in rec.rglob('*'):
    p.chmod(0o755 if p.is_dir() else 0o644)
print(json.dumps({'old_stopped':True,'session_id':session,'workspace_items':items,'snapshot_files':len(files),'credentials_copied':False}))
