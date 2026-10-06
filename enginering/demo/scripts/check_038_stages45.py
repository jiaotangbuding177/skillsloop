"""Real-model stage-4/5 acceptance from the frozen 047 database.

Full enterprise records stay in the private destination. The stdout summary has
IDs, statuses and usage only. The optional demo acceptance is operator action,
not evidence of enterprise user adoption.
"""
import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

DEMO=Path(__file__).resolve().parents[1]
PROJECT=DEMO.parents[1]
sys.path.insert(0,str(DEMO))
from skilldemo.core import Loop
from skilldemo.live import load_env
from skilldemo.runtime import OpenClawAgent

SOURCE=PROJECT/'research/cases/038_contract_multi_review/private/047-stages123-network/loop.sqlite'
DEFAULT=PROJECT/'research/cases/038_contract_multi_review/private/049-stages45-acceptance'


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',type=Path,default=DEFAULT)
    ap.add_argument('--daily-limit',type=int,default=30)
    ap.add_argument('--adopt-for-demo',action='store_true')
    ap.add_argument('--consume',action='store_true')
    ap.add_argument('--retry-creator',action='store_true',help='Only explicit one-time retry of an already failed creator candidate')
    ap.add_argument('--finalize-existing',action='store_true',help='Revalidate completed creator draft without a model call')
    args=ap.parse_args()
    load_env(DEMO/'.env')
    args.data.mkdir(parents=True,exist_ok=True)
    dest=args.data/'loop.sqlite'
    if not dest.exists():
        with sqlite3.connect(SOURCE) as source,sqlite3.connect(dest) as target:source.backup(target)
    loop=Loop(args.data,OpenClawAgent(),settle_seconds=0,daily_limit=args.daily_limit,
              pool_wait_seconds=0,stage_pipeline=True)
    before=loop.snapshot('alice')
    existing={t['id']:t for t in before['traces'] if t.get('schemaVersion')=='task-trace-v2'}
    generation={t['id'] for t in existing.values() if t.get('purposeSplit')=='generation'}
    holdout={t['id'] for t in existing.values() if t.get('purposeSplit')=='holdout'}
    if len(generation)!=2 or len(holdout)!=2:raise RuntimeError('047来源快照任务数异常，停止验收')
    candidates=loop.discover('alice')
    stage4=loop.snapshot('alice')
    workflows=[w for w in stage4['workflows'] if w['action']=='NEW']
    decisions=[json.loads(r[0]) for r in sqlite3.connect(dest).execute("SELECT data FROM records WHERE kind='learning_decision' AND owner='alice'")]
    stage4_ok=bool(workflows and decisions) and all(set(r['id'] for r in w['sourceRefs'])<=generation for w in workflows)
    stage4_ok &= all(t.get('decision') is None for t in stage4['traces'] if t['id'] in holdout)
    stage4_ok &= all(d['methodLedger'] and d['analysisId'] and d['mergeId'] for d in decisions)
    if not stage4_ok:raise RuntimeError('阶段4来源/方法台账验收未通过；不启动creator')
    ready=[c for c in stage4['candidates'] if c.get('workflowId') and c['status'] in ('READY','INSTALLED')]
    if args.finalize_existing:
        from skilldemo.workflow_bridge import finalize_existing
        failed=[c for c in stage4['candidates'] if c.get('workflowId') and c['status']=='FAILED']
        if not failed:raise RuntimeError('没有可复核的已完成creator草稿')
        created=finalize_existing(loop,'alice',failed[0]['id'])
    elif not ready:
        available=candidates
        if args.retry_creator:
            failed=[c for c in stage4['candidates'] if c.get('workflowId') and c['status']=='FAILED']
            if not failed:raise RuntimeError('没有可显式重试的阶段5失败候选')
            available=[loop.retry_candidate('alice',failed[0]['id'])]
        if not available:raise RuntimeError('阶段4未形成NEW候选')
        target=max(available,key=lambda c:(len(c['input']['traces']),len(c['input']['workflow'].get('includedMethodIds',[]))))
        created=loop.generate('alice',target['id'])
    else:created=ready[0]
    stage5=loop.snapshot('alice')
    check5=created['status'] in ('READY','INSTALLED') and bool(created.get('files')) and bool(created.get('package'))
    check5 &= created.get('validation',{}).get('creatorRead',{}).get('status')=='FILE_READ'
    check5 &= created.get('validation',{}).get('officialPackage',{}).get('status')=='PASS'
    check5 &= len(stage5['skills'])==len(before['skills'])
    if not check5:raise RuntimeError('阶段5封装未通过，候选与运行记录已保留: '+str(created.get('error','')))
    accepted=None;consumed=None
    if args.adopt_for_demo:
        accepted=loop.accept('alice',created['id'])
        if args.consume:
            sample='请使用选中的技能，审阅这个构造的付款条款，只给风险说明与建议文本，不要声称改动了文件：买方验收后六十日内支付价款；逾期处理方式暂未约定。'
            consumed=loop.chat('alice','049-synthetic-consumption-'+str(int(time.time())),sample,[accepted['id']])
            read=any(s.get('id')==accepted['id'] and s.get('status')=='FILE_READ' for s in consumed.get('skillEvidence',{}).get('skills',[]))
            if consumed['status']!='COMPLETED' or not read:raise RuntimeError('新任务执行或技能实际读取未通过，记录已保留')
    result={'stage4Passed':stage4_ok,'stage5Passed':check5,'generationTraceCount':len(generation),
            'holdoutTraceCount':len(holdout),'workflowCount':len(workflows),'workflowIds':[w['id'] for w in workflows],
            'decisionIds':[d['id'] for d in decisions],
            'candidateId':created['id'],'candidateStatus':created['status'],
            'filePaths':[f['path'] for f in created['files']],'archiveSha256':created['package']['sha256'],
            'demoAdoption':accepted['id'] if accepted else None,
            'demoConsumption':{'turnId':consumed['id'],'skillRead':'FILE_READ'} if consumed else None,
            'metricsBefore':before['metrics'],'metricsAfter':loop.metrics('alice'),
            'privateDataRoot':str(args.data),'enterpriseOutcome':'UNKNOWN',
            'operatorAdoptionIsNotEnterpriseEvidence':True}
    (args.data/'acceptance-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':main()
