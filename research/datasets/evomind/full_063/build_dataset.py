"""Local lossless assembly and deterministic order diagnostics; no network or LLM."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import html
import json
import re
import sys

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'private'
RAW = Path('C:/Users/39835/Downloads/zkys-raw-export-20260925')
MINING = Path('C:/Users/39835/Downloads/zkys-skill-mining-20260925')
SOURCES = {'messages': RAW/'zclaw_messages.jsonl', 'sessions': RAW/'zclaw_sessions.jsonl',
           'members': RAW/'zclaw_members.jsonl', 'dated_users': MINING/'user_messages.json',
           'dated_sessions': MINING/'sessions.json'}
LABELS = {'source_numeric_descent': '原文件顺序与数字编号不一致',
          'source_user_time_descent': '原文件中用户时间倒退',
          'time_numeric_conflict': '用户时间与数字编号方向冲突'}
CSS = '''body{margin:0;background:#f3f5f8;color:#203047;font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1150px;margin:auto;padding:28px}h1{font-size:28px}a{color:#245abb}table{border-collapse:collapse;width:100%;background:white}td,th{padding:10px;border-bottom:1px solid #dde3ec;text-align:left}td{overflow-wrap:anywhere}.note{background:#fff1cd;padding:16px;border-radius:10px}.meta{font-size:13px;color:#627189}section,details{background:white;padding:15px;margin:18px 0;border-radius:10px}summary{cursor:pointer;font-weight:bold}.message{padding:14px;border-left:4px solid #9aaaba;background:#f4f6f8;margin:12px 0}.user{border-color:#477cd4;background:#eaf2ff}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.8 system-ui,"Microsoft YaHei",sans-serif}input,select{padding:9px;margin:8px 8px 16px 0;max-width:90%}.bad{color:#a54217}'''

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def read_lines(p):
    with p.open(encoding='utf-8-sig') as f:
        return [(i,json.loads(x)) for i,x in enumerate(f,1) if x.strip()]

def dump(p,x):
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def number(sid,mid):
    if not mid.startswith(sid+':'): return None
    suffix=mid[len(sid)+1:]
    m=re.fullmatch(r'msg_(\d+)',suffix)
    if m:return ('msg_N',int(m[1]))
    if re.fullmatch(r'\d+',suffix):return ('numeric_suffix',int(suffix))
    return None

def view(ms,basis):
    turns=[]; current=None; side=[]
    for m in ms:
        role=m['role']
        if role not in ('user','assistant'):
            side.append(m['id']);continue
        if current is None or (role=='user' and current['assistant_message_ids']):
            current={'turn_index':len(turns)+1,'user_message_ids':[], 'assistant_message_ids':[],
                     'pairing_status':'DISPLAY_ONLY_NOT_VERIFIED_REPLY_TO'}
            turns.append(current)
        current['user_message_ids' if role=='user' else 'assistant_message_ids'].append(m['id'])
    return {'ordering_basis':basis,'chronology_verified':False,'ordered_message_ids':[m['id'] for m in ms],
            'turns':turns,'side_event_ids':side}

def diagnostics(ms):
    reasons={k:[] for k in LABELS};ties=[]
    numbered=defaultdict(list)
    for m in ms:
        if m['numeric_id'] is not None: numbered[m['numeric_scheme']].append(m)
    def pair(a,b):return {'before_id':a['id'],'after_id':b['id'],
                         'before_source_line':a['source_line'],'after_source_line':b['source_line'],
                         'before_user_time':a['user_created_at'],'after_user_time':b['user_created_at']}
    for group in numbered.values():
        for a,b in zip(group,group[1:]):
            if a['numeric_id']>b['numeric_id']:reasons['source_numeric_descent'].append(pair(a,b))
        us=sorted([m for m in group if m['role']=='user' and m['user_created_at']],
                  key=lambda m:(m['user_created_at'],m['dated_source_position']))
        for a,b in zip(us,us[1:]):
            if a['numeric_id']>b['numeric_id']:
                (ties if a['user_created_at']==b['user_created_at'] else reasons['time_numeric_conflict']).append(pair(a,b))
    us=[m for m in ms if m['role']=='user' and m['user_created_at']]
    for a,b in zip(us,us[1:]):
        if a['user_created_at']>b['user_created_at']:reasons['source_user_time_descent'].append(pair(a,b))
    trusted=sum(m['copy_kind']=='trusted' for m in ms)
    return {'status':'ORDER_CONFLICT_REVIEW' if any(reasons.values()) else 'NO_CONFLICT_OBSERVED_UNVERIFIED',
            'reasons':reasons,'same_time_numeric_descents':ties,
            'mixed_client_trusted_records':bool(trusted and trusted<len(ms)),
            'consecutive_user_pairs':sum(a['role']==b['role']=='user' for a,b in zip(ms,ms[1:])),
            'complete_chronology_verified':False}

def fence(text):
    f='`'*(max([len(x) for x in re.findall(r'`+',text)]+[3])+1)
    return f+'text\n'+text+'\n'+f+'\n'

def render(s):
    esc=html.escape;sid=s['session_id'];d=s['order_diagnostics'];c=s['counts']
    state='顺序冲突，待核验' if d['status']=='ORDER_CONFLICT_REVIEW' else '未发现规则可见冲突；顺序未独立核验'
    notes=[LABELS[k] for k,v in d['reasons'].items() if v]
    if d['mixed_client_trusted_records']:notes.append('客户端与平台副本并存，未擅自去重')
    notes.append('回合仅为展示分组；连续用户发言不单独判为混乱或缺回复。')
    title=s['session_metadata'].get('title') or sid
    md=[f'# {sid}\n',f'原始标题：{title}\n',f'共{c["records"]}条原始记录：用户{c["user"]}、AI {c["assistant"]}、系统／其他{c["other"]}。\n',f'**{state}**\n',*['- '+n+'\n' for n in notes],
        '\n正文保持导出原样；编号、状态及来源行可回查。未核验回复归属和任务边界。\n']
    hp=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
        '<title>'+esc(sid)+'</title><style>'+CSS+'</style><main><a href="../index.html">返回会话目录</a>',
        '<h1>'+esc(str(title))+'</h1><p class="meta">'+esc(sid)+f' · {c["records"]}条原始记录</p>',
        '<p class="note">'+esc(state)+'<br>'+esc('；'.join(notes))+'</p>']
    byid={m['id']:m for m in s['messages']}
    for vn,v in s['views'].items():
        vl='原导出顺序（完整记录）' if vn=='source_order' else '数字编号候选顺序（非确认时间线）'
        md+=['\n## '+vl+'\n']
        hp+=['<details'+(' open' if vn=='source_order' else '')+'><summary>'+vl+'</summary>']
        for t in v['turns']:
            md+=['\n### 展示回合 '+str(t['turn_index'])+'\n']
            hp+=['<section><h3>展示回合 '+str(t['turn_index'])+'</h3>']
            for role,key in [('用户','user_message_ids'),('AI','assistant_message_ids')]:
                for mid in t[key]:
                    m=byid[mid];meta=f'{mid} · 原文件第{m["source_line"]}行 · 状态{m["status"]} · '+(m['user_created_at'] or '无可用消息时间')
                    md+=['\n**'+role+'** · '+meta+'\n',fence(m['content'])]
                    hp+=['<div class="message '+('user' if role=='用户' else 'assistant')+'"><strong>'+role+'</strong><div class="meta">'+esc(meta)+'</div><pre>'+esc(m['content'])+'</pre></div>']
            hp+=['</section>']
        if v['side_event_ids']:
            md+=['\n### 系统及其他原始事件（位置见完整消息序列）\n'];hp+=['<h3>系统及其他原始事件</h3>']
            for mid in v['side_event_ids']:
                m=byid[mid];md+=['\n'+mid+'\n',fence(m['content'])];hp+=['<pre>'+esc(mid+'\n'+m['content'])+'</pre>']
        hp+=['</details>']
    hp+=['</main></html>']
    return '\n'.join(md),'\n'.join(hp)

def main():
    initial={k:sha(p) for k,p in SOURCES.items()}
    sessions=dict((r['id'],r) for _,r in read_lines(SOURCES['sessions']))
    members={r['userId'] for _,r in read_lines(SOURCES['members'])}
    dated_list=json.loads(SOURCES['dated_users'].read_text(encoding='utf-8-sig'))
    dated={r['id']:(i,r) for i,r in enumerate(dated_list)}
    ds={r['id']:r for r in json.loads(SOURCES['dated_sessions'].read_text(encoding='utf-8-sig'))}
    assert len(dated)==len(dated_list) and set(sessions)==set(ds)
    rows=read_lines(SOURCES['messages']);groups=defaultdict(list)
    assert len({r['id'] for _,r in rows})==len(rows)
    for line,r in rows:
        assert r['sessionId'] in sessions
        groups[r['sessionId']].append((line,r))
    for r in sessions.values():
        assert r['userId'] in members and ds[r['id']]['user_id']==r['userId']
    for _,r in rows:
        if r['id'] in dated:
            u=dated[r['id']][1];assert u['session_id']==r['sessionId'] and r['role']=='user'
    assert set(dated)<=set(r['id'] for _,r in rows)
    for folder in ['conversations','internal_sessions']:(OUT/folder).mkdir(parents=True,exist_ok=True)
    mainset={};internal={};empty={};inventory=[];text_differences=0
    for sid,session in sessions.items():
        assert re.fullmatch(r'[A-Za-z0-9_-]+',sid)
        if not groups[sid]:
            empty[sid]={'session_metadata':session,'dated_session_metadata':ds[sid],
                        'status':'NO_MESSAGES_IN_EXPORT_NOT_PROOF_ORIGINALLY_EMPTY'};continue
        ms=[]
        for line,r in groups[sid]:
            dp,u=dated.get(r['id'],(None,None));n=number(sid,r['id'])
            assert isinstance(r['content'],str)
            if u and u['content']!=r['content']:text_differences+=1
            ms.append({'id':r['id'],'role':r['role'],'content':r['content'],'status':r.get('status'),
                       'source_line':line,'source_file':'messages','copy_kind':'trusted' if r['id'].startswith(sid+':') else 'client_or_nontrusted',
                       'user_created_at':u.get('created_at') if u else None,'dated_source_position':dp,
                       'numeric_scheme':n[0] if n else None,'numeric_id':n[1] if n else None,
                       'raw_record':r,'matched_user_source_record':u})
        roles=Counter(m['role'] for m in ms);d=diagnostics(ms)
        vs={'source_order':view(ms,'RAW_JSONL_LINE_ORDER_UNVERIFIED')}
        if all(m['numeric_id'] is not None for m in ms) and len({m['numeric_scheme'] for m in ms})==1:
            vs['numeric_id_candidate']=view(sorted(ms,key=lambda m:m['numeric_id']),'NUMERIC_ID_HYPOTHESIS_UNVERIFIED')
        scope='user_conversation' if session.get('purpose')=='consumer' else 'internal_session'
        s={'schema_version':'evomind-063-v1','session_id':sid,'owner_id':session['userId'],
           'scope':scope,'session_metadata':session,'dated_session_metadata':ds[sid],
           'counts':{'records':len(ms),'user':roles['user'],'assistant':roles['assistant'],
                     'other':len(ms)-roles['user']-roles['assistant']},
           'order_diagnostics':d,'primary_view':'source_order','messages':ms,'views':vs,
           'objective_flags':{'attachment_binaries_available':False,'full_tool_history_available':False,
                             'automatic_deduplication_performed':False,'semantic_labels_added':False}}
        for v in vs.values():
            ids=v['ordered_message_ids'];assert len(ids)==len(ms) and set(ids)==set(m['id'] for m in ms)
            partition=[mid for t in v['turns'] for key in ('user_message_ids','assistant_message_ids') for mid in t[key]]+v['side_event_ids']
            assert Counter(partition)==Counter(ids)
        target=mainset if scope=='user_conversation' else internal;target[sid]=s
        folder='conversations' if scope=='user_conversation' else 'internal_sessions'
        md,hp=render(s)
        (OUT/folder/(sid+'.md')).write_text(md,encoding='utf-8')
        (OUT/folder/(sid+'.html')).write_text(hp,encoding='utf-8')
        inventory.append({'session_id':sid,'title':session.get('title'),'scope':scope,**s['counts'],
                          'order_status':d['status'],'reason_counts':{k:len(v) for k,v in d['reasons'].items()},
                          'same_time_numeric_descents':len(d['same_time_numeric_descents']),
                          'mixed_client_trusted_records':d['mixed_client_trusted_records'],
                          'html_path':folder+'/'+sid+'.html','markdown_path':folder+'/'+sid+'.md'})
    dump(OUT/'evomind_conversations.json',mainset)
    with (OUT/'evomind_conversations.jsonl').open('w',encoding='utf-8') as f:
        for s in mainset.values():f.write(json.dumps(s,ensure_ascii=False,separators=(',',':'))+'\n')
    dump(OUT/'internal_sessions.json',internal);dump(OUT/'sessions_without_exported_messages.json',empty)
    dump(OUT/'conversation_inventory.json',inventory)
    conflicts=[r for r in inventory if r['scope']=='user_conversation' and r['order_status']=='ORDER_CONFLICT_REVIEW']
    dump(OUT/'order_review_sessions.json',conflicts)
    summary={'all_session_metadata':len(sessions),'main_user_conversations':len(mainset),'internal_sessions':len(internal),
             'sessions_without_exported_messages':len(empty),'all_raw_message_records':len(rows),
             'main_raw_message_records':sum(s['counts']['records'] for s in mainset.values()),
             'main_roles':dict(Counter(m['role'] for s in mainset.values() for m in s['messages'])),
             'main_order_conflict_review_sessions':len(conflicts),'main_no_detected_conflict_unverified':len(mainset)-len(conflicts),
             'main_reason_sessions':{k:sum(bool(s['order_diagnostics']['reasons'][k]) for s in mainset.values()) for k in LABELS},
             'main_mixed_client_trusted_sessions':sum(s['order_diagnostics']['mixed_client_trusted_records'] for s in mainset.values()),
             'main_same_time_numeric_descent_sessions':sum(bool(s['order_diagnostics']['same_time_numeric_descents']) for s in mainset.values()),
             'main_status_counts':dict(Counter(m['status'] for s in mainset.values() for m in s['messages'])),
             'matched_user_dates':len(dated),'matched_user_content_differences':text_differences,
             'verified_complete_chronologies':0,'llm_calls':0}
    assert len(mainset)+len(internal)+len(empty)==len(sessions)
    assert sum(s['counts']['records'] for s in [*mainset.values(),*internal.values()])==len(rows)
    loaded=json.loads((OUT/'evomind_conversations.json').read_text(encoding='utf-8'));assert loaded==mainset
    with (OUT/'evomind_conversations.jsonl').open(encoding='utf-8') as f:
        lines=0
        for line in f:
            s=json.loads(line);assert s==mainset[s['session_id']];lines+=1
        assert lines==len(mainset)
    raw_lookup={r['id']:r for _,r in rows}
    for s in [*loaded.values(),*internal.values()]:
        for m in s['messages']:
            assert m['raw_record']==raw_lookup[m['id']] and m['content']==raw_lookup[m['id']]['content']
    assert initial=={k:sha(p) for k,p in SOURCES.items()}
    dump(ROOT/'summary.json',summary)
    esc=html.escape
    hp=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EvoMind真实会话数据集</title><style>'+CSS+'</style><main>',
        '<h1>EvoMind · 全量真实会话目录</h1>',
        f'<p>用户会话 <b>{len(mainset)}</b> 条 · 顺序冲突待核验 <b>{len(conflicts)}</b> 条 · 未发现规则可见冲突 <b>{len(mainset)-len(conflicts)}</b> 条</p>',
        '<p class="note">“待核验”表示原文件顺序、数字编号或用户时间存在冲突，不等于已确认真实聊天错乱。其余会话也未独立核验。完整原文均保留，副本未自动合并；连续用户发言不单独算冲突。</p>',
        '<p><a href="evomind_conversations.json">会话编号JSON</a> · <a href="evomind_conversations.jsonl">逐会话JSONL</a> · <a href="order_review_sessions.json">顺序冲突清单</a> · <a href="sessions_without_exported_messages.json">39条无导出消息元数据</a></p>',
        '<input id="q" placeholder="搜索会话编号或标题"><select id="scope"><option value="user_conversation">用户会话</option><option value="internal_session">内部用途附表</option><option value="">全部有正文会话</option></select><select id="status"><option value="">全部顺序状态</option><option value="ORDER_CONFLICT_REVIEW">顺序冲突待核验</option><option value="NO_CONFLICT_OBSERVED_UNVERIFIED">未发现规则可见冲突</option></select><span id="count"></span>',
        '<table><thead><tr><th>会话／标题</th><th>原始记录</th><th>顺序状态与说明</th></tr></thead><tbody>']
    for r in inventory:
        reasons=[LABELS[k] for k,v in r['reason_counts'].items() if v]
        if r['mixed_client_trusted_records']:reasons.append('两类副本并存')
        label='冲突待核验' if r['order_status']=='ORDER_CONFLICT_REVIEW' else '未发现冲突（未核验）'
        hp+=['<tr data-scope="'+r['scope']+'" data-status="'+r['order_status']+'"><td><a href="'+r['html_path']+'">'+esc(r['session_id'])+'</a><br>'+esc(r['title'] or '')+'</td><td>'+str(r['records'])+'<br><small>用户'+str(r['user'])+' / AI '+str(r['assistant'])+'</small></td><td>'+label+'<br><small>'+esc('；'.join(reasons))+'</small></td></tr>']
    hp+=['</tbody></table><script>const q=document.getElementById("q"),s=document.getElementById("scope"),t=document.getElementById("status"),rows=[...document.querySelectorAll("tbody tr")];function filter(){let n=0;for(const r of rows){let show=(!s.value||r.dataset.scope===s.value)&&(!t.value||r.dataset.status===t.value)&&r.textContent.toLowerCase().includes(q.value.toLowerCase());r.hidden=!show;if(show)n++;}document.getElementById("count").textContent="显示 "+n+" 条";}q.addEventListener("input",filter);s.addEventListener("change",filter);t.addEventListener("change",filter);filter();</script></main></html>']
    (OUT/'index.html').write_text('\n'.join(hp),encoding='utf-8')
    checklist=['# 顺序冲突待核验会话清单\n',f'主数据集{len(mainset)}条用户会话中，{len(conflicts)}条满足以下至少一项：原行序与数字编号冲突、原行序用户时间倒退、严格用户时间与编号方向冲突。各原因重叠，按会话去重。\n',
               '不把连续用户消息、同时间的编号下降或副本并存单独当作顺序冲突。不含模型语义判定，不代表全部真实混乱数。\n',
               '| 会话 | 原顺序／编号冲突对 | 原顺序／时间倒退对 | 时间／编号冲突对 |\n|---|---:|---:|---:|']
    for r in conflicts:
        checklist.append('| ['+r['session_id']+']('+r['markdown_path']+') | '+' | '.join(str(r['reason_counts'][k]) for k in LABELS)+' |')
    (OUT/'order_review_sessions.md').write_text('\n'.join(checklist)+'\n',encoding='utf-8')
    outputs={str(p.relative_to(ROOT)).replace('\\','/'):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()}
    dump(ROOT/'manifest.json',{'schema':'evomind-063-v1','sources':{k:{'path':str(p),'sha256':initial[k]} for k,p in SOURCES.items()},
                              'script_sha256':sha(Path(__file__)),'summary':summary,'outputs':outputs,
                              'validation':{'all_sessions_accounted_for':True,'all_raw_records_preserved':True,
                              'content_exactly_preserved':True,'view_partitions_complete':True,'json_jsonl_equal':True,'sources_unchanged':True}})
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
