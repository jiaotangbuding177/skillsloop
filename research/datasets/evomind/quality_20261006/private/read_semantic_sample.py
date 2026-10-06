import sys,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
source=R.parents[1]/'enriched_20261006/private/candidate_contexts_union.jsonl'
rows=[json.loads(s) for s in source.read_text(encoding='utf-8').splitlines()]
rows.sort(key=lambda x:x['candidate_id'])
regular=rows[::24]
supp=[r for r in rows if r['candidate_id'].endswith(':supp01')]
selected={r['candidate_id']:r for r in regular}
selected.update({r['candidate_id']:r for r in supp})
samples=sorted(selected.values(),key=lambda x:x['candidate_id'])
selection={'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'population':len(rows),'rule':'候选编号排序后索引0,24,...固定30条，另加全部8个supp01，去重',
 'systematic_sample_count':len(regular),'targeted_supplement_count':len(supp),
 'unique_sample_count':len(samples),'not_unbiased_accuracy_estimate':True,
 'samples':[{'rank':i+1,'candidate_id':r['candidate_id'],'session_id':r['session_id'],
 'selection_components':[k for k,a in [('systematic',regular),('targeted_supplement',supp)] if any(x['candidate_id']==r['candidate_id'] for x in a)],
 'message_count':len(r['messages']),'message_chars':sum(len(m['content']) for m in r['messages'])} for i,r in enumerate(samples)]}
(R/'sample_selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8')
start,end=map(int,sys.argv[1:3])
for rank,r in enumerate(samples,1):
 if not start<=rank<=end: continue
 print('\n### SAMPLE',rank,r['candidate_id'])
 for k in ['task','learning_candidate','evidence_quote','limitations']:
  print(k+':',r[k])
 for m in r['messages']:
  print('\n',m['role'],m['group_id'],'inclusion',m['inclusion'],'active',m['learning_active'],'FULL',len(m['content']))
  print(m['content'])
