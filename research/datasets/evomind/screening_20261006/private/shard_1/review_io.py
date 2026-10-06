import json,sys,pathlib,os
sys.stdout.reconfigure(encoding='utf-8')
p=pathlib.Path(__file__).parent
cards=json.loads((p.parent/'all_cards.json').read_text(encoding='utf-8'))
ids=json.loads((p/'assigned_ids.json').read_text(encoding='utf-8'))
by={c['session_id']:c for c in cards}
if sys.argv[1] in ('read','brief'):
    start,end=int(sys.argv[2]),int(sys.argv[3])
    for i,sid in enumerate(ids[start:end],start):
        c=by[sid]
        print(i,sid,c['topic'],c['topic_reason'])
        seen={}
        for j,u in enumerate(c['users']):
            if sys.argv[1]=='brief' and u['text'] in seen: continue
            seen[u['text']]=j
            print('U'+str(j),u['text'].replace('\n',' ') if sys.argv[1]=='read' else u['text'].replace('\n',' ')[:95])
        for j,a in enumerate(c['assistant_evidence']):
            t=a['text'].replace('\n',' ')
            print('A'+str(j),t if sys.argv[1]=='read' else t[:100]+' … '+t[-60:],' | ', ' / '.join(a.get('method_lines',[])))
elif sys.argv[1]=='keys': print(by[ids[int(sys.argv[2])]].keys())
elif sys.argv[1]=='save':
    data=json.loads(sys.argv[2])
    rows=json.loads((p/'review_labels.json').read_text(encoding='utf-8')) if (p/'review_labels.json').exists() else []
    existing={r['session_id']:r for r in rows}
    for x in data:
        idx,d,reason=x[:3]; c=by[ids[idx]]; cand=[]
        if d=='KEEP':
            task,lesson,uis,ais,quote=x[3:]
            cand=[dict(task=task,lesson=lesson,user_ids=[c['users'][j]['id'] for j in uis],assistant_ids=[c['assistant_evidence'][j]['id'] for j in ais],evidence_quote=quote,limitations=['原始时序未独立核验','附件与产物字节未提供','方法适用性及任务结果未独立验收'])]
        existing[c['session_id']]=dict(session_id=c['session_id'],decision=d,reason_code=('METHOD_CONSTRAINT' if d=='KEEP' else 'INSUFFICIENT_METHOD' if d=='HOLD' else 'NO_LEARNING_TASK'),reason=reason,candidates=cand,review_basis='card')
    (p/'review_labels.json').write_text(json.dumps([existing[i] for i in ids if i in existing],ensure_ascii=False,indent=2),encoding='utf-8')
    print('saved',len(existing))
