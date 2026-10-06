"""Bounded real-model functional acceptance with constructed, disclosed inputs."""
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from skilldemo.core import Loop
from skilldemo.runtime import OpenClawAgent
from skilldemo.live import load_env

load_env(ROOT/'.env')
root=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'artifacts/031-multitrace-live'
if (root/'acceptance.json').exists():
    print('Existing completed acceptance retained; no model dispatch.',flush=True)
    raise SystemExit(0)
loop=Loop(root,OpenClawAgent(),settle_seconds=0,idle_seconds=0,daily_limit=4)

def save(stage, obj):
    root.mkdir(parents=True,exist_ok=True)
    (root/(stage+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print(stage, json.dumps({k:v for k,v in obj.items() if k in ('status','id','error','passed','members')},ensure_ascii=False),flush=True)

for name, text, checks, answer in [
    ('success','整理销售报告，必须先按订单号去重再汇总，金额单位为元。',[{'name':'去重','expected':100,'actual':100}],'两条重复订单各100元，按订单号去重后100元。'),
    ('failure','整理销售报告，必须排除取消订单；发生重复计入时先检查状态再汇总。',[{'name':'取消订单排除','expected':100,'actual':120}],'已算出120元，但包含20元取消订单，评估失败。'),
    ('unknown','整理销售报告，必须将跨期退款单独列示，不从本期净收入扣除。',[],'先按期间分组，再分别展示本期净额与跨期退款。')]:
    loop.import_turn('alice',{'session':'031-'+name,'requestId':name,'user':text,'assistant':answer,'checks':checks})
loop.tick();loop.discover('alice')
candidates=loop.snapshot('alice')['candidates']
first=next(c for c in candidates if c['action']=='NEW')
assert len(first['input']['traces'])==3
first=loop.generate('alice',first['id']);save('01-new',first)
if first['status'] not in ('READY','INSTALLED'): raise SystemExit('NEW未通过，保留证据，不自动重试')
skill=loop.accept('alice',first['id'])
message='整理销售报告。期间2026-09，金额单位元。订单A已完成100，重复订单A已完成100，订单B已完成80，订单C已取消20；本期退款10，跨期退款30。请读取技能，以Python计算并将结果JSON写入outputs/result.json，字段net、cross_period_refund。'
turn=loop.chat('alice','031-consume',message,[skill['id']],request_id='consume-v1');save('02-consume',turn)
assert turn['status']=='COMPLETED'
art=next(a for a in turn.get('artifacts',[]) if a['path'].replace('\\','/')=='outputs/result.json')
result=json.loads(loop.artifact('alice',turn['runId'],art['path']).read_text(encoding='utf-8-sig'))
assert result['net']==170 and result['cross_period_refund']==30,result
assert turn['skills'][0]['readEvidence']=='FILE_READ'
# Two independent actual uses of the same frozen version feed an UPDATE pool.
second=loop.chat('alice','031-consume-2','整理销售报告。订单D已完成200，本期退款20，跨期退款5。请读取技能，用Python将net和cross_period_refund写入outputs/result.json。',[skill['id']],request_id='consume-v1-b');save('03-consume',second)
assert second['status']=='COMPLETED'
loop.import_turn('alice',{'session':'031-consume','requestId':'fix-1','user':'不对，输出必须同时列出gross和current_refund，保留原net及cross_period_refund。','assistant':'后续报告会补齐字段。','replyTo':turn['id']})
loop.import_turn('alice',{'session':'031-consume-2','requestId':'fix-2','user':'不对，输出必须同时列出currency，固定为CNY；保留原有金额字段。','assistant':'后续报告会标注币种。','replyTo':second['id']})
loop.tick();loop.discover('alice')
update=next(c for c in loop.snapshot('alice')['candidates'] if c['action']=='UPDATE')
assert len(update['input']['traces'])==2
update=loop.generate('alice',update['id']);save('04-update',update)
assert update['status'] in ('READY','INSTALLED'),update.get('error')
new=loop.accept('alice',update['id'])
sub=loop.submit('alice',update['id']);org=loop.review('reviewer',sub['id'],True)
last=loop.chat('bob','031-shared','整理销售报告，按技能将JSON写入outputs/result.json。已完成订单E=300，F=50，本期退款25，跨期退款15，期间2026-09。',[org['id']],request_id='consume-v2');save('05-shared',last)
assert last['status']=='COMPLETED'
last_art=next(a for a in last['artifacts'] if a['path'].replace('\\','/')=='outputs/result.json')
out=json.loads(loop.artifact('bob',last['runId'],last_art['path']).read_text(encoding='utf-8-sig'))
assert out['net']==325 and out['gross']==350 and out['current_refund']==25 and out['currency']=='CNY' and out['cross_period_refund']==15,out
assert last['skills'][0]['readEvidence']=='FILE_READ'
save('acceptance',{'passed':True,'source':'constructed fixtures + real model; not enterprise benchmark',
    'newPoolMembers':3,'updatePoolMembers':2,'initialAnalysts':[e['analyst'] for e in first['input']['evidence']],
    'v1Result':result,'v2Result':out,'metricsAlice':loop.metrics('alice'),'metricsBob':loop.metrics('bob')})
