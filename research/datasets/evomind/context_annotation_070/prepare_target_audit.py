import json,re
from pathlib import Path
P=Path(__file__).resolve().parent/'private';d=json.loads((P/'review_data.json').read_text(encoding='utf-8'))
spec={
'a49d5bb92bc6':['a_c97a6e0345875293e3'],
'7b0ea502fdac':['a_78c148d6bf9e3e9c9c','u_4982e77571c4001ad6','u_e14e9b26ac1aba92b1'],
'e5c7e28a572b':['a_bd451f4e41b5a3731a','u_2a9b8d6fb68b5af0e8'],
'8e704f119abe':['a_205f7a19184f4fa49a','a_244f8eff3f8e2a8a04'],
'a08c766fa806':['a_0763bdc2a7bb006d74','a_5b329c442ee1d6fb6a'],
'129e16e6d449':['a_dfbf13ce243a841f9b','a_1205683'],
'0e5f49df8fb6':['a_b53c3a31463445ebf2'],
'079':['u_3741fe3eb02bd4528b'],
'ae3627d8a84b':['a_6632faf7568e262eaa','a_bfc02c5227bb319ae1','a_8de7fef5ce5d0c8ec8','a_3b6e49a16de37db106']}
for s in d['sessions']:
 short=s['id'][5:]; needles=next((v for k,v in spec.items() if short.startswith(k)),None)
 if not needles:continue
 nodes=sorted(s['users']+s['assistants'],key=lambda x:min(o['line'] for o in x['occurrences']))
 indices={j for i,n in enumerate(nodes) if any(n['id'].startswith(z) for z in needles) for j in range(max(0,i-3),min(len(nodes),i+4))}
 out=[{'id':nodes[i]['id'],'text':nodes[i]['text'][:1600]} for i in sorted(indices)]
 (P/f'target_{short}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('saved')
