"""Bounded synthetic contract acceptance for the heuristic pipeline.

These fixtures test host constraints and lifecycle wiring.  Their model answers,
checks and organizational decisions are authored examples, not semantic quality
measurements or evidence of enterprise benefit.  The companion check script
imports this fixture so that one disclosed input exercises the same contracts.
"""
import copy
import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest
import zipfile

from skilldemo.core import Loop
from skilldemo.runtime import HEADINGS, ReplayAgent, digest


INITIAL_REQUEST = ('请审阅这份合成协议。先确认交付要求，再按条款核对问题，'
                   '按原编号列出待确认项；只输出文本。')
INITIAL_REPLY = '已逐条核对；输出问题说明和待确认项，业务正确性尚未独立验证。'
USE_REQUEST = ('请使用所选技能，按原条款编号审阅下面的合成协议，列出问题和待确认项。'
               '必须把非空Markdown交付到 outputs/review.md，回复中给出文件路径。\n'
               '1. 服务内容按需求单约定，但未指定需求单版本。\n'
               '2. 验收时间由双方另行确认，未给出验收标准。\n'
               '3. 修改经双方确认后生效，未约定确认方式。\n'
               '条款均为人工虚构，仅验收流程，不评价真实法律效果。')
FEEDBACK_REQUEST = ('补充一个今后复用的交付偏好：以后每次输出必须为每项建议列出'
                    '来源条款或可见依据，并把无法确认的问题单列为“待确认项”。'
                    '请据此更新本次 outputs/review.md。')
FEEDBACK_REPLY = '已补充每项建议的来源条款与可见依据，并单列待确认项；真实业务效果仍未验证。'
BOB_FEEDBACK_REQUEST = ('以后每次输出必须在待确认项后注明需谁确认和确认材料；'
                        '这是一条新增的合成组织使用反馈，请更新 outputs/review.md。')
FIXTURE_NOTICE = ('人工合成输入和模型答案；工具、文件读取及组织审核由本地夹具构造。'
                  '不衡量关系恢复准确率、算法语义性能或企业效果。')
LIVE_NOTICE = ('输入、使用任务及反馈为人工合成材料；执行使用真实 provider/OpenClaw，'
               '模型回答、工具调用和文件读取以实际运行记录为准。'
               '不衡量关系恢复准确率、算法语义性能或企业效果。')
EXPLICIT_INPUT_NOTICE = ('输入为调用方提供的 E/C/V；执行使用真实 provider/OpenClaw，'
                         '模型回答、工具调用和文件读取以实际运行记录为准。'
                         '不衡量关系恢复准确率、算法语义性能或企业效果。')


def synthetic_experience(session='synthetic-generation'):
    """Public, small E/C/V input with no benchmark gold or private conversation."""
    return {
        'events': [
            {'id': session+'-u1', 'sessionId': session, 'role': 'user',
             'order': 1, 'content': INITIAL_REQUEST},
            {'id': session+'-a1', 'sessionId': session, 'role': 'assistant',
             'order': 2, 'responseTo': session+'-u1', 'content': INITIAL_REPLY},
        ],
        'context': [{'id': session+'-c1', 'kind': 'PUBLIC_CONTEXT',
                     'text': '这是人工编写的协议审阅流程示例，未附真实合同。',
                     'source': 'SYNTHETIC_FIXTURE'}],
        'evaluations': [],
    }


def _span(pair, side, needle=None):
    spans = [s for s in pair['evidenceSpans'] if s['side'] == side]
    if needle:
        spans = [s for s in spans if needle in s['text']]
    if not spans:
        raise AssertionError('fixture requires a source span: '+str(needle))
    return {'span': spans[0]['id']}


def relational_answer(payload):
    """A source-bound authored answer, never fed back as learning gold."""
    tasks, first, annotations, memberships, observations = {}, {}, [], [], []
    requirements, relations, bindings = [], [], []
    for pair in payload['pairs']:
        key = 'reminder' if '提醒邮件' in pair['user'] else 'review'
        if key not in tasks:
            tasks[key] = 't'+str(len(tasks)+1)
            first[key] = pair
        task = tasks[key]
        is_first = first[key]['id'] == pair['id']
        kind = 'OPEN' if is_first else ('RETURN' if key == 'review' and 'reminder' in tasks else 'CONTINUE')
        fragment = pair['id']+':f1'
        annotations.append({'pair': pair['id'], 'fragments': [{
            'id': 'f1', 'quote': pair['user'], 'intent': '核对协议的文本交付要求' if key == 'review' else '起草提醒邮件',
            'kind': kind, 'task': task, 'alternatives': [], 'references': [], 'uncertainty': ''}]})
        memberships.append({'fragment': fragment, 'options': [{
            'task': task, 'status': 'CONFIRMED', 'score': .9,
            'reason': '人工夹具：同一明确对象与交付要求'}]})
        for span in pair['evidenceSpans']:
            if span['side'] == 'assistant':
                claim = '操作成功' in span['text'] or '文件已生成' in span['text']
                observations.append({'fragment': fragment, 'kind': 'EXECUTION_CLAIM' if claim else 'VISIBLE_TEXT',
                                     'evidence': {'span': span['id']}, 'description': '人工夹具标注的可见文本'})
        if is_first and key == 'review':
            requirements.extend([
                {'fragment': fragment, 'dimension': 'numbering', 'op': 'ADD', 'value': '保留原编号',
                 'evidence': [_span(pair, 'user')], 'scope': 'CURRENT_TASK'},
                {'fragment': fragment, 'dimension': 'output_format', 'op': 'ADD',
                 'value': 'Markdown文件' if 'outputs/review.md' in pair['user'] else '文本',
                 'evidence': [_span(pair, 'user')], 'scope': 'CURRENT_TASK'},
            ])
        if not is_first and key == 'review' and ('以后' in pair['user'] or '改成表格' in pair['user']):
            target = first[key]
            change = ('待确认项注明需谁确认和所需确认材料' if '需谁确认' in pair['user'] else
                      '以后每项建议列出来源条款或可见依据，无法确认的问题单列待确认项'
                      if '以后' in pair['user'] else '输出改成表格')
            scope = 'FUTURE_TASKS' if '以后' in pair['user'] else 'CURRENT_DELIVERY'
            relations.append({'id': 'r'+str(len(relations)+1), 'source': fragment, 'options': [{
                'target': target['id']+':f1', 'kind': 'CHANGE_REQUIREMENT', 'score': .9,
                'evidence': [_span(pair, 'user'), _span(target, 'assistant')],
                'reason': '人工夹具：明确指出此前交付并提出要求增量', 'delta': change, 'scope': scope}]})
            requirements.append({'fragment': fragment,
                                 'dimension': 'confirmation_owner' if '需谁确认' in pair['user'] else
                                              'evidence_listing' if '以后' in pair['user'] else 'output_format',
                                 'op': 'ADD' if '以后' in pair['user'] else 'REPLACE',
                                 'value': change if '以后' in pair['user'] else '表格',
                                 'evidence': [_span(pair, 'user')], 'scope': scope})
    seeds = [{'key': task, 'anchor': first[key]['id']+':f1',
              'goal': '按交付要求审阅协议' if key == 'review' else '起草提醒邮件',
              'object': '合成协议' if key == 'review' else '独立提醒事项',
              'deliverable': '带原编号的审阅文本' if key == 'review' else '邮件草稿', 'constraints': []}
             for key, task in tasks.items()]
    # Live-pair tool records may be included by the host evidence catalog.  Bind
    # only records whose pair reference is explicit; no nearest-turn guessing.
    catalog = payload['evidence']
    rows = list(catalog.values()) if isinstance(catalog, dict) else catalog
    aliases = {p['pairId']: p['id']+':f1' for p in payload['pairs']}
    for item in rows:
        if not isinstance(item, dict) or item.get('kind') not in ('TOOL_CALL', 'TOOL_RESULT'):
            continue
        ref = item.get('ref') or {}
        pair_id = ref.get('pairId')
        if pair_id in aliases:
            bindings.append({'evidenceId': item['id'], 'fragment': aliases[pair_id]})
    return {'sourceHash': payload['sourceHash'], 'seeds': seeds, 'annotations': annotations,
            'memberships': memberships, 'relations': relations, 'observations': observations,
            'requirements': requirements, 'executionBindings': bindings,
            'evaluationBindings': [], 'uncertainties': []}


