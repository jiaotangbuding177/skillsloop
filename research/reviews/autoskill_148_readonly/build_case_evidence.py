"""Offline evidence extraction from completed files. No network or model invocation."""
import json,re
from pathlib import Path
root=Path('D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill')
out=Path(__file__).parent
data={g:json.loads((root/'runs/test_v4'/f'{n}.json').read_text(encoding='utf-8')) for g,n in [('B0','no_skill'),('B1','autoskill_library')]}
(out/'recorded_retail_policy.md').write_text(data['B1']['info']['environment_info']['policy'],encoding='utf-8')
selected={('49',0),('97',3),('55',1),('111',0),('39',2),('60',0)}
evidence={'audit_mode':'Offline read-only; writes reviews directory only','message_index_convention':'zero-based index in source simulations[].messages','cases':[],'learning_sources':[],'provenance':[]}
for tid,trial in sorted(selected,key=lambda x:(int(x[0]),x[1])):
 item={'task_id':tid,'trial':trial,'groups':{}}
 for g,d in data.items():
  ix,s=next((i,x) for i,x in enumerate(d['simulations']) if x['task_id']==tid and x['trial']==trial)
  messages=[]
  for i,m in enumerate(s['messages']):
   c=m.get('content','')
   if m['role']=='tool':
    try:
     obj=json.loads(c)
     if isinstance(obj,dict) and ('order_id' in obj or 'user_id' in obj):
      c=json.dumps({k:v for k,v in obj.items() if k in ['order_id','user_id','status','items','orders','payment_history','exchange_items','exchange_new_items','return_items','cancel_reason']},ensure_ascii=False)
     else: continue
    except (ValueError,TypeError):
     if not (isinstance(c,str) and c.startswith('Error:')): continue
   messages.append({'index':i,'role':m['role'],'content':c,'tool_calls':m.get('tool_calls')})
  item['groups'][g]={'source_file':str(root/'runs/test_v4'/('no_skill.json' if g=='B0' else 'autoskill_library.json')),'simulation_index':ix,'simulation_id':s['id'],'seed':s['seed'],'termination_reason':s['termination_reason'],'reward_info':s['reward_info'],'messages':messages}
 evidence['cases'].append(item)
collect=json.loads((root/'runs/collect/evolution.json').read_text(encoding='utf-8'))
tasks={t['id']:t for t in collect['tasks']}
for tid in ['0','50','96']:
 ix,s=next((i,x) for i,x in enumerate(collect['simulations']) if x['task_id']==tid)
 calls=[{'message_index':i,'calls':m['tool_calls']} for i,m in enumerate(s['messages']) if m.get('tool_calls')]
 evidence['learning_sources'].append({'task_id':tid,'raw_file':str(root/'runs/collect/evolution.json'),'simulation_index':ix,'simulation_id':s['id'],'seed':s['seed'],'termination_reason':s['termination_reason'],'reward_info':s['reward_info'],'tool_calls':calls,'evaluation_criteria':tasks[tid].get('evaluation_criteria'),'trajectory_file':str(root/'autoskill_input/trajectories'/f'task_{tid}.txt')})
provfile=root/'autoskill_state/skillbank_trajectory/index/online_skill_provenance_tau_retail_pool_v2.json'
prov=json.loads(provfile.read_text(encoding='utf-8'))
for sid,s in prov['skills'].items():
 for h in s['history']:
  if re.search(r'Title: task_(50|96)\.txt',h.get('latest_user_preview','')):
   evidence['provenance'].append({'file':str(provfile),'skill_id':sid,'current_name':s['name'],'version':h['version'],'timestamp':h['timestamp'],'source_key':h['source_key'],'message_hash':h['message_hash'],'description':h['description'],'metadata':h.get('metadata'),'version_timeline_tail':h['version_timeline_tail']})
(out/'case_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
short=[]
for s in evidence['learning_sources']:
 short.append({k:v for k,v in s.items() if k!='evaluation_criteria'})
print(json.dumps(short,ensure_ascii=False,indent=2))
for x in evidence['provenance']: print(x['current_name'],x['version'],x['source_key'],x['message_hash'])
