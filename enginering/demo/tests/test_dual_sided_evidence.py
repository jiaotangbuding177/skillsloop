import unittest
import tempfile
from skilldemo import evidence, intake


class DualSidedEvidenceTests(unittest.TestCase):
    def assemble(self, rows):
        events = [intake.event('alice', row, 'generation', i)
                  for i, row in enumerate(rows, 1)]
        return intake.assemble(events)

    def row(self, key, role, content='', **fields):
        return dict(id=key, sessionId='s', role=role, content=content, **fields)

    def call(self, key, name='toggle_roaming', **fields):
        return dict(id=key, name=name, arguments={}, **fields)

    def test_empty_user_and_assistant_calls_survive_with_distinct_actors(self):
        pairs, unknown = self.assemble([
            self.row('u', 'user', runId='run1', toolCalls=[
                self.call('cu', objectIds=['device-1'])]),
            self.row('ru', 'tool', 'Device roaming is ON', runId='run1',
                     callId='cu', executionStatus='SUCCEEDED'),
            self.row('a', 'assistant', runId='run1', responseTo='u', toolCalls=[
                self.call('ca', 'enable_roaming', objectIds=['line-1'])]),
            self.row('ra', 'tool', 'Line roaming enabled', runId='run1',
                     callId='ca', executionStatus='SUCCEEDED')])
        self.assertEqual(unknown, [])
        pair = pairs[0]
        self.assertEqual(pair['user'], '')
        self.assertEqual(pair['contentStatus'], 'ACTION_ONLY')
        self.assertTrue(pair['actionOnly'])
        self.assertTrue(pair['userEvidenceAbsent'])
        rows = evidence.catalog(pairs)
        calls = {r['metadata']['callId']: r for r in rows if r['kind'] == 'TOOL_CALL'}
        results = {r['metadata']['callId']: r for r in rows if r['kind'] == 'TOOL_RESULT'}
        self.assertEqual(set(calls), {'cu', 'ca'})
        self.assertEqual(calls['cu']['metadata']['actor'], 'user')
        self.assertEqual(calls['ca']['metadata']['actor'], 'assistant')
        self.assertEqual(results['cu']['metadata']['actor'], 'tool')
        self.assertEqual(results['cu']['metadata']['requestor'], 'user')
        self.assertEqual(results['ca']['metadata']['requestor'], 'assistant')
        self.assertEqual(calls['cu']['metadata']['objectIds'], ['device-1'])
        self.assertEqual(calls['ca']['metadata']['objectIds'], ['line-1'])
        self.assertEqual(calls['cu']['ref']['sourceMessageId'], 'u')
        self.assertEqual(calls['cu']['ref']['originPairId'], pair['id'])
        self.assertEqual(calls['cu']['ref']['runId'], 'run1')
        self.assertTrue(calls['cu']['ref']['actionOnly'])
        self.assertTrue(all(r['metadata']['outcomeType'] == 'TECHNICAL' for r in rows))

    def test_same_call_id_in_distinct_runs_keeps_exact_receipt_scope(self):
        pairs, unknown = self.assemble([
            self.row('u1', 'user', 'First task', runId='r1', toolCalls=[self.call('c')]),
            self.row('u2', 'user', 'Second task', runId='r2', toolCalls=[self.call('c')]),
            self.row('t2', 'tool', 'second result', runId='r2', callId='c'),
            self.row('t1', 'tool', 'first result', runId='r1', callId='c')])
        self.assertEqual(unknown, [])
        for pair in pairs:
            result = next(r for r in evidence.catalog([pair]) if r['kind'] == 'TOOL_RESULT')
            self.assertEqual(result['ref']['sourceId'], 't'+pair['sourceUserMessageId'][-1])
            self.assertEqual(result['metadata']['requestor'], 'user')

    def test_missing_run_does_not_choose_between_reused_call_ids(self):
        pairs, unknown = self.assemble([
            self.row('u1', 'user', 'First task', runId='r1', toolCalls=[self.call('c')]),
            self.row('u2', 'user', 'Second task', runId='r2', toolCalls=[self.call('c')]),
            self.row('t', 'tool', 'unassigned result', callId='c')])
        self.assertEqual(len(unknown), 1)
        self.assertEqual(unknown[0]['sourceId'], 't')
        self.assertTrue(all(not any(t.get('sourceId') == 't' for t in p['toolEvents']) for p in pairs))

    def test_duplicate_calls_in_one_run_remain_separate_and_result_unresolved(self):
        pairs, unknown = self.assemble([
            self.row('u', 'user', 'Task', runId='r', toolCalls=[self.call('c')]),
            self.row('a', 'assistant', 'Guidance', runId='r', toolCalls=[self.call('c', 'enable_roaming')]),
            self.row('t', 'tool', 'ambiguous result', runId='r', callId='c', toolName='toggle_roaming')])
        self.assertEqual(len(unknown), 1)
        calls = [r for r in evidence.catalog(pairs) if r['kind'] == 'TOOL_CALL']
        self.assertEqual(len(calls), 2)
        self.assertEqual(len({r['id'] for r in calls}), 2)

    def test_unlinked_result_never_invents_call_or_assistant_requestor(self):
        pairs, _ = self.assemble([
            self.row('u', 'user', 'Check status'),
            self.row('a', 'assistant', 'Status pending'),
            self.row('t', 'tool', 'Error', responseTo='u', name='check_status',
                     executionStatus='FAILED')])
        result = next(r for r in evidence.catalog(pairs) if r['kind'] == 'TOOL_RESULT')
        self.assertIsNone(result['metadata']['callId'])
        self.assertEqual(result['metadata']['requestor'], 'UNKNOWN')
        self.assertEqual(result['metadata']['actor'], 'tool')
        self.assertFalse(result['metadata']['verified'])

    def test_source_requestor_and_long_result_are_preserved_without_gold_inference(self):
        body = 'actual user result\n' * 500
        pairs, _ = self.assemble([
            self.row('u', 'user', 'Task', hidden_goal='gold goal', taskId='gold-task'),
            self.row('a', 'assistant', 'Guidance'),
            self.row('t', 'tool', body, responseTo='u', callId='c', requestor='user',
                     objectIds=['phone'], executionStatus='SUCCEEDED')])
        result = next(r for r in evidence.catalog(pairs) if r['kind'] == 'TOOL_RESULT')
        self.assertEqual(result['metadata']['result'], body)
        self.assertEqual(result['metadata']['requestor'], 'user')
        self.assertEqual(result['metadata']['requestorBasis'], 'SOURCE_RECORDED')
        self.assertEqual(result['metadata']['objectIds'], ['phone'])
        self.assertNotIn('gold-task', str(pairs))
        self.assertNotIn('gold goal', str(pairs))

    def test_missing_user_body_is_not_called_action_only(self):
        pairs, _ = self.assemble([
            self.row('u', 'user', None, toolCalls=[self.call('c')]),
            self.row('a', 'assistant', 'Guidance')])
        self.assertEqual(pairs[0]['contentStatus'], 'MISSING_CONTENT')
        self.assertFalse(pairs[0]['actionOnly'])
        self.assertTrue(pairs[0]['userEvidenceAbsent'])
        self.assertEqual(len([r for r in evidence.catalog(pairs) if r['kind'] == 'TOOL_CALL']), 1)

    def test_standalone_user_call_event_preserves_actor_and_origin(self):
        pairs, _ = self.assemble([
            self.row('u', 'user', eventType='CALL', callId='c', toolName='toggle_roaming',
                     arguments={}, runId='r')])
        call = next(r for r in evidence.catalog(pairs) if r['kind'] == 'TOOL_CALL')
        self.assertEqual(call['metadata']['actor'], 'user')
        self.assertEqual(call['metadata']['requestor'], 'user')
        self.assertEqual(call['metadata']['sourceOrder'], 1)
        self.assertEqual(call['ref']['sourceMessageId'], 'u')
        self.assertTrue(call['ref']['actionOnly'])

    def test_invalid_embedded_call_is_rejected_instead_of_dropped(self):
        with self.assertRaises(ValueError):
            self.assemble([self.row('u', 'user', toolCalls=[{'name':'toggle_roaming','arguments':{}}])])

    def test_conflicting_tool_name_cannot_establish_requestor_from_call_id(self):
        pairs, unknown = self.assemble([
            self.row('u', 'user', 'Task', runId='r', toolCalls=[self.call('c', 'toggle_roaming')]),
            self.row('t', 'tool', 'Different action result', runId='r', callId='c',
                     toolName='cancel_order')])
        self.assertEqual(len(unknown), 1)
        self.assertEqual(unknown[0]['sourceId'], 't')
        self.assertEqual(len([r for r in evidence.catalog(pairs) if r['kind'] == 'TOOL_RESULT']), 0)

    def test_unknown_orphan_receipt_keeps_no_origin_pair_or_action_actor(self):
        pairs, _ = self.assemble([self.row('u', 'user', 'Task'),
                                  self.row('a', 'assistant', 'Guidance')])
        pairs[0]['unassignedToolEvents'] = [
            intake.event('alice', self.row('t', 'tool', 'orphan', callId='c'), 'generation', 3)]
        result = next(r for r in evidence.catalog(pairs) if r['kind'] == 'TOOL_RESULT')
        self.assertIsNone(result['ref']['pairId'])
        self.assertIsNone(result['ref']['originPairId'])
        self.assertFalse(result['ref']['actionOnly'])
        self.assertEqual(result['metadata']['requestor'], 'UNKNOWN')

    def test_orphan_from_other_session_does_not_inherit_first_pair_session(self):
        pairs, _ = self.assemble([self.row('u', 'user', 'Task'),
                                  self.row('a', 'assistant', 'Guidance')])
        orphan = self.row('t', 'tool', 'other session receipt', callId='c')
        orphan['sessionId'] = 'other-session'
        pairs[0]['unassignedToolEvents'] = [intake.event('alice', orphan, 'generation', 3)]
        result = next(r for r in evidence.catalog(pairs) if r['kind'] == 'TOOL_RESULT')
        self.assertEqual(result['ref']['session'], 'other-session')
        self.assertIsNone(result['ref']['originPairId'])
        del pairs[0]['unassignedToolEvents'][0]['session']
        result = next(r for r in evidence.catalog(pairs) if r['kind'] == 'TOOL_RESULT')
        self.assertIsNone(result['ref']['session'])

    def test_sparse_evaluation_result_rejects_nested_gold_and_nonfinite_numbers(self):
        base = dict(id='v', source='public-checker', scope='TASK', targetIds=['u'],
                    criterion='Target state', outcomeType='BUSINESS')
        for bad in ({'reward_info': {'actions':[{'name':'gold-action'}]}}, [], [1], float('inf'), float('nan')):
            with self.subTest(result=bad), self.assertRaises(ValueError):
                evidence.normalize_evaluations([{**base, 'result':bad}])
        for good in (None, 'FAILURE', True, False, 0, 1, 0.5):
            with self.subTest(result=good):
                self.assertEqual(evidence.normalize_evaluations([{**base, 'result':good}])[0]['result'], good)

    def test_context_and_evaluation_source_are_flat_public_provenance(self):
        provenance = dict(kind='PUBLIC_CHECKER', file='checks.jsonl', line=4, path='public/checks.jsonl')
        context = dict(id='c', kind='POLICY', text='Public policy mentions gold and hidden in prose.', source=provenance)
        evaluation = dict(id='v', scope='TASK', targetIds=['u'], criterion='Public check', result='FAILURE', source=provenance)
        self.assertEqual(evidence.normalize_context([context])[0]['source'], provenance)
        self.assertEqual(evidence.normalize_evaluations([evaluation])[0]['source'], provenance)
        bad_sources = [dict(kind='PUBLIC_CHECKER', actions=[{'name':'gold-action'}]),
                       dict(kind='PUBLIC_CHECKER', file={'actions':[]}),
                       dict(kind='sourceGold'), dict(kind='hidden'), dict(id='goldAnswer'),
                       {'sourceGold':True}, 'sourceGold', 'hidden', 'goldAnswer']
        for source in bad_sources:
            with self.subTest(source=source):
                with self.assertRaises(ValueError): evidence.normalize_context([{**context, 'source':source}])
                with self.assertRaises(ValueError): evidence.normalize_evaluations([{**evaluation, 'source':source}])

    def test_legacy_bundled_receipt_does_not_default_to_assistant(self):
        pair = dict(id='p', session='s', sourceUserMessageId='u', toolEvents=[
            dict(id='legacy', name='cancel_order', arguments={'id':'A'}, result='done')])
        rows = evidence.catalog([pair])
        self.assertEqual({r['kind'] for r in rows}, {'TOOL_CALL', 'TOOL_RESULT'})
        self.assertTrue(all(r['metadata']['actor'] == 'UNKNOWN' for r in rows))
        self.assertTrue(all(r['metadata']['requestor'] == 'UNKNOWN' for r in rows))

    def test_imported_action_only_pair_reaches_recovery_catalog_without_fabricated_text(self):
        from skilldemo.core import Loop
        from skilldemo.runtime import ReplayAgent
        from skilldemo import relational
        rows = [self.row('goal', 'user', 'Restore data', runId='r'),
                self.row('guide', 'assistant', 'Turn on device roaming', runId='r'),
                self.row('action', 'user', toolCalls=[self.call('c')], runId='r'),
                self.row('receipt', 'tool', 'Roaming ON', callId='c', runId='r')]
        with tempfile.TemporaryDirectory() as root:
            loop = Loop(root, ReplayAgent(), stage_pipeline=True)
            self.assertEqual(loop.import_events('alice', rows)['addedEvents'], 4)
            pairs = loop.snapshot('alice')['pairs']
            action_pair = next(p for p in pairs if p['sourceUserMessageId'] == 'action')
            self.assertEqual(action_pair['user'], '')
            self.assertEqual(action_pair['contentStatus'], 'ACTION_ONLY')
            payload, _ = relational.prepare(pairs)
            call = next(r for r in payload['evidence'] if r['kind'] == 'TOOL_CALL')
            self.assertEqual(call['ref']['originPairId'], action_pair['id'])
            self.assertTrue(call['ref']['actionOnly'])
            self.assertEqual(call['metadata']['actor'], 'user')
            self.assertEqual(call['metadata']['requestor'], 'user')


if __name__ == '__main__':
    unittest.main()
