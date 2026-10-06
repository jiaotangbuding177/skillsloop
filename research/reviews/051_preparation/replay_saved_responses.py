"""Offline host replay of frozen model responses and creator drafts, never fresh inference.

The source model/read receipts remain historical evidence. This replay proves
deterministic host treatment under the frozen code and validates/repacks the
same public skill content. It does not repeat an OpenClaw read or legal review.
"""
import argparse
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import socket
import sys

PROJECT=Path(__file__).resolve().parents[3]
DEMO=PROJECT/'enginering/demo'
sys.path.insert(0,str(DEMO))
from skilldemo.core import Loop
from skilldemo.experiment import (select_source,source_fingerprint,make_manifest,
    execute_experiment,verify_saved_results,write_json,file_sha)
from skilldemo.runtime import digest,request_config


class SavedResponseAgent:
    """Exact request lookup; no text/hash rewriting, model API, or OpenClaw process."""
    def __init__(self,source):
        self.source=Path(source)
        runs=json.loads((self.source/'model-runs.json').read_text(encoding='utf-8'))
        modes={r['mode'] for r in runs}
        if len(modes)!=1:raise ValueError('Mixed source runtime modes are not replayable')
        self.mode=modes.pop()
        self.records={};self.consumed=[]
        for row in runs:
            if row['status']!='COMPLETED' or not isinstance(row.get('result'),dict):
                raise ValueError('Source contains incomplete/failed run; exact successful replay requires completed responses')
            key=(row['purpose'],digest(row['request']))
            if key in self.records:raise ValueError('Ambiguous duplicate source request: '+row['purpose'])
            self.records[key]=row
        stage5=json.loads((self.source/'stage-5.json').read_text(encoding='utf-8'))
        self.drafts={c['runId']:c['files'] for c in stage5['candidates'] if c.get('status')=='READY'}

    def run(self,purpose,payload,workspace):
        key=(purpose,digest(payload))
        row=self.records.get(key)
        if row is None:
            raise ValueError('SAVED_REQUEST_MISMATCH: '+purpose+' '+key[1]+'; no sourceHash repair is permitted')
        if key in self.consumed:raise ValueError('Saved response requested twice; replay stopped')
        self.consumed.append(key)
        result=deepcopy(row['result'])
        result['savedEvidenceReplay']={'sourceRunId':row['id'],'requestHash':key[1],
            'newInference':False,'newOpenClawRead':False,'sourceUsage':result.get('usage')}
        result['usage']={'total':0}
        result['costUsd']=0
        result['modelRequestStarts']=0
        result['runtime']='saved-response-host-replay'
        result['sourceRuntime']=row['result'].get('runtime')
        if purpose=='workflow_creator':
            files=self.drafts.get(row['id'])
            if not files:raise ValueError('Original READY creator draft is missing')
            for item in files:
                path=workspace/'draft'/item['path']
                if not path.resolve().is_relative_to((workspace/'draft').resolve()):raise ValueError('Unsafe saved draft path')
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(item['content'].encode('utf-8'))
            if result.get('foundationRead'):
                result['foundationRead']['replayedHistoricalReceipt']=True
                result['foundationRead']['newReadObserved']=False
                result['foundationRead']['sourceRunId']=row['id']
        write_json(workspace/'saved-request.json',{'purpose':purpose,'payload':payload,'sourceRunId':row['id']})
        write_json(workspace/'saved-response.json',result)
        return result


@contextmanager
def frozen_environment(manifest):
    requests=manifest['runtime'].get('requests',{})
    if not requests:raise ValueError('Source manifest does not freeze model request configuration')
    structured=requests['detect_pairs'];creator=requests['workflow_creator']
    values={'DEMO_MODEL':structured['model'],'DEMO_MODEL_API':structured['api'],
            'DEMO_BASE_URL':structured['baseUrl'],'DEMO_NETWORK_MODE':structured['networkMode'],
            'DEMO_DETECT_TIMEOUT':str(structured['timeoutSeconds']),
            'DEMO_AGENT_TIMEOUT':str(creator['timeoutSeconds'])}
    old={k:os.environ.get(k) for k in values}
    try:
        for key,value in values.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=str(value)
        if any(request_config(purpose)!=config for purpose,config in requests.items()):
            raise ValueError('Frozen request configuration differs from current code')
        yield
    finally:
        for key,value in old.items():
            if value is None:os.environ.pop(key,None)
            else:os.environ[key]=value


@contextmanager
def deny_network():
    attempts=[]
    original=socket.socket.connect
    def denied(sock,address):
        attempts.append(True)
        raise RuntimeError('Network is forbidden during saved-response replay')
    socket.socket.connect=denied
    try:yield attempts
    finally:socket.socket.connect=original


