import json,re
from pathlib import Path
R=Path(__file__).resolve().parent
ts=json.loads((R/'private/normalized_skill_tools.json').read_text(encoding='utf-8'))
rs=json.loads((R/'private/skills_by_evidence.json').read_text(encoding='utf-8'))
source=json.loads((R.parent/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
def flat(x):
    if isinstance(x,str):return x
    if isinstance(x,list):return '\n'.join(flat(y) for y in x)
    if isinstance(x,dict):return '\n'.join(flat(x[k]) for k in ['text','content','output','stdout','stderr'] if k in x)
    return ''
for r in rs:
    texts=[flat(ts[i]['output']) for i in r['evidence_indices']]
    text=max(texts,key=len,default='').replace('\\n','\n').replace('\\r','')
    lines=[l for l in text.splitlines() if re.search(r'license:|author:|source:|repository:|原生|内置|EvoMind|zzz4ai|github.com|版权所有',l,re.I)]
    print(r['skill'],json.dumps(lines[:4],ensure_ascii=False))
for name in ['guizang-ppt-skill','follow-builders','nuwa-skill','AutoEvoSkillCreate']:
    row=next(r for r in rs if r['skill']==name)
    owners={source[s]['owner_id'] for s in row['session_ids']}
    print('INSTALL',name)
    for sid,s in source.items():
        for g in s['user_requests']:
            text=g['content']
            if name.lower() in text.lower() and 'github.com/' in text and len(text)<1200 and re.search('安装|装一下',text):
                print(json.dumps({'sid':sid,'same_session_consumption':sid in row['session_ids'],'same_owner_consumption':s['owner_id'] in owners,'group':g['group_id']},ensure_ascii=False))
