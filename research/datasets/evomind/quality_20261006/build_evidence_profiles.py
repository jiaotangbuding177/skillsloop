"""Objective evidence inventory of 719 learning candidates; no semantic score or API calls."""
from pathlib import Path
from collections import Counter,defaultdict
import csv,hashlib,json,statistics,sys
R=Path(__file__).resolve().parent;P=R/'private';B=R.parent/'enriched_20261006'
INPUTS={'candidates':B/'private/candidate_contexts_union.jsonl','sessions':B/'private/enriched_sessions.jsonl','tools':B/'private/tools.jsonl','enriched_manifest':B/'manifest.json'}
LABELS=['单边素材','一问一答素材','单用户多AI素材','多用户输入素材']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def readrows(p):
 with p.open(encoding='utf-8') as f:
  for line in f:
   if line.strip():yield json.loads(line)
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def writejsonl(p,xs):
 with p.open('w',encoding='utf-8') as f:
  for x in xs:f.write(json.dumps(x,ensure_ascii=False)+'\n')
def distribution(xs):
 a=sorted(xs);n=len(a)
 return {'min':a[0] if a else None,'median':statistics.median(a) if a else None,'p90':a[min(n-1,int((n-1)*.9))] if a else None,'max':a[-1] if a else None,'sum':sum(a),'mean':statistics.mean(a) if a else None}
def anchor_refs(obj,aliases,mids):
 matches=[]
 for ref in obj.get('source_refs',[]):
  bases=[]
  if ref.get('group_id') in aliases:bases.append('source_group_id')
  if ref.get('message_id') in mids:bases.append('source_occurrence_message_id')
  if bases:matches.append({'group_id':ref.get('group_id'),'message_id':ref.get('message_id'),'basis':bases,'origin':ref.get('origin')})
 return matches

