import importlib.util,json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(root))
spec=importlib.util.spec_from_file_location('checked_relay',root/'relay.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
cases=[]
for finish,content,reasoning,expected in [('stop','ok','',True),('stop','','private fixture text',False),('length','partial','',False),('tool_calls','','',True)]:
 rec={}; message={'role':'assistant','content':content,'reasoning_content':reasoning}
 if finish=='tool_calls': message['tool_calls']=[{'id':'fixture','function':{'name':'fixture','arguments':'{}'}}]
 payload={'model':'fixture','choices':[{'finish_reason':finish,'message':message}]}
 try: m.complete(payload,rec); accepted=True
 except ValueError: accepted=False
 assert accepted==expected
 assert 'private fixture text' not in json.dumps(rec)
 assert rec['response_shape']['choices'][0]['content_characters']==len(content)
 cases.append({'finish_reason':finish,'accepted':accepted,'expected':expected,'diagnostics_without_text':True})
out={'passed':True,'model_called':False,'cases':cases}; (root/'reports/diagnostic_admission.json').write_text(json.dumps(out,indent=2)); print(json.dumps(out))
