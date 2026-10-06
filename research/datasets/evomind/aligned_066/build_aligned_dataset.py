"""Lossless content deduplication and evidence-scored reply candidates. Offline, no LLM calls.

This reconstructs a reviewable correspondence view, not an authenticated event timeline.
"""
from pathlib import Path
from collections import Counter,defaultdict
import bisect,hashlib,html,importlib.util,json,math,re,sys

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'private'; BASE=ROOT.parent/'full_063'
sp=importlib.util.spec_from_file_location('base063',BASE/'build_dataset.py');b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b)
RETRY='Continue where you left off. The previous model attempt failed or timed out.'
PREFIX='请使用中文回复，除非用户明确使用其他语言。'
STOP={'帮我','一下','请问','可以','这个','一个','需要','进行','什么','如何','好的','谢谢','继续','使用','提供','根据','内容','相关','分析','所有','请使','用中','文回','回复','除非','用户','明确','其他','语言','希望','完成','the','and','this','that','with','for','you','your','please','from','have','will','let','can'}
METHOD={'SOURCE_POSITION_CANDIDATE':'按原位置初配（未独立核验）','POSITION_AGREEMENT_CANDIDATE':'两种位置线索一致（推断）',
        'CONTENT_POSITION_CANDIDATE':'词面内容与位置综合匹配（推断）','REVIEWED_CASE_INFERENCE':'本轮逐条阅读校对（仍为推断）',
        'UNRESOLVED':'归属未确定','NO_VISIBLE_REQUEST':'未找到对应的用户输入'}

def norm(t):return t.replace('\r\n','\n').strip()
def core(t):
    t=norm(t)
    return t[len(PREFIX):].strip() if t.startswith(PREFIX) else t
def is_retry(t):return core(t)==RETRY
def digest(t):return hashlib.sha256(t.encode('utf-8')).hexdigest()
def files(m):
    p=m['raw_record'].get('rawPayload');v=p.get('files') if isinstance(p,dict) else None
    return json.dumps(v or [],ensure_ascii=False,sort_keys=True)
def features(t):
    t=core(t).lower()[:14000];out=set()
    for run in re.findall(r'[\u4e00-\u9fff]+',t):
        for n in (2,3):out.update(run[i:i+n] for i in range(len(run)-n+1))
    out.update(re.findall(r'[a-z][a-z0-9_.-]{2,}|\d{3,}',t))
    return out-STOP

def grouped(ms):
    nodes={'user':{},'assistant':{}};controls=[];empty=[];side=[];loc={}
    for m in ms:
        if is_retry(m['content']):controls.append(m);continue
        if m['role']=='assistant' and not norm(m['content']):empty.append(m);continue
        if m['role'] not in nodes:side.append(m);continue
        key=norm(m['content'])+('\nATTACHMENTS:'+files(m) if m['role']=='user' else '')
        gid=('u_' if m['role']=='user' else 'a_')+digest(key)[:18]
        node=nodes[m['role']].setdefault(gid,{'group_id':gid,'role':m['role'],'content':m['content'],'occurrences':[]})
        # Full occurrence records preserve context, status, payload and exact original whitespace.
        node['occurrences'].append(m);loc[m['id']]=gid
    return list(nodes['user'].values()),list(nodes['assistant'].values()),controls,empty,side,loc

def position_votes(ms,loc):
    raw={};numeric={};current=None
    for m in ms:
        if m['id'] not in loc:continue
        if m['role']=='user':current=loc[m['id']]
        elif m['role']=='assistant':raw[m['id']]=current
    schemes=defaultdict(list)
    for m in ms:
        if m['id'] in loc and m['numeric_id'] is not None:schemes[m['numeric_scheme']].append(m)
    for events in schemes.values():
        current=None
        for m in sorted(events,key=lambda x:x['numeric_id']):
            if m['role']=='user':current=loc[m['id']]
            elif m['role']=='assistant':numeric[m['id']]=current
    return raw,numeric

