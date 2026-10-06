import json,re,sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parents[3]
old=R/'screening_20261006/private'
labels=json.loads((old/'screening_decisions.json').read_text(encoding='utf-8'))
print('labels_type',type(labels).__name__)
if isinstance(labels,dict):
    print('keys',list(labels)[:10]); labels=list(labels.values())
cards={x['session_id']:x for x in json.loads((old/'all_cards.json').read_text(encoding='utf-8'))}
topics={x['session_id']:x for x in json.loads((R/'analysis_20261005/private/session_task_categories.json').read_text(encoding='utf-8'))}
pool=[]
for row in labels:
    if row.get('decision')!='HOLD': continue
    sid=row['session_id'];c=cards[sid]
    if not pool: print('card_keys',list(c));print('count_keys',c.get('counts'))
    uc=len(c['users']);ac=c['assistant_count']
    omitted=ac-len(c['assistant_evidence'])
    user_text='\n'.join(x['text'] for x in c['users'])
    ai_text='\n'.join(x['text']+'\n'+'\n'.join(x.get('method_lines',[])) for x in c['assistant_evidence'])
    correction=len(re.findall(r'不对|错误|错了|重新|修正|还是|没有|不满意|缺少|漏|不是|改成|改为|太|换|不要',user_text))
    diagnosis=len(re.findall(r'报错|错误|失败|超时|缺少|未安装|依赖|权限|格式|乱码|根因|渲染|解析|冲突|无法|受限|不兼容',ai_text))
    basis=row.get('review_basis','card')
    score=min(omitted,100)*0.7+min(correction,20)*3+min(diagnosis,10)*4+(12 if basis=='card' else 0)
    pool.append(dict(session_id=sid,title=c.get('topic_reason',''),topic=topics.get(sid,{}).get('primary',''),users=uc,assistant=ac,omitted=omitted,correction=correction,diagnosis=diagnosis,old_basis=basis,score=score,old_reason=row.get('reason','')))
pool.sort(key=lambda x:(-x['score'],x['session_id']))
(Path(__file__).parent/'ranked_hold_pool.json').write_text(json.dumps(pool,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('pool',len(pool))
for i,x in enumerate(pool[:65]): print(i+1,x['session_id'],x['topic'],x['users'],x['assistant'],x['correction'],x['diagnosis'],x['old_basis'],x['old_reason'])
