"""Rebuild the private screening deliverables from frozen semantic decisions.

No model/service requests and no historical command execution. Source files remain intact.
"""
from pathlib import Path
from collections import Counter, defaultdict
import ast, csv, hashlib, html, json, re, sys

R=Path(__file__).resolve().parent; B=R.parent; P=R/'private'
SOURCE=B/'matched_066/private/evomind_conversations.json'
ANN=B/'accepted_071/private/accepted_annotations.json'
CATS=B/'analysis_20261005/private/session_task_categories.json'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# Extract only reviewed functions rather than importing preparation side effects.
ns={'re':re}
for path,names in [(B/'analysis_20261005/analyze_local.py',{'clean'}),(R/'prepare_review.py',{'redact','clean_user','assoc'})]:
    tree=ast.parse(path.read_text(encoding='utf-8'))
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
redact,clean_user,assoc=[ns[n] for n in ('redact','clean_user','assoc')]
source=json.loads(SOURCE.read_text(encoding='utf-8'))
annotations=json.loads(ANN.read_text(encoding='utf-8'))['labels']
cats={x['session_id']:x for x in json.loads(CATS.read_text(encoding='utf-8'))}
prep=json.loads((R/'preparation_manifest.json').read_text(encoding='utf-8'))
assert sha(SOURCE)==prep['source_sha256'] and sha(ANN)==prep['annotations_sha256']
assert sha(CATS)==prep['categories_sha256']
labels=[]
for i in range(1,4):
    p=P/f'shard_{i}/review_labels.json'
    batch=json.loads(p.read_text(encoding='utf-8'))
    expected=json.loads((p.parent/'assigned_ids.json').read_text(encoding='utf-8'))
    assert len(batch)==len(expected) and {x['session_id'] for x in batch}==set(expected),(i,len(batch),len(expected))
    labels.extend(batch)
assert len(labels)==len(source) and len({x['session_id'] for x in labels})==len(source)
labelmap={x['session_id']:x for x in labels}
# Root boundary review is an explicit, auditable overlay; originals retained.
op=P/'boundary_review_overrides.json'
if op.exists():
    for x in json.loads(op.read_text(encoding='utf-8')):
        sid=x['session_id'];assert sid in labelmap
        labelmap[sid]={**labelmap[sid],**x}

noise=json.loads((P/'deterministic_noise.json').read_text(encoding='utf-8'))
noiseids={(n['session_id'],n['assistant_id']) for n in noise}
tools=json.loads((P/'tool_refs.json').read_text(encoding='utf-8'))
sessionrows=[]; candidates=[]; errors=[]; kept_u=set();kept_a=set();repeat_group_merges=0
candidate_root=P/'candidate_texts';candidate_root.mkdir(exist_ok=True)

def compact(t):return re.sub(r'\s+','',t)
def group_record(g,role):
    text=clean_user(g['content']) if role=='user' else g['content'].strip()
    return {'role':role,'group_ids':[g['group_id']],'content':redact(text),
            'source_refs':[{'message_id':o['id'],'line':o.get('source_line'),'file':o.get('source_file')} for o in g['occurrences']],
            'attachment_metadata_refs':sum(len((o.get('raw_record',{}).get('rawPayload') or {}).get('files') or []) for o in g['occurrences'])}

