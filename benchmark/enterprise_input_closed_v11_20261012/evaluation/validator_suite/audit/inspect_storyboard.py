from pathlib import Path
import json
d=json.loads(Path('D:/skillloop/output/20261012_evaluation_task_checkpoints/逐任务评测点明细.json').read_text('utf-8'))
c=next(c for c in d['cases'] if c['session_id']=='conv_a196d952691c')
for u in c['users']:
 if u['index'] in [1,2]:print(u['text'][:4800])
