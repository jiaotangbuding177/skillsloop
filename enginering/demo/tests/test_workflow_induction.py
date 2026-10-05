"""Structural induction tests; authored cases are not an effectiveness benchmark."""
from copy import deepcopy
import unittest

from skilldemo.workflow_induction import induce


def method(mid, *, state='pending', verdict='SATISFIED', support=None):
    condition = {'dimension': 'order.status', 'value': state,
                 'basis': 'OBSERVED', 'sourceRefs': [mid + ':state']}
    steps = []
    for i, (operator, effect) in enumerate((('get_order', 'order.visible'),
                                           ('change_address', 'address.updated'))):
        sid = mid + ':s' + str(i)
        status = verdict if i else 'SATISFIED'
        steps.append({'id': sid, 'operator': operator, 'action': operator,
                      'actor': 'agent', 'objectRole': 'target_order', 'effect': effect,
                      'inputRoles': ['target_order'], 'outputRoles': [effect],
                      'dependsOn': [steps[-1]['id']] if steps else [],
                      'sourceRefs': [mid + ':event' + str(i)], 'kind': 'ACTION',
                      'conditions': [], 'checks': [
                          {'criterion': effect, 'dimension': effect, 'status': status,
                           'supportRefs': [mid + ':check'] if status == 'SATISFIED' else [],
                           'counterRefs': [mid + ':error'] if status == 'VIOLATED' else [],
                           'unknownReason': 'missing receipt' if status == 'UNKNOWN' else '',
                           'verification': 'VISIBLE_EVIDENCE'}], 'verdict': status})
    return {'id': mid, 'traceId': 'trace-' + mid, 'goal': '调整目标订单地址',
            'goalKey': 'order.change_address', 'objectType': 'order',
            'outputType': 'order.address', 'contextKey': 'retail-policy-v1',
            'supportKey': support or 'task-' + mid, 'steps': steps,
            'conditions': [condition], 'sourceRefs': [mid + ':source'],
            'unknowns': ['result missing'] if verdict == 'UNKNOWN' else []}


