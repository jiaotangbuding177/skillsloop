"""End-to-end orchestration using explicitly authored semantic responses."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from skilldemo.library_pipeline import build, prepare_batches
from skilldemo.library_export import verify_frozen


def material(count=2):
    events=[]
    for i in range(count):
        events.extend([{'id':f'u{i}','sessionId':f's{i}','role':'user','order':1,
                        'content':'请按原编号列出审阅意见。'},
                       {'id':f'a{i}','sessionId':f's{i}','role':'assistant','order':2,
                        'content':f'{i+1}.1 交付期限需要明确。'}])
    return {'E':events,'C':[],'V':[]}


class SemanticFixture:
    mode='explicit-authored-fixture'
    def __init__(self):self.calls=[]
    def run(self,purpose,payload,workspace):
        self.calls.append(purpose)
        if purpose=='library_relational_extract':
            out={k:[] for k in ('seeds','annotations','memberships','relations','observations','requirements','executionBindings','evaluationBindings')}
            for i,pair in enumerate(payload['pairs'],1):
                task=f't{i}';frag=pair['id']+':f1'
                out['seeds'].append(dict(key=task,anchor=frag,goal='保留原编号的审阅输出',object='本次文档',deliverable='意见文本',constraints=[]))
                out['annotations'].append({'pair':pair['id'],'fragments':[dict(id='f1',quote=pair['user'],intent='审阅',kind='OPEN',task=task,alternatives=[],references=[],uncertainty='')]})
                out['memberships'].append({'fragment':frag,'options':[dict(task=task,status='CONFIRMED',score=1,reason='人工夹具独立会话')]})
                for span in pair['evidenceSpans']:
                    if span['side']=='assistant':out['observations'].append(dict(fragment=frag,kind='VISIBLE_TEXT',evidence={'span':span['id']},description='可见意见正文'))
        elif purpose=='local_experience_extract':
            from skilldemo.local_experience import expand_model_input
            payload=expand_model_input(payload)
            methods=[]
            for i,trace in enumerate(payload['traces'],1):
                source=next(s for s in payload['catalog'] if s['kind']=='ASSISTANT_TEXT' and s['id'] in trace['sourceRefs'])
                methods.append(dict(id=f'm{i}',trace=trace['id'],goal='保留原编号的审阅输出',goalKey='review_output',
                    objectType='document',outputType='review',conditions=[],unknowns=['内容尚无独立业务核验'],
                    steps=[dict(id='s1',operator='render_review',action='按本次文档原编号列审阅意见',actor='assistant',
                        objectRole='review',effect='review_rendered',effectDimensions=['numbering','quality'],
                        inputRoles=['source_document'],outputRoles=['review'],dependsOn=[],sourceRefs=[source['id']],
                        kind='VISIBLE_OUTPUT',conditions=[],checks=[])]))
            out={'methods':methods,'unassigned':[]}
        else:raise AssertionError('不能偷偷追加合并或包装模型调用')
        return {'text':json.dumps({**out,'sourceHash':payload['sourceHash']},ensure_ascii=False),
                'modelRequestStarts':0,'runtime':self.mode,'usage':None}


class DirectPipelineTests(unittest.TestCase):
    def test_two_instances_really_merge_and_export_official_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            agent=SemanticFixture();root=Path(temp)/'run'
            result=build(material(),root,agent=agent)
            self.assertEqual((result['recoveredTaskCount'],result['localMethodCount'],result['skillCount']),(2,2,1))
            self.assertEqual(agent.calls,['library_relational_extract','local_experience_extract'])
            wf=json.loads((root/'04_workflows.json').read_text(encoding='utf-8'))
            self.assertEqual(len(wf['mergeLedger']),1)
            self.assertTrue(verify_frozen(root)['valid'])
            self.assertTrue((root/result['skills'][0]['package']).is_file())
            self.assertFalse(list(root.rglob('*.sqlite')))

    def test_cross_batch_pooling_happens_before_packaging(self):
        with tempfile.TemporaryDirectory() as temp:
            result=build(material(),temp,max_calls=4,agent=SemanticFixture(),official=False,batch_sessions=1)
            self.assertEqual((result['batchCount'],result['localMethodCount'],result['skillCount']),(2,2,1))

    def test_frozen_rerun_is_zero_requests_and_checks_tampering(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);build(material(),root,agent=SemanticFixture(),official=False)
            agent=SemanticFixture();result=build(material(),root,max_calls=0,agent=agent,official=False)
            self.assertEqual(agent.calls,[]);self.assertEqual(result['modelRequestStartsThisInvocation'],0)
            (root/result['skills'][0]['entry']).write_text('corruption',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'冻结库'):
                build(material(),root,agent=agent,official=False)

    def test_budget_failure_does_not_publish_frozen_library(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            with self.assertRaisesRegex(ValueError,'MODEL_CALL_BUDGET'):
                build(material(),root,max_calls=1,agent=SemanticFixture(),official=False)
            self.assertFalse((root/'frozen_manifest.json').exists())
            self.assertFalse((root/'requests').exists())
            self.assertTrue((root/'normalized_input.json').exists())
            self.assertEqual(json.loads((root/'run.json').read_text(encoding='utf-8'))['status'],'FAILED')

    def test_changed_input_rejected_without_overwriting_frozen_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);build(material(),root,agent=SemanticFixture(),official=False)
            before=(root/'run.json').read_bytes();value=material();value['E'][0]['content']+='额外要求'
            with self.assertRaisesRegex(ValueError,'不同输入'):
                build(value,root,agent=SemanticFixture(),official=False)
            self.assertEqual((root/'run.json').read_bytes(),before)

    def test_preflight_keeps_whole_sessions_and_rejects_missing_evaluation_targets(self):
        value=material();value['E'][1]['content']='x'*3000
        with self.assertRaisesRegex(ValueError,'SESSION_INPUT_BUDGET'):prepare_batches(value,batch_chars=1000)
        value=material();value['V']=[{'id':'v1','source':'public check','scope':'STEP','targetIds':['u0','missing'],
                                    'criterion':'编号','result':True}]
        with self.assertRaisesRegex(ValueError,'评价目标'):prepare_batches(value)

    def test_run_lock_rejects_another_invocation(self):
        with tempfile.TemporaryDirectory() as temp:
            (Path(temp)/'.pipeline.lock').write_text('existing',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'运行锁'):build(material(),temp,agent=SemanticFixture(),official=False)

    def test_final_verification_failure_invalidates_manifest_and_preserves_evidence(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);agent=SemanticFixture()
            with patch('skilldemo.library_export.verify_frozen',
                       side_effect=ValueError('injected final verification failure')):
                with self.assertRaisesRegex(ValueError,'injected final verification failure'):
                    build(material(),root,agent=agent,official=False)
            run=json.loads((root/'run.json').read_text(encoding='utf-8'))
            manifest=json.loads((root/'frozen_manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(run['status'],'FAILED')
            self.assertEqual(manifest['status'],'FAILED')
            self.assertTrue(list((root/'skills').rglob('SKILL.md')))
            self.assertTrue((root/'03_local_experience.json').exists())
            self.assertFalse((root/'.pipeline.lock').exists())
            self.assertEqual(agent.calls,['library_relational_extract','local_experience_extract'])
            with self.assertRaisesRegex(ValueError,'冻结库尚未完成'):
                verify_frozen(root)


if __name__=='__main__':unittest.main()
