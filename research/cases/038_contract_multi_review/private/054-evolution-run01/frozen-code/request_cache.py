"""Validated structured requests with immutable attempts and explicit bounded retry.

The request index is resumable bookkeeping, never a learning decision. Budget waits
do not consume attempts; failures do not authorize another provider call.
"""
import hashlib
import os
from pathlib import Path
import time
from . import runtime

VERSION = 'validated-request-cache-v1'
KINDS = {'front_analysis', 'workflow_analysis'}


def configuration(loop, purpose):
    from . import pair_detection, recovery, workflow
    modules = {'detect_pairs': pair_detection, 'recover_trace': recovery,
               'workflow_extract': workflow, 'workflow_merge': workflow}
    module = modules[purpose]
    helper = getattr(runtime, 'request_config', None)
    if helper:
        config = helper(purpose)
    else:
        prompt = {'detect_pairs': pair_detection.INSTRUCTIONS, 'recover_trace': recovery.INSTRUCTIONS,
                  'workflow_extract': workflow.EXTRACT_PROMPT, 'workflow_merge': workflow.MERGE_PROMPT}[purpose]
        config = {'prompt': prompt, 'model': os.getenv('DEMO_MODEL'),
                  'baseUrl': os.getenv('DEMO_BASE_URL', 'https://api.openai.com/v1').rstrip('/'),
                  'api': os.getenv('DEMO_MODEL_API', 'openai-completions'), 'temperature': 0,
                  'maxTokens': 8000 if purpose == 'detect_pairs' else 14000,
                  'timeoutSeconds': max(10, min(240, int(os.getenv('DEMO_DETECT_TIMEOUT', '180')))),
                  'networkMode': os.getenv('DEMO_NETWORK_MODE', 'environment')}
    return {'version': VERSION, 'mode': loop.agent.mode, 'runtime': config,
            'validatorVersion': getattr(module, 'VALIDATOR_VERSION', getattr(module, 'VERSION', 'source-bound')),
            'validatorSourceSha256': hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
            'runtimeSourceSha256': hashlib.sha256(Path(runtime.__file__).read_bytes()).hexdigest()}


def retry_request(loop, actor, kind, request_id, reason, max_attempts=2):
    """Authorize one additional attempt; dispatch only on the next normal process call."""
    if kind not in KINDS: raise ValueError('未知结构化请求类型')
    if not isinstance(reason, str) or not reason.strip(): raise ValueError('重试必须提供明确原因')
    if type(max_attempts) is not int or not 1 <= max_attempts <= 3:
        raise ValueError('max_attempts必须为1—3的预定有限上限')
    with loop.store.tx() as db:
        row = loop.store.get(db, kind+'_request', request_id)
        if not row or row['owner'] != actor: raise ValueError('请求不存在或不可访问')
        if row['state'] == 'RUNNING':
            run = db.execute('SELECT status FROM runs WHERE id=?', (row['attempts'][-1],)).fetchone()
            if not run or run['status'] not in ('FAILED', 'INTERRUPTED', 'UNKNOWN'):
                raise ValueError('原派发仍在运行，不能创建并行重试')
        elif row['state'] != 'FAILED':
            raise ValueError('只有失败/已中断请求可显式授权重试；预算等待直接续跑')
        if row['attemptCount'] >= max_attempts: raise ValueError('达到预定最大attempt数')
        grant = {'id':request_id+':retry:'+str(row['attemptCount']+1), 'owner':actor,
                 'requestId':request_id, 'reason':reason.strip(), 'maxAttempts':max_attempts,
                 'previousRunId':row['attempts'][-1], 'at':time.time()}
        loop.store.put(db, kind+'_retry', grant)
        row.update(state='RETRY_AUTHORIZED', retryAuthorized=True, retryGrantId=grant['id'])
        loop.store.put(db, kind+'_request', row)
        loop.store.event(db, actor, time.time(), 'analysis.retry_authorized', grant)
        return row


def request(loop, actor, kind, purpose, payload, validator, metadata=None):
    if kind not in KINDS or not callable(validator): raise ValueError('结构化请求必须声明校验器')
    config = configuration(loop, purpose)
    request_id = purpose+'-'+runtime.digest([actor, payload, config])[:24]
    field = 'state' if kind == 'front_analysis' else 'status'
    budget_wait = False
    with loop.store.tx() as db:
        index = loop.store.get(db, kind+'_request', request_id)
        if index and index['state'] == 'READY':
            row = loop.store.get(db, kind, index['attempts'][-1])
            if not row or row[field] != 'READY': raise ValueError('有效缓存索引不完整')
            validator(row['output'])
            return row['output'], row['id']
        if index and index['state'] in ('FAILED', 'RUNNING'):
            raise ValueError('该派发失败或尚未完成，保留原attempt；不自动重试。requestId='+request_id)
        index = index or {'id':request_id, 'owner':actor, 'purpose':purpose,
                           'sourceHash':payload['sourceHash'], 'configuration':config,
                           'configurationHash':runtime.digest(config), 'attemptCount':0, 'attempts':[]}
        if index['attemptCount'] and not index.get('retryAuthorized'):
            raise ValueError('新的模型attempt必须显式授权')
        attempt = index['attemptCount']+1
        run_id = request_id if attempt == 1 else request_id+'-attempt'+str(attempt)
        if not loop._reserve(db, actor, purpose, run_id, payload):
            index.update(state='WAITING_BUDGET', updated=time.time())
            loop.store.put(db, kind+'_request', index)
            budget_wait = True
        else:
            index.update(state='RUNNING', attemptCount=attempt, attempts=index['attempts']+[run_id],
                         retryAuthorized=False, updated=time.time())
            loop.store.put(db, kind+'_request', index)
            row = {'id':run_id, 'owner':actor, field:'RUNNING', 'purpose':purpose,
                   'requestId':request_id, 'attempt':attempt, 'sourceHash':payload['sourceHash'],
                   'configurationHash':index['configurationHash'], **(metadata or {})}
            loop.store.put(db, kind, row)
    if budget_wait: raise ValueError('BUDGET_EXHAUSTED：材料保留待处理，未消耗attempt。requestId='+request_id)
    output = None
    try:
        result = loop._execute(actor, purpose, run_id, payload)
        output = runtime.parse_object(result['text'])
        validator(output)
    except Exception as exc:
        with loop.store.tx() as db:
            row.update({field:'FAILED', 'error':str(exc)[:1500], 'finished':time.time()})
            if output is not None: row['output'] = output
            loop.store.put(db, kind, row)
            index.update(state='FAILED', error=str(exc)[:1500], updated=time.time())
            loop.store.put(db, kind+'_request', index)
        raise
    with loop.store.tx() as db:
        row.update({field:'READY', 'output':output, 'finished':time.time()})
        loop.store.put(db, kind, row)
        index.update(state='READY', updated=time.time())
        index.pop('error', None)
        loop.store.put(db, kind+'_request', index)
    return output, run_id
