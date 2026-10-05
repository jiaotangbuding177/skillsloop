"""Checks for experiment-consumable, evidence-scoped exports (no model requests)."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


def family():
    def step(key, kind, verdict, text):
        return dict(id=key, kind=kind, verdict=verdict, action=text, operator=key,
                    actor='assistant', objectRole='target_order', effect=key,
                    inputRoles=[], outputRoles=[], dependsOn=[], sourceRefs=['e1'],
                    conditions=[], checks=[dict(criterion='本次调用', dimension='execution',
                        status=verdict, supportRefs=[], counterRefs=[], unknownReason='')])
    methods=[dict(id='m1', traceId='t1', goal='核对订单', goalKey='check-order',
        steps=[step('lookup','ACTION','SATISFIED','查询目标订单'),
               step('modify','ACTION','VIOLATED','在不允许的状态修改'),
               step('claim','CLAIM','UNKNOWN','已创建新订单')],
        conditions=[], sourceRefs=['e1'], unknowns=['没有创建订单凭据'])]
    return dict(id='wf1', title='订单核对', memberIds=['m1'], members=methods,
        coreSteps=[], variants=[dict(methodId='m1', traceId='t1',
            conditions={'allOf':[]}, stepConditions=[], steps=methods[0]['steps'],
            status='MIXED', wholePathStatus='NOT_ESTABLISHED_BY_LOCAL_CHECKS',
            sourceRefs=['e1'], unknowns=['没有创建订单凭据'])],
        warnings=[], conflicts=[], unknowns=[], sourceRefs=['e1'], supportCount=1,
        mappings=[], compression={}, semanticAlignment='PROPOSED_NOT_INDEPENDENTLY_VERIFIED',
        composition={'observedPathsOnly':True,'allowUnobservedCombinations':False})


class ExportTests(unittest.TestCase):
    def api(self):
        self.assertIsNotNone(importlib.util.find_spec('skilldemo.library_export'),
                             '实验库的冻结与验真导出尚未实现')
        from skilldemo import library_export
        return library_export

    def test_failed_actions_and_claims_are_outside_candidate_procedures(self):
        files=self.api().files_for(family())
        text=next(f['content'] for f in files if f['path']=='SKILL.md')
        procedures=text.split('## 可参考的方法')[1].split('## 失败、冲突与未执行内容')[0]
        self.assertIn('查询目标订单',procedures)
        self.assertNotIn('在不允许的状态修改',procedures)
        self.assertNotIn('已创建新订单',procedures)
        self.assertIn('没有创建订单凭据',text)
        self.assertIn('局部检查不证明整条路径成功',text)

    def test_frozen_manifest_checks_modified_and_extra_files(self):
        api=self.api()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            rows=api.publish(root,[family()],official=False)
            manifest=api.freeze(root,rows,{'inputHash':'test','algorithm':'test'})
            self.assertEqual(len(manifest['skills']),1)
            self.assertTrue(api.verify_frozen(root)['valid'])
            extra=root/'skills'/'extra.txt'; extra.write_text('drift',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'冻结库'):
                api.verify_frozen(root)
            extra.unlink()
            (root/rows[0]['entry']).write_text('modified',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'冻结库'):
                api.verify_frozen(root)

    def test_semantic_candidate_is_not_a_claim_of_benchmark_success(self):
        with tempfile.TemporaryDirectory() as temp:
            rows=self.api().publish(Path(temp),[family()],official=False)
            self.assertEqual(rows[0]['semanticValidation'],'NOT_INDEPENDENTLY_VERIFIED')
            self.assertTrue((Path(temp)/rows[0]['entry']).is_file())

    def test_failed_prerequisite_does_not_leave_dependent_action_in_recipe(self):
        wf=family();steps=wf['variants'][0]['steps']
        steps[0]['verdict']='VIOLATED'
        steps[1].update(verdict='SATISFIED',dependsOn=['lookup'])
        text=next(f['content'] for f in self.api().files_for(wf) if f['path']=='SKILL.md')
        recipe=text.split('## 可参考的方法')[1].split('## 失败、冲突与未执行内容')[0]
        self.assertNotIn('在不允许的状态修改',recipe)
        self.assertIn('前置依据尚未成立',text)

    def test_recipe_obeys_graph_dependencies_and_exposes_step_ids(self):
        wf=family();steps=wf['variants'][0]['steps']
        steps[1].update(verdict='UNKNOWN',dependsOn=['lookup'])
        wf['variants'][0]['steps']=[steps[1],steps[0],steps[2]]
        text=next(f['content'] for f in self.api().files_for(wf) if f['path']=='SKILL.md')
        self.assertLess(text.index('步骤 lookup'),text.index('步骤 modify'))

    def test_only_promises_are_preserved_as_candidates_not_published_skills(self):
        wf=family();wf['variants'][0]['steps']=wf['variants'][0]['steps'][-1:]
        self.assertFalse(self.api().is_exportable(wf))
        with self.assertRaisesRegex(ValueError,'只有计划或自述'):
            self.api().files_for(wf)


if __name__=='__main__': unittest.main()
