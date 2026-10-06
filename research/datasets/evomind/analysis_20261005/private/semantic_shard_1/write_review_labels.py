import json, sys
from pathlib import Path
BASE=Path(__file__).parent
n=sys.argv[1]
source=json.loads((BASE/f'batch_{n}.json').read_text(encoding='utf-8'))
rows=(BASE/f'manual_labels_{n}.txt').read_text(encoding='utf-8').splitlines()
assert len(rows)==len(source),(len(rows),len(source))
out=[]
for r,line in zip(source,rows):
    a=line.split('|')
    primary,secondary,conf,j,reason=a[:5]
    inds=[int(v) for v in j.split(',')]
    assert all(0<=i<len(r['requests']) for i in inds),(r['session_id'],j,len(r['requests']))
    score=float(conf)
    out.append(dict(session_id=r['session_id'],primary=primary,secondary=secondary.split(',') if secondary else [],confidence='high' if score>=.8 else 'medium' if score>=.6 else 'low',evidence_user=[r['requests'][i]['u'] for i in inds],reason=reason,review_basis=a[5] if len(a)>5 else 'digest'))
(BASE/f'result_{n}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'Written {len(out)} reviewed labels')
