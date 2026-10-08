"""Safe provider streaming admission; never saves credentials or text payloads."""
import json
from pathlib import Path
import time
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
c=json.loads((ROOT/'model_resource.json').read_text())
key=json.loads((ROOT/c['credential_file']).read_text())['api_key']
start=time.time(); record={'purpose':'transport_admission_not_task','stream_requested':True}
try:
    q=urllib.request.Request(c['upstream_base_url']+'/chat/completions',data=json.dumps({'model':c['model_id'],'stream':True,'max_tokens':512,'messages':[{'role':'user','content':'Reply OK only.'}]}).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+key})
    with urllib.request.urlopen(q,timeout=1800) as r:
        mime=r.headers.get('Content-Type'); raw=r.read()
    frames=[]; done=False
    for line in raw.splitlines():
        if line.startswith(b'data:'):
            payload=line[5:].strip()
            if payload==b'[DONE]': done=True
            elif payload: frames.append(json.loads(payload))
    record.update(content_type=mime,bytes=len(raw),sse_frames=len(frames),done=done,models=sorted({x.get('model','') for x in frames}),finish_reasons=[v.get('finish_reason') for x in frames for v in x.get('choices',[]) if v.get('finish_reason')],frame_key_sets=[sorted(x.keys()) for x in frames[:2]],elapsed_s=round(time.time()-start,3))
except Exception as e:
    record.update(error_class=type(e).__name__,http_status=getattr(e,'code',None),elapsed_s=round(time.time()-start,3))
(ROOT/'reports/upstream_stream_admission.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record))
