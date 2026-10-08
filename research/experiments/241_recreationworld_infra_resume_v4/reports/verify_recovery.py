import hashlib
import http.client
import importlib.util
import io
import json
from pathlib import Path
import py_compile
import threading
import urllib.error
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('relay',ROOT/'relay.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
original=urllib.request.urlopen; counter=0
def temporary_failure(request,**kwargs):
    global counter
    counter+=1
    if counter==1: raise urllib.error.HTTPError('synthetic',524,'synthetic timeout',{},None)
    if counter==2: raise urllib.error.URLError('synthetic disconnect')
    return io.BytesIO(json.dumps({'choices':[{'index':0,'finish_reason':'stop','message':{'role':'assistant','content':'OK'}}]}).encode())
server=m.ThreadingHTTPServer(('127.0.0.1',0),m.Handler)
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    urllib.request.urlopen=temporary_failure
    conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=20)
    conn.request('POST','/synthetic_recovery_test/chat/completions',json.dumps({'messages':[]}),{'Content-Type':'application/json'})
    response=conn.getresponse(); body=json.loads(response.read())
    assert response.status==200 and counter==3 and body['choices'][0]['message']['content']=='OK'
finally:
    urllib.request.urlopen=original; server.shutdown(); server.server_close()
request=urllib.request.Request('http://127.0.0.1:8160/admission/chat/completions',data=json.dumps({'stream':True,'messages':[{'role':'user','content':'Reply OK only.'}],'max_tokens':512}).encode(),headers={'Content-Type':'application/json'})
with urllib.request.urlopen(request,timeout=1800) as r: data=r.read()
assert b'data: [DONE]' in data
rec=ROOT/'private/recovery'; recovery=json.loads((rec/'recovery_manifest.json').read_text())
assert all(hashlib.sha256((rec/x['path']).read_bytes()).hexdigest()==x['sha256'] for x in recovery['files'])
files=['relay.py','model_resource.json','run_canary.py','container_entry.py','resume_cli.py','execution_guidance.txt']
for x in files:
    if x.endswith('.py'): py_compile.compile(str(ROOT/x),doraise=True)
manifest={'version':'rw_web_deepseek_infra_resume_v4','official_vendor_unchanged':True,'deployment_resume_after_infra_only':True,'source_attempt':recovery['source_attempt'],'recovery_manifest_sha256':hashlib.sha256((rec/'recovery_manifest.json').read_bytes()).hexdigest(),'snapshot_files':len(recovery['files']),'local_bind':'127.0.0.1:8160','proxy_port':8790,'tests':{'HTTP524_and_disconnect_then_success':counter==3,'real_sse_passed':True,'snapshot_sha_passed':True,'syntax_passed':True},'files':[{'path':x,'sha256':hashlib.sha256((ROOT/x).read_bytes()).hexdigest()} for x in files]}
(ROOT/'reports/phase_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest['tests']))
