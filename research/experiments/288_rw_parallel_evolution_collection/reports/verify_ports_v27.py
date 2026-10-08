import json,os,socket,subprocess,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
prefix=(root/'scripts_v27/container_entry.py').read_text().split("Path('/var/lib/mockweb-scorer')",1)[0]
test=prefix+"\nprint(json.dumps({'proxy_port':env['PORT'],'actor_base_url':env['RB_AGENT_BASE_URL']}))"
args=['--model-base-url','http://127.0.0.1:8193/fixture/v1','--model','deepseek-v4-flash-vision-exp','--stage','recreation_eval']
results=[]
for port in (8792,8793):
    env=os.environ.copy();env['RW_MODEL_PROXY_PORT']=str(port)
    r=subprocess.run(['python3','-c',test,*args],env=env,capture_output=True,text=True);assert r.returncode==0,r.stderr
    value=json.loads(r.stdout);assert value['proxy_port']==str(port) and value['actor_base_url'].endswith(':'+str(port))
    with socket.socket() as occupied:
        occupied.bind(('127.0.0.1',port));occupied.listen()
        r=subprocess.run(['python3','-c',test,*args],env=env,capture_output=True,text=True);assert r.returncode!=0 and 'Address already in use' in r.stderr
    results.append({'port':port,'actor_matches_own_proxy':True,'occupied_listener_rejected_before_proxy_or_model':True})
r={'epoch':time.time(),'version':'v2.7','cases':results,'model_calls':0,'current_actor_untouched':True,'scope':'Real OS binding collision negative test; not a full future application admission'}
(root/'reports/port_isolation_verification_v27.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
