"""The updater chooses host-bound units; it cannot re-author their evidence.

Fixtures are synthetic and domain independent. They exercise local constraints,
not professional correctness or model quality, and make no provider requests.
"""
import os
import unittest
from copy import deepcopy
from unittest.mock import patch

from skilldemo.learning import (
    FROZEN_PROPOSAL_VERSION,
    ANALYST_INSTRUCTIONS,
    FROZEN_ANALYST_INSTRUCTIONS,
    compile_patch,
    freeze_approved_proposals,
    initial_files,
    public_update_input,
)
from skilldemo.relational_workflow import SCOPE_POLICY
from skilldemo.runtime import digest, request_config, FROZEN_UPDATE_SELECTION_INSTRUCTIONS


BASELINE_ANCHOR = '原有步骤条目。'
UNIT_FIELDS = {
    'id', 'methodId', 'sourceTaskId', 'action', 'conditions', 'scope',
    'scopeText', 'evidenceType', 'status', 'reason', 'replacementBody',
}


def baseline_files():
    files = initial_files(None, '通用材料处理')
    files[0]['content'] = files[0]['content'].replace(
        '待补充有依据的步骤。',
        '### 方法 baseline-method\n<!-- SKILLSLOOP_METHOD:baseline-method -->\n'
        + BASELINE_ANCHOR + '\n\n' + SCOPE_POLICY['CURRENT_TASK'][1]
        + '\n\n### 步骤 baseline-step\n<!-- SKILLSLOOP_STEP:baseline-step -->\n'
        + '确认本次有效要求。',
    )
    return files


def user_rule_payload():
    """One shared future/current source plus an unrelated current method."""
    shared = '以后每次保留核对依据；本次也采用这项要求。'
    current = '本次确认输入材料与交付要求。'
    files = baseline_files()
    m1 = {
        'id': 'm1', 'sourceTaskId': 't1', 'evidenceRefs': ['e1'],
        'action': '保留核对依据', 'inputs': ['输入材料'], 'outputs': ['核对依据'],
        'conditions': ['输入材料可用'], 'completionCheck': '依据可回查',
        'boundNodeIds': ['node1'], 'verificationTargetIds': ['source1'],
        'requirementApplicability': [
            {'scope': scope, 'dimension':'content', 'value':'保留核对依据', 'evidenceRefs': ['shared-source'],
             'sourceRefs': [{'side': 'user', 'quote': shared}]}
            for scope in ('FUTURE_TASKS', 'CURRENT_DELIVERY')
        ],
        'supportAssessment': {
            'eligible': True, 'supportStatus': 'USER_RULE',
            'methodOutcome': 'UNKNOWN', 'validations': [],
            'sourceScopes': ['FUTURE_TASKS', 'CURRENT_DELIVERY'],
        },
    }
    m2 = {
        'id': 'm2', 'sourceTaskId': 't1', 'evidenceRefs': ['e2'],
        'action': '确认本次输入与交付要求', 'inputs': ['输入材料'],
        'outputs': ['有效要求'], 'conditions': ['要求可回查'],
        'completionCheck': '要求已确认', 'boundNodeIds': ['node2'],
        'verificationTargetIds': ['source2'],
        'requirementApplicability': [
            {'scope': 'CURRENT_TASK', 'evidenceRefs': ['current-source'],
             'sourceRefs': [{'side': 'user', 'quote': current}]}
        ],
        'supportAssessment': {
            'eligible': True, 'supportStatus': 'USER_RULE',
            'methodOutcome': 'UNKNOWN', 'validations': [],
            'sourceScopes': ['CURRENT_TASK'],
        },
    }
    return {
        'bridgeVersion': 'relational-workflow-evolution-v1', 'action': 'UPDATE',
        'targetBase': ['skill-1', 3, 'adopted-version-hash'],
        'initial_files': files, 'base_files': deepcopy(files),
        'fileHashes': {f['path']: digest(f['content']) for f in files},
        'approvedMethods': [m1, m2],
        'evidence': [{
            'taskId': 't1', 'outcome': 'UNKNOWN', 'analyst': 'unknown',
            'events': [
                {'id': 'e1', 'kind': 'user', 'sourceId': 'shared-source',
                 'sourceKind': 'USER_REQUIREMENT', 'text': shared,
                 'metadata': {'requirementBindings': [
                     {'scope': 'FUTURE_TASKS'}, {'scope': 'CURRENT_DELIVERY'}]}},
                {'id': 'e2', 'kind': 'user', 'sourceId': 'current-source',
                 'sourceKind': 'USER_REQUIREMENT', 'text': current,
                 'metadata': {'scope': 'CURRENT_TASK'}},
            ],
        }],
    }