def workflow_answer(payload):
    from skilldemo.workflow_index import expand
    payload = expand(payload)
    frames, methods = [], []
    for index, trace in enumerate(payload['traces'], 1):
        fid, mid = 'f'+str(index), 'm'+str(index)
        evidence = trace['evidence']
        # Use the actual feedback source to exercise exact-version UPDATE.
        selected = next((e for e in reversed(evidence) if e['kind'] in ('USER_FEEDBACK', 'USER_REQUIREMENT')
                         and '以后' in e['text']), None)
        selected = selected or next((e for e in reversed(evidence) if e['kind'] == 'USER_FEEDBACK'), None)
        selected = selected or next(e for e in evidence if e['kind'] == 'USER_REQUIREMENT')
        future_rule = '以后' in selected['text'] or selected['kind'] == 'USER_FEEDBACK'
        action = ('每轮按来源条款编号整理问题、依据与待确认事项。'
                  if future_rule else '先确认输出形式，再按条款编号整理问题与待确认事项。')
        frames.append({'id': fid, 'traceId': trace['traceId'], 'goal': '审阅文本的编号与依据核对',
                       'inputContract': ['需审阅的文本及交付要求'], 'outputContract': ['逐条问题与待确认项'],
                       'processSketch': [action], 'conditions': ['收到文本审阅请求时'],
                       'parameters': ['当前交付格式'], 'methodIds': [mid]})
        methods.append({'id': mid, 'frameId': fid, 'action': action,
                        'inputs': ['待审阅文本及原条款编号'], 'outputs': ['问题、依据和待确认事项'],
                        'conditions': ['收到文本审阅请求时'], 'parameters': ['当前交付格式'],
                        'completionCheck': '逐项核对编号与原文本一致，未证实内容标为待确认。',
                        'evidenceRefs': [selected['id']], 'evidenceKind': selected['kind'],
                        'outcome': 'UNKNOWN', 'decisionHint': 'INCLUDE',
                        'reason': '人工夹具：仅提取用户明示的交付流程，未推断业务成功'})
    return {'sourceHash': payload['sourceHash'], 'frames': frames, 'methods': methods, 'relations': []}


def merge_answer(payload):
    from skilldemo.workflow_index import expand
    payload = expand(payload)
    workflows, ledger = [], []
    for cluster in payload['clusters']:
        methods = cluster['methods']
        workflows.append({'frameIds': cluster['frameIds'], 'title': '审阅交付编号核对',
                          'trigger': '需要按条款审阅文本并整理交付时', 'inputs': ['待审文本与当前要求'],
                          'steps': [{'id': 's'+str(i), 'methodIds': [m['id']], 'action': m['action'],
                                     'condition': m['conditions'][0] if m['conditions'] else '',
                                     'completionCheck': m['completionCheck']} for i, m in enumerate(methods, 1)],
                          'outputs': ['逐条问题、依据和待确认项'], 'parameters': ['交付格式'],
                          'conditions': ['取得可读的待审文本'], 'dependencies': [],
                          'limitations': ['人工夹具；业务结果与专业正确性尚未独立验证。'],
                          'includedMethodIds': [m['id'] for m in methods]})
        ledger.extend({'methodId': m['id'], 'disposition': 'INCLUDED', 'duplicateOf': None,
                       'reason': '人工夹具：来源支持且属于同一可复用流程'} for m in methods)
    return {'sourceHash': payload['sourceHash'], 'workflows': workflows, 'ledger': ledger}


