import hashlib
import importlib.util
import io
import json
from pathlib import Path
import py_compile
import urllib.request
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('relay',ROOT/'relay.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
class Response(io.BytesIO):
    headers={'Content-Type':'text/event-stream'}
def frames(values,done=True):
    data=''.join('data: '+json.dumps(x)+'\n\n' for x in values)
    if done: data+='data: [DONE]\n\n'
    return Response(data.encode())
def chunk(delta,finish=None):
    return {'id':'test','model':'fixture','choices':[{'index':0,'delta':delta,'finish_reason':finish}]}
text=m.receive(frames([chunk({'content':'O'}),chunk({'content':'K'},'stop')]),{},'synthetic_text')
assert text['choices'][0]['message']['content']=='OK'
parts=[chunk({'tool_calls':[{'index':0,'id':'t1','type':'function','function':{'name':'report_status','arguments':'{"status":'}}]}),chunk({'tool_calls':[{'index':0,'function':{'arguments':'"ready"}'}}]},'tool_calls')]
tool=m.receive(frames(parts),{},'synthetic_tool')['choices'][0]['message']['tool_calls'][0]
assert tool['function']['name']=='report_status' and json.loads(tool['function']['arguments'])=={'status':'ready'}
rejected=0
for stream in [frames([chunk({'content':'partial'},'stop')],False),frames([chunk({'content':'partial'})]),frames([chunk({'content':'partial'},'length')])]:
    try: m.receive(stream,{},'synthetic_bad')
    except ValueError: rejected+=1
assert rejected==3
payload={'model':m.CFG['model_id'],'stream':True,'max_tokens':512,'messages':[{'role':'user','content':'Call report_status with status ready.'}],'tools':[{'type':'function','function':{'name':'report_status','description':'Report status','parameters':{'type':'object','properties':{'status':{'type':'string'}},'required':['status']}}}],'tool_choice':{'type':'function','function':{'name':'report_status'}}}
q=urllib.request.Request(m.CFG['upstream_base_url']+'/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+m.KEY})
record={'purpose':'stream_tool_admission_not_task'}
with urllib.request.urlopen(q,timeout=1800) as response: result=m.receive(response,record,'real_tool_admission')
calls=result['choices'][0]['message'].get('tool_calls',[])
assert calls and calls[0]['function']['name']=='report_status' and json.loads(calls[0]['function']['arguments'])['status']=='ready'
record.update(model_reported=result.get('model'),finish_reasons=[c['finish_reason'] for c in result['choices']],usage=result.get('usage'),tool_name='report_status',tool_arguments_valid=True)
(ROOT/'reports/stream_tool_admission.json').write_text(json.dumps(record,indent=2))
files=['relay.py','model_resource.json','run_canary.py','container_entry.py','resume_cli.py','execution_guidance.txt']
for x in files:
    if x.endswith('.py'): py_compile.compile(str(ROOT/x),doraise=True)
manifest={'version':'rw_web_deepseek_checkpoint_v6','official_vendor_unchanged':True,'upstream_stream':True,'downstream_released_only_after_DONE_and_finish':True,'local_bind':'127.0.0.1:8162','proxy_port':8792,'tests':{'fragmented_text':True,'fragmented_tool_arguments':True,'reject_incomplete_streams':rejected,'real_stream_tool':True},'files':[{'path':x,'sha256':hashlib.sha256((ROOT/x).read_bytes()).hexdigest()} for x in files]}
(ROOT/'reports/transport_manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(manifest['tests']))
