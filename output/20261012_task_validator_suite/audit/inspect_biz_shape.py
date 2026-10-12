from pathlib import Path
import json
p=Path('D:/skillloop/output/20261012_task_validator_suite/audit')
a=json.loads((p/'biz_edu_know.json').read_text('utf-8-sig'))
print(json.dumps(a[0]['original_checks'][0],ensure_ascii=False))
m=json.loads((p/'biz_edu_know.machine_overrides.json').read_text('utf-8-sig'))
print('kind_list',sorted({c['kind'] for v in m.values() for c in v['additions']}))
for sid,v in m.items():
 if v['additional_deliverables']:print(json.dumps({'sid':sid,'new':v['additional_deliverables']},ensure_ascii=False))
