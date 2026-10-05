"""Local evidence constraints, not a semantic or downstream benchmark."""
from copy import deepcopy
import unittest

from skilldemo import local_experience as local


def fixture():
    experience = {'events': [
        {'id': 'u1', 'sessionId': 'session1', 'role': 'user', 'content': '保留编号并用表格输出。', 'sourceOrder': 1},
        {'id': 'a1', 'sessionId': 'session1', 'role': 'assistant', 'content': '|2.1|意见|', 'sourceOrder': 2},
        {'id': 'a2', 'sessionId': 'session1', 'role': 'assistant', 'content': '已创建订单。', 'sourceOrder': 3},
        {'id': 'a3', 'sessionId': 'session1', 'role': 'assistant', 'content': '', 'sourceOrder': 4,
         'toolCalls': [{'id': 'call1', 'name': 'modify_order', 'arguments': {'order_id': 'one'}}]},
        {'id': 'r1', 'sessionId': 'session1', 'role': 'tool', 'callId': 'call1', 'name': 'modify_order',
         'result': {'error': 'Order not pending'}, 'executionStatus': 'FAILED', 'sourceOrder': 5},
    ], 'context': [{'id': 'policy', 'kind': 'POLICY', 'text': '只有待处理订单可以修改。', 'source': 'public'}],
       'evaluations': [
           {'id': 'numbering', 'source': 'fixture-check', 'scope': 'ARTIFACT', 'targetIds': ['a1'],
            'criterion': '保留原编号', 'status': 'SUCCESS', 'verified': True, 'verificationBasis': 'exact numbering check'},
           {'id': 'task-score', 'source': 'fixture-check', 'scope': 'TASK', 'targetIds': ['t-original'],
            'criterion': '整个任务成功', 'status': 'SUCCESS', 'verified': True, 'verificationBasis': 'external score'},
       ]}
    trace = {'id': 't-original', 'taskId': 't-original', 'sessionIds': ['session1'],
             'sourceMessageIds': ['u1', 'a1', 'a2', 'a3', 'r1'], 'goal': '按要求处理订单与输出',
             'requirements': [], 'attempts': [], 'outcomeEvidence': [], 'typedSources': [], 'unresolved': []}
    return experience, [trace]


def answer(payload):
    return {'sourceHash': payload['sourceHash'], 'methods': [{
        'id': 'm1', 'trace': 't1', 'goal': '按编号输出审阅表', 'goalKey': 'review_output',
        'objectType': 'document', 'outputType': 'review_table', 'conditions': [], 'unknowns': [],
        'steps': [{'id': 's1', 'operator': 'render_review', 'action': '输出审阅表', 'actor': 'assistant',
                   'objectRole': 'review', 'effect': 'review_rendered', 'effectDimensions': ['numbering', 'format'],
                   'inputRoles': ['source_document'], 'outputRoles': ['review'], 'dependsOn': [],
                   'sourceRefs': ['e2'], 'kind': 'VISIBLE_OUTPUT', 'conditions': [],
                   'checks': [{'dimension': 'numbering', 'criterion': '保留原编号', 'evidenceRefs': ['v1']}]}],
    }], 'unassigned': []}


