from pathlib import Path
import json,importlib.util
R=Path(__file__).resolve().parent;P=R/'private'
sp=importlib.util.spec_from_file_location('ctx',R/'run_context_review.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
d=json.loads((P/'review_data.json').read_text(encoding='utf-8'));ss={s['id']:s for s in d['sessions']};pack=json.loads((P/'direct_review_packets.json').read_text(encoding='utf-8'))
for i in [1,2,4,6,8,9,13,22,25,26,30,31,32,33,34,35,46]:
 row=pack[i-1];s=ss[row['session']];nodes=s['users']+s['assistants'];n=next(x for x in nodes if x['id']==row['key'].split(':')[1]);lines=[x['line'] for x in n['occurrences']]
 dist=lambda o:min(abs(x['line']-l) for x in o['occurrences'] for l in lines)
 near=sorted(nodes,key=dist)[:9]
 out={'i':i,'target':row['text'],'all_users':[{'id':x['id'],'text':m.clean(x['text'])[:600]} for x in s['users']],'neighbors':[{'id':x['id'],'text':m.clean(x['text'])[:850],'lines':[o['line'] for o in x['occurrences']]} for x in near]}
 (P/('near_'+str(i)+'.json')).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
