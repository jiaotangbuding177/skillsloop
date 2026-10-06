"""Reproduce a frozen host rejection from saved model output; this is not skill acceptance."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

from replay_saved_responses import (SavedResponseAgent,frozen_environment,deny_network,comparison,
    Loop,select_source,source_fingerprint,make_manifest,execute_experiment,verify_saved_results,
    write_json,file_sha,DEMO,PROJECT,digest)


def stages_errors(root):
    stages=json.loads((Path(root)/'stage-2.json').read_text(encoding='utf-8'))
    return sorted(({k:s.get(k) for k in ('session','stage2','stage3','error','taskSeedCount','traceCount')}
                   for s in stages['stageStatus']),key=lambda s:s['session'])


def replay_failure(source,data,case):
    source=Path(source).resolve();data=Path(data).resolve()
    if source==data or data.is_relative_to(source):raise ValueError('Failure replay requires an independent new directory')
    if data.exists() and any(data.iterdir()):raise ValueError('Failure replay directory must be new/empty')
    original=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    outcome=json.loads((source/'acceptance-summary.json').read_text(encoding='utf-8'))
    if outcome['status']!='FAILED':raise ValueError('Only an original failed experiment is eligible for rejection replay')
    if verify_saved_results(source)['status']!='PASS':raise ValueError('Original failed-run artifacts changed')
    events,selection=select_source(case)
    if selection!=original['source']:raise ValueError('Input selection changed')
    if source_fingerprint(DEMO)!=original['codeFiles']:raise ValueError('Frozen application code changed')
    agent=SavedResponseAgent(source)
    runtime=deepcopy(original['runtime'])
    runtime['replayExecution']={'mode':'SAVED_RESPONSE_REJECTION_REPLAY','sourceManifestHash':original['manifestHash'],
        'scriptSha256':file_sha(__file__),'sharedReplayScriptSha256':file_sha(Path(__file__).with_name('replay_saved_responses.py')),
        'newInference':False,'networkAllowed':False,'inputOrResponseRewritten':False}
    protocol=original['protocol']
    manifest=make_manifest(selection,original['codeFiles'],runtime,protocol['dailyDispatchLimit'],protocol['maxCandidates'])
    def final_manifest():
        _,selected=select_source(case)
        return make_manifest(selected,source_fingerprint(DEMO),runtime,protocol['dailyDispatchLimit'],protocol['maxCandidates'])
    with frozen_environment(original),deny_network() as attempts:
        factory=lambda path:Loop(path,agent,settle_seconds=0,daily_limit=protocol['dailyDispatchLimit'],pool_wait_seconds=0,stage_pipeline=True)
        result=execute_experiment(data,events,manifest,factory,progress=lambda message:print(message,flush=True),final_manifest=final_manifest)
    stage_compare=comparison(source,data)
    errors_before,errors_after=stages_errors(source),stages_errors(data)
    same_fields={field:outcome.get(field)==result.get(field) for field in ('status','stoppedAt','error','checks','traceCount','candidateStatuses')}
    same_fields['perSessionStatesAndErrors']=errors_before==errors_after
    same_fields['allSavedResponsesConsumedExactlyOnce']=len(agent.consumed)==len(agent.records)
    same_fields['zeroNetworkAttempts']=not attempts
    reproduced=(result['status']=='FAILED' and all(same_fields.values()) and all(c['match'] for c in stage_compare.values()))
    report={'rejectionReproduced':reproduced,'mode':'SAVED_RESPONSE_REJECTION_REPLAY',
        'skillGenerationAcceptance':'FAILED','sourceAcceptance':outcome['status'],'replayAcceptance':result['status'],
        'sourceManifestHash':original['manifestHash'],'replayManifestHash':manifest['manifestHash'],
        'sourceStoppedAt':outcome.get('stoppedAt'),'replayStoppedAt':result.get('stoppedAt'),
        'sourceResponseCount':len(agent.records),'consumedResponseCount':len(agent.consumed),
        'newNetworkAttempts':len(attempts),'newInference':False,'newOpenClawRead':False,
        'sourceHashOrResponseRewritten':False,'sameOutcomeFields':same_fields,'comparison':stage_compare,
        'sourceSessionStates':errors_before,'replaySessionStates':errors_after,
        'scope':'A reproduced rejection proves deterministic host validation for these saved responses, not successful skills generation, universal model accuracy, or a new model trial.'}
    write_json(data/'failure-replay-comparison.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run',type=Path,required=True)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--case',type=Path,default=PROJECT/'research/cases/038_contract_multi_review')
    args=parser.parse_args()
    try:
        report=replay_failure(args.source_run,args.data,args.case)
        # Session errors remain in the private report; stdout is metadata only.
        print(json.dumps({k:v for k,v in report.items() if k not in ('sourceSessionStates','replaySessionStates')},ensure_ascii=False,indent=2))
        return 0 if report['rejectionReproduced'] else 1
    except Exception as exc:
        print(json.dumps({'rejectionReproduced':False,'newInference':False,'error':str(exc)[:1500]},ensure_ascii=False))
        return 1


if __name__=='__main__':raise SystemExit(main())
