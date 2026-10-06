"""One delayed readiness snapshot; no startup, change, model or container."""
import json,subprocess
from pathlib import Path
from audited_runtime import HERE,dump

target=HERE/'docker_post_backoff_snapshot.json'
if target.exists(): raise RuntimeError('Do not overwrite readiness evidence')
command=['C:/Program Files/Docker/Docker/resources/bin/docker.exe','info','--format','{{.ServerVersion}}']
try:
    result=subprocess.run(command,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10)
    ready=result.returncode==0 and bool(result.stdout.strip())
    evidence={'status':'DAEMON_READY' if ready else 'DAEMON_NOT_READY','exit_code':result.returncode,
              'server_version':result.stdout.strip(),'stderr':result.stderr,'timeout':False}
except subprocess.TimeoutExpired:
    evidence={'status':'DAEMON_NOT_READY','timeout':True,'timeout_seconds':10}
evidence.update(model_calls=0,containers_or_images_started=0,docker_restarted=False,settings_modified=False)
dump(target,evidence)
print(json.dumps(evidence,ensure_ascii=False))
