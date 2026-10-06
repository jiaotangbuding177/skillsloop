"""Frozen-source derivative export; topic votes are explicit editorial review, not rules."""
from pathlib import Path
import json, csv, hashlib, html
from collections import Counter
R=Path(__file__).resolve().parent; P=R/'private'; S=R.parent/'enriched_20261006/private'
TOPICS={'LEGAL':'合同审阅与法务合规','HR':'招聘、简历与人事','OFFICE':'文档、演示与视觉内容','DATA':'财务核算、预算与数据表格','BIZ':'企业、市场与经营调研','EDU':'教学、教育与科研','TECH':'软件产品、代码与技术排障','NEWS':'新闻与一般信息检索','ASSIST':'助手配置与技能管理','KNOW':'知识库、记忆与资料整理','COMM':'行政协同、邮件与日程','LIFE':'个人生活与旅行咨询','UNCLEAR':'可见目标尚不明确'}
# Explicit corrections after reading all 719 task/method/source-user cards.
# Local transferable operation, rather than the overall session topic, determines this axis.
CORRECTIONS={
 'COMM':[1,10,47,145,186,231,397,426,433],
 'TECH':[2,6,16,104,119,227,243,264,286,297,330,350,360,415,417,428,429,447,508,537,543,545,611],
 'KNOW':[12,15,24,109,116,185,250,518],
 'HR':[22],
 'ASSIST':[93,154],
 'DATA':[64,83,110,115,216,288,289,302,342,358,373,384,412,478,497,510,536,679,718],
 'LEGAL':[42,318,332,446,450,511,623,653],
 'BIZ':[36,212,269],
 'EDU':[107,681],
 'OFFICE':[74,85,101,127,143,146,150,162,168,170,175,178,192,196,214,218,219,232,239,271,281,295,306,328,331,335,352,353,354,355,401,402,406,427,430,432,456,468,473,475,479,489,507,520,523,532,564,565,595,616,618,620,625,651,674,689,698,699,704,708],
}
SESSION_CORRECTIONS={460:'DATA',643:'DATA',658:'DATA',778:'DATA'}
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def jsonl(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(''.join(json.dumps(v,ensure_ascii=False)+'\n' for v in x),encoding='utf-8')
def esc(s):return html.escape(str(s))
def main():
 cards=json.loads((P/'session_review_cards.json').read_text(encoding='utf-8')); full=rows(S/'enriched_sessions.jsonl'); inputs={x['session_id']:x for x in rows(S/'source_inputs.jsonl')}; candidates=rows(S/'candidate_contexts_union.jsonl'); quality={x['candidate_id']:x for x in rows(R.parent/'quality_20261006/private/quality_assessments.jsonl')}; bysid={x['session_id']:x for x in full}
 votes={i:t for t,ids in CORRECTIONS.items() for i in ids}; assert len(votes)==sum(map(len,CORRECTIONS.values()))
 anns=[]; cexport=[]; changes=[]; ctopics={}
 for i,c in enumerate(candidates,1):
  old=bysid[c['session_id']]['topic_annotation']['primary']; new=votes.get(i,old)
  annotation={'task_topic':new,'task_topic_name':TOPICS[new],'previous_session_topic':old,'classification_axis':'本片段可复用的具体任务或局部操作；不是整场会话主题','review_scope':'719条任务、方法与来源用户摘录逐条复查；不等于719条全文或专业正确性验收','review_index':i,'confidence':'medium' if new!=old else 'inherited_reviewed','source_evidence_group_ids':c['seed_group_ids'],'complete_trace_verified':False,'task_success':'unknown','method_validated_on_new_task':False}
  ce={**c,'research_annotations':annotation,'quality_profile':quality[c['candidate_id']]}; cexport.append(ce);ctopics.setdefault(c['session_id'],set()).add(new)
  if new!=old:changes.append({'kind':'学习片段主题','id':c['candidate_id'],'task':c['task'],'old':old,'new':new,'reason':'逐条核对实际任务及可学习局部操作，解除对会话主主题的继承'})
 for card in cards:
  s=bysid[card['session_id']]; old=s['topic_annotation']; new=SESSION_CORRECTIONS.get(card['review_index'],old['primary']); secondary=sorted((set(old.get('secondary',[]))|ctopics.get(s['session_id'],set())|({old['primary']} if new!=old['primary'] else set()))-{new})
  ann={'session_id':s['session_id'],'screening':s['effective_screening_decision'],'screening_name':'保留学习候选' if s['effective_screening_decision']=='KEEP' else '暂存待补证','session_primary_topic':new,'session_primary_topic_name':TOPICS[new],'secondary_topics':secondary,'secondary_topic_names':[TOPICS[x] for x in secondary],'previous_topic_annotation':old,'topic_reason':old['reason'] if new==old['primary'] else '完整用户正文明确包含记账、会计分录、财务报表或财务税务处理，调整为财务数据主题；其他任务保留次主题','topic_evidence_group_ids':old.get('evidence_user',[]),'review_index':card['review_index'],'review_scope':'1224条原依据用户摘录、主题理由及候选任务逐条复查；7条扩展阅读全部有效用户正文','expanded_user_text_read':card['review_index'] in [460,643,658,679,778,810,876],'title_used_as_task_truth':False,'candidate_ids':s['candidate_ids'],'complete_trace_verified':False,'chronology_verified':False,'business_outcome':'unknown'}
  anns.append(ann)
  if new!=old['primary']:changes.append({'kind':'会话主主题','id':s['session_id'],'old':old['primary'],'new':new,'reason':ann['topic_reason']})
 amap={x['session_id']:x for x in anns}; included=set(amap); exported=[]
 for a in anns:
  s=bysid[a['session_id']]; exported.append({**inputs[a['session_id']],'schema':'evomind-topic-conversation-v1','research_annotations':a,'accepted_content_correspondences':s['accepted_content_correspondences'],'unverified_correspondence_candidates':s['unverified_correspondence_candidates'],'skill_evidence':s['skill_evidence'],'presentation_note':'正文保持来源展示顺序；内容匹配与真实时序分开，未冒充完整任务轨迹'})
 jsonl(P/'conversations.jsonl',exported);jsonl(P/'model_inputs.jsonl',[inputs[a['session_id']] for a in anns]);jsonl(P/'session_annotations.jsonl',anns);jsonl(P/'learning_candidates.jsonl',cexport);dump(P/'annotation_changes.json',changes)
 # Topic partitions are mutually exclusive for primary counts. Secondary labels are overlaps.
 table=[]
 for t,name in TOPICS.items():
  ss=[x for x in exported if x['research_annotations']['session_primary_topic']==t];cc=[x for x in cexport if x['research_annotations']['task_topic']==t]
  jsonl(P/f'topics/{t}/conversations.jsonl',ss);jsonl(P/f'topics/{t}/learning_candidates.jsonl',cc)
  table.append({'主题':name,'代码':t,'可用会话素材':len(ss),'保留学习候选会话':sum(x['research_annotations']['screening']=='KEEP' for x in ss),'暂存待补证会话':sum(x['research_annotations']['screening']=='HOLD' for x in ss),'具体任务学习片段':len(cc)})
 with (R/'topic_statistics.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
 summary={'source_sessions':len(full),'included_sessions':len(exported),'keep_sessions':sum(a['screening']=='KEEP' for a in anns),'hold_sessions':sum(a['screening']=='HOLD' for a in anns),'excluded_from_this_release':len(full)-len(exported),'learning_candidate_fragments':len(cexport),'certified_complete_traces':'未进行完整轨迹认证，不以会话数替代','session_primary_corrections':sum(x['kind']=='会话主主题' for x in changes),'candidate_topic_corrections':sum(x['kind']=='学习片段主题' for x in changes),'topic_statistics':table,'review_coverage':{'session_cards':1224,'candidate_cards':719,'expanded_full_user_sessions':7,'independent_gold_validation':False}}
 dump(R/'summary.json',summary);dump(P/'excluded_ids.json',[{'session_id':s['session_id'],'decision':'EXCLUDE','reason':s['original_screening'].get('reason')} for s in full if s['session_id'] not in included])
 # Readable per-session export: every user/assistant body is present; no manufactured rounds.
 for x in exported:
  a=x['research_annotations']; lines=[f"# {x['session_id']}",'',f"会话主主题：{a['session_primary_topic_name']}；状态：{a['screening_name']}",f"其他主题：{'、'.join(a['secondary_topic_names']) or '无'}",'', '说明：下面保留来源正文展示次序；内容对应关系另存，不据此保证真实时间顺序。','']
  for m in x['messages']:lines.extend([f"## {'用户' if m['role']=='user' else 'AI'} · {m['group_id']}",'',m['content'],''])
  (P/'conversations').mkdir(exist_ok=True);(P/'conversations'/f"{x['session_id']}.md").write_text('\n'.join(lines),encoding='utf-8')
 links=[]
 for x in exported:
  a=x['research_annotations'];cs=[c for c in cexport if c['session_id']==x['session_id']]; text=' / '.join(c['task']+'（'+c['research_annotations']['task_topic_name']+'）' for c in cs)
  links.append(f'<tr data-topic="{a["session_primary_topic"]}" data-state="{a["screening"]}"><td><a href="conversations/{x["session_id"]}.md">{x["session_id"]}</a></td><td>{esc(a["session_primary_topic_name"])}</td><td>{a["screening_name"]}</td><td>{esc(text or "尚未确定局部学习点")}</td><td>{esc(a["topic_reason"])}</td></tr>')
 page='''<!doctype html><meta charset="utf-8"><title>EvoMind任务主题数据集</title><style>body{font:15px Microsoft YaHei;background:#f5f7fb;margin:30px;color:#17263d}table{border-collapse:collapse;background:white;width:100%}td,th{border:1px solid #dde4ed;padding:9px;text-align:left}input,select{padding:10px;margin:8px}img{max-width:100%}</style><h1>EvoMind任务主题数据集</h1><p>1,224条会话素材：716保留、508暂存。719条局部学习片段；尚未认证为完整轨迹。242条排除会话未纳入本版本，原归档保留。</p><img src="../figures/01_sessions_by_topic.png"><img src="../figures/02_candidates_by_task.png"><input id="search" placeholder="搜索编号、任务、依据"><select id="topic"><option value="">全部主题</option>'''+''.join(f'<option value="{t}">{n}</option>' for t,n in TOPICS.items())+'''</select><select id="state"><option value="">全部状态</option><option value="KEEP">保留</option><option value="HOLD">暂存</option></select><p id="count"></p><table><thead><tr><th>会话编号与全文</th><th>会话主主题</th><th>状态</th><th>具体学习任务与主题</th><th>会话归类依据</th></tr></thead><tbody>'''+''.join(links)+'''</tbody></table><script>const rows=[...document.querySelectorAll('tbody tr')];function filter(){let n=0;for(const r of rows){let yes=(!topic.value||r.dataset.topic===topic.value)&&(!state.value||r.dataset.state===state.value)&&r.textContent.toLowerCase().includes(search.value.toLowerCase());r.hidden=!yes;if(yes)n++;}count.textContent='当前显示 '+n+' 条';}for(const el of [search,topic,state])el.addEventListener('input',filter);filter();</script>'''
 (P/'index.html').write_text(page,encoding='utf-8')
 import matplotlib;matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 from matplotlib.font_manager import FontProperties
 font=FontProperties(fname='C:/Windows/Fonts/msyh.ttc');plt.rcParams['axes.unicode_minus']=False;(R/'figures').mkdir(exist_ok=True)
 for filename,field,title,stack in [('01_sessions_by_topic','可用会话素材','可用会话素材按主主题分布（1,224条）',True),('02_candidates_by_task','具体任务学习片段','学习片段按实际任务分布（719条）',False)]:
  data=sorted(table,key=lambda x:x[field],reverse=True); fig,ax=plt.subplots(figsize=(14,7));pos=range(len(data))
  if stack:
   keep=[x['保留学习候选会话'] for x in data];hold=[x['暂存待补证会话'] for x in data];ax.bar(pos,keep,color='#296ab3',label='保留学习候选');ax.bar(pos,hold,bottom=keep,color='#f1b85c',label='暂存待补证');ax.legend(prop=font,frameon=False)
  else:ax.bar(pos,[x[field] for x in data],color='#39878c')
  for i,x in enumerate(data):ax.text(i,x[field]+2,str(x[field]),ha='center',fontproperties=font)
  ax.set_xticks(list(pos),[x['主题'].replace('、','\n').replace('与','\n') for x in data],fontproperties=font,fontsize=9);ax.set_title(title,fontproperties=font,fontsize=18,pad=20);ax.set_ylabel('数量',fontproperties=font);ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);ax.set_ylim(0,max(x[field] for x in data)*1.17);fig.text(.06,.02,'会话素材与学习片段为不同统计单位；均不表示已成功生成技能或已认证完整轨迹。',fontproperties=font,color='#617083',fontsize=10);fig.tight_layout(rect=[0,.05,1,1])
  for ext in ['png','svg','pdf']:fig.savefig(R/'figures'/f'{filename}.{ext}',dpi=180)
  plt.close(fig)
 # Deliverable checks include exact source text equality and no excluded leakage.
 assert len(exported)==1224 and len(cexport)==719 and len(full)-len(exported)==242
 assert sum(x['可用会话素材'] for x in table)==1224 and sum(x['具体任务学习片段'] for x in table)==719
 assert all(c['session_id'] in included for c in cexport)
 assert all(x['messages']==inputs[x['session_id']]['messages'] for x in exported)
 assert all(a['screening']!='EXCLUDE' for a in anns)
 frozen=json.loads((R/'review_inputs_manifest.json').read_text(encoding='utf-8'))
 assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in frozen['source_files'].items())
 for c in cexport:
  groups={m['group_id'] for m in bysid[c['session_id']]['messages']};assert all(g in groups for g in c['seed_group_ids'])
 dump(R/'verification.json',{'passed':True,'checks':['1224会话、719片段、242排除数量正确','主题互斥分区数量守恒','全部片段可回查保留会话','全部会话正文与冻结输入逐字一致','新工作集不含EXCLUDE会话','4项冻结来源哈希未改变','全部片段证据消息编号存在'],'browser_interactive_verified':False,'topic_accuracy_gold_verified':False})
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
