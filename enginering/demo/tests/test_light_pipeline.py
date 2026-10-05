"""Functional acceptance for the independent file pipeline; no semantic benchmark."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from skilldemo.pipeline import build, normalize_input
from skilldemo.runtime import digest
from test_heuristic_pipeline import synthetic_experience, relational_answer, workflow_answer, merge_answer


class Fixture:
    mode='authored-fixture'
    def __init__(self, empty=False):
        self.calls=[]
        self.payloads=[]
        self.empty=empty
    def run(self,purpose,payload,workspace):
        self.calls.append(purpose)
        self.payloads.append(deepcopy(payload))
        if purpose=='relational_extract':
            output=relational_answer(payload)
        elif purpose=='workflow_extract':
            output={'sourceHash':payload['sourceHash'],'frames':[],'methods':[],'relations':[]} if self.empty else workflow_answer(payload)
        elif purpose=='workflow_merge':
            output=merge_answer(payload)
        else:
            raise AssertionError('轻入口不应调用creator模型或治理阶段')
        return {'text':json.dumps(output,ensure_ascii=False),'usage':None,
                'runtime':'authored-fixture','modelRequestStarts':0}


class LightPipelineTests(unittest.TestCase):
    def test_more_than_eight_tasks_are_processed_without_truncation(self):
        class NineTasks(Fixture):
            def run(self,purpose,payload,workspace):
                result=super().run(purpose,payload,workspace)
                if purpose=='relational_extract':
                    answer=json.loads(result['text']);first=answer['seeds'][0]
                    answer['seeds']=[]
                    for i, (annotation, member) in enumerate(zip(answer['annotations'],answer['memberships']),1):
                        task='t'+str(i)
                        annotation['fragments'][0].update(task=task,kind='OPEN')
                        member['options'][0]['task']=task
                        seed=deepcopy(first);seed.update(key=task,anchor=member['fragment'])
                        answer['seeds'].append(seed)
                    result['text']=json.dumps(answer,ensure_ascii=False)
                return result
        value={'events':[],'context':[],'evaluations':[]}
        for i in range(9):value['events'].extend(synthetic_experience('independent-'+str(i))['events'])
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';agent=NineTasks()
            state=build(value,root,max_calls=5,agent=agent,official=False)
            self.assertEqual(state['recoveredTaskCount'],9)
            self.assertEqual(len(state['aggregationBatches']),2)
            self.assertEqual(len(agent.calls),5)
            self.assertEqual(sum(len(b['traceIds']) for b in state['aggregationBatches']),9)
            self.assertTrue((root/'04_batches/batch-002/workflows.json').is_file())

    def test_no_users_no_database_produces_official_skill_package(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';agent=Fixture()
            state=build(synthetic_experience(),root,agent=agent)
            self.assertEqual(state['status'],'COMPLETED')
            self.assertEqual(state['skillCount'],1)
            self.assertEqual(agent.calls,['relational_extract','workflow_extract','workflow_merge'])
            self.assertEqual(state['modelRequestStartsThisInvocation'],0)
            self.assertFalse(list(root.rglob('*.sqlite')))
            self.assertTrue((root/state['skills'][0]['entry']).is_file())
            self.assertTrue((root/state['skills'][0]['package']).is_file())
            self.assertEqual(state['skills'][0]['validation'],'STRUCTURAL_AND_OFFICIAL_PACKAGE')
            self.assertNotIn('KNOWN_NONE',(root/'01_collected.json').read_text(encoding='utf-8'))

    def test_exact_validated_cache_skips_model_dispatch(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';first=Fixture()
            build(synthetic_experience(),root,agent=first,official=False)
            second=Fixture();state=build(synthetic_experience(),root,agent=second,official=False)
            self.assertEqual(second.calls,[])
            self.assertEqual(state['modelRequestStartsThisInvocation'],0)
            self.assertTrue(all(r['status']=='CACHED' for r in state['requestLedger']))

    def test_explicit_saved_response_revalidation_avoids_new_calls_in_new_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/'source';target=Path(temp)/'new-version'
            build(synthetic_experience(),source,agent=Fixture(),official=False)
            agent=Fixture()
            state=build(synthetic_experience(),target,max_calls=0,agent=agent,official=False,reuse_requests=source)
            self.assertEqual(agent.calls,[])
            self.assertEqual(state['skillCount'],1)
            self.assertEqual(state['modelRequestStartsThisInvocation'],0)
            self.assertTrue(all(r['sourceBinding']['basis']=='EXACT_SAVED_RESPONSE_REVALIDATED' for r in state['requestLedger']))
            self.assertTrue(all(r['usageFromPriorInvocation'] for r in state['requestLedger']))

    def test_changed_source_cannot_overwrite_run(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';value=synthetic_experience()
            build(value,root,agent=Fixture(),official=False)
            value['events'][0]['content']+='额外要求。'
            with self.assertRaisesRegex(ValueError,'不同输入'):
                build(value,root,agent=Fixture(),official=False)

    def test_changed_cached_answer_cannot_impersonate_the_saved_response(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run'
            build(synthetic_experience(),root,agent=Fixture(),official=False)
            path=next((root/'requests').glob('relational_extract-*/record.json'))
            row=json.loads(path.read_text(encoding='utf-8'))
            row['output']['seeds'][0]['goal']='另一份格式合法但并非原模型响应的目标'
            path.write_text(json.dumps(row,ensure_ascii=False),encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'原始响应'):
                build(synthetic_experience(),root,agent=Fixture(),official=False)

    def test_generic_runtime_error_does_not_invent_a_model_start(self):
        class Broken(Fixture):
            def run(self,*args):raise RuntimeError('配置检查失败，没有开始HTTP')
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run'
            with self.assertRaisesRegex(RuntimeError,'配置检查失败'):
                build(synthetic_experience(),root,agent=Broken(),official=False)
            row=json.loads((root/'run.json').read_text(encoding='utf-8'))
            self.assertEqual(row['dispatchesThisInvocation'],1)
            self.assertIsNone(row['modelRequestStartsThisInvocation'])
            self.assertEqual(row['unknownStartReceiptsThisInvocation'],1)

    def test_empty_method_pool_finishes_without_fabricated_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            agent=Fixture(empty=True)
            state=build(synthetic_experience(),Path(temp)/'run',agent=agent,official=False)
            self.assertEqual(state['skillCount'],0)
            self.assertEqual(len(agent.calls),2)
            self.assertEqual(state['stages']['packaging'],'NO_CANDIDATES')

    def test_budget_stops_and_preserves_prior_stages(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';agent=Fixture()
            with self.assertRaisesRegex(ValueError,'MODEL_CALL_BUDGET'):
                build(synthetic_experience(),root,max_calls=1,agent=agent,official=False)
            self.assertEqual(len(agent.calls),1)
            self.assertTrue((root/'02_03_recovered.json').is_file())
            self.assertEqual(json.loads((root/'run.json').read_text(encoding='utf-8'))['status'],'FAILED')

    def test_same_output_has_an_exclusive_run_lock(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'run';root.mkdir()
            (root/'.pipeline.lock').write_text('other-running-process',encoding='utf-8')
            agent=Fixture()
            with self.assertRaisesRegex(ValueError,'运行锁'):
                build(synthetic_experience(),root,agent=agent,official=False)
            self.assertEqual(agent.calls,[])
            self.assertEqual((root/'.pipeline.lock').read_text(encoding='utf-8'),'other-running-process')

    def test_ecv_aliases_and_native_user_call_are_preserved(self):
        value={'E':[{'role':'user','content':'请检查设备。'},
                    {'role':'user','content':'','tool_calls':[{'id':'c1','function':{'name':'check','arguments':'{"phone":1}'}}]}],
               'C':[],'V':[]}
        normalized,mapping=normalize_input(value)
        self.assertEqual(normalized['events'][1]['toolCalls'][0]['arguments'],{'phone':1})
        self.assertEqual(normalized['events'][1]['content'],'')
        self.assertTrue(mapping[0]['idGenerated'])

    def test_whole_benchmark_gold_is_not_implicitly_imported(self):
        with self.assertRaisesRegex(ValueError,'隐藏答案'):
            normalize_input({'E':[{'role':'user','content':'任务'}],'reward_info':{'reward':1}})

    def test_response_replay_requires_exact_payload_identity(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(ValueError,'payloadHash'):
                build(synthetic_experience(),Path(temp)/'run',responses={'responses':[
                    {'purpose':'relational_extract','payloadHash':'wrong','output':{}}]},official=False)