def main():
 P.mkdir(parents=True,exist_ok=True)
 hashes={k:sha(p) for k,p in INPUTS.items()}
 frozen=json.loads(INPUTS['enriched_manifest'].read_text(encoding='utf-8'))
 for k in ['candidates','sessions','tools']:
  rel=str(INPUTS[k].relative_to(B));assert frozen['outputs'][rel]==hashes[k],('unfrozen input',k)
 candidates=list(readrows(INPUTS['candidates']));sessions={x['session_id']:x for x in readrows(INPUTS['sessions'])};toolmap=defaultdict(list)
 for t in readrows(INPUTS['tools']):toolmap[t['session_id']].append({k:t.get(k) for k in ['record_id','session_id','name','status','source_refs','started_at']})
 profiles=[];validation_errors=[]
 for c in candidates:
  s=sessions[c['session_id']];raw={g['group_id']:g for g in s['messages']};messages=[g for g in c['messages'] if g.get('learning_active',True) and g['content'].strip()]
  aliases={x for g in messages for x in g.get('source_group_ids',[g['group_id']])};canonical={x:g['group_id'] for g in messages for x in g.get('source_group_ids',[g['group_id']])}
  seed=set(c['seed_group_ids']);expanded=set(c['expanded_group_ids']);anchors=seed|expanded;missing=sorted(anchors-set(raw));source_occ=[o for gid in sorted(anchors-set(missing)) for o in raw[gid]['occurrences']]
  bad_locator=[{'group_id':gid,'message_id':o.get('id')} for gid in sorted(anchors-set(missing)) for o in raw[gid]['occurrences'] if not o.get('id') or not o.get('source_file') or o.get('source_line') is None]
  no_occ=[gid for gid in sorted(anchors-set(missing)) if not raw[gid]['occurrences']]
  mids={o['id'] for gid in aliases for o in raw[gid]['occurrences']}
  users=[g for g in messages if g['role']=='user'];ais=[g for g in messages if g['role']=='assistant'];u=len(users);a=len(ais)
  structure=LABELS[0] if not u or not a else LABELS[1] if u==1 and a==1 else LABELS[2] if u==1 else LABELS[3]
  accepted=[e for e in s['accepted_content_correspondences'] if e['user_group_id'] in aliases and e['assistant_group_id'] in aliases]
  proposed=[e for e in s['unverified_correspondence_candidates'] if e['user_group_id'] in aliases and e['assistant_group_id'] in aliases]
  accepted_pairs={(canonical[e['user_group_id']],canonical[e['assistant_group_id']]) for e in accepted};proposed_pairs={(canonical[e['user_group_id']],canonical[e['assistant_group_id']]) for e in proposed}
  human=[]
  for key,decision in s['annotation_decisions_071'].items():
   if decision.get('basis')!='human_explicit_selection':continue
   role,gid=key.split(':',1);targets=set(decision.get('targets',[]));involved={gid}|targets
   if involved&anchors:human.append({'annotation_key':key,'decision':decision['decision'],'targets':sorted(targets),'source_group_matches':sorted(involved&anchors),'all_endpoints_in_candidate':involved<=anchors,'has_matched_both_endpoints':decision['decision']=='matched' and bool(targets) and involved<=anchors,'basis':decision['basis']})
  anchored_tools=[]
  for t in toolmap[s['session_id']]:
   matched=anchor_refs(t,aliases,mids)
   if matched:anchored_tools.append({'record_id':t['record_id'],'tool':t['name'],'status':t['status'],'matched_payload_source_refs':matched,'task_execution_attribution':'not_certified'})
  candidate_files=[]
  for f in s['file_references']:
   if f.get('group_id') in aliases or f.get('message_id') in mids:candidate_files.append(f)
  anchored_skills=[]
  for ev in s['skill_evidence']:
   matched=anchor_refs(ev,aliases,mids)
   if matched:anchored_skills.append({'evidence_id':ev['evidence_id'],'skill':ev['skill'],'kind':ev['kind'],'matched_payload_source_refs':matched})
  seed_texts=[g for g in messages if set(g.get('source_group_ids',[g['group_id']]))&seed]
  context_texts=[g for g in messages if not set(g.get('source_group_ids',[g['group_id']]))&seed]
  mixed=[g for g in messages if set(g.get('source_group_ids',[g['group_id']]))&seed and set(g.get('source_group_ids',[g['group_id']]))&expanded]
  coverage='已有显式对应' if accepted else '仅有待核对应候选' if proposed else '当前窗口无对应记录'
  complete=not(missing or no_occ or bad_locator)
  linked_groups={x for e in accepted for x in [e['user_group_id'],e['assistant_group_id']]}
  timeline=[o for o in source_occ if o.get('user_created_at')]
  quote=c.get('evidence_quote','');norm=lambda t:''.join(str(t).split());quote_in_reading=bool(quote) and any(norm(quote) in norm(g['content']) for g in messages)
  quote_in_source=bool(quote) and any(norm(quote) in norm(raw[gid].get('original_content_sanitized',raw[gid]['content'])) for gid in anchors if gid in raw)
  obj={'schema':'evomind-objective-evidence-profile-v1','candidate_id':c['candidate_id'],'session_id':c['session_id'],'task':c['task'],'topic_code':s['topic_annotation']['primary'],'learning_candidate':c['learning_candidate'],'evidence_quote':quote,'evidence_quote_in_reading_text':quote_in_reading,'evidence_quote_in_source_text':quote_in_source,'limitations':c.get('limitations',[]),'pool':c['pool'],'review_basis':c.get('review_basis'),'structure_label':structure,'user_text_count':u,'assistant_text_count':a,'text_count':len(messages),'char_count':sum(len(g['content']) for g in messages),'user_char_count':sum(len(g['content']) for g in users),'assistant_char_count':sum(len(g['content']) for g in ais),'seed_text_count':len(seed_texts),'expanded_context_count':len(context_texts),'mixed_alias_text_count':len(mixed),'seed_source_group_count':len(seed),'expanded_source_group_count':len(expanded),'readable_alias_count':len(aliases),'source_anchor_count':len(anchors),'source_anchor_found_count':len(anchors)-len(missing),'source_anchor_complete':complete,'source_traceability_label':'来源锚点可完整回查' if complete else '来源锚点或出现定位不完整','source_anchor_missing_ids':missing,'source_anchor_no_occurrence_ids':no_occ,'incomplete_occurrence_locators':bad_locator,'source_anchor_without_reading_text_ids':sorted(anchors-aliases),'source_occurrence_count':len(source_occ),'accepted_local_edge_count':len(accepted),'proposed_local_edge_count':len(proposed),'accepted_reading_pair_count':len(accepted_pairs),'proposed_reading_pair_count':len(proposed_pairs),'accepted_linked_reading_text_count':len({canonical[x] for x in linked_groups}),'content_correspondence_status':coverage,'accepted_local_edges':accepted,'proposed_local_edges':proposed,'human_local_decision_count':len(human),'human_both_end_local_decision_count':sum(x['has_matched_both_endpoints'] for x in human),'human_annotation_source_records':human,'session_tool_count':len(toolmap[s['session_id']]),'payload_anchored_tool_count':len(anchored_tools),'payload_anchored_tools':anchored_tools,'session_file_reference_count':len(s['file_references']),'candidate_file_reference_count':len(candidate_files),'candidate_file_reference_ids':[f['file_reference_id'] for f in candidate_files],'candidate_file_bytes_available_count':sum(f.get('bytes_available_in_export') is True or f.get('attachment_bytes_restored') is True for f in candidate_files),'session_skill_evidence_count':len(s['skill_evidence']),'session_skill_evidence_kind_counts':dict(Counter(x['kind'] for x in s['skill_evidence'])),'payload_anchored_skill_evidence_count':len(anchored_skills),'payload_anchored_skill_evidence':anchored_skills,'known_user_time_occurrence_count':len(timeline),'bilateral_readable':bool(u and a),'content_diversity_label':structure,'chronology_verified':False,'same_task_feedback_verified':False,'task_outcome_verified':False,'artifact_bytes_restored':False,'external_execution_status':'未认证：载荷来源锚点不是该任务执行归因','artifact_status':'仅有元数据，当前候选无已补回字节' if candidate_files else '本候选未联到文件元数据，不代表任务无需文件','time_status':'部分用户出现有时间，完整用户—AI时序未认证' if timeline else '所选来源缺可用用户时间，完整时序未认证','quality_score':None,'semantic_quality_certified':False,'candidate_html':'../enriched_20261006/private/contexts/'+c['candidate_id'].replace(':','_')+'.html','session_html':'../enriched_20261006/private/sessions/'+c['session_id']+'.html','counts_note':'文本数按去重阅读组；来源组/出现次数/对应边分别计数，不称真实回合数。'}
  profiles.append(obj)
  if not complete:validation_errors.append({'candidate_id':c['candidate_id'],'issue':'incomplete_source_locator','missing':missing,'bad_locator':bad_locator})
 assert len(profiles)==len(candidates)==719 and len({x['candidate_id'] for x in profiles})==719
 writejsonl(P/'evidence_profiles.jsonl',profiles)
 complex_fields={'accepted_local_edges','proposed_local_edges','human_annotation_source_records','payload_anchored_tools','payload_anchored_skill_evidence','incomplete_occurrence_locators'}
 fields=[k for k in profiles[0] if k not in complex_fields]
 with (P/'evidence_profiles.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
  for p in profiles:w.writerow({k:json.dumps(p[k],ensure_ascii=False) if isinstance(p[k],(dict,list)) else p[k] for k in fields})
 metrics=['user_text_count','assistant_text_count','text_count','char_count','seed_text_count','expanded_context_count','source_anchor_count','accepted_local_edge_count','proposed_local_edge_count','human_local_decision_count','payload_anchored_tool_count','session_tool_count','candidate_file_reference_count','session_file_reference_count','session_skill_evidence_count']
 by_topic={k:{'candidate_count':sum(p['topic_code']==k for p in profiles),'structure_counts':dict(Counter(p['structure_label'] for p in profiles if p['topic_code']==k))} for k in sorted({p['topic_code'] for p in profiles})}
 summary={'candidate_count':719,'unique_session_count':len({x['session_id'] for x in profiles}),'pool_counts':dict(Counter(p['pool'] for p in profiles)),'structure_counts':{k:sum(p['structure_label']==k for p in profiles) for k in LABELS},'correspondence_counts':dict(Counter(p['content_correspondence_status'] for p in profiles)),'evidence_quotes_found_in_reading_count':sum(p['evidence_quote_in_reading_text'] for p in profiles),'evidence_quotes_found_in_source_count':sum(p['evidence_quote_in_source_text'] for p in profiles),'source_anchor_complete_count':sum(p['source_anchor_complete'] for p in profiles),'bilateral_readable_count':sum(p['bilateral_readable'] for p in profiles),'candidates_with_expanded_context':sum(p['expanded_context_count']>0 for p in profiles),'candidates_with_source_anchors_excluded_from_reading':sum(bool(p['source_anchor_without_reading_text_ids']) for p in profiles),'candidate_with_human_relevant_annotation_count':sum(p['human_local_decision_count']>0 for p in profiles),'candidate_with_human_both_end_match_count':sum(p['human_both_end_local_decision_count']>0 for p in profiles),'candidate_with_payload_anchored_tools_count':sum(p['payload_anchored_tool_count']>0 for p in profiles),'candidate_with_any_session_tool_count':sum(p['session_tool_count']>0 for p in profiles),'candidate_with_file_metadata_count':sum(p['candidate_file_reference_count']>0 for p in profiles),'candidate_with_session_skill_evidence_count':sum(p['session_skill_evidence_count']>0 for p in profiles),'candidate_with_payload_anchored_skill_evidence_count':sum(p['payload_anchored_skill_evidence_count']>0 for p in profiles),'candidate_with_known_user_timestamp_count':sum(p['known_user_time_occurrence_count']>0 for p in profiles),'restored_file_bytes_count':sum(p['candidate_file_bytes_available_count'] for p in profiles),'certified_complete_trace_count':0,'certified_successful_task_count':0,'certified_effective_skill_count':0,'metric_distributions':{k:distribution([p[k] for p in profiles]) for k in metrics},'by_topic':by_topic,'structural_classification_is_semantic_quality':False,'model_api_calls':0,'historical_commands_executed':False,'limitations':['分档只描述文本角色和数量，不能证明连续回合、同任务修订、方法质量或复用效果','071显式对应含多种标注来源，人工选项也不是任务或时序黄金真值','工具来源锚点可能位于累积快照，只能证明该载荷承载此记录','会话级文件/skill工具记录不能自动归给候选任务','候选间可共享同一会话和消息，指标汇总有成员重复，不能当独立真实事件总量']}
 expansion_cases=[]
 for c,p in zip(candidates,profiles):
  if c['expanded_group_ids'] and p['expanded_context_count']==0:
   omitted=[{'group_id':gid,'noise_reason':next(g for g in sessions[c['session_id']]['messages'] if g['group_id']==gid).get('noise_reason')} for gid in c['expanded_group_ids'] if gid in p['source_anchor_without_reading_text_ids']]
   expansion_cases.append({'candidate_id':c['candidate_id'],'expanded_source_group_ids':c['expanded_group_ids'],'mixed_alias_text_count':p['mixed_alias_text_count'],'omitted_expanded_anchors':omitted,'reason':'新增来源组与已有种子清理后同文，合并别名不新增正文' if not omitted else '新增来源组属于既定纯进度噪声，审计保留而不进入阅读'})
 summary['expansion_comparison']={'candidates_with_added_source_group_context':sum(bool(c['expanded_group_ids']) for c in candidates),'candidates_with_added_independent_reading_text':sum(p['expanded_context_count']>0 for p in profiles),'difference_cases':expansion_cases,'interpretation':'162是新增来源组的窗口数；158是新增独立阅读正文的窗口数。3条同文别名合并、1条固定纯进度噪声清理；未改写上轮来源组统计。'}
 dump(R/'evidence_summary.json',summary)
 schema={'description':'客观证据画像，不输出语义总分','structure_rules':{'单边素材':'用户正文数为0或AI正文数为0','一问一答素材':'1条用户正文、1条AI正文；不因此认证真实回复关系','单用户多AI素材':'1条用户正文且2条以上AI正文','多用户输入素材':'2条以上用户正文且至少1条AI正文；不推定这些输入属于同一任务或是反馈'},'fields':{
 'candidate_id':'719个候选的稳定唯一编号','session_id':'真实来源会话编号，候选不是新增会话','task':'继承已有筛选任务描述，不是本轮重新认证','topic_code':'继承会话主主题，不是候选方法聚类或新主题判断','learning_candidate':'已有可学习线索，非有效skill认证','limitations':'旧候选明确边界','structure_label':'只按去重角色正文数量分档，无高低分','user_text_count':'活跃、非空、去重用户正文数；不是人头数或真实轮数','assistant_text_count':'活跃、非空、去重AI正文数','text_count':'全部活跃去重正文数','char_count':'正文字符数，不含新增标题和字段；不是token数','seed_text_count':'至少一个别名属于原种子的正文数','expanded_context_count':'所有别名均不在种子中的扩入上下文正文数','mixed_alias_text_count':'同时含种子和扩入别名，按seed计一次','source_anchor_count':'原种子+扩入来源group编号并集数，包含被移出阅读的噪声/空白来源','source_anchor_complete':'每个来源group在enriched审计中存在、至少一个出现、每个出现有id/源文件/源行号','source_anchor_without_reading_text_ids':'仍可回查但因固定噪声/空白清理未进入阅读正文的锚点','accepted_local_edge_count':'071显式接受的边中，用户和AI两个原组都在候选阅读别名集合内的边数','proposed_local_edge_count':'066待核对应中，两端都在候选阅读别名集合的边数','accepted_reading_pair_count':'将对应边两端别名映射到去重正文后，独立正文对数','proposed_reading_pair_count':'待核边映射去重正文后的独立正文对数','content_correspondence_status':'只描述已有局部记录覆盖；没有记录不代表真实无回复','human_local_decision_count':'071 basis为human_explicit_selection且至少一个端点涉及候选原锚点的标注项数，含无匹配项，不称纯人工黄金','human_both_end_local_decision_count':'上述人工显式匹配项所有端点都在候选原锚点中的项数','session_tool_count':'同来源会话工具快照记录数，不是候选调用数','payload_anchored_tool_count':'source_refs的group或message与候选阅读别名/出现ID相交的工具记录数，只是载荷定位','candidate_file_reference_count':'文件元数据group或message与候选阅读别名/出现ID相交的引用次数；不是不同实体文件数','session_file_reference_count':'会话的所有文件元数据引用次数','session_skill_evidence_count':'会话全部分级技能证据含管理、失败、读取、执行尝试','payload_anchored_skill_evidence_count':'载荷来源可定位到候选阅读别名的分级技能证据数，不保证实际有效应用','known_user_time_occurrence_count':'所选原锚点出现中有user_created_at的次数，不含AI时间补造','quality_score':'恒为null，不凑总分','semantic_quality_certified':'恒为false，本轮不做专业内容正确性与技能收益认证','candidate_html':'相对于quality_20261006目录的原候选正文链接','session_html':'相对于quality_20261006目录的完整审计页链接'}}
 dump(R/'evidence_profile_schema.json',schema)
 checks={'719_candidates_once':len(profiles)==719 and len({p['candidate_id'] for p in profiles})==719,'candidate_ids_exactly_match_source':{p['candidate_id'] for p in profiles}=={c['candidate_id'] for c in candidates},'716_source_sessions':len({p['session_id'] for p in profiles})==716,'all_role_counts_sum':all(p['text_count']==p['user_text_count']+p['assistant_text_count'] for p in profiles),'all_seed_context_counts_sum':all(p['text_count']==p['seed_text_count']+p['expanded_context_count'] for p in profiles),'all_anchor_locators_complete':not validation_errors,'local_edges_with_both_endpoints':all(all(e['user_group_id'] in {g for m in candidates[i]['messages'] for g in m['source_group_ids']} and e['assistant_group_id'] in {g for m in candidates[i]['messages'] for g in m['source_group_ids']} for e in p['accepted_local_edges']+p['proposed_local_edges']) for i,p in enumerate(profiles)),'payload_tool_counts_le_session':all(p['payload_anchored_tool_count']<=p['session_tool_count'] for p in profiles),'candidate_file_counts_le_session':all(p['candidate_file_reference_count']<=p['session_file_reference_count'] for p in profiles),'no_fabricated_quality_or_outcome':all(p['quality_score'] is None and not p['semantic_quality_certified'] and not p['task_outcome_verified'] and not p['chronology_verified'] for p in profiles),'source_hashes_unchanged':all(sha(INPUTS[k])==h for k,h in hashes.items()),'all_reference_pages_exist':all((R/p['candidate_html']).resolve().exists() and (R/p['session_html']).resolve().exists() for p in profiles)}
 dump(R/'evidence_validation.json',{'passed':all(checks.values()),'passed_count':sum(checks.values()),'check_count':len(checks),'checks':checks,'locator_issues':validation_errors,'meaning':'覆盖与客观计数/来源检查，不是语义质量或黄金认证'})
 outputs=[P/'evidence_profiles.jsonl',P/'evidence_profiles.csv',R/'evidence_summary.json',R/'evidence_profile_schema.json',R/'evidence_validation.json']
 dump(R/'evidence_manifest.json',{'inputs':{k:{'path':str(p),'sha256':hashes[k]} for k,p in INPUTS.items()},'script':{'path':str(Path(__file__)),'sha256':sha(Path(__file__))},'outputs':{str(p.relative_to(R)):sha(p) for p in outputs},'rebuild_command':'python -X utf8 research/datasets/evomind/quality_20261006/build_evidence_profiles.py'})
 print(json.dumps({'candidates':len(profiles),'structure_counts':summary['structure_counts'],'correspondence_counts':summary['correspondence_counts'],'checks':f"{sum(checks.values())}/{len(checks)}"},ensure_ascii=False))
 if not all(checks.values()):raise SystemExit(2)
if __name__=='__main__':main()