class WorkflowInductionTests(unittest.TestCase):
    def test_two_distinct_instances_actually_merge_with_positive_gain(self):
        rows = [method('a'), method('b')]
        result = induce(rows)
        self.assertEqual(len(result['workflows']), 1)
        workflow = result['workflows'][0]
        self.assertEqual(workflow['memberIds'], ['a', 'b'])
        self.assertEqual(len(workflow['coreSteps']), 2)
        self.assertEqual(workflow['supportCount'], 2)
        self.assertGreater(workflow['compression']['savedUnits'], 0)
        self.assertEqual(len(result['mergeLedger']), 1)
        self.assertEqual(workflow['members'], rows)

    def test_failure_and_unknown_keep_identity_and_evidence_in_family(self):
        rows = [method('a'), method('b', state='shipped', verdict='VIOLATED'),
                method('c', verdict='UNKNOWN')]
        workflow = induce(rows)['workflows'][0]
        self.assertEqual(len(workflow['variants']), 3)
        self.assertEqual({v['methodId']: v['status'] for v in workflow['variants']},
                         {'a': 'SATISFIED', 'b': 'VIOLATED', 'c': 'UNKNOWN'})
        self.assertTrue(any(w['type'] == 'LOCAL_VIOLATION' for w in workflow['warnings']))
        self.assertEqual(workflow['members'][1]['steps'], rows[1]['steps'])
        self.assertEqual(workflow['variants'][2]['unknowns'], ['result missing'])
        self.assertFalse(workflow['conflicts'])  # Different conditions remain separate.

    def test_same_condition_counterexample_limits_local_rule(self):
        workflow = induce([method('a'), method('b', verdict='VIOLATED')])['workflows'][0]
        self.assertEqual(len(workflow['conflicts']), 1)
        conflict = workflow['conflicts'][0]
        self.assertEqual(conflict['dimension'], 'address.updated')
        self.assertEqual(conflict['status'], 'CONFLICT')
        self.assertEqual(set(conflict['methodIds']), {'a', 'b'})
        self.assertIn('b:error', conflict['counterRefs'])
        self.assertIn('b:error', workflow['sourceRefs'])
        self.assertEqual(workflow['variants'][0]['status'], 'SATISFIED')
        self.assertEqual(workflow['variants'][0]['steps'][1]['effectiveVerdict'], 'CONFLICT')
        self.assertEqual(workflow['variants'][0]['steps'][0]['effectiveVerdict'], 'SATISFIED')
        self.assertEqual(workflow['variants'][0]['steps'][1]['verdict'], 'SATISFIED')
        self.assertEqual(workflow['variants'][0]['steps'][1]['blockedDimensions'], ['address.updated'])
        self.assertEqual(workflow['members'][0]['steps'][1]['verdict'], 'SATISFIED')
        self.assertFalse(workflow['composition']['allowUnobservedCombinations'])

    def test_conditional_extensions_allow_members_without_pairwise_isomorphism(self):
        a, b = method('a'), method('b', state='requires_confirmation')
        extra = deepcopy(b['steps'][0]); extra.update(id='b:confirm', operator='confirm_address',
                                                     action='confirm', effect='address.confirmed',
                                                     outputRoles=['address.confirmed'], dependsOn=['b:s0'])
        b['steps'].insert(1, extra)
        b['steps'][-1]['dependsOn'] = ['b:confirm']
        workflow = induce([a, b])['workflows'][0]
        self.assertEqual(len(workflow['memberIds']), 2)
        self.assertEqual(len(workflow['coreSteps']), 2)
        self.assertEqual(len(workflow['variants'][1]['steps']), 3)
        self.assertEqual(workflow['variants'][1]['conditions']['allOf'], b['conditions'])
        self.assertIsNone(workflow['variants'][1]['stepMapping'][1]['workflowStepId'])

    def test_dependency_reversal_prevents_merge(self):
        a, b = method('a'), method('b')
        b['steps'][0]['dependsOn'] = ['b:s1']; b['steps'][1]['dependsOn'] = []
        self.assertEqual(len(induce([a, b])['workflows']), 2)

    def test_object_role_or_actor_conflict_is_not_synonymized(self):
        a, b = method('a'), method('b')
        b['steps'][-1]['objectRole'] = 'account_default_address'
        self.assertEqual(len(induce([a, b])['workflows']), 2)
        b = method('b'); b['steps'][-1]['actor'] = 'user'
        self.assertEqual(len(induce([a, b])['workflows']), 2)

    def test_bridge_similarity_is_not_transitive_clustering(self):
        a, b, c = method('a'), method('b'), method('c')
        a['steps'] = [a['steps'][0]]
        c['steps'] = [c['steps'][1]]; c['steps'][0]['dependsOn'] = []
        result = induce([a, b, c])
        self.assertEqual(len(result['workflows']), 2)
        self.assertEqual(sum(len(w['memberIds']) for w in result['workflows']), 3)

    def test_retries_do_not_increase_independent_support(self):
        w = induce([method('a', support='one'), method('b', support='one')])['workflows'][0]
        self.assertEqual(w['supportCount'], 1)
        self.assertEqual(len(w['memberIds']), 2)

    def test_claim_and_plan_never_become_core_actions(self):
        a, b = method('a'), method('b')
        for row in (a, b):
            row['steps'][1]['kind'] = 'CLAIM'
            row['steps'][1]['verdict'] = 'UNKNOWN'
        w = induce([a, b])['workflows'][0]
        self.assertEqual([s['operator'] for s in w['coreSteps']], ['get_order'])
        self.assertTrue(any(warn['type'] == 'UNEXECUTED_STATEMENT' for warn in w['warnings']))
        self.assertTrue(all(v['status'] == 'UNKNOWN' for v in w['variants']))

    def test_only_generic_shared_chatter_is_not_a_workflow_core(self):
        a, b = method('a'), method('b')
        for row in (a, b):
            row['steps'] = row['steps'][:1]
            row['steps'][0]['operator'] = 'greet'
        self.assertEqual(len(induce([a, b])['workflows']), 2)

    def test_context_version_and_output_effect_are_hard_boundaries(self):
        a, b = method('a'), method('b'); b['contextKey'] = 'retail-policy-v2'
        self.assertEqual(len(induce([a, b])['workflows']), 2)
        b = method('b'); b['outputType'] = 'account.address'
        self.assertEqual(len(induce([a, b])['workflows']), 2)

    def test_input_order_and_step_list_order_do_not_change_output(self):
        rows = [method('a'), method('b'), method('c', verdict='UNKNOWN')]
        self.assertEqual(induce(rows), induce(list(reversed(rows))))
        # Source steps retain their original order as evidence; the actual graph
        # and grouping do not derive dependencies from array order.
        reversed_steps = deepcopy(rows); reversed_steps[1]['steps'].reverse()
        self.assertEqual(induce(rows)['workflows'][0]['memberIds'],
                         induce(reversed_steps)['workflows'][0]['memberIds'])

    def test_cycle_dangling_dependency_and_duplicate_id_are_rejected(self):
        a = method('a'); a['steps'][0]['dependsOn'] = ['a:s1']
        with self.assertRaisesRegex(ValueError, '循环'): induce([a])
        a = method('a'); a['steps'][0]['dependsOn'] = ['missing']
        with self.assertRaisesRegex(ValueError, '依赖'): induce([a])
        with self.assertRaisesRegex(ValueError, '重复'): induce([method('a'), method('a')])

    def test_does_not_mutate_input_and_empty_pool_is_valid(self):
        rows = [method('a'), method('b')]; before = deepcopy(rows)
        induce(rows)
        self.assertEqual(rows, before)
        self.assertEqual(induce([])['workflows'], [])

    def test_repeated_parallel_actions_are_not_silently_collapsed(self):
        a, b = method('a'), method('b')
        for row in (a, b):
            duplicate = deepcopy(row['steps'][0]); duplicate['id'] += ':again'
            duplicate['sourceRefs'] = [row['id'] + ':another-real-call']
            row['steps'].append(duplicate)
        result = induce([a, b])
        self.assertEqual(len(result['workflows']), 1)
        w = result['workflows'][0]
        self.assertEqual([s['operator'] for s in w['coreSteps']], ['change_address'])
        self.assertTrue(all(len(v['steps']) == 3 for v in w['variants']))
        self.assertTrue(all(sum(s['workflowStepId'] is None for s in v['stepMapping']) == 2
                            for v in w['variants']))

    def test_all_conjunctive_conditions_and_uncertain_bases_survive(self):
        a, b = method('a'), method('b', state='shipped')
        a['conditions'].append({'dimension': 'permission', 'value': 'approved',
                                'basis': 'PUBLIC_RULE', 'sourceRefs': ['policy:p']})
        b['conditions'].append({'dimension': 'account.tier', 'value': 'vip',
                                'basis': 'HYPOTHESIS', 'sourceRefs': ['b:guess']})
        w = induce([a, b])['workflows'][0]
        self.assertEqual(w['variants'][0]['conditions']['allOf'], a['conditions'])
        self.assertEqual(w['variants'][1]['conditions']['allOf'], b['conditions'])
        self.assertFalse(w['composition']['allowUnobservedCombinations'])
        self.assertIn('policy:p', w['sourceRefs'])
        self.assertIn('b:guess', w['sourceRefs'])


if __name__ == '__main__':
    unittest.main()
