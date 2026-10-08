import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=json.loads((ROOT/'reports/pipeline_status.json').read_text()); run=ROOT/'runs'/s['attempt']
log=run/'controller.log'
lines=log.read_text(errors='replace').splitlines() if log.exists() else []
markers=[x for x in lines if any(v in x.lower() for v in ['stage','passed','failed','scoring','evaluation','test ','infra_error','submission','finished'])]
print(json.dumps({'state':s['state'],'log_last_markers':markers[-8:],'metrics_exists':(run/'metrics.json').exists()},ensure_ascii=False))
