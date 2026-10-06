import json,sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parent
C={x['session_id']:x for x in json.loads((R.parent/'all_cards.json').read_text(encoding='utf-8'))}
ids=json.loads((R/'assigned_ids.json').read_text(encoding='utf-8'))
for arg in sys.argv[1:]:
 b=int(arg);print('BATCH',b)
 for j,sid in enumerate(ids[(b-1)*25:b*25]):
  x=C[sid];print(j+1,sid,x['topic_reason'],'U',x['user_count'],'A',x['assistant_count'],'omitted',x['omitted_assistant_groups'])
  seen={}
  for i,u in enumerate(x['users']):
   t=u['text'].replace('\n',' ')
   print('u'+str(i),'同u'+str(seen[t]) if t in seen else t)
   seen.setdefault(t,i)
  for i,a in enumerate(x['assistant_evidence']):print('a'+str(i),a['text'].replace('\n',' '),'LINE', ' / '.join(a['method_lines']))
