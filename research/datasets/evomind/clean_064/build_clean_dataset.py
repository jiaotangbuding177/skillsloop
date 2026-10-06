"""Reversible local cleaning of 063: empty AI bodies and bounded exact resends."""
from pathlib import Path
from collections import Counter
from datetime import datetime
import importlib.util
import json
import html
import sys

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'full_063'
OUT=ROOT/'private'
WINDOW_SECONDS=120
spec=importlib.util.spec_from_file_location('evomind063',BASE/'build_dataset.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def attachments(m):
    payload=m['raw_record'].get('rawPayload')
    return payload.get('files') if isinstance(payload,dict) else None

def delta(a,c):
    x,y=a.get('user_created_at'),c.get('user_created_at')
    if not x or not y:return None
    return (datetime.fromisoformat(y)-datetime.fromisoformat(x)).total_seconds()

def clean(s):
    original=s['messages'];removed=[];candidates=[]
    nonempty=[]
    for m in original:
        if m['role']=='assistant' and not m['content'].strip():
            removed.append({'session_id':s['session_id'],'reason':'EMPTY_AI_BODY',
                            'retained_message_id':None,'removed_message':m,
                            'payload_preserved_in_audit':bool(m['raw_record'].get('rawPayload'))})
        else:nonempty.append(m)
    # A candidate numeric order must not contradict the absence of an AI response.
    ais=[m for m in nonempty if m['role']=='assistant' and m['numeric_id'] is not None]
    kept=[];anchor=None
    for m in nonempty:
        collapse=False
        if m['role']=='user' and m['content'].strip() and anchor and m['content']==anchor['content']:
            seconds=delta(anchor,m)
            same_files=attachments(anchor)==attachments(m)
            intervening_numeric_ai=[]
            comparable=anchor['numeric_id'] is not None and m['numeric_id'] is not None and anchor['numeric_scheme']==m['numeric_scheme']
            if comparable:
                low,high=sorted([anchor['numeric_id'],m['numeric_id']])
                intervening_numeric_ai=[a['id'] for a in ais if a['numeric_scheme']==m['numeric_scheme'] and low<a['numeric_id']<high]
            collapse=seconds is not None and 0<=seconds<=WINDOW_SECONDS and same_files and not intervening_numeric_ai
            candidate={'session_id':s['session_id'],'first_id':anchor['id'],'repeat_id':m['id'],
                       'seconds_from_first':seconds,'attachment_metadata_equal':same_files,
                       'numeric_comparison_available':comparable,'intervening_numeric_ai_ids':intervening_numeric_ai,
                       'action':'COLLAPSED_SUSPECTED_RESEND' if collapse else 'KEPT_INSUFFICIENT_OR_CONTRADICTING_EVIDENCE'}
            candidates.append(candidate)
            if collapse:
                anchor.setdefault('collapsed_duplicate_ids',[]).append(m['id'])
                removed.append({'session_id':s['session_id'],'reason':'EXACT_SHORT_WINDOW_RESEND',
                                'retained_message_id':anchor['id'],'evidence':candidate,'removed_message':m})
        if not collapse:
            kept.append(m)
            anchor=m if m['role']=='user' else None
    before=s['order_diagnostics'];after=b.diagnostics(kept)
    s['schema_version']='evomind-064-clean-v1'
    s['source_dataset']='evomind-063-v1'
    s['original_counts']=s['counts'];s['messages']=kept
    roles=Counter(m['role'] for m in kept)
    s['counts']={'records':len(kept),'user':roles['user'],'assistant':roles['assistant'],'other':len(kept)-roles['user']-roles['assistant']}
    s['source_order_diagnostics']=before;s['order_diagnostics']=after
    s['cleaning']={'window_seconds':WINDOW_SECONDS,'empty_ai_removed':sum(x['reason']=='EMPTY_AI_BODY' for x in removed),
                   'exact_user_resends_collapsed':sum(x['reason']=='EXACT_SHORT_WINDOW_RESEND' for x in removed),
                   'removed_message_ids':[x['removed_message']['id'] for x in removed],
                   'stall_cause_verified':False,'source_conflict_flag_retained':before['status']=='ORDER_CONFLICT_REVIEW',
                   'events_after_cleaning':len(kept),'all_user_sessions_retained':True}
    s['objective_flags']['automatic_deduplication_performed']=s['cleaning']['exact_user_resends_collapsed']>0
    vs={'source_order':b.view(kept,'SOURCE_ORDER_AFTER_REVERSIBLE_CLEANING_UNVERIFIED')}
    if kept and all(m['numeric_id'] is not None for m in kept) and len({m['numeric_scheme'] for m in kept})==1:
        vs['numeric_id_candidate']=b.view(sorted(kept,key=lambda m:m['numeric_id']),'NUMERIC_ID_HYPOTHESIS_UNVERIFIED')
    s['views']=vs
    original_ids={m['id'] for m in original};keep_ids={m['id'] for m in kept};remove_ids={x['removed_message']['id'] for x in removed}
    assert not keep_ids&remove_ids and keep_ids|remove_ids==original_ids
    original_map={m['id']:m for m in original}
    for m in kept:assert m['content']==original_map[m['id']]['content']
    for v in vs.values():
        ids=[i for t in v['turns'] for k in ('user_message_ids','assistant_message_ids') for i in t[k]]+v['side_event_ids']
        assert Counter(ids)==Counter(keep_ids)
    assert not any(m['role']=='assistant' and not m['content'].strip() for m in kept)
    return s,removed,candidates

def main():
    source_paths=[BASE/'private/evomind_conversations.jsonl',BASE/'private/internal_sessions.json',BASE/'private/sessions_without_exported_messages.json',BASE/'build_dataset.py']
    hashes={str(p):b.sha(p) for p in source_paths}
    OUT.mkdir(parents=True,exist_ok=True)
    datasets={'user_conversation':{},'internal_session':{}};inventory=[];removed_all=[];candidate_all=[]
    # Streaming source avoids loading the large duplicated JSON representation.
    with source_paths[0].open(encoding='utf-8') as f:
        source=[json.loads(line) for line in f]
    source+=list(json.loads(source_paths[1].read_text(encoding='utf-8')).values())
    for s in source:
        s,removed,candidates=clean(s);sid=s['session_id'];scope=s['scope']
        datasets[scope][sid]=s;removed_all.extend(removed);candidate_all.extend(candidates)
        folder='conversations' if scope=='user_conversation' else 'internal_sessions'
        (OUT/folder).mkdir(exist_ok=True)
        md,hp=b.render(s)
        note=f'清理版：移除空AI正文{s["cleaning"]["empty_ai_removed"]}条，合并疑似短时完全重发{s["cleaning"]["exact_user_resends_collapsed"]}条。保留原文及原始顺序冲突标记，未证明卡顿成因或修复全部回复归属。'
        raw_link='../../../full_063/private/'+folder+'/'+sid+'.md'
        md=md.replace('原导出顺序（完整记录）','清理后保留顺序').replace('条原始记录：','条保留记录：')
        md=md.replace('\n', '\n\n'+note+'\n\n[清理前完整原文]('+raw_link+')\n',1)
        hp=hp.replace('原导出顺序（完整记录）','清理后保留顺序').replace('条原始记录','条保留记录')
        hp=hp.replace('</h1>','</h1><p class="note">'+html.escape(note)+'</p><a href="'+raw_link+'">清理前完整原文</a>',1)
        (OUT/folder/(sid+'.md')).write_text(md,encoding='utf-8')
        (OUT/folder/(sid+'.html')).write_text(hp,encoding='utf-8')
        inventory.append({'session_id':sid,'title':s['session_metadata'].get('title'),'scope':scope,
                          'before_records':s['original_counts']['records'],'after_records':s['counts']['records'],
                          'source_conflict':s['source_order_diagnostics']['status']=='ORDER_CONFLICT_REVIEW',
                          'remaining_conflict':s['order_diagnostics']['status']=='ORDER_CONFLICT_REVIEW',
                          **s['cleaning'],'html_path':folder+'/'+sid+'.html'})
    mainset=datasets['user_conversation'];internal=datasets['internal_session']
    b.dump(OUT/'evomind_conversations.json',mainset)
    with (OUT/'evomind_conversations.jsonl').open('w',encoding='utf-8') as f:
        for s in mainset.values():f.write(json.dumps(s,ensure_ascii=False,separators=(',',':'))+'\n')
    b.dump(OUT/'internal_sessions.json',internal)
    b.dump(OUT/'sessions_without_exported_messages.json',json.loads(source_paths[2].read_text(encoding='utf-8')))
    b.dump(OUT/'conversation_inventory.json',inventory)
    b.dump(OUT/'repeat_candidates.json',candidate_all)
    with (OUT/'removed_records.jsonl').open('w',encoding='utf-8') as f:
        for r in removed_all:f.write(json.dumps(r,ensure_ascii=False,separators=(',',':'))+'\n')
    main_removed=[r for r in removed_all if r['session_id'] in mainset]
    main_inventory=[r for r in inventory if r['scope']=='user_conversation']
    counts=Counter(r['reason'] for r in main_removed)
    remaining=[r for r in main_inventory if r['remaining_conflict']]
    disappeared=[r for r in main_inventory if r['source_conflict'] and not r['remaining_conflict']]
    new=[r for r in main_inventory if r['remaining_conflict'] and not r['source_conflict']]
    b.dump(OUT/'order_review_sessions.json',remaining)
    b.dump(OUT/'conflict_signal_disappeared_sessions.json',disappeared)
    summary={'sessions_before':len(mainset),'sessions_after':len(mainset),
             'records_before':sum(s['original_counts']['records'] for s in mainset.values()),
             'records_after':sum(s['counts']['records'] for s in mainset.values()),
             'removed_empty_ai':counts['EMPTY_AI_BODY'],'collapsed_exact_user_resends':counts['EXACT_SHORT_WINDOW_RESEND'],
             'sessions_with_empty_ai_removed':sum(s['cleaning']['empty_ai_removed']>0 for s in mainset.values()),
             'sessions_with_user_resends_collapsed':sum(s['cleaning']['exact_user_resends_collapsed']>0 for s in mainset.values()),
             'order_conflicts_before':sum(r['source_conflict'] for r in main_inventory),'order_conflicts_after':len(remaining),
             'conflict_signal_disappeared':len(disappeared),'new_conflict_signal':len(new),
             'remaining_reason_sessions':{k:sum(bool(s['order_diagnostics']['reasons'][k]) for s in mainset.values()) for k in b.LABELS},
             'removed_empty_ai_with_payload_preserved_in_audit':sum(r['reason']=='EMPTY_AI_BODY' and r['payload_preserved_in_audit'] for r in main_removed),
             'main_roles_after':dict(Counter(m['role'] for s in mainset.values() for m in s['messages'])),
             'internal_sessions':len(internal),'internal_removed_records':len(removed_all)-len(main_removed),
             'unchanged_sessions_without_exported_messages':39,'window_seconds':WINDOW_SECONDS,'llm_calls':0,
             'lag_causation_verified':False,'chronology_repair_claimed':False}
    assert summary['records_before']-summary['records_after']==sum(counts.values())
    # Attribute disappearing diagnostics separately to empty-body filtering and resend collapse.
    ablation=Counter()
    for s in mainset.values():
        removed=[r['removed_message'] for r in main_removed if r['session_id']==s['session_id']]
        reconstructed=sorted(s['messages']+removed,key=lambda m:m['source_line'])
        empty_only=[m for m in reconstructed if not(m['role']=='assistant' and not m['content'].strip())]
        ablation['conflicts_after_only_empty_ai_removal']+=b.diagnostics(empty_only)['status']=='ORDER_CONFLICT_REVIEW'
    summary.update(ablation)
    with (OUT/'evomind_conversations.jsonl').open(encoding='utf-8') as f:
        reloaded=[json.loads(line) for line in f]
    assert {s['session_id']:s for s in reloaded}==mainset
    for r in inventory:assert (OUT/r['html_path']).exists()
    assert hashes=={str(p):b.sha(p) for p in source_paths}
    b.dump(ROOT/'summary.json',summary)
    esc=html.escape
    hp=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EvoMind清理版</title><style>'+b.CSS+'</style><main><h1>EvoMind · 清理版</h1>',
        f'<p>{len(mainset)}条用户会话；移除空AI {counts["EMPTY_AI_BODY"]}条，合并疑似完全重发{counts["EXACT_SHORT_WINDOW_RESEND"]}条。</p>',
        f'<p class="note">原顺序冲突{summary["order_conflicts_before"]}条，清理后仍检测到{len(remaining)}条。冲突信号消失不代表时序已恢复，原标记保留。非完全相同文字不合并；原文和删除记录均可追溯。</p>',
        '<p><a href="evomind_conversations.json">会话JSON</a> · <a href="evomind_conversations.jsonl">JSONL</a> · <a href="removed_records.jsonl">移除记录及依据</a> · <a href="order_review_sessions.json">剩余冲突清单</a></p>',
        '<input id="q" placeholder="搜索会话编号／标题"><select id="scope"><option value="user_conversation">用户会话</option><option value="internal_session">内部用途附表</option></select><select id="status"><option value="">全部</option><option value="remaining">清理后仍有顺序冲突</option><option value="source">清理前有顺序冲突</option><option value="changed">本轮有清理记录</option></select><span id="n"></span><table><thead><tr><th>会话</th><th>记录数前→后</th><th>移除空AI／重发</th><th>顺序冲突前→后</th></tr></thead><tbody>']
    for r in inventory:
        hp+=['<tr data-scope="'+r['scope']+'" data-remaining="'+str(int(r['remaining_conflict']))+'" data-source="'+str(int(r['source_conflict']))+'" data-changed="'+str(int(r['before_records']!=r['after_records']))+'"><td><a href="'+r['html_path']+'">'+esc(r['session_id'])+'</a><br>'+esc(r['title'] or '')+'</td><td>'+str(r['before_records'])+' → '+str(r['after_records'])+'</td><td>'+str(r['empty_ai_removed'])+' / '+str(r['exact_user_resends_collapsed'])+'</td><td>'+('有' if r['source_conflict'] else '未检出')+' → '+('有' if r['remaining_conflict'] else '未检出')+'</td></tr>']
    hp+=['</tbody></table><script>const q=document.getElementById("q"),s=document.getElementById("scope"),t=document.getElementById("status"),rows=[...document.querySelectorAll("tbody tr")];function f(){let n=0;for(const r of rows){let show=r.dataset.scope===s.value&&(!t.value||r.dataset[t.value]==="1")&&r.textContent.toLowerCase().includes(q.value.toLowerCase());r.hidden=!show;if(show)n++;}document.getElementById("n").textContent="显示 "+n+" 条";}q.oninput=f;s.onchange=f;t.onchange=f;f();</script></main></html>']
    (OUT/'index.html').write_text('\n'.join(hp),encoding='utf-8')
    b.dump(ROOT/'manifest.json',{'sources_sha256':hashes,'script_sha256':b.sha(Path(__file__)),
        'summary':summary,'validation':{'source_files_unchanged':True,'all_records_partitioned_into_retained_or_removed':True,
        'retained_content_unchanged':True,'all_sessions_retained':True,'no_empty_ai_in_clean_messages':True,
        'all_turn_views_cover_retained_messages':True,'jsonl_roundtrip_equal':True},
        'outputs':{str(p.relative_to(ROOT)).replace('\\','/'):{'sha256':b.sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()}})
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
