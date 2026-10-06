import json,re
from pathlib import Path
P=Path(__file__).resolve().parent/'private';d=json.loads((P/'review_data.json').read_text(encoding='utf-8'))
patterns={'7b0ea502fdac':('assistant','L1|L5|LLM|自主|去掉|重新发布'), '98d45aba0065':('assistant','英文|图片.*讲|图.*意思|English'), 'e5c7e28a572b':('both','word|Word|docx|成绩|签到|最终版本在哪'), 'b4c2962f1747':('assistant','创新点'), '079':('both','搞定了|白名单|扫码|登录成功'), 'a08c766fa806':('user','.'), '23':('assistant','技能|skill|论文')}
for s in d['sessions']:
 cfg=next((v for k,v in patterns.items() if s['id'][5:].startswith(k)),None)
 if not cfg:continue
 role,pat=cfg;out=[]
 for n in s['users']+s['assistants']:
  if role!='both' and n['role']!=role:continue
  if re.search(pat,n['text'],re.I):out.append({'id':n['id'],'text':n['text'][:1200]+(' [...] '+n['text'][-500:] if len(n['text'])>1200 else '')})
 (P/f'lookup_{s["id"][5:]}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('saved')
