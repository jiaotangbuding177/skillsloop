"""Offline evidence-quality presentation; no model calls or historical tool execution."""
from pathlib import Path
import csv, json, html, hashlib
from collections import Counter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager

BASE = Path(__file__).resolve().parent
SOURCE = BASE.parent / 'enriched_20261006'
PRIVATE = BASE / 'private'
FIG = BASE / 'figures'
BLUE, TEAL, ORANGE, GRAY = '#275F9A', '#438C8B', '#C8893C', '#A9AFB7'
SHORT_TOPICS = {'BIZ':'经营与商业分析','OFFICE':'文档与交付制作','EDU':'教育与科研','LEGAL':'合同与法务','HR':'招聘与人事','ASSIST':'助手日常操作','NEWS':'新闻与资讯','KNOW':'知识整理','TECH':'技术与工具排障','COMM':'沟通与协作','LIFE':'生活与个人事务','DATA':'数据与计算','UNCLEAR':'原标目标不明确','PLATFORM':'平台模板或模拟'}
STRUCTURE_LABELS = {'多用户输入素材':'多条用户输入','单用户多AI素材':'单条输入、多条AI正文','一问一答素材':'单条输入、单条AI正文','单边素材':'单边正文'}

def rows(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]

def esc(value):
    if isinstance(value, list): value = '；'.join(str(x) for x in value)
    return html.escape(str(value if value is not None else ''))

def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def filename(cid): return cid.replace(':', '_')

def classify(p):
    if not p['source_anchor_complete'] or not p['user_text_count'] or not p['assistant_text_count']:
        return '需核对正文或来源'
    if p['accepted_local_edge_count']:
        return '有已接受的局部内容对应'
    if p['proposed_local_edge_count']:
        return '只有待核的局部对应候选'
    return '没有局部对应记录'

def advice(p):
    bucket = p['recovery_preparation_state']
    prefix = {'需核对正文或来源':'先回查缺少的正文或出处，再判断能否组成任务过程。',
              '有已接受的局部内容对应':'可以优先恢复任务、要求替换与反馈关系；已有对应只说明部分内容能对应，不能代替完整轨迹。',
              '只有待核的局部对应候选':'用户与AI正文都在，但已有局部对应仍待核；先做语义关联，避免把同会话的其他任务拼进来。',
              '没有局部对应记录':'保留原文作为恢复输入；没有局部关系记录不代表没有真实回复，也不代表该方法没有价值。'}[bucket]
    return prefix + ' 当前仅能学习正文支持的局部方法，历史执行效果、完整时序和新任务收益均未认证。'

def setup_font():
    fonts = font_manager.findSystemFonts()
    choice = next((x for x in fonts if Path(x).name.lower() == 'msyh.ttc'), None)
    if not choice: choice = next((x for x in fonts if Path(x).name.lower() in ('simhei.ttf','simsun.ttc')), None)
    if not choice: raise RuntimeError('No Chinese font available; do not export unreadable charts.')
    font_manager.fontManager.addfont(choice)
    name = font_manager.FontProperties(fname=choice).get_name()
    plt.rcParams.update({'font.family':name,'axes.unicode_minus':False,'font.size':12,'axes.labelcolor':'#34445B','text.color':'#25344A','axes.edgecolor':'#BDC6D1','svg.fonttype':'none','pdf.fonttype':42})
    return choice

def decorate(ax):
    ax.set_axisbelow(True)
    ax.grid(axis='x', color='#E7EDF3', lw=0.7)
    for side in ('top','right','left'): ax.spines[side].set_visible(False)
    ax.tick_params(axis='y',length=0,pad=10)

def export(fig, name):
    for ext in ('png','svg','pdf'): fig.savefig(FIG / f'{name}.{ext}', dpi=180, bbox_inches='tight', facecolor='white')
    plt.close(fig)

