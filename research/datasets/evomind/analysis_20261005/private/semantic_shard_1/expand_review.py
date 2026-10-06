import json,sys,re
from pathlib import Path
base=Path(__file__).parent
src=Path(r'D:\skillsgen-industry_track\research\datasets\evomind\matched_066\private\conversations')
b=sys.argv[1]; inds=[int(i) for i in sys.argv[2].split(',')]
batch=json.loads((base/f'batch_{b}.json').read_text(encoding='utf-8'))
lines=[]
for i in inds:
    sid=batch[i]['session_id']; d=json.loads((src/f'{sid}.json').read_text(encoding='utf-8'))
    lines += [f'## {i} {sid}']
    for j,u in enumerate(d['user_requests']):
        t=u['content']
        t=re.sub(r'(?:授权码|AppSecret|api[_ -]?key|apikey|password|密码)\s*(?:是|为)?[:：]?\s*[^\s，,。;；]+','[凭据已遮蔽]',t,flags=re.I)
        t=re.sub(r'(?<![A-Za-z0-9])[A-Za-z0-9]{16,}(?![A-Za-z0-9])','[长标识已遮蔽]',t)
        lines += [f"### {j} {u['group_id']}",t,'']
(base/f'expanded_{b}_{sys.argv[2]}.md').write_text('\n'.join(lines),encoding='utf-8')
print('expanded',len(inds))
