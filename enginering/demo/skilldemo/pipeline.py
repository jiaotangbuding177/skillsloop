"""File-in / skill-library-out research pipeline; no users, server or database."""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import time
import os
from datetime import datetime, timezone
from uuid import uuid4

from . import intake, evidence, relational, workflow, relational_workflow, creator, bootstrap
from .runtime import OpenClawAgent, RuntimeFailure, digest, parse_object, HEADINGS, request_config

VERSION = 'ecv-to-skills-v1'
SPACE = 'offline-library-workspace'


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def _calls(rows):
    if not isinstance(rows, list):
        raise ValueError('toolCalls必须是原始调用数组')
    result = []
    for raw in rows:
        if not isinstance(raw, dict):
            raise ValueError('工具调用必须是对象')
        function = raw.get('function') or {}
        args = raw.get('arguments', raw.get('args', function.get('arguments')))
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                pass  # Keep the original string; do not repair arguments.
        item = {**deepcopy(raw), 'id': raw.get('id') or raw.get('callId'),
                'name': raw.get('name') or function.get('name'), 'arguments': args}
        if not isinstance(item['id'], str) or not item['id'].strip():
            raise ValueError('原始工具调用缺少稳定调用ID')
        result.append(item)
    return result


def normalize_input(value):
    """Normalize only observable messages. Never import reward_info or task gold."""
    if not isinstance(value, dict):
        raise ValueError('输入应为X=(E,C,V) JSON对象')
    ecv = bool(set(value) & {'E', 'C', 'V'})
    allowed = {'E', 'C', 'V', 'sessionId'} if ecv else {'events', 'context', 'evaluations', 'sessionId'}
    if set(value) - allowed:
        raise ValueError('输入只接收E/C/V或events/context/evaluations；不自动读取隐藏答案和reward_info')
    rows = value.get('E' if ecv else 'events')
    if not isinstance(rows, list) or not rows or len(rows) > 5000:
        raise ValueError('E需要1—5000条原始事件；超预算材料不截断')
    context = evidence.normalize_context(value.get('C' if ecv else 'context', []))
    evaluations = evidence.normalize_evaluations(value.get('V' if ecv else 'evaluations', []))
    normalized, mappings, seen = [], [], set()
    default_session = value.get('sessionId') or 'imported-conversation'
    for index, raw in enumerate(rows, 1):
        if not isinstance(raw, dict):
            raise ValueError('E中的事件必须是对象')
        role = raw.get('role')
        if role not in ('user', 'assistant', 'tool'):
            raise ValueError('E只含可见user/assistant/tool；公开背景请显式放C')
        session = raw.get('sessionId') or raw.get('session') or default_session
        source_id = raw.get('id') or raw.get('messageId') or f'{session}:message-{index}'
        if (session, source_id) in seen:
            raise ValueError('同一会话原消息ID重复，不能覆盖历史')
        seen.add((session, source_id))
        row = {**deepcopy(raw), 'id': source_id, 'sessionId': session,
               'sourceOrder': raw.get('sourceOrder', raw.get('order', raw.get('sourceLine', index))),
               'orderBasis': raw.get('orderBasis', 'EXPORTED_POSITION'),
               'content': raw.get('content'), 'runId': raw.get('runId') or raw.get('run_id')}
        # τ²/native spellings are structural aliases, not inferred task edges.
        if 'tool_calls' in raw or 'toolCalls' in raw:
            row['toolCalls'] = _calls(raw.get('toolCalls', raw.get('tool_calls')))
        if role == 'tool':
            row['callId'] = raw.get('callId') or raw.get('toolCallId') or raw.get('tool_call_id') or raw.get('id')
            row['name'] = raw.get('toolName') or raw.get('name')
            row['eventType'] = raw.get('eventType', 'RESULT')
            row['result'] = deepcopy(raw.get('result', raw.get('content')))
            if raw.get('error') is True:
                row['executionStatus'] = 'FAILED'
            elif raw.get('error') is False:
                row['executionStatus'] = 'SUCCEEDED'
        if raw.get('requestor') in ('user', 'assistant'):
            row['requestor'] = raw['requestor']
        normalized.append(row)
        mappings.append({'inputPosition': index, 'sessionId': session, 'sourceId': source_id,
                         'idGenerated': not bool(raw.get('id') or raw.get('messageId')),
                         'orderBasis': row['orderBasis']})
    return {'events': normalized, 'context': context, 'evaluations': evaluations}, mappings