def align(s):
    us,ais,controls,empty,side,loc=grouped(s['messages']);um={u['group_id']:u for u in us}
    raw,num=position_votes(s['messages'],loc);conflict=s['order_diagnostics']['status']=='ORDER_CONFLICT_REVIEW'
    uf={u['group_id']:features(u['content']) for u in us};df=Counter(t for ts in uf.values() for t in ts)
    weights={t:1+math.log((len(us)+1)/(n+1)) for t,n in df.items()}
    totals={g:sum(weights[t] for t in ts) for g,ts in uf.items()}
    results=[]
    for a in ais:
        av=features(a['content']);rv=Counter(raw.get(m['id']) for m in a['occurrences'] if raw.get(m['id']));nv=Counter(num.get(m['id']) for m in a['occurrences'] if num.get(m['id']))
        evidence=[{'assistant_message_id':m['id'],'raw_preceding_user_group':raw.get(m['id']),
                   'numeric_preceding_user_group':num.get(m['id'])} for m in a['occurrences']]
        ranked=[]
        for uid,u in um.items():
            overlap=uf[uid]&av;lex=sum(weights[t] for t in overlap)/max(1,totals[uid]);r=rv[uid]/max(1,sum(rv.values()));n=nv[uid]/max(1,sum(nv.values()))
            score=.70*lex+.20*n+.10*r
            ranked.append({'user_group_id':uid,'score':round(score,6),'lexical_coverage':round(lex,6),'raw_position_share':round(r,6),
                           'numeric_position_share':round(n,6),'shared_features':sorted(overlap,key=lambda t:(-weights[t],-len(t),t))[:12]})
        ranked.sort(key=lambda x:(-x['score'],x['user_group_id']))
        chosen=[];method='UNRESOLVED';note='位置或内容证据不足，未强行配对。'
        if not us:method='NO_VISIBLE_REQUEST'
        elif not conflict:
            chosen=sorted(rv);method='SOURCE_POSITION_CANDIDATE' if chosen else 'NO_VISIBLE_REQUEST'
            note='未检出原始编号冲突，保留原位置的对应候选；不等于真实回复关系已验证。'
        else:
            top=ranked[0];second=ranked[1]['score'] if len(ranked)>1 else 0
            uid=top['user_group_id']
            content_clear=top['lexical_coverage']>=.28 and top['score']-second>=.075 and len(top['shared_features'])>=3
            anchored=bool(top['raw_position_share'] or top['numeric_position_share'])
            agreement=top['raw_position_share']>=.8 and top['numeric_position_share']>=.8
            if content_clear and anchored:
                chosen=[uid];method='CONTENT_POSITION_CANDIDATE';note='会话内词面线索有区分度，并有原位置或数字位置支持；不是模型语义验真。'
            elif agreement:
                chosen=[uid];method='POSITION_AGREEMENT_CANDIDATE';note='原位置与数字位置多数一致，作为待复核候选；缺少可靠时间线。'
            elif not rv and not nv:method='NO_VISIBLE_REQUEST';note='该AI内容在两个可用序列中均无可见前置用户输入。'
        results.append({'assistant_group_id':a['group_id'],'user_group_ids':chosen,'method':method,'explanation':note,
                        'candidate_ranking':ranked[:3],'occurrence_position_evidence':evidence,
                        'confidence_probability':None,'verified_reply_link':False})
    return {'schema_version':'evomind-066-association-v1','session_id':s['session_id'],'scope':s['scope'],
            'owner_id':s['owner_id'],'session_metadata':s['session_metadata'],'dated_session_metadata':s['dated_session_metadata'],
            'original_counts':s['counts'],'source_order_diagnostics':s['order_diagnostics'],
            'user_requests':us,'assistant_contents':ais,'associations':results,
            'retry_controls':controls,'empty_ai_events':empty,'other_events':side,
            'source_order_ids':[m['id'] for m in s['messages']],
            'deduplication_scope':'same_session_equal_trimmed_body_user_attachment_sensitive',
            'title_used_for_matching':False,'complete_chronology_verified':False}

def apply_review(s,overrides):
    if s['session_id'] not in overrides:return
    loc={m['id']:n['group_id'] for n in s['user_requests']+s['assistant_contents'] for m in n['occurrences']}
    byaid={x['assistant_group_id']:x for x in s['associations']}
    for entry in overrides[s['session_id']]:
        aid=loc[entry['assistant_representative_id']];target=byaid[aid]
        target['automatic_proposal_before_review']={k:target[k] for k in ('user_group_ids','method','explanation')}
        target['user_group_ids']=[loc[i] for i in entry['user_message_ids']]
        target['method']='REVIEWED_CASE_INFERENCE' if entry['user_message_ids'] else entry['unassigned_method']
        target['explanation']=entry['reason'];target['reviewer']='assistant_reading_source_not_independent_human_gold'

