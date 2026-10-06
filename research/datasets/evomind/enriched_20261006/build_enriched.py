"""Rebuild an evidence-enriched view of frozen enterprise history; never execute historical code.
Run from any directory with Python 3.10+. No third-party dependency or network call.
"""
from pathlib import Path
from collections import Counter, defaultdict
import ast, csv, hashlib, html, json, re, sys

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
OUT=ROOT/'private'
S=BASE/'screening_20261006'
A=BASE/'analysis_20261005'
K=BASE/'km_skill_audit_20261005'
RAW_SAMPLE=Path('C:/Users/39835/Downloads/zkys-raw-export-20260925/raw_payload_sample.jsonl')
INPUTS={
 'corpus':BASE/'matched_066/private/evomind_conversations.json',
 'annotations':BASE/'accepted_071/private/accepted_annotations.json',
 'screening':S/'private/screened_sessions.json',
 'candidates':S/'private/learning_candidates.jsonl',
 'noise':S/'private/deterministic_noise.json',
 'protected_noise':S/'private/noise_semantic_overrides.json',
 'topics':A/'private/session_task_categories.json',
 'files':A/'private/file_metadata_inventory.json',
 'tool_refs':S/'private/tool_refs.json',
 'skill_evidence':K/'private/classified_events.json',
 'skill_provenance':K/'private/skill_provenance.json',
 'raw_tool_sample':RAW_SAMPLE,
 'clean_functions':A/'analyze_local.py',
 'redact_functions':S/'prepare_review.py',
 'frozen_screening_manifest':S/'screening_manifest.json',
}
SUPPLEMENT=ROOT/'review/private/supplemental_candidates.jsonl'
if SUPPLEMENT.exists():INPUTS['supplemental_candidates']=SUPPLEMENT

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8-sig').splitlines() if x.strip()]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jsonl(p,rows):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('w',encoding='utf-8') as f:
  for row in rows:f.write(json.dumps(row,ensure_ascii=False)+'\n')
def safe(x,key=''):
 # Opaque event identifiers are join keys, not credential payload.
 if isinstance(x,str) and key in {'id','session_id','sessionId','owner_id','userId','agentInstanceId','group_id','message_id','tool_call_id','toolCallId','call_id','record_id','file_reference_id','evidence_id','kind','basis','method','granularity','annotation_scope','origin','source_file','status','copy_kind','numeric_scheme','role','name','tool','skill','reported_yaml_name','schema','schema_version'}:return x
 if isinstance(x,str):return redact(x)
 if isinstance(x,list):return [safe(y,key) for y in x]
 if isinstance(x,dict):return {k:safe(v,k) for k,v in x.items()}
 return x

def load_functions():
 ns={'re':re}
 for path,names in [(INPUTS['clean_functions'],{'clean'}),(INPUTS['redact_functions'],{'redact','clean_user'})]:
  nodes=[n for n in ast.parse(path.read_text(encoding='utf-8')).body if isinstance(n,ast.FunctionDef) and n.name in names]
  assert len(nodes)==len(names)
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
 return ns['redact'],ns['clean_user']
_base_redact,clean_user=load_functions()
def redact(text):
 text=_base_redact(text)
 return re.sub(r'(?i)((?:密码|授权码|密钥|口令)(?:是|为)?\s*[:：=]\s*[\"\']?)[A-Za-z0-9_+/=.\-]{6,}',r'\1[凭据已隐藏]',text)

def association_view(s,labels):
 links={x['assistant_group_id']:set(x.get('user_group_ids',[])) for x in s['associations']}
 evidence={}
 for key,lab in labels.items():
  role,gid=key.split(':',1)
  if role=='user':
   for aid,us in links.items():us.discard(gid);evidence.pop((gid,aid),None)
   if lab['decision']=='matched':
    for aid in lab['targets']:
     links.setdefault(aid,set()).add(gid);evidence[(gid,aid)]={'annotation_key':key,'basis':lab.get('basis',''),'note':lab.get('note','')}
  elif role=='assistant':
   links[gid]=set(lab['targets']) if lab['decision']=='matched' else set()
   for pair in list(evidence):
    if pair[1]==gid:evidence.pop(pair)
   for uid in links[gid]:evidence[(uid,gid)]={'annotation_key':key,'basis':lab.get('basis',''),'note':lab.get('note','')}
 accepted=[];proposed=[]
 for aid,us in links.items():
  for uid in sorted(us):
   edge={'user_group_id':uid,'assistant_group_id':aid,'chronology_verified':False,'same_task_verified':False}
   if (uid,aid) in evidence:accepted.append({**edge,'source':'accepted_071','evidence':evidence[(uid,aid)],'meaning':'用户验收的内容对应；来源含AI建议与人工选择，不是全人工或时序真值'})
   else:proposed.append({**edge,'source':'matched_066','meaning':'原位置或语义对应候选，未由071该项标注覆盖'})
 return accepted,proposed

