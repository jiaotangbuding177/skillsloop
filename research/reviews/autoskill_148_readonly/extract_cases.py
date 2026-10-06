"""Read-only extraction from frozen 148 artifacts; writes this review directory only."""
import json
from pathlib import Path

ROOT = Path('D:/skillsgen-industry_track/research/experiments/148_tau2_retail_autoskill')
OUT = Path(__file__).parent
GROUPS = {'B0': 'no_skill', 'B1': 'autoskill_library'}
SELECTED = {'111', '39', '60', '38', '64', '108'}
loaded = {g: json.loads((ROOT / 'runs/test_v4' / (n + '.json')).read_text(encoding='utf-8')) for g, n in GROUPS.items()}
tasks = {t['id']: t for t in loaded['B0']['tasks']}
paired = {}
for group, data in loaded.items():
    for sim in data['simulations']:
        if sim['task_id'] in SELECTED:
            paired.setdefault((sim['task_id'], sim['trial']), {})[group] = sim
evidence = {'scope': 'Existing completed v4 results only; no API or experiment execution.', 'source_files': {g: str(ROOT / 'runs/test_v4' / (n + '.json')) for g,n in GROUPS.items()}, 'cases': []}
lines = ['# 148 v4 case extraction (all indices zero-based)', '']
for (task_id,trial), pair in sorted(paired.items(), key=lambda z: (int(z[0][0]),z[0][1])):
    rewards = {g: s['reward_info']['reward'] for g,s in pair.items()}
    print(task_id, trial, rewards, {g:s['seed'] for g,s in pair.items()})
    if trial == 0:
        print('TASK', json.dumps(tasks[task_id]['user_scenario'], ensure_ascii=False))
    # Capture every discordant pair and one shared-zero example for task 38.
    if rewards['B0'] == rewards['B1'] and not (task_id == '38' and trial == 0):
        continue
    case = {'task_id': task_id, 'trial': trial, 'task': tasks[task_id], 'groups': {}}
    lines += [f'## task {task_id}, trial {trial}: {rewards}', '', '### User scenario (private evaluator context; excluded from learner input)', json.dumps(tasks[task_id]['user_scenario'], ensure_ascii=False), '']
    for group, sim in pair.items():
        case['groups'][group] = {k:sim.get(k) for k in ['id','seed','termination_reason','reward_info','messages','start_time','end_time','duration']}
        lines += [f'### {group}: seed={sim["seed"]}, sim={sim["id"]}', '', 'Reward details:', json.dumps(sim['reward_info'], ensure_ascii=False), '']
        for i,m in enumerate(sim['messages']):
            text = m.get('content')
            if m.get('tool_calls'):
                text = json.dumps(m['tool_calls'], ensure_ascii=False)
            lines += [f'[{i}] {m.get("role")} ({m.get("id", "")})', str(text), '']
    evidence['cases'].append(case)
(OUT/'case_extraction.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'case_extraction.md').write_text('\n'.join(lines),encoding='utf-8')
digest = ['# Concise case evidence; message indices are zero-based', '']
for case in evidence['cases']:
    if (case['task_id'],case['trial']) not in {('38',2),('39',2),('60',0),('64',1),('111',0)}:
        continue
    digest += [f'## task {case["task_id"]}, trial {case["trial"]}', '']
    for group, sim in case['groups'].items():
        r=sim['reward_info']
        digest += [f'### {group} seed={sim["seed"]} sim={sim["id"]}',f'Reward={r["reward"]}, db={r.get("db_check")}, nl={r.get("nl_assertions")}', '']
        for i,m in enumerate(sim['messages']):
            if m['role']=='tool':
                text=m.get('content','')
                if isinstance(text,str) and not text.startswith('{'):
                    digest += [f'[{i}] tool: {text}', '']
                continue
            text=m.get('content')
            if m.get('tool_calls'):
                text=json.dumps(m['tool_calls'],ensure_ascii=False)
            digest += [f'[{i}] {m["role"]}: {text}', '']
(OUT/'case_digest.md').write_text('\n'.join(digest),encoding='utf-8')
print('WROTE', OUT/'case_extraction.md', len(lines))