class HeuristicFixture(ReplayAgent):
    """Synthetic model outputs, actual local creator draft/package and file read."""
    def __init__(self):
        self.calls = []
        self.payloads = []

    def run(self, purpose, payload, workspace):
        workspace = Path(workspace)
        self.calls.append(purpose)
        self.payloads.append({'purpose': purpose, 'payload': copy.deepcopy(payload)})
        if purpose == 'relational_extract':
            output = relational_answer(payload)
        elif purpose == 'workflow_extract':
            output = workflow_answer(payload)
        elif purpose == 'workflow_merge':
            output = merge_answer(payload)
        elif purpose == 'workflow_creator':
            from skilldemo.bootstrap import initialize
            initialize(workspace)
            foundation = workspace/'.foundation/skill-creator/SKILL.md'
            foundation.read_text(encoding='utf-8')
            methods = payload['methods']
            text = '---\nname: review-delivery-check\ndescription: 核对文本审阅的编号和交付要求。\n---\n'
            coverage = []
            for method in methods:
                action, check = method['action'], method['completionCheck']
                conditions = method.get('conditions', [])
                text += '\n## 操作 '+method['id']+'\n<!-- SKILLSLOOP_METHOD:'+method['id']+' -->\n'+action+'\n'
                text += '\n'.join(conditions)+'\n'+check+'\n'
                row = {'methodId': method['id'], 'file': 'SKILL.md', 'actionQuote': action,
                       'conditionQuotes': conditions, 'completionCheckQuote': check}
                if method.get('scopeContract'):
                    bindings = method['scopeContract']['bindings']
                    text += '\n'.join(binding['text'] for binding in bindings)+'\n'
                    row['scopeQuotes'] = [{'scopeId': binding['id'], 'quote': binding['text']}
                                          for binding in bindings]
                coverage.append(row)
            text += '\n## 市场信息\n'+'\n'.join('### '+h+'\n用于整理文本审阅交付要求。' for h in HEADINGS)
            draft = workspace/'draft'
            draft.mkdir(parents=True, exist_ok=True)
            (draft/'SKILL.md').write_text(text, encoding='utf-8')
            output = {'decision': 'CREATE', 'title': '审阅交付编号核对', 'coverageManifest': coverage}
            return self._result(output, foundationRead={
                'status': 'FILE_READ', 'fixtureHostProof': True,
                'source': 'SYNTHETIC_FIXTURE',
                'sha256': hashlib.sha256(foundation.read_bytes()).hexdigest(),
                'reason': 'actual local fixture read; provider foundation read was not exercised'})
        elif purpose == 'chat':
            skills = payload.get('selected_skills', [])
            receipts = []
            for skill in skills:
                entry = workspace/'skills'/skill['id']/'SKILL.md'
                if not entry.is_file():
                    raise AssertionError('host did not place selected skill in workspace')
                # The file read itself is real.  Its attribution envelope is
                # synthetic and must not be confused with a provider transcript.
                entry.read_text(encoding='utf-8')
                receipts.append({'id': skill['id'], 'version': skill['version'], 'hash': skill['hash'],
                                 'status': 'FILE_READ', 'fixtureHostProof': True, 'source': 'SYNTHETIC_FIXTURE'})
            answer = (FEEDBACK_REPLY if '以后' in payload.get('message', '') else INITIAL_REPLY)
            content = ('# 合成协议审阅\n\n'
                       '1. 需求单版本未指明；待确认项：需求单版本与适用范围。\n'
                       '2. 验收标准未确定；待确认项：标准和验收时间。\n'
                       '3. 确认方式未约定；待确认项：双方确认记录的形式。\n')
            if '以后' in payload.get('message', ''):
                content += '\n## 可见依据与待确认项\n每项依据为对应原编号条款；其余事实需确认。\n'
            out = workspace/'outputs'/'review.md'
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(content, encoding='utf-8')
            file_hash = hashlib.sha256(out.read_bytes()).hexdigest()
            result = self._result(answer+' 交付路径：outputs/review.md。')
            result.update(skillEvidence={'status': 'FIXTURE_HOST_PROOF', 'skills': receipts, 'tools': [],
                                         'fixtureHostProof': True}, toolEvents=[],
                          artifacts=[{'path': 'outputs/review.md', 'sha256': file_hash,
                                      'bytes': out.stat().st_size, 'synthetic': True}],
                          fixtureHostProof=True)
            return result
        elif purpose == 'learn' and payload.get('algorithm') == 'trace-patch-v1':
            if payload.get('proposalContractVersion'):
                from skilldemo.learning import public_update_input
                view = public_update_input(payload)
                approved = [u for u in view['updateUnits'] if u['status'] == 'APPROVED']
                selected = [u for u in approved if u['scope'] == 'FUTURE_TASKS']
                anchors = view['updateAnchors']
                if not anchors:
                    selected = []
                chosen = {u['id'] for u in selected}
                output = {'decision':'UPDATE' if selected else 'DEFER',
                    'mergedPatches':[{'proposalIds':sorted(chosen), 'operations':[{
                        'op':'insert_after', 'anchorId':anchors[-1]['id'],
                        'compatibility':'NO_CONFLICT',
                        'reason':'人工夹具：未来来源标注要求补充本次实例流程；不假称模型语义效果'}]}]
                        if selected else [],
                    'deferred':[{'proposalId':u['id'], 'reason':'人工夹具仅选未来持续偏好，其余保留'}
                                for u in approved if u['id'] not in chosen]}
                return self._result(output)
            # Bind the exact approved method and its remapped source event ID;
            # the legacy finance fixture guesses rules from words and cannot
            # represent this relational bridge contract.
            analyses, merged = [], []
            for index, bundle in enumerate(payload['evidence']):
                proposals = []
                events = {e['id']: e for e in bundle['events']}
                methods = [m for m in payload['approvedMethods'] if m['sourceTaskId'] == bundle['taskId']]
                for count, method in enumerate(methods):
                    users = [events[eid] for eid in method['evidenceRefs'] if events[eid]['kind'] == 'user']
                    if not users:
                        continue
                    event = users[0]
                    pid = 'fixture-p'+str(index)+'-'+str(count)
                    scope = event.get('scope', 'CURRENT_TASK')
                    lesson = '按原编号为每项建议注明来源条款或可见依据，并单列尚需确认的问题。'
                    proposals.append({'id': pid, 'lesson': lesson,
                                      'applicability': '收到同类文本审阅请求时，遵循该用户明确声明的交付偏好。',
                                      'applicabilityScope': scope, 'evidenceType': 'USER_RULE',
                                      'approvedMethodIds': [method['id']],
                                      'evidenceRefs': [{'eventId': event['id'], 'quote': event['text']}]})
                    merged.append({'proposalIds': [pid], 'operations': [{
                        'op': 'append', 'path': 'SKILL.md', 'beforeHash': payload['fileHashes']['SKILL.md'],
                        'content': '\n## 用户明确声明的审阅交付偏好\n'+lesson+'\n业务效果尚未验证。'}]})
                analyses.append({'taskId': bundle['taskId'], 'analyst': bundle['analyst'], 'proposals': proposals,
                                 'reason': '人工夹具；精确批准方法与原事件引用，不是模型语义效果'})
            output = {'decision': 'UPDATE' if merged else 'DEFER', 'title': '审阅交付编号核对',
                      'analyses': analyses, 'mergedPatches': merged, 'deferred': []}
            return self._result(output)
        else:
            raise AssertionError('unexpected fixture purpose: '+purpose)
        return self._result(output)

    @staticmethod
    def _result(value, **extra):
        return {'text': value if isinstance(value, str) else json.dumps(value, ensure_ascii=False),
                'usage': {'total': 0}, 'modelRequestStarts': 0, 'mode': 'replay',
                'fixtureHostProof': True, **extra}


def records(loop, kind, actor='alice'):
    with loop.store.tx() as db:
        return loop.store.rows(db, kind, actor)


def newest_candidate(loop, action):
    rows = [c for c in records(loop, 'candidate') if c['action'] == action and c['status'] == 'QUEUED']
    if not rows:
        raise AssertionError('missing '+action+' candidate: '+json.dumps(
            [{'id': c['id'], 'action': c['action'], 'status': c['status'], 'error': c.get('error')}
             for c in records(loop, 'candidate')], ensure_ascii=False))
    return sorted(rows, key=lambda c: (c.get('created', 0), c['id']))[-1]