def prepare_events(experience):
    events = [intake.event(SPACE, row, 'generation', index)
              for index, row in enumerate(experience['events'], 1)]
    groups = {}
    for row in events:
        groups.setdefault(row['session'], []).append(row)
    pairs, unresolved = [], []
    for rows in groups.values():
        found, pending = intake.assemble(rows)
        pairs.extend(found)
        unresolved.extend(pending)
    if not pairs:
        raise ValueError('没有可整理的用户回合；事件保留，不能虚构任务')
    covered = {sid for pair in pairs for sid in pair['sourceEventIds']}
    pairs[0]['unassignedToolEvents'] = [row for row in events
        if row['role'] == 'tool' and row['id'] not in covered]
    return events, pairs, unresolved


def source_configuration():
    names = ('pipeline', 'intake', 'evidence', 'relational', 'workflow',
             'relational_workflow', 'creator', 'runtime', 'pair_detection',
             'recovery', 'workflow_index', 'bootstrap')
    root = Path(__file__).parent
    return {'version': VERSION,
            'sources': {name: hashlib.sha256((root / (name+'.py')).read_bytes()).hexdigest() for name in names},
            'entrypointSha256':hashlib.sha256((root.parent/'trace_to_skills.py').read_bytes()).hexdigest(),
            'packagingSources':{name:(hashlib.sha256((bootstrap.CREATOR/name).read_bytes()).hexdigest() if (bootstrap.CREATOR/name).is_file() else None)
                for name in ('SKILL.md','scripts/package_skill.py','scripts/quick_validate.py')},
            'requests': {purpose: request_config(purpose) for purpose in
                         ('relational_extract', 'workflow_extract', 'workflow_merge')}}


