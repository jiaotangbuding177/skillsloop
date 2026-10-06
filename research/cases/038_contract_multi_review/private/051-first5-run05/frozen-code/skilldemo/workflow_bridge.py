"""Stage-4/5 orchestration over the existing records, events and runs tables."""
import json
import time
from .runtime import digest
from . import workflow
from .creator import verify_files, verify_archive, parse_creator_result
from .bootstrap import draft_files, package
from .request_cache import request as cached_request


def _request(loop, actor, purpose, payload, catalog=None, validator=None):
    if validator is None and purpose=='workflow_extract':
        validator=lambda value:workflow.validate_extract(value,payload,catalog)
    return cached_request(loop,actor,'workflow_analysis',purpose,payload,validator,
                          {'catalog':catalog or {}})


def discover(loop, actor, stop_on_failure=False):
    """Return queued NEW candidates; preserve decisions and every method disposition."""
    with loop.store.tx() as db:
        pending=sorted((t for t in loop.store.rows(db,'trace',actor)
            if t.get('schemaVersion')=='task-trace-v2' and t.get('purposeSplit') in ('generation','live')
            and t.get('state')=='SEALED' and not t.get('decision')),
            key=lambda t:(t.get('updated',0),t['id']))
    created=[]
    for split in ('generation','live'):
        scoped=[t for t in pending if t['purposeSplit']==split]
        for start in range(0,len(scoped),8):
            traces=scoped[start:start+8]
            status_id='stage4-'+digest([actor,[(t['id'],t['hash']) for t in traces]])[:24]
            stage_status={'id':status_id,'owner':actor,'traceIds':[t['id'] for t in traces],
                          'sourceRefs':[{'id':t['id'],'hash':t['hash']} for t in traces],
                          'state':'RUNNING','updated':time.time()}
            with loop.store.tx() as db:loop.store.put(db,'stage4_status',stage_status)
            try:
                payload,catalog=workflow.prepare(traces)
                extracted_raw,analysis_id=_request(loop,actor,'workflow_extract',payload,catalog)
                extracted=workflow.validate_extract(extracted_raw,payload,catalog)
                with loop.store.tx() as db:
                    analysis=loop.store.get(db,'workflow_analysis',analysis_id)
                    analysis['validatedOutput']={k:extracted[k] for k in ('frames','methods','relations','aliases')}
                    loop.store.put(db,'workflow_analysis',analysis)
                groups,routes=workflow.clusters(extracted,traces,catalog)
                merge_view=workflow.merge_input(extracted,groups,routes,payload)
                if merge_view['clusters']:
                    merged_raw,merge_id=_request(loop,actor,'workflow_merge',merge_view,
                        validator=lambda value:workflow.validate_merge(value,merge_view,extracted))
                    workflows,ledger=workflow.validate_merge(merged_raw,merge_view,extracted)
                else:
                    merge_id=None;workflows=[];ledger=[]
                deferred={m['id'] for f in extracted['frames'] if routes[f['id']][0]=='DEFER' for m in extracted['methods'] if m['frameId']==f['id']}
                ledger += [{'methodId':mid,'disposition':'DEFERRED','reason':'技能使用归因不明，不能确定NEW/UPDATE',
                            'duplicateOf':None} for mid in sorted(deferred)]
                with loop.store.tx() as db:
                    for source in traces:
                        current=loop.store.get(db,'trace',source['id'])
                        if not current or current['hash']!=source['hash'] or current['state']!='SEALED':raise ValueError('阶段4期间来源已修订')
                    ids=[]
                    for w in workflows:
                        frame_ids=w['frameIds']
                        route=routes[frame_ids[0]]
                        if any(routes[f]!=route for f in frame_ids):raise ValueError('workflow混合学习路由')
                        refs=[]
                        for f in frame_ids:
                            t=next(t for t in traces if t['id']==extracted['frameMap'][f]['traceId'])
                            if not any(r['id']==t['id'] for r in refs):refs.append({'id':t['id'],'revision':t['revision'],'hash':t['hash']})
                        workflow_hash=digest(w)
                        wid='workflow-'+digest([actor,workflow_hash,refs,route])[:24]
                        row={'id':wid,'owner':actor,'org':traces[0]['org'],'schemaVersion':'workflow-candidate-v1',
                             'action':route[0],'targetBase':route[1],'workflow':w,'workflowHash':workflow_hash,
                             'sourceRefs':refs,'analysisId':analysis_id,'mergeId':merge_id,
                             'methodLedger':[x for x in ledger if x['methodId'] in {m for f in frame_ids for m in extracted['frameMap'][f]['methodIds']}],
                             'created':time.time(),'status':'FROZEN'}
                        loop.store.put(db,'workflow',row)
                        ids.append(wid)
                        if route[0]=='NEW':
                            candidate_id='candidate-'+digest([wid,workflow_hash])[:24]
                            base=loop.store.get(db,'candidate',candidate_id)
                            if not base:
                                methods=[{k:extracted['methodMap'][mid].get(k) for k in ('id','action','inputs','outputs','conditions','parameters','completionCheck','reason')}
                                    for mid in w['includedMethodIds']]
                                public={'algorithm':'workflow-creator-v1','workflow':w,'methods':methods,
                                        'workflowHash':workflow_hash,'workflowId':wid,'traces':refs,'trace':refs[0]}
                                c={'id':candidate_id,'owner':actor,'org':traces[0]['org'],'mode':loop.agent.mode,
                                   'action':'NEW','target':None,'baseHash':None,'baseVersion':None,'status':'QUEUED',
                                   'input':public,'signature':digest([wid,workflow_hash]),'signatures':[wid],
                                   'created':time.time(),'notBefore':0,'title':w['title'][:80],
                                   'reason':'STAGE4_WORKFLOW','workflowId':wid,'analysisId':analysis_id}
                                loop.store.put(db,'candidate',c);created.append(c)
                                pool={'id':'pool-'+candidate_id,'owner':actor,'candidateId':candidate_id,
                                      'members':[{'taskId':r['id'],'revision':r['revision'],'hash':r['hash']} for r in refs],
                                      'algorithm':'workflow-frame-complete-link-v1','snapshotHash':workflow_hash,'state':'QUEUED'}
                                c['poolId']=pool['id'];loop.store.put(db,'pool',pool);loop.store.put(db,'candidate',c)
                        # UPDATE is a stage-9 work item. The workflow remains frozen but is not packaged by stage 5.
                    batch_id='decision-'+digest([actor,payload['sourceHash'],merge_view['sourceHash']])[:24]
                    decision={'id':batch_id,'owner':actor,'sourceHash':payload['sourceHash'],
                              'analysisId':analysis_id,'mergeId':merge_id,'frameRelations':extracted['relations'],
                              'clusters':groups,'routes':routes,'methodLedger':ledger,'workflowIds':ids,
                              'excludedTraceIds':[t['id'] for t in traces if not any(f['traceId']==t['id'] for f in extracted['frames'])]}
                    loop.store.put(db,'learning_decision',decision)
                    stage_status.update(state='PROCESSED',analysisId=analysis_id,mergeId=merge_id,
                                        learningDecisionId=batch_id,workflowIds=ids,updated=time.time())
                    loop.store.put(db,'stage4_status',stage_status)
                    for source in traces:
                        current=loop.store.get(db,'trace',source['id'])
                        linked=[wid for wid in ids if any(r['id']==source['id'] for r in loop.store.get(db,'workflow',wid)['sourceRefs'])]
                        current['decision']={'action':'NEW' if any(loop.store.get(db,'workflow',wid)['action']=='NEW' for wid in linked) else
                            'UPDATE' if linked else 'DEFER','reason':'WORKFLOW_DISCOVERED' if linked else 'NO_APPROVED_METHOD',
                            'workflowIds':linked,'learningDecisionId':batch_id}
                        current['learningHandoff']='STAGE4_PROCESSED'
                        loop.store.put(db,'trace',current)
                    loop.store.event(db,actor,time.time(),'workflow.discovered',{'decisionId':batch_id,'workflowCount':len(ids),'methodCount':len(ledger)})
            except Exception as exc:
                with loop.store.tx() as db:
                    stage_status.update(state='WAITING_BUDGET' if 'BUDGET_EXHAUSTED' in str(exc) else 'FAILED',
                                        error=str(exc)[:1000],updated=time.time())
                    loop.store.put(db,'stage4_status',stage_status)
                    loop.store.event(db,actor,time.time(),'workflow.failed',{'traceIds':[t['id'] for t in traces],
                                                                                 'reason':str(exc)[:350]})
                if stop_on_failure: return created
    return created


