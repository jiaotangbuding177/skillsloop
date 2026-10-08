"""Mechanical local export of stable messages/images; never claim learning acceptance."""
import base64,hashlib,json,re,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];EXP=ROOT.parent
SOURCES={'minipaint':[
 EXP/'285_rw_evolution_collection/runs/recreation_eval_1791121638371741570',
 EXP/'288_rw_parallel_evolution_collection/runs/minipaint_recreation_eval_1791126784363902808',
 EXP/'288_rw_parallel_evolution_collection/runs/minipaint_recreation_eval_1791129685783416430'],
 'squoosh':[EXP/'288_rw_parallel_evolution_collection/runs/squoosh_recreation_eval_1791129536850164583']}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def redact(s,counts):
 s,n=re.subn(r'\bsk-[A-Za-z0-9_-]{12,}\b','[REDACTED_CREDENTIAL]',s);counts['credential_redactions']+=n
 s,n=re.subn(r'(?i)(Bearer\s+)(?!local\b)[A-Za-z0-9_.-]{12,}',r'\1[REDACTED_CREDENTIAL]',s);counts['credential_redactions']+=n
 return s
def main():
 summary={'epoch':time.time(),'model_calls':0,'skills_learning_started':False,'families':{}}
 for family,attempts in SOURCES.items():
  dest=ROOT/'exports'/family;assert not dest.exists(),'Preserve prior export';(dest/'images').mkdir(parents=True)
  counts=Counter();seen={};events=[];index=[];image_index={};pending={};results=set();conflicts=[]
  def convert(value,ordinal):
   if isinstance(value,str):return redact(value,counts)
   if isinstance(value,list):return [v for x in value if (v:=convert(x,ordinal)) is not None]
   if not isinstance(value,dict):return value
   if value.get('type') in ('thinking','redacted_thinking','reasoning','reasoning_content'):
    counts['hidden_reasoning_blocks_excluded']+=1;return None
   source=value.get('source',{})
   if value.get('type')=='image' and source.get('type')=='base64':
    binary=base64.b64decode(source['data'],validate=True);digest=hashlib.sha256(binary).hexdigest();media=source.get('media_type','application/octet-stream');ext={'image/png':'png','image/jpeg':'jpg','image/webp':'webp','image/gif':'gif'}.get(media,'bin')
    path=dest/'images'/f'{digest}.{ext}'
    if not path.exists():path.write_bytes(binary)
    image_index.setdefault(digest,{'sha256':digest,'bytes':len(binary),'media_type':media,'path':str(path.relative_to(dest)),'source_event_ordinals':[]})['source_event_ordinals'].append(ordinal)
    counts['image_observation_blocks']+=1
    return {'type':'image_reference','sha256':digest,'media_type':media,'path':str(path.relative_to(dest)),'source_type':'native_inline_image','exact_per_request_consumer_mapping':'pending'}
   return {k:v for k,x in value.items() if k not in ('thinking','reasoning_content','signature') and (v:=convert(x,ordinal)) is not None}
  for round_no,attempt in enumerate(attempts,1):
   raw=attempt/'private_raw_sessions';manifest=json.loads((raw/'copy_manifest.json').read_text())
   mains=[]
   for f in manifest['files']:
    src=raw/f['file'];assert sha(src)==f['source_sha256']==f['copied_sha256'] and src.stat().st_size==f['bytes']
    if src.suffix=='.jsonl' and len(Path(f['file']).parts)==2:mains.append(src)
   assert len(mains)==1
   added=0;duplicates=0
   for line_no,line in enumerate(mains[0].read_text().splitlines(),1):
    j=json.loads(line);message=j.get('message');counts['raw_records_examined']+=1
    if not isinstance(message,dict) or message.get('role') not in ('user','assistant'):continue
    event_key=j.get('uuid') or f'{round_no}:{line_no}'
    canonical=json.dumps(message,sort_keys=True,ensure_ascii=False);digest=hashlib.sha256(canonical.encode()).hexdigest()
    if event_key in seen:
     if seen[event_key]!=digest:conflicts.append({'uuid':event_key,'round':round_no,'source_line':line_no});continue
     duplicates+=1;continue
    seen[event_key]=digest;ordinal=len(events)+1
    content=convert(message.get('content',''),ordinal)
    e={'ordinal':ordinal,'source_uuid':j.get('uuid'),'round_first_observed':round_no,'native_role':message['role'],
       'content':content,'source_line':line_no,'source_session':str(mains[0]),
       'user_role_may_be_tool_result_not_human':True}
    events.append(e);added+=1
    if isinstance(content,list):
     for b in content:
      if not isinstance(b,dict):continue
      if b.get('type')=='tool_use':pending[b['id']]={'name':b.get('name'),'ordinal':ordinal};counts['tool_calls']+=1
      if b.get('type')=='tool_result':results.add(b['tool_use_id']);counts['tool_results']+=1
   index.append({'round':round_no,'attempt':str(attempt),'source_session_sha256':sha(mains[0]),
                 'new_public_message_events':added,'inherited_duplicate_uuid_events_removed':duplicates,
                 'raw_manifest_sha256':sha(raw/'copy_manifest.json')})
  with (dest/'public_messages.jsonl').open('w') as out:
   for e in events:out.write(json.dumps(e,ensure_ascii=False)+'\n')
  (dest/'image_index.json').write_text(json.dumps(list(image_index.values()),indent=2))
  (dest/'round_index.json').write_text(json.dumps(index,indent=2))
  (dest/'public_text_view.txt').write_text('\n\n'.join('EVENT '+str(e['ordinal'])+' ROUND '+str(e['round_first_observed'])+' ROLE '+e['native_role']+'\n'+json.dumps(e['content'],ensure_ascii=False) for e in events))
  report={'family':family,'phase':'mechanical_export_pending_semantic_and_learning_admission',
          'rounds':len(attempts),'public_message_events':len(events),'unique_images':len(image_index),'counts':dict(counts),
          'unmatched_tool_call_ids':sorted(set(pending)-results),'orphan_tool_result_ids':sorted(results-set(pending)),
          'conflicting_uuid_records':conflicts,'outcome_labels_injected_into_actor_messages':False,
          'hidden_reasoning_excluded':True,'no_synthetic_success_added':True,
          'originality_and_private_source_access_audit':'pending','actual_AutoSkill_input_admission':'not performed',
          'image_pixels_consumed_by_text_only_AutoSkill':False,'final_scores_retained_in_original_sidecars':True,
          'public_view_sha256':sha(dest/'public_messages.jsonl'),'text_view_sha256':sha(dest/'public_text_view.txt')}
  (dest/'export_manifest.json').write_text(json.dumps(report,indent=2));summary['families'][family]=report
 (ROOT/'reports/existing_public_exports.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:{'events':v['public_message_events'],'images':v['unique_images'],'unmatched':len(v['unmatched_tool_call_ids']),'conflicts':len(v['conflicting_uuid_records'])} for k,v in summary['families'].items()}))
if __name__=='__main__':main()