def simple_bars(ax, labels, values, total, colors=None):
    ax.barh(labels, values, color=colors or BLUE, height=0.6)
    ax.invert_yaxis()
    maxv = max(values, default=0)
    ax.set_xlim(0, max(maxv * 1.35, 1))
    for i,v in enumerate(values): ax.text(v+max(maxv*.025, .04),i,f'{v:,}  ({v/total:.1%})',va='center',fontsize=11)
    decorate(ax)
    ax.set_xlabel('候选片段数')

STYLE = '''<style>:root{--nav:#18344e;--blue:#275f9a;--soft:#edf3f8;--ink:#25344a}*{box-sizing:border-box}body{margin:0;background:#f3f6f9;color:var(--ink);font:15px/1.7 'Microsoft YaHei',sans-serif}header{background:var(--nav);color:white;padding:28px max(4vw,20px)}header h1{margin:0 0 8px;font-size:28px}main{max-width:1440px;margin:auto;padding:24px}a{color:var(--blue);text-decoration:none}a:hover{text-decoration:underline}header a{color:#a8d4ef}.box,.card{background:white;border:1px solid #dde5ec;border-radius:12px;padding:22px;margin-bottom:18px}.notice{background:#fff7e8;border-left:4px solid #c8893c;padding:15px;margin-bottom:18px}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}.stat{background:white;border-radius:10px;padding:15px;border:1px solid #dde5ec}.stat strong{display:block;font-size:30px;color:var(--blue)}.controls{display:flex;gap:10px;flex-wrap:wrap;position:sticky;top:0;background:#f3f6f9;padding:12px 0;z-index:2}input,select,button{font:inherit;padding:9px;border:1px solid #cbd6df;border-radius:6px;background:white}input{flex:2;min-width:250px}select{max-width:280px}button{cursor:pointer;color:var(--blue)}.badge{display:inline-block;font-size:13px;background:#e9f0f7;color:#285273;padding:2px 8px;border-radius:5px;margin:0 6px 4px 0}.id{color:#758397;font-size:12px;overflow-wrap:anywhere}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}.grid div{background:#f5f8fb;padding:12px;border-radius:7px}.grid small{display:block;color:#6c7a8b}.card h2{font-size:20px;margin:6px 0}.card p{margin:8px 0}.muted{color:#6c7a8b}.message{white-space:pre-wrap;word-break:break-word;border:1px solid #e1e7ee;padding:16px;border-radius:8px;background:#fafcfe;margin:12px 0;font:14px/1.8 'Microsoft YaHei',sans-serif}.message.user{border-left:4px solid #438c8b}.message.assistant{border-left:4px solid #275f9a}summary{cursor:pointer;color:#275f9a}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:10px;border-bottom:1px solid #e5ebf1}th{background:#edf3f8}img{max-width:100%;height:auto}.pager{display:flex;gap:16px;justify-content:center;align-items:center;padding:20px}.caution{color:#8d6328}h3{margin-bottom:8px}@media(max-width:600px){main{padding:12px}header{padding:18px}.box,.card{padding:15px}}</style>'''

