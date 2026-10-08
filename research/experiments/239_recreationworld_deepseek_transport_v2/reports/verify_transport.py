import hashlib
import http.client
import importlib.util
import io
import json
from pathlib import Path
import threading
import urllib.request
import urllib.error

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('relay',ROOT/'relay.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
bad=[{'choices':[]},{'choices':[{'finish_reason':None,'message':{}}]},
    {'choices':[{'finish_reason':'length','message':{}}]},{'error':{'message':'failed'}}]
rejected=0
for item in bad:
    try: module.complete(item)
    except ValueError: rejected+=1
assert rejected==4
original=urllib.request.urlopen
counter=0
def temporary_failure(request,**kwargs):
    global counter
    counter+=1
    if counter<3: raise urllib.error.URLError('synthetic connection failure')
    return io.BytesIO(json.dumps({'choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':'OK'}}]}).encode())
server=module.ThreadingHTTPServer(('127.0.0.1',0),module.Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
try:
    urllib.request.urlopen=temporary_failure
    connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=20)
    connection.request('POST','/239_transport_test/synthetic/chat/completions',json.dumps({'messages':[]}),{'Content-Type':'application/json'})
    response=connection.getresponse(); body=json.loads(response.read())
    assert response.status==200 and counter==3 and body['choices'][0]['message']['content']=='OK'
finally:
    urllib.request.urlopen=original; server.shutdown(); server.server_close()
request=urllib.request.Request('http://127.0.0.1:8159/239_recreationworld/admission/v1/chat/completions',
    data=json.dumps({'stream':True,'messages':[{'role':'user','content':'Reply OK only.'}],'max_tokens':512}).encode(),
    headers={'Content-Type':'application/json'})
with urllib.request.urlopen(request,timeout=1800) as response: data=response.read()
assert b'data: [DONE]' in data
manifest={'version':'rw_web_deepseek_transport_v2','old_versions_preserved':True,'credential_excluded':True,
    'local_bind':'127.0.0.1:8159','transport_retries':3,'tests':{'reject_incomplete_cases':rejected,
    'two_transient_failures_then_success':counter==3,'real_sse_passed':True},'files':[
    {'path':name,'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest()}
    for name in ('model_resource.json','relay.py','container_entry.py','run_canary.py','probe.py')]}
(ROOT/'reports/phase_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest['tests']))
