import unittest
from copy import deepcopy

from skilldemo import workflow, relational_workflow
from skilldemo.learning import compile_patch, initial_files
from skilldemo.runtime import digest
from skilldemo.creator import verify_files
from test_relational import prepared, proposal, span


def trace():
    return {'id': 't1', 'owner': 'alice', 'org': 'acme', 'schemaVersion': 'task-trace-v2',
            'relationalSchema': 'relational-trace-v1', 'purposeSplit': 'generation',
            'state': 'SEALED', 'revision': 1, 'hash': 'trace-hash', 'goal': '处理订单',
            'businessOutcome': 'UNKNOWN', 'initializationEvidence': [{'status': 'KNOWN_NONE', 'basis': 'fixture'}],
            'skillUseReceipts': [], 'requirementTimeline': [], 'feedbackEdges': [],
            'observations': [], 'unresolved': [],
            'requirements': [{'id': 'r1', 'dimension': 'operation', 'status': 'ACTIVE', 'version': 1,
                              'effectiveFromPairId': 'p1', 'value': '检查状态后修改地址', 'evidenceRefs': ['u1']}],
            'attempts': [{'id': 'a1', 'pairId': 'p1', 'fragmentId': 'f1', 'requirementVersion': 1,
                          'requirementIds': ['r1'], 'evidenceRefs': ['process1'], 'executionRefs': {}}],
            'typedSources': [{'id': 'u1', 'kind': 'USER_REQUIREMENT', 'text': '检查状态后修改地址',
                              'ref': {'pairId': 'p1'}, 'metadata': {}},
                             {'id': 'process1', 'kind': 'VISIBLE_PROCESS', 'text': '先查状态，再修改地址。',
                              'ref': {'pairId': 'p1', 'attemptId': 'a1'}, 'metadata': {}}],
            'typedRelations': [], 'outcomeEvidence': []}


def extracted(t, source='process1', **overrides):
    payload, catalog = workflow.prepare([t])
    eid = next((eid for eid, row in catalog.items() if row.get('sourceId') == source), None)
    if eid is None:
        raise AssertionError('typed source was not projected into the stage-4 catalog: ' + source)
    method = {'id': 'm1', 'frameId': 'f1', 'action': '检查状态后修改地址', 'inputs': ['订单状态', '地址'],
              'outputs': ['修改结果'], 'conditions': [], 'parameters': [], 'completionCheck': '检查修改结果',
              'evidenceRefs': [eid], 'requirementIds': ['r1'], 'attemptIds': ['a1'],
              'decisionHint': 'INCLUDE', 'outcome': 'SUCCESS'}
    method.update(overrides)
    output = {'sourceHash': payload['sourceHash'], 'frames': [{'id': 'f1', 'traceId': t['id'],
              'goal': '处理订单', 'inputContract': ['订单状态', '地址'], 'outputContract': ['修改结果'],
              'processSketch': ['查询状态', '修改地址'], 'conditions': [], 'parameters': [], 'methodIds': ['m1']}],
              'methods': [method], 'relations': []}
    return payload, catalog, workflow.validate_extract(output, payload, catalog)


def merged_view(t, **method):
    payload, catalog, ext = extracted(t, **method)
    groups, routes = workflow.clusters(ext, [t], catalog)
    view = workflow.merge_input(ext, groups, routes, payload)
    output = {'sourceHash': view['sourceHash'], 'workflows': [{'frameIds': ['f1'], 'title': '地址修改',
              'trigger': '用户要求修改地址', 'inputs': ['订单状态', '地址'], 'outputs': ['修改结果'],
              'steps': [{'id': 's1', 'methodIds': ['m1'], 'action': '检查状态后修改地址',
                         'completionCheck': '检查修改结果'}], 'limitations': [], 'includedMethodIds': ['m1']}],
              'ledger': [{'methodId': 'm1', 'disposition': 'INCLUDED', 'reason': '有来源支持'}]}
    return ext, view, output


