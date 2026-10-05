import unittest
from copy import deepcopy
from skilldemo import workflow
from skilldemo.creator import verify_files
from skilldemo.runtime import HEADINGS


def trace(i, split='generation'):
    pair=f'p{i}'
    return {'id':f't{i}','owner':'alice','org':'acme','schemaVersion':'task-trace-v2','purposeSplit':split,
            'session':f's{i}','state':'SEALED','revision':1,'hash':f'h{i}','goal':f'完成实例{i}的合同流程',
            'object':'合同','businessOutcome':'UNKNOWN',
            'initializationEvidence':[{'status':'KNOWN_NONE','basis':'fixture no skill'}],
            'skillUseReceipts':[],
            'requirementTimeline':[{'version':1,'effectiveFromPairId':pair,'requestedText':'请按本次立场核查条款并给出修改文本',
                                    'scope':'CURRENT_TASK'}],
            'feedbackEdges':[],'observations':[],
            'attempts':[{'id':f'a{i}','pairId':pair,'fragmentId':f'f{i}','requirementVersion':1,
                         'deliveryStatus':'TEXT_PRESENT','technicalStatus':'COMPLETED','businessOutcome':'UNKNOWN'}],
            'unresolved':[]}


class WorkflowContractTests(unittest.TestCase):
    def test_complementary_steps_cluster_at_workflow_level(self):
        traces=[trace(1),trace(2)]
        payload,catalog=workflow.prepare(traces)
        output={'sourceHash':payload['sourceHash'],
            'frames':[{'id':f'f{i}','traceId':f't{i}','goal':'按立场审阅并修订合同',
                       'inputContract':['立场','合同'],'outputContract':['审阅意见','建议文本'],
                       'processSketch':['确认立场','风险审阅','局部修订'],'conditions':[],'parameters':['立场'],
                       'methodIds':[f'm{i}']} for i in (1,2)],
            'methods':[{'id':f'm{i}','frameId':f'f{i}','action':action,'inputs':['合同'],'outputs':['文本'],
                        'conditions':[],'parameters':['立场'],'completionCheck':'逐项核对','evidenceRefs':[f'e{i}'],
                        'evidenceKind':'USER_REQUIREMENT','outcome':'UNKNOWN','decisionHint':'INCLUDE','reason':'用户要求'}
                       for i,action in ((1,'确认本次角色'),(2,'根据新增约束局部修订'))],
            'relations':[{'left':'f1','right':'f2','kind':'SHARE_CORE',
                          'sharedSteps':['确认角色','审阅风险'],'condition':'角色可变','reason':'相同处理流程'}]}
        extracted=workflow.validate_extract(output,payload,catalog)
        groups,routes=workflow.clusters(extracted,traces,catalog)
        self.assertEqual(groups,[['f1','f2']])
        self.assertEqual(routes['f1'],('NEW',None))
        view=workflow.merge_input(extracted,groups,routes,payload)
        merged={'sourceHash':view['sourceHash'],
                'workflows':[{'frameIds':['f1','f2'],'title':'合同审阅与局部修订','trigger':'用户要求审阅合同',
                              'inputs':['合同','本次立场'],'steps':[{'id':'s1','methodIds':['m1'],'action':'确认本次角色','completionCheck':'角色确认'},
                              {'id':'s2','methodIds':['m2'],'action':'依据变化局部修订','completionCheck':'文本核对'}],
                              'outputs':['建议文本'],'limitations':['业务结果未知'],'includedMethodIds':['m1','m2']}],
                'ledger':[{'methodId':m,'disposition':'INCLUDED','reason':'有用户要求'} for m in ('m1','m2')]}
        self.assertEqual(len(workflow.validate_merge(merged,view,extracted)[0]),1)

    def test_holdout_and_unknown_use_are_not_learning_inputs(self):
        with self.assertRaises(ValueError):workflow.prepare([trace(1,'holdout')])
        t=trace(1);t['initializationEvidence']=[{'status':'UNKNOWN'}]
        payload,catalog=workflow.prepare([t])
        output={'sourceHash':payload['sourceHash'],
                'frames':[{'id':'f1','traceId':'t1','goal':'审阅','inputContract':['合同'],'outputContract':['审阅意见'],
                           'processSketch':['确认立场'],'conditions':[],'parameters':[],'methodIds':['m1']}],
                'methods':[{'id':'m1','frameId':'f1','action':'确认立场','inputs':['用户立场'],'outputs':['确认结果'],
                            'conditions':[],'completionCheck':'核对用户确认','evidenceRefs':['e1'],'decisionHint':'INCLUDE'}], 'relations':[]}
        extracted=workflow.validate_extract(output,payload,catalog)
        _,routes=workflow.clusters(extracted,[t],catalog)
        self.assertEqual(routes['f1'][0],'DEFER')

    def test_creator_requires_approved_method_and_keeps_private_text_out(self):
        body='---\nname: contract-review\ndescription: 根据当前立场审阅协议并给出建议文本。\n---\n'
        body+='\n<!-- SKILLSLOOP_METHOD:m1 -->\n先确认立场，再核对条款。\n## 市场信息\n'
        body+='\n'.join('### '+h+'\n示例内容。' for h in HEADINGS)
        files=[{'path':'SKILL.md','content':body}]
        self.assertEqual(verify_files(files,['m1'])['status'],'PASS')
        with self.assertRaises(ValueError):verify_files(files,['m1','m2'])
        secret='某企业内部谈判材料与客户标识不得进入可分发技能文件，且不能复制历史完整对话。'+('这些案例专属细节应始终保留在受控来源中。'*3)
        with self.assertRaises(ValueError):verify_files([{'path':'SKILL.md','content':body+secret}],['m1'],[secret])

    def extraction(self, t=None, method_id='m1', frame_id='f1'):
        t=t or trace(1)
        payload,catalog=workflow.prepare([t])
        output={'sourceHash':payload['sourceHash'],
                'frames':[{'id':frame_id,'traceId':t['id'],'goal':'按用户立场审阅',
                           'inputContract':['合同文本'],'outputContract':['审阅建议'],
                           'processSketch':['确认立场','核对条款'],'conditions':[],'parameters':[],
                           'methodIds':[method_id]}],
                'methods':[{'id':method_id,'frameId':frame_id,'action':'先确认当前用户立场',
                            'inputs':['用户要求'],'outputs':['确认的当前立场'],'conditions':[],
                            'completionCheck':'检查立场是否已明确','evidenceRefs':['e1'],
                            'evidenceKind':'USER_REQUIREMENT','outcome':'UNKNOWN','decisionHint':'INCLUDE'}],
                'relations':[]}
        return payload,catalog,output

    def test_model_ids_are_aliased_without_mutating_saved_response(self):
        payload,catalog,output=self.extraction(method_id='m1.1',frame_id='frame / 角色')
        raw=deepcopy(output)
        first=workflow.validate_extract(output,payload,catalog)
        second=workflow.validate_extract(output,payload,catalog)
        method=first['methods'][0];frame=first['frames'][0]
        self.assertRegex(method['id'],r'^m_[a-f0-9]+$')
        self.assertEqual(frame['methodIds'],[method['id']])
        self.assertEqual(method['frameId'],frame['id'])
        self.assertEqual(first['aliases'],second['aliases'])
        self.assertEqual(output,raw)

    def test_source_authority_downgrades_unverified_model_success(self):
        payload,catalog,output=self.extraction()
        output['methods'][0].update(evidenceKind='VERIFIED_CHECK',outcome='SUCCESS')
        method=workflow.validate_extract(output,payload,catalog)['methods'][0]
        self.assertEqual(method['evidenceKind'],'USER_REQUIREMENT')
        self.assertEqual(method['outcome'],'UNKNOWN')
        self.assertEqual(method['evidenceAssessment']['claimWarnings'],
                         ['UNSUPPORTED_EVIDENCE_KIND','UNVERIFIED_OUTCOME_CLAIM'])

    def test_method_cannot_borrow_evidence_from_another_trace(self):
        payload,catalog=workflow.prepare([trace(1),trace(2)])
        self.assertEqual(payload['traces'][0]['allowedEvidenceIds'],['e1'])
        self.assertEqual(payload['traces'][1]['allowedEvidenceIds'],['e2'])
        _,_,output=self.extraction()
        output['sourceHash']=payload['sourceHash']
        workflow.validate_extract(output,payload,catalog)
        for refs in (['e2'],['e1','e2']):
            invalid=deepcopy(output)
            invalid['methods'][0]['evidenceRefs']=refs
            saved=deepcopy(invalid)
            with self.subTest(refs=refs),self.assertRaisesRegex(ValueError,'本来源证据'):
                workflow.validate_extract(invalid,payload,catalog)
            self.assertEqual(invalid,saved)

    def test_full_evidence_and_execution_references_survive_projection(self):
        t=trace(1);quote='甲'*1200+'末尾的真正要求'
        t['requirementTimeline'][0]['requestedText']=quote
        t['attempts'][0]['executionRefs']={'runId':'run1','toolEventIds':['tool1'],
            'rawToolOutput':'never expose','artifacts':[{'path':'outputs/review.md','sha256':'abc','content':'never expose'}],
            'checks':[{'id':'check1','status':'PASS','scope':'TECHNICAL','output':'never expose'}]}
        payload,catalog=workflow.prepare([t])
        self.assertEqual(catalog['e1']['text'],quote)
        execution=payload['traces'][0]['attempts'][0]['executionRefs']
        self.assertEqual(execution['runId'],'run1')
        self.assertEqual(execution['toolEventIds'],['tool1'])
        self.assertEqual(execution['checks'][0]['id'],'check1')
        self.assertNotIn('never expose',str(execution))
        t['requirementTimeline'][0]['requestedText']='甲'*110001
        with self.assertRaisesRegex(ValueError,'STAGE4_INPUT_BUDGET'):workflow.prepare([t])

    def test_workflow_required_content_and_unknown_boundary(self):
        payload,catalog,output=self.extraction()
        extracted=workflow.validate_extract(output,payload,catalog)
        view=workflow.merge_input(extracted,[['f1']],{'f1':('NEW',None)},payload)
        raw={'sourceHash':view['sourceHash'],'workflows':[{'frameIds':['f1'],'title':'立场确认',
             'trigger':'审阅前','inputs':['用户要求'],'outputs':['明确立场'],
             'steps':[{'id':'s1','methodIds':['m1'],'action':'确认当前立场','completionCheck':'检查是否明确'}],
             'limitations':['仅为文本流程'],'includedMethodIds':['m1']}],
             'ledger':[{'methodId':'m1','disposition':'INCLUDED','reason':'用户要求'}]}
        approved,_=workflow.validate_merge(raw,view,extracted)
        self.assertEqual(approved[0]['businessOutcome'],'UNKNOWN')
        self.assertTrue(any('UNKNOWN' in x for x in approved[0]['limitations']))
        self.assertEqual(raw['workflows'][0]['limitations'],['仅为文本流程'])
        for key in ('inputs','outputs','limitations'):
            invalid=deepcopy(raw);invalid['workflows'][0][key]=[]
            with self.subTest(key=key),self.assertRaises(ValueError):workflow.validate_merge(invalid,view,extracted)


if __name__=='__main__':unittest.main()
