from pathlib import Path
import json
root = Path('D:/skillloop/output/20261012_task_validator_suite')
audit = json.loads((root / 'audit/artifacts_tech.json').read_text('utf-8'))
data = json.loads(Path('D:/skillloop/output/20261012_evaluation_task_checkpoints/逐任务评测点明细.json').read_text('utf-8'))
byid = {c['session_id']: c for c in data['cases']}
for c in audit['tasks']:
    decisions = c['original_check_decisions']
    if any(p.get('action') not in ['keep', 'retain', 'replace'] for p in decisions):
        print(json.dumps({'session_id': c['session_id'], 'decisions': [p for p in decisions if p.get('action') not in ['keep','retain']], 'user_inputs': byid[c['session_id']]['users']},ensure_ascii=False))
