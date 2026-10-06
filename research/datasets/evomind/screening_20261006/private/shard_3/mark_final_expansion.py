import json
from pathlib import Path
R=Path(__file__).resolve().parent
p=R/'review_labels.json'
data=json.loads(p.read_text(encoding='utf-8'))
for row in data:
    if row['session_id']=='conv_3091cd80dbb4': row['review_basis']='expanded'
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
