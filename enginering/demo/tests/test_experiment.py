import json
from pathlib import Path
import tempfile
import unittest

from skilldemo.core import Loop
from skilldemo.experiment import (select_source,make_manifest,execute_experiment,freeze,sha,verify_saved_results)
from skilldemo.runtime import HEADINGS
from test_front_stages import StructuredFixture


def case_files(root):
    root=Path(root);(root/'private').mkdir(parents=True)
    raw=[];index=[];selection=[]
    for i,session in enumerate(('group-a','group-b','held-out'),1):
        ids=[]
        for j,(role,body) in enumerate((('user','请审查合同条款'),('assistant','先核对输入，再列出风险和建议'))):
            mid=session+':'+role;ids.append(mid)
            row={'id':mid,'sessionId':session,'role':role,'content':body,'status':'done'}
            line=json.dumps(row,ensure_ascii=False).encode();raw.append(line)
            index.append({'messageId':mid,'sessionId':session,'role':role,'sourceLine':i*10+j,
                          'rawLineSha256':sha(line),'contentSha256':sha(body.encode()),'userCreatedAt':None})
        selection.append({'sessionId':session,'split':'holdout' if i==3 else 'generation','sourceMessageCount':2,
            'turns':[{'userMessageId':ids[0],'assistantMessageIds':[ids[1]],'task':'HUMAN_LABEL_MUST_NEVER_LEAK','replyTo':'FORGED_REPLY'}]})
    (root/'private/raw_messages.jsonl').write_bytes(b'\n'.join(raw)+b'\n')
    (root/'source_index.json').write_text(json.dumps(index,ensure_ascii=False),encoding='utf-8')
    (root/'recovered_trajectories.json').write_text(json.dumps(selection,ensure_ascii=False),encoding='utf-8')


class CompleteFixture(StructuredFixture):
    def run(self,purpose,payload,workspace):
        if purpose not in ('workflow_extract','workflow_merge','workflow_creator'):
            return super().run(purpose,payload,workspace)
        self.calls.append(purpose)
        if purpose=='workflow_extract':
            frames=[];methods=[]
            for i,trace in enumerate(payload['traces'],1):
                frame=f'f{i}';method=f'm{i}'
                evidence=next(e for e in trace['evidence'] if e['kind']=='USER_REQUIREMENT')
                frames.append({'id':frame,'traceId':trace['traceId'],'goal':'审阅合同条款',
                    'inputContract':['待审条款'],'outputContract':['审阅建议'],'processSketch':['核对输入','提出建议'],
                    'conditions':[],'parameters':['当前立场'],'methodIds':[method]})
                methods.append({'id':method,'frameId':frame,'action':'核对输入并按当前立场给出建议',
                    'inputs':['待审条款'],'outputs':['审阅建议'],'conditions':[],'parameters':['当前立场'],
                    'completionCheck':'每个结论对应原文依据；专业效果待验证','evidenceRefs':[evidence['id']],
                    'evidenceKind':'USER_REQUIREMENT','outcome':'UNKNOWN','decisionHint':'INCLUDE','reason':'来源支持用户需求'})
            out={'sourceHash':payload['sourceHash'],'frames':frames,'methods':methods,
                 'relations':[{'left':'f1','right':'f2','kind':'SHARE_CORE','sharedSteps':['核对输入','提出建议'],'condition':'当前立场','reason':'流程相同'}]}
        elif purpose=='workflow_merge':
            group=payload['clusters'][0];mids=[m['id'] for m in group['methods']]
            out={'sourceHash':payload['sourceHash'],'workflows':[{'frameIds':group['frameIds'],'title':'合同条款审阅',
                'trigger':'需要审阅条款','inputs':['待审条款','当前立场'],
                'steps':[{'id':'step'+str(i),'methodIds':[m],'action':'核对输入再给出建议','condition':'当前任务',
                          'completionCheck':'建议对应条款；专业效果未知'} for i,m in enumerate(mids)],
                'outputs':['建议文本'],'parameters':['当前立场'],'conditions':[],'dependencies':[],
                'limitations':['业务结果与专业正确性未知'],'includedMethodIds':mids}],
                'ledger':[{'methodId':m,'disposition':'INCLUDED','reason':'保留来源支持的方法','duplicateOf':None} for m in mids]}
        else:
            mids=payload['workflow']['includedMethodIds']
            text='---\nname: fixture-review\ndescription: 核对输入并提供条款审阅建议。\n---\n# 合同审阅\n'
            coverage=[]
            for i,method in enumerate(mids,1):
                heading=f'步骤 {i}';body='明确本次角色，逐项核对材料；输出对应条款的建议文本，未知结论标记为待验证。'
                text+=f'\n## {heading}\n<!-- SKILLSLOOP_METHOD:{method} -->\n{body}\n'
                coverage.append({'methodId':method,'file':'SKILL.md','actionQuote':'明确本次角色，逐项核对材料',
                                 'conditionQuotes':[],'completionCheckQuote':'未知结论标记为待验证'})
            text+='\n## 市场信息\n'+'\n'.join('### '+h+'\n供示例使用。' for h in HEADINGS)
            (workspace/'draft').mkdir(parents=True,exist_ok=True)
            (workspace/'draft/SKILL.md').write_bytes(text.encode())
            out={'decision':'CREATE','title':'合同条款审阅','coverageManifest':coverage}
        result={'text':json.dumps(out,ensure_ascii=False),'usage':{'total':100},'modelRequestStarts':0,'mode':self.mode}
        if purpose=='workflow_creator':result['foundationRead']={'status':'FILE_READ','basis':'SYNTHETIC_HOST_CONTROL_NOT_REAL_AGENT'}
        return result


