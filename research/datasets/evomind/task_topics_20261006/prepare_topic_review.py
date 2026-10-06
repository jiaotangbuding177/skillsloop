"""Prepare source-grounded research review cards; no classifier or model call."""
from pathlib import Path
import json,hashlib,re
R=Path(__file__).resolve().parent;P=R/'private';S=R.parent/'enriched_20261006'
def rows(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def short(s,n=85):
 s=re.sub(r'\s+',' ',s).strip()
 return s if len(s)<=n else s[:n*2//3]+'[…截…]'+s[-n//3:]
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def main():
 P.mkdir(parents=True,exist_ok=True)
 sessions=rows(S/'private/enriched_sessions.jsonl');candidates=rows(S/'private/candidate_contexts_union.jsonl');by={}
 for c in candidates:by.setdefault(c['session_id'],[]).append(c)
 included=[s for s in sessions if s['effective_screening_decision']!='EXCLUDE']
 cards=[]
 for i,s in enumerate(included,1):
  old=s['topic_annotation'];gm={m['group_id']:m for m in s['messages']};basis=[]
  for gid in old.get('evidence_user',[]):
   if gid in gm:basis.append({'group_id':gid,'excerpt':short(gm[gid]['content']),'truncated':len(re.sub(r'\s+',' ',gm[gid]['content']).strip())>85})
  cards.append({'review_index':i,'session_id':s['session_id'],'original_primary':old['primary'],'original_secondary':old.get('secondary',[]),'original_confidence':old['confidence'],'original_reason':old.get('reason',''),'original_review_basis':old.get('review_basis'), 'source_evidence':basis,'candidate_tasks':[{'candidate_id':c['candidate_id'],'task':c['task'],'method':c['learning_candidate'],'quote':c['evidence_quote']} for c in by.get(s['session_id'],[])],'screening':s['effective_screening_decision']})
 dump(P/'session_review_cards.json',cards)
 for start in range(0,len(cards),100):
  lines=[]
  for c in cards[start:start+100]:
   ev=' / '.join(b['excerpt'] for b in c['source_evidence'])
   tasks=' / '.join(x['task'] for x in c['candidate_tasks'])
   lines.append(f"{c['review_index']}|{c['original_primary']}|{','.join(c['original_secondary'])}|{c['original_reason']}|{ev}|候选:{tasks}")
  (P/f'review_{start//100+1:02}.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 clines=[]
 for i,c in enumerate(candidates,1):
  s=next(s for s in included if s['session_id']==c['session_id']);u=next(m for m in c['messages'] if m['role']=='user')
  clines.append(f"{i}|{s['topic_annotation']['primary']}|{c['task']}|{short(c['learning_candidate'],100)}|用户:{short(u['content'],70)}")
 for start in range(0,len(clines),100):(P/f'candidate_review_{start//100+1:02}.txt').write_text('\n'.join(clines[start:start+100])+'\n',encoding='utf-8')
 dump(P/'candidate_index.json',[{'review_index':i,'candidate_id':c['candidate_id'],'session_id':c['session_id']} for i,c in enumerate(candidates,1)])
 dump(R/'review_inputs_manifest.json',{'source_files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [S/'private/enriched_sessions.jsonl',S/'private/candidate_contexts_union.jsonl',S/'private/source_inputs.jsonl',S/'manifest.json']},'included_sessions':len(cards),'excluded_sessions':len(sessions)-len(cards),'candidate_count':len(candidates),'initial_review_view':'原主题理由+原依据用户文本首尾摘录+候选任务；不是全文审阅','source_title_used':False,'no_model_api_calls':True})
 print('Prepared',len(cards),'session cards and',len(candidates),'candidate cards')
if __name__=='__main__':main()
