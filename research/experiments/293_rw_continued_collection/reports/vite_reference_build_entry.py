"""Build the fixed Vite docs reference in an isolated container, no model calls."""
import json,subprocess,time
from pathlib import Path
status={'started_epoch':time.time(),'model_calls':0,'reference_only':True}
commands=[['corepack','prepare','pnpm@10.33.0','--activate'],
          ['pnpm','install','--frozen-lockfile'],['pnpm','build'],['pnpm','docs-build']]
for command in commands:
 p=subprocess.run(command)
 if p.returncode:
  status.update(state='reference_build_failed',command=command,returncode=p.returncode,ended_epoch=time.time())
  Path('/build-reports/container_build_status.json').write_text(json.dumps(status,indent=2));raise SystemExit(p.returncode)
status.update(state='build_completed_pending_gui_admission',ended_epoch=time.time(),model_calls=0)
Path('/build-reports/container_build_status.json').write_text(json.dumps(status,indent=2))