def extract_tools(source):
 records=[]
 def add(sid,mid,t,origin,group=''):
  if not isinstance(t,dict):return
  records.append({'session_id':sid,'message_id':mid,'group_id':group,'origin':origin,'tool_call_id':t.get('toolCallId',t.get('tool_call_id')),'name':t.get('name',''),'status':t.get('status',''),'args':t.get('args',t.get('arguments',{})),'output':t.get('output',''),'error':t.get('error'),'started_at':t.get('startedAt')})
 for sid,s in source.items():
  for key in ['user_requests','assistant_contents']:
   for g in s[key]:
    for o in g['occurrences']:
     rp=o.get('raw_record',{}).get('rawPayload') or {};ts=rp.get('toolActivity',[])
     for t in ts if isinstance(ts,list) else [ts]:add(sid,o['id'],t,'message_toolActivity',g['group_id'])
 text=RAW_SAMPLE.read_text(encoding='utf-8-sig');decoder=json.JSONDecoder(strict=False);pos=0
 while pos<len(text):
  while pos<len(text) and text[pos].isspace():pos+=1
  if pos>=len(text):break
  x,pos=decoder.raw_decode(text,pos)
  if x.get('sessionId') not in source:continue
  rp=x.get('rawPayload') or {};ts=rp.get('toolActivity',[])
  for t in ts if isinstance(ts,list) else [ts]:add(x['sessionId'],x['id'],t,'raw_sample_toolActivity')
  if rp.get('name'):
   t={**rp};t.setdefault('output',x.get('content',''));t.setdefault('status',x.get('status',''));add(x['sessionId'],x['id'],t,'raw_sample_top_level')
 def j(x):return x if isinstance(x,str) else json.dumps(x,ensure_ascii=False)
 unique={}
 for r in records:
  key=(r['session_id'],r['tool_call_id'] or r['message_id'],r['name'],j(r['args']))
  ref={k:r[k] for k in ['origin','message_id','group_id']}
  if key not in unique:unique[key]={**r,'source_refs':[ref],'snapshot_statuses':[r['status']]}
  else:
   old=unique[key];old['source_refs'].append(ref);old['snapshot_statuses'].append(r['status'])
   if len(j(r['output']))>len(j(old['output'])):old['output']=r['output']
   if r['status']=='completed':old['status']='completed'
   if r.get('error'):old['error']=r['error']
 result=[]
 for i,r in enumerate(unique.values()):
  r={**r,'record_id':f'tool_{i:05d}','record_index':i,'evidence_scope':'有限历史工具快照；同一调用可能有多个来源，状态不认证整个任务成功','historical_command_executed':False}
  result.append(safe(r))
 return result

def dedup_view(groups):
 """Exact same-role cleaned text only. Keep alias IDs and every source occurrence."""
 out=[];seen={}
 for g in groups:
  if g.get('noise_reason') or not g['content'].strip():continue
  key=(g['role'],g.get('cleaned_content_fingerprint',re.sub(r'\s+',' ',g['content']).strip()))
  if key not in seen:
   x={**g,'source_group_ids':[g['group_id']],'source_occurrences':list(g['occurrences']),'source_group_memberships':{g['group_id']:g.get('inclusion','full_context')},'learning_active':True,'exact_clean_duplicate_of':None};seen[key]=len(out);out.append(x)
  else:
   x=out[seen[key]];x['source_group_ids'].append(g['group_id']);x['source_occurrences']+=g['occurrences'];x['source_group_memberships'][g['group_id']]=g.get('inclusion','full_context')
   if g.get('inclusion')=='SEED':x['inclusion']='SEED'
   x['relation_indices']=sorted(set(x.get('relation_indices',[])+g.get('relation_indices',[])))
 return out

CSS='body{margin:0;background:#f3f6fb;color:#172536;font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1160px;margin:32px auto;padding:0 20px}a{color:#1552aa}header,.box,article,details{background:white;border:1px solid #dce4ee;border-radius:12px;padding:18px;margin:12px 0}h1{font-size:28px}h2{font-size:22px}.meta{color:#596777;font-size:13px}.badge{display:inline-block;padding:3px 9px;border-radius:6px;background:#e9f0fa;margin-right:6px}pre{font:inherit;white-space:pre-wrap;overflow-wrap:anywhere}input,select{font:inherit;padding:9px;border:1px solid #b9c8da;border-radius:7px}summary{cursor:pointer;font-weight:600}.muted{color:#68788b}.noise{background:#f6f6f6}table{border-collapse:collapse;width:100%}td,th{text-align:left;border-bottom:1px solid #dce4ee;padding:9px}nav{display:flex;gap:16px;flex-wrap:wrap}section{scroll-margin-top:15px}'
def esc(x):return html.escape(str(x))
def page(title,body):return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(title)+'</title><style>'+CSS+'</style><main>'+body+'</main></html>'
def msg_html(g,fold=False):
 meta=f"{g['role']} · {g['group_id']} · {len(g.get('source_occurrences',g['occurrences']))}次来源记录"
 if len(g.get('source_group_ids',[]))>1:meta+=' · 同文别名 '+', '.join(g['source_group_ids'])
 flags=[]
 if g.get('noise_reason'):flags.append('已清理噪声：'+g['noise_reason'])
 if g.get('exact_clean_duplicate_of'):flags.append('与 '+g['exact_clean_duplicate_of']+' 清理后正文完全相同')
 content='<p class="meta">'+esc(meta)+'<br>'+esc('；'.join(flags))+'</p><pre>'+esc(g['content'])+'</pre>'
 if g.get('wrapper_changed'):content+='<details><summary>去包装前正文（明显凭据已隐藏）</summary><pre>'+esc(g['original_content_sanitized'])+'</pre></details>'
 if fold:return '<details id="'+g['group_id']+'"><summary>'+esc(meta)+'</summary>'+content+'</details>'
 return '<section id="'+g['group_id']+'" class="box '+('noise' if not g['learning_active'] else '')+'">'+content+'</section>'

