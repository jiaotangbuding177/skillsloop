import json,sys
sys.stdout.reconfigure(encoding='utf-8')
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parent
labels=json.loads((R/'review_labels.json').read_text(encoding='utf-8'))
source=json.loads((R.parents[2]/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
assigned=json.loads((R/'assigned_ids.json').read_text(encoding='utf-8'))
errors=[]
for row in labels:
    sid=row['session_id']
    if sid not in assigned: errors.append([sid,'not_assigned'])
    raw={x['group_id']:x['content'] for x in source[sid]['user_requests']+source[sid]['assistant_contents']}
    if row['decision']=='KEEP' and not row['candidates']: errors.append([sid,'missing_candidates'])
    for c in row['candidates']:
        if not c['user_ids'] or not c['assistant_ids']: errors.append([sid,'missing_ids'])
        if not all(x in raw for x in c['user_ids']+c['assistant_ids']): errors.append([sid,'invalid_id'])
        elif not any(c['evidence_quote'] in raw[x] for x in c['user_ids']+c['assistant_ids']): errors.append([sid,'invalid_quote'])
        if len(c['evidence_quote'])<14: print('short',sid,c['evidence_quote'])
print('count',len(labels),'unique',len({x['session_id'] for x in labels}))
print('decisions',dict(Counter(x['decision'] for x in labels)))
print('basis',dict(Counter(x['review_basis'] for x in labels)))
print('errors',errors)
print('missing',len(set(assigned)-{x['session_id'] for x in labels}))
