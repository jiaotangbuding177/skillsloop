from pathlib import Path
import json
data=json.loads(Path('D:/skillloop/output/20261012_evaluation_task_checkpoints/逐任务评测点明细.json').read_text('utf-8'))
for c in data['cases']:
 if c['session_id'] in {'conv_ab3863a19fb2','conv_470d66397a7d','conv_5785a8ce4b6a','conv_a196d952691c','conv_fcee61c6481d'}:
  print(json.dumps({'sid':c['session_id'],'input_files':c['input_files']},ensure_ascii=False))
