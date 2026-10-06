"""Fresh host pipeline with eight saved responses, repaired parser, one new creator.

The old experiment remains FAILED. Saved output text, source hashes and public
drafts are never edited. Historical read receipts are replayed, not new reads.
"""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
import time

PROJECT=Path(__file__).resolve().parents[3]
DEMO=PROJECT/'enginering/demo'
sys.path.insert(0,str(DEMO))
from skilldemo.core import Loop
from skilldemo.live import load_env
from skilldemo.bootstrap import draft_files
from skilldemo.runtime import OpenClawAgent,digest,request_config
from skilldemo.experiment import (select_source,source_fingerprint,runtime_fingerprint,make_manifest,
    execute_experiment,verify_saved_results,write_json,file_sha)


def source_material(source,case,runtime_override=None):
    source=Path(source).resolve()
    manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    outcome=json.loads((source/'acceptance-summary.json').read_text(encoding='utf-8'))
    if outcome['status']!='FAILED' or outcome.get('stoppedAt')!='5':
        raise ValueError('Source must remain a stage-5 FAILED experiment')
    if not all(all(outcome['checks'][s].values()) for s in ('1','2','3','4')):
        raise ValueError('Source stages 1–4 were not all accepted')
    if verify_saved_results(source)['status']!='PASS':raise ValueError('Source saved artifacts changed')
    candidates=json.loads((source/'stage-5.json').read_text(encoding='utf-8'))['candidates']
    if sorted(c['status'] for c in candidates)!=['FAILED','QUEUED','READY']:
        raise ValueError('Expected exactly one READY, one FAILED and one QUEUED source candidate')
    queued=next(c for c in candidates if c['status']=='QUEUED')
    runs=json.loads((source/'model-runs.json').read_text(encoding='utf-8'))
    if len(runs)!=8 or any(r['status']!='COMPLETED' or not isinstance(r.get('result'),dict) for r in runs):
        raise ValueError('Exactly eight completed source agent responses are required')
    counts={p:sum(r['purpose']==p for r in runs) for p in ('detect_pairs','recover_trace','workflow_extract','workflow_merge','workflow_creator')}
    if counts!={'detect_pairs':2,'recover_trace':2,'workflow_extract':1,'workflow_merge':1,'workflow_creator':2}:
        raise ValueError('Source response purpose inventory differs')
    current_code=source_fingerprint(DEMO)
    changed={p for p in set(current_code)|set(manifest['codeFiles']) if current_code.get(p)!=manifest['codeFiles'].get(p)}
    if not changed<={'skilldemo/runtime.py'}:raise ValueError('Unapproved source change beyond runtime parser: '+str(sorted(changed)))
    current_runtime=runtime_override or runtime_fingerprint(DEMO)
    base_runtime={k:v for k,v in manifest['runtime'].items() if k!='mixedExecution'}
    if current_runtime!=base_runtime:raise ValueError('Model/prompt/provider/runtime configuration changed; parser-only replay required')
    for purpose,config in base_runtime['requests'].items():
        if request_config(purpose)!=config:raise ValueError('Actual request configuration changed: '+purpose)
    events,selection=select_source(case)
    if selection!=manifest['source']:raise ValueError('Original selected source events changed')
    drafts={}
    for candidate in candidates:
        if candidate['status'] not in ('READY','FAILED'):continue
        files=draft_files(source/'workspaces'/candidate['runId'])
        if not files:raise ValueError('Original creator draft is missing')
        if candidate.get('files') and candidate['files']!=files:raise ValueError('Saved READY draft differs from original accepted files')
        drafts[candidate['runId']]=files
    return manifest,outcome,events,selection,runs,queued,drafts,current_runtime,sorted(changed)