def render(s):
    esc=html.escape;sid=s['session_id'];us=s['user_requests'];ais={a['group_id']:a for a in s['assistant_contents']}
    assoc={a['assistant_group_id']:a for a in s['associations']};used=set();links=defaultdict(list)
    for a in s['associations']:
        for u in a['user_group_ids']:links[u].append(a['assistant_group_id'])
    hint='清理版按用户输入展示对应AI候选，一条输入可有多条回复。相同正文只展示一次，全部出现位置保留。候选对应不是已验证的真实时间线。'
    md=['# '+sid+'：用户输入与AI回复','',hint,'',
        '原始标题仅作元数据，不参与匹配：'+str(s['session_metadata'].get('title','')),'',
        f'原始{s["original_counts"]["records"]}条记录；{len(us)}组不重复用户正文、{len(ais)}组不重复AI正文、{len(s["retry_controls"])}条重试控制。','']
    hp=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(sid)+'</title><style>'+b.CSS+'</style><main><a href="../index.html">返回总目录</a><h1>用户输入与AI回复</h1><p class="meta">'+esc(sid)+'</p><p class="note">'+hint+'</p><details><summary>原始标题（不作为任务或匹配依据）</summary>'+esc(str(s['session_metadata'].get('title','')))+'</details>']
    def show_ai(aid):
        a=ais[aid];link=assoc[aid];label=METHOD[link['method']];positions='；'.join(m['id']+' / 原第'+str(m['source_line'])+'行' for m in a['occurrences'])
        if aid in used:
            md.extend(['相同AI正文已在其他输入处展示：'+aid+'（共享正文不等于同一次执行）。',''])
            hp.append('<p><a href="#'+aid+'">查看已展示的同一AI正文</a>（保留独立出现位置，不重复铺开）</p>');return
        used.add(aid)
        md.extend(['#### AI · '+label,'依据：'+link['explanation'],'出现'+str(len(a['occurrences']))+'次：'+positions,b.fence(a['content']),''])
        hp.extend(['<div class="message" id="'+aid+'"><strong>AI · '+label+'</strong><p class="meta">'+esc(link['explanation'])+'</p><details><summary>全部'+str(len(a['occurrences']))+'次出现位置</summary><p class="meta">'+esc(positions)+'</p></details><pre>'+esc(a['content'])+'</pre></div>'])
    for i,u in enumerate(us,1):
        uid=u['group_id'];positions='；'.join(m['id'] for m in u['occurrences'])
        md.extend(['## 用户输入 '+str(i),'同文出现'+str(len(u['occurrences']))+'次：'+positions,b.fence(u['content']),''])
        hp.extend(['<section id="'+uid+'"><h2>用户输入 '+str(i)+'</h2><div class="message user"><p class="meta">'+esc(positions)+'</p><pre>'+esc(u['content'])+'</pre></div>'])
        if not links[uid]:
            md.extend(['**目前没有足够证据挂接AI回复；不是判定系统没有回复。**',''])
            hp.append('<p class="note">目前没有足够证据挂接AI回复；不是判定系统没有回复。</p>')
        for aid in links[uid]:show_ai(aid)
        hp.append('</section>')
    md.extend(['## 未确定归属的AI回复',''])
    hp.append('<h2>未确定归属的AI回复</h2>')
    for aid,a in ais.items():
        if not assoc[aid]['user_group_ids']:
            show_ai(aid)
            candidates=assoc[aid]['candidate_ranking']
            if candidates:
                names={u['group_id']:i for i,u in enumerate(us,1)}
                label='供核验的候选：'+ '、'.join('用户输入'+str(names[x['user_group_id']]) for x in candidates)
                md.extend([label,'']);hp.append('<p class="meta">'+label+'</p>')
    md.extend(['## 隔离与来源','重试控制'+str(len(s['retry_controls']))+'条、空AI '+str(len(s['empty_ai_events']))+'条，完整保存在本会话JSON中，不作为用户任务和有效答复。',
               '[本会话结构化数据]('+sid+'.json)','[063原始完整会话](../../../full_063/private/'+('conversations' if s['scope']=='user_conversation' else 'internal_sessions')+'/'+sid+'.md)'])
    hp.extend(['<details><summary>清理与来源</summary><p>重试控制'+str(len(s['retry_controls']))+'条，空AI '+str(len(s['empty_ai_events']))+'条。原记录及每个同文出现位置完整保留。</p><a href="'+sid+'.json">本会话结构化数据</a></details></main></html>'])
    assert used==set(ais)
    return '\n\n'.join(md),'\n'.join(hp)

