import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=ROOT/'private'
rs=json.loads((p/'skills_by_evidence.json').read_text(encoding='utf-8'))
ts=json.loads((p/'normalized_skill_tools.json').read_text(encoding='utf-8'))
source=json.loads((ROOT.parent/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
pat=re.compile(r'https?://[^\s<>"\x27)]+')
out=[]
for r in rs:
    snippets=[]
    for sid,s in source.items():
        for g in s['user_requests']:
            text=g.get('content',g.get('text',''))
            if not isinstance(text,str):continue
            if r['skill'].lower() in text.lower() and re.search('安装|下载|纳入|github|clawhub|skills add',text,re.I):
                snippets.append({'session_id':sid,'group_id':g['group_id'],'text':text[:1800]})
    out.append({'skill':r['skill'],'paths':sorted(set(q['path'] for i in r['evidence_indices'] for q in ts[i].get('paths',[]))),'urls':sorted(set(u for i in r['evidence_indices'] for u in pat.findall(str(ts[i]['output'])) if 'github.com' in u or 'clawhub' in u)),'user_install_context':snippets})
(p/'provenance_probe.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
for x in out:
    print(json.dumps({'skill':x['skill'],'paths':x['paths'][:3],'urls':x['urls'][:8],'install_context':x['user_install_context'][:2]},ensure_ascii=False))
