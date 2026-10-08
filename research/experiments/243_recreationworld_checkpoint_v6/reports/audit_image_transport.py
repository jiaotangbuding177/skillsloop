import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'reports'))
from proxy_source_audit.translator import anthropic_message_to_openai_messages
sample={'type':'image','source':{'type':'base64','media_type':'image/png','data':'fixture_base64'}}
converted=anthropic_message_to_openai_messages({'role':'user','content':[{'type':'tool_result','tool_use_id':'fixture','content':[sample]}]})
assert isinstance(converted[0]['content'],str) and 'fixture_base64' in converted[0]['content']
status=json.loads((ROOT/'reports/pipeline_status.json').read_text()); name='rw238-'+status['attempt']
raw=subprocess.check_output(['docker','exec',name,'cat','/workspace/recreation/trajectory.jsonl'],text=True)
images=[]
def walk(v):
 if isinstance(v,dict):
  if v.get('type')=='image' and v.get('source',{}).get('type')=='base64': images.append({'mime':v['source'].get('media_type'),'encoded_length':len(v['source'].get('data',''))})
  for x in v.values(): walk(x)
 elif isinstance(v,list):
  for x in v: walk(x)
for line in raw.splitlines(): walk(json.loads(line))
report={'official_adapter_serializes_image_as_text':True,'synthetic_exact_path_verified':True,'native_image_blocks':len(images),'encoded_characters':sum(x['encoded_length'] for x in images),'mime_types':sorted(set(x['mime'] for x in images)),'current_run_not_correct_multimodal_transport':bool(images),'provider_timeout_exact_causality_unproven':True}
(ROOT/'reports/image_transport_audit.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))