for sid,s in source.items():
    label=labelmap[sid];decision=label['decision']; assert decision in {'KEEP','HOLD','EXCLUDE'}
    proposed=label.get('candidates',[])
    assert (decision=='KEEP')==bool(proposed),(sid,decision,len(proposed))
    umap={u['group_id']:u for u in s['user_requests']};amap={a['group_id']:a for a in s['assistant_contents']}
    links=assoc(s,annotations.get(sid,{}));out=[]
    for n,c in enumerate(proposed,1):
        uids=list(dict.fromkeys(c.get('user_ids',[])));aids=list(dict.fromkeys(c.get('assistant_ids',[])))
        if not uids or any(u not in umap for u in uids) or any(a not in amap for a in aids):
            errors.append({'session_id':sid,'candidate':n,'problem':'消息ID缺失或无效'});continue
        quote=c.get('evidence_quote','')
        full='\n'.join([umap[u]['content'] for u in uids]+[amap[a]['content'] for a in aids])
        if not quote or compact(quote) not in compact(full):
            errors.append({'session_id':sid,'candidate':n,'problem':'引用不属于选定消息'});continue
        # Selected factual groups form a learning window, not a fabricated timeline.
        messages=[];seen={}
        for role,gs,ids in [('user',s['user_requests'],set(uids)),('assistant',s['assistant_contents'],set(aids))]:
            for g in gs:
                if g['group_id'] not in ids or (sid,g['group_id']) in noiseids:continue
                rec=group_record(g,role);key=(role,re.sub(r'\s+',' ',rec['content']).strip())
                if key in seen:
                    old=messages[seen[key]];old['group_ids']+=rec['group_ids'];old['source_refs']+=rec['source_refs'];repeat_group_merges+=1
                else:seen[key]=len(messages);messages.append(rec)
                (kept_u if role=='user' else kept_a).add((sid,g['group_id']))
        if compact(redact(quote)) not in compact('\n'.join(m['content'] for m in messages)):
            errors.append({'session_id':sid,'candidate':n,'problem':'引用仅存在于被清除噪声或包装中'});continue
        obj={'candidate_id':f'{sid}:learn{n:02d}','session_id':sid,'owner_id':s['owner_id'],
             'task':redact(c['task']),'learning_candidate':redact(c['lesson']),
             'evidence_quote':redact(quote),'limitations':c.get('limitations',[]),
             'qualification':'AI筛选的学习候选，未认证为完整黄金轨迹或有效技能',
             'outcome':'未做独立业务结果判定','chronology_verified':False,
             'presentation':'分别呈现用户和AI正文；顺序不代表完整原始时序',
             'source_user_ids':uids,'source_assistant_ids':aids,'messages':messages,
             'accepted_associations':[{'assistant_id':a,'user_ids':sorted(links.get(a,set()))} for a in aids],
             'tool_evidence_scope':'会话级有限导出记录，非该片段完整执行日志',
             'session_tool_records':tools.get(sid,[]),'review_basis':label.get('review_basis','card')}
        candidates.append(obj);out.append(obj)
    sessionrows.append({'session_id':sid,'decision':decision,'topic':cats[sid]['primary'],
                        'reason_code':label.get('reason_code',''), 'reason':redact(label['reason']),
                        'candidate_count':len(out),'tasks':[x['task'] for x in out],
                        'user_count':len(umap),'ai_count':len(amap),'review_basis':label.get('review_basis','card'),
                        'candidate_ids':[x['candidate_id'] for x in out]})
dump(P/'validation_errors.json',errors)
if errors:
    sys.stdout.reconfigure(encoding='utf-8');print(json.dumps({'errors':len(errors),'examples':errors[:8]},ensure_ascii=False));sys.exit(2)

