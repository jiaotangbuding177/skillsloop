import unittest
from copy import deepcopy
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import MagicMock, patch
import json

from skilldemo import creator, relational_workflow
from skilldemo.runtime import HEADINGS, digest


def method(mid='m1', scope='CURRENT_DELIVERY'):
    mode, text = relational_workflow.SCOPE_POLICY[scope]
    return {'id': mid, 'action': '读取当前任务的实际输入材料', 'inputs': ['输入材料'],
            'outputs': ['处理结果'], 'conditions': ['本次要求仍适用时采用该流程'],
            'completionCheck': '核对结果符合本次有效要求',
            'scopeContract': {'version': relational_workflow.SCOPE_VERSION, 'bindings': [
                {'id': 'scope1', 'scope': scope, 'mode': mode, 'parameter': '本次有效要求', 'text': text}]},
            'requirementApplicability': [{'value': 'PRIVATE-INSTANCE-VALUE', 'sourceRefs': ['PRIVATE-REF']} ]}


def workflow():
    return {'title': '处理任务', 'trigger': '用户请求执行已有任务流程',
            'inputs': ['任务目标', '本次有效要求'], 'outputs': ['本次交付物'],
            'conditions': ['开始前确认可用输入'], 'dependencies': ['执行前确认所需工具可用'],
            'parameters': ['本次交付形式'], 'limitations': ['整体业务效果仍为UNKNOWN'],
            'includedMethodIds': ['m1'], 'businessOutcome': 'UNKNOWN',
            'steps': [{'id': 'source-step-' + str(i), 'methodIds': ['m1'],
                       'action': '执行来源实例动作第' + str(i) + '步',
                       'condition': '核对本次要求后才执行',
                       'completionCheck': '检查第' + str(i) + '步满足本次要求'} for i in range(1, 5)]}


def draft():
    text = '---\nname: always-plain-text\ndescription: 所有任务永远只输出纯文本。\n---\n'
    text += '## 方法\n所有后续任务永远只输出纯文本。\n'
    text += '\n## 市场信息\n' + '\n'.join('### ' + h + '\n所有任务永远只输出纯文本。' for h in HEADINGS)
    return [{'path': 'SKILL.md', 'content': text}]


def assembled():
    methods = [method()]
    scoped = relational_workflow.with_step_scope_contract(workflow(), methods)
    files, audit = creator.assemble_step_scoped_files(draft(), scoped, methods)
    return scoped, methods, files, audit


def verify(scoped, methods, files, audit):
    return creator.verify_files(files, scoped['includedMethodIds'], methods=methods,
        coverageManifest=audit['methodCoverageManifest'], workflow=scoped,
        stepCoverageManifest=audit['stepCoverageManifest'])