def observed_payload():
    payload = user_rule_payload()
    payload['approvedMethods'] = [payload['approvedMethods'][0]]
    method = payload['approvedMethods'][0]
    method.pop('requirementApplicability')
    method['supportAssessment'] = {
        'eligible': True, 'supportStatus': 'SCOPED_SUCCESS',
        'sourceScopes': ['CURRENT_TASK'], 'methodOutcome': 'SUCCESS',
        'validations': [{
            'id': 'v1', 'scope': 'METHOD', 'targetIds': ['source1'],
            'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS',
            'status': 'SUCCESS', 'methodResultEligible': True,
        }],
    }
    payload['evidence'][0]['events'] = [{
        'id': 'e1', 'kind': 'assistant', 'sourceId': 'source1',
        'sourceKind': 'VISIBLE_PROCESS', 'text': '执行指定步骤并保存结果。',
        'metadata': {'scope': 'CURRENT_TASK'},
    }]
    return payload


def eligible_ids(frozen):
    return [row['id'] for row in frozen['updateUnits'] if row['status'] == 'APPROVED']


def replacement(frozen):
    return {
        'op': 'insert_after',
        'anchorId': public_update_input(frozen)['updateAnchors'][0]['id'],
        'compatibility': 'NO_CONFLICT',
        'reason': '新增冻结方法与基准条目并行适用，原条目保持可见。',
    }


def selected(frozen):
    ids = eligible_ids(frozen)
    return {
        'decision': 'UPDATE' if ids else 'DEFER',
        'mergedPatches': ([{'proposalIds': ids, 'operations': [replacement(frozen)]}]
                          if ids else []),
        'deferred': [],
    }