class ExperimentTests(unittest.TestCase):
    def test_selection_fetches_bodies_excludes_holdout_and_manual_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            case_files(temp);events,source=select_source(temp)
            self.assertEqual(source['eventCount'],4)
            self.assertEqual(source['sessionIds'],['group-a','group-b'])
            self.assertNotIn('HUMAN_LABEL',json.dumps(events))
            self.assertNotIn('replyTo',json.dumps(events))
            self.assertNotIn('held-out',json.dumps(events))
            self.assertTrue(all(e['content'] for e in events))

    def test_hash_mismatch_and_foreign_database_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            case=Path(temp)/'case';case_files(case)
            events,source=select_source(case)
            manifest=make_manifest(source,{'code':'hash'},{'provider':'fixture'})
            data=Path(temp)/'run';data.mkdir();(data/'loop.sqlite').write_bytes(b'foreign')
            with self.assertRaisesRegex(ValueError,'UNOWNED_DATABASE'):freeze(data,manifest)
            index=json.loads((case/'source_index.json').read_text());index[0]['contentSha256']='wrong'
            (case/'source_index.json').write_text(json.dumps(index))
            with self.assertRaisesRegex(ValueError,'hash mismatch'):select_source(case)

    def test_frozen_config_changed_rejected_before_factory(self):
        with tempfile.TemporaryDirectory() as temp:
            case=Path(temp)/'case';case_files(case);events,source=select_source(case)
            manifest=make_manifest(source,{'code':'a'},{'provider':'fixture'})
            data=Path(temp)/'run'
            execute_experiment(data,events,manifest,lambda _:self.fail('preflight created a loop'),True)
            other=make_manifest(source,{'code':'b'},{'provider':'fixture'})
            with self.assertRaisesRegex(ValueError,'MANIFEST_CHANGED'):
                execute_experiment(data,events,other,lambda _:self.fail('changed run created a loop'))

    def test_first5_fresh_host_pipeline_official_package_and_cache_resume(self):
        from skilldemo.bootstrap import CREATOR
        if not (CREATOR/'scripts/package_skill.py').exists():self.skipTest('official local creator not installed')
        with tempfile.TemporaryDirectory() as temp:
            case=Path(temp)/'case';case_files(case);events,source=select_source(case)
            agent=CompleteFixture();data=Path(temp)/'run'
            manifest=make_manifest(source,{'fixture':'fixed'},{'provider':'synthetic'})
            factory=lambda path:Loop(path,agent,settle_seconds=0,daily_limit=12,stage_pipeline=True)
            result=execute_experiment(data,events,manifest,factory)
            self.assertEqual(result['status'],'PASSED',result)
            self.assertEqual(agent.calls,['detect_pairs','recover_trace','detect_pairs','recover_trace','workflow_extract','workflow_merge','workflow_creator'])
            self.assertEqual(result['workflowCount'],1)
            self.assertEqual(len(result['deliverables']),1)
            self.assertEqual(verify_saved_results(data)['status'],'PASS')
            before=list(agent.calls);result=execute_experiment(data,events,manifest,factory)
            self.assertEqual(result['status'],'PASSED',result)
            self.assertEqual(agent.calls,before)

    def test_resume_queued_candidate_and_detect_final_manifest_drift(self):
        from skilldemo.bootstrap import CREATOR
        if not (CREATOR/'scripts/package_skill.py').exists():self.skipTest('official local creator not installed')
        with tempfile.TemporaryDirectory() as temp:
            case=Path(temp)/'case';case_files(case);events,source=select_source(case)
            agent=CompleteFixture();data=Path(temp)/'run'
            manifest=make_manifest(source,{'fixture':'fixed'},{'provider':'synthetic'})
            freeze(data,manifest)
            factory=lambda path:Loop(path,agent,settle_seconds=0,daily_limit=12,stage_pipeline=True)
            loop=factory(data)
            for session in source['sessionIds']:
                loop.import_events('alice',[e for e in events if e['sessionId']==session],'generation',manifest['initialization'])
            loop.run_stages('alice');loop.discover('alice')
            self.assertEqual(loop.snapshot('alice')['candidates'][0]['status'],'QUEUED')
            before=list(agent.calls)
            result=execute_experiment(data,events,manifest,factory,final_manifest=lambda:{'changed':'code'})
            self.assertEqual(agent.calls,before+['workflow_creator'])
            self.assertEqual(result['status'],'FAILED')
            self.assertFalse(result['frozenInputsCodeAndConfigUnchanged'])
            self.assertEqual(len(result['deliverables']),1)
            calls=list(agent.calls)
            result=execute_experiment(data,events,manifest,factory)
            self.assertEqual(result['status'],'FAILED')
            self.assertEqual(agent.calls,calls)


if __name__=='__main__':unittest.main()
