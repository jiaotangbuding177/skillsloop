"""Read-only source mapping audit of existing provenance JSON."""
import json
from pathlib import Path
root=Path('D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill')
out=Path(__file__).parent
p=json.loads((root/'autoskill_state/skillbank_trajectory/index/online_skill_provenance_tau_retail_pool_v2.json').read_text(encoding='utf-8'))
lines=['# Existing skill provenance summaries','']
for sid,s in p['skills'].items():
 lines += [f'## {s["name"]} {sid}', 'Keys: '+', '.join(s),'']
 for k,v in s.items():
  if k in ['version_timeline','usage_stats']: continue
  if isinstance(v,(list,dict)): lines += [f'### {k}',json.dumps(v,ensure_ascii=False,indent=2),'']
  else: lines += [f'{k}: {v}','']
(out/'provenance_digest.md').write_text('\n'.join(lines),encoding='utf-8')
print('Top keys',list(p))
short=['# Skill source/version mapping','']
for sid,s in p['skills'].items():
 print(s['name'],list(s))
 short += ['## '+s['name'], '']
 for x in s['sources']:
  short += [f'{x.get("last_version")}: {x.get("latest_user_preview")}', '']
 short += ['First history entry keys: '+str(list(s['history'][0])),json.dumps(s['history'][0],ensure_ascii=False,indent=2),'']
(out/'source_version_map.md').write_text('\n'.join(short),encoding='utf-8')
