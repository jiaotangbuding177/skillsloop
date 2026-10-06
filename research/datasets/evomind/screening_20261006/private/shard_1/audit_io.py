import json,re,sys,pathlib,ast
sys.stdout.reconfigure(encoding='utf-8')
p=pathlib.Path(__file__).parent
root=p.parent.parent
raw=json.loads((root.parent/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
cards={c['session_id']:c for c in json.loads((p.parent/'all_cards.json').read_text(encoding='utf-8'))}
ids=json.loads((p/'assigned_ids.json').read_text(encoding='utf-8'))
rows=json.loads((p/'review_labels.json').read_text(encoding='utf-8'))
labels={r['session_id']:r for r in rows}
redactor_src=(root/'expand_review.py').read_text(encoding='utf-8').replace('    return re.sub',' return re.sub')
tree=ast.parse(redactor_src)
fun=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='redact')
scope={'re':re};exec(compile(ast.Module(body=[fun],type_ignores=[]),'<redact>','exec'),scope)
redact=scope['redact']
def source_text(s):return {x['group_id']:x['content'] for x in s['user_requests']+s['assistant_contents']}
def dump():
 (p/'review_labels.json').write_text(json.dumps([labels[x] for x in ids if x in labels],ensure_ascii=False,indent=2),encoding='utf-8')
if sys.argv[1]=='newquotes':
 for ix in [7,32,108,179,254,263,385]:
  r=labels[ids[ix]];texts=source_text(raw[ids[ix]]);print('SESSION',ix)
  for c in r['candidates']:
   for aid in c['assistant_ids']:
    print('A',aid,redact(texts.get(aid,''))[:1800])
elif sys.argv[1]=='links':
 todo={248:['合同','批注'],257:['TTFA','标语'],258:['系列','体检'],261:['Word','只提取'],318:['缺','文字'],330:['记忆','最新'],350:['160','采购'],412:['专利','集团'],419:['prompt','提示词'],430:['模板'],438:['公园','墓'],447:['状态'],456:['整机','四个'],469:['名次','排序'],194:['五步','三步']}
 for ix,ks in todo.items():
  print('SESSION',ix,ids[ix]);hit=[]
  for a in raw[ids[ix]]['assistant_contents']:
   t=redact(a['content']);h=[k for k in ks if k in t]
   if h and not re.search(r'技能.*(?:创建|沉淀)|经验.*(?:已写入|已记录)',t[:80]):
    pos=t.index(h[0]);hit.append((a['group_id'],t[max(0,pos-40):pos+330]))
  for a,t in hit[-3:]:print('A',a,t)
elif sys.argv[1]=='find':
 ix=int(sys.argv[2]);sid=ids[ix];print('SESSION',ix,sid)
 hits=[]
 for a in raw[sid]['assistant_contents']:
  t=redact(a['content']);ks=[k for k in sys.argv[3:] if k in t]
  if ks:
   pos=t.index(ks[0]);hits.append((a['group_id'],t[max(0,pos-70):pos+450]))
 for a,t in hits[-5:]:print('A',a,t)
elif sys.argv[1]=='merge':
 for r in json.loads((p/'root_tail_labels.json').read_text(encoding='utf-8')):labels[r['session_id']]=r
 dump();print('merged',len(labels))
elif sys.argv[1]=='audit':
 import collections
 print('counts',dict(collections.Counter(r['decision'] for r in labels.values())))
 for i,sid in enumerate(ids):
  if sid not in labels:continue
  r=labels[sid];texts=source_text(raw[sid])
  for c in r['candidates']:
   sel='\n'.join(texts.get(x,'') for x in c['user_ids']+c['assistant_ids'])
   if c['evidence_quote'] not in sel:print('NO_QUOTE',i,sid,redact(c['evidence_quote']))
   elif len(c['evidence_quote'])<10:print('SHORT',i,sid,redact(c['evidence_quote']))
   for x in c['user_ids']+c['assistant_ids']:
    if x not in texts:print('BAD_ID',i,sid,x)
 print('long nonkeep',[(i,sid,len(raw[sid]['assistant_contents'])) for i,sid in enumerate(ids) if sid in labels and labels[sid]['decision']!='KEEP' and len(raw[sid]['assistant_contents'])>10])
elif sys.argv[1]=='source':
 for ix in map(int,sys.argv[2:]):
  sid=ids[ix];s=raw[sid];print('\nSESSION',ix,sid)
  for a in s['assistant_contents']:
   t=redact(a['content'])
   paras=[z for z in re.split(r'\n+',t) if len(z)>12 and re.search(r'错误|不一致|修复|纠正|改用|改为|原因|根因|失败|漏|校验|公式|不匹配|不能|必须|已调整|缺|失效|过期|问题|改正|对比|手动|实际上|验证',z,re.I)]
   if paras:print('A',a['group_id'],' | '.join(z[:160] for z in paras[:2]))
elif sys.argv[1]=='ai':
 ix=int(sys.argv[2]);sid=ids[ix];print('SESSION',ix,sid)
 for a in raw[sid]['assistant_contents']:
  if len(sys.argv)<4 or any(k in a['content'] for k in sys.argv[3:]):print('A',a['group_id'],redact(a['content'])[:2500])
elif sys.argv[1]=='quotes':
 proposals=[]
 for ix,sid in enumerate(ids[:475]):
  r=labels[sid];texts=source_text(raw[sid])
  for ci,c in enumerate(r['candidates']):
   q='除了参会人员' if ix==421 else c['evidence_quote']
   if len(q)>=10:continue
   hits=[texts[x] for x in c['user_ids']+c['assistant_ids'] if q in texts.get(x,'')]
   if not hits:continue
   t=hits[0];pos=t.index(q);left=t.rfind('\n',0,pos)+1;end=t.find('\n',pos+len(q));end=len(t) if end<0 else end
   if end-left>180:left=max(left,pos-35);end=min(end,pos+len(q)+70)
   if end-left<10:end=min(len(t),end+100)
   nq=t[left:end].strip()
   proposals.append([ix,ci,nq])
   print(ix,redact(q),'→',redact(nq))
 (p/'quote_proposals.json').write_text(json.dumps(proposals,ensure_ascii=False,indent=2),encoding='utf-8')
elif sys.argv[1]=='applyquotes':
 for ix,ci,q in json.loads((p/'quote_proposals.json').read_text(encoding='utf-8')):labels[ids[ix]]['candidates'][ci]['evidence_quote']=q
 dump();print('quotes updated')
