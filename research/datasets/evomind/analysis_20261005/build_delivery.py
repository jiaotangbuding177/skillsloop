"""Validate independent AI semantic review rows and render data exploration.
No source mutations, no model/API calls, no task success inference.
"""
from pathlib import Path
from collections import Counter, defaultdict
import csv, hashlib, html, json, re, sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

R=Path(__file__).resolve().parent;P=R/'private';F=R/'figures';F.mkdir(exist_ok=True)
BASE=R.parent
AUDIT=BASE.parents[1]/'reviews/2026-10-05_evomind_full_audit'
def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def redact(t):
    t=re.sub(r'(?i)\bsk-[a-z0-9_-]{12,}', '[密钥已遮蔽]',t)
    t=re.sub(r'(?i)\bBearer\s+[a-z0-9._~+/-]{12,}', 'Bearer [已遮蔽]',t)
    t=re.sub(r'(?i)((?:api[_-]?key|access[_-]?token|secret|password|密码|授权码)[\s：:=]*["\']?)[^\s"\'`,;；]{8,}', r'\1[已遮蔽]',t)
    return t
def csvwrite(path,keys,rows):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=keys,extrasaction='ignore');w.writeheader();w.writerows(rows)

def main():
    categories=json.loads((R/'category_definitions.json').read_text(encoding='utf-8'))
    source=json.loads((P/'conversation_cluster_rows.json').read_text(encoding='utf-8'))
    sm={x['session_id']:x for x in source};labels=[]
    for i in (1,2,3):
        path=P/f'semantic_shard_{i}/combined_labels.json'
        labels.extend(json.loads(path.read_text(encoding='utf-8')))
    assert len(labels)==1466 and len({x['session_id'] for x in labels})==1466
    assert {x['session_id'] for x in labels}==set(sm)
    def validate_label(x):
        assert x['primary'] in categories
        assert x['confidence'] in ['high','medium','low']
        assert len(set(x['secondary']))==len(x['secondary'])
        assert x['primary'] not in x['secondary']
        assert all(z in categories for z in x['secondary'])
        assert (x['evidence_user'] or (not sm[x['session_id']]['user_groups'] and x['primary']=='UNCLEAR'))
        assert all(z in sm[x['session_id']]['user_groups'] for z in x['evidence_user'])
        assert x['review_basis'] in ['digest','expanded']
    for x in labels:validate_label(x)
    # Optional independent read-only reassessment; keep agent originals intact.
    overrides=json.loads((P/'semantic_review_overrides.json').read_text(encoding='utf-8')) if (P/'semantic_review_overrides.json').exists() else {}
    for x in labels:
        if x['session_id'] in overrides:
            x['initial_review']=dict(x)
            x.update(overrides[x['session_id']])
            validate_label(x)
    primary=Counter(x['primary'] for x in labels)
    coverage=Counter(k for x in labels for k in [x['primary']]+x['secondary'])
    confidence=Counter(x['confidence'] for x in labels)
    summary=[{'code':k,'category':categories[k],'primary_sessions':primary[k],'percent':round(100*primary[k]/1466,2),'all_relevant_sessions':coverage[k]} for k in sorted(categories,key=lambda k:-primary[k])]
    dump(P/'session_task_categories.json',labels)
    csvwrite(P/'session_task_categories.csv',['session_id','primary','secondary','confidence','evidence_user','reason','review_basis'],[{**x,'secondary':'|'.join(x['secondary']),'evidence_user':'|'.join(x['evidence_user'])} for x in labels])
    csvwrite(R/'task_distribution.csv',['category','primary_sessions','percent','all_relevant_sessions'],summary)
    dump(R/'task_distribution.json',summary)
    signatures=defaultdict(list)
    for row in source:
        key=hashlib.sha256('\n'.join(row['clean_user_texts']).encode()).hexdigest()
        signatures[key].append(row['session_id'])
    repeats=[ids for ids in signatures.values() if len(ids)>1]
    dump(P/'identical_clean_user_session_groups.json',repeats)
    # Existing source audit is explicitly a partial file inventory.
    inventory=json.loads((AUDIT/'inventory_stats.json').read_text(encoding='utf-8'))
    stats={'conversations':1466,'users':len({x['owner_id'] for x in source}),'user_groups':sum(x['user_group_count'] for x in source),'assistant_groups':sum(x['assistant_group_count'] for x in source),'primary_total':sum(primary.values()),'multi_category_sessions':sum(bool(x['secondary']) for x in labels),'confidence':dict(confidence),'review_basis':dict(Counter(x['review_basis'] for x in labels)),'identical_clean_user_text_session_groups':len(repeats),'sessions_in_identical_groups':sum(map(len,repeats)),'unique_clean_session_inputs':len(signatures),'counts_are':'session-level topic labels; not independent task instances or task success','classification_source':'AI semantic review of all session digests with selective expansion; automatic lexical clusters assist discovery only','external_model_API_calls':0,'semantic_accuracy_independently_measured':False,'inventory_source':str(AUDIT/'inventory_stats.json')}
    dump(R/'summary.json',stats)
    font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc')
    plt.rcParams['axes.unicode_minus']=False
    for field,name,title in [('primary_sessions','task_primary_bars','主任务主题：每条会话只计一次'),('all_relevant_sessions','task_coverage_bars','任务主题覆盖：同一会话可涉及多类')]:
        ss=sorted(summary,key=lambda x:x[field])
        fig,ax=plt.subplots(figsize=(13,8),dpi=170)
        colors=['#9ca3af' if x['code'] in ['UNCLEAR','PLATFORM'] else '#2764a0' for x in ss]
        bars=ax.barh([x['category'] for x in ss],[x[field] for x in ss],color=colors,height=.7)
        for tick in ax.get_yticklabels():tick.set_fontproperties(font);tick.set_fontsize(11)
        maxn=max(x[field] for x in ss)
        for bar,x in zip(bars,ss):ax.text(bar.get_width()+maxn*.012,bar.get_y()+bar.get_height()/2,str(x[field]),va='center',fontsize=11,color='#243447')
        ax.set_xlim(0,maxn*1.2);ax.grid(axis='x',alpha=.16);ax.set_axisbelow(True)
        for edge in ['top','right','left']:ax.spines[edge].set_visible(False)
        ax.spines['bottom'].set_color('#ced5df');ax.tick_params(axis='y',length=0)
        ax.set_title(title,fontproperties=font,fontsize=18,pad=22,loc='left',color='#172e49')
        ax.set_xlabel('涉及会话数',fontproperties=font,fontsize=11)
        note='范围：1,466 条企业成员名下历史会话。AI语义归类为探索标签；会话数不等于独立任务数。'
        if field=='all_relevant_sessions':note+=' 多类覆盖不相加当总会话数。'
        fig.text(.025,.025,note,fontproperties=font,fontsize=9,color='#5c6675')
        fig.tight_layout(rect=(.02,.065,.98,.97));fig.savefig(F/f'{name}.png');fig.savefig(F/f'{name}.svg');plt.close(fig)
    file_refs=json.loads((AUDIT/'private/file_metadata_references.json').read_text(encoding='utf-8'))
    csvwrite(P/'requested_file_references.csv',['session_id','user_id','role','group_id','message_id','source_line','file_name','file_path','mime_type','size_bytes','source','required_status'],[{**x,'user_id':x['owner_id'],'file_name':x['file'].get('name'),'file_path':x['file'].get('path'),'mime_type':x['file'].get('mimeType'),'size_bytes':x['file'].get('sizeBytes'),'source':x['file'].get('source'),'required_status':'REQUEST_BYTES_OR_EXPLICIT_NOT_FOUND'} for x in file_refs])
    # Provider target IDs freeze original scope without requerying current memberships.
    (P/'session_ids.txt').write_text('\n'.join(sm)+'\n',encoding='utf-8')
    csvwrite(P/'session_ids.csv',['session_id'],[{'session_id':sid} for sid in sm])
    ui=[]
    for x in labels:
        src=sm[x['session_id']]
        ui.append({'id':x['session_id'],'category':categories[x['primary']],'extra':[categories[k] for k in x['secondary']],'confidence':x['confidence'],'reason':x['reason'],'text':redact('\n'.join(src['clean_user_texts']))[:2000],'requests':src['user_group_count'],'local_cluster':src['local_cluster']})
    htmlprefix='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>EvoMind 全量任务分布与补数核查</title><style>body{background:#f4f7fb;color:#173047;font:16px "Microsoft YaHei",sans-serif;margin:0;padding:32px}main{max-width:1280px;margin:auto}.cards{display:flex;gap:18px}.card{background:white;border-radius:12px;padding:20px;flex:1}h1{font-size:28px}img{width:100%;background:white;border-radius:12px}input,select{padding:11px;border:1px solid #c5d2e0;border-radius:6px;margin:8px}table{width:100%;border-collapse:collapse;background:white}th,td{padding:12px;border-bottom:1px solid #e5ecf4;vertical-align:top}summary{cursor:pointer}.muted{color:#667788;font-size:13px}pre{white-space:pre-wrap;font:14px "Microsoft YaHei";max-height:400px;overflow:auto}.reason{max-width:260px}a{color:#2764a0}</style><main><h1>EvoMind 全量任务主题分布与补数核查</h1><p>按真实用户输入的可见目标归类，支持查看每条会话的归类依据和原文。企业成员来源不等于每段都属于企业业务；分类是探索标签。</p><div class="cards"><div class="card">全部会话<br><b>1,466</b></div><div class="card">去重用户输入<br><b>8,202</b></div><div class="card">有用户文件元数据的会话<br><b>442</b></div><div class="card">有工具活动快照的会话<br><b>57</b></div></div><p><a href="../../../reports/2026-10-05_evomind_full_data_processing.md">处理报告</a> · <a href="../../../reports/2026-10-05_evomind_data_supplement_request.md">数据方补交说明</a> · <a href="session_task_categories.csv">逐会话分类CSV</a> · <a href="requested_file_references.csv">文件补交定位CSV</a></p><img src="../figures/task_primary_bars.png"><img src="../figures/task_coverage_bars.png"><h2>逐会话归类</h2><input id="q" placeholder="查会话编号或正文" size="35"><select id="cat"><option value="">全部类别</option></select><select id="cf"><option value="">全部置信度</option><option>high</option><option>medium</option><option>low</option></select><span id="count"></span><table><thead><tr><th>会话</th><th>主类与其他主题</th><th>归类依据</th><th>可见用户输入</th></tr></thead><tbody id="body"></tbody></table></main><script>const rows='''
    j=json.dumps(ui,ensure_ascii=False).replace('</',r'<\/')
    tail='''; const E=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); [...new Set(rows.map(x=>x.category))].sort().forEach(x=>{const o=document.createElement('option');o.textContent=x;cat.append(o)});function render(){const selected=rows.filter(x=>(!cat.value||x.category===cat.value)&&(!cf.value||x.confidence===cf.value)&&(!q.value||[x.id,x.text,x.reason].join(' ').toLowerCase().includes(q.value.toLowerCase()))); count.textContent=selected.length+' 条'; body.innerHTML=selected.map(x=>'<tr><td><a href="../../matched_066/private/conversations/'+encodeURIComponent(x.id)+'.html">'+E(x.id)+'</a><br><span class="muted">'+x.requests+'组用户输入 · '+E(x.confidence)+'</span></td><td>'+E(x.category)+(x.extra.length?'<br><span class="muted">其他：'+E(x.extra.join('、'))+'</span>':'')+'</td><td class="reason">'+E(x.reason)+'</td><td><details><summary>'+E(x.text.slice(0,80))+'</summary><pre>'+E(x.text)+'</pre><span class="muted">此处最多展示2000字，完整原文见会话链接</span></details></td></tr>').join('')};[q,cat,cf].forEach(x=>x.addEventListener('input',render));render();</script></html>'''
    htmlprefix=htmlprefix.replace('../../../reports/', '../../../../reports/')
    (P/'index.html').write_text(htmlprefix+j+tail,encoding='utf-8')
    manifest=json.loads((R/'manifest.json').read_text(encoding='utf-8'))
    source_path=BASE/'matched_066/private/evomind_conversations.json'
    annotations_path=BASE/'accepted_071/private/accepted_annotations.json'
    source_unchanged=hashlib.sha256(source_path.read_bytes()).hexdigest()==manifest['source_sha256']
    annotations_unchanged=hashlib.sha256(annotations_path.read_bytes()).hexdigest()==manifest['annotation_sha256']
    assert source_unchanged and annotations_unchanged,'Inputs changed during processing'
    validation={'source_session_ids_exactly_covered':True,'labels_unique':True,'primary_counts_sum_to_1466':sum(primary.values())==1466,'category_values_valid':True,'evidence_user_groups_exist':True,'source_files_unmodified':'hashes stored in manifest; checked separately at finish','semantic_accuracy':'not independently measured'}
    validation.update({'source_files_unmodified':source_unchanged and annotations_unchanged,'source_sha256':manifest['source_sha256'],'annotation_sha256':manifest['annotation_sha256']})
    dump(R/'delivery_validation.json',validation)
    print(json.dumps({'summary':stats,'distribution':summary},ensure_ascii=False),flush=True)

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
