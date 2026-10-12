from pathlib import Path
import json
root = Path('D:/skillloop/output/20261012_task_validator_suite/audit')
data = json.loads((root / 'biz_edu_know.json').read_text('utf-8-sig'))
print('audit_shape', list(data)[:8] if isinstance(data, dict) else list(data[0]))
cases = data if isinstance(data, list) else data.get('tasks', data.get('cases', []))
if cases: print('case_keys', list(cases[0]))
machines = json.loads((root / 'biz_edu_know.machine_overrides.json').read_text('utf-8-sig'))
if 'overrides' in machines: machines = machines['overrides']
for sid, case in machines.items():
    extra = case.get('additions', [])
    changed_files = [c for c in case.get('replacements', []) if c['kind'] in ['file_delivery_open', 'delivered_file_open', 'final_file_native_open']]
    if extra or changed_files or case.get('additional_deliverables'):
        print(json.dumps({'sid': sid, 'file_changes': changed_files, 'additions': extra, 'new_deliveries': case.get('additional_deliverables', [])}, ensure_ascii=False))