def main():
 for d in [OUT,OUT/'sessions',OUT/'contexts']:d.mkdir(parents=True,exist_ok=True)
 before={k:sha(v) for k,v in INPUTS.items()}
 source=read(INPUTS['corpus']);ann=read(INPUTS['annotations']);screen={x['session_id']:x for x in read(INPUTS['screening'])};topics={x['session_id']:x for x in read(INPUTS['topics'])}
 manifest=read(INPUTS['frozen_screening_manifest']);prep=read(S/'preparation_manifest.json')
 assert before['corpus']==prep['source_sha256'] and before['annotations']==prep['annotations_sha256'] and before['topics']==prep['categories_sha256']
 original=lines(INPUTS['candidates']);supp=lines(SUPPLEMENT) if SUPPLEMENT.exists() else []
 for c in supp:
  c.setdefault('source_user_ids',c.get('user_ids',[]));c.setdefault('source_assistant_ids',c.get('assistant_ids',[]));c.setdefault('learning_candidate',c.get('lesson',''));c.setdefault('candidate_id',c['session_id']+':supp01')
 all_candidates=[{**c,'pool':'original_711'} for c in original]+[{**c,'pool':'supplemental_review'} for c in supp]
 assert len({c['candidate_id'] for c in all_candidates})==len(all_candidates)
 noise={(x['session_id'],x['assistant_id']):x['reason'] for x in read(INPUTS['noise'])}
 protected={(x['session_id'],x['assistant_id']) for x in read(INPUTS['protected_noise'])}
 files=read(INPUTS['files']);filemap=defaultdict(list)
 for i,f in enumerate(files):filemap[f['session_id']].append({'file_reference_id':f'file_{i:05d}',**safe(f),'attachment_bytes_restored':False})
 tools=extract_tools(source);refs=read(INPUTS['tool_refs']);toolmap=defaultdict(list)
 for t in tools:toolmap[t['session_id']].append(t)
 assert len(tools)==sum(len(v) for v in refs.values())==3578
 for sid,items in refs.items():assert [(x['record_index'],x['tool'],x['call_id']) for x in items]==[(x['record_index'],x['name'],x['tool_call_id']) for x in toolmap[sid]]
 skillmap=defaultdict(list);provenance={x['skill']:x for x in read(INPUTS['skill_provenance'])}
 for i,x in enumerate(read(INPUTS['skill_evidence'])):
  x=safe(x);skillmap[x['session_id']].append({'evidence_id':f'skill_ev_{i:04d}',**x,'evidence_scope':'路径/读取/执行/管理等分级证据；并非全部有效使用','provenance':{k:provenance.get(x['skill'],{}).get(k) for k in ['source_class','platform_class','user_installation','retrieval']}})
 cmap=defaultdict(list)
 for c in all_candidates:cmap[c['session_id']].append(c)
 sessions=[];contexts=[];counts=Counter();base_counts=Counter();effective_counts=Counter();csvrows=[]
 for sid,s in source.items():
  accepted,proposed=association_view(s,ann['labels'].get(sid,{}));groups=[];seen={};groups_by_id={};known_occ=set()
  for source_key,role in [('user_requests','user'),('assistant_contents','assistant')]:
   for g in s[source_key]:
    raw=g['content'];cleaned=clean_user(raw) if role=='user' else raw.strip();text=redact(cleaned)
    clean_fingerprint=hashlib.sha256(re.sub(r'\s+',' ',cleaned).strip().encode()).hexdigest();duplicate=seen.get((role,clean_fingerprint));seen.setdefault((role,clean_fingerprint),g['group_id'])
    occurrences=[]
    for o in g['occurrences']:
     known_occ.add(o['id']);occurrences.append({k:safe(o.get(k),k) for k in ['id','role','status','source_line','source_file','copy_kind','user_created_at','dated_source_position','numeric_scheme','numeric_id']})
    gr={'group_id':g['group_id'],'role':role,'content':text,'original_content_sanitized':redact(raw),'wrapper_changed':cleaned!=raw.strip(),'occurrences':occurrences,'learning_active':not bool((sid,g['group_id']) in noise or duplicate or not text.strip()),'noise_reason':noise.get((sid,g['group_id'])),'protected_short_reply':(sid,g['group_id']) in protected,'exact_clean_duplicate_of':duplicate,'source_content_sha256':hashlib.sha256(raw.encode()).hexdigest(),'cleaned_content_fingerprint':clean_fingerprint,'order_in_role_view':len(groups),'chronology_verified':False}
    groups.append(gr);groups_by_id[gr['group_id']]=gr;counts[role+'_groups']+=1;counts['occurrences']+=len(occurrences);counts['noise_groups']+=bool(gr['noise_reason']);counts['clean_duplicate_groups']+=bool(duplicate);counts['cleaned_wrapper_groups']+=gr['wrapper_changed']
  archive=[]
  for key in ['retry_controls','empty_ai_events','other_events']:
   for n,event in enumerate(s[key]):
    archive.append({'archive_id':f'{sid}:{key}:{n}','kind':key,'learning_active':False,'content':redact(event.get('content','')),'source_metadata':safe({k:v for k,v in event.items() if k not in ['content','raw_record','matched_user_source_record']}),'archive_reason':'历史控制/空消息保留作审计，不混入学习正文' if key!='other_events' else '其他角色保留，未独立解释其学习含义'})
    counts[key]+=1
  for edge in accepted+proposed:assert edge['user_group_id'] in groups_by_id and edge['assistant_group_id'] in groups_by_id
  counts['accepted_edges']+=len(accepted);counts['proposed_edges']+=len(proposed)
  base=screen[sid]['decision'];effective='KEEP' if any(c['pool']=='supplemental_review' for c in cmap[sid]) else base
  base_counts[base]+=1;effective_counts[effective]+=1
  ss={'schema':'evomind-evidence-enriched-v1','session_id':sid,'owner_id':s['owner_id'],'source_title':redact(s['session_metadata'].get('title','')),'title_used_as_task_truth':False,'source_session_metadata':safe(s['session_metadata']),'dated_session_metadata':safe(s['dated_session_metadata']),'original_screening':screen[sid],'effective_screening_decision':effective,'screening_changed_by_supplemental_review':effective!=base,'supplemental_review_findings':[{'candidate_id':c['candidate_id'],'task':c['task'],'learning_candidate':c['learning_candidate']} for c in cmap[sid] if c['pool']=='supplemental_review'],'topic_annotation':topics[sid],'messages':groups,'accepted_content_correspondences':accepted,'unverified_correspondence_candidates':proposed,'annotation_decisions_071':safe(ann['labels'].get(sid,{})),'archive_events':archive,'source_order_ids':s['source_order_ids'],'source_order_diagnostics':s['source_order_diagnostics'],'chronology_verified':False,'original_counts':s['original_counts'],'file_references':filemap[sid],'tool_record_ids':[t['record_id'] for t in toolmap[sid]],'skill_evidence':skillmap[sid],'candidate_ids':[c['candidate_id'] for c in cmap[sid]],'unknowns':['完整原始消息时序未核验','缺失附件和产物字节未补造','业务结果与技能收益未独立验证'],'tool_scope':'group/message锚点指向日志承载来源；toolActivity可能为累积快照，不能据此认证调用发生时刻或任务归属。缺组锚点仅会话级关联，不强配任务','source_corpus_sha256':before['corpus']}
  sessions.append(ss)
  for c in cmap[sid]:
   seed=set(c['source_user_ids']+c['source_assistant_ids']);assert seed<=set(groups_by_id),(sid,seed-set(groups_by_id))
   quote=re.sub(r'\s+','',c.get('evidence_quote',''));quoted=re.sub(r'\s+','', ''.join(groups_by_id[g]['original_content_sanitized'] for g in seed))
   assert not quote or re.sub(r'\s+','',redact(c['evidence_quote'])) in quoted,(sid,'quote mismatch')
   selected=set(seed);edge_ids=[];reasons=defaultdict(list)
   for n,e in enumerate(accepted):
    pair={e['user_group_id'],e['assistant_group_id']}
    if pair&seed:selected|=pair;edge_ids.append(n)
   new_ai={g for g in selected-seed if groups_by_id[g]['role']=='assistant'}
   for n,e in enumerate(accepted):
    if e['assistant_group_id'] in new_ai:selected.add(e['user_group_id']);edge_ids.append(n)
   for n in set(edge_ids):
    e=accepted[n]
    for g in [e['user_group_id'],e['assistant_group_id']]:reasons[g].append(n)
   cm=[]
   for g in groups:
    if g['group_id'] in selected:cm.append({**g,'inclusion':'SEED' if g['group_id'] in seed else 'linked_context','relation_indices':reasons[g['group_id']]})
   cm=dedup_view(cm)
   obj={'schema':'evomind-candidate-context-v1','candidate_id':c['candidate_id'],'session_id':sid,'pool':c['pool'],'task':redact(c['task']),'learning_candidate':redact(c['learning_candidate']),'evidence_quote':redact(c.get('evidence_quote','')),'limitations':c.get('limitations',[]),'seed_group_ids':sorted(seed),'expanded_group_ids':sorted(selected-seed),'messages':cm,'included_associations':[accepted[n] for n in sorted(set(edge_ids))],'expansion_rule':'种子的一跳已验收内容对应；新增AI关联的共同用户作上下文。非递归连通分量，扩入不认证同任务。','source_user_ids':c['source_user_ids'],'source_assistant_ids':c['source_assistant_ids'],'complete_trace_verified':False,'chronology_verified':False,'task_success':'unknown','review_basis':c.get('review_basis',''),'group_identity_note':'group_id指向会话唯一消息组；跨候选共用不代表新真实事件','linked_file_reference_ids':[f['file_reference_id'] for f in filemap[sid] if f.get('group_id') in selected],'session_tool_record_ids':ss['tool_record_ids'],'tool_assignment_to_candidate':'仅提供会话级清单，未确认该候选实际使用全部工具或skill','session_skill_evidence_ids':[x['evidence_id'] for x in skillmap[sid]]}
   contexts.append(obj);counts['candidate_seed_memberships']+=len(seed);counts['candidate_context_memberships']+=len(selected);counts['candidates_expanded']+=bool(selected-seed);counts['new_context_memberships']+=len(selected-seed)
   fname=c['candidate_id'].replace(':','_');parts=[f"# {c['task']}",'',f"会话：{sid}；候选：{c['candidate_id']}",'','这是带上下文的学习材料，扩入消息不等于同一任务，也不是完整黄金轨迹。','','可学习线索：'+c['learning_candidate'],'','边界：'+'；'.join(c.get('limitations',[])),'']
   body='<header><h1>'+esc(c['task'])+'</h1><p>'+esc(c['learning_candidate'])+'</p><p>来源种子 '+str(len(seed))+' 组；扩入上下文 '+str(len(selected-seed))+' 组。不是完整黄金轨迹，未认证时序或任务成功。</p><a href="../sessions/'+sid+'.html">查看完整会话及全部证据</a></header>'
   for g in cm:
    parts+=['## '+('原筛选种子' if g['inclusion']=='SEED' else '对应关系扩入上下文')+' · '+('用户' if g['role']=='user' else 'AI'),'',g['group_id'],'',g['content'],''];body+='<span class="badge">'+('种子' if g['inclusion']=='SEED' else '扩入上下文')+'</span>'+msg_html(g)
   (OUT/'contexts'/f'{fname}.md').write_text('\n'.join(parts),encoding='utf-8');(OUT/'contexts'/f'{fname}.html').write_text(page(c['task'],body),encoding='utf-8')
  title=ss['source_title'];decision_cn={'KEEP':'保留候选','HOLD':'暂存','EXCLUDE':'排除提炼'}[effective]
  body='<header><nav><a href="../index.html">返回全量目录</a><a href="'+sid+'.md">审计Markdown</a><a href="'+sid+'.reading.html">去重阅读全文</a><a href="../../../matched_066/private/index.html#'+sid+'">原066会话页</a></nav><h1>'+esc(sid)+'</h1><p>原始标题（不作为任务真值）：'+esc(title)+'</p><p><span class="badge">'+decision_cn+'</span>'+'上一轮理由：'+esc(screen[sid]['reason'])+('；本轮全文补漏发现：'+esc('；'.join(c['task'] for c in cmap[sid] if c['pool']=='supplemental_review')) if effective!=base else '')+'</p><p>全文按角色与内容对应展示；这些不是已经证明的原始时间顺序。此页是审计视图，完全同文别名折叠保留。去重阅读页每种同角色正文只显示一次，并合并全部来源。</p></header>'
  md=[f'# {sid}：完整会话证据','',f'原始标题（不作为任务真值）：{title}','',f'筛选：{decision_cn}；原结论：{base}。'+screen[sid]['reason'],'','本页按角色展示全部正文与内容对应，不宣称原始时序。空回复、重试与重复来源单独保留。','']
  if cmap[sid]:
   body+='<div class="box"><h2>学习候选与扩入上下文</h2>'
   for c in cmap[sid]:body+='<p><a href="../contexts/'+c['candidate_id'].replace(':','_')+'.html">'+esc(c['task'])+'</a> · '+('原711池' if c['pool']=='original_711' else '本轮补漏')+'</p>'
   body+='</div>'
  body+='<div class="box"><h2>内容对应关系</h2><p>071接受关系 '+str(len(accepted))+' 条；066未验候选 '+str(len(proposed))+' 条。AI建议经用户验收，不等于逐条人工真值。</p>'
  md+=['## 内容对应关系','']
  for e in accepted:body+='<p><a href="#'+e['user_group_id']+'">用户 '+e['user_group_id']+'</a> → <a href="#'+e['assistant_group_id']+'">AI '+e['assistant_group_id']+'</a> · '+esc(e['evidence']['basis'])+'</p>';md +=[e['user_group_id']+' → '+e['assistant_group_id']+'（071已接受内容对应，非时序）']
  body+='</div><h2>用户与 AI 完整正文</h2>'
  for g in groups:
   body+=msg_html(g,fold=g['role']=='assistant' or not g['learning_active']);md+=['','## '+('用户' if g['role']=='user' else 'AI')+' · '+g['group_id'],'','来源：'+'；'.join(o['id']+'（原行'+str(o['source_line'])+'）' for o in g['occurrences']),'',('学习视图停用原因：'+str(g['noise_reason'] or ('完全重复于'+g['exact_clean_duplicate_of'] if g['exact_clean_duplicate_of'] else '空正文')) if not g['learning_active'] else '学习上下文保留；不代表已认证技能价值'),'',g['content']]
  body+='<details><summary>文件、工具和skills证据（点击展开）</summary><p>附件引用 '+str(len(filemap[sid]))+'；工具快照 '+str(len(toolmap[sid]))+'；skill分级证据 '+str(len(skillmap[sid]))+'。有日志不等于本地可运行或业务成功。</p><pre>'+esc(json.dumps({'file_references':filemap[sid],'tools':toolmap[sid],'skill_evidence':skillmap[sid]},ensure_ascii=False,indent=2))+'</pre></details>'
  md+=['','## 文件与执行证据','',f"文件引用{len(filemap[sid])}条；工具快照{len(toolmap[sid])}条；skill分级证据{len(skillmap[sid])}条。文件字节未补造，工具参数及返回请见同名HTML证据折叠区或tools.jsonl。",'','## 空回复、重试及其他历史事件（不进入学习正文）','']
  for x in archive:md+=[x['archive_id']+' · '+x['kind'],'',x['content'] or '（空正文）','']
  body+='<details><summary>历史空回复/重试/其他事件 '+str(len(archive))+' 条</summary><pre>'+esc(json.dumps(archive,ensure_ascii=False,indent=2))+'</pre></details>'
  reading=dedup_view(groups)
  reading_body='<header><a href="'+sid+'.html">返回完整审计与关联证据</a><h1>'+esc(sid)+' · 去重阅读全文</h1><p>同会话、同角色、清理后完全相同正文合并显示一次；全部来源编号保留。按角色展示，不认证时序或任务成功。</p></header>'+''.join(msg_html(g,fold=g['role']=='assistant') for g in reading)
  (OUT/'sessions'/f'{sid}.reading.html').write_text(page(sid+'去重阅读',reading_body),encoding='utf-8')
  (OUT/'sessions'/f'{sid}.html').write_text(page(sid,body),encoding='utf-8');(OUT/'sessions'/f'{sid}.md').write_text('\n'.join(md),encoding='utf-8')
  csvrows.append({'session_id':sid,'original_decision':base,'effective_decision':effective,'primary_topic':topics[sid]['primary'],'user_groups':len(s['user_requests']),'ai_groups':len(s['assistant_contents']),'accepted_edges':len(accepted),'unverified_edges':len(proposed),'file_refs':len(filemap[sid]),'tool_records':len(toolmap[sid]),'skill_evidence':len(skillmap[sid]),'candidate_count':len(cmap[sid]),'archive_events':len(archive),'chronology_verified':False,'source_title':title})
 source_inputs=[]
 for ss in sessions:
  source_inputs.append({'schema':'evomind-source-input-v1','session_id':ss['session_id'],'owner_id':ss['owner_id'],'dated_session_metadata':ss['dated_session_metadata'],'messages':[{'group_id':g['group_id'],'source_group_ids':g['source_group_ids'],'role':g['role'],'content':g['content'],'cleaned_content_fingerprint':g['cleaned_content_fingerprint'],'source_occurrences':g['source_occurrences']} for g in dedup_view(ss['messages'])],'file_references':ss['file_references'],'tool_record_ids':ss['tool_record_ids'],'tool_records_file':'tools.jsonl','chronology_verified':False,'presentation':'role-grouped source content, not chronological turns','annotation_labels_included':False,'selected_task_or_lesson_included':False,'source_corpus_sha256':ss['source_corpus_sha256']})
 jsonl(OUT/'source_inputs.jsonl',source_inputs)
 jsonl(OUT/'enriched_sessions.jsonl',sessions);jsonl(OUT/'candidate_contexts.jsonl',[c for c in contexts if c['pool']=='original_711']);jsonl(OUT/'candidate_contexts_supplement.jsonl',[c for c in contexts if c['pool']=='supplemental_review']);jsonl(OUT/'candidate_contexts_union.jsonl',contexts);jsonl(OUT/'tools.jsonl',tools);jsonl(OUT/'file_references.jsonl',[f for fs in filemap.values() for f in fs])
 with (OUT/'session_inventory.csv').open('w',encoding='utf-8-sig',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(csvrows[0]));w.writeheader();w.writerows(csvrows)
 cards=[]
 for row,ss in zip(csvrows,sessions):
  search=ss['session_id']+' '+ss['source_title']+' '+ss['original_screening']['reason']+' '+ss['topic_annotation']['primary']+' '+' '.join(c['task'] for c in cmap[ss['session_id']])
  cards.append('<article data-decision="'+row['effective_decision']+'" data-search="'+esc(search.lower())+'"><a href="sessions/'+row['session_id']+'.html"><strong>'+row['session_id']+'</strong></a><span class="badge">'+{'KEEP':'保留','HOLD':'暂存','EXCLUDE':'排除'}[row['effective_decision']]+'</span><p>'+esc(ss['source_title'])+'</p><p>'+'上一版理由：'+esc(ss['original_screening']['reason'])+('</p><p>本轮补漏：'+esc('；'.join(c['task'] for c in cmap[ss['session_id']] if c['pool']=='supplemental_review')) if row['effective_decision']!=row['original_decision'] else '')+'</p><p class="meta">用户 '+str(row['user_groups'])+' / AI '+str(row['ai_groups'])+'；候选 '+str(row['candidate_count'])+'；文件引用 '+str(row['file_refs'])+'；工具 '+str(row['tool_records'])+'；skills证据 '+str(row['skill_evidence'])+'</p></article>')
 summary={'sessions':len(sessions),'real_session_count_increased':False,'original_screening':dict(base_counts),'effective_screening':dict(effective_counts),'original_candidate_count':len(original),'supplemental_candidate_count':len(supp),'union_candidate_count':len(contexts),**dict(counts),'file_reference_records':len(files),'file_reference_sessions':len({f['session_id'] for f in files}),'tool_records':len(tools),'tool_sessions':sum(bool(v) for v in toolmap.values()),'tool_records_with_group_anchor':sum(any(r.get('group_id') for r in t['source_refs']) for t in tools),'skill_evidence_records':sum(len(v) for v in skillmap.values()),'skill_evidence_sessions':sum(bool(v) for v in skillmap.values()),'skill_evidence_kind_counts':dict(Counter(x['kind'] for v in skillmap.values() for x in v)),'skill_evidence_sessions_by_kind':{kind:len({sid for sid,v in skillmap.items() if any(x['kind']==kind for x in v)}) for kind in sorted({x['kind'] for v in skillmap.values() for x in v})},'annotation_071_sessions':len(ann['labels']),'annotation_071_decisions':sum(len(v) for v in ann['labels'].values()),'annotation_basis_counts':dict(Counter(x.get('basis','') for v in ann['labels'].values() for x in v.values())),'original_seed_unique_groups':len({(c['session_id'],g) for c in contexts if c['pool']=='original_711' for g in c['seed_group_ids']}),'original_expanded_unique_groups':len({(c['session_id'],g) for c in contexts if c['pool']=='original_711' for m in c['messages'] for g in m.get('source_group_ids',[m['group_id']])}),'source_input_unique_text_groups':sum(len(x['messages']) for x in source_inputs),'source_input_group_aliases_preserved':sum(len(g['source_group_ids']) for x in source_inputs for g in x['messages']),'source_input_alias_merges':sum(len(g['source_group_ids'])-1 for x in source_inputs for g in x['messages']),'source_input_occurrences_preserved':sum(len(g['source_occurrences']) for x in source_inputs for g in x['messages']),'original_context_unique_text_groups':len({(c['session_id'],m['role'],m['cleaned_content_fingerprint']) for c in contexts if c['pool']=='original_711' for m in c['messages']}),'original_context_display_memberships':sum(len(c['messages']) for c in contexts if c['pool']=='original_711'),'original_linked_context_display_memberships':sum(m.get('inclusion')=='linked_context' for c in contexts if c['pool']=='original_711' for m in c['messages']),'candidate_context_alias_merges':sum(len(g.get('source_group_ids',[]))-1 for c in contexts for g in c['messages']),'new_external_model_calls':0,'skill_generation_runs':0,'synthetic_dialogues_created':0,'attachment_bytes_restored':0,'complete_trace_certified':0,'source_hashes_unchanged':all(sha(INPUTS[k])==v for k,v in before.items())}
 assert summary['source_hashes_unchanged']
 header='<header><h1>EvoMind 全量会话 · 证据富化版</h1><p>1466条真实会话完整正文；保留原711个种子，并按已接受内容对应补齐上下文。没有虚增真实会话、补造文件或认证成功轨迹。</p><p>当前可学习候选会话 '+str(effective_counts['KEEP'])+'；暂存 '+str(effective_counts['HOLD'])+'；排除 '+str(effective_counts['EXCLUDE'])+'；原候选 '+str(len(original))+' + 本轮补漏 '+str(len(supp))+'。</p><nav><a href="session_inventory.csv">下载清单CSV</a><a href="../README.md">数据说明</a><a href="../partition/README.md">分集与泄漏控制</a><a href="../method_research.md">数据演化研究</a></nav></header><div class="box"><input id="q" placeholder="搜索会话、标题、任务、筛选理由" size="43"><select id="d"><option value="">全部</option><option>KEEP</option><option>HOLD</option><option>EXCLUDE</option></select><p id="n"></p></div>'
 script='<script>function filter(){let q=document.getElementById("q").value.toLowerCase(),d=document.getElementById("d").value,n=0;document.querySelectorAll("article").forEach(x=>{let show=(!d||x.dataset.decision===d)&&x.dataset.search.includes(q);x.hidden=!show;if(show)n++});document.getElementById("n").textContent="当前显示 "+n+" 条会话"}document.getElementById("q").oninput=filter;document.getElementById("d").onchange=filter;filter()</script>'
 (OUT/'index.html').write_text(page('EvoMind 全量会话证据富化',header+''.join(cards)+script),encoding='utf-8')
 dump(ROOT/'summary.json',summary)
 checks={'1466_sessions':len(sessions)==1466,'all_source_sessions_once':len({x['session_id'] for x in sessions})==len(source),'all_user_and_ai_groups_preserved':counts['user_groups']==8202 and counts['assistant_groups']==19734,'original_screening_unchanged':dict(base_counts)=={'KEEP':708,'HOLD':516,'EXCLUDE':242},'original_711_preserved':len(original)==711,'source_hashes_unchanged':summary['source_hashes_unchanged'],'tool_inventory_matches_frozen_3578':len(tools)==3578,'file_refs_preserved':len(files)==1767,'all_candidates_have_valid_source_ids':True,'all_edges_have_valid_source_ids':True,'no_success_or_chronology_certification':all(not c['complete_trace_verified'] and c['task_success']=='unknown' for c in contexts),'canonical_group_identity_shared':all(len({m['group_id'] for m in c['messages']})==len(c['messages']) for c in contexts),'all_session_text_and_html_written':all((OUT/'sessions'/f'{sid}.{ext}').exists() for sid in source for ext in ['md','html']),'all_candidate_text_and_html_written':all((OUT/'contexts'/(c['candidate_id'].replace(':','_')+'.'+ext)).exists() for c in contexts for ext in ['md','html'])}
 # Every relative HTML href must resolve; fragments are separate correspondence evidence.
 missing=[]
 for p in [OUT/'index.html',*(OUT/'sessions').glob('*.html'),*(OUT/'contexts').glob('*.html')]:
  for ref in re.findall(r'href="([^"#][^"]*)"',p.read_text(encoding='utf-8')):
   if '://' in ref:continue
   target=(p.parent/html.unescape(ref.split('#',1)[0])).resolve()
   if target in [ROOT/'README.md',ROOT/'method_research.md',ROOT/'partition/README.md'] and not target.exists():continue
   if not target.exists():missing.append(str(target))
 checks['all_local_html_links_resolve']=not missing
 checks['skill_kind_enums_match_original']=Counter(x['kind'] for v in skillmap.values() for x in v)==Counter(x['kind'] for x in read(INPUTS['skill_evidence']))
 checks['071_annotation_basis_preserved']=all(ss['annotation_decisions_071']==safe(ann['labels'].get(ss['session_id'],{})) and all(v.get('basis')==ann['labels'][ss['session_id']][k].get('basis') for k,v in ss['annotation_decisions_071'].items()) for ss in sessions)
 checks['source_inputs_no_exact_same_role_text_duplicates']=all(len({(g['role'],g['cleaned_content_fingerprint']) for g in x['messages']})==len(x['messages']) for x in source_inputs)
 checks['candidate_contexts_no_exact_same_role_text_duplicates']=all(len({(g['role'],g['cleaned_content_fingerprint']) for g in x['messages']})==len(x['messages']) for x in contexts)
 checks['source_inputs_all_sessions_no_annotation_labels']=len(source_inputs)==1466 and all('topic_annotation' not in x and 'accepted_content_correspondences' not in x and 'original_screening' not in x for x in source_inputs)
 dump(ROOT/'validation.json',{'checks':checks,'passed':all(checks.values()),'passed_count':sum(checks.values()),'check_count':len(checks),'missing_links':missing,'meaning':'来源、覆盖、文件与结构一致性检查；不是语义准确率、轨迹真值或收益认证'})
 output_paths=[OUT/'source_inputs.jsonl',OUT/'enriched_sessions.jsonl',OUT/'candidate_contexts.jsonl',OUT/'candidate_contexts_supplement.jsonl',OUT/'candidate_contexts_union.jsonl',OUT/'tools.jsonl',OUT/'file_references.jsonl',OUT/'index.html',OUT/'session_inventory.csv',ROOT/'summary.json',ROOT/'validation.json']
 output_paths+=list((OUT/'sessions').glob('*'))+list((OUT/'contexts').glob('*'))
 dump(ROOT/'manifest.json',{'schema':'evomind-enrichment-manifest-v1','inputs':{k:{'path':str(v),'sha256':before[k]} for k,v in INPUTS.items()},'script':{'path':str(Path(__file__)),'sha256':sha(Path(__file__))},'outputs':{str(p.relative_to(ROOT)):sha(p) for p in output_paths},'source_hashes_unchanged':True,'frozen_natural_history':True,'rebuild_command':'python -X utf8 research/datasets/evomind/enriched_20261006/build_enriched.py'})
 print(json.dumps({'summary':summary,'checks_passed':sum(checks.values()),'checks_total':len(checks)},ensure_ascii=False))
 if not all(checks.values()):raise SystemExit(2)
if __name__=='__main__':main()
