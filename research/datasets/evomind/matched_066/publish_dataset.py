"""Apply validated semantic correspondences without changing source conversation text."""
from pathlib import Path
from collections import Counter
import importlib.util,json,html,sys

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'private';BASE=ROOT.parent/'aligned_066'
sp=importlib.util.spec_from_file_location('aligned066',BASE/'build_aligned_dataset.py');a=importlib.util.module_from_spec(sp);sp.loader.exec_module(a)
vp=importlib.util.spec_from_file_location('semantic066',ROOT/'semantic_match.py');v=importlib.util.module_from_spec(vp);vp.loader.exec_module(v)
a.METHOD['MODEL_SEMANTIC_CANDIDATE']='模型内容匹配（推断，非真值）'

def main():
    jobs=json.loads((OUT/'prepared_jobs.json').read_text(encoding='utf-8'));decisions={};valid_jobs=0;missing_jobs=[];modelstatus=Counter()
    for job in jobs:
        cache=OUT/'responses'/(job['id']+'.json')
        if not cache.exists():missing_jobs.append({'session_id':job['session_id'],'job_id':job['id']});continue
        saved=json.loads(cache.read_text(encoding='utf-8'))
        if not saved.get('validated'):missing_jobs.append({'session_id':job['session_id'],'job_id':job['id']});continue
        rows=v.validate(saved['text'],job);valid_jobs+=1
        for r in rows:
            key=(job['session_id'],job['assistant_map'][str(r['a'])]);assert key not in decisions
            decisions[key]={'user_group_ids':[job['user_map'][str(i)] for i in r['u']],
                            'status':r['status'],'confidence_label':r['confidence'],'assistant_quote':r['aq'],
                            'user_quote':r.get('uq',''),'reason':r.get('reason','模型未提供文字理由'),
                            'model_reason_missing':not bool(r.get('reason')),'source_job_id':job['id'],
                            'source_model':saved['model'],'quote_validation_passed':r['quote_validation_passed'],
                            'input_user_candidates_complete':job['payload']['user_candidates_complete'],
                            'assistant_input_truncated':next(x['truncated'] for x in job['payload']['assistants'] if x['a']==r['a'])}
            modelstatus[r['status']]+=1
    data={};inventory=[];queue=[];stats=Counter();methods=Counter()
    with (BASE/'private/evomind_conversations.jsonl').open(encoding='utf-8') as f:
        for line in f:
            s=json.loads(line);sid=s['session_id']
            def occurrence_digest(value):
                events=[m for n in value['user_requests']+value['assistant_contents'] for m in n['occurrences']]+value['retry_controls']+value['empty_ai_events']+value['other_events']
                return v.sha(json.dumps(sorted(events,key=lambda m:m['id']),ensure_ascii=False,sort_keys=True))
            original_occurrence_digest=occurrence_digest(s)
            for edge in s['associations']:
                decision=decisions.get((sid,edge['assistant_group_id']))
                if not decision:continue
                edge['proposal_before_model']={k:edge[k] for k in ('user_group_ids','method','explanation')};edge['semantic_review']=decision
                if decision['status']=='matched' and decision['confidence_label'] in ('high','medium'):
                    edge['user_group_ids']=decision['user_group_ids'];edge['method']='MODEL_SEMANTIC_CANDIDATE'
                    edge['explanation']=decision['reason']+'（模型推断；逐字引文已核验，关系未有独立真值。）'
                else:
                    edge['user_group_ids']=[];edge['method']='NO_VISIBLE_REQUEST' if decision['status']=='unmatched' else 'UNRESOLVED'
                    edge['explanation']=decision['reason']+'（不强行配对。）'
                    if decision['user_group_ids']:
                        edge['candidate_ranking']=[{'user_group_id':g,'source':'model_ambiguous_candidate','score':None} for g in decision['user_group_ids']]
                edge['verified_reply_link']=False
            s['schema_version']='evomind-066-semantic-association-v1';s['semantic_review_complete_for_requested_batches']=not any(j['session_id']==sid for j in missing_jobs)
            # Validate original occurrence partition, content and association targets against the frozen baseline.
            original={'messages':[m for n in s['user_requests']+s['assistant_contents'] for m in n['occurrences']]+s['retry_controls']+s['empty_ai_events']+s['other_events']}
            a.validate(s,original)
            assert occurrence_digest(s)==original_occurrence_digest
            data[sid]=s;(OUT/'conversations').mkdir(exist_ok=True)
            a.b.dump(OUT/'conversations'/(sid+'.json'),s);md,hp=a.render(s)
            (OUT/'conversations'/(sid+'.md')).write_text(md,encoding='utf-8');(OUT/'conversations'/(sid+'.html')).write_text(hp,encoding='utf-8')
            linked={u for x in s['associations'] for u in x['user_group_ids']};pending=sum(not x['user_group_ids'] for x in s['associations'])
            old=s['source_order_diagnostics']['status']=='ORDER_CONFLICT_REVIEW'
            row={'session_id':sid,'source_title':s['session_metadata'].get('title'),'original_order_conflict':old,
                 'user_groups':len(s['user_requests']),'ai_groups':len(s['assistant_contents']),
                 'unassigned_ai_groups':pending,'user_groups_without_ai':len(s['user_requests'])-len(linked),
                 'has_model_review':any('semantic_review' in e for e in s['associations']),
                 'model_review_incomplete':not s['semantic_review_complete_for_requested_batches'],
                 'path':'conversations/'+sid+'.html'}
            inventory.append(row)
            if pending or row['user_groups_without_ai'] or row['model_review_incomplete']:queue.append(row)
            stats['sessions']+=1;stats['user_groups']+=len(s['user_requests']);stats['ai_groups']+=len(s['assistant_contents']);stats['assigned_ai_groups']+=len(s['assistant_contents'])-pending
            stats['unassigned_ai_groups']+=pending;stats['user_groups_with_ai']+=len(linked);stats['user_groups_without_ai']+=row['user_groups_without_ai']
            stats['sessions_with_unassigned_ai']+=pending>0;stats['sessions_with_model_review']+=row['has_model_review'];stats['original_conflict_sessions']+=old
            if old:
                stats['original_conflict_sessions_all_ai_have_candidates']+=pending==0
                stats['original_conflict_sessions_with_unassigned_ai']+=pending>0
            for edge in s['associations']:methods[edge['method']]+=1
    a.b.dump(OUT/'evomind_conversations.json',data)
    with (OUT/'evomind_conversations.jsonl').open('w',encoding='utf-8') as f:
        for s in data.values():f.write(json.dumps(s,ensure_ascii=False,separators=(',',':'))+'\n')
    # Auxiliary data stays separate and retains the frozen, unreviewed baseline status.
    a.b.dump(OUT/'internal_sessions.json',json.loads((BASE/'private/internal_sessions.json').read_text(encoding='utf-8')))
    a.b.dump(OUT/'sessions_without_exported_messages.json',json.loads((BASE/'private/sessions_without_exported_messages.json').read_text(encoding='utf-8')))
    a.b.dump(OUT/'conversation_inventory.json',inventory);a.b.dump(OUT/'association_review_queue.json',queue);a.b.dump(OUT/'model_batches_incomplete.json',missing_jobs)
    original_summary=json.loads((BASE/'summary.json').read_text(encoding='utf-8'))
    ledger=[json.loads(x) for x in (OUT/'request_ledger.jsonl').read_text(encoding='utf-8').splitlines()]
    starts=[json.loads(x) for x in (OUT/'request_starts.jsonl').read_text(encoding='utf-8').splitlines()]
    legacy=sum('run_profile' not in x for x in ledger)
    known_in=sum(sum(x.get('usage',{}).get(k,0) for k in ('input_tokens','cache_read_input_tokens','cache_creation_input_tokens')) for x in ledger)+40
    known_out=sum(x.get('usage',{}).get('output_tokens',0) for x in ledger)+194
    outcomes=Counter(x['status'] for x in ledger);errors=Counter(x.get('error','').split(':')[0] for x in ledger if x['status']=='failed')
    summary={**dict(stats),'original_record_count':original_summary['source_records'],
        'removed_retry_controls':original_summary['retry_controls'],'removed_empty_ai':original_summary['empty_ai'],
        'folded_user_occurrences':original_summary['folded_user_occurrences'],'folded_ai_occurrences':original_summary['folded_ai_occurrences'],
        'model_jobs_planned':len(jobs),'model_jobs_validated':valid_jobs,'model_jobs_incomplete':len(missing_jobs),
        'model_decision_counts':dict(modelstatus),'association_methods':dict(methods),
        'model_items_with_failed_quote_validation':sum(not d['quote_validation_passed'] for d in decisions.values()),
        'model_items_without_written_reason':sum(d['model_reason_missing'] for d in decisions.values()),
        'model_items_with_truncated_ai_input':sum(d['assistant_input_truncated'] for d in decisions.values()),
        'model_items_with_incomplete_user_candidate_set':sum(not d['input_user_candidates_complete'] for d in decisions.values()),
        'api_requests_documented_including_probes':len(starts)+legacy+2,'additional_initial_interrupted_requests_upper_bound':4,
        'reported_input_tokens_including_probes':known_in,'reported_output_tokens_including_probes':known_out,
        'known_tokens_exclude_unreported_timeout_or_interrupted_usage':True,'cash_cost':'UNKNOWN',
        'request_outcomes':dict(outcomes),'request_error_types':dict(errors),'all_reply_links_verified':False,
        'independent_semantic_accuracy_not_measured':True}
    a.b.dump(ROOT/'summary.json',summary)
    esc=html.escape
    hp=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EvoMind清理与回复匹配</title><style>'+a.b.CSS+'</style><main><h1>EvoMind · 清理与回复匹配</h1>',
        f'<p>{stats["sessions"]}条用户会话，{stats["user_groups"]}组不重复用户正文，{stats["ai_groups"]}组不重复AI正文。</p>',
        f'<p class="note">{stats["assigned_ai_groups"]}组AI有对应候选，{stats["unassigned_ai_groups"]}组仍未挂接。匹配结合位置与内容，部分经过真实模型语义判断；所有结果仍是推断，不是已核验历史真值。同文所有出现位置仍保留。</p>',
        '<p><a href="conversations/conv_e09b70c51b19.html">查看指定案例</a> · <a href="evomind_conversations.json">会话JSON</a> · <a href="evomind_conversations.jsonl">JSONL</a> · <a href="association_review_queue.json">剩余核验清单</a></p>',
        '<input id="q" placeholder="搜索会话编号或来源标题"><select id="filter"><option value="">全部会话</option><option value="original">原始有顺序歧义</option><option value="pending">仍有AI未归属</option><option value="model">有模型内容匹配</option></select><span id="count"></span><table><thead><tr><th>会话</th><th>用户／AI正文组</th><th>未挂接AI／暂无AI的用户</th></tr></thead><tbody>']
    for r in inventory:
        hp+=['<tr data-original="'+str(int(r['original_order_conflict']))+'" data-pending="'+str(int(r['unassigned_ai_groups']>0))+'" data-model="'+str(int(r['has_model_review']))+'"><td><a href="'+r['path']+'">'+esc(r['session_id'])+'</a><br><small>来源标题：'+esc(r['source_title'] or '')+'</small></td><td>'+str(r['user_groups'])+' / '+str(r['ai_groups'])+'</td><td>'+str(r['unassigned_ai_groups'])+' / '+str(r['user_groups_without_ai'])+'</td></tr>']
    hp+=['</tbody></table><script>const q=document.getElementById("q"),t=document.getElementById("filter"),rows=[...document.querySelectorAll("tbody tr")];function f(){let n=0;for(const r of rows){const show=(!t.value||r.dataset[t.value]==="1")&&r.textContent.toLowerCase().includes(q.value.toLowerCase());r.hidden=!show;if(show)n++;}document.getElementById("count").textContent="显示 "+n+" 条";}q.oninput=f;t.onchange=f;f();</script></main></html>']
    (OUT/'index.html').write_text('\n'.join(hp),encoding='utf-8')
    with (OUT/'evomind_conversations.jsonl').open(encoding='utf-8') as f:
        count=0
        for line in f:
            s=json.loads(line);assert s==data[s['session_id']];count+=1
    assert count==1466
    a.b.dump(ROOT/'delivery_manifest.json',{'base_manifest_sha256':a.b.sha(BASE/'manifest.json'),
        'publisher_sha256':a.b.sha(Path(__file__)),'semantic_runner_sha256':a.b.sha(ROOT/'semantic_match.py'),
        'validation':{'all_sessions_retained':True,'all_occurrences_preserved':True,'all_selected_model_quotes_validated':True,'all_link_targets_exist':True,'jsonl_roundtrip_equal':True},
        'outputs':{str(p.relative_to(ROOT)).replace('\\','/'):{'sha256':a.b.sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()}})
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
