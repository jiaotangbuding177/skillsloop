from pathlib import Path
import csv,json,re
R=Path(__file__).resolve().parent; PROJECT=R.parents[3]
report=PROJECT/'research/reports/2026-10-05_local_evaluation_readiness_and_trace2skill.md'
text=report.read_text(encoding='utf-8')
table=text.split('| 优先级 | 要交什么 |')[1].split('\n\n')[0]
lines=[l for l in table.splitlines()[2:] if l.startswith('|')]
rows=[[c.strip() for c in l.strip('|').split('|')] for l in lines]
assert len(rows)==17 and all(len(x)==5 for x in rows)
target=R/'evaluation_supply_checklist.csv'
with target.open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f);w.writerow(['优先级','要交什么','已有部分与缺口','查询来源','交付标准','数据方填写交付位置','数据方填写缺失原因'])
 # The source table has five columns; validation below intentionally checks its schema.
 w.writerows([*x,'',''] for x in rows)
