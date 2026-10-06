import json
from pathlib import Path
P=Path(__file__).resolve().parent/'private'
def read(n):return json.loads((P/n).read_text(encoding='utf-8'))
def clean(t):
 if '# 当前角色任务' in t:t=t[t.index('# 当前角色任务'):]
 if '当前用户输入：' in t:t=t.split('当前用户输入：')[-1]
 return t
d=read('review_data.json');out=[];extra=[]
for s in d['sessions']:
 nodes={n['id']:n for n in s['users']+s['assistants']}
 for k,l in d['seed']['labels'][s['id']].items():
  if l['basis']=='ai_context_review_070' and l['decision']!='uncertain':
   n=nodes[k.split(':')[1]]
   out.append({'session':s['id'],'key':k,'d':l['decision'],'note':l['note'],'pivot':clean(n['text'])[:450],'targets':[{'id':t,'text':clean(nodes[t]['text'])[:500]} for t in l['targets']]})
  if l['decision']=='uncertain' and l['basis']!='ai_source_review_070':
   n=nodes[k.split(':')[1]];cs=s['suggestions'].get(k,[])[:8]
   extra.append({'session':s['id'],'key':k,'text':clean(n['text']),'candidates':[{'id':c['id'],'text':clean(nodes[c['id']]['text'])[:3200]} for c in cs]})
for i in range(0,len(out),30):(P/f'audit_model_{i//30+1}.json').write_text(json.dumps(out[i:i+30],ensure_ascii=False,indent=2),encoding='utf-8')
(P/'audit_extra_pending.json').write_text(json.dumps(extra,ensure_ascii=False,indent=2),encoding='utf-8')
print(len(out),len(extra))
