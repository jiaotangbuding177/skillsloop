import unittest
from copy import deepcopy

from skilldemo import creator, relational_workflow, workflow
from test_relational_workflow import trace, extracted, merged_view
from test_workflow_step_scope import draft, method, workflow as scoped_workflow, verify


def local_failure(t, technical=False, verified=True):
    t['outcomeEvidence'] = [{'id': 'failed-local', 'sourceType': 'EVALUATION',
        'outcomeType': 'TECHNICAL' if technical else 'BUSINESS', 'status': 'FAILURE',
        'scope': 'STEP', 'targetIds': ['process1'], 'criterion': '当前动作符合要求',
        'ref': {}, 'verified': verified}]


def package_for(m):
    w = scoped_workflow()
    w['steps'] = [w['steps'][0]]
    w['steps'][0]['action'] = m['action']
    scoped = relational_workflow.with_step_scope_contract(w, [m])
    files, audit = creator.assemble_step_scoped_files(draft(), scoped, [m])
    return scoped, [m], files, audit


class LessonDirectionTests(unittest.TestCase):
    def test_known_local_failure_cannot_be_labelled_a_procedure(self):
        t = trace(); local_failure(t)
        _, _, ext = extracted(t, lessonType='PROCEDURE')
        m = ext['methods'][0]
        self.assertEqual(m['lessonType'], 'FAILURE_WARNING')
        self.assertEqual(m['decisionHint'], 'INCLUDE')
        self.assertEqual(m['supportAssessment']['causalStatus'], 'NOT_ESTABLISHED')

    def test_actual_failed_receipt_is_a_warning_without_claiming_verified_business_failure(self):
        t = trace()
        t['typedSources'][1].update(kind='TOOL_RESULT', metadata={'status': 'FAILURE', 'verified': False})
        _, _, ext = extracted(t, lessonType='PROCEDURE')
        m = ext['methods'][0]
        self.assertEqual(m['lessonType'], 'FAILURE_WARNING')
        self.assertEqual(m['outcome'], 'UNKNOWN')
        self.assertTrue(m['supportAssessment']['failureEvidence'])
        self.assertFalse(m['supportAssessment']['failureEvidence'][0]['verified'])

    def test_explicit_warning_from_user_correction_is_not_promoted(self):
        _, _, ext = extracted(trace(), source='u1', lessonType='FAILURE_WARNING')
        self.assertEqual(ext['methods'][0]['lessonType'], 'FAILURE_WARNING')
        self.assertEqual(ext['methods'][0]['decisionHint'], 'INCLUDE')

    def test_whole_task_failure_keeps_unknown_actual_methods_as_candidates(self):
        t = trace()
        t['businessOutcome'] = 'FAILURE'
        t['outcomeEvidence'] = [{'id': 'task-failure', 'sourceType': 'EVALUATION',
            'outcomeType': 'BUSINESS', 'status': 'FAILURE', 'scope': 'TASK',
            'targetIds': ['t1'], 'ref': {}, 'verified': True}]
        _, _, ext = extracted(t)
        m = ext['methods'][0]
        self.assertEqual(m['lessonType'], 'PROCEDURE')
        self.assertEqual(m['decisionHint'], 'INCLUDE')
        self.assertEqual(m['supportAssessment']['supportStatus'], 'OBSERVED_UNVERIFIED')

    def test_technical_success_does_not_override_local_business_failure(self):
        t = trace(); local_failure(t)
        t['outcomeEvidence'].append({'id': 'technical-ok', 'sourceType': 'TOOL_RESULT',
            'outcomeType': 'TECHNICAL', 'status': 'SUCCESS', 'scope': 'STEP',
            'targetIds': ['process1'], 'ref': {}, 'verified': True})
        _, _, ext = extracted(t)
        m = ext['methods'][0]
        self.assertEqual(m['lessonType'], 'FAILURE_WARNING')
        self.assertEqual(m['supportAssessment']['technicalOutcome'], 'SUCCESS')

    def test_legacy_guard_is_a_warning_even_without_local_result(self):
        _, _, ext = extracted(trace(), methodKind='FAILURE_GUARD', conditions=['核对允许修改'])
        self.assertEqual(ext['methods'][0]['lessonType'], 'FAILURE_WARNING')

    def test_invalid_lesson_type_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '用途'):
            extracted(trace(), lessonType='VERIFIED_GOOD')

    def test_mixed_step_splits_into_stable_method_specific_clauses(self):
        ext, view, output = merged_view(trace())
        good = ext['methods'][0]
        bad = deepcopy(good)
        bad.update(id='m2', action='绕过允许状态直接修改地址', lessonType='FAILURE_WARNING')
        ext['methods'].append(bad); ext['methodMap']['m2'] = bad
        ext['frameMap']['f1']['methodIds'].append('m2')
        w = output['workflows'][0]
        w['includedMethodIds'].append('m2')
        w['steps'][0].update(methodIds=['m1', 'm2'], action='查询状态后绕过允许状态直接修改地址')
        before = deepcopy(w)
        relational_workflow.validate_workflow(w, ext)
        self.assertEqual([s['lessonType'] for s in w['steps']], ['PROCEDURE', 'FAILURE_WARNING'])
        self.assertEqual([s['action'] for s in w['steps']], [good['action'], bad['action']])
        self.assertEqual(len({s['id'] for s in w['steps']}), 2)
        again = deepcopy(before); relational_workflow.validate_workflow(again, ext)
        self.assertEqual(w, again)
        self.assertEqual([r['lessonType'] for r in w['clauseLedger']], ['PROCEDURE', 'FAILURE_WARNING'])

    def test_warning_action_is_retained_as_history_outside_execution_section(self):
        m = method(); m.update(lessonType='FAILURE_WARNING', action='绕过订单状态直接修改地址')
        scoped, methods, files, audit = package_for(m)
        md = files[0]['content']
        execution = md.split('## 执行步骤', 1)[1].split('## 失败警示', 1)[0]
        self.assertNotIn(m['action'], execution)
        warning = md.split('## 失败警示', 1)[1]
        self.assertIn(m['action'], warning)
        self.assertIn('请勿照此重复', warning)
        self.assertEqual(audit['stepCoverageManifest'][0]['lessonType'], 'FAILURE_WARNING')
        self.assertEqual(verify(scoped, methods, files, audit)['status'], 'PASS')

    def test_warning_cannot_be_relabelled_or_moved_to_execution(self):
        m = method(); m.update(lessonType='FAILURE_WARNING', action='绕过订单状态直接修改地址')
        scoped, methods, files, audit = package_for(m)
        bad = deepcopy(files)
        bad[0]['content'] = bad[0]['content'].replace('## 失败警示', '## 执行步骤')
        with self.assertRaisesRegex(ValueError, '用途|警示'):
            verify(scoped, methods, bad, audit)
        wrong = deepcopy(audit); wrong['stepCoverageManifest'][0]['lessonType'] = 'PROCEDURE'
        with self.assertRaisesRegex(ValueError, '用途'):
            verify(scoped, methods, files, wrong)

    def test_avoidance_rule_is_not_prefixed_with_an_instruction_to_repeat_or_negate_it(self):
        m=method();m.update(lessonType='FAILURE_WARNING',action='避免擅自更改原协议条款编号')
        scoped,methods,files,audit=package_for(m)
        md=files[0]['content']
        self.assertIn('警示内容（风险行为或防范规则）：避免擅自更改原协议条款编号',md)
        self.assertNotIn('请勿照此重复）：避免',md)
        self.assertIn('防范规则按其原意核对并遵守',md)
        self.assertEqual(verify(scoped,methods,files,audit)['status'],'PASS')

    def test_warning_declaration_cannot_be_hidden_or_removed(self):
        m = method(); m.update(lessonType='FAILURE_WARNING', action='绕过订单状态直接修改地址')
        for replacement in ('', '<!-- {text} -->', '```\n{text}\n```'):
            scoped, methods, files, audit = package_for(m)
            policy = relational_workflow.LESSON_POLICY['FAILURE_WARNING']
            files[0]['content'] = files[0]['content'].replace(policy, replacement.format(text=policy))
            with self.subTest(replacement=replacement), self.assertRaisesRegex(ValueError, '用途'):
                verify(scoped, methods, files, audit)

    def test_only_warning_skill_is_useful_without_promising_to_execute_failed_action(self):
        t = trace(); local_failure(t)
        ext, view, output = merged_view(t, lessonType='PROCEDURE')
        ws, _ = workflow.validate_merge(output, view, ext)
        methods = [relational_workflow.public_method(m) for m in ext['methods']]
        scoped = relational_workflow.public_workflow(ws[0], methods)
        files, audit = creator.assemble_step_scoped_files(draft(), scoped, methods)
        self.assertIn('不包含可执行的推荐步骤', files[0]['content'])
        self.assertEqual(scoped['steps'][0]['lessonType'], 'FAILURE_WARNING')
        self.assertEqual(verify(scoped, methods, files, audit)['status'], 'PASS')

    def test_warning_assets_cannot_bypass_the_non_execution_direction(self):
        m = method(); m.update(lessonType='FAILURE_WARNING', action='绕过订单状态直接修改地址')
        scoped, methods, files, audit = package_for(m)
        extra = {'path': 'references/bad.md', 'content': '继续执行：绕过订单状态直接修改地址。'}
        with self.assertRaisesRegex(ValueError, '附属资源'):
            creator.assemble_step_scoped_files(draft() + [extra], scoped, methods)
        with self.assertRaisesRegex(ValueError, '附属资源'):
            verify(scoped, methods, files + [extra], audit)
        procedure = method()
        ordinary = relational_workflow.with_step_scope_contract(scoped_workflow(), [procedure])
        valid_resource = {'path': 'references/input.md', 'content': '执行前确认本次任务的有效输入。'}
        retained, _ = creator.assemble_step_scoped_files(draft() + [valid_resource], ordinary, [procedure])
        self.assertIn(valid_resource, retained)  # No blanket removal of legacy/procedure resources.

    def test_validated_revision_can_cite_old_failed_receipts_and_still_be_a_procedure(self):
        t = trace()
        t['typedSources'][1]['ref']['fragmentId'] = 'new-fragment'
        t['typedSources'].append({'id': 'old-result', 'kind': 'TOOL_RESULT', 'text': '旧方法的失败回执',
            'ref': {'fragmentId': 'old-fragment', 'pairId': 'p0', 'attemptId': 'old-attempt'},
            'metadata': {'status': 'FAILURE', 'verified': False}})
        t['attempts'].append({'id': 'old-attempt', 'pairId': 'p0', 'fragmentId': 'old-fragment',
            'requirementIds': [], 'evidenceRefs': ['old-result'], 'requirementVersion': 1})
        t['typedRelations'] = [{'id': 'repair', 'type': 'REVISES', 'from': 'new-fragment',
            'to': 'old-fragment', 'status': 'CONFIRMED', 'scope': 'CURRENT_TASK', 'evidenceRefs': ['u1']}]
        t['outcomeEvidence'] = [
            {'id': 'old-failed', 'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS', 'status': 'FAILURE',
             'scope': 'STEP', 'targetIds': ['old-result'], 'criterion': '地址符合要求', 'ref': {}, 'verified': True},
            {'id': 'new-fixed', 'sourceType': 'EVALUATION', 'outcomeType': 'BUSINESS', 'status': 'SUCCESS',
             'scope': 'STEP', 'targetIds': ['process1'], 'criterion': '地址符合要求', 'ref': {}, 'verified': True}]
        _, catalog = workflow.prepare([t])
        refs = [eid for eid, s in catalog.items() if s.get('sourceId') in ('process1', 'old-result')]
        _, _, ext = extracted(t, methodKind='VALIDATED_REVISION', evidenceRefs=refs)
        private = ext['methods'][0]
        self.assertEqual(private['supportAssessment']['supportStatus'], 'VALIDATED_REVISION')
        self.assertTrue(private['supportAssessment']['failureEvidence'])
        self.assertTrue(all(v['role'] == 'PRIOR_FAILURE' for v in private['supportAssessment']['failureEvidence']))
        public = relational_workflow.public_method(private)
        self.assertEqual(public['lessonType'], 'PROCEDURE')
        scoped, methods, files, audit = package_for(public)
        execution = files[0]['content'].split('## 执行步骤', 1)[1].split('## 失败警示', 1)[0]
        self.assertIn(public['action'], execution)
        self.assertEqual(verify(scoped, methods, files, audit)['status'], 'PASS')

    def test_warning_is_deferred_on_the_old_plain_update_contract(self):
        payload = {'bridgeVersion': 'relational-workflow-evolution-v1',
            'approvedMethods': [{'id': 'm1', 'sourceTaskId': 't1', 'evidenceRefs': ['e1'],
                'methodKind': 'FAILURE_GUARD', 'supportAssessment': {'eligible': True}}],
            'evidence': [{'taskId': 't1', 'events': [{'id': 'e1'}]}]}
        output = {'analyses': [{'taskId': 't1', 'proposals': [{'approvedMethodIds': ['m1'],
            'evidenceRefs': [{'eventId': 'e1'}]}]}]}
        with self.assertRaisesRegex(ValueError, '用途.*延期'):
            relational_workflow.validate_patch_constraints(payload, output)

    def test_hypothesis_is_not_rendered_as_an_execution_instruction(self):
        m = method(); m.update(lessonType='HYPOTHESIS', action='未经尝试的新修复办法')
        scoped, methods, files, audit = package_for(m)
        md = files[0]['content']
        execution = md.split('## 执行步骤', 1)[1].split('## 失败警示', 1)[0]
        self.assertNotIn(m['action'], execution)
        self.assertIn('## 待验证假设', md)
        self.assertIn('未经验证，不作为执行指令', md)
        self.assertEqual(verify(scoped, methods, files, audit)['status'], 'PASS')

    def test_legacy_guard_triggers_safe_host_assembly_without_changing_plain_legacy(self):
        m = method(); m.pop('scopeContract'); m['methodKind'] = 'FAILURE_GUARD'
        scoped, methods, files, audit = package_for(m)
        self.assertIsNotNone(audit)
        self.assertIn('## 失败警示', files[0]['content'])
        plain = scoped_workflow()
        self.assertEqual(relational_workflow.with_step_scope_contract(plain, [{'id': 'm1'}]), plain)
        self.assertEqual(creator.assemble_step_scoped_files(draft(), plain, [{'id': 'm1'}]), (draft(), None))


if __name__ == '__main__':
    unittest.main()