class Requests:
    """A bounded, validated file cache; no automatic retry or hidden fixture fallback."""
    def __init__(self, root, max_calls=3, agent=None, responses=None, reuse_requests=None):
        if type(max_calls) is not int or max_calls < 0:
            raise ValueError('max_calls必须是非负整数')
        self.root, self.max_calls = Path(root), max_calls
        self.agent = agent or OpenClawAgent()
        self.responses = responses
        self.reuse_requests = Path(reuse_requests).resolve() if reuse_requests else None
        if self.reuse_requests and not self.reuse_requests.is_dir():
            raise ValueError('复用请求来源目录不存在')
        self.started = 0
        self.ledger = []
        self.mode = 'response-replay' if responses is not None else getattr(self.agent, 'mode', 'custom-fixture')

    def saved_response(self, purpose, identity, payload):
        """Explicit reuse only, with exact request/config and untampered raw reply."""
        if not self.reuse_requests or self.responses is not None:return None
        source = self.reuse_requests/'requests' if (self.reuse_requests/'requests').is_dir() else self.reuse_requests
        folder = source/(purpose+'-'+identity[:24])
        if not (folder/'record.json').is_file():return None
        old=json.loads((folder/'record.json').read_text(encoding='utf-8'))
        if old.get('status')!='READY':return None  # Failed attempts are not silently retried/reclassified.
        material=json.loads((folder/'payload.json').read_text(encoding='utf-8'))
        result=json.loads((folder/'result.json').read_text(encoding='utf-8'))
        if (old.get('requestId')!=identity or old.get('mode')!=self.mode
                or old.get('payloadHash')!=digest(payload) or digest(material)!=digest(payload)
                or old.get('resultHash')!=digest(result)
                or old.get('output')!={**parse_object(result['text']),'sourceHash':payload['sourceHash']}):
            raise ValueError('显式复用来源与原始请求/响应不一致，不得降级为重新调用')
        return {**result,'modelRequestStarts':0,'runtime':'saved-response-revalidation',
            'usageFromPriorInvocation':True,
            'reusedRequest':{'folder':str(folder),'requestId':identity,
                'originalResultHash':digest(result),'originalModelRequestStarts':old.get('modelRequestStarts'),
                'originalRuntime':result.get('runtime')}}

    def request(self, purpose, payload, validator):
        identity = digest([purpose, payload, request_config(purpose), self.mode])
        folder = self.root / 'requests' / (purpose+'-'+identity[:24])
        record_path = folder / 'record.json'
        if record_path.exists():
            old = json.loads(record_path.read_text(encoding='utf-8'))
            if old['status'] != 'READY':
                raise ValueError('旧请求未成功，保留记录；新attempt请使用新输出目录，不自动重发')
            saved_payload = json.loads((folder/'payload.json').read_text(encoding='utf-8'))
            saved_result = json.loads((folder/'result.json').read_text(encoding='utf-8'))
            if (old.get('requestId') != identity or old.get('payloadHash') != digest(payload)
                    or digest(saved_payload) != digest(payload) or old.get('resultHash') != digest(saved_result)):
                raise ValueError('缓存请求或响应内容指纹不一致，不能复用')
            bound = {**parse_object(saved_result['text']), 'sourceHash':payload['sourceHash']}
            if bound != old['output']:
                raise ValueError('缓存输出与原始响应不一致，不能冒充原模型回复')
            validator(old['output'])
            self.ledger.append({'purpose': purpose, 'status': 'CACHED', 'requestId': identity,
                                'modelRequestStarts': 0})
            return old['output']
        saved = self.saved_response(purpose, identity, payload)
        if self.responses is None and saved is None and self.started >= self.max_calls:
            raise ValueError('MODEL_CALL_BUDGET：达到本轮上限，材料保留，不追加调用')
        folder.mkdir(parents=True, exist_ok=True)
        write_json(folder/'payload.json', payload)
        record = {'purpose': purpose, 'requestId': identity, 'payloadHash': digest(payload),
                  'mode': self.mode, 'status': 'RUNNING', 'modelRequestStarts': 0}
        write_json(record_path, record)
        started = time.monotonic()
        try:
            if self.responses is not None:
                rows = self.responses.get('responses', [])
                match = [r for r in rows if r.get('purpose') == purpose and r.get('payloadHash') == digest(payload)]
                if len(match) != 1:
                    raise ValueError('回放需要唯一且与本次payloadHash完全一致的保存响应')
                result = {'text': json.dumps(match[0]['output'], ensure_ascii=False),
                          'usage': None, 'runtime': 'disclosed-response-replay', 'modelRequestStarts': 0}
            elif saved is not None:
                result = saved
            else:
                self.started += 1
                # A host dispatch is not an observed HTTP start. The adapter's
                # receipt determines actual starts; a generic error stays unknown.
                record['modelRequestStarts'] = None
                write_json(record_path, record)
                result = self.agent.run(purpose, payload, folder)
            record.update(usage=result.get('usage'), runtime=result.get('runtime'),
                          modelRequestStarts=result.get('modelRequestStarts',record['modelRequestStarts']),
                          elapsedMs=round((time.monotonic()-started)*1000))
            if saved is not None:
                record.update(reusedRequest=saved['reusedRequest'],usageFromPriorInvocation=True)
            write_json(folder/'result.json', result)
            record['resultHash'] = digest(result)
            output = parse_object(result['text'])
            # Actual invocation plus exact saved request is the transport binding.
            record['sourceBinding'] = {'payloadHash': digest(payload), 'modelEcho': output.get('sourceHash'),
                                       'basis': 'EXACT_SAVED_RESPONSE_REVALIDATED' if saved is not None else
                                                'EXACT_LOCAL_REQUEST' if self.responses is None else 'EXACT_REPLAY_PAYLOAD'}
            output = {**output, 'sourceHash': payload['sourceHash']}
            validator(output)
            record.update(status='READY', output=output)
            write_json(record_path, record)
            self.ledger.append({k: v for k, v in record.items() if k != 'output'})
            return output
        except Exception as exc:
            receipt = exc.result if isinstance(exc, RuntimeFailure) else {}
            record.update(status='FAILED', error=str(exc), usage=receipt.get('usage', record.get('usage')),
                          modelRequestStarts=receipt.get('modelRequestStarts',record.get('modelRequestStarts')),
                          elapsedMs=round((time.monotonic()-started)*1000))
            write_json(record_path, record)
            self.ledger.append({k: v for k, v in record.items() if k != 'output'})
            raise