def run_pipeline(loop, *, exercise_use_and_update=True, organization=True, experience=None,
                 initialization=None, report=None):
    """One bounded E/C/V fixture.  The caller chooses replay or real provider."""
    report = {} if report is None else report
    report.update(fixtureNotice=LIVE_NOTICE if loop.agent.mode == 'openclaw' else FIXTURE_NOTICE,
                  stages=[], organizationReview='NOT_EXERCISED',
                  organizationReuse='NOT_EXERCISED', organizationFeedback='NOT_EXERCISED')
    experience = synthetic_experience() if experience is None else copy.deepcopy(experience)
    initialization = initialization or {
        'status': 'KNOWN_NONE', 'basis': 'Disclosed synthetic history explicitly contains no selected skills'}
    loop.import_experience('alice', experience, purpose_split='generation', initialization=initialization)
    report['stages'].append({'stage': 'intake', 'inputHash': digest(experience)})
    report['completedThrough'] = 'STAGE_1'
    report['front'] = loop.run_stages('alice')
    traces = [t for t in records(loop, 'trace') if t.get('state') == 'SEALED']
    if not traces or any(t.get('relationalSchema') is None for t in traces):
        raise AssertionError('heuristic trace with relationalSchema required')
    report['stages'].append({'stage': 'task_attempt_feedback_requirement_recovery',
                             'traceIds': [t['id'] for t in traces],
                             'relationalSchemas': [t['relationalSchema'] for t in traces],
                             'traceHashes': [t['hash'] for t in traces]})
    report['completedThrough'] = 'STAGES_1_TO_3'
    loop.discover('alice')
    failed_analysis = [r for r in records(loop, 'workflow_analysis') if r.get('status') == 'FAILED']
    if failed_analysis:
        raise AssertionError('workflow analysis failed: '+str(failed_analysis[-1].get('error', 'unknown error')))
    if initialization['status'] == 'UNKNOWN' and not [
            c for c in records(loop, 'candidate') if c['action'] == 'NEW' and c['status'] == 'QUEUED']:
        report.update(status='DEFERRED', completedThrough='STAGES_2_AND_3',
                      packageDelivery='NOT_PRODUCED', stage4='SOURCE_USE_ATTRIBUTION_UNRESOLVED',
                      reason='Prior skill initialization is unknown; no source-supported NEW route.',
                      initialization=initialization, semanticPerformance='NOT_MEASURED',
                      businessOutcome='UNKNOWN')
        return report
    candidate = newest_candidate(loop, 'NEW')
    workflow_id = candidate.get('workflowId') or candidate['input']['workflowId']
    frozen_row = next(w for w in records(loop, 'workflow') if w['id'] == workflow_id)
    frozen = frozen_row['workflow']
    clauses = frozen.get('clauseLedger', [])
    if not clauses:
        raise AssertionError('frozen workflow has no auditable clauseLedger')
    report['stages'].append({'stage': 'workflow_extract_cluster_and_freeze',
                             'workflowPublicHash': candidate['input'].get('publicWorkflowHash') or
                                                   digest(candidate['input']['workflow']),
                             'workflowFrozenHash': frozen_row['workflowHash'], 'clauseLedger': clauses})
    report['completedThrough'] = 'STAGES_1_TO_4'
    ready = loop.generate('alice', candidate['id'])
    if ready['status'] != 'READY':
        raise AssertionError('creator failed: '+str(ready.get('error') or ready))
    if ready.get('validation', {}).get('hostBundle', {}).get('status') != 'PASS':
        raise AssertionError('missing creator host coverage validation')
    if ready.get('validation', {}).get('officialPackage', {}).get('status') != 'PASS':
        raise AssertionError('missing official package content validation')
    with loop.store.tx() as db:
        stored_run = db.execute('SELECT result FROM runs WHERE id=?', (ready['runId'],)).fetchone()
    assembly = json.loads(stored_run['result'] or '{}').get('hostAssembly') if stored_run else None
    step_contract = candidate['input']['workflow'].get('stepScopeContract')
    if step_contract:
        if not assembly or assembly.get('status') != 'HOST_ASSEMBLED' or assembly.get('assembledFilesHash') != ready['hash']:
            raise AssertionError('final package lacks exact host assembly evidence')
        covered = ready['validation']['hostBundle'].get('stepScopeCoverage', [])
        expected = [{'stepId': step['stepId'], 'methodIds': step['methodIds'],
                     'status': 'HOST_STEP_SCOPE_ANCHORED',
                     'scopeCoverage': [{'methodId': b['methodId'], 'scopeId': b['scopeId'], 'quote': b['text']}
                                       for b in step['bindings']]} for step in step_contract['steps']]
        if covered != expected:
            raise AssertionError('final package does not cover each frozen step scope')
    first = loop.accept('alice', ready['id'])
    report['stages'].append({'stage': 'creator_and_personal_adoption', 'candidateId': ready['id'],
                             'skillId': first['id'], 'version': first['version'], 'hash': first['hash'],
                             'archive': ready.get('package'),
                             'creatorValidation': ready.get('validation'), 'hostAssembly': assembly})
    report['skillV1'] = {'id': first['id'], 'version': first['version'], 'hash': first['hash']}
    report['completedThrough'] = 'STAGES_1_TO_6'
    if not exercise_use_and_update:
        report.update(status='PASS', completedThrough='STAGES_1_TO_5_AND_PERSONAL_ADOPTION',
                      useAndEvolution='NOT_EXERCISED')
        return report
    used = loop.chat('alice', 'synthetic-use', USE_REQUEST, [first['id']], request_id='synthetic-use-1')
    receipt = used.get('skillEvidence') or {}
    actual = [r for r in receipt.get('skills', []) if r.get('status') == 'FILE_READ']
    if not any((r.get('id'), r.get('version'), r.get('hash')) == (first['id'], 1, first['hash']) for r in actual):
        raise AssertionError('selected skill lacks exact version FILE_READ evidence')
    for artifact in used.get('artifacts', []):
        if artifact.get('sha256'):
            path = loop.artifact('alice', used['runId'], artifact['path'])
            if hashlib.sha256(path.read_bytes()).hexdigest() != artifact['sha256']:
                raise AssertionError('personal-use artifact hash does not match its registered file')
    delivered = [a for a in used.get('artifacts', []) if a.get('path') == 'outputs/review.md']
    if len(delivered) != 1:
        raise AssertionError('personal use did not register outputs/review.md')
    delivery_path = loop.artifact('alice', used['runId'], delivered[0]['path'])
    if not delivery_path.read_text(encoding='utf-8').strip():
        raise AssertionError('personal-use review.md deliverable is empty')
    report['stages'].append({'stage': 'personal_use', 'turnId': used['id'], 'receipt': receipt,
                             'artifacts': used.get('artifacts', [])})
    report['completedThrough'] = 'STAGES_1_TO_7'
    feedback = loop.chat('alice', 'synthetic-use', FEEDBACK_REQUEST, [first['id']],
                         request_id='synthetic-feedback-1', reply_to=used['id'])
    report['stages'].append({'stage': 'feedback', 'turnId': feedback['id'], 'requestHash': digest(FEEDBACK_REQUEST)})
    report['completedThrough'] = 'STAGES_1_TO_8'
    report['updateFront'] = loop.run_stages('alice')
    loop.discover('alice')
    update = newest_candidate(loop, 'UPDATE')
    if (update.get('target'), update.get('baseVersion'), update.get('baseHash')) != (first['id'], 1, first['hash']):
        raise AssertionError('feedback did not bind UPDATE to exactly the used version')
    draft = loop.generate('alice', update['id'])
    if draft['status'] != 'READY':
        raise AssertionError('UPDATE failed: '+str(draft.get('error') or draft))
    second = loop.accept('alice', draft['id'])
    if second['id'] != first['id'] or second['version'] != 2 or second['hash'] == first['hash']:
        raise AssertionError('UPDATE did not create changed v2 under the same personal skill')
    history = second.get('versions', [])
    if not any(v.get('version') == 1 and v.get('hash') == first['hash'] for v in history):
        raise AssertionError('UPDATE lost the historical v1')
    report['stages'].append({'stage': 'exact_version_update', 'candidateId': draft['id'],
                             'skillId': second['id'], 'version': second['version'], 'hash': second['hash'],
                             'patchAudit': draft.get('patchAudit')})
    report['skillV2'] = {'id': second['id'], 'version': second['version'], 'hash': second['hash']}
    if organization:
        submitted = loop.submit('alice', draft['id'])
        shared = loop.review('reviewer', submitted['id'], True)
        report['organizationReview'] = 'SYNTHETIC_TEST_DECISION'
        reused = loop.chat('bob', 'synthetic-organization-use', USE_REQUEST, [shared['id']],
                           request_id='synthetic-org-1')
        report['organizationReuse'] = 'EXERCISED'
        report['stages'].append({'stage': 'organization_review_and_reuse', 'orgSkillId': shared['id'],
                                 'bobTurnId': reused['id'], 'receipt': reused.get('skillEvidence'),
                                 'reviewDecision': 'SYNTHETIC_AUTHORIZED_TEST_DECISION',
                                 'enterpriseEffect': 'NOT_MEASURED'})
        if loop.agent.mode == 'replay':
            bob_feedback = loop.chat('bob', 'synthetic-organization-use', BOB_FEEDBACK_REQUEST,
                                     [shared['id']], request_id='synthetic-org-feedback-1', reply_to=reused['id'])
            bob_front = loop.run_stages('bob')
            bob_traces = [t for t in records(loop, 'trace', 'bob') if t.get('state') == 'SEALED']
            if not bob_traces or not any(t.get('feedbackEdges') for t in bob_traces):
                raise AssertionError('organization-use feedback did not become a recovered Bob trace')
            report['stages'].append({'stage': 'organization_use_feedback_recovery',
                                     'turnId': bob_feedback['id'], 'front': bob_front,
                                     'traceIds': [t['id'] for t in bob_traces],
                                     'automaticOrganizationUpdate': False, 'synthetic': True})
            report['organizationFeedback'] = 'EXERCISED'
    report.update(status='PASS', completedThrough='PERSONAL_VERSION_UPDATE',
                  logicalStageCoverage=('STAGES_1_TO_12_SYNTHETIC_FIXTURE' if organization and loop.agent.mode == 'replay'
                                        else 'STAGES_1_TO_9_REAL_PROVIDER' if loop.agent.mode == 'openclaw'
                                        else 'PERSONAL_PIPELINE_SYNTHETIC_FIXTURE'),
                  businessOutcome='UNKNOWN', semanticPerformance='NOT_MEASURED')
    return report


