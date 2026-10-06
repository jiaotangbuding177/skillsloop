"""Real-model stage-2 acceptance on the private 038 contract case.

Uses the 70 selected source rows, not the diagnostic import view with synthetic
replyTo. T3 is inspected only for task boundaries; no skill learning is run.
"""
import argparse
import json
from pathlib import Path
import sys
import time

DEMO = Path(__file__).resolve().parents[1]
PROJECT = DEMO.parents[1]
sys.path.insert(0, str(DEMO))

from skilldemo.core import Loop
from skilldemo.detection import _redact
from skilldemo.live import load_env
from skilldemo.runtime import OpenClawAgent

CASE = PROJECT / 'research/cases/038_contract_multi_review'


def source_turns():
    messages = {row['id']:row for row in (json.loads(line) for line in
        (CASE/'private/raw_messages.jsonl').open(encoding='utf-8'))}
    tracks = json.loads((CASE/'recovered_trajectories.json').read_text(encoding='utf-8'))
    for track in tracks:
        for turn in track['turns']:
            user = messages[turn['userMessageId']]
            assistant = '\n\n'.join(messages[i]['content'] for i in turn['assistantMessageIds'])
            yield {'session':track['sessionId'],'requestId':turn['userMessageId'],
                   'sourceUserMessageId':turn['userMessageId'],
                   'sourceTimestamp':turn['userTimestampUtc'],'user':user['content'],
                   'assistant':assistant,'status':'COMPLETED'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data',type=Path,default=DEMO/'artifacts'/('038-detection-'+str(int(time.time()))))
    parser.add_argument('--env-file',type=Path,default=DEMO/'.env')
    args = parser.parse_args()
    load_env(args.env_file)
    agent = OpenClawAgent()
    health = agent.health()
    if not (health.get('installed') and health.get('modelConfigured')):
        raise SystemExit('真实OpenClaw模型尚未就绪；仅保留本地数据，不回退合成结果')
    loop = Loop(args.data,agent,settle_seconds=0,daily_limit=3,task_detection=True,stage_pipeline=False)
    for turn in source_turns(): loop.import_turn('alice',turn)
    loop.tick()
    state = loop.snapshot('alice')
    by_session = {}
    for trace in state['traces']:
        if trace['state'] == 'SUPERSEDED': continue
        by_session.setdefault(trace['session'], []).append({
            'taskId':trace['id'],'goal':_redact(trace['goal']),
            'anchorSourceId':trace['turns'][0].get('sourceUserMessageId'),
            'sourceUserMessageIds':[t.get('sourceUserMessageId') for t in trace['turns']],
            'turnCount':len(trace['turns']),'verification':trace['verification'],
            'state':trace['state']})
    summary = {
        'case':'038_contract_multi_review', 'mode':'real-model-stage2',
        'artificialReplyTo':False,'skillsGenerated':False,
        'sourceUserTurns':len(state['turns']),
        'detections':[{'session':d['session'],'status':d['status'],'sourceHash':d['sourceHash'],
                       'runId':d.get('runId'),'error':d.get('error')}
                      for d in state['detections']],
        'tasksBySession':by_session,
        'unattachedSourceIds':[t.get('sourceUserMessageId') for t in state['turns'] if not t.get('taskId')],
        'metrics':state['metrics'],
    }
    tracks = json.loads((CASE/'recovered_trajectories.json').read_text(encoding='utf-8'))
    expected = {}
    for track in tracks:
        groups = {}
        for turn in track['turns']:
            groups.setdefault(turn['task'], []).append(turn['userMessageId'])
        expected[track['sessionId']] = sorted(sorted(group) for group in groups.values())
    actual = {session:sorted(sorted(task['sourceUserMessageIds']) for task in tasks)
              for session,tasks in by_session.items()}
    summary['checks'] = {
        'allThreeSessionsInterpreted':len(summary['detections']) == 3 and all(d['status']=='READY' for d in summary['detections']),
        'exactSourceMessageGroups':actual == expected,
        'allUserTurnsAttached':not summary['unattachedSourceIds'],
        'unknownOutcomePreserved':all(t['verification']=='UNKNOWN' for group in by_session.values() for t in group),
        'priceSeparated':any(t['anchorSourceId']=='conv_60925fa3f733:74cd5639' and t['turnCount']==1
                             for t in by_session.get('conv_60925fa3f733',[])),
    }
    summary['passed'] = all(summary['checks'].values())
    args.data.mkdir(parents=True,exist_ok=True)
    path = args.data/'038-task-detection-result.json'
    path.write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'passed':summary['passed'],'checks':summary['checks'],
                      'metrics':summary['metrics'],'result':str(path)},ensure_ascii=False,indent=2))
    raise SystemExit(0 if summary['passed'] else 1)


if __name__ == '__main__': main()
