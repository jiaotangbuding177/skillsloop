"""Experiment R/W pipeline: bounded semantic proposals, deterministic frozen skills."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from uuid import uuid4
from . import bootstrap, relational
from .pipeline import Requests, normalize_input, prepare_events, write_json
from .runtime import digest, request_config

VERSION='ecv-recovery-induction-v2'
PURPOSES=('library_relational_extract','local_experience_extract')


def source_configuration():
    base=Path(__file__).parent
    names=tuple(sorted(p.stem for p in base.glob('*.py')))
    return {'version':VERSION,'sources':{n:hashlib.sha256((base/(n+'.py')).read_bytes()).hexdigest() for n in names},
        'entrypointSha256':hashlib.sha256((base.parent/'trace_to_skills.py').read_bytes()).hexdigest(),
        'requests':{p:request_config(p) for p in PURPOSES},
        'packagingSources':{n:hashlib.sha256((bootstrap.CREATOR/n).read_bytes()).hexdigest()
            if (bootstrap.CREATOR/n).is_file() else None
            for n in ('SKILL.md','scripts/quick_validate.py','scripts/package_skill.py')}}


def batches(experience, max_sessions=4, max_chars=48000):
    """Pack whole sessions; never silently truncate their last failure."""
    if type(max_sessions) is not int or max_sessions<1:raise ValueError('batch_sessions必须为正整数')
    if type(max_chars) is not int or max_chars<1000:raise ValueError('batch_chars至少1000')
    groups={};targets={}
    for row in experience['events']:
        session=row['sessionId'];groups.setdefault(session,[]).append(row)
        ids=targets.setdefault(session,{session});ids.add(row['id'])
        ids.update(c['id'] for c in row.get('toolCalls',[]))
        if row.get('callId'):ids.add(row['callId'])
        ids.update(a['id'] for a in row.get('artifacts',[]) if isinstance(a,dict) and a.get('id'))
    evaluation_sessions={}
    for v in experience['evaluations']:
        if any(not any(target in ids for ids in targets.values()) for target in v['targetIds']):
            raise ValueError('评价目标未全部出现在输入中：'+v['id'])
        owners={s for s,ids in targets.items() if set(v['targetIds']) & ids}
        if len(owners)!=1:raise ValueError('评价目标缺失或跨独立会话歧义：'+v['id'])
        evaluation_sessions[v['id']]=next(iter(owners))
    def pack(sessions):
        return {'events':[r for s in sessions for r in groups[s]],'context':deepcopy(experience['context']),
            'evaluations':[v for v in experience['evaluations'] if evaluation_sessions[v['id']] in sessions]}
    result=[];current=[]
    for session in groups:
        if len(json.dumps(pack([session]),ensure_ascii=False))>max_chars:
            raise ValueError('SESSION_INPUT_BUDGET：完整会话超过batch_chars；提高显式预算或选择更短材料，禁止自动截断：'+session)
        trial=[*current,session]
        if current and (len(trial)>max_sessions or len(json.dumps(pack(trial),ensure_ascii=False))>max_chars):
            result.append(pack(current));current=[]
        current.append(session)
    if current:result.append(pack(current))
    return result


def prepare_batches(value, batch_sessions=4, batch_chars=48000):
    experience,mapping=normalize_input(value);prepared=[]
    for i,item in enumerate(batches(experience,batch_sessions,batch_chars),1):
        events,pairs,pending=prepare_events(item)
        payload,aliases=relational.prepare(pairs,item['context'],item['evaluations'])
        prepared.append({'id':f'batch-{i:03d}','experience':item,'events':events,
            'pairs':pairs,'pending':pending,'payload':payload,'aliases':aliases})
    return experience,mapping,prepared


def _recover(obj,payload,aliases):
    output=relational.compile_result(obj,payload,aliases)
    if any(len(t.get('sessionIds',[]))>1 for t in output['traces']):
        raise ValueError('独立实验实例被恢复为跨会话任务；保留响应，不自动重试')
    return output


def _summary(requests,state,root):
    starts=[r.get('modelRequestStarts') for r in requests.ledger]
    state.update(dispatchesThisInvocation=requests.started,requestLedger=requests.ledger,
        modelRequestStartsKnownThisInvocation=sum(n for n in starts if type(n) is int),
        modelRequestStartsThisInvocation=None if any(n is None for n in starts) else sum(starts),
        unknownStartReceiptsThisInvocation=sum(n is None for n in starts))
    tokens=0;unknown=0
    for r in requests.ledger:
        if r.get('status')=='CACHED' or r.get('usageFromPriorInvocation'):continue
        u=r.get('usage')
        if not isinstance(u,dict):unknown+=1;continue
        total=u.get('total',u.get('total_tokens'))
        if total is None:total=sum(u.get(k,0) or 0 for k in ('input_tokens','output_tokens','cache_creation_input_tokens','cache_read_input_tokens'))
        tokens+=total
    state['usageThisInvocation']={'knownTokens':tokens,'unknownUsageReceipts':unknown,'costUsd':None}
    write_json(root/'requests_ledger.json',requests.ledger)


def build(value,output,max_calls=2,agent=None,responses=None,official=True,reuse_requests=None,
          batch_sessions=4,batch_chars=48000):
    from . import local_experience, workflow_induction, library_export
    root=Path(output).resolve();root.mkdir(parents=True,exist_ok=True)
    lock=root/'.pipeline.lock'
    try:handle=lock.open('x',encoding='utf-8')
    except FileExistsError as exc:raise ValueError('输出目录已有运行锁，不并发覆盖') from exc
    invocation=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid4().hex[:8]
    requests=None;state=None
    try:
        with handle:handle.write(json.dumps({'pid':os.getpid(),'invocation':invocation}))
        experience,mapping,prepared=prepare_batches(value,batch_sessions,batch_chars)
        config=source_configuration()
        identity={'input':value,'config':config,'official':official,'batchSessions':batch_sessions,
            'batchChars':batch_chars,'mode':'response-replay' if responses is not None else getattr(agent,'mode','openclaw'),
            'responses':responses}
        fingerprint=digest(identity);prior_path=root/'run.json'
        if prior_path.exists():
            prior=json.loads(prior_path.read_text(encoding='utf-8'))
            if prior.get('fingerprint')!=fingerprint:raise ValueError('不同输入、代码或模型配置不能覆盖同一运行目录')
            if prior.get('status')=='COMPLETED':
                library_export.verify_frozen(root)
                result={**prior,'reusedFrozenLibrary':True,'dispatchesThisInvocation':0,
                    'modelRequestStartsThisInvocation':0,'modelRequestStartsKnownThisInvocation':0,
                    'unknownStartReceiptsThisInvocation':0,'requestLedger':[],
                    'usageThisInvocation':{'knownTokens':0,'unknownUsageReceipts':0,'costUsd':None}}
                write_json(root/'invocations'/f'{invocation}.json',result)
                return result
        elif any(p.name!='.pipeline.lock' for p in root.iterdir()):
            raise ValueError('输出目录非空且没有本管道运行清单，拒绝覆盖')
        if official and any(not (bootstrap.CREATOR/n).is_file() for n in ('scripts/package_skill.py','scripts/quick_validate.py')):
            raise ValueError('官方skill-creator打包脚本缺失；模型请求前停止，可显式使用--structural-only')
        requests=Requests(root,max_calls,agent,responses,reuse_requests)
        state={'version':VERSION,'fingerprint':fingerprint,'status':'RUNNING','inputHash':digest(value),
            'configuration':config,'stages':{},'skills':[],'batches':[],'batchCount':len(prepared),
            'maxNewCalls':max_calls,'plannedUpperBoundDispatches':2*len(prepared),
            'semanticValidation':'NOT_INDEPENDENTLY_VERIFIED'}
        write_json(prior_path,state);write_json(root/'input.json',value)
        write_json(root/'normalized_input.json',{'experience':experience,'mapping':mapping})
        base=Path(__file__).parent
        for name,expected in config['sources'].items():
            data=(base/(name+'.py')).read_bytes()
            if hashlib.sha256(data).hexdigest()!=expected:raise ValueError('运行准备过程中源码已变化，停止避免混用版本')
            dest=root/'source_snapshot'/'skilldemo'/(name+'.py');dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(data)
        (root/'source_snapshot'/'trace_to_skills.py').write_bytes((base.parent/'trace_to_skills.py').read_bytes())
        if (responses is None and reuse_requests is None and not (root/'requests').exists()
                and max_calls<2*len(prepared)):
            raise ValueError(f'MODEL_CALL_BUDGET_PRECHECK：完整冷启动需预留至多{2*len(prepared)}次请求；当前{max_calls}，未开始调用')
        traces=[];methods=[];unresolved=[];unassigned=[];source_catalog=[]
        for batch in prepared:
            folder=root/'batches'/batch['id']
            write_json(folder/'01_collected.json',{k:batch[k] for k in ('events','pairs','pending')})
            payload,aliases=batch['payload'],batch['aliases']
            raw=requests.request(PURPOSES[0],payload,lambda obj:_recover(obj,payload,aliases))
            recovered=_recover(raw,payload,aliases)
            for trace in recovered['traces']:
                trace['revision']=1;trace['hash']=digest({k:v for k,v in trace.items() if k!='hash'})
            write_json(folder/'02_recovered.json',recovered)
            traces.extend(recovered['traces']);unresolved.extend(recovered['unresolved'])
            local={'methods':[],'unassigned':[]}
            if recovered['traces']:
                view=local_experience.prepare(recovered['traces'],batch['experience'])
                write_json(folder/'03_local_input.json',view)
                public_view=local_experience.model_input(view)
                raw=requests.request(PURPOSES[1],public_view,lambda obj:local_experience.compile_result(obj,view))
                local=local_experience.compile_result(raw,view)
                methods.extend(local['methods']);unassigned.extend(local.get('unassigned',[]))
                source_catalog.extend(local.get('sourceCatalog',[]))
            write_json(folder/'03_local_experience.json',local)
            state['batches'].append({'id':batch['id'],'taskCount':len(recovered['traces']),
                'methodCount':len(local['methods'])})
            write_json(root/'run.json',state)
        state['stages']['recovery']='READY'
        write_json(root/'02_recovered.json',{'traces':traces,'unresolved':unresolved})
        write_json(root/'03_local_experience.json',{'methods':methods,'unassigned':unassigned,'sourceCatalog':source_catalog})
        induced=workflow_induction.induce(methods)
        write_json(root/'04_workflows.json',induced);state['stages']['aggregation']='READY'
        retained=[w for w in induced['workflows'] if library_export.is_exportable(w)]
        deferred=[{'workflowId':w['id'],'memberIds':w['memberIds'],
                   'reason':'只有承诺或计划，没有实际方法；保留完整候选记录，不封装'}
                  for w in induced['workflows'] if not library_export.is_exportable(w)]
        write_json(root/'05_deferred_workflows.json',deferred)
        skills=library_export.publish(root,retained,official)
        state.update(skills=skills,skillCount=len(skills),recoveredTaskCount=len(traces),
            localMethodCount=len(methods),deferredWorkflowCount=len(deferred),
            unresolvedCount=len(unresolved),unassignedEvidenceCount=len(unassigned))
        state['stages']['packaging']='READY' if skills else 'NO_CANDIDATES'
        _summary(requests,state,root)
        frozen=library_export.freeze(root,skills,{'inputHash':state['inputHash'],'algorithm':VERSION,
            'runFingerprint':fingerprint,'sourceConfiguration':config,'methodCount':len(methods),
            'requestLedger':state['requestLedger']})
        library_export.verify_frozen(root,require_completed_run=False)
        state.update(status='COMPLETED',frozenManifest='frozen_manifest.json',
            libraryPath=str(root/'skills'),manifestHash=frozen['manifestHash'])
        return state
    except Exception as exc:
        if state is not None:
            state.update(status='FAILED',error=str(exc))
            path=root/'frozen_manifest.json'
            if path.exists():
                failed=json.loads(path.read_text(encoding='utf-8'))
                failed.update(status='FAILED',error='运行未完成；不得接入正式实验')
                failed['manifestHash']=digest({k:v for k,v in failed.items() if k!='manifestHash'})
                write_json(path,failed)
        raise
    finally:
        if state is not None:
            if requests is not None:_summary(requests,state,root)
            write_json(root/'run.json',state);write_json(root/'invocations'/f'{invocation}.json',state)
        lock.unlink()