class RelationalWorkflowTests(unittest.TestCase):
    def test_full_typed_sources_and_relationships_are_projected(self):
        t = trace()
        t['typedRelations'] = [{'id': 'dep1', 'type': 'DEPENDS_ON', 'from': 'a1', 'to': 'r1',
                                'status': 'CONFIRMED', 'evidenceRefs': ['u1'], 'scope': 'CURRENT_TASK'}]
        t['typedSources'][1]['metadata'] = {'callId': 'call-1', 'result': {'status': 'pending'}}
        payload, catalog = workflow.prepare([t])
        from skilldemo.workflow_index import expand
        payload = expand(payload)
        self.assertEqual(payload['traces'][0]['typedRelations'], t['typedRelations'])
        self.assertEqual(payload['traces'][0]['typedSources'], t['typedSources'])
        row = next(r for r in catalog.values() if r.get('sourceId') == 'process1')
        self.assertEqual(row['metadata']['callId'], 'call-1')

    def test_task_success_does_not_prove_a_method(self):
        t = trace()
        t['outcomeEvidence'] = [{'id': 'v1', 'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS',
            'status': 'SUCCESS', 'scope': 'TASK', 'targetIds': ['t1'], 'criterion': '最终任务完成',
            'ref': {'sourceId': 'v1'}, 'verified': True}]
        _, _, ext = extracted(t)
        self.assertEqual(ext['methods'][0]['outcome'], 'UNKNOWN')
        self.assertNotIn('v1', ext['methods'][0]['supportAssessment']['validationEvidenceIds'])

    def test_attempt_business_result_is_scoped_and_preserved(self):
        t = trace()
        t['outcomeEvidence'] = [{'id': 'v1', 'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS',
            'status': 'SUCCESS', 'scope': 'ATTEMPT', 'targetIds': ['a1'], 'criterion': '地址符合要求',
            'ref': {'sourceId': 'v1'}, 'verified': True}]
        _, _, ext = extracted(t)
        method = ext['methods'][0]
        self.assertEqual(method['outcome'], 'SUCCESS')
        self.assertEqual(method['supportAssessment']['validationEvidenceIds'], ['v1'])
        self.assertEqual(method['supportAssessment']['validationScope'], ['ATTEMPT'])

    def test_tool_success_remains_technical(self):
        t = trace()
        t['outcomeEvidence'] = [{'id': 'tool1', 'sourceType': 'TOOL_RESULT', 'outcomeType': 'TECHNICAL',
            'status': 'SUCCESS', 'scope': 'ATTEMPT', 'targetIds': ['a1'], 'criterion': '调用返回',
            'ref': {}, 'verified': True}]
        _, _, ext = extracted(t)
        self.assertEqual(ext['methods'][0]['outcome'], 'UNKNOWN')
        self.assertEqual(ext['methods'][0]['supportAssessment']['technicalOutcome'], 'SUCCESS')

    def test_same_pair_two_calls_do_not_share_attempt_outcomes(self):
        t = trace()
        t['typedSources'][1].update(id='callA', kind='TOOL_CALL', text='query A',
                                   ref={'pairId': 'p1', 'attemptId': 'a1'})
        t['attempts'][0]['evidenceRefs'] = ['callA']
        t['attempts'].append({'id': 'a2', 'pairId': 'p1', 'fragmentId': 'f1',
                              'requirementIds': ['r1'], 'evidenceRefs': ['callB']})
        t['typedSources'].append({'id': 'callB', 'kind': 'TOOL_CALL', 'text': 'modify B',
                                 'ref': {'pairId': 'p1', 'attemptId': 'a2'}, 'metadata': {}})
        t['outcomeEvidence'] = [
            {'id': 'a-ok', 'sourceType': 'TOOL_RESULT', 'outcomeType': 'TECHNICAL',
             'status': 'SUCCESS', 'scope': 'ATTEMPT', 'targetIds': ['a1'], 'ref': {}, 'verified': True},
            {'id': 'b-fail', 'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS',
             'status': 'FAILURE', 'scope': 'ATTEMPT', 'targetIds': ['a2'], 'ref': {}, 'verified': True}]
        _, _, ext = extracted(t, source='callA', attemptIds=[])
        m = ext['methods'][0]
        self.assertEqual(m['attemptIds'], ['a1'])
        self.assertEqual(m['outcome'], 'UNKNOWN')
        self.assertEqual(m['supportAssessment']['technicalOutcome'], 'SUCCESS')
        self.assertNotIn('b-fail', m['supportAssessment']['validationEvidenceIds'])

    def test_plan_only_is_deferred_not_an_executed_capability(self):
        t = trace()
        t['typedSources'][1].update(kind='ASSISTANT_CLAIM', text='我将撤销已经完成的取消操作。')
        _, _, ext = extracted(t)
        self.assertEqual(ext['methods'][0]['decisionHint'], 'DEFER')
        self.assertEqual(ext['methods'][0]['supportAssessment']['supportStatus'], 'HYPOTHESIS')

    def test_progress_text_is_not_a_reusable_executed_method(self):
        t = trace()
        t['typedSources'][1].update(kind='PROGRESS_TEXT', text='请稍等，我正在处理。')
        _, _, ext = extracted(t)
        self.assertEqual(ext['methods'][0]['decisionHint'], 'DEFER')

    def test_format_revision_does_not_discard_unmodified_role_check(self):
        t = trace()
        t['requirements'] = [
            {'id': 'old-format', 'dimension': 'format', 'status': 'SUPERSEDED', 'version': 1,
             'value': 'Word', 'evidenceRefs': ['u1']},
            {'id': 'role', 'dimension': 'role', 'status': 'ACTIVE', 'version': 1,
             'value': 'supplier', 'evidenceRefs': ['u1']},
            {'id': 'new-format', 'dimension': 'format', 'status': 'ACTIVE', 'version': 2,
             'value': 'text', 'evidenceRefs': ['u2']}]
        t['attempts'][0]['requirementIds'] = ['old-format', 'role']
        _, _, ext = extracted(t, requirementIds=[], action='核对当前角色', requirementDimensions=['role'])
        m = ext['methods'][0]
        self.assertEqual(m['requirementIds'], ['role'])
        self.assertEqual(m['decisionHint'], 'INCLUDE')

    def test_quote_refs_do_not_break_requirement_binding(self):
        t = trace()
        t['requirements'][0]['evidenceRefs'] = [{'pairId': 'p1', 'side': 'user', 'quote': '检查状态'}]
        _, _, ext = extracted(t)
        self.assertEqual(ext['methods'][0]['requirementIds'], ['r1'])

    def test_actual_relation_kernel_preserves_role_method_after_format_revision(self):
        from skilldemo import relational
        payload, aliases = prepared([('supplier; Word output', '核对供应方角色。'),
                                     ('use text instead', '按当前格式输出。')])
        out = proposal(payload)
        out['requirements'] = [
            dict(fragment='q1:f1', dimension='role', op='ADD', value='supplier', evidence=[span(payload,'q1','user')]),
            dict(fragment='q1:f1', dimension='format', op='ADD', value='Word', evidence=[span(payload,'q1','user')]),
            dict(fragment='q2:f1', dimension='format', op='REPLACE', value='text', evidence=[span(payload,'q2','user')])]
        t = relational.compile_result(out, payload, aliases)['traces'][0]
        t.update(org='acme', revision=1)
        source = next(s['id'] for s in t['typedSources'] if s['kind'] == 'VISIBLE_PROCESS')
        _, _, ext = extracted(t, source=source, requirementIds=[], attemptIds=[],
                              requirementDimensions=['role'], action='核对当前角色')
        m = ext['methods'][0]
        self.assertEqual(m['decisionHint'], 'INCLUDE')
        self.assertEqual([r['dimension'] for r in t['requirements'] if r['id'] in m['requirementIds']], ['role'])
        deps = m['supportAssessment']['dependencyRelations']
        self.assertTrue(all(r['to'] in m['requirementIds'] for r in deps if r.get('basis') == 'REQUIREMENT_EFFECTIVE_AT_ATTEMPT'))

    def test_actual_relation_kernel_step_evaluation_reaches_only_bound_source(self):
        from skilldemo import relational
        catalog = [{'id': 'v1', 'kind': 'EVALUATION', 'text': '公开文本步骤核查通过', 'ref': {},
                    'metadata': {'targetIds': ['a0'], 'scope': 'STEP', 'status': 'SUCCESS',
                                 'outcomeType': 'BUSINESS', 'verified': True, 'verificationBasis': 'fixture check'}}]
        payload, aliases = prepared([('do work', '执行指定的文本核对步骤。')], catalog)
        out = proposal(payload)
        out['evaluationBindings'] = [dict(evaluationId='v1', fragment='q1:f1', scope='STEP')]
        t = relational.compile_result(out, payload, aliases)['traces'][0]
        t.update(org='acme', revision=1)
        source = next(s['id'] for s in t['typedSources'] if s['kind'] == 'VISIBLE_PROCESS')
        _, _, ext = extracted(t, source=source, requirementIds=[], attemptIds=[])
        self.assertEqual(ext['methods'][0]['supportAssessment']['methodOutcome'], 'SUCCESS')
        self.assertEqual(ext['methods'][0]['supportAssessment']['supportStatus'], 'SCOPED_SUCCESS')

    def test_requirement_id_without_source_association_is_rejected(self):
        t = trace()
        t['attempts'] = []
        t['typedSources'][1]['ref'] = {}
        with self.assertRaisesRegex(ValueError, '要求绑定'):
            extracted(t, attemptIds=[])

    def test_failed_process_is_retained_only_as_a_warning(self):
        t = trace()
        t['outcomeEvidence'] = [{'id': 'v1', 'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS',
            'status': 'FAILURE', 'scope': 'METHOD', 'targetIds': ['process1'], 'criterion': '修改失败',
            'ref': {}, 'verified': True}]
        _, _, ext = extracted(t)
        self.assertEqual(ext['methods'][0]['decisionHint'], 'INCLUDE')
        self.assertEqual(ext['methods'][0]['lessonType'], 'FAILURE_WARNING')
        _, _, ext = extracted(t, methodKind='FAILURE_GUARD', conditions=['先检查订单是否允许修改'])
        self.assertEqual(ext['methods'][0]['supportAssessment']['supportStatus'], 'FAILURE_BOUNDARY')
        self.assertEqual(ext['methods'][0]['decisionHint'], 'INCLUDE')
        self.assertEqual(ext['methods'][0]['lessonType'], 'FAILURE_WARNING')

    def test_mixed_user_source_cannot_hide_failed_process(self):
        t = trace()
        t['outcomeEvidence'] = [{'id': 'v1', 'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS',
            'status': 'FAILURE', 'scope': 'STEP', 'targetIds': ['process1'], 'criterion': '未完成修改',
            'ref': {}, 'verified': True}]
        payload, catalog, ext = extracted(t)
        out = {'sourceHash': payload['sourceHash'], 'frames': deepcopy(ext['frames']),
               'methods': deepcopy(ext['methods']), 'relations': []}
        out['methods'][0]['decisionHint'] = 'INCLUDE'
        out['methods'][0]['evidenceRefs'].append(next(e for e, s in catalog.items() if s.get('sourceId') == 'u1'))
        ext = workflow.validate_extract(out, payload, catalog)
        self.assertEqual(ext['methods'][0]['decisionHint'], 'INCLUDE')
        self.assertEqual(ext['methods'][0]['supportAssessment']['supportStatus'], 'FAILURE_BOUNDARY')
        self.assertEqual(ext['methods'][0]['lessonType'], 'FAILURE_WARNING')

    def test_validated_revision_needs_linked_old_failure_and_same_check(self):
        t = trace()
        t['typedSources'][1]['ref']['fragmentId'] = 'new-fragment'
        t['typedSources'].append({'id': 'old-process', 'kind': 'VISIBLE_PROCESS', 'text': '原地址修改',
            'ref': {'fragmentId': 'old-fragment', 'pairId': 'p0'}, 'metadata': {}})
        t['typedRelations'] = [{'id': 'repair', 'type': 'REVISES', 'from': 'new-fragment',
            'to': 'old-fragment', 'status': 'CONFIRMED', 'scope': 'CURRENT_TASK', 'evidenceRefs': ['u1']}]
        t['outcomeEvidence'] = [
            {'id': 'failed', 'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS', 'status': 'FAILURE',
             'scope': 'STEP', 'targetIds': ['old-process'], 'criterion': '地址符合要求', 'ref': {}, 'verified': True},
            {'id': 'fixed', 'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS', 'status': 'SUCCESS',
             'scope': 'STEP', 'targetIds': ['process1'], 'criterion': '地址符合要求', 'ref': {}, 'verified': True}]
        _, _, ext = extracted(t, methodKind='VALIDATED_REVISION')
        self.assertEqual(ext['methods'][0]['supportAssessment']['supportStatus'], 'VALIDATED_REVISION')
        self.assertEqual(ext['methods'][0]['lessonType'], 'PROCEDURE')
        t['outcomeEvidence'][1]['criterion'] = '编号保留'
        _, _, ext = extracted(t, methodKind='VALIDATED_REVISION')
        self.assertEqual(ext['methods'][0]['decisionHint'], 'DEFER')

    def test_superseded_requirement_cannot_support_current_rule(self):
        t = trace()
        t['requirements'][0]['status'] = 'SUPERSEDED'
        _, _, ext = extracted(t, source='u1')
        self.assertEqual(ext['methods'][0]['decisionHint'], 'DEFER')
        self.assertIn('SUPERSEDED_REQUIREMENT', ext['methods'][0]['supportAssessment']['limitations'])

    def test_failed_attempt_still_preserves_explicit_user_boundary(self):
        t = trace()
        t['outcomeEvidence'] = [{'id': 'v1', 'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS',
            'status': 'FAILURE', 'scope': 'ATTEMPT', 'targetIds': ['a1'], 'criterion': '地址不符合要求',
            'ref': {}, 'verified': True}]
        _, _, ext = extracted(t, source='u1')
        method = ext['methods'][0]
        self.assertEqual(method['outcome'], 'FAILURE')
        self.assertEqual(method['decisionHint'], 'INCLUDE')
        self.assertEqual(method['supportAssessment']['supportStatus'], 'USER_RULE')

    def test_ledger_binds_conditions_sources_and_validation_scope(self):
        t = trace()
        ext, view, output = merged_view(t, conditions=['只有订单状态允许时才修改地址'])
        workflows, _ = workflow.validate_merge(output, view, ext)
        clause = workflows[0]['clauseLedger'][0]
        self.assertEqual(clause['methodIds'], ['m1'])
        self.assertEqual(clause['sources'][0]['sourceId'], 'process1')
        self.assertIn('只有订单状态允许时才修改地址', clause['conditions'])
        self.assertEqual(clause['businessOutcome'], 'UNKNOWN')
        self.assertIn('只有订单状态允许时才修改地址', workflows[0]['steps'][0]['condition'])

    def test_deferred_plan_cannot_be_smuggled_into_merge(self):
        t = trace()
        t['typedSources'][1]['kind'] = 'ASSISTANT_CLAIM'
        ext, view, output = merged_view(t)
        with self.assertRaisesRegex(ValueError, '证据|待定|批准'):
            workflow.validate_merge(output, view, ext)

    def test_public_projection_keeps_constraints_and_removes_private_ledger(self):
        ext, view, output = merged_view(trace(), conditions=['只有状态允许时才修改'])
        ws, _ = workflow.validate_merge(output, view, ext)
        public = relational_workflow.public_workflow(ws[0])
        self.assertNotIn('clauseLedger', public)
        self.assertNotIn('frameIds', public)
        self.assertIn('只有状态允许时才修改', public['steps'][0]['condition'])
        method = relational_workflow.public_method(ext['methods'][0])
        self.assertNotIn('sourceBindings', method)
        self.assertNotIn('evidenceRefs', method)
        self.assertNotIn('requirementIds', method)

    def test_current_requirement_is_exposed_as_a_parameter_not_a_long_term_default(self):
        _, _, ext = extracted(trace())
        private = ext['methods'][0]
        public = relational_workflow.public_method(private)
        binding = public['scopeContract']['bindings'][0]
        self.assertEqual(binding['scope'], 'CURRENT_TASK')
        self.assertEqual(binding['mode'], 'INSTANCE_PARAMETER')
        self.assertIn('本次有效要求', public['parameters'])
        self.assertIn('不把历史取值作为长期默认', binding['text'])
        self.assertEqual(private['requirementApplicability'][0]['requirementId'], 'r1')
        self.assertNotIn('r1', str(public['scopeContract']))
        self.assertNotIn('检查状态后修改地址', str(public['scopeContract']))
        self.assertEqual(private['decisionHint'], 'INCLUDE')

    def test_current_and_future_scopes_are_both_preserved(self):
        t = trace()
        t['requirements'][0]['scope'] = 'CURRENT_DELIVERY'
        t['requirements'].append({'id': 'future', 'dimension': 'audit', 'scope': 'FUTURE_TASKS',
            'status': 'ACTIVE', 'version': 1, 'value': '每次列出待确认项', 'evidenceRefs': ['u1']})
        _, _, ext = extracted(t, source='u1', requirementIds=['r1', 'future'])
        c = relational_workflow.public_method(ext['methods'][0])['scopeContract']
        self.assertEqual({b['scope'] for b in c['bindings']}, {'CURRENT_DELIVERY', 'FUTURE_TASKS'})
        self.assertEqual({b['mode'] for b in c['bindings']},
                         {'INSTANCE_PARAMETER', 'EXPLICIT_PERSONAL_PREFERENCE'})

    def test_actual_shared_source_unknown_does_not_erase_distinct_requirement_scopes(self):
        from skilldemo import relational
        payload, aliases = prepared([('本次输出文本，以后每次附待确认项。', '收到要求。')])
        out = proposal(payload)
        out['requirements'] = [
            dict(fragment='q1:f1', dimension='content', op='ADD', value='输出文本', scope='CURRENT_TASK',
                 evidence=[span(payload,'q1','user')]),
            dict(fragment='q1:f1', dimension='content', op='ADD', value='附待确认项', scope='FUTURE_TASKS',
                 evidence=[span(payload,'q1','user')])]
        t = relational.compile_result(out, payload, aliases)['traces'][0]
        t.update(org='acme', revision=1)
        source = next(s for s in t['typedSources'] if s['kind'] == 'USER_REQUIREMENT')
        self.assertEqual(source['metadata']['scope'], 'UNKNOWN')
        _, _, ext = extracted(t, source=source['id'], requirementIds=[], attemptIds=[])
        contract = relational_workflow.public_method(ext['methods'][0])['scopeContract']
        self.assertEqual({b['scope'] for b in contract['bindings']}, {'CURRENT_TASK', 'FUTURE_TASKS'})

    def test_public_workflow_preserves_general_scope_contracts(self):
        ext, view, output = merged_view(trace())
        ws, _ = workflow.validate_merge(output, view, ext)
        private = ws[0]['clauseLedger'][0]
        self.assertEqual(private['requirementApplicability'][0]['requirementId'], 'r1')
        public = relational_workflow.public_workflow(ws[0])
        self.assertIn('scopeContracts', public)
        self.assertNotIn('source-span', str(public['scopeContracts']))
        self.assertNotIn('r1', str(public['scopeContracts']))

    def scope_package(self):
        _, _, ext = extracted(trace(), conditions=[])
        method = relational_workflow.public_method(ext['methods'][0])
        text = method['scopeContract']['bindings'][0]['text']
        body = '<!-- SKILLSLOOP_METHOD:m1 -->\n'+method['action']+'。\n'+text+'\n'+method['completionCheck']+'。'
        files = initial_files(None, '核对流程')
        files[0]['content'] = files[0]['content'].replace('待补充有依据的步骤。', body)
        coverage = [{'methodId': 'm1', 'file': 'SKILL.md', 'actionQuote': method['action'],
                     'conditionQuotes': [], 'completionCheckQuote': method['completionCheck'],
                     'scopeQuotes': [{'scopeId': 'scope1', 'quote': text}]}]
        return files, method, coverage, text

    def test_creator_scope_quote_is_exact_and_inside_the_method_body(self):
        files, method, coverage, _ = self.scope_package()
        result = verify_files(files, ['m1'], methods=[method], coverageManifest=coverage)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['methodCoverage'][0]['scopeCoverage'][0]['status'], 'HOST_SCOPE_ANCHORED')

    def test_creator_rejects_missing_wrong_or_comment_only_scope_coverage(self):
        for failure in ('missing', 'wrong', 'comment', 'fenced_method', 'quoted_code', 'indent_code', 'style'):
            files, method, coverage, text = self.scope_package()
            if failure == 'missing': coverage[0].pop('scopeQuotes')
            if failure == 'wrong': coverage[0]['scopeQuotes'][0]['quote'] = '本规则作为长期默认。'
            if failure == 'comment': files[0]['content'] = files[0]['content'].replace(text, '<!--'+text+'-->')
            if failure == 'fenced_method':
                files[0]['content'] = files[0]['content'].replace('<!-- SKILLSLOOP_METHOD:m1 -->',
                    '```text\n<!-- SKILLSLOOP_METHOD:m1 -->').replace('## 市场信息', '```\n\n## 市场信息')
            if failure == 'quoted_code': files[0]['content'] = files[0]['content'].replace(text, '> ```\n> '+text+'\n> ```')
            if failure == 'indent_code': files[0]['content'] = files[0]['content'].replace(text, '    '+text)
            if failure == 'style': files[0]['content'] = files[0]['content'].replace(text, '<style>\n'+text+'\n</style>')
            with self.assertRaisesRegex(ValueError, '范围'):
                verify_files(files, ['m1'], methods=[method], coverageManifest=coverage)

    def test_creator_cannot_cover_a_scope_contract_under_another_method(self):
        files, method, coverage, text = self.scope_package()
        other = {**deepcopy(method), 'id': 'm2'}
        files[0]['content'] = files[0]['content'].replace(text, '')
        files[0]['content'] = files[0]['content'].replace('## 市场信息',
            '<!-- SKILLSLOOP_METHOD:m2 -->\n'+method['action']+'\n'+text+'\n'+method['completionCheck']+'\n\n## 市场信息')
        coverage.append({**deepcopy(coverage[0]), 'methodId': 'm2'})
        with self.assertRaisesRegex(ValueError, '范围'):
            verify_files(files, ['m1', 'm2'], methods=[method, other], coverageManifest=coverage)

    def test_new_scope_package_cannot_claim_arbitrary_prose_covers_frozen_method(self):
        for field in ('action', 'condition', 'completion'):
            files, method, coverage, text = self.scope_package()
            unrelated = '任意六个字以上的无关描述。'
            files[0]['content'] = files[0]['content'].replace(text, text+'\n'+unrelated)
            if field == 'action': coverage[0]['actionQuote'] = unrelated
            if field == 'completion': coverage[0]['completionCheckQuote'] = unrelated
            if field == 'condition':
                method['conditions'] = ['只有本次要求允许时才执行']
                coverage[0]['conditionQuotes'] = [unrelated]
            with self.assertRaisesRegex(ValueError, '冻结'):
                verify_files(files, ['m1'], methods=[method], coverageManifest=coverage)

    def test_frozen_method_content_must_be_visible_in_its_own_method_block(self):
        for field, destination in [('action','comment'), ('completionCheck','fence'), ('action','other_method'),
                                   ('action','script')]:
            files, method, coverage, _ = self.scope_package()
            original = method[field]
            if destination == 'comment':
                fake = '足够长度的无关正文。<!--'+original+'-->'
                files[0]['content'] = files[0]['content'].replace(original, fake)
                coverage[0]['actionQuote'] = fake
            elif destination == 'fence':
                files[0]['content'] = files[0]['content'].replace(original, '```text\n'+original+'\n```')
            elif destination == 'script':
                files[0]['content'] = files[0]['content'].replace(original, '<script type="text/plain">'+original+'</script>')
            else:
                files[0]['content'] = files[0]['content'].replace(original, '其他足够长的可见描述。')
                files[0]['content'] = files[0]['content'].replace('## 市场信息',
                    '<!-- SKILLSLOOP_METHOD:m2 -->\n'+original+'\n其他步骤正文足够长度。\n## 市场信息')
            ids = ['m1', 'm2'] if destination == 'other_method' else ['m1']
            methods = [method, {**deepcopy(method), 'id':'m2'}] if len(ids) == 2 else [method]
            rows = coverage + [{**deepcopy(coverage[0]), 'methodId':'m2'}] if len(ids) == 2 else coverage
            with self.assertRaisesRegex(ValueError, '冻结'):
                verify_files(files, ids, methods=methods, coverageManifest=rows)

    def test_update_scope_uses_requirement_scope_despite_mixed_unknown_catalog(self):
        t = trace()
        t['requirements'][0]['scope'] = 'FUTURE_TASKS'
        t['typedSources'][0]['metadata']['scope'] = 'UNKNOWN'
        _, _, ext = extracted(t, source='u1')
        assessment = ext['methods'][0]['supportAssessment']
        self.assertEqual(assessment['sourceScopes'], ['FUTURE_TASKS'])
        self.assertEqual(assessment['catalogSourceScopes'], ['UNKNOWN'])
        payload, out = self.patch_fixture()
        payload['approvedMethods'][0]['supportAssessment'] = assessment
        payload['evidence'][0]['events'][0].update(kind='user', text='以后每次采用已确认的处理流程')
        out['analyses'][0]['proposals'][0].update(evidenceType='USER_RULE', applicabilityScope='FUTURE_TASKS',
            evidenceRefs=[{'eventId':'e1','quote':'以后每次采用已确认的处理流程'}])
        _, audit = compile_patch(payload, out)
        self.assertEqual(audit['proposalAudit'][0]['status'], 'PROPOSED')

    def test_update_scope_requires_the_cited_binding_not_a_future_sibling(self):
        from skilldemo import relational
        text = '本次交付输出文本，以后每次附待确认项。'
        r_payload, aliases = prepared([(text, '收到要求。')])
        recovered = proposal(r_payload)
        recovered['requirements'] = [
            dict(fragment='q1:f1', dimension='content', op='ADD', value='输出文本', scope='CURRENT_DELIVERY',
                 evidence=[span(r_payload,'q1','user')]),
            dict(fragment='q1:f1', dimension='content', op='ADD', value='附待确认项', scope='FUTURE_TASKS',
                 evidence=[span(r_payload,'q1','user')])]
        t = relational.compile_result(recovered, r_payload, aliases)['traces'][0]
        t.update(org='acme', revision=1)
        source = next(s for s in t['typedSources'] if s['kind'] == 'USER_REQUIREMENT')
        _, _, ext = extracted(t, source=source['id'], requirementIds=[], attemptIds=[])
        method = ext['methods'][0]
        self.assertEqual(source['metadata']['scope'], 'UNKNOWN')
        self.assertEqual({r['scope'] for r in method['requirementApplicability']},
                         {'CURRENT_DELIVERY', 'FUTURE_TASKS'})
        payload, out = self.patch_fixture()
        payload['approvedMethods'][0].update(requirementApplicability=method['requirementApplicability'],
            supportAssessment=method['supportAssessment'])
        payload['evidence'][0]['events'][0].update(kind='user', text=text, sourceId=source['id'])
        p = out['analyses'][0]['proposals'][0]
        p.update(evidenceType='USER_RULE', applicabilityScope='FUTURE_TASKS',
                 evidenceRefs=[{'eventId':'e1', 'quote':text}])
        _, audit = compile_patch(payload, out)
        self.assertEqual(audit['proposalAudit'][0]['status'], 'PROPOSED')
        p['evidenceRefs'][0]['quote'] = '本次交付输出文本'
        with self.assertRaisesRegex(ValueError, '来源适用范围'):
            compile_patch(payload, out)
        # A distinct, single-scope source keeps the existing legal short-quote behavior.
        single = [
            r for r in method['requirementApplicability'] if r['scope'] == 'FUTURE_TASKS']
        single[0]['evidenceRefs'] = ['independent-future-source']
        payload['approvedMethods'][0]['requirementApplicability'] = single
        payload['evidence'][0]['events'][0].update(sourceId='independent-future-source',
            text='以后每次附待确认项。', metadata={'scope':'FUTURE_TASKS'})
        p['evidenceRefs'][0]['quote'] = '以后每次附待确认项'
        _, audit = compile_patch(payload, out)
        self.assertEqual(audit['proposalAudit'][0]['status'], 'PROPOSED')

    def test_step_attempt_target_and_model_local_method_id_are_not_method_verification(self):
        for scope, target in [('STEP', 'a1'), ('METHOD', 'm1')]:
            t = trace()
            t['outcomeEvidence'] = [{'id': 'v1', 'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS',
                'status': 'SUCCESS', 'scope': scope, 'targetIds': [target], 'criterion': '步骤符合要求',
                'ref': {}, 'verified': True}]
            _, _, ext = extracted(t)
            a = ext['methods'][0]['supportAssessment']
            self.assertEqual(a['methodOutcome'], 'UNKNOWN')
            self.assertNotEqual(a['supportStatus'], 'SCOPED_SUCCESS')
            if scope == 'STEP':
                self.assertIn('NON_UNIQUE_METHOD_ATTRIBUTION', a['limitations'])

    def test_source_scoped_validation_shared_by_two_methods_is_not_broadcast(self):
        t = trace()
        t['outcomeEvidence'] = [{'id': 'v1', 'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS',
            'status': 'SUCCESS', 'scope': 'STEP', 'targetIds': ['process1'], 'criterion': '某一步通过',
            'ref': {}, 'verified': True}]
        payload, catalog, ext = extracted(t)
        m2 = deepcopy(ext['methods'][0]); m2.update(id='m2', action='另一方法')
        out = {'sourceHash': payload['sourceHash'], 'frames': deepcopy(ext['frames']),
               'methods': [deepcopy(ext['methods'][0]), m2], 'relations': []}
        out['frames'][0]['methodIds'].append('m2')
        ext = workflow.validate_extract(out, payload, catalog)
        self.assertTrue(all(m['supportAssessment']['methodOutcome'] == 'UNKNOWN' for m in ext['methods']))

    def test_clause_containing_verified_and_unknown_methods_stays_unknown(self):
        methods = {'m1': {'id': 'm1', 'frameId': 'f1', 'evidenceRefs': ['e1'], 'conditions': [],
                          'supportAssessment': {'eligible': True, 'methodOutcome': 'SUCCESS'}},
                   'm2': {'id': 'm2', 'frameId': 'f1', 'evidenceRefs': ['e2'], 'conditions': [],
                          'supportAssessment': {'eligible': True, 'methodOutcome': 'UNKNOWN'}}}
        ext = {'methodMap': methods, 'catalog': {'e1': {'sourceId': 'o1', 'ref': {}},
                                                'e2': {'sourceId': 'o2', 'ref': {}}}}
        w = {'trigger': '有任务时', 'steps': [{'id': 's1', 'methodIds': ['m1', 'm2'],
             'action': '两个动作', 'completionCheck': '分别检查'}], 'includedMethodIds': ['m1', 'm2'],
             'limitations': []}
        relational_workflow.validate_workflow(w, ext)
        self.assertEqual(w['clauseLedger'][0]['businessOutcome'], 'UNKNOWN')
        self.assertTrue(w['limitations'])

    def patch_fixture(self):
        files = initial_files(None, '订单修改')
        validation = {'id': 'v1', 'scope': 'METHOD', 'targetIds': ['source1'],
                      'outcomeType': 'BUSINESS', 'status': 'SUCCESS', 'methodResultEligible': True}
        methods = [dict(id=f'm{i}', sourceTaskId='t1', evidenceRefs=[f'e{i}'], boundNodeIds=[f'm{i}'],
                   verificationTargetIds=[f'source{i}'],
                   supportAssessment={'eligible': True, 'methodOutcome': 'SUCCESS' if i == 1 else 'UNKNOWN',
                                      'validations': [validation] if i == 1 else []}) for i in (1, 2)]
        payload = {'bridgeVersion': 'relational-workflow-evolution-v1', 'action': 'UPDATE',
            'approvedMethods': methods, 'initial_files': files,
            'evidence': [{'taskId': 't1', 'outcome': 'UNKNOWN', 'analyst': 'unknown',
                         'events': [dict(id=f'e{i}', kind='assistant', text=f'已完成步骤{i}') for i in (1, 2)]}]}
        proposal = {'id': 'p1', 'lesson': '执行已验证的修改方法', 'applicability': '状态允许的订单',
            'evidenceType': 'OBSERVED', 'approvedMethodIds': ['m1'],
            'evidenceRefs': [{'eventId': 'e1', 'quote': '已完成步骤1'}]}
        out = {'analyses': [{'taskId': 't1', 'analyst': 'unknown', 'proposals': [proposal]}],
            'mergedPatches': [{'proposalIds': ['p1'], 'operations': [{'op': 'append', 'path': 'SKILL.md',
                'beforeHash': digest(files[0]['content']), 'content': '状态允许时执行已验证的修改方法。'}]}]}
        return payload, out

    def test_only_verified_method_in_same_bundle_can_update_as_observed(self):
        payload, out = self.patch_fixture()
        files, audit = compile_patch(payload, out)
        self.assertEqual(audit['proposalAudit'][0]['status'], 'PROPOSED')
        self.assertNotIn('_hostObservedVerified', out['analyses'][0]['proposals'][0])
        out['analyses'][0]['proposals'][0].update(approvedMethodIds=['m2'],
            evidenceRefs=[{'eventId': 'e2', 'quote': '已完成步骤2'}])
        with self.assertRaisesRegex(ValueError, '同方法作用域'):
            compile_patch(payload, out)

    def test_task_score_technical_return_and_gratitude_cannot_authorize_observed(self):
        for scope, outcome_type, source_type in [('TASK', 'BUSINESS', 'EVALUATION'),
                ('METHOD', 'TECHNICAL', 'TOOL_RESULT'), ('METHOD', 'BUSINESS', 'USER_FEEDBACK')]:
            payload, out = self.patch_fixture()
            v = payload['approvedMethods'][0]['supportAssessment']['validations'][0]
            v.update(scope=scope, outcomeType=outcome_type, sourceType=source_type)
            with self.assertRaisesRegex(ValueError, '同方法作用域'):
                compile_patch(payload, out)

    def test_diagnosis_cannot_use_a_check_for_another_method(self):
        payload, out = self.patch_fixture()
        payload['evidence'][0]['events'].append(dict(id='v-other', kind='check', text='passed',
                                                   passed=True, scope='METHOD', targetIds=['m2']))
        out['analyses'][0]['proposals'][0]['diagnosis'] = {'cause': '修复', 'validationRefs': ['v-other']}
        with self.assertRaisesRegex(ValueError, '另一尝试或方法'):
            compile_patch(payload, out)

    def test_update_cannot_broaden_an_explicit_delivery_only_rule(self):
        payload, out = self.patch_fixture()
        payload['approvedMethods'][0]['supportAssessment']['sourceScopes'] = ['CURRENT_DELIVERY']
        out['analyses'][0]['proposals'][0]['applicabilityScope'] = 'FUTURE_TASKS'
        with self.assertRaisesRegex(ValueError, '来源适用范围'):
            compile_patch(payload, out)

    def test_update_preserves_existing_host_scope_guard(self):
        payload, out = self.patch_fixture()
        files, _, _, scope_text = self.scope_package()
        payload['initial_files'] = files
        op = out['mergedPatches'][0]['operations'][0]
        op['beforeHash'] = digest(files[0]['content'])
        result, audit = compile_patch(payload, out)
        self.assertIn(scope_text, result[0]['content'])
        self.assertEqual(audit['scopePreservation']['status'], 'HOST_SCOPE_PRESERVED')

    def test_update_cannot_remove_or_comment_out_existing_host_scope_guard(self):
        for replacement in ('', 'comment'):
            payload, out = self.patch_fixture()
            files, _, _, scope_text = self.scope_package()
            payload['initial_files'] = files
            out['mergedPatches'][0]['operations'] = [{'op':'replace', 'path':'SKILL.md',
                'beforeHash':digest(files[0]['content']), 'old':scope_text,
                'content':('<!--'+scope_text+'-->') if replacement else ''}]
            with self.assertRaisesRegex(ValueError, '范围'):
                compile_patch(payload, out)

    def test_legacy_and_relation_update_groups_keep_their_own_validators(self):
        from test_evolution import EvolutionTests
        from skilldemo.evolution import enqueue
        fixture = EvolutionTests()
        fixture.setUp()
        try:
            a = deepcopy(fixture.analysis); a['id'] = 'a2'
            m = a['validatedOutput']['methods'][0]
            m['supportAssessment'] = {'eligible': True, 'supportStatus': 'USER_RULE',
                                      'methodOutcome': 'UNKNOWN', 'validations': []}
            w = deepcopy(fixture.w); w.update(id='w2', analysisId='a2')
            with fixture.loop.store.tx() as db:
                fixture.loop.store.put(db, 'workflow_analysis', a)
                fixture.loop.store.put(db, 'workflow', w)
            rows = enqueue(fixture.loop, 'alice')
            self.assertEqual({r['input']['bridgeVersion'] for r in rows},
                             {'workflow-evolution-v1', 'relational-workflow-evolution-v1'})
        finally:
            fixture.tearDown()

    def test_whole_cluster_dependency_cycle_prevents_merge(self):
        t = trace()
        t['typedRelations'] = [{'id': 'd1', 'type': 'DEPENDS_ON', 'from': 'process1', 'to': 'process2',
            'status': 'CONFIRMED', 'evidenceRefs': ['u1'], 'scope': 'CURRENT_TASK'},
            {'id': 'd2', 'type': 'DEPENDS_ON', 'from': 'process2', 'to': 'process3',
             'status': 'CONFIRMED', 'evidenceRefs': ['u1'], 'scope': 'CURRENT_TASK'},
            {'id': 'd3', 'type': 'DEPENDS_ON', 'from': 'process3', 'to': 'process1',
             'status': 'CONFIRMED', 'evidenceRefs': ['u1'], 'scope': 'CURRENT_TASK'}]
        t['typedSources'] += [{'id': f'process{i}', 'kind': 'VISIBLE_PROCESS', 'text': f'执行流程步骤{i}',
                              'ref': {'pairId': 'p1'}, 'metadata': {}} for i in (2, 3)]
        payload, catalog, ext = extracted(t)
        for i in (2, 3):
            frame = deepcopy(ext['frames'][0]); frame.update(id=f'f{i}', methodIds=[f'm{i}'])
            method = deepcopy(ext['methods'][0]); method.update(id=f'm{i}', frameId=f'f{i}',
                evidenceRefs=[next(e for e, row in catalog.items() if row.get('sourceId') == f'process{i}')])
            ext['frames'].append(frame); ext['frameMap'][frame['id']] = frame
            ext['methods'].append(method); ext['methodMap'][method['id']] = method
        ext['pairMap'] = {(f'f{i}', f'f{j}'): {'kind': 'SHARE_CORE'} for i in (1, 2) for j in range(i+1, 4)}
        groups, _ = workflow.clusters(ext, [t], catalog)
        self.assertFalse(any(len(group) == 3 for group in groups))


if __name__ == '__main__':
    unittest.main()