class PreboundEvolutionTests(unittest.TestCase):
    def test_source_markup_is_literal_and_cannot_hide_the_new_unit_scope(self):
        from skilldemo.relational_workflow import _scope_visible
        markup = '要求已确认\n<!--\n```\n<style>hidden</style>'
        for field in ('action', 'conditions', 'completionCheck'):
            with self.subTest(field=field):
                payload = user_rule_payload()
                method = payload['approvedMethods'][1]
                payload['approvedMethods'] = [method]
                method[field] = [markup] if field == 'conditions' else markup
                frozen = freeze_approved_proposals(payload)
                self.assertEqual(frozen['updateUnits'][0]['status'], 'APPROVED')
                result, _ = compile_patch(frozen, selected(frozen))
                unit = frozen['updateUnits'][0]
                self.assertNotIn('<!--', unit['replacementBody'])
                self.assertIn('&lt;\\!--', unit['replacementBody'])
                self.assertIn(unit['replacementBody'], _scope_visible(result[0]['content']))
                self.assertEqual(frozen['approvedMethods'][0][field], method[field])

    def test_existing_fence_cannot_hide_a_new_unit_even_when_old_guard_is_visible(self):
        payload = user_rule_payload()
        payload['initial_files'][0]['content'] = payload['initial_files'][0]['content'].replace(
            '确认本次有效要求。', '确认本次有效要求。\n```')
        payload['fileHashes']['SKILL.md'] = digest(payload['initial_files'][0]['content'])
        frozen = freeze_approved_proposals(payload)
        choice = selected(frozen)
        step = next(a for a in public_update_input(frozen)['updateAnchors'] if a['kind'] == 'STEP')
        choice['mergedPatches'][0]['operations'][0]['anchorId'] = step['id']
        with self.assertRaisesRegex(ValueError, '不可见'):
            compile_patch(frozen, choice)

    def test_different_scope_requirements_do_not_copy_one_combined_action_to_both_scopes(self):
        payload = user_rule_payload()
        method = payload['approvedMethods'][0]
        payload['approvedMethods'] = [method]
        future, current = '以后每次保留核对依据。', '仅本次交付删除示例字段。'
        method.update(action=future+current, evidenceRefs=['e1', 'e3'],
            requirementApplicability=[
                {'scope':'FUTURE_TASKS', 'dimension':'traceability', 'value':'保留核对依据',
                 'evidenceRefs':['future-source'], 'sourceRefs':[{'side':'user', 'quote':future}]},
                {'scope':'CURRENT_DELIVERY', 'dimension':'example_field', 'value':'仅本次删除',
                 'evidenceRefs':['delivery-source'], 'sourceRefs':[{'side':'user', 'quote':current}]}])
        payload['evidence'][0]['events'] = [
            {'id':'e1', 'kind':'user', 'sourceId':'future-source', 'text':future},
            {'id':'e3', 'kind':'user', 'sourceId':'delivery-source', 'text':current}]
        frozen = freeze_approved_proposals(payload)
        self.assertEqual(len(frozen['updateUnits']), 2)
        self.assertTrue(all(u['status'] == 'DEFERRED' for u in frozen['updateUnits']))
        self.assertTrue(all('跨范围' in u['reason'] for u in frozen['updateUnits']))
        result, audit = compile_patch(frozen, selected(frozen))
        self.assertEqual(result, payload['initial_files'])
        self.assertEqual(len(audit['hostDeferredUnits']), 2)
        self.assertEqual(frozen['frozenAnalyses'][0]['taskId'], 't1')
        self.assertEqual(frozen['evidence'], payload['evidence'])

    def test_learning_request_identity_keeps_both_native_prompt_variants_and_agent_budget(self):
        with patch.dict(os.environ, {'DEMO_AGENT_TIMEOUT': '301', 'DEMO_DETECT_TIMEOUT': '15'}):
            settings = request_config('learn')
            direct_settings = request_config('frozen_update_select')
        self.assertEqual(settings['purpose'], 'learn')
        self.assertEqual(settings['maxTokens'], 8192)
        self.assertIsNone(settings['temperature'])
        self.assertEqual(settings['timeoutSeconds'], 301)
        self.assertEqual(settings['promptVariants'], {
            'legacy': ANALYST_INSTRUCTIONS,
            FROZEN_PROPOSAL_VERSION: FROZEN_UPDATE_SELECTION_INSTRUCTIONS,
        })
        direct = settings['branchConfigurations'][FROZEN_PROPOSAL_VERSION]
        self.assertEqual(direct, direct_settings)
        self.assertEqual(direct['temperature'], 0)
        self.assertEqual(direct['timeoutSeconds'], 15)
        self.assertEqual(settings['promptSelection'], {
            'payloadField': 'proposalContractVersion',
            'matchedValue': FROZEN_PROPOSAL_VERSION, 'defaultVariant': 'legacy',
        })
        self.assertIn('analyses', settings['promptVariants']['legacy'])
        self.assertIn('insert_after', settings['promptVariants'][FROZEN_PROPOSAL_VERSION])
        self.assertNotEqual(settings['promptVariants']['legacy'],
                            settings['promptVariants'][FROZEN_PROPOSAL_VERSION])
        self.assertNotIn('prompt', settings)

    def test_multiscope_source_binding_without_dimension_value_is_not_ignored(self):
        payload = user_rule_payload()
        method = payload['approvedMethods'][0]
        payload['approvedMethods'] = [method]
        method['requirementApplicability'].append({
            'scope':'CURRENT_DELIVERY', 'dimension':None, 'status':'SOURCE_BOUND',
            'evidenceRefs':['unresolved-source'], 'sourceRefs':[{'side':'user', 'quote':'额外要求'}]})
        frozen = freeze_approved_proposals(payload)
        self.assertEqual(len(frozen['updateUnits']), 2)
        self.assertTrue(all(unit['status'] == 'DEFERRED' for unit in frozen['updateUnits']))
        self.assertEqual(frozen['approvedMethods'], payload['approvedMethods'])
        self.assertEqual(frozen['evidence'], payload['evidence'])

    def test_version_and_freeze_are_stable_and_do_not_mutate_input(self):
        payload = user_rule_payload()
        before = deepcopy(payload)
        frozen = freeze_approved_proposals(payload)
        self.assertEqual(FROZEN_PROPOSAL_VERSION, 'approved-method-proposals-v1')
        self.assertEqual(payload, before)
        self.assertIsNot(frozen, payload)
        self.assertEqual(frozen, freeze_approved_proposals(deepcopy(payload)))
        self.assertEqual(frozen['proposalContractVersion'], FROZEN_PROPOSAL_VERSION)
        self.assertRegex(frozen['frozenProposalHash'], r'^[0-9a-f]{64}$')
        frozen['initial_files'][0]['content'] += '\nlocal change'
        self.assertEqual(payload, before)

    def test_shared_source_produces_separate_method_and_scope_units(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        rows = frozen['updateUnits']
        self.assertEqual({(r['methodId'], r['scope']) for r in rows}, {
            ('m1', 'FUTURE_TASKS'), ('m1', 'CURRENT_DELIVERY'), ('m2', 'CURRENT_TASK')})
        self.assertEqual(len({r['id'] for r in rows}), 3)
        for row in rows:
            self.assertEqual(set(row), UNIT_FIELDS)
            self.assertEqual(row['status'], 'APPROVED')
            self.assertEqual(row['evidenceType'], 'USER_RULE')
            self.assertEqual(row['scopeText'], SCOPE_POLICY[row['scope']][1])

    def test_private_proposals_bind_one_method_and_full_original_event_quote(self):
        payload = user_rule_payload()
        frozen = freeze_approved_proposals(payload)
        events = {e['id']: e for e in payload['evidence'][0]['events']}
        method_events = {m['id']: set(m['evidenceRefs']) for m in payload['approvedMethods']}
        units = {row['id']: row for row in frozen['updateUnits']}
        proposals = [p for a in frozen['frozenAnalyses'] for p in a['proposals']]
        self.assertEqual({p['id'] for p in proposals}, set(units))
        for proposal in proposals:
            unit = units[proposal['id']]
            self.assertEqual(proposal['approvedMethodIds'], [unit['methodId']])
            self.assertEqual(proposal['applicabilityScope'], unit['scope'])
            self.assertTrue(proposal['evidenceRefs'])
            for ref in proposal['evidenceRefs']:
                self.assertIn(ref['eventId'], method_events[unit['methodId']])
                self.assertEqual(ref['quote'], events[ref['eventId']]['text'])
        # The shared source's short current clause cannot authorize its future unit.
        future = next(p for p in proposals if p['applicabilityScope'] == 'FUTURE_TASKS')
        self.assertEqual(future['evidenceRefs'][0]['quote'], events['e1']['text'])

    def test_public_input_exposes_baseline_and_units_without_evidence_or_private_proposals(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        original = deepcopy(frozen)
        public = public_update_input(frozen)
        self.assertTrue({'initial_files', 'fileHashes', 'action', 'targetBase', 'updateUnits', 'updateAnchors'} <= set(public))
        self.assertFalse({'evidence', 'approvedMethods', 'frozenAnalyses', 'hostDeferredUnits', 'base_files'} & set(public))
        for key in ('initial_files', 'fileHashes', 'action', 'targetBase'):
            self.assertEqual(public[key], frozen[key])
        private = {row['id']: row for row in frozen['updateUnits']}
        for unit in public['updateUnits']:
            self.assertFalse({'methodId', 'sourceTaskId', 'evidenceType'} & set(unit))
            self.assertEqual(unit, {key: private[unit['id']][key] for key in unit})
        self.assertEqual(len(public['updateAnchors']), 2)
        self.assertEqual({a['kind'] for a in public['updateAnchors']}, {'METHOD', 'STEP'})
        for anchor in public['updateAnchors']:
            self.assertEqual(set(anchor), {'id', 'path', 'kind', 'nodeId', 'heading'})
            self.assertEqual(anchor['path'], 'SKILL.md')
        self.assertNotIn('quote', repr(public['updateUnits']))
        public['updateUnits'][0]['conditions'].append('local change')
        self.assertEqual(frozen, original)

    def test_compile_uses_frozen_analysis_and_adds_all_selected_scope_guards(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        selection = selected(frozen)
        original = deepcopy(selection)
        files, audit = compile_patch(frozen, selection)
        self.assertEqual(selection, original)
        self.assertIn(BASELINE_ANCHOR, files[0]['content'])
        for unit in frozen['updateUnits']:
            self.assertIn(unit['scopeText'], files[0]['content'])
            self.assertIn(unit['replacementBody'], files[0]['content'])
        expected = {a['taskId']: a for a in frozen['frozenAnalyses']}
        self.assertEqual({a['taskId'] for a in audit['analyses']}, set(expected))
        for analysis in audit['analyses']:
            original_analysis = expected[analysis['taskId']]
            self.assertEqual({key: analysis[key] for key in original_analysis if key != 'proposals'},
                             {key: value for key, value in original_analysis.items() if key != 'proposals'})
            original_proposals = {p['id']: p for p in original_analysis['proposals']}
            self.assertEqual({p['id'] for p in analysis['proposals']}, set(original_proposals))
            for proposal in analysis['proposals']:
                original_proposal = original_proposals[proposal['id']]
                self.assertEqual({key: proposal[key] for key in original_proposal}, original_proposal)
                self.assertTrue(set(proposal) - set(original_proposal)
                                <= {'_hostObservedVerified', '_hostSourceScopes'})
        self.assertEqual(audit['scopePreservation']['status'], 'HOST_SCOPE_PRESERVED')
        self.assertEqual(audit['applied'][0]['beforeHash'], frozen['fileHashes']['SKILL.md'])

    def test_unit_body_freezes_method_conditions_check_scope_and_unknown_boundary(self):
        payload = user_rule_payload()
        frozen = freeze_approved_proposals(payload)
        methods = {m['id']: m for m in payload['approvedMethods']}
        for row in frozen['updateUnits']:
            method = methods[row['methodId']]
            body = row['replacementBody']
            self.assertIn(method['action'], body)
            for condition in method['conditions']:
                self.assertIn(condition, body)
            self.assertIn(method['completionCheck'], body)
            self.assertIn(row['scopeText'], body)
            self.assertIn('UNKNOWN', body)
        public = public_update_input(frozen)
        for event in payload['evidence'][0]['events']:
            self.assertNotIn(event['text'], repr(public['updateUnits']))

    def test_eligible_units_can_be_explicitly_deferred_without_changing_baseline(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        selection = {
            'decision': 'SUPPORT', 'mergedPatches': [],
            'deferred': [{'proposalId': pid, 'reason': '基准规则已经覆盖'}
                         for pid in eligible_ids(frozen)],
        }
        files, audit = compile_patch(frozen, selection)
        self.assertEqual(files, frozen['initial_files'])
        self.assertEqual({r['proposalId'] for r in audit['deferred']}, set(eligible_ids(frozen)))

    def test_eligible_unit_omission_is_rejected(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        selection = selected(frozen)
        selection['mergedPatches'][0]['proposalIds'].pop()
        with self.assertRaises(ValueError):
            compile_patch(frozen, selection)

    def test_duplicate_or_unknown_unit_selection_is_rejected(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        for extra in (eligible_ids(frozen)[0], 'invented-unit'):
            with self.subTest(extra=extra):
                selection = selected(frozen)
                selection['mergedPatches'][0]['proposalIds'].append(extra)
                with self.assertRaises(ValueError):
                    compile_patch(frozen, selection)

    def test_selected_unit_cannot_also_be_deferred(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        selection = selected(frozen)
        selection['deferred'] = [{'proposalId': eligible_ids(frozen)[0], 'reason': '重复延期'}]
        with self.assertRaises(ValueError):
            compile_patch(frozen, selection)

    def test_model_cannot_supply_analysis_or_change_bound_metadata(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        for field, value in (
            ('analyses', frozen['frozenAnalyses']), ('approvedMethodIds', ['m2']),
            ('updateUnits', []), ('targetBase', ['another-skill', 9, 'other-hash']),
            ('proposalContractVersion', 'model-owned-v1'), ('evidence', []),
            ('title', '模型新增未获准能力标题'),
        ):
            with self.subTest(field=field):
                selection = selected(frozen)
                selection[field] = deepcopy(value)
                with self.assertRaises(ValueError):
                    compile_patch(frozen, selection)

    def test_model_cannot_rewrite_group_scope_or_citations(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        for field, value in (
            ('scope', 'FUTURE_TASKS'), ('methodId', 'm2'),
            ('evidenceRefs', [{'eventId': 'e2', 'quote': 'invented'}]),
        ):
            with self.subTest(field=field):
                selection = selected(frozen)
                selection['mergedPatches'][0][field] = value
                with self.assertRaises(ValueError):
                    compile_patch(frozen, selection)

    def test_frozen_unit_or_private_analysis_tampering_is_rejected(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        for field in ('updateUnits', 'frozenAnalyses', 'frozenProposalHash'):
            with self.subTest(field=field):
                modified = deepcopy(frozen)
                if field == 'updateUnits':
                    modified[field][0]['methodId'] = 'm2'
                elif field == 'frozenAnalyses':
                    modified[field][0]['proposals'][0]['evidenceRefs'][0]['quote'] = 'invented'
                else:
                    modified[field] = '0' * 64
                with self.assertRaises(ValueError):
                    compile_patch(modified, selected(frozen))

    def test_observed_requires_verified_business_result_for_that_method(self):
        for scope in ('STEP', 'METHOD'):
            with self.subTest(scope=scope):
                payload = observed_payload()
                payload['approvedMethods'][0]['supportAssessment']['validations'][0]['scope'] = scope
                frozen = freeze_approved_proposals(payload)
                self.assertEqual(len(eligible_ids(frozen)), 1)
                self.assertEqual(frozen['updateUnits'][0]['evidenceType'], 'OBSERVED')
                _, audit = compile_patch(frozen, selected(frozen))
                self.assertEqual(audit['proposalAudit'][0]['status'], 'PROPOSED')

    def test_unknown_process_and_technical_results_are_host_deferred(self):
        invalid = (
            ('unknown-method', {'methodOutcome': 'UNKNOWN'}),
            ('no-validation', {'validations': []}),
            ('task-score', {'scope': 'TASK'}),
            ('tool-success', {'outcomeType': 'TECHNICAL', 'sourceType': 'TOOL_RESULT'}),
            ('user-gratitude', {'sourceType': 'USER_FEEDBACK'}),
            ('other-method', {'targetIds': ['source2']}),
            ('ineligible-result', {'methodResultEligible': False}),
            ('failed-check', {'status': 'FAILURE'}),
        )
        for label, changes in invalid:
            with self.subTest(case=label):
                payload = observed_payload()
                assessment = payload['approvedMethods'][0]['supportAssessment']
                for key, value in changes.items():
                    if key in ('methodOutcome', 'validations'):
                        assessment[key] = value
                    else:
                        assessment['validations'][0][key] = value
                frozen = freeze_approved_proposals(payload)
                self.assertFalse(eligible_ids(frozen))
                self.assertTrue(frozen['hostDeferredUnits'])
                self.assertTrue(all(row['status'] == 'DEFERRED' and row['reason']
                                    for row in frozen['updateUnits']))
                files, audit = compile_patch(frozen, selected(frozen))
                self.assertEqual(files, frozen['initial_files'])
                self.assertTrue(all(row['status'] == 'DEFERRED' for row in audit['proposalAudit']))
                self.assertEqual(audit['hostDeferredUnits'], frozen['hostDeferredUnits'])

    def test_host_deferred_units_need_no_model_ack_and_cannot_be_selected(self):
        payload = user_rule_payload()
        payload['approvedMethods'][1]['supportAssessment']['eligible'] = False
        frozen = freeze_approved_proposals(payload)
        selection = selected(frozen)
        _, audit = compile_patch(frozen, selection)
        host_ids = {r['id'] for r in frozen['updateUnits'] if r['status'] == 'DEFERRED'}
        self.assertTrue(host_ids)
        self.assertTrue(host_ids <= {r['proposalId'] for r in audit['hostDeferredUnits']})
        selection['mergedPatches'][0]['proposalIds'].extend(host_ids)
        with self.assertRaises(ValueError):
            compile_patch(frozen, selection)

    def test_new_contract_forbids_append_add_replace_and_free_text(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        for action in ('append', 'add', 'replace'):
            with self.subTest(action=action):
                selection = selected(frozen)
                selection['mergedPatches'][0]['operations'][0]['op'] = action
                with self.assertRaises(ValueError):
                    compile_patch(frozen, selection)
        for field, value in (('path', 'SKILL.md'), ('content', 'model-authored instructions'),
                             ('old', BASELINE_ANCHOR), ('beforeHash', frozen['fileHashes']['SKILL.md'])):
            with self.subTest(field=field):
                selection = selected(frozen)
                selection['mergedPatches'][0]['operations'][0][field] = value
                with self.assertRaises(ValueError):
                    compile_patch(frozen, selection)

    def test_frozen_baseline_content_or_version_hash_tampering_is_rejected(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        for field in ('initial_files', 'fileHashes', 'targetBase'):
            with self.subTest(field=field):
                modified = deepcopy(frozen)
                if field == 'initial_files':
                    modified[field][0]['content'] += '\nchanged adopted version'
                elif field == 'fileHashes':
                    modified[field]['SKILL.md'] = digest('previous version')
                else:
                    modified[field][1] = 4
                with self.assertRaises(ValueError):
                    compile_patch(modified, selected(frozen))

    def test_anchor_id_must_exist_and_may_only_be_used_once(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        selection = selected(frozen)
        selection['mergedPatches'][0]['operations'][0]['anchorId'] = 'invented-anchor'
        with self.assertRaises(ValueError):
            compile_patch(frozen, selection)
        selection = selected(frozen)
        selection['mergedPatches'][0]['operations'].append(deepcopy(replacement(frozen)))
        with self.assertRaises(ValueError):
            compile_patch(frozen, selection)

    def test_insert_requires_no_conflict_assessment_and_reason(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        for field, value in (('compatibility', None), ('compatibility', 'REPLACE_BASELINE'),
                             ('reason', ''), ('reason', None)):
            with self.subTest(field=field, value=value):
                selection = selected(frozen)
                op = selection['mergedPatches'][0]['operations'][0]
                if value is None:
                    op.pop(field)
                else:
                    op[field] = value
                with self.assertRaises(ValueError):
                    compile_patch(frozen, selection)

    def test_baseline_without_structural_anchor_requires_explicit_defer(self):
        payload = user_rule_payload()
        files = initial_files(None, '通用材料处理')
        payload.update(initial_files=files, base_files=deepcopy(files),
                       fileHashes={f['path']: digest(f['content']) for f in files})
        frozen = freeze_approved_proposals(payload)
        self.assertEqual(public_update_input(frozen)['updateAnchors'], [])
        deferred = {
            'decision': 'DEFER', 'mergedPatches': [],
            'deferred': [{'proposalId': pid, 'reason': '基准没有唯一可用插入锚点'}
                         for pid in eligible_ids(frozen)],
        }
        result, _ = compile_patch(frozen, deferred)
        self.assertEqual(result, files)
        selection = deepcopy(deferred)
        selection['deferred'] = []
        selection['mergedPatches'] = [{'proposalIds': eligible_ids(frozen), 'operations': [{
            'op': 'insert_after', 'anchorId': 'invented-anchor',
            'compatibility': 'NO_CONFLICT', 'reason': '无依据的定位',
        }]}]
        with self.assertRaises(ValueError):
            compile_patch(frozen, selection)

    def test_duplicate_baseline_marker_never_becomes_a_public_anchor(self):
        payload = user_rule_payload()
        md = payload['initial_files'][0]['content']
        md += '\n\n### 方法 repeated\n<!-- SKILLSLOOP_METHOD:baseline-method -->\n重复定位。\n'
        payload['initial_files'][0]['content'] = md
        payload['base_files'] = deepcopy(payload['initial_files'])
        payload['fileHashes']['SKILL.md'] = digest(md)
        try:
            frozen = freeze_approved_proposals(payload)
        except ValueError:
            return  # Rejecting the ambiguous baseline itself also fails closed.
        self.assertFalse(any(a['kind'] == 'METHOD' and a['nodeId'] == 'baseline-method'
                             for a in public_update_input(frozen)['updateAnchors']))

    def test_existing_guard_cannot_be_removed_hidden_or_moved_by_model(self):
        frozen = freeze_approved_proposals(user_rule_payload())
        text = SCOPE_POLICY['CURRENT_TASK'][1]
        for content in ('', '<!--' + text + '-->', '```text\n' + text + '\n```'):
            with self.subTest(content=content[:20]):
                selection = selected(frozen)
                selection['mergedPatches'][0]['operations'][0].update(op='replace', old=text, content=content)
                with self.assertRaises(ValueError):
                    compile_patch(frozen, selection)

    def test_legacy_payload_shape_and_original_patch_output_remain_compatible(self):
        files = initial_files(None, '通用材料处理')
        payload = {
            'bridgeVersion': 'workflow-evolution-v1', 'action': 'UPDATE',
            'initial_files': files,
            'evidence': [{'taskId': 'legacy-task', 'outcome': 'UNKNOWN', 'analyst': 'unknown',
                          'events': [{'id': 'legacy-event', 'kind': 'user', 'text': '本次保留核对依据。'}]}],
        }
        output = {
            'analyses': [{'taskId': 'legacy-task', 'analyst': 'unknown', 'proposals': [{
                'id': 'legacy-proposal', 'lesson': '保留核对依据', 'applicability': '本次有效要求',
                'evidenceType': 'USER_RULE',
                'evidenceRefs': [{'eventId': 'legacy-event', 'quote': '保留核对依据'}],
            }]}],
            'mergedPatches': [{'proposalIds': ['legacy-proposal'], 'operations': [{
                'op': 'append', 'path': 'SKILL.md', 'beforeHash': digest(files[0]['content']),
                'content': '新增依据核对条目。',
            }]}],
        }
        frozen = freeze_approved_proposals(payload)
        self.assertEqual(frozen, payload)
        self.assertIsNot(frozen, payload)
        self.assertEqual(public_update_input(payload), payload)
        result, audit = compile_patch(frozen, output)
        self.assertEqual(result[0]['content'], files[0]['content'] + '\n新增依据核对条目。')
        self.assertEqual(audit['analyses'], output['analyses'])
        self.assertEqual(audit['applied'][0]['status'], 'APPLIED')
        self.assertNotIn('proposalContractVersion', audit)


if __name__ == '__main__':
    unittest.main()
