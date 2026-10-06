import json,hashlib,sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
R=Path(__file__).resolve().parent
pool=json.loads((R/'ranked_hold_pool.json').read_text(encoding='utf-8'))
selection={
 'selection_id':'hold_supplement_20261006_25',
 'population':'旧版516条HOLD会话',
 'selection_method':'固定线索优先目的抽样；非随机抽样，不估计整体召回率',
 'ranking_rule':'0.7*min(未在卡片展示的AI数,100)+3*min(用户纠正线索数,20)+4*min(AI诊断线索数,10)+12*(原审阅为card)',
 'tie_breaker':'会话编号字典序',
 'limit':25,
 'scope':'逐条定向复读正文；全保留正负判断；不因未找到方法替换会话，不改变旧版分类',
 'status':'selection_frozen_before_supplemental_review',
 'sessions':[dict(rank=i+1,selection_reason='长AI未展示、用户纠正或工具诊断线索优先；是否存在可学习方法留待原文复核',**x) for i,x in enumerate(pool[:25])]
}
(R/'selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('frozen',len(selection['sessions']))
for x in selection['sessions']: print(x['rank'],x['session_id'],x['title'])
