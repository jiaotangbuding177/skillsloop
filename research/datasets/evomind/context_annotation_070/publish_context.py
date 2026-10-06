"""Build a new desk, honoring user labels and retaining a full reconciliation audit."""
from pathlib import Path
import json,copy,hashlib,collections,sys
R=Path(__file__).resolve().parent;P=R/'private';OLD=R.parent/'ai_annotation_069'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def main():
 data=read(OLD/'private/review_data.json');original=read(P/'user_backup_original.json');seed=copy.deepcopy(original);labels=seed['labels'];queries=read(P/'queries.json');new=set();missing=[]
 for j in read(P/'jobs.json'):
  f=P/'responses'/(j['id']+'.json')
  if f.exists():rows=read(f)['items']
  else:missing.append(j['id']);rows=[{'q':q['q'],'d':'U','t':[],'r':'本批尚无有效模型返回'} for c in j['cases'] for q in c['questions']]
  for row in rows:
   q=queries[str(row['q'])];sid=q['session'];key=q['key'];assert labels[sid][key].get('basis')!='human_explicit_selection'
   labels[sid][key]={'decision':{'M':'matched','N':'none','U':'uncertain'}[row['d']],'targets':row['t'],'note':row['r'],'basis':'ai_context_review_070','source_job':j['id'],'granularity':'deduplicated_content_group'};new.add((sid,key))
 overrides=read(P/'direct_review.json') if (P/'direct_review.json').exists() else []
 for row in overrides:
  sid=row['session'];key=row['key'];assert labels[sid][key].get('basis')!='human_explicit_selection'
  labels[sid][key]={'decision':row['decision'],'targets':row['targets'],'note':row['note'],'basis':'ai_source_review_070','granularity':'deduplicated_content_group'};new.add((sid,key))
 dump(P/'labels_before_reconciliation.json',labels)
 logs=[];conflicts=[]
 def priority(l):return 100 if l.get('basis')=='human_explicit_selection' else 90 if l.get('basis')=='ai_source_review_070' else 80 if l.get('basis')=='ai_context_review_070' else 10
 for s in data['sessions']:
  sid=s['id'];ls=labels[sid]
  # Process strongest evidence first. Explicit human targets also settle an uncertain opposite side.
  for key,l in sorted(list(ls.items()),key=lambda kv:priority(kv[1]),reverse=True):
   if l['decision']=='uncertain':continue
   role,nid=key.split(':',1);opp=s['assistants'] if role=='user' else s['users']
   for o in opp:
    ok=o['role']+':'+o['id'];ol=ls.get(ok)
    if not ol:continue
    edge=o['id'] in l['targets'];reverse=nid in ol['targets']
    if edge==reverse or (not edge and ol['decision']=='uncertain'):continue
    if ol['decision']=='uncertain' and priority(l)<90:continue
    if priority(l)<priority(ol):continue
    if priority(l)==priority(ol):
     if ol['decision']=='uncertain':continue
     conflicts.append({'session':sid,'left':key,'right':ok,'left_label':copy.deepcopy(l),'right_label':copy.deepcopy(ol)})
     if priority(l)==100:raise ValueError('Conflicting user labels')
     for ck in [key,ok]:
      prev=copy.deepcopy(ls[ck]);ls[ck]={**ls[ck],'decision':'uncertain','targets':[],'note':'本轮两方向判断存在具体分歧，需继续核对'};logs.append({'session':sid,'key':ck,'before':prev,'after':copy.deepcopy(ls[ck])})
     break
    before=copy.deepcopy(ol)
    if edge:
     ol['targets']=list(dict.fromkeys(ol['targets']+[nid]));ol['decision']='matched';ol['note']='按更高优先级的上下文/人工对应同步；'+ol['note']
    else:
     ol['targets']=[t for t in ol['targets'] if t!=nid]
     if not ol['targets']:ol['decision']='uncertain';ol['note']='原AI匹配被本轮具体上下文否定，需重新定位回复'
    logs.append({'session':sid,'key':ok,'before':before,'after':copy.deepcopy(ol)})
 dump(P/'reconciliation_log.json',logs);dump(P/'conflicts.json',conflicts)
 counts=collections.Counter();remaining=[]
 for s in data['sessions']:
  issues=[]
  for t in s['issues']:
   k=t['role']+':'+t['id'];l=labels[s['id']][k];counts[l['decision']]+=1
   if l['decision']=='uncertain':issues.append({'key':k,'reason':l['note']})
  if issues:remaining.append({'session_id':s['id'],'items':issues})
 human=[(sid,k,l) for sid,ls in original['labels'].items() for k,l in ls.items() if l.get('basis')=='human_explicit_selection']
 for sid,k,l in human:assert labels[sid][k]==l
 ledger=[json.loads(x) for x in (P/'request_ledger.jsonl').read_text(encoding='utf-8').splitlines()] if (P/'request_ledger.jsonl').exists() else []
 summary={**counts,'sessions':505,'items':2674,'human_labels_preserved':len(human),'initial_remaining_items':156,'initial_remaining_sessions':50,'remaining_human_items':counts['uncertain'],'sessions_needing_human':len(remaining),'sessions_resolved':505-len(remaining),'newly_resolved_net':156-counts['uncertain'],'jobs_without_response':len(missing),'api_attempts':len(ledger),'failed_attempts':sum(x['status']=='failed' for x in ledger),'reported_input_tokens':sum(sum(x.get('usage',{}).get(k,0) for k in ['input_tokens','cache_read_input_tokens','cache_creation_input_tokens']) for x in ledger),'reported_output_tokens':sum(x.get('usage',{}).get('output_tokens',0) for x in ledger),'direct_source_review_items':len(overrides),'independent_accuracy_measured':False}
 seed['ai_assistance_version']='070';data['seed']=seed;data['ai_summary']=summary
 dump(P/'ai_assisted_annotations.json',seed);dump(P/'review_data.json',data);dump(P/'remaining_human_review.json',remaining);dump(R/'summary.json',summary)
 core=(OLD/'annotation_core.js').read_text(encoding='utf-8');(R/'annotation_core.js').write_text(core,encoding='utf-8')
 template=(OLD/'review_ui_generated.html').read_text(encoding='utf-8').replace('evomind-annotation-069:', 'evomind-annotation-070:').replace('AI 已接手初标 · 默认仅显示仍需你判断的会话 · 你的原标注已保留','已结合新人工样例复核上下文 · 默认只看剩余项 · 51项人工选择已保留')
 text=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
 page=template.replace('/*__CORE__*/',core).replace('/*__DATA__*/',text);(P/'index.html').write_text(page,encoding='utf-8')
 dump(R/'manifest.json',{'html_sha256':hashlib.sha256((P/'index.html').read_bytes()).hexdigest(),'human_backup_sha256':hashlib.sha256((P/'user_backup_original.json').read_bytes()).hexdigest(),'source_dataset':data['fingerprint'],'prior_069_not_modified':True})
 print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
