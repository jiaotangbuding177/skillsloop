"""Explicit, bounded real-model lifecycle acceptance; never a business benchmark."""
import argparse
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skilldemo.core import Loop
from skilldemo.live import load_env
from skilldemo.runtime import OpenClawAgent

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ('将结果写入 outputs/summary.json（数值字段 net_revenue、current_refunds、cross_period_refunds）、'
          'outputs/report.csv 和 outputs/report.md。必须用Python计算并实际创建文件，最终回答简要列出文件。')

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',default='artifacts/a024')
    args=parser.parse_args()
    load_env(ROOT/'.env')
    os.environ.setdefault('DEMO_AGENT_TIMEOUT','300')
    root=Path(args.data).resolve();root.mkdir(parents=True,exist_ok=True)
    record=root/'acceptance.json'
    report=json.loads(record.read_text(encoding='utf-8')) if record.exists() else {
        'kind':'controlled-real-model-acceptance', 'enterpriseData':False, 'benchmark':False,'steps':{}}
    loop=Loop(root,OpenClawAgent(),settle_seconds=0,daily_limit=4)
    def save():record.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    def step(name,operation):
        if name in report['steps']:return report['steps'][name]
        print('START '+name,flush=True)
        value=operation();report['steps'][name]=value;save();print('PASS '+name,flush=True);return value
    def chat(actor,session,message,skills,request,expected):
        t=loop.chat(actor,session,message,skills,request)
        assert t['status']=='COMPLETED',t.get('error',t['status'])
        for filename in ('summary.json','report.csv','report.md'):
            assert any(a['path'].replace('\\','/')=='outputs/'+filename for a in t['artifacts']),filename
        p=loop.store.root/'workspaces'/t['runId']/'outputs/summary.json'
        values=json.loads(p.read_text(encoding='utf-8-sig'))
        for k,v in expected.items():assert values[k]==v,(k,values[k],v)
        if skills:assert all(s['readEvidence']=='FILE_READ' for s in t['skills'])
        return {'turnId':t['id'],'runId':t['runId'],'values':values,'skills':t['skills'],'artifacts':t['artifacts']}
    def learn(action):
        loop.tick();loop.discover('alice')
        candidates=[c for c in loop.snapshot('alice')['candidates'] if c['action']==action]
        assert len(candidates)==1,[(c['action'],c['status']) for c in candidates]
        c=loop.generate('alice',candidates[0]['id'])
        assert c['status'] in ('READY','INSTALLED'),c.get('error',c['status'])
        result=next(r['result'] for r in loop.snapshot('alice')['runs'] if r['id']==c['runId'])
        assert result.get('package'), 'Official creator package missing'
        assert any(t['name']=='read' and t['status']=='SUCCEEDED' and 'skill-creator' in json.dumps(t['arguments'])
                   for t in result['skillEvidence']['tools']), 'Creator was not read'
        assert any(f['path'].startswith('scripts/') for f in c['files']), 'Reusable helper missing'
        return {'candidateId':c['id'],'runId':c['runId'],'package':result['package'],'files':[f['path'] for f in c['files']]}
    try:
        step('source',lambda:chat('alice','source',
            '整理销售周报：本期销售100元，同期退款10元，跨期退款5元。必须先核对退款期间，再从本期销售扣除同期退款；跨期退款单独列示，不重复扣除。'
            '请将通用计算方法写成Python函数，后续同类任务能复用。'+OUTPUT,[], 'source',
            {'net_revenue':90,'current_refunds':10,'cross_period_refunds':5}))
        new=step('generate',lambda:learn('NEW'))
        s=step('personal',lambda:loop.accept('alice',new['candidateId']))
        step('reuse_v1',lambda:chat('alice','reuse',
            '整理销售周报：本期销售240元，同期退款30元，跨期退款7元。请按选中技能口径处理。'+OUTPUT,[s['id']],'reuse',
            {'net_revenue':210,'current_refunds':30,'cross_period_refunds':7}))
        def support():
            loop.tick();assert not loop.discover('alice')
            t=next(t for t in loop.snapshot('alice')['traces'] if t['session']=='reuse')
            assert t['decision']['action']=='SUPPORT';return t['decision']
        step('support_without_generation',support)
        step('correction',lambda:chat('alice','reuse',
            '不对，必须先排除已取消订单，再计算收入。之前的退款期间规则保持不变。补充通用规则：状态为cancelled的销售不能计入。'
            '请用修订数据重新整理：本期completed销售200元，cancelled销售50元，同期退款20元，跨期退款7元。'+OUTPUT,[s['id']],'correction',
            {'net_revenue':180,'current_refunds':20,'cross_period_refunds':7}))
        update=step('generate_update',lambda:learn('UPDATE'))
        v2=step('accept_v2',lambda:loop.accept('alice',update['candidateId']))
        assert v2['id']==s['id'] and v2['version']==2 and v2['hash']!=s['hash']
        proposal=step('submit',lambda:loop.submit('alice',update['candidateId']))
        shared=step('approve',lambda:loop.review('reviewer',proposal['id'],True))
        assert all(x['id']!=shared['id'] for x in loop.snapshot('outsider')['skills'])
        step('reuse_org',lambda:chat('bob','org-task',
            '整理销售周报：本期completed销售300元，cancelled销售40元，同期退款25元，跨期退款9元。按选中技能规则处理。'+OUTPUT,
            [shared['id']],'org-task',{'net_revenue':275,'current_refunds':25,'cross_period_refunds':9}))
        report.update(passed=True,metrics={a:loop.metrics(a) for a in ('alice','bob')})
    except Exception as exc:
        report.update(passed=False,error=str(exc));raise
    finally:
        save()
        for actor in ('alice','bob','reviewer'):
            (root/(actor+'-snapshot.json')).write_text(json.dumps(loop.snapshot(actor),ensure_ascii=False,indent=2),encoding='utf-8')
    print('ACCEPTED '+str(record),flush=True)

if __name__=='__main__':main()