class WorkflowStepScopeTests(unittest.TestCase):
    def test_same_method_requires_scope_on_all_four_steps(self):
        scoped, methods, files, audit = assembled()
        checked = verify(scoped, methods, files, audit)
        self.assertEqual([r['stepId'] for r in checked['stepScopeCoverage']], ['s1', 's2', 's3', 's4'])
        self.assertEqual(len(audit['stepCoverageManifest']), 4)
        text = methods[0]['scopeContract']['bindings'][0]['text']
        md = files[0]['content']
        for sid in ('s1', 's2', 's3', 's4'):
            segment = relational_workflow._step_segment(md, sid)
            self.assertIn(text, segment)

    def test_later_step_cannot_borrow_first_step_scope(self):
        scoped, methods, files, audit = assembled()
        guard = methods[0]['scopeContract']['bindings'][0]['text']
        marker = '<!-- SKILLSLOOP_STEP:s4 -->'
        before, after = files[0]['content'].split(marker, 1)
        files[0]['content'] = before + marker + after.replace(guard, '', 1)
        with self.assertRaisesRegex(ValueError, '步骤范围'):
            verify(scoped, methods, files, audit)

    def test_host_discards_model_defaults_and_keeps_frozen_contract(self):
        scoped, methods, files, audit = assembled()
        md = files[0]['content']
        self.assertNotIn('所有任务永远只输出纯文本', md)
        self.assertNotIn('always-plain-text', md)
        for key in ('trigger', 'inputs', 'outputs', 'conditions', 'dependencies', 'limitations'):
            values = [scoped[key]] if isinstance(scoped[key], str) else scoped[key]
            for value in values:
                self.assertIn(value, md)
        self.assertIn('来源实例动作', md)
        self.assertIn('否则先重新绑定实例取值', md)
        self.assertEqual(audit['status'], 'HOST_ASSEMBLED')
        self.assertEqual(verify(scoped, methods, files, audit)['semanticValidation'], 'NOT_INDEPENDENTLY_VERIFIED')

    def test_private_requirement_values_never_enter_public_contract_or_body(self):
        scoped, methods, files, audit = assembled()
        self.assertNotIn('PRIVATE-', repr(scoped['stepScopeContract']))
        self.assertNotIn('PRIVATE-', files[0]['content'])

    def test_step_scope_cannot_be_hidden_or_moved_into_another_step(self):
        for hidden in ('<!-- {text} -->', '```\n{text}\n```', '> ```\n> {text}\n> ```', '<style>{text}</style>'):
            scoped, methods, files, audit = assembled()
            guard = methods[0]['scopeContract']['bindings'][0]['text']
            marker = '<!-- SKILLSLOOP_STEP:s4 -->'
            before, after = files[0]['content'].split(marker, 1)
            files[0]['content'] = before + marker + after.replace(guard, hidden.format(text=guard), 1)
            with self.subTest(hidden=hidden), self.assertRaisesRegex(ValueError, '步骤范围'):
                verify(scoped, methods, files, audit)

    def test_each_step_gets_only_its_bound_methods_scopes(self):
        methods = [method('m1'), method('m2', 'FUTURE_TASKS')]
        w = workflow(); w['includedMethodIds'].append('m2'); w['steps'][3]['methodIds'] = ['m2']
        scoped = relational_workflow.with_step_scope_contract(w, methods)
        rows = scoped['stepScopeContract']['steps']
        self.assertEqual([b['scope'] for b in rows[0]['bindings']], ['CURRENT_DELIVERY'])
        self.assertEqual([b['scope'] for b in rows[3]['bindings']], ['FUTURE_TASKS'])

    def test_contract_mutation_or_missing_step_manifest_is_rejected(self):
        scoped, methods, files, audit = assembled()
        bad = deepcopy(scoped); bad['stepScopeContract']['steps'][3]['methodIds'] = ['m2']
        with self.assertRaises(ValueError):
            verify(bad, methods, files, audit)
        with self.assertRaises(ValueError):
            creator.verify_files(files, ['m1'], methods=methods,
                coverageManifest=audit['methodCoverageManifest'], workflow=scoped)

    def test_legacy_workflow_is_not_upgraded_or_assembled(self):
        w = workflow(); old = deepcopy(w)
        self.assertEqual(relational_workflow.with_step_scope_contract(w, [{'id': 'm1'}]), old)
        self.assertEqual(w, old)
        files, audit = creator.assemble_step_scoped_files(draft(), w, [{'id': 'm1'}])
        self.assertEqual(files, draft())
        self.assertIsNone(audit)

    def test_public_step_normalization_does_not_modify_frozen_workflow(self):
        w = workflow(); before = deepcopy(w)
        scoped = relational_workflow.with_step_scope_contract(w, [method()])
        self.assertEqual(w, before)
        self.assertEqual([s['id'] for s in scoped['steps']], ['s1', 's2', 's3', 's4'])

    def test_bridge_finalization_packages_host_body_and_retains_raw_result_audit(self):
        from skilldemo import workflow_bridge
        methods = [method()]
        scoped = relational_workflow.with_step_scope_contract(workflow(), methods)
        raw_files = draft(); original_files = deepcopy(raw_files)
        candidate = {'id': 'c1', 'status': 'GENERATING', 'runId': 'run1', 'analysisId': 'analysis1',
                     'workflowId': 'workflow1', 'title': '冻结标题',
                     'input': {'workflow': scoped, 'methods': methods}}
        store = MagicMock(); store.root = Path('synthetic-workspace'); store.tx.side_effect = lambda: nullcontext(MagicMock())
        store.get.side_effect = lambda db, kind, key: {'catalog': {}} if kind == 'workflow_analysis' else None
        loop = MagicMock(); loop.store = store; loop._owned.return_value = candidate
        result = {'text': json.dumps({'decision': 'CREATE', 'title': '模型原标题'}),
                  'foundationRead': {'status': 'FILE_READ'}}
        original_text = result['text']
        with patch.object(workflow_bridge, 'draft_files', return_value=raw_files), \
             patch.object(workflow_bridge, 'package', return_value={'path': 'synthetic.skill'}) as package, \
             patch.object(workflow_bridge, 'verify_archive', return_value={'status': 'PASS'}):
            final = workflow_bridge._finalize(loop, 'alice', 'c1', 'run1', result, 'GENERATING')
        self.assertEqual(final['status'], 'READY')
        self.assertEqual(final['title'], '冻结标题')
        self.assertEqual(len(final['validation']['hostBundle']['stepScopeCoverage']), 4)
        self.assertEqual(package.call_args.args[1], final['files'])
        self.assertNotIn('所有任务永远只输出纯文本', final['files'][0]['content'])
        self.assertEqual(result['text'], original_text)
        self.assertEqual(result['hostAssembly']['rawFilesHash'], digest(original_files))
        self.assertEqual(raw_files, original_files)


if __name__ == '__main__':
    unittest.main()
