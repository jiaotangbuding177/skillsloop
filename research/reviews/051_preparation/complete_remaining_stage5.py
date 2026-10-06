"""Independent one-dispatch stage-5 continuation from a documented budget checkpoint.

The parent remains PARTIAL. Its database is opened read-only and copied into a
new directory. Only the single queued candidate may run; this is not a fresh
five-stage experiment and does not increase or rewrite the parent's budget.
"""
import argparse
from contextlib import contextmanager,closing
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import sys
import time

PROJECT=Path(__file__).resolve().parents[3]
DEMO=PROJECT/'enginering/demo'
sys.path.insert(0,str(DEMO))
from skilldemo.core import Loop
from skilldemo.live import load_env
from skilldemo.runtime import OpenClawAgent,digest
from skilldemo.experiment import (select_source,source_fingerprint,runtime_fingerprint,verify_saved_results,
    export_deliverables,write_json,file_sha,exclusive_run)


@contextmanager
def readonly_db(path):
    db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)
    db.row_factory=sqlite3.Row
    try:yield db
    finally:db.close()


def database_snapshot(path):
    with readonly_db(path) as db:
        rows={table:[list(r) for r in db.execute('SELECT * FROM '+table+' ORDER BY '+order)]
              for table,order in (('records','kind,id'),('events','seq'),('runs','id'))}
        candidates=[json.loads(r['data']) for r in db.execute("SELECT data FROM records WHERE kind='candidate' AND owner='alice'")]
        day=int(time.time()//86400)*86400
        current_count=db.execute("SELECT count(*) FROM runs WHERE owner='alice' AND started>=? AND purpose IN ('learn','detect','detect_pairs','recover_trace','workflow_extract','workflow_merge','workflow_creator')",(day,)).fetchone()[0]
    files={Path(path).name:file_sha(path)}
    wal=Path(str(path)+'-wal')
    if wal.exists():files[wal.name]=file_sha(wal)
    return {'logicalHash':digest(rows),'physicalFiles':files,'currentUtcDayDispatches':current_count},candidates


def inspect_parent(source,case,runtime_override=None):
    source=Path(source).resolve()
    parent=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    host=json.loads((source/'acceptance-summary.json').read_text(encoding='utf-8'))
    mixed=json.loads((source/'mixed-experiment-summary.json').read_text(encoding='utf-8'))
    if mixed.get('status')!='PARTIAL' or not mixed.get('budgetStopped') or mixed.get('newOuterDispatches')!=4:
        raise ValueError('Parent must be the preserved four-new-dispatch budget-limited PARTIAL run')
    if host.get('status')!='FAILED' or host.get('stoppedAt')!='5' or not all(all(host['checks'][s].values()) for s in ('1','2','3','4')):
        raise ValueError('Parent stages 1–4 did not all pass before stage-5 budget stop')
    if verify_saved_results(source)['status']!='PASS':raise ValueError('Parent saved artifacts changed')
    if source_fingerprint(DEMO)!=parent['codeFiles']:raise ValueError('Application code changed since parent')
    actual_runtime=runtime_override or runtime_fingerprint(DEMO)
    parent_runtime={k:v for k,v in parent['runtime'].items() if k!='mixedExecution'}
    if actual_runtime!=parent_runtime:raise ValueError('Model/runtime configuration changed since parent')
    _,selection=select_source(case)
    if selection!=parent['source']:raise ValueError('Selected source data changed since parent')
    db_fingerprint,candidates=database_snapshot(source/'loop.sqlite')
    snapshot=json.loads((source/'stage-5.json').read_text(encoding='utf-8'))['candidates']
    if sorted(candidates,key=lambda c:c['id'])!=sorted(snapshot,key=lambda c:c['id']):
        raise ValueError('Parent database candidates differ from frozen stage-5 checkpoint')
    ready=[c for c in candidates if c['status']=='READY'];queued=[c for c in candidates if c['status']=='QUEUED']
    if len(candidates)!=3 or len(ready)!=2 or len(queued)!=1:
        raise ValueError('Exactly two READY and one QUEUED candidate are required')
    expected={c['id'] for c in ready}
    if {d['candidateId'] for d in host.get('deliverables',[])}!=expected:
        raise ValueError('Parent READY deliveries are incomplete')
    for delivery in host['deliverables']:
        archive=Path(delivery['archive']).resolve()
        if not archive.is_relative_to(source) or file_sha(archive)!=delivery['archiveSha256']:
            raise ValueError('Parent delivery archive location/hash mismatch')
        for name,expected_hash in delivery['files'].items():
            path=(archive.parent/name).resolve()
            if not path.is_relative_to(archive.parent) or file_sha(path)!=expected_hash:
                raise ValueError('Parent delivery file location/hash mismatch')
    return parent,host,mixed,db_fingerprint,ready,queued[0],actual_runtime


class OneCreatorAgent:
    def __init__(self,delegate,data,expected):
        self.mode=delegate.mode;self.delegate=delegate;self.data=Path(data);self.expected=expected

    def run(self,purpose,payload,workspace):
        if purpose!='workflow_creator' or digest(payload)!=self.expected:
            raise ValueError('Only the frozen remaining workflow creator payload is allowed')
        ledger_path=self.data/'new-model-dispatch.json'
        if ledger_path.exists():raise ValueError('Independent stage-5 one-dispatch limit exhausted; no retry')
        receipt={'purpose':purpose,'requestHash':digest(payload),'status':'STARTED','started':time.time(),
                 'workspace':workspace.name,'maximumNewOuterDispatches':1}
        write_json(ledger_path,receipt)
        try:
            result=self.delegate.run(purpose,payload,workspace)
            receipt.update(status='COMPLETED',modelRequestStarts=result.get('modelRequestStarts'),usage=result.get('usage'),finished=time.time())
            write_json(ledger_path,receipt)
            result['independentStage5Continuation']=True
            return result
        except Exception as exc:
            partial=getattr(exc,'result',{})
            receipt.update(status='FAILED',modelRequestStarts=partial.get('modelRequestStarts'),usage=partial.get('usage'),
                           errorType=type(exc).__name__,finished=time.time())
            write_json(ledger_path,receipt)
            raise


def complete(source,data,case,preflight_only=False,delegate=None,runtime_override=None):
    source=Path(source).resolve();data=Path(data).resolve()
    if source==data or data.is_relative_to(source):raise ValueError('Independent continuation directory required')
    with exclusive_run(data):
        parent,host,mixed,db_fingerprint,ready,queued,runtime=inspect_parent(source,case,runtime_override)
        public={k:queued['input'][k] for k in ('algorithm','workflow','methods','workflowHash','workflowId')}
        spec={'schemaVersion':'stage5-only-continuation-v1','isFreshFirst5Experiment':False,
              'parentManifestHash':parent['manifestHash'],'parentAcceptance':'PARTIAL','parentHostAcceptance':'FAILED',
              'parentDatabase':{'path':str(source/'loop.sqlite'),**db_fingerprint},
              'codeFiles':source_fingerprint(DEMO),'runtime':runtime,'source':parent['source'],
              'scriptSha256':file_sha(__file__),'candidateId':queued['id'],'stage5InputHash':digest(public),
              'preservedReadyCandidateIds':sorted(c['id'] for c in ready),
              'maximumNewOuterDispatches':1,'retryAllowed':False,'stagesExecuted':[5],
              'newDatabaseDerivedFrom':'READ_ONLY_SQLITE_BACKUP_OF_COMPLETED_CHECKPOINT',
              'budgetAccounting':'Independent additional one-dispatch allowance; parent budget and failure/partial outcome remain unchanged'}
        manifest={**spec,'manifestHash':digest(spec)}
        manifest_path=data/'continuation-manifest.json'
        if manifest_path.exists():
            if json.loads(manifest_path.read_text(encoding='utf-8'))!=manifest:
                raise ValueError('Continuation manifest changed; old evidence preserved')
        else:
            if (data/'loop.sqlite').exists():raise ValueError('Unowned database in continuation directory')
            write_json(manifest_path,manifest)
        if preflight_only:
            result={'status':'PREFLIGHT_PASSED','manifestHash':manifest['manifestHash'],'candidateId':queued['id'],
                    'maximumNewOuterDispatches':1,'paidCalls':0,'parentAcceptancePreserved':'PARTIAL'}
            write_json(data/'preflight-summary.json',result);return result
        final_path=data/'stage5-completion-summary.json'
        if final_path.exists():return json.loads(final_path.read_text(encoding='utf-8'))
        db_path=data/'loop.sqlite'
        if not db_path.exists():
            with readonly_db(source/'loop.sqlite') as src,closing(sqlite3.connect(db_path)) as dst:src.backup(dst)
        copied,_=database_snapshot(db_path)
        if copied['logicalHash']!=db_fingerprint['logicalHash']:
            raise ValueError('Copied checkpoint changed or already attempted; no implicit retry')
        from skilldemo.creator import verify_archive
        copied_archives=[]
        for candidate in ready:
            source_work=source/'workspaces'/candidate['runId']
            receipt=candidate['package']
            verify_archive(source_work,receipt,candidate['files'])
            dest_work=data/'workspaces'/candidate['runId']
            dest=(dest_work/receipt['path']).resolve()
            if not dest.is_relative_to(dest_work.resolve()):raise ValueError('Illegal copied archive path')
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes((source_work/receipt['path']).read_bytes())
            verified=verify_archive(dest_work,receipt,candidate['files'])
            copied_archives.append({'candidateId':candidate['id'],'runId':candidate['runId'],
                'path':str(dest.relative_to(data)),'sha256':verified['sha256'],
                'canonicalContentHash':digest({f['path']:__import__('hashlib').sha256(f['content'].encode()).hexdigest() for f in candidate['files']})})
        write_json(data/'copied-parent-archives.json',copied_archives)
        agent=OneCreatorAgent(delegate or OpenClawAgent(),data,digest(public))
        loop=Loop(data,agent,settle_seconds=0,daily_limit=db_fingerprint['currentUtcDayDispatches']+1,stage_pipeline=True)
        with loop.store.tx() as db:
            old_ids={r[0] for r in db.execute('SELECT id FROM runs')}
        write_json(data/'stage5-input.json',{'candidateId':queued['id'],'input':public})
        print('Stage 5 continuation only: '+queued['id'],flush=True)
        created=loop.generate('alice',queued['id'])
        state=loop.snapshot('alice')
        write_json(data/'stage5-output.json',created)
        new_runs=[r for r in state['runs'] if r['id'] not in old_ids]
        write_json(data/'new-model-runs.json',new_runs)
        deliveries=[];delivery_error=None
        try:deliveries=export_deliverables(data,{'candidates':[created]})
        except Exception as exc:delivery_error=str(exc)[:600]
        current_db,_=database_snapshot(source/'loop.sqlite')
        unchanged=(current_db['logicalHash']==db_fingerprint['logicalHash'] and
                   source_fingerprint(DEMO)==parent['codeFiles'] and (runtime_override or runtime_fingerprint(DEMO))==runtime)
        before={c['id']:c for c in ready};after={c['id']:c for c in state['candidates']}
        ready_unchanged=all(after.get(cid)==c for cid,c in before.items())
        checks={'singleNewCreatorDispatch':len(new_runs)==1 and new_runs[0]['purpose']=='workflow_creator',
                'remainingCandidateReady':created['status']=='READY','newArchiveVerified':len(deliveries)==1 and not delivery_error,
                'parentAndFrozenCodeConfigUnchanged':unchanged,'existingReadyCandidatesNotRegenerated':ready_unchanged,
                'copiedParentArchivesVerified':len(copied_archives)==2,
                'allThreeCandidatesReady':len(after)==3 and all(c['status']=='READY' for c in after.values()),
                'noAutomaticAdoptionOrPublication':not state['skills'] and not state['submissions']}
        passed=all(checks.values())
        receipt=json.loads((data/'new-model-dispatch.json').read_text(encoding='utf-8')) if (data/'new-model-dispatch.json').exists() else {}
        result={'status':'PASSED' if passed else 'FAILED','mode':'INDEPENDENT_STAGE5_ONLY_CONTINUATION',
                'isFreshFirst5Experiment':False,'manifestHash':manifest['manifestHash'],'parentManifestHash':parent['manifestHash'],
                'parentAcceptanceUnchanged':'PARTIAL','parentHostAcceptanceUnchanged':'FAILED','checks':checks,
                'candidateStatuses':{cid:c['status'] for cid,c in after.items()},'newDeliverables':deliveries,
                'copiedParentArchives':copied_archives,
                'combinedDeliveries':[{'origin':'PARENT_PARTIAL_RUN',**d} for d in host['deliverables']]+[{'origin':'INDEPENDENT_STAGE5_CONTINUATION',**d} for d in deliveries],
                'newOuterDispatches':1 if receipt else 0,'newInternalRequestStarts':receipt.get('modelRequestStarts'),
                'newUsage':receipt.get('usage'),'deliveryError':delivery_error,
                'combinedScope':'Three READY packages across parent mixed run plus independent single-candidate continuation; this does not relabel the parent as passed.'}
        write_json(final_path,result)
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-run',type=Path,required=True)
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--case',type=Path,default=PROJECT/'research/cases/038_contract_multi_review')
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--preflight-only',action='store_true')
    mode.add_argument('--run',action='store_true')
    args=parser.parse_args();load_env(DEMO/'.env')
    try:result=complete(args.source_run,args.data,args.case,args.preflight_only)
    except Exception as exc:result={'status':'PRECONDITION_FAILED','error':str(exc)[:1500]}
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)
    return 0 if result['status'] in ('PASSED','PREFLIGHT_PASSED') else 1


if __name__=='__main__':raise SystemExit(main())