class SavedEightOneNewAgent:
    def __init__(self,runs,drafts,queued,delegate,data):
        modes={r['mode'] for r in runs}
        if len(modes)!=1 or delegate.mode not in modes:raise ValueError('Runtime mode mismatch')
        self.mode=modes.pop();self.delegate=delegate;self.data=Path(data)
        self.saved={(r['purpose'],digest(r['request'])):r for r in runs};self.drafts=drafts;self.consumed=[]
        if len(self.saved)!=8:raise ValueError('Ambiguous saved requests')
        public={k:queued['input'][k] for k in ('algorithm','workflow','methods','workflowHash','workflowId')}
        self.allowed_new=digest(public)

    def run(self,purpose,payload,workspace):
        key=(purpose,digest(payload));row=self.saved.get(key)
        if row is not None:
            if key in self.consumed:raise ValueError('Duplicate saved request during replay')
            self.consumed.append(key)
            result=deepcopy(row['result'])
            result['savedAgentResponseReplay']={'sourceRunId':row['id'],'requestHash':key[1],
                'sourceUsage':result.get('usage'),'newInference':False,'originalTextUnchanged':True}
            result['usage']={'total':0};result['costUsd']=0;result['modelRequestStarts']=0
            result['runtime']='saved-agent-response-parser-replay'
            if purpose=='workflow_creator':
                files=self.drafts.get(row['id'])
                if not files:raise ValueError('Saved creator file set missing')
                for item in files:
                    path=workspace/'draft'/item['path']
                    if not path.resolve().is_relative_to((workspace/'draft').resolve()):raise ValueError('Illegal saved draft path')
                    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(item['content'].encode('utf-8'))
                if result.get('foundationRead'):
                    result['foundationRead']['replayedHistoricalReceipt']=True
                    result['foundationRead']['newReadObserved']=False
                    result['foundationRead']['sourceRunId']=row['id']
            write_json(workspace/'saved-request.json',{'purpose':purpose,'sourceRunId':row['id'],'payload':payload})
            write_json(workspace/'saved-response.json',result)
            return result
        if purpose!='workflow_creator' or key[1]!=self.allowed_new:
            raise ValueError('UNMATCHED_SAVED_REQUEST: '+purpose+' '+key[1]+'; no text/sourceHash repair')
        ledger=self.data/'one-new-creator-dispatch.json'
        if ledger.exists():raise ValueError('One-new-dispatch limit exhausted; no retry')
        receipt={'purpose':purpose,'requestHash':key[1],'status':'STARTED','started':time.time()}
        write_json(ledger,receipt)
        try:
            result=self.delegate.run(purpose,payload,workspace)
            receipt.update(status='COMPLETED',modelRequestStarts=result.get('modelRequestStarts'),usage=result.get('usage'))
            write_json(ledger,receipt);result['oneNewCreatorAfterSavedReplay']=True
            return result
        except Exception as exc:
            measured=getattr(exc,'result',{})
            receipt.update(status='FAILED',errorType=type(exc).__name__,modelRequestStarts=measured.get('modelRequestStarts'),usage=measured.get('usage'))
            write_json(ledger,receipt);raise


