import importlib.util,json,sys,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'reports'))
from proxy_source_audit.translator import anthropic_message_to_openai_messages
from vision_bridge import repair_messages,split_images
spec=importlib.util.spec_from_file_location('relay',ROOT/'relay.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
fixture=json.loads((ROOT/'reports/vision_fixture.json').read_text()); image=fixture['image']; expected=fixture['expected']
tool=anthropic_message_to_openai_messages({'role':'user','content':[{'type':'tool_result','tool_use_id':'read_fixture','content':[{'type':'text','text':'Image loaded.'},image]}]})
messages=[{'role':'user','content':'Read the six-character code from the image returned by read_image. Return only the code.'},{'role':'assistant','content':'','tool_calls':[{'id':'read_fixture','type':'function','function':{'name':'read_image','arguments':'{}'}}]},*tool]
fixed,audit=repair_messages(messages); assert audit['recovered_image_blocks']==1 and fixed[2]['role']=='tool' and fixed[3]['role']=='user'
assert fixed[3]['content'][1]['image_url']['url'].endswith(image['source']['data'])
assert repair_messages([{'role':'user','content':'Ordinary text'}])[0]==[{'role':'user','content':'Ordinary text'}]
invalid='{"type":"image","source":{"type":"base64","media_type":"image/png","data":"!bad"}}'; assert split_images(invalid)[1]==0
payload={'model':m.CFG['model_id'],'stream':True,'max_tokens':512,'temperature':0,'messages':fixed,'tools':[{'type':'function','function':{'name':'read_image','parameters':{'type':'object','properties':{}}}}]}
q=urllib.request.Request(m.CFG['upstream_base_url']+'/chat/completions',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+m.KEY})
record={'purpose':'official_proxy_image_conversion_admission_not_task','image_transport':audit}
with urllib.request.urlopen(q,timeout=1800) as response: result=m.receive(response,record,'full_image_path_admission')
answer=result['choices'][0]['message']['content'].strip(); record.update(expected=expected,answer=answer[:100],passed=answer==expected,model_reported=result.get('model'),finish_reason=result['choices'][0]['finish_reason'])
(ROOT/'reports/full_image_path_admission.json').write_text(json.dumps(record,indent=2)); print(json.dumps(record))
assert record['passed']
