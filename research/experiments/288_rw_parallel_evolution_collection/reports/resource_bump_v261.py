from pathlib import Path
import subprocess,json,time,hashlib
root=Path(__file__).resolve().parents[1]
name='rw288-squoosh_recreation_eval_1791129536850164583'
j=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
assert j['Id']=='eac7784b1f4fd2acb35b3705e204b0f86f84c2a66ee264c496a09ae376802ed4' and j['State']['Running'] and j['State']['OOMKilled']
assert 'claude -p --model' in subprocess.check_output(['docker','top',name,'-eo','pid,args'],text=True)
assert Path('/proc/127286/stat').read_text().split()[21]
mem={k:int(v.split()[0]) for k,v in (x.split(':',1) for x in Path('/proc/meminfo').read_text().splitlines()) if v.strip().split()[0].isdigit()}
assert mem['MemAvailable']>3*1024*1024
p=root/'reports/external_resource_v261_manifest.json';assert not p.exists()
r={'version':'rw_external_resource_repair_v2.6.1','attempt':'squoosh_recreation_eval_1791129536850164583','container_id':j['Id'],'before_state':j['State'],'before_limits':{k:j['HostConfig'][k] for k in ['Memory','MemorySwap','NanoCpus']},'reason':'Exact container MEMCG OOM killed browser child; original native actor PID127286 remains alive. Increase external cap, preserve OOM evidence. Failed v26 assertion performed no update.','model_round':1,'new_round':False,'actor_restart':False,'frozen_files_modified':False,'external_execution_resource_changed':True,'mem_available_kib':mem['MemAvailable'],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'epoch':time.time(),'state':'prepared'}
p.write_text(json.dumps(r,indent=2))
subprocess.run(['docker','update','--memory','3g','--memory-swap','3g',name],check=True,capture_output=True)
q=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
assert q['HostConfig']['Memory']==3221225472
r.update(state='applied',after_limits={k:q['HostConfig'][k] for k in ['Memory','MemorySwap','NanoCpus']},applied_epoch=time.time())
p.write_text(json.dumps(r,indent=2));print(json.dumps({'state':r['state'],'memory_mib':3072,'original_actor_retained':True}))
