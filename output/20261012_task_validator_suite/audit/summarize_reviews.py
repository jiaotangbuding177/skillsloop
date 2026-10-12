from pathlib import Path
import collections
import json

root = Path('D:/skillloop/output/20261012_task_validator_suite/audit')
for group in ['artifacts_tech', 'legal_hr_services', 'biz_edu_know']:
    file = root / (group + '.json')
    if not file.is_file():
        print(group + ': pending')
        continue
    value = json.loads(file.read_text('utf-8-sig'))
    cases = value if isinstance(value, list) else value.get('tasks', value.get('cases', []))
    print(json.dumps({'group': group, 'top_keys': list(value) if isinstance(value, dict) else 'list', 'tasks': len(cases), 'case_keys': list(cases[0]), 'statuses': dict(collections.Counter(c.get('audit_status', '') for c in cases))}, ensure_ascii=False))
    for case in cases:
        original = case.get('original_check_decisions', case.get('original_checks', case.get('points', [])))
        changed = [p for p in original if p.get('action') not in ['keep', 'retain', None]]
        additions = case.get('approved_new_checks', case.get('new_checks', case.get('additions', case.get('proposed_checks', []))))
        observations = case.get('observations', [])
        if changed or additions:
            print(json.dumps({'session_id': case['session_id'], 'changed': changed, 'additions': additions}, ensure_ascii=False))
