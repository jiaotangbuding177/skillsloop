import json,pathlib,re
R=pathlib.Path(__file__).resolve().parent
obj=json.loads((R/'bench_public_domain_evidence.json').read_text(encoding='utf-8'))
rows=[]
for x in obj['records']:
    fp=(R/'bench_readmes'/x['instance_id'].replace('/','__')).with_suffix('.txt')
    if not fp.exists():
        rows.append(x['instance_id']+' | README not retrieved')
        continue
    lines=fp.read_text(encoding='utf-8',errors='replace').splitlines()
    plain=[]
    for line in lines:
        line=line.strip()
        if not line or any(t in line.lower() for t in ('badge','shields.io','<img','<svg','<!--','[![','data:image','license','copyright','====','----')):continue
        if line.startswith(('https://','http://','![','[','|','```','<','* [','- [')):continue
        if len(line)>400:line=line[:400]
        plain.append(line)
        if sum(len(z) for z in plain)>350:break
    rows.append(x['instance_id']+' | '+' / '.join(plain)[:420])
(R/'bench_readme_briefs.txt').write_text('\n'.join(rows)+'\n',encoding='utf-8')
print('briefs',len(rows))
