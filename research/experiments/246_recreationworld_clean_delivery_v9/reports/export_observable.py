"""Export observable benchmark actions and images, excluding private reasoning."""
import base64,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=json.loads((ROOT/'reports/pipeline_status.json').read_text()); run=ROOT/'runs'/s['attempt']
key=json.loads((ROOT.parent/'238_recreationworld_deepseek_vision/private/provider.json').read_text())['api_key']
dest=ROOT/'public_trajectory'; (dest/'images').mkdir(parents=True,exist_ok=True)
image_count=0
def clean(v):
 global image_count
 if isinstance(v,str): return re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',v.replace(key,'[REDACTED]'))
 if isinstance(v,list): return [clean(x) for x in v]
 if isinstance(v,dict):
  if v.get('type')=='image' and v.get('source',{}).get('type')=='base64':
   source=v['source']; raw=base64.b64decode(source['data'],validate=True); sha=hashlib.sha256(raw).hexdigest(); ext={'image/png':'.png','image/jpeg':'.jpg','image/webp':'.webp','image/gif':'.gif'}.get(source.get('media_type'),'.bin')
   name='images/'+sha+ext; (dest/name).write_bytes(raw); image_count+=1
   return {'type':'image_observation','path':name,'sha256':sha,'media_type':source.get('media_type')}
  return {k:clean(x) for k,x in v.items() if k not in ('thinking','reasoning_content','signature')}
 return v
path=run/'trajectory.jsonl'; rows=[json.loads(x) for x in path.read_text().splitlines() if x]; output=[]
for i,row in enumerate(rows):
 blocks=row.get('message',{}).get('content',[])
 if isinstance(blocks,list):
  for block in blocks:
   if isinstance(block,dict) and block.get('type') in ('tool_use','tool_result'): output.append({'source_record':i,'observable':clean(block)})
(dest/'actions_and_observations.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in output)+'\n')
prompt=run/'recreation/prompt.txt'
if prompt.exists(): (dest/'task_instruction.txt').write_text(clean(prompt.read_text())+'\n\n'+(ROOT/'execution_guidance.txt').read_text())
manifest={'version':s['version'],'attempt':s['attempt'],'task_id':s['task_id'],'requested_model':s['model'],'reported_model':'deepseek-v4.1-flash','exact_checkpoint_unverified':True,'fresh_scaffold':True,'baseline':False,'additional_guidance':True,'canary_excluded':True,'private_reasoning_excluded':True,'credentials_redacted':True,'records':len(output),'image_observations':image_count,'raw_trajectory_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'observable_sha256':hashlib.sha256((dest/'actions_and_observations.jsonl').read_bytes()).hexdigest()}
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2)); print(json.dumps({'records':len(output),'image_observations':image_count}))
