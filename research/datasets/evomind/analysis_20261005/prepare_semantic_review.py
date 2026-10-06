from pathlib import Path
import json, re

R=Path(__file__).resolve().parent
P=R/'private'
rows=json.loads((P/'conversation_cluster_rows.json').read_text(encoding='utf-8'))
categories={
 'LEGAL':'合同审阅与法务合规','HR':'招聘、简历与人事','OFFICE':'文档、演示与视觉内容制作',
 'DATA':'数据分析与表格处理','BIZ':'企业、市场与经营调研','EDU':'教学、教育与科研',
 'TECH':'软件开发、代码与技术排障','NEWS':'新闻、热点与一般信息检索','ASSIST':'助手配置、技能管理与系统操作',
 'KNOW':'知识库、记忆与资料整理','COMM':'邮件、提醒与协同行动','LIFE':'个人生活与一般咨询',
 'PLATFORM':'仅平台注入或多智能体模拟内容','UNCLEAR':'可见目标不明确或依据不足'
}
(R/'category_definitions.json').write_text(json.dumps(categories,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
parts=[rows[:489],rows[489:978],rows[978:]]
for shard,rs in enumerate(parts):
 folder=P/f'semantic_shard_{shard+1}';folder.mkdir(exist_ok=True)
 for start in range(0,len(rs),55):
  packed=[]
  for row in rs[start:start+55]:
   pairs=list(zip(row['user_groups'],row['clean_user_texts']))
   entries=[]
   # Every user input is represented; long texts explicitly show extraction limits.
   allowance=max(65,650//max(1,len(pairs)))
   for gid,text in pairs:
    cut=len(text)>allowance
    visible=text if not cut else text[:max(40,allowance*3//4)]+'[…]'+text[-max(20,allowance//4):]
    entries.append({'u':gid,'text':visible,'cut':cut})
   packed.append({'session_id':row['session_id'],'requests':entries,'local_cluster':row['local_cluster'],'full_text_available':'../conversation_cluster_rows.json / matched_066 per-session JSON'})
  (folder/f'batch_{start//55+1:02}.json').write_text(json.dumps(packed,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
print(json.dumps({'shards':[len(x) for x in parts],'sessions':len(rows),'categories':categories},ensure_ascii=False))
