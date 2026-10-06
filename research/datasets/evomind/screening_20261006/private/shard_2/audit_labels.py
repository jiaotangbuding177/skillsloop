import json
from pathlib import Path
b=Path(__file__).resolve().parents[3]
src=json.loads((b/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
p=Path(__file__).parent/'review_labels.json'
labels=json.loads(p.read_text(encoding='utf-8'))
for row in labels:
 s=src[row['session_id']]
 u={x['group_id']:x['content'] for x in s['user_requests']}
 a={x['group_id']:x['content'] for x in s['assistant_contents']}
 for c in row['candidates']:
  for gid in c['user_ids']:
   if gid not in u: print('BAD_U',row['session_id'],gid)
  for gid in c['assistant_ids']:
   if gid not in a: print('BAD_A',row['session_id'],gid)
  selected='\n'.join(u.get(g,'') for g in c['user_ids'])+'\n'+'\n'.join(a.get(g,'') for g in c['assistant_ids'])
  if c['evidence_quote'] not in selected:
   print('BAD_QUOTE',row['session_id'],c['evidence_quote'])
   found=[g for g,t in {**u,**a}.items() if c['evidence_quote'] in t]
   print('SOURCE_IDS',found)
print('coverage',len(labels))