def validate(s,original):
    nodes=s['user_requests']+s['assistant_contents'];occ=[m for n in nodes for m in n['occurrences']]+s['retry_controls']+s['empty_ai_events']+s['other_events']
    assert Counter(m['id'] for m in occ)==Counter(m['id'] for m in original['messages'])
    orig={m['id']:m for m in original['messages']}
    for m in occ:assert m==orig[m['id']]
    for n in nodes:assert all(norm(m['content'])==norm(n['content']) for m in n['occurrences'])
    assert not any(is_retry(n['content']) for n in nodes)
    for n in s['assistant_contents']:assert norm(n['content'])
    uid={u['group_id'] for u in s['user_requests']};aid={a['group_id'] for a in s['assistant_contents']}
    assert Counter(x['assistant_group_id'] for x in s['associations'])==Counter(aid)
    for x in s['associations']:assert set(x['user_group_ids'])<=uid

def main():
    paths=[BASE/'private/evomind_conversations.jsonl',BASE/'private/internal_sessions.json',BASE/'private/sessions_without_exported_messages.json',ROOT/'case_review_overrides.json',BASE/'build_dataset.py']
    hashes={str(p):b.sha(p) for p in paths};overrides=json.loads(paths[3].read_text(encoding='utf-8'))
    OUT.mkdir(parents=True,exist_ok=True)
    data={};internal={};inventory=[];summary=Counter();methods=Counter();unresolved=[]
    with paths[0].open(encoding='utf-8') as f:source=[json.loads(line) for line in f]
    source+=list(json.loads(paths[1].read_text(encoding='utf-8')).values())
    for original in source:
        s=align(original);apply_review(s,overrides);validate(s,original)
        sid=s['session_id'];is_main=s['scope']=='user_conversation';target=data if is_main else internal;target[sid]=s
        folder='conversations' if is_main else 'internal_sessions';(OUT/folder).mkdir(exist_ok=True)
        b.dump(OUT/folder/(sid+'.json'),s);md,hp=render(s)
        (OUT/folder/(sid+'.md')).write_text(md,encoding='utf-8');(OUT/folder/(sid+'.html')).write_text(hp,encoding='utf-8')
        linked={u for a in s['associations'] for u in a['user_group_ids']};pending=sum(not a['user_group_ids'] for a in s['associations'])
        row={'session_id':sid,'scope':s['scope'],'original_title':s['session_metadata'].get('title'),
             'source_order_conflict':s['source_order_diagnostics']['status']=='ORDER_CONFLICT_REVIEW',
             'user_groups':len(s['user_requests']),'assistant_groups':len(s['assistant_contents']),
             'pending_ai_groups':pending,'user_groups_without_assigned_ai':len(s['user_requests'])-len(linked),
             'retry_controls':len(s['retry_controls']),'empty_ai':len(s['empty_ai_events']),
             'html_path':folder+'/'+sid+'.html'}
        inventory.append(row)
        if is_main:
            summary['sessions']+=1;summary['source_records']+=s['original_counts']['records'];summary['retry_controls']+=len(s['retry_controls']);summary['empty_ai']+=len(s['empty_ai_events'])
            summary['user_groups']+=len(s['user_requests']);summary['assistant_groups']+=len(s['assistant_contents'])
            summary['folded_user_occurrences']+=sum(len(u['occurrences'])-1 for u in s['user_requests'])
            summary['folded_ai_occurrences']+=sum(len(a['occurrences'])-1 for a in s['assistant_contents'])
            summary['other_events']+=len(s['other_events']);summary['assistant_groups_with_candidate_link']+=len(s['assistant_contents'])-pending
            summary['assistant_groups_unassigned']+=pending;summary['user_groups_with_candidate_ai']+=len(linked)
            summary['user_groups_without_candidate_ai']+=len(s['user_requests'])-len(linked)
            summary['sessions_with_unassigned_ai']+=pending>0
            summary['sessions_with_no_nonretry_user']+=not s['user_requests']
            for a in s['associations']:methods[a['method']]+=1
            if row['source_order_conflict']:
                summary['original_conflict_sessions_processed']+=1
                summary['original_conflict_sessions_with_unassigned_ai']+=pending>0
                summary['original_conflict_sessions_all_ai_have_candidates']+=pending==0
            if pending or row['user_groups_without_assigned_ai']:unresolved.append(row)
    b.dump(OUT/'evomind_conversations.json',data)
    with (OUT/'evomind_conversations.jsonl').open('w',encoding='utf-8') as f:
        for s in data.values():f.write(json.dumps(s,ensure_ascii=False,separators=(',',':'))+'\n')
    b.dump(OUT/'internal_sessions.json',internal);b.dump(OUT/'sessions_without_exported_messages.json',json.loads(paths[2].read_text(encoding='utf-8')))
    b.dump(OUT/'conversation_inventory.json',inventory);b.dump(OUT/'association_review_queue.json',unresolved)
    with (OUT/'evomind_conversations.jsonl').open(encoding='utf-8') as f:
        count=0
        for line in f:
            s=json.loads(line);assert s==data[s['session_id']];count+=1
    assert count==len(data) and hashes=={str(p):b.sha(p) for p in paths}
    summary=dict(summary);summary['association_methods']=dict(methods);summary['llm_calls']=0;summary['all_reply_links_verified']=False
    summary['internal_sessions']=len(internal);summary['metadata_only_sessions']=39
    b.dump(ROOT/'summary.json',summary)
    esc=html.escape
    hp=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EvoMind问答对应版</title><style>'+b.CSS+'</style><main><h1>EvoMind · 去重与问答对应版</h1>',
        f'<p>{len(data)}条用户会话；隔离{summary["retry_controls"]}条重试提示、{summary["empty_ai"]}条空AI；折叠用户同文{summary["folded_user_occurrences"]}次、AI同文{summary["folded_ai_occurrences"]}次。</p>',
        '<p class="note">按每组不重复用户输入查看一条或多条AI候选回复。同文的全部出现位置仍在；标题不参与匹配。配对是可核对的推断，无法归属的AI单列，不宣称恢复全部真实时序。内容分组不是独立任务计数。</p>',
        '<p><a href="conversations/conv_e09b70c51b19.html">查看你指定的案例</a> · <a href="evomind_conversations.json">JSON</a> · <a href="evomind_conversations.jsonl">JSONL</a> · <a href="association_review_queue.json">仍需核验的会话</a></p>',
        '<input id="q" placeholder="搜索会话编号或来源标题"><select id="scope"><option value="user_conversation">用户会话</option><option value="internal_session">内部用途</option></select><select id="filter"><option value="">全部</option><option value="conflict">原始顺序有歧义</option><option value="pending">有AI未挂接</option><option value="missing">有用户输入未匹配AI</option></select><span id="count"></span><table><thead><tr><th>会话</th><th>去重用户／AI</th><th>未挂接AI／无AI用户</th></tr></thead><tbody>']
    for r in inventory:
        hp+=['<tr data-scope="'+r['scope']+'" data-conflict="'+str(int(r['source_order_conflict']))+'" data-pending="'+str(int(r['pending_ai_groups']>0))+'" data-missing="'+str(int(r['user_groups_without_assigned_ai']>0))+'"><td><a href="'+r['html_path']+'">'+esc(r['session_id'])+'</a><br><small>来源标题：'+esc(r['original_title'] or '')+'</small></td><td>'+str(r['user_groups'])+' / '+str(r['assistant_groups'])+'</td><td>'+str(r['pending_ai_groups'])+' / '+str(r['user_groups_without_assigned_ai'])+'</td></tr>']
    hp+=['</tbody></table><script>const q=document.getElementById("q"),s=document.getElementById("scope"),t=document.getElementById("filter"),rows=[...document.querySelectorAll("tbody tr")];function f(){let n=0;for(const r of rows){const show=r.dataset.scope===s.value&&(!t.value||r.dataset[t.value]==="1")&&r.textContent.toLowerCase().includes(q.value.toLowerCase());r.hidden=!show;if(show)n++;}document.getElementById("count").textContent="显示 "+n+" 条";}q.oninput=f;s.onchange=f;t.onchange=f;f();</script></main></html>']
    (OUT/'index.html').write_text('\n'.join(hp),encoding='utf-8')
    b.dump(ROOT/'manifest.json',{'source_hashes':hashes,'script_sha256':b.sha(Path(__file__)),
        'validation':{'source_unchanged':True,'all_original_events_accounted_for':True,'all_occurrences_exactly_preserved':True,
                      'all_association_targets_exist':True,'all_ai_bodies_displayed_once_per_session':True,'jsonl_roundtrip_equal':True},
        'outputs':{str(p.relative_to(ROOT)).replace('\\','/'):{'sha256':b.sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()}})
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
