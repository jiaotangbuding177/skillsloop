import json, re
from pathlib import Path
BASE=Path(__file__).parent
for p in BASE.glob('batch_*.json'):
    d=json.loads(p.read_text(encoding='utf-8'))
    lines=[]
    for i,r in enumerate(d):
        req=r['requests']; n=len(req)
        inds=list(range(n)) if n<=10 else sorted(set(list(range(4))+[round(x*(n-1)/5) for x in range(6)]+list(range(n-3,n))))
        texts=[]
        for j in inds:
            t=req[j]['text'].replace('\n',' / ')
            t=re.sub(r'(?<![A-Za-z0-9])[A-Za-z0-9]{16,}(?![A-Za-z0-9])','[标识遮蔽]',t)
            t=re.sub(r'\[附加文件:[^\]]*\]','[附件]',t)
            if len(t)>145:t=t[:105]+'[…摘要截取…]'+t[-35:]
            texts.append(f"({j}){t}")
        lines.append(f"{i}|{r['session_id']}|{n}条|"+' || '.join(texts))
    p.with_suffix('.compact.txt').write_text('\n'.join(lines),encoding='utf-8')
print('9 compact batches prepared')