def _finalize(loop, actor, candidate_id, run_id, result, allowed_status):
    from .core import Conflict
    output=parse_creator_result(result['text'])
    if output.get('decision')=='BLOCKED':raise ValueError('creator无法封装冻结workflow: '+str(output.get('reason',''))[:300])
    if output.get('decision')!='CREATE':raise ValueError('creator未返回CREATE')
    if result.get('foundationRead',{}).get('status')!='FILE_READ':raise ValueError('未观察到官方skill-creator实际读取')
    work=loop.store.root/'workspaces'/run_id
    files=draft_files(work)
    with loop.store.tx() as db:
        c=loop._owned(db,'candidate',candidate_id,actor)
        loop._current(db,c)
        if c['status']!=allowed_status or c['runId']!=run_id:raise Conflict('封装候选/运行状态已变化')
        analysis=loop.store.get(db,'workflow_analysis',c['analysisId'])
        if not analysis:raise ValueError('私有来源索引缺失')
        phrases=[v['text'] for v in analysis.get('catalog',{}).values()]
        method_ids=c['input']['workflow']['includedMethodIds']
    checked=verify_files(files,method_ids,phrases,methods=c['input']['methods'],
                         coverageManifest=output.get('coverageManifest'))
    receipt=package(work,files)
    archive_check=verify_archive(work,receipt,files)
    result['package']=receipt
    result['validation']={'creatorRead':result['foundationRead'],'hostBundle':checked,
                          'officialPackage':archive_check,'businessOutcome':'NOT_RUN','consumerExecution':'NOT_RUN'}
    with loop.store.tx() as db:
        c=loop._owned(db,'candidate',candidate_id,actor)
        loop._current(db,c)
        if c['status']!=allowed_status or c['runId']!=run_id:raise Conflict('封装提交前状态已变化')
        db.execute('UPDATE runs SET result=? WHERE id=?',(json.dumps(result,ensure_ascii=False),run_id))
        c.update(status='READY',files=files,hash=digest(files),title=str(output.get('title') or c['title'])[:80],
                 validation=result['validation'],package=receipt)
        c.pop('error',None);loop.store.put(db,'candidate',c)
        pool=loop.store.get(db,'pool',c.get('poolId')) if c.get('poolId') else None
        if pool:pool['state']='READY';loop.store.put(db,'pool',pool)
        row=loop.store.get(db,'workflow',c['workflowId'])
        if row:row['status']='PACKAGED';row['candidateId']=c['id'];loop.store.put(db,'workflow',row)
        return c


