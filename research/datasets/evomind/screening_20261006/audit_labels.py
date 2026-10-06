"""Offline validation of review coverage, source IDs and literal quotations."""
from pathlib import Path
from collections import Counter
import json,re,sys
R=Path(__file__).resolve().parent;P=R/'private'
source=json.loads((R.parent/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
compact=lambda t:re.sub(r'\s+','',t)
errors=[];coverage=[];decisions=[]
for shard in range(1,4):
    path=P/f'shard_{shard}/review_labels.json'
    if not path.exists():continue
    rows=json.loads(path.read_text(encoding='utf-8'));expected=json.loads((path.parent/'assigned_ids.json').read_text(encoding='utf-8'))
    tail=path.parent/'root_tail_labels.json'
    if tail.exists():
        seen={x['session_id'] for x in rows}
        rows += [x for x in json.loads(tail.read_text(encoding='utf-8')) if x['session_id'] not in seen]
    assert len({x['session_id'] for x in rows})==len(rows)
    coverage.append({'shard':shard,'read_sessions':len(rows),'assigned':len(expected),'counts':dict(Counter(x['decision'] for x in rows))})
    for row in rows:
        sid=row['session_id'];assert sid in expected;decisions.append(row)
        if (row['decision']=='KEEP')!=bool(row.get('candidates')):errors.append({'shard':shard,'session_id':sid,'problem':'处理标签和候选数量不一致'});continue
        s=source[sid];umap={x['group_id']:x['content'] for x in s['user_requests']};amap={x['group_id']:x['content'] for x in s['assistant_contents']}
        for n,c in enumerate(row.get('candidates',[]),1):
            uids=c.get('user_ids',[]);aids=c.get('assistant_ids',[])
            if not uids or any(i not in umap for i in uids) or any(i not in amap for i in aids):
                errors.append({'shard':shard,'session_id':sid,'candidate':n,'problem':'消息ID无效或未选用户正文'});continue
            text='\n'.join([umap[u] for u in uids]+[amap[a] for a in aids]);q=c.get('evidence_quote','')
            if not q or compact(q) not in compact(text):
                errors.append({'shard':shard,'session_id':sid,'candidate':n,'problem':'引用不是选定消息原文'})
dump={'coverage':coverage,'errors':errors,'source_ids_and_quotes_only':True,'semantic_accuracy_not_certified':True}
(R/'partial_validation.json').write_text(json.dumps(dump,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(dump,ensure_ascii=False))