dump(P/'screening_decisions.json',[labelmap[s] for s in source])
dump(P/'screened_sessions.json',sessionrows)
(P/'selected_session_ids.txt').write_text(''.join(x['session_id']+'\n' for x in sessionrows if x['decision']=='KEEP'),encoding='utf-8')
(P/'learning_candidates.jsonl').write_text(''.join(json.dumps(c,ensure_ascii=False)+'\n' for c in candidates),encoding='utf-8')
with (P/'session_screening.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['会话编号','本轮处理','原主主题','保留候选片段数','筛选理由','原用户组数','原AI组数','审阅方式'])
    for row in sessionrows:writer.writerow([row['session_id'],{'KEEP':'保留','HOLD':'暂存','EXCLUDE':'排除'}[row['decision']],row['topic'],row['candidate_count'],row['reason'],row['user_count'],row['ai_count'],row['review_basis']])
for c in candidates:
    lines=[f"# {c['candidate_id']}：{c['task']}",'',f"会话：{c['session_id']}",'',f"本轮可学习：{c['learning_candidate']}",'',f"原文依据：{c['evidence_quote']}",'',
           '这是待验证学习片段，不能直接当完整成功轨迹。未重新执行工具，附件与产物字节未补。正文按角色分组，不能据此证明原始时间顺序。','',
           '边界：'+'；'.join(c['limitations'] or ['任务效果尚未独立验证']),'']
    for m in c['messages']:
        lines += ['## '+('用户需求／反馈' if m['role']=='user' else 'AI处理／结果'),'',
                  '来源消息组：'+', '.join(m['group_ids']),'',m['content'],'']
    (candidate_root/(c['candidate_id'].replace(':','_')+'.md')).write_text('\n'.join(lines),encoding='utf-8')

# Superseded draft fragments remain recoverable outside the active pool.
expected_texts={c['candidate_id'].replace(':','_')+'.md' for c in candidates}
archive_root=P/'superseded_candidate_texts'
for old in candidate_root.glob('*.md'):
    if old.name in expected_texts or not re.fullmatch(r'conv_[a-f0-9]{12}_learn\d{2}\.md',old.name):continue
    archive_root.mkdir(exist_ok=True)
    target=archive_root/(old.stem+'.'+sha(old)[:12]+'.md')
    n=1
    while target.exists():
        target=archive_root/(old.stem+'.'+sha(old)[:12]+f'.{n}.md');n+=1
    assert old.resolve().parent==candidate_root.resolve() and target.resolve().parent==archive_root.resolve()
    old.rename(target)

counts=Counter(x['decision'] for x in sessionrows);bytopic=defaultdict(Counter);reasons=Counter()
for row in sessionrows:bytopic[row['topic']][row['decision']]+=1;reasons[(row['decision'],row['reason_code'])]+=1
summary={'total_sessions':len(source),'kept_sessions':counts['KEEP'],'held_sessions':counts['HOLD'],'excluded_sessions':counts['EXCLUDE'],
         'learning_candidate_fragments':len(candidates),'selected_unique_user_groups':len(kept_u),'selected_unique_ai_groups':len(kept_a),
         'new_high_precision_ai_noise_groups':len(noise),'original_ai_groups':prep['ai_groups'],
         'unselected_ai_groups_not_automatically_noise':prep['ai_groups']-len(noise)-len(kept_a),
         'repeated_selected_clean_groups_merged_within_windows':repeat_group_merges,
         'review_basis_counts':dict(Counter(x['review_basis'] for x in sessionrows)),
         'topic_counts':{k:dict(v) for k,v in bytopic.items()},
         'reason_counts':[{'decision':k[0],'code':k[1],'sessions':v} for k,v in reasons.most_common()],
         'original_hashes_unchanged':True,'source_sha256':sha(SOURCE),'annotations_sha256':sha(ANN),
         'semantic_gold_labels':False,'generated_skills':0,'task_success_evaluated':False}
dump(R/'screening_summary.json',summary)

# Make the short-reply boundary audit readable; preserve diagnostic context.
noise_overrides=json.loads((P/'noise_semantic_overrides.json').read_text(encoding='utf-8')) if (P/'noise_semantic_overrides.json').exists() else []
protected={(x['session_id'],x['assistant_id']):x for x in noise_overrides}
before=json.loads((P/'noise_before_boundary_review.json').read_text(encoding='utf-8')) if (P/'noise_before_boundary_review.json').exists() else noise
noise_audit=[]
for x in before:
    sid,aid=x['session_id'],x['assistant_id']
    g=next(a for a in source[sid]['assistant_contents'] if a['group_id']==aid)
    saved=(sid,aid) not in noiseids
    noise_audit.append({'session_id':sid,'assistant_id':aid,'decision':'保留上下文' if saved else '移出纯进度／控制文本',
                        'reason':protected.get((sid,aid),{}).get('reason',x['reason']),
                        'content':redact(g['content']),'task_membership_certified':False})
dump(P/'short_ai_boundary_review.json',noise_audit)
audit_body=''.join('<section><h3>'+html.escape(x['session_id'])+' · '+x['decision']+'</h3><p>'+html.escape(x['reason'])+'</p><pre>'+html.escape(x['content'])+'</pre><a href="../../matched_066/private/index.html#'+html.escape(x['session_id'])+'">查看原会话</a></section>' for x in noise_audit)
(P/'noise_review.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>短AI回复边界复核</title><style>body{max-width:1100px;margin:30px auto;padding:20px;font:16px/1.7 system-ui;background:#f4f7fa}section{background:white;padding:18px;margin:14px 0;border-radius:10px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit}</style><h1>短AI回复：清理与保护</h1><p>短句和未来式句法不能单独证明无学习价值；诊断、修订条件与方法上下文保留。保护不等于技能或任务成功认证。</p>'+audit_body+'</html>',encoding='utf-8')

cards=[];cmap=defaultdict(list)
for c in candidates:cmap[c['session_id']].append(c)
e=lambda v:html.escape(str(v))
for row in sessionrows:
    sid=row['session_id'];s=source[sid]
    text='\n'.join(clean_user(u['content']) for u in s['user_requests'])
    details=''
    for c in cmap[sid]:
        msgs=''.join(f'<h4>{"用户需求／反馈" if m["role"]=="user" else "AI处理／结果"}</h4><small>{e(", ".join(m["group_ids"]))}</small><pre>{e(m["content"])}</pre>' for m in c['messages'])
        file=c['candidate_id'].replace(':','_')+'.md'
        details+=f'<details><summary>{e(c["task"])}</summary><p><b>可以学习：</b>{e(c["learning_candidate"])}</p><p><b>原文依据：</b>{e(c["evidence_quote"])}</p><p><b>边界：</b>{e("；".join(c["limitations"]))}</p><a href="candidate_texts/{e(file)}">完整文字片段</a>{msgs}</details>'
    cards.append(f'<article data-state="{row["decision"]}" data-topic="{e(row["topic"])}"><h3>{e(sid)} · {e({"KEEP":"保留","HOLD":"暂存","EXCLUDE":"排除"}[row["decision"]])}</h3><p>{e(row["reason"])}<br><small>原主题 {e(row["topic"])} · 候选 {row["candidate_count"]} · {e(row["review_basis"])}</small></p><details><summary>用户任务概览</summary><pre>{e(redact(text[:1500]))}{"（概览截断，请回原会话查看）" if len(text)>1500 else ""}</pre></details>{details}<a href="../../matched_066/private/index.html#{e(sid)}">回到完整会话</a></article>')
page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>SkillsLoop 企业学习候选精筛</title><style>
body{max-width:1200px;margin:36px auto;padding:0 24px;background:#f4f7fa;color:#233443;font:16px/1.7 system-ui}h1{font-size:29px}article{background:white;margin:15px 0;padding:18px;border:1px solid #dce3e9;border-radius:12px}input,select{font:inherit;padding:9px;border:1px solid #c4cfda;border-radius:7px;margin:5px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:inherit;background:#f5f7fa;padding:12px}details{padding:8px 0}summary{cursor:pointer;color:#125e80}small{color:#627280}a{color:#125e80}header{position:sticky;top:0;background:#f4f7fa;padding:12px 0;border-bottom:1px solid #ccd7e1}#n{padding:10px}h4{margin-bottom:4px}
</style><h1>企业会话：技能学习候选筛选</h1><p>保留的是有正文依据的学习片段，未认证为完整成功轨迹或有效技能。会话缺少独立 AI 时间；页面按角色呈现正文。原始数据及 071 标注没有修改。</p>'''
page+=f'<p><b>1,466 会话 → 保留 {counts["KEEP"]} · 暂存 {counts["HOLD"]} · 排除 {counts["EXCLUDE"]}；{len(candidates)} 个候选学习片段</b></p><p><a href="noise_review.html">查看短AI清理与保护：{len(noise)}条移出，{len(noise_overrides)}条保护</a></p>'
page+='''<header><input id="q" placeholder="搜索会话编号／任务／理由"><select id="state"><option value="">全部处理</option><option value="KEEP">保留候选</option><option value="HOLD">证据不足暂存</option><option value="EXCLUDE">排除</option></select><span id="n"></span></header>'''+''.join(cards)+'''
<script>const rows=[...document.querySelectorAll('article')];function filter(){const q=document.querySelector('#q').value.toLowerCase(),s=document.querySelector('#state').value;let n=0;for(const r of rows){const ok=(!s||r.dataset.state===s)&&(!q||r.textContent.toLowerCase().includes(q));r.hidden=!ok;if(ok)n++}document.querySelector('#n').textContent='当前 '+n+' 条会话'}document.querySelector('#q').oninput=filter;document.querySelector('#state').onchange=filter;filter()</script></html>'''
(P/'index.html').write_text(page,encoding='utf-8')
manifest={'date':'2026-10-06','input':prep,'summary':summary,'decision_hashes':{f'shard_{i}':sha(P/f'shard_{i}/review_labels.json') for i in range(1,4)},
          'boundary_overlay_sha256':sha(op) if op.exists() else None,
          'noise_semantic_overrides_sha256':sha(P/'noise_semantic_overrides.json') if (P/'noise_semantic_overrides.json').exists() else None,
          'processing_scripts':{p.name:sha(p) for p in [R/'prepare_review.py',R/'expand_review.py',R/'audit_labels.py',R/'export_screening.py',R/'verify_outputs.py']},
          'output_files':{str(p.relative_to(R)):sha(p) for p in [P/'screening_decisions.json',P/'screened_sessions.json',P/'learning_candidates.jsonl',P/'selected_session_ids.txt',P/'session_screening.csv',P/'index.html',P/'noise_review.html',P/'short_ai_boundary_review.json',R/'screening_summary.json',*sorted(candidate_root.glob('*.md'))]},
          'validation':{'coverage_1466':True,'message_ids_valid':True,'quotes_in_selected_source':True,'source_and_annotation_hashes_unchanged':True}}
dump(R/'screening_manifest.json',manifest)
sys.stdout.reconfigure(encoding='utf-8');print(json.dumps({k:v for k,v in summary.items() if k in ['total_sessions','kept_sessions','held_sessions','excluded_sessions','learning_candidate_fragments','selected_unique_user_groups','selected_unique_ai_groups','new_high_precision_ai_noise_groups']},ensure_ascii=False))
