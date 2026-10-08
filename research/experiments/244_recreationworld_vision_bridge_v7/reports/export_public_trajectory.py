"""Export observable actions/receipts only; no reasoning blocks or credentials."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT.parent
key=json.loads((BASE/'238_recreationworld_deepseek_vision/private/provider.json').read_text())['api_key']
def safe(value):
 if isinstance(value,str): return re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',value.replace(key,'[REDACTED]'))
 if isinstance(value,list): return [safe(x) for x in value]
 if isinstance(value,dict):
  if value.get('type')=='thinking': return {'type':'omitted_private_reasoning'}
  if value.get('type')=='image':
   source=value.get('source',{}); data=source.get('data','')
   return {'type':'image_observation','media_type':source.get('media_type'),'encoded_data_sha256':hashlib.sha256(data.encode()).hexdigest()}
  return {k:safe(v) for k,v in value.items() if k not in ('reasoning_content','thinking','signature')}
 return value
segments=[]; lines=[]; seen=set()
for directory in ['240_recreationworld_delivery_hint_v3','241_recreationworld_infra_resume_v4','242_recreationworld_stream_resume_v5','243_recreationworld_checkpoint_v6','244_recreationworld_vision_bridge_v7']:
 root=BASE/directory; status=json.loads((root/'reports/pipeline_status.json').read_text()); run=root/'runs'/status['attempt']; path=run/'trajectory.jsonl'
 if not path.exists() and directory=='243_recreationworld_checkpoint_v6': path=ROOT/'private/recovery/retained_failed_workspace/trajectory.jsonl'
 rows=[json.loads(x) for x in path.read_text().splitlines() if x] if path.exists() else []
 segment={'version':status['version'],'attempt':status['attempt'],'native_state':status['state'],'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None,'actions':0,'tool_results':0}
 for i,row in enumerate(rows):
  blocks=row.get('message',{}).get('content',[])
  if not isinstance(blocks,list): continue
  for block in blocks:
   if not isinstance(block,dict) or block.get('type') not in ('tool_use','tool_result'): continue
   identity=(block.get('type'),block.get('id') or block.get('tool_use_id'),hashlib.sha256(json.dumps(block,sort_keys=True).encode()).hexdigest())
   if identity in seen: continue
   seen.add(identity)
   lines.append(json.dumps({'segment':len(segments),'source_record':i,'observable':safe(block)},ensure_ascii=False))
   segment['actions' if block['type']=='tool_use' else 'tool_results']+=1
 segments.append(segment)
out=ROOT/'public_trajectory'; out.mkdir(exist_ok=True)
(out/'actions_and_observations.jsonl').write_text('\n'.join(lines)+'\n')
manifest={'task_id':'corravale.example','requested_model':'deepseek-v4-flash-vision-exp','model_reported':'deepseek-v4.1-flash','exact_checkpoint_unverified':True,'recovery_chain':True,'baseline':False,'private_reasoning_excluded':True,'credentials_redacted':True,'segments':segments,'observable_records':len(lines),'export_sha256':hashlib.sha256((out/'actions_and_observations.jsonl').read_bytes()).hexdigest()}
(out/'manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'segments':len(segments),'observable_records':len(lines)}))
