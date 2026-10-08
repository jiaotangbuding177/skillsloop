import json,urllib.request,urllib.error
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; cfg=json.loads((ROOT/'model_resource.json').read_text()); key=json.loads((ROOT/cfg['credential_file']).read_text())['api_key']
q=urllib.request.Request(cfg['upstream_base_url']+'/messages',data=json.dumps({'model':cfg['model_id'],'max_tokens':128,'messages':[{'role':'user','content':'Return exactly OK.'}]}).encode(),headers={'Content-Type':'application/json','x-api-key':key,'anthropic-version':'2023-06-01'})
r={'purpose':'native_endpoint_admission_not_task'}
try:
 with urllib.request.urlopen(q,timeout=1800) as response:
  body=json.load(response); r.update(http_status=response.status,keys=sorted(body),model_reported=body.get('model'),stop_reason=body.get('stop_reason'))
  if isinstance(body.get('content'),list):
   answer=''.join(x.get('text','') for x in body['content'] if x.get('type')=='text'); r.update(answer=answer[:80],passed=answer.strip()=='OK')
  else: r['passed']=False
except urllib.error.HTTPError as e: r.update(http_status=e.code,error_class=type(e).__name__,passed=False)
except Exception as e: r.update(error_class=type(e).__name__,passed=False)
(ROOT/'reports/native_endpoint_admission.json').write_text(json.dumps(r,indent=2)); print(json.dumps(r))
