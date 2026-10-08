import subprocess,json
text=subprocess.check_output(['dmesg','--ctime'],text=True);lines=[l for l in text.splitlines() if 'oom-kill:' in l or 'Memory cgroup out of memory:' in l or 'Out of memory:' in l]
containers=json.loads(subprocess.check_output(['docker','inspect','rw288-minipaint_recreation_eval_1791126784363902808','rw288-squoosh_eval_1791128197331372710','rw288-squoosh_eval_1791128738283803882'],text=True))
print(json.dumps({'containers':[{ 'id':x['Id'],'name':x['Name'],'state':x['State']} for x in containers],'last_oom_events':lines[-18:]}))