def _seed_files():
    # The frozen workflow is the authoring source; packaging does not call a model.
    md = '---\nname: workflow-candidate\ndescription: 根据已归纳工作流封装候选技能。\n---\n# 工作流候选\n\n## 市场信息\n'
    md += '\n'.join('### '+heading+'\n按当前工作流与适用要求使用。\n' for heading in HEADINGS)
    return [{'path': 'SKILL.md', 'content': md}]


def package_workflow(root, row, methods, ordinal, official=True):
    public_methods = [relational_workflow.public_method(method) for method in methods]
    public = relational_workflow.public_workflow(row, public_methods)
    files, assembly = creator.assemble_step_scoped_files(_seed_files(), public, public_methods)
    if assembly is None:
        raise ValueError('轻管道要求宿主逐步骤封装契约，不能回退为自由草稿')
    check = creator.verify_files(files, public['includedMethodIds'], methods=public_methods,
        coverageManifest=assembly['methodCoverageManifest'], workflow=public,
        stepCoverageManifest=assembly['stepCoverageManifest'])
    name = 'skill-'+digest([public, files])[:16]
    directory = root/'skills'/name
    directory.mkdir(parents=True, exist_ok=True)
    for item in files:
        path = directory/item['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != item['content'].encode('utf-8'):
            raise ValueError('技能内容指纹冲突，不能覆盖已有技能')
        path.write_bytes(item['content'].encode('utf-8'))
    origin = {'workflow': row, 'methods': methods, 'assembly': assembly, 'checks': check}
    evidence_path = root/'evidence'/f'{name}.json'
    if evidence_path.exists():
        prior = json.loads(evidence_path.read_text(encoding='utf-8'))
        originals = [{k:v for k,v in prior.items() if k != 'additionalOrigins'}, *prior.get('additionalOrigins', [])]
        if all(digest(old) != digest(origin) for old in originals):
            prior.setdefault('additionalOrigins', []).append(origin)
            write_json(evidence_path, prior)
    else:
        write_json(evidence_path, origin)
    receipt = None
    if official:
        workspace = root/'packaging'/name
        workspace.mkdir(parents=True, exist_ok=True)
        receipt_path = workspace/'receipt.json'
        if receipt_path.exists():
            receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
        else:
            receipt = bootstrap.package(workspace, files)
            write_json(receipt_path, receipt)
        creator.verify_archive(workspace, receipt, files)
    return {'id': name, 'title': row['title'], 'entry': f'skills/{name}/SKILL.md',
            'methodCount': len(methods), 'steps': len(public['steps']), 'hash': digest(files),
            'validation': 'STRUCTURAL_AND_OFFICIAL_PACKAGE' if official else 'STRUCTURAL_ONLY',
            'semanticValidation': 'NOT_INDEPENDENTLY_VERIFIED',
            'package': f'packaging/{name}/'+receipt['path'].replace('\\','/') if receipt else None,
            'lessonCounts': {kind: sum(m.get('lessonType', 'PROCEDURE') == kind for m in public_methods)
                             for kind in ('PROCEDURE', 'FAILURE_WARNING', 'HYPOTHESIS')}}


def _build(value, output, max_calls=3, agent=None, responses=None, official=True, reuse_requests=None):
    """Run the two core algorithms and compile a fresh, unadopted skill library."""
    root = Path(output).resolve()
    experience, mapping = normalize_input(value)
    config = source_configuration()
    signature = digest([value, config, official, responses, getattr(agent, 'mode', None),
                        str(Path(reuse_requests).resolve()) if reuse_requests else None])
    manifest_path = root/'run.json'
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text(encoding='utf-8'))
        if previous['fingerprint'] != signature:
            raise ValueError('输出目录已有不同输入、配置或源码的运行；请使用新目录')
    elif root.exists() and any(p.name != '.pipeline.lock' for p in root.iterdir()):
        raise ValueError('输出目录非空且无本管道清单，拒绝覆盖')
    root.mkdir(parents=True, exist_ok=True)
    requests = Requests(root, max_calls, agent, responses, reuse_requests)
    state = {'version': VERSION, 'fingerprint': signature, 'inputHash': digest(value),
             'configuration': config, 'mode': requests.mode, 'status': 'RUNNING',
             'stages': {}, 'modelRequestStartsThisInvocation': 0, 'skills': [],
             'scope': 'FRESH_LIBRARY_DISCOVERY_NO_ADOPTION_OR_ORGANIZATION'}
    state['explicitReuseRequestsFrom'] = str(requests.reuse_requests) if requests.reuse_requests else None
    invocation = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid4().hex[:12]
    state['invocationId'] = invocation
    write_json(manifest_path, state)
    write_json(root/'input.json', value)
    write_json(root/'normalized_input.json', {'experience': experience, 'sourceMapping': mapping})
    try:
        events, pairs, pending = prepare_events(experience)
        write_json(root/'01_collected.json', {'events': events, 'pairs': pairs, 'unassigned': pending})
        state['stages']['collection'] = 'READY'
        payload, aliases = relational.prepare(pairs, experience['context'], experience['evaluations'])
        raw = requests.request('relational_extract', payload,
                               lambda obj: relational.compile_result(obj, payload, aliases))
        recovered = relational.compile_result(raw, payload, aliases)
        traces = recovered['traces']
        for trace in traces:
            trace['revision'] = 1
            trace['hash'] = digest({k:v for k,v in trace.items() if k != 'hash'})
        write_json(root/'02_03_recovered.json', recovered)
        state['stages']['recovery'] = 'READY'
        state['recoveredTaskCount'] = len(traces)
        state['unresolvedCount'] = len(recovered['unresolved'])
        write_json(root/'experience_routes.json', [{'traceId': t['id'], 'goal': t['goal'],
            'route': 'SUCCESS_ANALYSIS' if t['businessOutcome']=='SUCCESS' else
                     'FAILURE_ANALYSIS' if t['businessOutcome']=='FAILURE' else 'MIXED_OR_UNKNOWN_ANALYSIS',
            'result': t['businessOutcome'], 'note': '任务结果不下放每步；失败与未知仍可学有依据的方法'} for t in traces])
        if traces:
            batches, all_methods, all_workflows = [], [], []
            for start in range(0, len(traces), 8):
                batch = traces[start:start+8]
                batch_id = 'batch-'+str(start//8+1).zfill(3)
                folder = root/'04_batches'/batch_id
                wp, catalog = workflow.prepare(batch)
                raw = requests.request('workflow_extract', wp, lambda obj: workflow.validate_extract(obj, wp, catalog))
                extracted = workflow.validate_extract(raw, wp, catalog)
                groups, routes = workflow.clusters(extracted, batch, catalog, fresh_library=True)
                methods_record = {'frames': extracted['frames'], 'methods': extracted['methods'],
                    'relations': extracted['relations'], 'clusters': groups, 'routes': routes}
                write_json(folder/'methods_clusters.json', methods_record)
                view = workflow.merge_input(extracted, groups, routes, wp)
                if extracted['methods']:
                    raw = requests.request('workflow_merge', view,
                        lambda obj: workflow.validate_merge(obj, view, extracted))
                    workflows, ledger = workflow.validate_merge(raw, view, extracted)
                else:
                    workflows, ledger = [], []
                workflows_record = {'workflows': workflows, 'ledger': ledger}
                write_json(folder/'workflows.json', workflows_record)
                batches.append({'id':batch_id, 'traceIds':[t['id'] for t in batch],
                    'methodCount':len(extracted['methods']), 'workflowCount':len(workflows)})
                all_methods.append({'batchId':batch_id, **methods_record})
                all_workflows.append({'batchId':batch_id, **workflows_record})
                # Each batch has an independent evidence/ID namespace. Do not
                # invent cross-batch compatibility or quietly fuse skills.
                for item in workflows:
                    methods = [extracted['methodMap'][mid] for mid in item['includedMethodIds']]
                    candidate = package_workflow(root, item, methods, len(state['skills'])+1, official)
                    candidate['batchId'] = batch_id
                    prior = next((s for s in state['skills'] if s['id']==candidate['id']), None)
                    if prior:
                        prior.setdefault('additionalBatches', []).append(batch_id)
                    else:
                        state['skills'].append(candidate)
                state['aggregationBatches'] = batches
                write_json(root/'04_methods_clusters.json', all_methods[0] if len(all_methods)==1 else {'batches':all_methods})
                write_json(root/'04_workflows.json', all_workflows[0] if len(all_workflows)==1 else {'batches':all_workflows})
            state['stages']['aggregation'] = 'READY'
        else:
            state['stages']['aggregation'] = 'NO_TASKS'
        state['stages']['packaging'] = 'READY' if state['skills'] else 'NO_CANDIDATES'
        write_json(root/'skills/index.json', {'version': VERSION, 'skills': state['skills'],
            'note': '生成的候选库；未自动个人采纳、组织发布或验证业务收益'})
        state.update(status='COMPLETED', recoveredTaskCount=len(traces), skillCount=len(state['skills']),
                     unresolvedCount=len(recovered['unresolved']))
    except Exception as exc:
        state.update(status='FAILED', error=str(exc))
        raise
    finally:
        state['dispatchesThisInvocation'] = requests.started
        state['skillCount'] = len(state['skills'])
        starts = [r.get('modelRequestStarts') for r in requests.ledger]
        state['modelRequestStartsKnownThisInvocation'] = sum(n for n in starts if type(n) is int)
        state['unknownStartReceiptsThisInvocation'] = sum(n is None for n in starts)
        state['modelRequestStartsThisInvocation'] = None if any(n is None for n in starts) else sum(starts)
        state['requestLedger'] = requests.ledger
        all_starts = [json.loads(p.read_text(encoding='utf-8')).get('modelRequestStarts')
            for p in (root/'requests').glob('*/record.json')]
        state['modelRequestStartsKnownTotal'] = sum(n for n in all_starts if type(n) is int)
        state['unknownStartReceiptsTotal'] = sum(n is None for n in all_starts)
        state['modelRequestStartsTotalRecorded'] = None if any(n is None for n in all_starts) else sum(all_starts)
        write_json(root/'skills/index.json', {'version':VERSION, 'status':state['status'],
            'skills':state['skills'], 'note':'候选库；没有自动采纳、组织发布或独立业务验证。失败运行可能仅含已完成批次。'})
        write_json(root/'requests_ledger.json', requests.ledger)
        write_json(manifest_path, state)
        write_json(root/'invocations'/f'{invocation}.json', state)
    return state


def build(value, output, max_calls=3, agent=None, responses=None, official=True, reuse_requests=None):
    """One exclusive invocation per output directory; validated caches may resume."""
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    lock = root/'.pipeline.lock'
    try:
        handle = lock.open('x', encoding='utf-8')
    except FileExistsError as exc:
        raise ValueError('输出目录已有运行锁；请检查原进程，不并发调用或自动清理残留锁') from exc
    try:
        with handle:
            handle.write(json.dumps({'pid':os.getpid(), 'startedUtc':datetime.now(timezone.utc).isoformat()}))
        return _build(value, root, max_calls, agent, responses, official, reuse_requests)
    finally:
        lock.unlink()
