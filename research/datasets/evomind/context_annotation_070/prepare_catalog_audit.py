import json,re
from pathlib import Path
P=Path(__file__).resolve().parent/'private';d=json.loads((P/'review_data.json').read_text(encoding='utf-8'))
both=['1484e8af3800','98d45aba0065','271afc5da7d7','da7d6a0140d5','0e5f49df8fb6','f128041d3dc7','010ad4ece7b3','8dbc2e14c3fc']
usersonly=['a49d5bb92bc6','fcee61c6481d','a08c766fa806','58cbbc1e3d0a','2007f7ec09fb']
for s in d['sessions']:
 short=s['id'][5:]
 if short not in both+usersonly:continue
 out=[]
 for n in s['users']+(s['assistants'] if short in both else []):
  t=re.sub(r'^\[[^\]]+\]\s*','',n['text']);t=t.replace('请使用中文回复，除非用户明确使用其他语言。','').strip()
  if n['role']=='user' and len(t)>1000:t=t[:220]+' [...] '+t[-500:]
  elif len(t)>650:t=t[:450]+' [...] '+t[-180:]
  out.append({'id':n['id'],'text':t})
 (P/f'catalog_{short}.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print('catalogs saved')
