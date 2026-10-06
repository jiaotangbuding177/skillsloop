"""Offline concise audit of discordant wins; writes only this reviews directory."""
import json
from pathlib import Path
root=Path('D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill')
out=Path(__file__).parent
groups={g:json.loads((root/'runs/test_v4'/f'{n}.json').read_text(encoding='utf-8')) for g,n in [('B0','no_skill'),('B1','autoskill_library')]}
tasks={x['id']:x for x in groups['B0']['tasks']}
pairs={}
for g,data in groups.items():
 for s in data['simulations']: pairs.setdefault((s['task_id'],s['trial']),{})[g]=s
lines=['# Existing discordant wins: local audit digest','']
losses=['# Existing discordant losses: local audit digest','']
for (tid,trial),p in sorted(pairs.items(),key=lambda x:(int(x[0][0]),x[0][1])):
 if p['B0']['reward_info']['reward']==p['B1']['reward_info']['reward']: continue
 target=lines if p['B1']['reward_info']['reward']==1 else losses
 saved=lines
 lines=target
 lines += [f'## task {tid} trial {trial}', 'Private scenario (not learner-visible): '+json.dumps(tasks[tid]['user_scenario'],ensure_ascii=False),'']
 for g,s in p.items():
  lines += [f'### {g} seed {s["seed"]} sim {s["id"]}', '']
  for i,m in enumerate(s['messages']):
   if m['role']=='tool':
    c=m.get('content','')
    if isinstance(c,str) and (c.startswith('Error:') or 'not found' in c.lower()): lines += [f'[{i}] tool {c}','']
    continue
   c=json.dumps(m['tool_calls'],ensure_ascii=False) if m.get('tool_calls') else str(m.get('content',''))
   lines += [f'[{i}] {m["role"]}: {c}','']
 lines=saved
(out/'wins_digest.md').write_text('\n'.join(lines),encoding='utf-8')
(out/'losses_digest.md').write_text('\n'.join(losses),encoding='utf-8')
print('Saved',len(lines),'lines')
