"""Apply saved analyst decisions; no classification heuristics or API calls."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent/'private'
for path in P.glob('root_review_*_*.tsv'):
    _,_,shard,batch=path.stem.split('_')
    folder=P/f'semantic_shard_{shard}'
    rows=json.loads((folder/f'batch_{int(batch):02}.json').read_text(encoding='utf-8'))
    decisions=[]
    for line in path.read_text(encoding='utf-8').splitlines():
        index,primary,secondary,confidence,reason,evidence=line.split('\t')
        src=rows[int(index)-1]
        ev=[] if evidence=='-' else [src['requests'][int(n)-1]['u'] for n in evidence.split(',')]
        decisions.append({'session_id':src['session_id'],'primary':primary,'secondary':[] if secondary=='-' else secondary.split(','),'confidence':confidence,'evidence_user':list(dict.fromkeys(ev)),'reason':reason,'review_basis':'digest','reviewer':'root_semantic_read'})
    assert len(decisions)==len(rows) and len({x['session_id'] for x in decisions})==len(rows),path
    (folder/f'result_{int(batch):02}.json').write_text(json.dumps(decisions,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(path.name,len(decisions))
