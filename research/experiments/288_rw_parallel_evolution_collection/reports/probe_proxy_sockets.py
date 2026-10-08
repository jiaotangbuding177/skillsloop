import subprocess,json
name='rw288-minipaint_recreation_eval_1791129685783416430'
j=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0];top=subprocess.check_output(['docker','top',name,'-eo','pid,args'],text=True);pids=set(line.split()[0] for line in top.splitlines()[1:] if line.strip())
ss=subprocess.check_output(['ss','-tnp'],text=True);lines=[l for l in ss.splitlines() if ':8788' in l and any('pid='+p+',' in l for p in pids)]
print(json.dumps({'container_id':j['Id'],'container_pid':j['State']['Pid'],'processes':[l for l in top.splitlines() if 'python' in l or 'claude' in l],'model_proxy_sockets':lines}))
