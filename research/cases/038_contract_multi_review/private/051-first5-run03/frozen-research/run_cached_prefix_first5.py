"""New isolated 1→5 run: exact saved-response prefix, fresh workflow model calls.

This is a mixed experiment, not a fresh five-stage model trial. The failed
parent experiment is preserved and never loaded as a SQLite database.
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
from skilldemo.experiment import (select_source,source_fingerprint,runtime_fingerprint,make_manifest,
    execute_experiment,verify_saved_results,write_json,file_sha)
from skilldemo.runtime import OpenClawAgent,digest,request_config

PREFIX_PURPOSES=('detect_pairs','recover_trace')
PREFIX_FILES=('skilldemo/intake.py','skilldemo/pair_detection.py','skilldemo/recovery.py',
              'skilldemo/front_stages.py','skilldemo/request_cache.py','skilldemo/store.py',
              'skilldemo/core.py','skilldemo/runtime.py')


def inspect_parent(source,case):
    source=Path(source).resolve()
    manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    result=json.loads((source/'acceptance-summary.json').read_text(encoding='utf-8'))
    if result['status']!='FAILED' or result.get('stoppedAt')!='4':
        raise ValueError('Parent must remain a stage-4 failed experiment; no relabeling permitted')
    if not all(all(result['checks'][s].values()) for s in ('1','2','3')):
        raise ValueError('Parent first-three-stage acceptance was not complete')
    if verify_saved_results(source)['status']!='PASS':raise ValueError('Parent saved artifacts changed')
    current=source_fingerprint(DEMO)
    for path in PREFIX_FILES:
        if not current.get(path) or current[path]!=manifest['codeFiles'].get(path):
            raise ValueError('Prefix implementation changed: '+path)
    for purpose in PREFIX_PURPOSES:
        if request_config(purpose)!=manifest['runtime']['requests'][purpose]:
            raise ValueError('Prefix prompt/model/request configuration changed: '+purpose)
    events,selection=select_source(case)
    if selection!=manifest['source']:raise ValueError('Selected events differ from parent prefix')
    stage2=json.loads((source/'stage-2.json').read_text(encoding='utf-8'))
    stages=stage2['stageStatus']
    if any(s.get('stage2')!='ANNOTATED' or s.get('stage3')!='RECOVERED' for s in stages):
        raise ValueError('Parent prefix contains unverified session output')
    accepted_ids={s[k] for s in stages for k in ('detectionRun','recoveryRun')}
    all_runs=json.loads((source/'model-runs.json').read_text(encoding='utf-8'))
    runs=[r for r in all_runs if r['purpose'] in PREFIX_PURPOSES]
    if len(runs)!=4 or {r['id'] for r in runs}!=accepted_ids:
        raise ValueError('Exactly four validated parent prefix dispatches are required')
    if any(r['status']!='COMPLETED' or not isinstance(r.get('result'),dict) for r in runs):
        raise ValueError('Parent prefix response incomplete')
    return manifest,result,events,selection,runs


class CachedPrefixAgent:
    def __init__(self,runs,delegate,data,max_new_calls=4):
        modes={r['mode'] for r in runs}
        if len(modes)!=1 or delegate.mode not in modes:raise ValueError('Source/delegate mode mismatch')
        self.mode=modes.pop();self.delegate=delegate;self.data=Path(data)
        self.max_new_calls=max_new_calls;self.consumed=[]
        self.saved={(r['purpose'],digest(r['request'])):r for r in runs}
        if len(self.saved)!=4:raise ValueError('Ambiguous prefix request keys')

    def run(self,purpose,payload,workspace):
        if purpose in PREFIX_PURPOSES:
            key=(purpose,digest(payload));row=self.saved.get(key)
            if row is None:raise ValueError('PREFIX_REQUEST_MISMATCH: '+purpose+' '+key[1]+'; no response/sourceHash rewriting')
            if key in self.consumed:raise ValueError('Prefix request repeated unexpectedly')
            self.consumed.append(key)
            result=deepcopy(row['result'])
            result['savedPrefixReplay']={'sourceRunId':row['id'],'requestHash':key[1],
                'originalUsage':result.get('usage'),'originalRuntime':result.get('runtime'),'newInference':False}
            result['usage']={'total':0};result['costUsd']=0;result['modelRequestStarts']=0
            result['runtime']='saved-prefix-response-host-replay'
            write_json(workspace/'saved-prefix-request.json',{'purpose':purpose,'sourceRunId':row['id'],'payload':payload})
            write_json(workspace/'saved-prefix-response.json',result)
            return result
        if purpose not in ('workflow_extract','workflow_merge','workflow_creator'):
            raise ValueError('Unapproved new-model purpose: '+purpose)
        ledger_path=self.data/'new-model-dispatches.json'
        ledger=json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else []
        if len(ledger)>=self.max_new_calls:raise ValueError('NEW_MODEL_DISPATCH_BUDGET_EXHAUSTED')
        entry={'ordinal':len(ledger)+1,'purpose':purpose,'requestHash':digest(payload),
               'status':'STARTED','at':time.time(),'workspace':workspace.name}
        ledger.append(entry);write_json(ledger_path,ledger)
        try:
            result=self.delegate.run(purpose,payload,workspace)
            result['mixedExperimentNewInference']=True
            entry.update(status='COMPLETED',modelRequestStarts=result.get('modelRequestStarts'),usage=result.get('usage'))
            write_json(ledger_path,ledger)
            return result
        except Exception as exc:
            entry.update(status='FAILED',errorType=type(exc).__name__)
            write_json(ledger_path,ledger)
            raise


def run_mixed(source,data,case,preflight_only=False,delegate=None,runtime_override=None):
    source=Path(source).resolve();data=Path(data).resolve()
    if source==data or data.is_relative_to(source):raise ValueError('New independent mixed-run directory required')
    original,parent_result,events,selection,runs=inspect_parent(source,case)
    runtime=runtime_override or runtime_fingerprint(DEMO)
    def current_manifest():
        _,current_selection=select_source(case)
        current_runtime=deepcopy(runtime_override or runtime_fingerprint(DEMO))
        current_runtime['mixedExecution']={
            'mode':'SAVED_STAGE123_PREFIX_AND_FRESH_STAGE45',
            'scriptSha256':file_sha(__file__),'parentManifestHash':original['manifestHash'],
            'parentAcceptance':parent_result['status'],'parentStoppedAt':parent_result['stoppedAt'],
            'savedPrefix':[{'sourceRunId':r['id'],'purpose':r['purpose'],'requestHash':digest(r['request']),
                            'responseHash':digest(r['result'])} for r in runs],
            'prefixModelInference':'NONE; source responses unchanged, revalidated by current matching prefix code',
            'stage45Inference':'NEW','maxNewOuterDispatches':4,'totalDispatchBudgetIncludingPrefix':8,
            'maxCandidates':3,'maxRetriesPerNewOuterDispatch':0,'parentFailedWorkflowResponseReused':False,
            'isAllFreshFiveStageModelTrial':False}
        return make_manifest(current_selection,source_fingerprint(DEMO),current_runtime,daily_limit=8,max_candidates=3)
    manifest=current_manifest()
    agent=CachedPrefixAgent(runs,delegate or OpenClawAgent(),data,max_new_calls=4)
    result=execute_experiment(data,events,manifest,
        lambda path:Loop(path,agent,settle_seconds=0,daily_limit=8,pool_wait_seconds=0,stage_pipeline=True),
        preflight_only,lambda message:print(message,flush=True),current_manifest)
    if preflight_only:return result
    observed=json.loads((data/'model-runs.json').read_text(encoding='utf-8'))
    prefix_observed=[r for r in observed if (r.get('result') or {}).get('savedPrefixReplay')]
    ledger_path=data/'new-model-dispatches.json'
    ledger=json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else []
    stage5=json.loads((data/'stage-5.json').read_text(encoding='utf-8'))['candidates']
    remaining=[c['id'] for c in stage5 if c.get('status')=='QUEUED']
    budget_partial=(result['status']=='FAILED' and result.get('stoppedAt')=='5' and
                    len(ledger)==4 and bool(remaining) and bool(result.get('deliverables')))
    # Preserve host acceptance-summary and its integrity hashes; report mixed-run
    # budget classification separately instead of overwriting a failed host result.
    summary={'status':'PARTIAL' if budget_partial else result['status'],
        'hostAcceptance':result['status'],'isAllFreshFiveStageModelTrial':False,
        'mode':'SAVED_STAGE123_PREFIX_AND_FRESH_STAGE45','parentManifestHash':original['manifestHash'],
        'parentAcceptance':parent_result['status'],'parentStoppedAt':'4','manifestHash':manifest['manifestHash'],
        'prefixSavedResponsesRevalidated':len(prefix_observed),'newOuterDispatches':len(ledger),
        'newOuterDispatchLimit':4,'newInternalRequestStarts':sum((e.get('modelRequestStarts') or 0) for e in ledger),
        'internalRequestCountMissingRuns':sum(e.get('modelRequestStarts') is None for e in ledger),
        'unproducedCandidateIds':remaining,'deliverables':result.get('deliverables',[]),
        'checks':result.get('checks',{}),'metrics':result.get('metrics'),
        'budgetStopped':budget_partial,'sourceHashOrResponseRewritten':False,
        'failedParentWorkflowResponseReused':False,'scope':'Original events are reimported into a fresh DB; stages 1–3 reuse exact validated model responses, stages 4–5 perform new inference under a four-dispatch cap.'}
    write_json(data/'mixed-experiment-summary.json',summary)
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run',type=Path,required=True)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--case',type=Path,default=PROJECT/'research/cases/038_contract_multi_review')
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight-only',action='store_true')
    mode.add_argument('--run',action='store_true')
    args=parser.parse_args()
    load_env(DEMO/'.env')
    try:result=run_mixed(args.source_run,args.data,args.case,args.preflight_only)
    except Exception as exc:result={'status':'PRECONDITION_FAILED','error':str(exc)[:1200]}
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    return 0 if result['status'] in ('PASSED','PREFLIGHT_PASSED') else 1


if __name__=='__main__':raise SystemExit(main())
