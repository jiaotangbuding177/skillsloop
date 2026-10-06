import json,sys,pathlib,re,ast
sys.stdout.reconfigure(encoding='utf-8')
p=pathlib.Path(__file__).parent
root=p.parent.parent
cards={x['session_id']:x for x in json.loads((p.parent/'all_cards.json').read_text(encoding='utf-8'))}
ids=json.loads((p/'assigned_ids.json').read_text(encoding='utf-8'))
out=p/'tail17_19_review_labels.json'
raw=json.loads((root.parent/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
tree=ast.parse((root/'expand_review.py').read_text(encoding='utf-8'))
fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='redact')
scope={'re':re};exec(compile(ast.Module(body=[fun],type_ignores=[]),'<redact>','exec'),scope);redact=scope['redact']
if sys.argv[1]=='audit':
 rows=json.loads(out.read_text(encoding='utf-8'));print('coverage',len(rows))
 for r in rows:
  texts={x['group_id']:x['content'] for x in raw[r['session_id']]['user_requests']+raw[r['session_id']]['assistant_contents']}
  for c in r['candidates']:
   selected='\n'.join(texts.get(i,'') for i in c['user_ids']+c['assistant_ids'])
   if c['evidence_quote'] not in selected:print('NO_QUOTE',ids.index(r['session_id']),r['session_id'],redact(c['evidence_quote']))
   elif len(c['evidence_quote'])<10:print('SHORT',ids.index(r['session_id']),r['session_id'],redact(c['evidence_quote']))
   for i in c['user_ids']+c['assistant_ids']:
    if i not in texts:print('BAD_ID',r['session_id'],i)
elif sys.argv[1]=='save':
 rows=json.loads(out.read_text(encoding='utf-8')) if out.exists() else [];existing={x['session_id']:x for x in rows}
 for x in json.loads(pathlib.Path(sys.argv[2]).read_text(encoding='utf-8')):
  ix,d,reason=x[:3];c=cards[ids[ix]];cand=[]
  if d=='KEEP':
   task,lesson,uis,ais,q=x[3:]
   cand=[dict(task=task,lesson=lesson,user_ids=[c['users'][i]['id'] for i in uis],assistant_ids=[c['assistant_evidence'][i]['id'] for i in ais],evidence_quote=q,limitations=['原始时序未独立核验','附件与产物字节未提供','方法适用性及任务结果未独立验收'])]
  existing[c['session_id']]=dict(session_id=c['session_id'],decision=d,reason_code='METHOD_CONSTRAINT' if d=='KEEP' else 'INSUFFICIENT_METHOD' if d=='HOLD' else 'NO_LEARNING_TASK',reason=reason,candidates=cand,review_basis='card')
 out.write_text(json.dumps([existing[i] for i in ids if i in existing],ensure_ascii=False,indent=2),encoding='utf-8');print('saved',len(existing))
elif sys.argv[1]=='find':
 ix=int(sys.argv[2]);sid=ids[ix];print('SESSION',ix,sid)
 for a in raw[sid]['assistant_contents']:
  t=redact(a['content']);hits=[k for k in sys.argv[3:] if k in t]
  if hits:
   z=t.index(hits[0]);print('A',a['group_id'],t[max(0,z-100):z+900])
elif sys.argv[1] in ('source','ai','users'):
 for ix in map(int,sys.argv[2:]):
  sid=ids[ix];s=raw[sid];print('SESSION',ix,sid)
  if sys.argv[1]=='users':
   for j,u in enumerate(s['user_requests']):print(j,u['group_id'],redact(u['content'])[:200])
  else:
   for a in s['assistant_contents']:
    t=redact(a['content'])
    if sys.argv[1]=='ai':print('A',a['group_id'],t[:1300])
    else:
     z=[x for x in re.split(r'\n+',t) if len(x)>12 and re.search(r'错误|修复|改用|改为|原因|根因|失败|校验|不匹配|不能|必须|已调整|缺|失效|过期|问题|对比|手动|实际上|验证|缩|支持',x)]
     if z:print('A',a['group_id'],' | '.join(x[:150] for x in z[:2]))
