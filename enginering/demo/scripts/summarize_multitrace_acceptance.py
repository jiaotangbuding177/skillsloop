"""Offline resource accounting; never makes a model request."""
import json
import sqlite3
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'artifacts'
summary={}
for name in ['031-multitrace-live','031-multitrace-live-network']:
    directory=root/name
    with sqlite3.connect(directory/'loop.sqlite') as db:
        rows=db.execute('SELECT id,purpose,status,result FROM runs ORDER BY started').fetchall()
    runs=[]
    for rid,purpose,status,result in rows:
        data=json.loads(result or '{}')
        log=directory/'workspaces'/(rid+'-control')/'stderr.log'
        content=log.read_text(encoding='utf-8') if log.exists() else ''
        runs.append({'id':rid,'purpose':purpose,'status':status,'requestStarts':content.count('[model-fetch] start') if '[model-fetch]' in content else None,
                     'usage':data.get('usage'),'costUsd':data.get('costUsd')})
    summary[name]={'runs':runs,'outerDispatches':len(runs),'requestStarts':sum(r['requestStarts'] or 0 for r in runs),
                   'requestCountsMissing':sum(r['requestStarts'] is None for r in runs),
                   'reportedTokens':sum((r['usage'] or {}).get('total',0) for r in runs) if any(r['usage'] is not None for r in runs) else None,
                   'usageMissing':sum(r['usage'] is None for r in runs),'cashCost':'UNKNOWN'}
out=root/'031-multitrace-live-network/resource-audit.json'
out.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:{a:b for a,b in v.items() if a!='runs'} for k,v in summary.items()},ensure_ascii=False,indent=2))
