import json,sys,re
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
BASE=Path(__file__).parent
ROOT=BASE.parent
cards={x['session_id']:x for x in json.loads((ROOT/'all_cards.json').read_text(encoding='utf-8'))}
ids=json.loads((BASE/'assigned_ids.json').read_text(encoding='utf-8'))
def flat(s):return re.sub(r'\s+',' ',s)
source=None
def extras(indices):
 global source
 if source is None:source=json.loads((ROOT.parent.parent/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
 for idx in indices:
  sid=ids[idx];print('\nEXTRA',idx,sid)
  for i,a in enumerate(source[sid]['assistant_contents']):
   t=flat(a['content']);t=re.sub(r'(?i)(?:gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,})','[KEY]',t)
   t=re.sub(r'(?i)((?:api\s*key|access\s*key|secret\s*key|授权码|密码)\s*[:：=]\s*)\S+',r'\1[KEY]',t)
   snippets=[t[:160]]
   for pat in ['失败','不支持','错误','修复','限流','权限','缺少','水印','先确认','不是','改为','必须','字段']:
    m=re.search(pat,t)
    if m and m.start()>160:snippets.append(t[max(0,m.start()-30):m.start()+140])
   print(i,a['group_id'],' | '.join(snippets[:3]))
def show(start,count=25):
 for idx,sid in enumerate(ids[start:start+count],start):
  c=cards[sid]
  print(f"\n[{idx}] {sid} {c['topic_reason']} U{c['user_count']} A{c['assistant_count']} tool={c['tool_names']}")
  for i,u in enumerate(c['users']):
   t=flat(u['text']);print('U'+str(i)+': '+t[:125]+(' … '+t[-55:] if len(t)>125 else ''))
  for i,a in enumerate(c['assistant_evidence']):
   t=flat(a['text']);m=flat(' / '.join(a['method_lines']));print('A'+str(i)+': '+t[:200]+(' … '+t[-90:] if len(t)>200 else '')+' | '+m[:230])
def record(start,entries):
 f=BASE/'review_labels.json'
 prior=json.loads(f.read_text(encoding='utf-8')) if f.exists() else []
 labels={x['session_id']:x for x in prior}
 for off,e in enumerate(entries):
  sid=ids[start+off];c=cards[sid]
  decision,reason=e[0],e[1]
  out={'session_id':sid,'decision':decision,'reason_code':e[2] if len(e)>2 else ('NO_METHOD' if decision=='HOLD' else 'FACT_OR_CONTENT' if decision=='EXCLUDE' else 'REUSABLE_CONSTRAINT'),'reason':reason,'candidates':[],'review_basis':'card'}
  if decision=='KEEP':
   task,lesson,ui,ai,quote=e[3:8]
   out['candidates']=[{'task':task,'lesson':lesson,'user_ids':[c['users'][i]['id'] if isinstance(i,int) else i for i in ui],'assistant_ids':[c['assistant_evidence'][i]['id'] if isinstance(i,int) else i for i in ai],'evidence_quote':quote,'limitations':['关联为现有语义标注，不认证原始时间顺序','附件或实际交付与执行成效未核验']}]
   if len(e)>8:out['review_basis']=e[8]
  labels[sid]=out
 f.write_text(json.dumps([labels[s] for s in ids if s in labels],ensure_ascii=False,indent=2),encoding='utf-8')
 print('saved',len(labels))
if __name__=='__main__':
 if sys.argv[1]=='extra':extras([int(x) for x in sys.argv[2:]])
 else:show(int(sys.argv[1]),int(sys.argv[2]) if len(sys.argv)>2 else 25)
