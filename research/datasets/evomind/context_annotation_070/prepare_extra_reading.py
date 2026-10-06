from pathlib import Path
import json,re
P=Path(__file__).resolve().parent/'private';data=json.loads((P/'review_data.json').read_text(encoding='utf-8'));ss={s['id']:s for s in data['sessions']}
terms={'conv_5c2f401a22a3':['案例','第9','第 9','融资'],'conv_079666ce3ba0':['App','配置','保存','白名单'],'conv_7b0ea502fdac':['类似','游戏','CEO','标题','安装','几个','三张','确认'],'conv_15f0f4d89d3f':['一段','整理','简介'],'conv_2c6000fce9b3':['定稿','消失','投研','一等奖'],'conv_8e704f119abe':['字体','中文','焦点','截图','插入','文字'],'conv_6f4fad2b911f':['年度','申报','做一份','更新'],'conv_ae3627d8a84b':['图','三选','徐新','PPT']}
for sid,words in terms.items():
 rows=[]
 for n in ss[sid]['users']:
  t=re.sub(r'^\[[^\n\]]+\]\s*','',n['text']).removeprefix('请使用中文回复，除非用户明确使用其他语言。').strip()
  if any(w.lower() in t.lower() for w in words):
   if len(t)>1600:t=t[:800]+'\n[中间略]\n'+t[-800:]
   rows.append({'id':n['id'],'text':t,'lines':[x['line'] for x in n['occurrences']]})
 (P/('extra_'+sid+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 print(sid,len(rows))
rows=[]
for n in ss['conv_2a18a3d5990b']['users']:
 t=n['text'];at=t.find('# 当前角色任务');t=t[at:] if at>=0 else t
 rows.append({'id':n['id'],'task':t[:1000],'tail':t[-350:],'lines':[x['line'] for x in n['occurrences']]})
(P/'debate_roles.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
