"""Private real-model acceptance: raw events only; no manual replyTo/task labels."""
import argparse
import json
import sys
import time
from pathlib import Path

DEMO=Path(__file__).resolve().parents[1]
PROJECT=DEMO.parents[1]
sys.path.insert(0,str(DEMO))
from skilldemo.core import Loop
from skilldemo.live import load_env
from skilldemo.runtime import OpenClawAgent

CASE=PROJECT/'research/cases/038_contract_multi_review'
SESSIONS=['conv_f586a09e7356','conv_011570125174','conv_60925fa3f733']

def source_events():
    index={r['messageId']:r for r in json.loads((CASE/'source_index.json').read_text(encoding='utf-8'))}
    rows=[json.loads(x) for x in (CASE/'private/raw_messages.jsonl').read_text(encoding='utf-8').splitlines() if x.strip()]
    out=[]
    for r in rows:
        meta=index[r['id']]
        files=(r.get('rawPayload') or {}).get('files') or []
        attachments=[{'name':f.get('name',f.get('fileName','unknown')) if isinstance(f,dict) else 'unknown','available':False,'basis':'EXPORT_METADATA_ONLY'} for f in files]
        out.append({k:r[k] for k in ('id','sessionId','role','content','status')} | dict(sourceOrder=meta['sourceLine'],sourceTimestamp=meta.get('userCreatedAt'),orderBasis='SOURCE_JSONL_ROW',attachments=attachments))
    return out

def control_events():
    turns=[('请审查合同甲的付款条款，指出延期付款风险。','合同甲应明确付款截止日和逾期利息。'),
           ('另外，写一份周五下午停电通知。','通知：本周五下午停电，请提前保存工作。'),
           ('回到合同甲，把付款截止日改成验收后30天，先只给修改文本。','合同甲付款条款：验收后30天内付款。'),
           ('审查另一份合同乙的保密条款；同时将刚才停电通知的时间改成周六上午。','合同乙保密条款需明确保密期限。通知修订为本周六上午停电。')]
    return [dict(id=f'control-{i}-{role}',sessionId='synthetic-ABA-multigoal',role=role,content=text,sourceOrder=i*2+j,status='done') for i,p in enumerate(turns,1) for j,(role,text) in enumerate(zip(('user','assistant'),p))]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,default=CASE/'private'/('047-stages123-'+str(int(time.time()))));ap.add_argument('--control-only',action='store_true');ap.add_argument('--daily-limit',type=int,default=8)
    args=ap.parse_args();load_env(DEMO/'.env')
    loop=Loop(args.data,OpenClawAgent(),settle_seconds=0,daily_limit=args.daily_limit,stage_pipeline=True)
    rows=source_events()
    init={'status':'KNOWN_NONE','basis':'User confirmed the historical enterprise agent had no skills; not inferred from missing receipts.'}
    if not args.control_only:
        for session in SESSIONS:
            loop.import_events('alice',[r for r in rows if r['sessionId']==session], 'holdout' if session==SESSIONS[2] else 'generation',init)
        print('Stage1 imported: 70 events, expected 14 pairs; starting real semantic calls.',flush=True)
        result=loop.run_stages('alice')
        print(json.dumps({'realStatuses':[{k:s.get(k) for k in ('stage2','stage3','error')} for s in result['sessions']]},ensure_ascii=False),flush=True)
    loop.import_events('bob',control_events(),'synthetic_control',{'status':'KNOWN_NONE','basis':'Synthetic fixture has no skills.'})
    print('Starting independent synthetic A-B-A / multi-goal control.',flush=True)
    loop.run_stages('bob')
    state=loop.snapshot('alice');control=loop.snapshot('bob')
    pairs=state['pairs'];traces=[t for t in state['traces'] if t['state']!='SUPERSEDED'];ct=control['traces']
    actual={s:sorted(sorted(t['pairIds']) for t in traces if t['session']==s) for s in SESSIONS}
    expected={}
    for s in SESSIONS:
        ps=sorted((p for p in pairs if p['session']==s),key=lambda p:p['sourceOrder'])
        expected[s]=sorted([sorted(p['id'] for p in ps[:-1]),[ps[-1]['id']]]) if s==SESSIONS[2] and ps else [sorted(p['id'] for p in ps)]
    a=next((t for t in traces if t['session']==SESSIONS[0]),{})
    cps=sorted(control['pairs'],key=lambda p:p['sourceOrder']);cgroups=sorted(sorted(cps.index(next(p for p in cps if p['id']==pid))+1 for pid in t['pairIds']) for t in ct)
    before=len(state['runs'])+len(control['runs']);loop.run_stages('alice');loop.run_stages('bob')
    after=len(loop.snapshot('alice')['runs'])+len(loop.snapshot('bob')['runs'])
    checks={
      'stage1_all70_source_ids':{i for p in pairs for i in p['sourceMessageIds']}=={r['id'] for r in rows},
      'stage1_14_pairs_56_assistant_ids':len(pairs)==14 and len({x['sourceId'] for p in pairs for x in p['assistantSegments']})==56,
      'stage2_all14_annotations':sum(s.get('annotationCount',0) for s in state['stageStatus'])==14,
      'stage2_expected_candidate_counts':sorted(s.get('taskSeedCount',0) for s in state['stageStatus'])==[1,1,2],
      'stage3_all_real_sessions_recovered':len(state['stageStatus'])==3 and all(s['stage3']=='RECOVERED' for s in state['stageStatus']),
      'stage3_expected_task_memberships':actual==expected,
      'stage3_unknown_business_outcomes':len(traces)==4 and all(t['businessOutcome']=='UNKNOWN' for t in traces),
      'stage3_a_question_not_rejection':any(e['kind']=='ASK_ABOUT_PRIOR_ADVICE' for e in a.get('feedbackEdges',[])),
      'stage3_a_delivery_change_scoped':any(e['kind']=='CHANGE_OUTPUT' and e['scope']=='CURRENT_DELIVERY' for e in a.get('feedbackEdges',[])),
      'stage3_a_option_ambiguity_preserved':any(e['kind']=='OPTION_RELATION_UNRESOLVED' for e in a.get('feedbackEdges',[])) or any(u['status']=='OPTION_REALIZATION_UNVERIFIED' for u in a.get('unresolved',[])),
      'stage3_no_unverified_file_promoted':bool(traces) and all(not t['artifactAvailability']['verifiedFiles'] for t in traces),
      'synthetic_interleaving_multigoal':cgroups==[[1,3],[2,4],[4]],
      'synthetic_return_annotated':any(f['kind']=='RETURN' for an in control['pairAnnotations'] for f in an['fragments']),
      'unchanged_replay_no_paid_calls':before==after,
      'no_generated_skills':not state['candidates'] and not control['candidates'],
    }
    summary={'case':'038 raw-event first-three-stage acceptance','checks':checks,'passed':all(checks.values()),'metrics':{'real':state['metrics'],'control':control['metrics']},'statuses':[{k:s.get(k) for k in ('session','stage2','stage3','error','taskSeedCount','traceCount')} for s in state['stageStatus']+control['stageStatus']], 'data':str(args.data),'callsTotal':after,'modelMode':loop.agent.mode,'syntheticControlNotEnterpriseEvidence':True}
    args.data.mkdir(parents=True,exist_ok=True)
    (args.data/'private-snapshots.json').write_text(json.dumps({'real':state,'control':control},ensure_ascii=False,indent=2),encoding='utf-8')
    (args.data/'acceptance-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)
    return 0 if summary['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