def detail_html(p, c, sem):
    messages = ''
    for role,label in [('user','用户'),('assistant','AI')]:
        messages += f'<h2>{label}原文集合</h2><p class="muted">以下按阅读视图排列，不代表已核准的真实时间顺序。</p>'
        for m in c['messages']:
            if m.get('role') != role or not m.get('learning_active',True): continue
            ids = m.get('source_group_ids',[m['group_id']])
            messages += f'<div class="message {role}"><div class="id">{esc(" / ".join(ids))} · {esc(m.get("inclusion",""))}</div>{esc(m["content"])}</div>'
    shtml = '<p>本轮未逐字复核本片段；任务和学习点沿用上轮AI筛选，不是人工黄金标签。</p>'
    if sem:
        support = {'supported':'正文支持局部方法','partial':'只支持部分归纳','unsupported':'归纳缺乏正文依据','unclear':'目前无法判断'}
        align = {'coherent':'目标与处理点相符','partial':'部分相符，需限制范围','unclear':'目前无法判断','mismatch':'目标与处理点对不上'}
        shtml = f'<p><b>方法依据：</b>{esc(support.get(sem.get("method_support"),sem.get("method_support","未记录")))}</p><p><b>目标与方法：</b>{esc(align.get(sem.get("goal_method_alignment"),sem.get("goal_method_alignment","未记录")))}</p><p>{esc(sem.get("readable_assessment",""))}</p><h3>主要缺证</h3><p>{esc(sem.get("limitations",[]))}</p><h3>迁移风险</h3><p>{esc(sem.get("transfer_risk",""))}</p>'
        for label,field in [('方法支持原文','method_evidence'),('反馈与修订原文','feedback_or_revision_evidence')]:
            shtml += f'<h3>{label}</h3>'
            evidence = sem.get(field,[])
            if isinstance(evidence,dict): evidence=[evidence]
            if not evidence: shtml += '<p class="muted">没有独立核准的此类证据；不能据此认定从未发生。</p>'
            for e in evidence:
                if isinstance(e,dict): shtml += f'<p>{esc(e.get("quote",""))}<br><small class="id">{esc(e.get("group_id",""))}</small></p>'
                else: shtml += f'<p>{esc(e)}</p>'
    table = ''.join(f'<tr><td>{esc(k)}</td><td>{esc(v)}</td></tr>' for k,v in [
        ('当前关系恢复准备状态',p['recovery_preparation_state']),('去重正文结构',p['structure_label']),
        ('用户／AI正文数',f"{p['user_text_count']} / {p['assistant_text_count']}"),
        ('全部来源锚点可回查','是' if p['source_anchor_complete'] else '有缺口'),
        ('局部已接受内容对应',p['accepted_local_edge_count']),('局部待核对应候选',p['proposed_local_edge_count']),
        ('已接受对应覆盖的用户／AI正文',f"{p['accepted_covered_user_text_count']}/{p['user_text_count']} · {p['accepted_covered_assistant_text_count']}/{p['assistant_text_count']}"),
        ('本候选载荷锚点的工具记录',p['payload_anchored_tool_count']),('同会话工具记录',p['session_tool_count']),
        ('候选关联文件元数据',p['candidate_file_reference_count']),('同会话文件元数据',p['session_file_reference_count']),
        ('独立历史时序／任务结果／新任务收益','均未认证；不能当失败、无收益或从未执行'),
    ])
    return f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(c['task'])}｜质量卡</title>{STYLE}<header><h1>{esc(c['task'])}</h1><div>{esc(c['candidate_id'])}</div><a href="../index.html">返回719条质量总览</a></header><main><div class="notice">这是候选素材质量卡，不是完整轨迹或技能收益认证。时间、回复关系、工具归属与业务成功分别核对。</div><div class="box"><h2>现在有什么质量，下一步怎么用</h2><p><b>{esc(p['learning_use_recommendation'])}</b></p><p>{esc(p['quality_readout'])}</p><table>{table}</table></div><div class="box"><h2>目前提炼出的局部学习点</h2><p>{esc(c['learning_candidate'])}</p><h3>原文支持线索</h3><p>{esc(c.get('evidence_quote',''))}</p><h3>原筛选保留的限制</h3><p>{esc(c.get('limitations',[]))}</p><p><a href="../../../enriched_20261006/private/sessions/{esc(p['session_id'])}.reading.html">完整会话去重阅读页</a> · <a href="../../../enriched_20261006/private/sessions/{esc(p['session_id'])}.html">原来源审计页</a></p></div><div class="box"><h2>本轮正文语义复核状态</h2>{shtml}</div><div class="box">{messages}</div></main></html>'''

def main():
    FIG.mkdir(parents=True,exist_ok=True); (PRIVATE/'cards').mkdir(parents=True,exist_ok=True)
    candidates = {x['candidate_id']:x for x in rows(SOURCE/'private/candidate_contexts_union.jsonl')}
    profiles = rows(PRIVATE/'evidence_profiles.jsonl')
    semantic_path = PRIVATE/'semantic_audit.jsonl'
    semantic = {x['candidate_id']:x for x in rows(semantic_path)} if semantic_path.exists() else {}
    with (SOURCE/'private/session_inventory.csv').open(encoding='utf-8-sig',newline='') as f: sessions = list(csv.DictReader(f))
    assert len(profiles)==len(candidates)==719 and len(sessions)==1466
    assert set(candidates)=={x['candidate_id'] for x in profiles}
    topics = {}
    for s in sessions:
        code = s['primary_topic']; topics.setdefault(code,Counter())[s['effective_decision']]+=1
    topic_order = sorted(topics, key=lambda x:sum(topics[x].values()), reverse=True)
    for p in profiles:
        p['source_structure_label'] = p['structure_label']
        p['structure_label'] = STRUCTURE_LABELS[p['structure_label']]
        p['topic_label'] = SHORT_TOPICS[p['topic_code']]
        c = candidates[p['candidate_id']]
        alias_to_message = {}
        for m in c['messages']:
            if m.get('learning_active',True) and m.get('content','').strip():
                for alias in m.get('source_group_ids',[m['group_id']]): alias_to_message[alias] = (m['group_id'],m['role'])
        covered = set()
        for e in p['accepted_local_edges']:
            for field in ('user_group_id','assistant_group_id'):
                if e[field] in alias_to_message: covered.add(alias_to_message[e[field]])
        p['accepted_covered_user_text_count'] = sum(role=='user' for _,role in covered)
        p['accepted_covered_assistant_text_count'] = sum(role=='assistant' for _,role in covered)
        p['accepted_coverage_state'] = '全部正文有内容对应' if p['accepted_covered_user_text_count']==p['user_text_count'] and p['accepted_covered_assistant_text_count']==p['assistant_text_count'] else ('部分正文有内容对应' if covered else '未提供已接受对应')
        p['recovery_preparation_state'] = classify(p)
        p['quality_readout'] = advice(p)
        p['semantic_review_status'] = '本轮正文复核' if p['candidate_id'] in semantic else '沿用上轮候选筛选，未在本轮正文复核'
        p['semantic_review'] = semantic.get(p['candidate_id'])
        sem = p['semantic_review']
        if not sem: p['learning_use_recommendation'] = '保留旧候选建议；本轮未逐条语义复核其全部语义'
        elif sem.get('method_support')=='unsupported' or sem.get('goal_method_alignment')=='mismatch': p['learning_use_recommendation'] = '暂停按旧摘要直接归纳，先回查原文和任务关联'
        elif sem.get('method_support')=='partial' or sem.get('goal_method_alignment')=='partial': p['learning_use_recommendation'] = '先按语义复核意见收窄学习范围，再进入恢复'
        elif sem.get('method_support')=='unclear' or sem.get('goal_method_alignment')=='unclear': p['learning_use_recommendation'] = '仍需补语义依据，当前不能作确定学习结论'
        else: p['learning_use_recommendation'] = '正文支持的局部方法可进入恢复；执行效果仍待验证'
        p['card_url'] = f"cards/{filename(p['candidate_id'])}.html"
        (PRIVATE/p['card_url']).write_text(detail_html(p,candidates[p['candidate_id']],p['semantic_review']),encoding='utf-8')
    with (PRIVATE/'quality_assessments.jsonl').open('w',encoding='utf-8') as f:
        for p in profiles: f.write(json.dumps(p,ensure_ascii=False)+'\n')
    export_fields = [('candidate_id','候选编号'),('session_id','会话编号'),('task','任务'),('topic_label','原会话主主题'),('learning_candidate','局部学习点'),('recovery_preparation_state','关系恢复准备状态'),('structure_label','正文结构'),('user_text_count','去重用户正文数'),('assistant_text_count','去重AI正文数'),('source_anchor_complete','来源锚点完整'),('accepted_local_edge_count','局部已接受对应数'),('proposed_local_edge_count','局部待核对应数'),('accepted_covered_user_text_count','有已接受对应的用户正文数'),('accepted_covered_assistant_text_count','有已接受对应的AI正文数'),('accepted_coverage_state','全部正文的内容对应覆盖状态'),('payload_anchored_tool_count','候选载荷锚点工具记录数'),('session_tool_count','同会话工具记录数'),('candidate_file_reference_count','候选关联文件元数据数'),('semantic_review_status','本轮正文语义复核状态'),('quality_readout','逐条质量解释'),('limitations','原筛选限制')]
    with (PRIVATE/'逐条质量清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
        export_fields.extend([('learning_use_recommendation','当前学习范围建议')])
        w = csv.writer(f); w.writerow([v for k,v in export_fields])
        for p in profiles: w.writerow(['；'.join(map(str,p.get(k,[]))) if isinstance(p.get(k),list) else p.get(k,'') for k,v in export_fields])
    prep_order = ['有已接受的局部内容对应','只有待核的局部对应候选','没有局部对应记录','需核对正文或来源']
    structure_order = ['多条用户输入','单条输入、多条AI正文','单条输入、单条AI正文','单边正文']
    prep = Counter(p['recovery_preparation_state'] for p in profiles)
    structures = Counter(p['structure_label'] for p in profiles)
    coverage = [
        ('来源锚点全部可回查',sum(bool(p['source_anchor_complete']) for p in profiles)),
        ('用户与AI正文都保留',sum(bool(p['user_text_count'] and p['assistant_text_count']) for p in profiles)),
        ('有多段用户输入素材',sum(p['user_text_count']>=2 for p in profiles)),
        ('有局部已接受内容对应',sum(p['accepted_local_edge_count']>0 for p in profiles)),
        ('补入了非种子上下文',sum(p['expanded_context_count']>0 for p in profiles)),
        ('载荷锚点带有工具记录',sum(p['payload_anchored_tool_count']>0 for p in profiles)),
        ('有候选关联文件元数据',sum(p['candidate_file_reference_count']>0 for p in profiles)),
        ('完整历史时序已认证',0),('历史业务整体结果已认证',0),('新任务技能收益已认证',0),
    ]
    sem_support = Counter(x.get('method_support',x.get('method_supported','unknown')) for x in semantic.values())
    summary = {'sessions':len(sessions),'candidates':len(profiles),'candidate_sessions':len({p['session_id'] for p in profiles}),'effective_screening':dict(Counter(s['effective_decision'] for s in sessions)), 'topic_counts':{k:dict(topics[k]) for k in topic_order},'preparation_states':dict(prep),'structure_counts':dict(structures),'coverage':dict(coverage),'content_coverage_states':dict(Counter(p['accepted_coverage_state'] for p in profiles)),'semantic_reviewed_count':len(semantic),'semantic_support_counts':dict(sem_support),'verified_complete_trajectories':0,'interpretation':'数据准备与证据画像，不是任务成功率/语义准确率/技能有效率'}
    save_json(BASE/'quality_summary.json',summary)
    with (FIG/'topic_distribution.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['主题代码','主主题','保留','暂存','排除','合计'])
        for k in topic_order:w.writerow([k,SHORT_TOPICS[k],topics[k]['KEEP'],topics[k]['HOLD'],topics[k]['EXCLUDE'],sum(topics[k].values())])
    with (FIG/'quality_chart_data.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f);w.writerow(['图表','指标','数量','分母'])
        for k in prep_order:w.writerow(['关系恢复准备',k,prep[k],719])
        for k in structure_order:w.writerow(['正文结构',k,structures[k],719])
        for k,v in coverage:w.writerow(['证据覆盖',k,v,719])
    font = setup_font()
    fig,ax = plt.subplots(figsize=(13.8,8.5))
    labels=[SHORT_TOPICS[k] for k in topic_order];left=[0]*len(labels)
    for state,label,color in [('KEEP','保留学习候选',BLUE),('HOLD','暂存待补证',ORANGE),('EXCLUDE','排除本轮提炼',GRAY)]:
        vals=[topics[k][state] for k in topic_order];ax.barh(labels,vals,left=left,label=label,color=color,height=.68)
        for i,v in enumerate(vals):
            if v>=17:ax.text(left[i]+v/2,i,str(v),va='center',ha='center',color='white' if state=='KEEP' else '#25344A',fontsize=10)
        left=[a+b for a,b in zip(left,vals)]
    for i,v in enumerate(left):ax.text(v+4,i,str(v),va='center',fontsize=11)
    ax.invert_yaxis();ax.set_xlim(0,max(left)*1.13);decorate(ax);ax.set_xlabel('会话记录数（不是独立任务数）')
    ax.set_title('哪些主题有可学习材料？',loc='left',fontsize=20,pad=32)
    ax.legend(ncol=3,frameon=False,loc='lower left',bbox_to_anchor=(0,1.01),fontsize=11)
    fig.text(.02,.015,'来源会话1,466条｜保留716、暂存508、排除242。沿用会话主主题，不是工作流聚类。',fontsize=11,color='#657386')
    fig.subplots_adjust(left=.23,right=.96,top=.86,bottom=.10)
    export(fig,'01_topic_distribution')
    fig,axes=plt.subplots(1,2,figsize=(19.5,6.4),gridspec_kw={'wspace':.67})
    simple_bars(axes[0],prep_order,[prep[k] for k in prep_order],719,[TEAL,ORANGE,BLUE,GRAY]);simple_bars(axes[1],structure_order,[structures[k] for k in structure_order],719,BLUE)
    axes[0].set_title('A. 关系恢复准备状态',loc='left',fontsize=19,pad=22);axes[1].set_title('B. 去重正文的结构',loc='left',fontsize=19,pad=22)
    fig.text(.03,.015,'共719个候选片段。内容对应 ≠ 同任务或完整轨迹；多条用户输入 ≠ 已确认的多轮反馈。',fontsize=12,color='#657386')
    fig.subplots_adjust(left=.20,right=.96,top=.86,bottom=.16)
    export(fig,'02_quality_preparation')
    fig,ax=plt.subplots(figsize=(14,8.7));simple_bars(ax,[k for k,v in coverage],[v for k,v in coverage],719,[BLUE]*7+[GRAY]*3)
    ax.set_title('每个候选能观察到哪些证据？',loc='left',fontsize=20,pad=22)
    fig.text(.02,.02,'分母719；各项可重叠。0表示没有已认证记录，不表示历史任务全部失败。工具锚点仅定位载荷。',fontsize=11,color='#657386')
    fig.subplots_adjust(left=.30,right=.95,top=.90,bottom=.12);export(fig,'03_evidence_coverage')
    small = [{k:p.get(k) for k in ('candidate_id','session_id','task','topic_label','learning_candidate','recovery_preparation_state','structure_label','user_text_count','assistant_text_count','accepted_local_edge_count','proposed_local_edge_count','payload_anchored_tool_count','candidate_file_reference_count','quality_readout','semantic_review_status','learning_use_recommendation','card_url')} for p in profiles]
    data_json=json.dumps(small,ensure_ascii=False).replace('</','<\\/')
    options=''.join(f'<option>{esc(k)}</option>' for k in prep_order)
    topic_options=''.join(f'<option>{esc(SHORT_TOPICS[k])}</option>' for k in topic_order)
    index='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>719条候选轨迹质量总览</title>__STYLE__<header><h1>候选轨迹逐条质量总览</h1><div>每条都保留任务、学习点、证据、缺口与原文入口｜2026-10-06</div></header><main><div class="notice">评估的是719份候选素材的证据准备程度。已有筛选认为它们有局部学习点；本轮全量核对结构与来源，正文语义复核__SEM__份。没有将未复核内容标成语义正确，也没有认证完整轨迹、任务成功或技能收益。</div><div class="stats"><div class="stat"><strong>1,466</strong>来源会话记录</div><div class="stat"><strong>716</strong>保留候选的会话</div><div class="stat"><strong>719</strong>逐条质量卡</div><div class="stat"><strong>__SEM__</strong>本轮正文语义复核</div></div><p><a href="../../../../reports/2026-10-06_evomind_trajectory_quality_assessment.md">整体评估报告</a> · <a href="逐条质量清单.csv">下载中文逐条清单</a> · <a href="quality_assessments.jsonl">完整机器可读画像</a> · <a href="../../enriched_20261006/private/index.html">完整会话与原始证据</a></p><details class="box"><summary>查看3张柱状图（可下载PNG／SVG／PDF）</summary><img src="../figures/01_topic_distribution.png" alt="主主题与筛选分布"><img src="../figures/02_quality_preparation.png" alt="关系准备与正文结构"><img src="../figures/03_evidence_coverage.png" alt="证据覆盖"><p><a href="../figures/topic_distribution.csv">主题图原始数值</a> · <a href="../figures/quality_chart_data.csv">质量图原始数值</a></p></details><div class="controls"><input id="search" placeholder="搜索会话编号、任务、学习点"><select id="prep"><option value="">全部关系准备状态</option>__OPTIONS__</select><select id="topic"><option value="">全部主题</option>__TOPICS__</select><select id="review"><option value="">全部语义复核状态</option><option value="yes">本轮正文复核</option><option value="no">本轮未逐条语义复核</option></select></div><div id="count" class="muted"></div><div id="list"></div><div class="pager"><button id="prev">上一页</button><span id="page"></span><button id="next">下一页</button></div></main><script>const data=__DATA__;let page=0;let selected=[];const size=30;const $=id=>document.getElementById(id);function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}function filter(){const q=$('search').value.trim().toLowerCase();selected=data.filter(p=>(!q||[p.candidate_id,p.session_id,p.task,p.learning_candidate].join(' ').toLowerCase().includes(q))&&(!$('prep').value||p.recovery_preparation_state===$('prep').value)&&(!$('topic').value||p.topic_label===$('topic').value)&&(!$('review').value||($('review').value==='yes')===(p.semantic_review_status==='本轮正文复核')));page=0;render()}function render(){const a=selected.slice(page*size,(page+1)*size);$('count').textContent=`找到 ${selected.length} 条；每页 ${size} 条。`; $('list').innerHTML=a.map(p=>`<article class="card"><div class="id">${esc(p.candidate_id)} · ${esc(p.session_id)}</div><h2><a href="${esc(p.card_url)}">${esc(p.task)}</a></h2><span class="badge">${esc(p.recovery_preparation_state)}</span><span class="badge">${esc(p.structure_label)}</span><span class="badge">${esc(p.topic_label)}</span><p><b>可学什么：</b>${esc(p.learning_candidate)}</p><div class="grid"><div><small>去重用户／AI正文</small>${p.user_text_count}／${p.assistant_text_count}</div><div><small>局部已接受／待核对应</small>${p.accepted_local_edge_count}／${p.proposed_local_edge_count}</div><div><small>载荷锚点工具／关联文件元数据</small>${p.payload_anchored_tool_count}／${p.candidate_file_reference_count}</div></div><p class="muted">${esc(p.quality_readout)}</p><p class="caution">${esc(p.semantic_review_status)}</p><a href="${esc(p.card_url)}">打开逐条质量与全部候选原文 →</a></article>`).join('');const n=Math.max(1,Math.ceil(selected.length/size));$('page').textContent=`第 ${page+1} / ${n} 页`;$('prev').disabled=page===0;$('next').disabled=page+1>=n}['search','prep','topic','review'].forEach(x=>$(x).addEventListener('input',filter));$('prev').onclick=()=>{if(page>0){page--;render();$('list').scrollIntoView()}};$('next').onclick=()=>{if((page+1)*size<selected.length){page++;render();$('list').scrollIntoView()}};filter();</script></html>'''
    for k,v in {'__STYLE__':STYLE,'__SEM__':str(len(semantic)),'__OPTIONS__':options,'__TOPICS__':topic_options,'__DATA__':data_json}.items(): index=index.replace(k,v)
    (PRIVATE/'index.html').write_text(index,encoding='utf-8')
    save_json(BASE/'presentation_build.json',{'font':font,'candidate_pages':len(profiles),'semantic_reviewed_count':len(semantic),'charts':3,'formats':['png','svg','pdf'],'no_model_calls':True,'no_demo_changes':True})
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