def finalize_existing(loop, actor, candidate_id):
    """Revalidate a completed creator draft after a host-only packaging fix; no model request."""
    from .core import Conflict
    with loop.store.tx() as db:
        c=loop._owned(db,'candidate',candidate_id,actor)
        if c['input'].get('algorithm')!='workflow-creator-v1' or c['status']!='FAILED':raise Conflict('只有失败的新封装候选可复核')
        run_id=c.get('runId')
        row=db.execute('SELECT status,result FROM runs WHERE id=? AND owner=?',(run_id,actor)).fetchone()
        if not row or row['status']!='COMPLETED' or not row['result']:raise Conflict('原creator未完整返回，不能仅复核草稿')
        result=json.loads(row['result'])
    candidate=_finalize(loop,actor,candidate_id,run_id,result,'FAILED')
    with loop.store.tx() as db:
        loop.store.event(db,actor,time.time(),'creator.host_revalidated',{'candidateId':candidate_id,'runId':run_id})
    return candidate


def generate(loop, actor, candidate_id):
    from .core import Conflict
    with loop.store.tx() as db:
        c=loop._owned(db,'candidate',candidate_id,actor)
        if c['status']!='QUEUED':return c
        if c['mode']!=loop.agent.mode:raise Conflict('候选运行模式不符')
        loop._current(db,c)
        run_id='creator-'+c['id']+('-retry'+str(c['retryCount']) if c.get('retryCount') else '')
        public={k:c['input'][k] for k in ('algorithm','workflow','methods','workflowHash','workflowId')}
        if not loop._reserve(db,actor,'workflow_creator',run_id,public):
            c['error']='学习额度不足，待下一UTC日或调整额度';loop.store.put(db,'candidate',c);return c
        c.update(status='GENERATING',runId=run_id);loop.store.put(db,'candidate',c)
        pool=loop.store.get(db,'pool',c.get('poolId')) if c.get('poolId') else None
        if pool:pool['state']='FROZEN';loop.store.put(db,'pool',pool)
    try:
        result=loop._execute(actor,'workflow_creator',run_id,public)
        return _finalize(loop,actor,candidate_id,run_id,result,'GENERATING')
    except Exception as exc:
        with loop.store.tx() as db:
            c=loop._owned(db,'candidate',candidate_id,actor)
            if c['status']=='GENERATING':
                c.update(status='FAILED',error=str(exc)[:1500]);loop.store.put(db,'candidate',c)
                pool=loop.store.get(db,'pool',c.get('poolId')) if c.get('poolId') else None
                if pool:pool['state']='FAILED';loop.store.put(db,'pool',pool)
        return c