class HeuristicPipelineTests(unittest.TestCase):
    def loop(self, root, agent=None):
        return Loop(root, agent or HeuristicFixture(), settle_seconds=0,
                    stage_pipeline=True, learning_algorithm='heuristic', daily_limit=30)

    def compile(self, pairs, output_mutator=None, context=None, evaluations=None):
        from skilldemo import relational
        payload, aliases = relational.prepare(pairs, context=context or [], evaluations=evaluations or [])
        output = relational_answer(payload)
        if output_mutator:
            output_mutator(output, payload)
        return relational.compile_result(output, payload, aliases), payload, output

    def imported_pairs(self, loop, user_replies):
        events = []
        for index, (user, assistant) in enumerate(user_replies, 1):
            events.extend([
                {'id': 'u'+str(index), 'sessionId': 'contract', 'role': 'user', 'order': 2*index-1, 'content': user},
                {'id': 'a'+str(index), 'sessionId': 'contract', 'role': 'assistant', 'order': 2*index,
                 'responseTo': 'u'+str(index), 'content': assistant},
            ])
        loop.import_experience('alice', {'events': events, 'context': [], 'evaluations': []},
                               initialization={'status': 'KNOWN_NONE', 'basis': 'Synthetic inputs with no selected skill'})
        return sorted(records(loop, 'qa_pair'), key=lambda p: p['sourceOrder'])

    def test_fixture_full_pipeline_keeps_v1_and_updates_exact_used_skill(self):
        with tempfile.TemporaryDirectory() as root:
            agent = HeuristicFixture()
            loop = self.loop(root, agent)
            report = run_pipeline(loop)
            self.assertEqual(report['status'], 'PASS')
            self.assertEqual(report['skillV2']['id'], report['skillV1']['id'])
            self.assertEqual(report['skillV2']['version'], 2)
            self.assertIn('relational_extract', agent.calls)
            self.assertIn('workflow_creator', agent.calls)
            self.assertIn('learn', agent.calls)
            self.assertNotIn('detect_pairs', agent.calls)
            self.assertNotIn('recover_trace', agent.calls)
            self.assertEqual(report['semanticPerformance'], 'NOT_MEASURED')
            creator_payload = next(p['payload'] for p in agent.payloads if p['purpose'] == 'workflow_creator')
            public_json = json.dumps(creator_payload, ensure_ascii=False)
            self.assertNotIn('clauseLedger', public_json)
            self.assertNotIn('typedSources', public_json)
            self.assertNotIn(INITIAL_REQUEST, public_json)
            self.assertNotIn(INITIAL_REPLY, public_json)
            for turn in records(loop, 'turn'):
                for receipt in (turn.get('skillEvidence') or {}).get('skills', []):
                    self.assertTrue(receipt.get('fixtureHostProof'))

    def test_notice_separates_synthetic_input_from_real_provider_execution(self):
        from scripts.check_heuristic_pipeline import acceptance_notice
        self.assertEqual(acceptance_notice(False), FIXTURE_NOTICE)
        for explicit in (False, True):
            notice = acceptance_notice(True, explicit_input=explicit)
            self.assertIn('真实 provider', notice)
            self.assertNotIn('模型答案；工具、文件读取及组织审核由本地夹具构造', notice)
            self.assertIn('运行记录', notice)
        self.assertIn('调用方', acceptance_notice(True, explicit_input=True))

    def test_model_request_summary_counts_rounds_and_keeps_missing_counts_unknown(self):
        from scripts.check_heuristic_pipeline import request_summary
        calls = [{'mode': 'openclaw', 'modelRequestStarts': 4},
                 {'mode': 'openclaw', 'modelRequestStarts': 3},
                 {'mode': 'replay', 'modelRequestStarts': 0}]
        summary = request_summary(calls)
        self.assertEqual(summary['requestDispatches'], 3)
        self.assertEqual(summary['modelRequestStarts'], 7)
        self.assertEqual(summary['realModelRequestStarts'], 7)
        self.assertEqual(summary['modelRequestStartsUnknownDispatches'], 0)
        calls.append({'mode': 'openclaw', 'modelRequestStarts': None})
        unknown = request_summary(calls)
        self.assertIsNone(unknown['modelRequestStarts'])
        self.assertIsNone(unknown['realModelRequestStarts'])
        self.assertEqual(unknown['knownRealModelRequestStarts'], 7)
        self.assertEqual(unknown['modelRequestStartsUnknownDispatches'], 1)
        replay = request_summary([{'mode': 'replay', 'modelRequestStarts': 0}])
        self.assertEqual(replay['realModelRequestStarts'], 0)

    def test_requested_organization_is_not_claimed_before_it_executes(self):
        with tempfile.TemporaryDirectory() as root:
            report = run_pipeline(self.loop(root), exercise_use_and_update=False, organization=True)
            self.assertEqual(report['status'], 'PASS')
            self.assertEqual(report['organizationReview'], 'NOT_EXERCISED')
            self.assertEqual(report['organizationReuse'], 'NOT_EXERCISED')
            self.assertEqual(report['organizationFeedback'], 'NOT_EXERCISED')

    def test_failed_update_preserves_executed_stages_without_claiming_organization(self):
        class FailingUpdateFixture(HeuristicFixture):
            def run(self, purpose, payload, workspace):
                if purpose == 'learn':
                    raise ValueError('Synthetic UPDATE failure')
                return super().run(purpose, payload, workspace)
        with tempfile.TemporaryDirectory() as root:
            report = {}
            with self.assertRaisesRegex(AssertionError, 'UPDATE failed'):
                run_pipeline(self.loop(root, FailingUpdateFixture()), report=report)
            self.assertEqual(report['completedThrough'], 'STAGES_1_TO_8')
            self.assertIn('skillV1', report)
            self.assertNotIn('skillV2', report)
            self.assertIn('personal_use', [stage['stage'] for stage in report['stages']])
            self.assertIn('feedback', [stage['stage'] for stage in report['stages']])
            self.assertEqual(report['organizationReview'], 'NOT_EXERCISED')

    def test_final_package_preserves_scope_for_each_step_and_keeps_provider_draft(self):
        class RepeatedStepFixture(HeuristicFixture):
            def run(self, purpose, payload, workspace):
                result = super().run(purpose, payload, workspace)
                if purpose == 'workflow_merge':
                    value = json.loads(result['text'])
                    for workflow_row in value['workflows']:
                        repeated = copy.deepcopy(workflow_row['steps'][0])
                        repeated['id'] = 'repeated-step'
                        workflow_row['steps'].append(repeated)
                    result['text'] = json.dumps(value, ensure_ascii=False)
                return result
        with tempfile.TemporaryDirectory() as root:
            agent = RepeatedStepFixture()
            loop = self.loop(root, agent)
            report = run_pipeline(loop, exercise_use_and_update=False, organization=False)
            payload = next(p['payload'] for p in agent.payloads if p['purpose'] == 'workflow_creator')
            contract = payload['workflow']['stepScopeContract']
            self.assertEqual(contract['version'], 'workflow-step-scope-v1')
            self.assertEqual([step['stepId'] for step in contract['steps']], ['s1', 's2'])
            first = next(skill for skill in records(loop, 'skill') if skill['id'] == report['skillV1']['id'])
            final_md = next(item['content'] for item in first['files'] if item['path'] == 'SKILL.md')
            for step in contract['steps']:
                marker = '<!-- SKILLSLOOP_STEP:'+step['stepId']+' -->'
                self.assertIn(marker, final_md)
                tail = final_md.split(marker, 1)[1]
                boundary = re.search(r'<!--\s*SKILLSLOOP_STEP:|^\s*#{1,6}\s', tail, re.M)
                segment = tail[:boundary.start()] if boundary else tail
                for binding in step['bindings']:
                    self.assertIn(binding['text'], segment)
            candidate = next(c for c in records(loop, 'candidate') if c['installedSkill'] == first['id'])
            workspace = loop.store.root/'workspaces'/candidate['runId']
            draft_md = (workspace/'draft/SKILL.md').read_text(encoding='utf-8')
            self.assertNotEqual(draft_md, final_md)
            self.assertNotIn('SKILLSLOOP_STEP:', draft_md)
            from skilldemo.bootstrap import draft_files
            from skilldemo.creator import assemble_step_scoped_files, verify_files
            raw_files = draft_files(workspace)
            assembled, audit = assemble_step_scoped_files(raw_files, payload['workflow'], payload['methods'])
            self.assertEqual(assembled, first['files'])
            self.assertEqual(audit['rawFilesHash'], digest(raw_files))
            self.assertEqual(audit['assembledFilesHash'], first['hash'])
            stage = next(s for s in report['stages'] if s['stage'] == 'creator_and_personal_adoption')
            self.assertEqual(stage['hostAssembly'], audit)
            kwargs = {'methods': payload['methods'], 'coverageManifest': audit['methodCoverageManifest'],
                      'workflow': payload['workflow'], 'stepCoverageManifest': audit['stepCoverageManifest']}
            ids = payload['workflow']['includedMethodIds']
            checked = verify_files(assembled, ids, **kwargs)
            self.assertEqual([r['stepId'] for r in checked['stepScopeCoverage']], ['s1', 's2'])
            missing_body = copy.deepcopy(assembled)
            prefix, second_step = final_md.split('<!-- SKILLSLOOP_STEP:s2 -->', 1)
            scope_text = contract['steps'][1]['bindings'][0]['text']
            missing_body[0]['content'] = prefix+'<!-- SKILLSLOOP_STEP:s2 -->'+second_step.replace(scope_text, '', 1)
            with self.assertRaises(ValueError):
                verify_files(missing_body, ids, **kwargs)
            missing_manifest = copy.deepcopy(kwargs)
            missing_manifest['stepCoverageManifest'][1]['scopeQuotes'] = []
            with self.assertRaises(ValueError):
                verify_files(assembled, ids, **missing_manifest)
            archive = workspace/candidate['package']['path']
            with zipfile.ZipFile(archive) as package:
                entry = next(name for name in package.namelist() if name.endswith('/SKILL.md'))
                self.assertEqual(package.read(entry).decode('utf-8'), final_md)

    def test_unknown_initialization_defers_without_claiming_a_delivered_package(self):
        with tempfile.TemporaryDirectory() as root:
            agent = HeuristicFixture()
            loop = self.loop(root, agent)
            result = run_pipeline(loop, exercise_use_and_update=False, organization=False,
                                  initialization={'status': 'UNKNOWN', 'basis': 'No prior skill provenance supplied'})
            self.assertEqual(result['status'], 'DEFERRED')
            self.assertEqual(result['completedThrough'], 'STAGES_2_AND_3')
            self.assertEqual(result['packageDelivery'], 'NOT_PRODUCED')
            self.assertNotIn('workflow_creator', agent.calls)
            self.assertFalse(records(loop, 'skill'))

    def test_interleaving_delayed_feedback_and_one_dimension_replace(self):
        with tempfile.TemporaryDirectory() as root:
            loop = self.loop(root)
            pairs = self.imported_pairs(loop, [
                (INITIAL_REQUEST, INITIAL_REPLY),
                ('请另写提醒邮件，通知同事明天提交材料。', '提醒邮件草稿：请明天提交材料。'),
                ('回到合成协议，只把输出改成表格，仍保留原编号。', FEEDBACK_REPLY),
            ])
            compiled, payload, output = self.compile(pairs)
            self.assertEqual(len(compiled['traces']), 2)
            review = next(t for t in compiled['traces'] if '协议' in t['goal'])
            self.assertEqual(review['pairIds'], [pairs[0]['id'], pairs[2]['id']])
            self.assertNotIn(pairs[1]['id'], review['pairIds'])
            self.assertEqual(review['feedbackEdges'][0]['targetPairId'], pairs[0]['id'])
            timeline = review['requirementTimeline']
            self.assertGreaterEqual(len(timeline), 2)
            last = timeline[-1]
            values = last.get('values')
            self.assertIsNotNone(values, 'dimension state must be auditable after REPLACE')
            rendered = json.dumps(values, ensure_ascii=False)
            self.assertIn('numbering', rendered)
            self.assertIn('output_format', rendered)
            self.assertIn('表格', rendered)
            self.assertNotEqual(review['businessOutcome'], 'SUCCESS')

    def test_context_and_evaluations_change_full_source_fingerprint(self):
        with tempfile.TemporaryDirectory() as root:
            loop = self.loop(root)
            pairs = self.imported_pairs(loop, [(INITIAL_REQUEST, INITIAL_REPLY)])
            from skilldemo import relational
            p1, _ = relational.prepare(pairs, context=[], evaluations=[])
            p2, _ = relational.prepare(pairs, context=[{'id': 'c1', 'kind': 'PUBLIC_CONTEXT', 'text': '公开环境说明。',
                                                     'source': 'SYNTHETIC_FIXTURE'}], evaluations=[])
            p3, _ = relational.prepare(pairs, context=[], evaluations=[{
                'id': 'v1', 'source': 'SYNTHETIC_FIXTURE', 'scope': 'TASK', 'status': 'UNKNOWN',
                'criterion': '总体交付待人工确认', 'targetIds': ['u1'], 'verified': False}])
            self.assertNotEqual(p1['sourceHash'], p2['sourceHash'])
            self.assertNotEqual(p1['sourceHash'], p3['sourceHash'])

    def test_metadata_change_invalidates_candidate_and_new_source_gets_a_new_request(self):
        with tempfile.TemporaryDirectory() as root:
            agent = HeuristicFixture()
            loop = self.loop(root, agent)
            experience = synthetic_experience()
            init = {'status': 'KNOWN_NONE', 'basis': 'Synthetic immutable initialization'}
            loop.import_experience('alice', experience, initialization=init)
            loop.run_stages('alice')
            loop.discover('alice')
            old = newest_candidate(loop, 'NEW')
            count = agent.calls.count('relational_extract')
            loop.run_stages('alice')
            self.assertEqual(agent.calls.count('relational_extract'), count)
            experience['context'][0]['text'] += ' 新公开约束：交付需包含待确认项。'
            loop.import_experience('alice', experience, initialization=init)
            stale = next(c for c in records(loop, 'candidate') if c['id'] == old['id'])
            self.assertEqual(stale['status'], 'STALE')
            loop.run_stages('alice')
            self.assertEqual(agent.calls.count('relational_extract'), count+1)
            with loop.store.tx() as db:
                metadata_history = loop.store.rows(db, 'experience_metadata_history', 'alice')
            self.assertEqual(len(metadata_history), 1)

    def test_joint_request_budget_wait_does_not_consume_attempt_or_automatically_retry_failure(self):
        class InvalidFixture(HeuristicFixture):
            def run(self, purpose, payload, workspace):
                result = super().run(purpose, payload, workspace)
                if purpose == 'relational_extract':
                    answer = json.loads(result['text'])
                    answer['observations'][0]['evidence'] = {'span': 'invented'}
                    result['text'] = json.dumps(answer, ensure_ascii=False)
                return result
        with tempfile.TemporaryDirectory() as root:
            agent = InvalidFixture()
            loop = self.loop(root, agent)
            loop.daily_limit = 0
            loop.import_experience('alice', synthetic_experience(), initialization={
                'status': 'KNOWN_NONE', 'basis': 'Synthetic fixture'})
            result = loop.run_stages('alice')
            self.assertIn('BUDGET_EXHAUSTED', json.dumps(result))
            self.assertFalse(agent.calls)
            with loop.store.tx() as db:
                index = loop.store.rows(db, 'front_analysis_request', 'alice')[0]
            self.assertEqual(index['attemptCount'], 0)
            loop.daily_limit = 1
            loop.run_stages('alice')
            self.assertEqual(agent.calls, ['relational_extract'])
            loop.run_stages('alice')
            self.assertEqual(agent.calls, ['relational_extract'])

    def test_invalid_reference_and_future_feedback_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            loop = self.loop(root)
            pairs = self.imported_pairs(loop, [(INITIAL_REQUEST, INITIAL_REPLY), (FEEDBACK_REQUEST, FEEDBACK_REPLY)])
            def missing(output, payload):
                output['observations'][0]['evidence'] = {'span': 'invented-span'}
            with self.assertRaises(ValueError):
                self.compile(pairs, missing)
            def future(output, payload):
                option = output['relations'][0]['options'][0]
                output['relations'][0]['source'] = 'q1:f1'
                option['target'] = 'q2:f1'
            with self.assertRaises(ValueError):
                self.compile(pairs, future)

    def test_ambiguous_membership_is_retained_without_forcing_a_task(self):
        with tempfile.TemporaryDirectory() as root:
            loop = self.loop(root)
            pairs = self.imported_pairs(loop, [
                (INITIAL_REQUEST, INITIAL_REPLY),
                ('请另写提醒邮件，通知同事明天提交材料。', '提醒邮件草稿：请明天提交材料。'),
                ('刚才那个再调整一下。', '对象尚不明确，请确认要调整哪项交付。'),
            ])
            def ambiguous(output, payload):
                fragment = output['annotations'][2]['fragments'][0]
                fragment.update(kind='UNRESOLVED', task=None, alternatives=['t1','t2'],
                                uncertainty='缺少对象，两个候选均可能')
                output['memberships'][2]['options'] = [
                    {'task': task, 'status': 'CONFIRMED', 'score': .5, 'reason': '两个候选得分相同且对象缺失'}
                    for task in ('t1','t2')]
                output['observations'] = [o for o in output['observations'] if o['fragment'] != 'q3:f1']
                output['uncertainties'].append({'fragment': 'q3:f1', 'reason': '仍缺少调整对象'})
            compiled, _, _ = self.compile(pairs, ambiguous)
            self.assertTrue(compiled['unresolved'])
            self.assertFalse(any(pairs[2]['id'] in t['pairIds'] for t in compiled['traces']))
            self.assertTrue(any(t.get('searchAudit') for t in compiled['traces']))

    def test_progress_text_does_not_create_executed_attempt(self):
        with tempfile.TemporaryDirectory() as root:
            loop = self.loop(root)
            pairs = self.imported_pairs(loop, [(INITIAL_REQUEST, '正在准备核对，尚未交付结果。')])
            def progress(output, payload):
                for observation in output['observations']:
                    observation['kind'] = 'PROGRESS_TEXT'
            compiled, _, _ = self.compile(pairs, progress)
            trace = compiled['traces'][0]
            self.assertFalse(trace['attempts'])
            self.assertEqual(trace['businessOutcome'], 'UNKNOWN')

    def test_failed_call_binding_is_not_overridden_by_assistant_success_claim(self):
        with tempfile.TemporaryDirectory() as root:
            loop = self.loop(root)
            pairs = self.imported_pairs(loop, [(INITIAL_REQUEST, '操作成功，文件已生成。')])
            pairs[0]['toolEvents'] = [{
                'id': 'synthetic-call-1', 'callId': 'synthetic-call-1', 'name': 'exec',
                'arguments': {'command': 'synthetic command'}, 'status': 'FAILED',
                'result': 'Synthetic test error: command exited with status 1',
                'recordBasis': 'SYNTHETIC_FIXTURE_CALL_RESULT', 'receipt': False}]
            from skilldemo import relational
            payload, aliases = relational.prepare(pairs, context=[], evaluations=[])
            output = relational_answer(payload)
            catalog = payload['evidence']
            items = list(catalog.values()) if isinstance(catalog, dict) else catalog
            tools = [item for item in items if item['kind'] in ('TOOL_CALL','TOOL_RESULT')]
            self.assertEqual({item['kind'] for item in tools}, {'TOOL_CALL','TOOL_RESULT'})
            output['executionBindings'] = [{'evidenceId': item['id'], 'fragment': 'q1:f1'} for item in tools]
            compiled = relational.compile_result(output, payload, aliases)
            trace = compiled['traces'][0]
            self.assertNotEqual(trace['businessOutcome'], 'SUCCESS')
            outcomes = trace.get('outcomeEvidence', [])
            self.assertTrue(any(e.get('status') == 'FAILURE' and e.get('outcomeType') == 'TECHNICAL'
                                for e in outcomes), json.dumps(outcomes, ensure_ascii=False))
            self.assertTrue(any(o.get('kind') == 'EXECUTION_CLAIM' for o in trace['observations']))
            def forged_binding(answer, view):
                answer['executionBindings'].append({'evidenceId': 'invented-call', 'fragment': 'q1:f1'})
            with self.assertRaises(ValueError):
                self.compile(pairs, forged_binding)

    def test_task_evaluation_does_not_certify_a_local_method(self):
        with tempfile.TemporaryDirectory() as root:
            loop = self.loop(root)
            pairs = self.imported_pairs(loop, [(INITIAL_REQUEST, INITIAL_REPLY)])
            evaluation = {'id': 'synthetic-task-eval', 'source': 'SYNTHETIC_FIXTURE',
                          'scope': 'TASK', 'targetIds': ['u1'], 'criterion': '总体交付被人工fixture认可',
                          'status': 'SUCCESS', 'outcomeType': 'BUSINESS', 'verified': True,
                          'verificationBasis': 'Synthetic test assertion; no actual business verification'}
            def bind(output, payload):
                catalog = payload['evidence']
                items = list(catalog.values()) if isinstance(catalog, dict) else catalog
                evaluation_row = next(e for e in items if e['kind'] == 'EVALUATION')
                output['evaluationBindings'] = [{'evaluationId': evaluation_row['id'],
                                                 'fragment': 'q1:f1', 'scope': 'TASK',
                                                 'requirementVersion': 1}]
            compiled, _, _ = self.compile(pairs, bind, evaluations=[evaluation])
            trace = {**compiled['traces'][0], 'revision': 1}
            from skilldemo import workflow
            from skilldemo.workflow_index import expand
            view, catalog = workflow.prepare([trace])
            answer = workflow_answer(view)
            task_sources = [catalog[eid] for eid in expand(view)['traces'][0]['allowedEvidenceIds']
                            if catalog[eid]['kind'] in ('EVALUATION','OUTCOME_EVIDENCE','TASK_EVALUATION')]
            self.assertTrue(task_sources, 'stage4 must retain scoped task evaluation')
            answer['methods'][0].update(evidenceRefs=[task_sources[0]['id']],
                                        evidenceKind='VERIFIED_CHECK', outcome='SUCCESS')
            extracted = workflow.validate_extract(answer, view, catalog)
            self.assertNotEqual(extracted['methods'][0]['outcome'], 'SUCCESS')

    def test_current_and_future_scope_survive_workflow_and_creator_coverage(self):
        from skilldemo import workflow
        from skilldemo.bootstrap import draft_files
        from skilldemo.creator import verify_files
        with tempfile.TemporaryDirectory() as root:
            loop = self.loop(Path(root)/'state')
            pairs = self.imported_pairs(loop, [(INITIAL_REQUEST, INITIAL_REPLY),
                                                (FEEDBACK_REQUEST, FEEDBACK_REPLY)])
            compiled, _, _ = self.compile(pairs)
            trace = {**compiled['traces'][0], 'revision': 1}
            view, catalog = workflow.prepare([trace])
            from skilldemo.workflow_index import expand
            evidence = [catalog[eid] for eid in expand(view)['traces'][0]['allowedEvidenceIds']]
            current = next(e for e in evidence if e['kind'] == 'USER_REQUIREMENT'
                           and e['scope'] == 'CURRENT_TASK')
            future = next(e for e in evidence if e['kind'] in ('USER_REQUIREMENT', 'USER_FEEDBACK')
                          and e['scope'] == 'FUTURE_TASKS' and '以后' in e['text'])
            answer = workflow_answer(view)
            answer['methods'][0]['evidenceRefs'] = [current['id'], future['id']]
            extracted = workflow.validate_extract(answer, view, catalog)
            method = extracted['methods'][0]
            bindings = method['scopeContract']['bindings']
            by_scope = {binding['scope']: binding for binding in bindings}
            self.assertIn('CURRENT_TASK', by_scope)
            self.assertIn('FUTURE_TASKS', by_scope)
            self.assertEqual(by_scope['CURRENT_TASK']['mode'], 'INSTANCE_PARAMETER')
            self.assertEqual(by_scope['FUTURE_TASKS']['mode'], 'EXPLICIT_PERSONAL_PREFERENCE')
            public = workflow.relational_workflow.public_method(method)
            self.assertEqual(public['scopeContract'], method['scopeContract'])
            workspace = Path(root)/'scope-creator'
            result = HeuristicFixture().run('workflow_creator', {'methods': [public]}, workspace)
            output = json.loads(result['text'])
            package = draft_files(workspace)
            checked = verify_files(package, [method['id']], methods=[public],
                                   coverageManifest=output['coverageManifest'])
            self.assertEqual(checked['status'], 'PASS')
            body = package[0]['content']
            for binding in bindings:
                self.assertIn(binding['text'], body)
            missing_future = copy.deepcopy(output['coverageManifest'])
            missing_future[0]['scopeQuotes'] = [q for q in missing_future[0]['scopeQuotes']
                                               if q['scopeId'] != by_scope['FUTURE_TASKS']['id']]
            with self.assertRaises(ValueError):
                verify_files(package, [method['id']], methods=[public], coverageManifest=missing_future)
            missing_scope_body = copy.deepcopy(package)
            missing_scope_body[0]['content'] = body.replace(by_scope['FUTURE_TASKS']['text'], '')
            with self.assertRaises(ValueError):
                verify_files(missing_scope_body, [method['id']], methods=[public],
                             coverageManifest=output['coverageManifest'])

    def test_evaluation_allowlist_rejects_hidden_gold_fields(self):
        from skilldemo.evidence import normalize_evaluations
        with self.assertRaises(ValueError):
            normalize_evaluations([{'id': 'bad', 'source': 'SYNTHETIC_FIXTURE', 'scope': 'TASK',
                                   'targetIds': ['u1'], 'criterion': 'public criterion',
                                   'reward_info': {'hidden_answer': 'Never pass this into learning'}}])

    def test_raw_tool_failure_status_survives_source_normalization(self):
        from skilldemo import evidence, intake
        source = [
            {'id': 'u', 'sessionId': 'raw-tool', 'role': 'user', 'content': INITIAL_REQUEST},
            {'id': 'a', 'sessionId': 'raw-tool', 'role': 'assistant', 'content': '已发起操作。',
             'responseTo': 'u', 'toolCalls': [{'id': 'call-1', 'name': 'exec',
                                            'arguments': {'command': 'synthetic command'}}]},
            {'id': 'tool-1', 'sessionId': 'raw-tool', 'role': 'tool', 'content': 'Synthetic command failed',
             'callId': 'call-1', 'status': 'FAILED'},
        ]
        events = [intake.event('alice', row, 'generation', index) for index, row in enumerate(source, 1)]
        pairs, unassigned = intake.assemble(events, {'status': 'KNOWN_NONE', 'basis': 'Synthetic fixture'})
        self.assertFalse(unassigned)
        catalog = evidence.catalog(pairs)
        result = next(e for e in catalog if e['kind'] == 'TOOL_RESULT')
        self.assertEqual(result['metadata']['status'], 'FAILED')

    def test_recorded_no_argument_tool_call_is_not_silently_dropped(self):
        from skilldemo import evidence, intake
        source = [
            {'id': 'u', 'sessionId': 'no-args', 'role': 'user', 'content': '请读取当前公开状态。'},
            {'id': 'a', 'sessionId': 'no-args', 'role': 'assistant', 'content': '已发起状态读取。',
             'responseTo': 'u', 'toolCalls': [{'id': 'status-call', 'name': 'get_status'}]},
        ]
        events = [intake.event('alice', row, 'generation', index) for index, row in enumerate(source, 1)]
        pairs, _ = intake.assemble(events, {'status': 'KNOWN_NONE', 'basis': 'Synthetic fixture'})
        calls = [e for e in evidence.catalog(pairs) if e['kind'] == 'TOOL_CALL']
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]['metadata']['callId'], 'status-call')

    def test_missing_assistant_content_does_not_fabricate_a_delivery(self):
        with tempfile.TemporaryDirectory() as root:
            loop = self.loop(root)
            loop.import_experience('alice', {'events': [
                {'id': 'missing-u', 'sessionId': 'missing', 'role': 'user', 'order': 1, 'content': INITIAL_REQUEST}],
                'context': [], 'evaluations': []}, initialization={'status': 'KNOWN_NONE', 'basis': 'Synthetic fixture'})
            loop.run_stages('alice')
            for trace in records(loop, 'trace'):
                self.assertFalse(trace['attempts'])
                self.assertEqual(trace['businessOutcome'], 'UNKNOWN')
                self.assertIn('MISSING_CONTENT', json.dumps(trace['unresolved']))
            self.assertFalse(records(loop, 'candidate'))
            pair = records(loop, 'qa_pair')[0]
            self.assertEqual(pair['contentStatus'], 'MISSING_CONTENT')
            self.assertEqual(pair['user'], INITIAL_REQUEST)
            self.assertEqual(pair['sourceUserMessageId'], 'missing-u')

    def test_complete_link_does_not_bridge_incompatible_third_frame(self):
        from skilldemo import workflow
        # This host constraint is meaningful independently of model semantics:
        # f1~f2 and f2~f3 must not hide an explicit f1/f3 incompatibility.
        traces = []
        for i in range(1, 4):
            traces.append({'id': 't'+str(i), 'owner': 'alice', 'purposeSplit': 'generation',
                           'schemaVersion': 'task-trace-v2', 'state': 'SEALED', 'revision': 1,
                           'hash': 'h'+str(i), 'goal': '审阅要求', 'object': '合成协议',
                           'requirementTimeline': [{'version': 1, 'requestedText': INITIAL_REQUEST,
                                                    'effectiveFromPairId': 'p'+str(i)}],
                           'initializationEvidence': [{'status': 'KNOWN_NONE', 'basis': 'Synthetic no skill'}],
                           'attempts': [], 'skillUseReceipts': [], 'feedbackEdges': [], 'observations': [], 'unresolved': []})
        payload, catalog = workflow.prepare(traces)
        answer = workflow_answer(payload)
        answer['relations'] = [
            {'left': a, 'right': b, 'kind': kind, 'sharedSteps': ['核对交付形式'] if kind == 'SHARE_CORE' else [],
             'condition': '', 'reason': '人工fixture明确给定的两两关系'}
            for a, b, kind in [('f1','f2','SHARE_CORE'), ('f2','f3','SHARE_CORE'), ('f1','f3','INCOMPATIBLE')]]
        extracted = workflow.validate_extract(answer, payload, catalog)
        groups, _ = workflow.clusters(extracted, traces, catalog)
        self.assertEqual(sorted(map(len, groups)), [1, 2])


if __name__ == '__main__':
    unittest.main()