class LocalExperienceTests(unittest.TestCase):
    def setUp(self):
        self.experience, self.traces = fixture()
        self.payload = local.prepare(self.traces, self.experience)

    def compile(self, value=None):
        return local.compile_result(value or answer(self.payload), self.payload)

    def ref(self, alias):
        return 'source-' + self.payload['sourceHash'][:16] + ':' + alias

    def test_partial_check_does_not_certify_other_dimension(self):
        step = self.compile()['methods'][0]['steps'][0]
        self.assertEqual(step['checks'][0]['status'], 'SATISFIED')
        self.assertEqual(step['verdict'], 'UNKNOWN')
        self.assertIn('format', step['unverifiedDimensions'])
        self.assertIn('SEMANTIC', step['checks'][0]['verification'])

    def test_wrong_criterion_target_and_task_scope_cannot_be_promoted(self):
        for change, expected in [({'criterion': '输出表格'}, 'CRITERION_NOT_IDENTICAL'),
                                 ({'evidenceRefs': ['v2'], 'criterion': '整个任务成功'}, 'TASK_RESULT_NOT_LOCAL'),
                                 ({'sourceRefs': ['e3']}, 'TARGET_NOT_LOCAL')]:
            data = answer(self.payload)
            if 'sourceRefs' in change:
                data['methods'][0]['steps'][0].update(change)
            else:
                data['methods'][0]['steps'][0]['checks'][0].update(change)
            step = self.compile(data)['methods'][0]['steps'][0]
            self.assertEqual(step['checks'][0]['status'], 'UNKNOWN')
            self.assertIn(expected, step['checks'][0]['unknownReason'])

    def test_conflicting_checks_preserve_both_sources(self):
        value = deepcopy(self.experience['evaluations'][0])
        value.update(id='numbering-again', status='FAILURE')
        self.experience['evaluations'].append(value)
        self.payload = local.prepare(self.traces, self.experience)
        data = answer(self.payload)
        # Deliberately omit the negative check from the model answer.  The host
        # must recover this already-known same-criterion counterexample.
        check = self.compile(data)['methods'][0]['steps'][0]['checks'][0]
        self.assertEqual(check['status'], 'CONFLICT')
        self.assertEqual(check['supportRefs'], [self.ref('v1')])
        self.assertEqual(check['counterRefs'], [self.ref('v3')])

    def test_unverified_evaluation_retains_report_but_not_certified_status(self):
        self.experience['evaluations'][0]['verified'] = False
        self.payload = local.prepare(self.traces, self.experience)
        check = self.compile()['methods'][0]['steps'][0]['checks'][0]
        self.assertEqual(check['status'], 'UNKNOWN')
        self.assertEqual(check['reportedEvidence'][0]['reportedStatus'], 'SUCCESS')

    def test_known_local_failure_cannot_disappear_when_model_omits_checks(self):
        self.experience['evaluations'][0]['status'] = 'FAILURE'
        self.payload = local.prepare(self.traces, self.experience)
        data = answer(self.payload)
        data['methods'][0]['steps'][0]['checks'] = []
        step = self.compile(data)['methods'][0]['steps'][0]
        self.assertEqual(step['verdict'], 'VIOLATED')
        self.assertEqual(step['checks'][0]['counterRefs'], [self.ref('v1')])
        self.assertTrue(step['checks'][0]['dimension'].startswith('criterion:'))

    def test_reused_message_id_across_sessions_does_not_broadcast_evaluation(self):
        self.experience['events'].append({'id': 'a1', 'sessionId': 'another-session', 'role': 'assistant',
                                          'content': 'another output', 'sourceOrder': 1})
        self.payload = local.prepare(self.traces, self.experience)
        check = self.compile()['methods'][0]['steps'][0]['checks'][0]
        self.assertEqual(check['status'], 'UNKNOWN')
        self.assertIn('TARGET_AMBIGUOUS_ACROSS_SESSIONS', check['unknownReason'])

    def test_self_claim_cannot_become_action_or_gain_task_success(self):
        data = answer(self.payload)
        step = data['methods'][0]['steps'][0]
        step.update(kind='ACTION', sourceRefs=['e3'], effectDimensions=['order_created'])
        step['checks'] = [{'criterion': '整个任务成功', 'dimension': 'order_created', 'evidenceRefs': ['v2']}]
        result = self.compile(data)['methods'][0]['steps'][0]
        self.assertEqual(result['kind'], 'CLAIM')
        self.assertEqual(result['verdict'], 'UNKNOWN')
        self.assertTrue(result['normalizationNotes'])

    def test_actual_call_failure_is_kept_and_cannot_be_written_as_success(self):
        data = answer(self.payload)
        step = data['methods'][0]['steps'][0]
        step.update(kind='ACTION', sourceRefs=['e4.c1'], effectDimensions=['address_changed'],
                    operator='invented_tool', actor='user', checks=[])
        result = self.compile(data)['methods'][0]['steps'][0]
        self.assertEqual(result['operator'], 'modify_order')
        self.assertEqual(result['actor'], 'assistant')
        self.assertEqual(result['verdict'], 'VIOLATED')
        self.assertIn(self.ref('e5'), result['sourceRefs'])
        self.assertEqual(result['checks'][0]['dimension'], 'tool_reported_result')

    def test_timeout_does_not_prove_backend_failure(self):
        self.experience['events'][-1].update(executionStatus='TIMEOUT', result={'error': 'Request timeout'})
        self.payload = local.prepare(self.traces, self.experience)
        data = answer(self.payload)
        data['methods'][0]['steps'][0].update(kind='ACTION', sourceRefs=['e4.c1'], checks=[])
        step = self.compile(data)['methods'][0]['steps'][0]
        self.assertEqual(step['verdict'], 'UNKNOWN')
        self.assertEqual(step['checks'][0]['status'], 'UNKNOWN')

    def test_omitted_actual_action_and_negative_evidence_are_retained(self):
        output = self.compile()
        missed = {row['sourceRef']: row for row in output['unassigned']}
        self.assertIn(self.ref('e4.c1'), missed)
        self.assertIn(self.ref('e5'), missed)
        self.assertEqual(missed[self.ref('e4.c1')]['reasonCode'], 'UNASSIGNED_ACTUAL_ACTION')

    def test_dependencies_checked_and_source_closure_retained(self):
        data = answer(self.payload)
        first = data['methods'][0]['steps'][0]
        second = deepcopy(first)
        second.update(id='s2', sourceRefs=['e3'], dependsOn=['s1'], checks=[], kind='CLAIM')
        data['methods'][0]['steps'].append(second)
        method = self.compile(data)['methods'][0]
        self.assertEqual(method['steps'][1]['dependencyClosure'], ['s1'])
        self.assertIn(self.ref('e2'), method['steps'][1]['evidenceClosure'])
        first['dependsOn'] = ['s2']
        with self.assertRaisesRegex(ValueError, '依赖'):
            self.compile(data)

    def test_unknown_reference_is_rejected_instead_of_fabricated(self):
        data = answer(self.payload)
        data['methods'][0]['steps'][0]['sourceRefs'] = ['does-not-exist']
        with self.assertRaisesRegex(ValueError, '来源'):
            self.compile(data)

    def test_public_rule_cannot_be_grounded_in_assistant_claim(self):
        data = answer(self.payload)
        data['methods'][0]['conditions'] = [{'dimension': 'state', 'value': 'pending',
                                            'basis': 'PUBLIC_RULE', 'sourceRefs': ['e3']}]
        condition = self.compile(data)['methods'][0]['conditions'][0]
        self.assertEqual(condition['basis'], 'HYPOTHESIS')
        self.assertEqual(condition['proposedBasis'], 'PUBLIC_RULE')

    def test_structured_field_comparison_is_recomputed(self):
        self.experience['events'][-1]['result'] = {'color': 'green'}
        self.experience['events'][0]['content'] = 'green'
        self.payload = local.prepare(self.traces, self.experience)
        data = answer(self.payload)
        step = data['methods'][0]['steps'][0]
        step.update(kind='ACTION', sourceRefs=['e4.c1'], effectDimensions=['color'])
        step['checks'] = [{'dimension': 'color', 'criterion': '颜色满足用户要求', 'evidenceRefs': [],
                           'comparison': {'op': 'eq', 'actual': {'ref': 'e5', 'path': ['data', 'color']},
                                          'expected': {'ref': 'e1', 'path': ['text']}}}]
        result = self.compile(data)['methods'][0]['steps'][0]
        self.assertEqual(result['checks'][0]['status'], 'SATISFIED')
        self.assertIn('SOURCE_FIELD_COMPARISON', result['checks'][0]['verification'])

    def test_context_and_support_identity_are_host_owned(self):
        data = answer(self.payload)
        data['methods'][0].update(contextKey='fake', supportKey='fake')
        method = self.compile(data)['methods'][0]
        self.assertNotEqual(method['contextKey'], 'fake')
        self.assertEqual(method['traceId'], 't-original')
        self.assertNotEqual(method['supportKey'], 'fake')
        self.assertTrue(method['id'].startswith('method-'))
        self.assertNotEqual(method['id'], 'm1')

    def test_model_seed_change_does_not_inflate_independent_support(self):
        first = self.compile()['methods'][0]
        self.traces[0]['id'] = 'different-model-seed'
        self.traces[0]['taskId'] = 'different-model-seed'
        self.payload = local.prepare(self.traces, self.experience)
        second = self.compile()['methods'][0]
        self.assertEqual(first['supportKey'], second['supportKey'])

    def test_assistant_text_comparison_cannot_prove_tool_effect(self):
        data = answer(self.payload)
        step = data['methods'][0]['steps'][0]
        step.update(kind='ACTION', sourceRefs=['e4.c1', 'e2'], effectDimensions=['order_created'])
        step['checks'] = [{'dimension': 'order_created', 'criterion': '订单创建', 'evidenceRefs': [],
                           'comparison': {'op': 'eq', 'actual': {'ref': 'e2', 'path': ['text']},
                                          'expected': {'ref': 'e1', 'path': ['text']}}}]
        check = self.compile(data)['methods'][0]['steps'][0]['checks'][0]
        self.assertEqual(check['status'], 'UNKNOWN')
        self.assertIn('TEXT_CANNOT_PROVE_ACTION_EFFECT', check['unknownReason'])

    def test_numbering_criterion_cannot_certify_model_renamed_format_dimension(self):
        data = answer(self.payload)
        step = data['methods'][0]['steps'][0]
        step['effectDimensions'] = ['format']
        step['checks'][0]['dimension'] = 'format'
        output = self.compile(data)['methods'][0]['steps'][0]
        self.assertEqual(output['checks'][0]['status'], 'SATISFIED')
        self.assertEqual(output['checks'][0]['proposedDimension'], 'format')
        self.assertTrue(output['checks'][0]['dimension'].startswith('criterion:'))
        self.assertEqual(output['verdict'], 'UNKNOWN')

    def test_transport_success_does_not_overrule_explicit_tool_error(self):
        for content in ({'error': 'not allowed'}, '{"error":"not allowed"}', 'Error: not allowed'):
            self.experience['events'][-1].update(result=content, error=False, executionStatus='SUCCEEDED')
            self.payload = local.prepare(self.traces, self.experience)
            data = answer(self.payload)
            data['methods'][0]['steps'][0].update(kind='ACTION', sourceRefs=['e4.c1'], checks=[])
            step = self.compile(data)['methods'][0]['steps'][0]
            self.assertEqual(step['verdict'], 'VIOLATED')
            check = step['checks'][0]
            self.assertEqual(check['dimension'], 'tool_reported_result')
            self.assertEqual(check['reportedEvidence'][0]['transportStatus'], 'SUCCESS')
            self.assertEqual(check['reportedEvidence'][0]['reportedResultStatus'], 'FAILURE')

    def test_known_claim_cannot_bypass_recovery_using_raw_message_alias(self):
        self.traces[0]['typedSources'].append({'id': 'claim1', 'kind': 'ASSISTANT_CLAIM',
                                             'text': '已创建订单。', 'ref': {'sourceId': 'a2', 'session': 'session1'},
                                             'metadata': {'observationKind': 'EXECUTION_CLAIM'}})
        self.payload = local.prepare(self.traces, self.experience)
        data = answer(self.payload)
        data['methods'][0]['steps'][0].update(sourceRefs=['e3'], kind='VISIBLE_OUTPUT', checks=[])
        step = self.compile(data)['methods'][0]['steps'][0]
        self.assertEqual(step['kind'], 'CLAIM')
        self.assertEqual(step['verdict'], 'UNKNOWN')

    def test_mixed_message_keeps_visible_local_span_separate_from_claim(self):
        self.experience['events'][1]['content'] = '|2.1|意见|\n已创建订单。'
        self.traces[0]['typedSources'].append({'id': 'claim1', 'kind': 'ASSISTANT_CLAIM',
                                             'text': '已创建订单。', 'ref': {'sourceId': 'a1', 'session': 'session1'},
                                             'metadata': {'observationKind': 'EXECUTION_CLAIM'}})
        self.payload = local.prepare(self.traces, self.experience)
        data = answer(self.payload)
        data['methods'][0]['steps'][0]['sourceSpans'] = [{'sourceRef': 'e2', 'quote': '|2.1|意见|'}]
        step = self.compile(data)['methods'][0]['steps'][0]
        self.assertEqual(step['kind'], 'VISIBLE_OUTPUT')
        self.assertEqual(step['sourceSpans'][0]['sourceRef'], self.ref('e2'))
        data['methods'][0]['steps'][0].pop('sourceSpans')
        self.assertEqual(self.compile(data)['methods'][0]['steps'][0]['kind'], 'CLAIM')

    def test_all_used_and_unused_sources_have_namespaced_catalog_rows(self):
        result = self.compile()
        catalog = {s['id']: s for s in result['sourceCatalog']}
        used = result['methods'][0]['sourceRefs']
        self.assertTrue(all(ref in catalog for ref in used))
        self.assertTrue(all(item['sourceRef'] in catalog for item in result['unassigned']))
        self.assertEqual(catalog[self.ref('e2')]['rawAlias'], 'e2')
        self.assertEqual(catalog[self.ref('e2')]['originalIds'], ['a1'])

    def test_attempt_failure_cannot_be_distributed_to_its_local_steps(self):
        self.traces[0]['attempts'] = [{'id': 'attempt1', 'evidenceRefs': ['a1', 'a2']}]
        self.experience['evaluations'].append({'id': 'attempt-score', 'source': 'fixture-check',
                                              'scope': 'ATTEMPT', 'targetIds': ['attempt1'],
                                              'criterion': '整次尝试失败', 'status': 'FAILURE',
                                              'verified': True, 'verificationBasis': 'external score'})
        self.payload = local.prepare(self.traces, self.experience)
        data = answer(self.payload)
        step = data['methods'][0]['steps'][0]
        step['checks'] = [{'criterion': '整次尝试失败', 'dimension': 'format', 'evidenceRefs': ['v3']}]
        check = self.compile(data)['methods'][0]['steps'][0]['checks'][0]
        self.assertEqual(check['status'], 'UNKNOWN')
        self.assertIn('ATTEMPT_RESULT_NOT_LOCAL', check['unknownReason'])

    def test_source_kind_tool_call_alias_is_normalized_with_actual_call(self):
        data = answer(self.payload)
        data['methods'][0]['steps'][0].update(kind='TOOL_CALL', sourceRefs=['e4.c1'], checks=[])
        step = self.compile(data)['methods'][0]['steps'][0]
        self.assertEqual(step['kind'], 'ACTION')
        self.assertEqual(step['proposedKind'], 'TOOL_CALL')
        self.assertIn('SOURCE_KIND_TOOL_CALL_NORMALIZED_TO_ACTION', step['normalizationNotes'])
        data['methods'][0]['steps'][0]['sourceRefs'] = ['e3']
        self.assertEqual(self.compile(data)['methods'][0]['steps'][0]['kind'], 'CLAIM')

    def test_model_transport_is_lossless_and_keeps_source_identity(self):
        import json
        text = '保留完整工具返回及末尾错误。' * 300
        payload = deepcopy(self.payload)
        payload['additional'] = [
            {'text': text, 'data': {'result': text, 'error': 'Error: forbidden'}},
            {'text': text, 'data': {'result': text, 'error': 'Error: forbidden'}},
        ]
        view = local.model_input(payload)
        self.assertEqual(local.expand_model_input(view), payload)
        self.assertEqual(view['sourceHash'], payload['sourceHash'])
        self.assertLess(len(json.dumps(view)), len(json.dumps(payload)))
        self.assertEqual(json.dumps(view, ensure_ascii=False).count(text), 1)

    def test_model_transport_preserves_literal_reserved_keys_and_json_strings(self):
        import json
        payload = deepcopy(self.payload)
        long_text = '完整来源' * 100
        body = {'result': long_text, 'error': 'Error: not allowed'}
        payload['additional'] = [body, json.dumps(body, ensure_ascii=False, sort_keys=True),
                                 {'$localText': 'not-a-reference'}, {'$localRecord': 'not-a-reference'},
                                 {'$localJSON': {'unaltered': True}}]
        view = local.model_input(payload)
        self.assertEqual(local.expand_model_input(view), payload)

    def test_action_coverage_counts_raw_and_recovered_views_as_one_real_call(self):
        self.traces[0]['typedSources'].append({
            'id': 'call-source', 'kind': 'TOOL_CALL', 'text': 'recorded call',
            'ref': {'sourceId': 'a3', 'session': 'session1'},
            'metadata': {'callId': 'call1', 'name': 'modify_order', 'actor': 'assistant',
                         'arguments': {'order_id': 'one'}}})
        self.payload = local.prepare(self.traces, self.experience)
        data = answer(self.payload)
        data['methods'][0]['steps'][0].update(kind='ACTION', sourceRefs=['r1'], checks=[])
        result = self.compile(data)
        self.assertEqual(result['coverage']['actualCallCount'], 1)
        self.assertEqual(result['coverage']['usedActualCallCount'], 1)
        self.assertEqual(result['coverage']['unassignedActualActions'], 0)
        self.assertEqual(result['coverage']['unassignedActualActionAliases'], 1)
        unused = next(s for s in result['unassigned'] if s['sourceRef'] == self.ref('e4.c1'))
        self.assertEqual(unused['reasonCode'], 'DUPLICATE_SOURCE_VIEW')


if __name__ == '__main__':
    unittest.main()