def comparison(source,data):
    def stage(root,n):return json.loads((Path(root)/f'stage-{n}.json').read_text(encoding='utf-8'))
    def sorted_rows(rows,keys):
        return sorted(({k:r.get(k) for k in keys} for r in rows),key=lambda r:r['id'])
    projections={
        'stage1Sources':lambda root:sorted_rows(stage(root,1)['pairs'],('id','sourceHash','sourceMessageIds','contentStatus')),
        'stage2Annotations':lambda root:sorted_rows(stage(root,2)['pairAnnotations'],('id','pairId','fragments','sourceHash')),
        'stage3Traces':lambda root:sorted_rows(stage(root,3)['traces'],('id','hash','sourceMessageIds','requirementTimeline','feedbackEdges','businessOutcome')),
        'stage4MethodsAndDecisions':lambda root:sorted_rows(stage(root,4)['learningDecisions'],('id','methodLedger','clusters','routes','workflowIds')),
        'stage4Workflows':lambda root:sorted_rows(stage(root,4)['workflows'],('id','workflow','workflowHash','sourceRefs','action')),
        'stage5CanonicalFiles':lambda root:sorted_rows(stage(root,5)['candidates'],('id','files','workflowId','status'))}
    result={}
    for name,project in projections.items():
        left,right=digest(project(source)),digest(project(data))
        result[name]={'match':left==right,'sourceHash':left,'replayHash':right}
    return result


def replay(source,data,case):
    source=Path(source).resolve();data=Path(data).resolve()
    if source==data or data.is_relative_to(source):raise ValueError('Replay must use an independent new directory')
    if data.exists() and any(data.iterdir()):raise ValueError('Replay directory must be empty/new')
    original=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    original_result=json.loads((source/'acceptance-summary.json').read_text(encoding='utf-8'))
    if original_result['status']!='PASSED':raise ValueError('Source experiment did not pass; do not reinterpret a failed run as success')
    if verify_saved_results(source)['status']!='PASS':raise ValueError('Source saved artifact integrity check failed')
    events,selection=select_source(case)
    if selection!=original['source']:raise ValueError('Selected source data no longer matches frozen run')
    if source_fingerprint(DEMO)!=original['codeFiles']:raise ValueError('Application code drifted; exact frozen-code replay refused')
    agent=SavedResponseAgent(source)
    runtime=deepcopy(original['runtime'])
    runtime['replayExecution']={'mode':'SAVED_RESPONSE_HOST_REPLAY','sourceManifestHash':original['manifestHash'],
        'scriptSha256':file_sha(__file__),'newInference':False,'newOpenClawRead':False,'networkAllowed':False}
    protocol=original['protocol']
    manifest=make_manifest(selection,original['codeFiles'],runtime,protocol['dailyDispatchLimit'],protocol['maxCandidates'])
    def final_manifest():
        _,selected=select_source(case)
        return make_manifest(selected,source_fingerprint(DEMO),runtime,protocol['dailyDispatchLimit'],protocol['maxCandidates'])
    with frozen_environment(original),deny_network() as attempts:
        factory=lambda path:Loop(path,agent,settle_seconds=0,daily_limit=protocol['dailyDispatchLimit'],pool_wait_seconds=0,stage_pipeline=True)
        result=execute_experiment(data,events,manifest,factory,progress=lambda message:print(message,flush=True),final_manifest=final_manifest)
    compare=comparison(source,data)
    passed=result['status']=='PASSED' and all(c['match'] for c in compare.values()) and not attempts and len(agent.consumed)==len(agent.records)
    summary={'status':'PASS' if passed else 'FAILED','mode':'SAVED_RESPONSE_HOST_REPLAY',
        'sourceManifestHash':original['manifestHash'],'replayManifestHash':manifest['manifestHash'],
        'newInference':False,'newOpenClawRead':False,'newNetworkAttempts':len(attempts),
        'sourceResponseCount':len(agent.records),'consumedResponseCount':len(agent.consumed),
        'comparison':compare,'hostAcceptance':result['status'],
        'scope':'Frozen responses and creator files processed again by the current matching host code and official packager; historical read receipts are reused, not observed anew.'}
    write_json(data/'replay-comparison.json',summary)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run',type=Path,required=True)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--case',type=Path,default=PROJECT/'research/cases/038_contract_multi_review')
    args=parser.parse_args()
    try:result=replay(args.source_run,args.data,args.case)
    except Exception as exc:
        result={'status':'FAILED','newInference':False,'error':str(exc)[:1500]}
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    return 0 if result['status']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
