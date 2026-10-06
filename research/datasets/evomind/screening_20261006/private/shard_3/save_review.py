import json,sys
from pathlib import Path
R=Path(__file__).resolve().parent
BASE=R.parent.parent
cards={x['session_id']:x for x in json.loads((R.parent/'all_cards.json').read_text(encoding='utf-8'))}
ids=json.loads((R/'assigned_ids.json').read_text(encoding='utf-8'))
src=json.loads((BASE.parent/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
def save(batch,rows):
    current=json.loads((R/'review_labels.json').read_text(encoding='utf-8')) if (R/'review_labels.json').exists() else []
    labels={x['session_id']:x for x in current}
    chunk=ids[(batch-1)*25:batch*25]
    assert len(chunk)==len(rows),(batch,len(chunk),len(rows))
    for sid,row in zip(chunk,rows):
        c=cards[sid]
        status=row[0]
        reason=row[1]
        cand=[]
        if status=='KEEP':
            # Row body: task, lesson, exact quote, user indexes, assistant indexes or exact ids.
            task,lesson,quote,ui,ai=row[2:7]
            uids=[c['users'][i]['id'] if isinstance(i,int) else i for i in ui]
            aids=[c['assistant_evidence'][i]['id'] if isinstance(i,int) else i for i in ai]
            raw={x['group_id']:x['content'] for x in src[sid]['user_requests']+src[sid]['assistant_contents']}
            assert all(x in raw for x in uids+aids),(sid,uids,aids)
            assert any(quote in raw[x] for x in uids+aids),(sid,quote)
            cand=[dict(task=task,lesson=lesson,user_ids=uids,assistant_ids=aids,evidence_quote=quote,limitations=['历史执行顺序未核准','任务成功及新任务复用收益未独立验证'])]
        labels[sid]=dict(session_id=sid,decision=status,reason_code='PROCEDURAL_EVIDENCE' if status=='KEEP' else 'INSUFFICIENT_LEARNING_EVIDENCE' if status=='HOLD' else 'NO_REUSABLE_TASK_EVIDENCE',reason=reason,candidates=cand,review_basis='expanded' if len(row)>7 and row[7]=='expanded' else 'card')
    out=[labels[sid] for sid in ids if sid in labels]
    (R/'review_labels.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('saved',batch,len(out))

if __name__=='__main__':
    import runpy
    scope=runpy.run_path(sys.argv[1]);save(scope['batch'],scope['rows'])