def run(source,data,case,preflight_only=False,delegate=None,runtime_override=None):
    source=Path(source).resolve();data=Path(data).resolve()
    if source==data or data.is_relative_to(source):raise ValueError('New independent data directory required')
    parent,outcome,events,selection,runs,queued,drafts,runtime,changed=source_material(source,case,runtime_override)
    draft_hashes={run_id:digest(files) for run_id,files in drafts.items()}
    def current_manifest():
        _,current_selection=select_source(case)
        current_runtime=deepcopy(runtime_override or runtime_fingerprint(DEMO))
        current_runtime['savedResponsesAndOneNewCreator']={
            'mode':'EIGHT_SAVED_RESPONSES_REPAIRED_PARSER_ONE_NEW_CREATOR',
            'sourceManifestHash':parent['manifestHash'],'sourceHostAcceptance':'FAILED',
            'sourceMixedSummaryCorrection':'FAILED takes precedence over the original PARTIAL/budgetStopped label',
            'scriptSha256':file_sha(__file__),'isFreshFiveStageModelTrial':False,
            'changedApplicationFiles':{p:{'old':parent['codeFiles'].get(p),'new':source_fingerprint(DEMO).get(p)} for p in changed},
            'savedResponses':[{'sourceRunId':r['id'],'purpose':r['purpose'],'requestHash':digest(r['request']),
                               'responseHash':digest(r['result'])} for r in runs],
            'savedCreatorDraftHashes':draft_hashes,'newCreatorCandidateId':queued['id'],
            'maximumNewOuterDispatches':1,'hostDispatchBudgetIncludingSavedResponses':9,
            'responseTextOrSourceHashRewrite':False,'newReadsForSavedCreators':False}
        return make_manifest(current_selection,source_fingerprint(DEMO),current_runtime,daily_limit=9,max_candidates=3)
    manifest=current_manifest();agent=SavedEightOneNewAgent(runs,drafts,queued,delegate or OpenClawAgent(),data)
    result=execute_experiment(data,events,manifest,
        lambda path:Loop(path,agent,settle_seconds=0,daily_limit=9,pool_wait_seconds=0,stage_pipeline=True),
        preflight_only,lambda message:print(message,flush=True),current_manifest)
    if preflight_only:return result
    observed=json.loads((data/'model-runs.json').read_text(encoding='utf-8'))
    saved=[r for r in observed if (r.get('result') or {}).get('savedAgentResponseReplay')]
    ledger=data/'one-new-creator-dispatch.json'
    receipt=json.loads(ledger.read_text(encoding='utf-8')) if ledger.exists() else {}
    source_unchanged=verify_saved_results(source)['status']=='PASS' and all(digest(draft_files(source/'workspaces'/rid))==value for rid,value in draft_hashes.items())
    fresh=[r for r in observed if (r.get('result') or {}).get('oneNewCreatorAfterSavedReplay')]
    checks={'hostAcceptancePassed':result['status']=='PASSED','eightResponsesRevalidated':len(saved)==8,
            'oneNewCreatorCompleted':len(fresh)==1,'threeReadyDeliveries':len(result.get('deliverables',[]))==3,
            'sourceArtifactsAndDraftsUnchanged':source_unchanged}
    summary={'status':'PASSED' if all(checks.values()) else 'FAILED','hostAcceptance':result['status'],
        'mode':'EIGHT_SAVED_RESPONSES_REPAIRED_PARSER_ONE_NEW_CREATOR','isFreshFiveStageModelTrial':False,
        'sourceAcceptanceUnchanged':'FAILED','sourceManifestHash':parent['manifestHash'],'manifestHash':manifest['manifestHash'],
        'checks':checks,'savedResponsesRevalidated':len(saved),'newOuterDispatches':1 if receipt else 0,
        'newInternalRequestStarts':receipt.get('modelRequestStarts'),'newUsage':receipt.get('usage'),
        'deliverables':result.get('deliverables',[]),'candidateStatuses':result.get('candidateStatuses',{}),
        'scope':'Fresh database from original events; eight original responses and two original creator drafts revalidated under repaired parser; only the previously unrun third creator uses new inference.'}
    write_json(data/'saved-response-completion-summary.json',summary)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run',type=Path,required=True)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--case',type=Path,default=PROJECT/'research/cases/038_contract_multi_review')
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight-only',action='store_true');mode.add_argument('--run',action='store_true')
    args=parser.parse_args();load_env(DEMO/'.env')
    try:result=run(args.source_run,args.data,args.case,args.preflight_only)
    except Exception as exc:result={'status':'PRECONDITION_FAILED','error':str(exc)[:1500]}
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    return 0 if result['status'] in ('PASSED','PREFLIGHT_PASSED') else 1


if __name__=='__main__':raise SystemExit(main())
