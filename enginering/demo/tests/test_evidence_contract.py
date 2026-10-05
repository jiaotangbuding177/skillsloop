import unittest
from skilldemo import evidence, intake


class EvidenceContractTests(unittest.TestCase):
    def pair(self):
        rows = [dict(id='u',sessionId='s',role='user',content='取消订单A',sourceOrder=1),
                dict(id='a',sessionId='s',role='assistant',content='已完成。',sourceOrder=2),
                dict(id='t',sessionId='s',role='tool',content='取消失败：状态不允许',sourceOrder=3,
                     responseTo='u',callId='c1',toolName='cancel_order',arguments={'order_id':'A'},
                     result={'error':'status_not_allowed'},executionStatus='FAILED')]
        events=[intake.event('alice',r,'generation',i) for i,r in enumerate(rows,1)]
        return intake.assemble(events,{'status':'KNOWN_NONE','basis':'fixture'})[0][0]

    def test_call_result_and_raw_failure_survive(self):
        rows=evidence.catalog([self.pair()])
        tool=next(x for x in rows if x['kind']=='TOOL_RESULT')
        self.assertEqual(tool['metadata']['callId'],'c1')
        self.assertEqual(tool['metadata']['executionStatus'],'FAILED')
        self.assertIn('status_not_allowed',tool['text'])
        self.assertEqual(tool['ref']['sourceId'],'t')

    def test_evaluation_is_sparse_scoped_and_allowlisted(self):
        v=dict(id='v1',source='public_checker',scope='TASK',targetIds=['u'],
               criterion='目标状态验收',result='FAILURE',outcomeType='BUSINESS',evidenceIds=['t'])
        clean=evidence.normalize_evaluations([v])
        self.assertEqual(clean[0]['scope'],'TASK')
        self.assertEqual(clean[0]['status'],'FAILURE')
        self.assertFalse(clean[0]['verified'])
        for extra in ('reward_info','actions','hidden_goal','gold_answer'):
            with self.subTest(extra=extra),self.assertRaises(ValueError):
                evidence.normalize_evaluations([{**v,extra:'gold'}])
        self.assertEqual(evidence.normalize_evaluations([]),[])

    def test_context_has_provenance_and_changes_catalog(self):
        c=[dict(id='p1',kind='POLICY',text='取消必须满足订单状态条件',source='public-policy-v1')]
        first=evidence.catalog([self.pair()],evidence.normalize_context(c))
        c[0]['text']='取消必须取得用户确认'
        second=evidence.catalog([self.pair()],evidence.normalize_context(c))
        self.assertNotEqual(first,second)
        with self.assertRaises(ValueError):evidence.normalize_context([{'id':'p','text':'无来源'}])

    def test_legacy_receipt_boolean_is_not_business_success(self):
        p=self.pair();p['toolEvents'][0]['receipt']=True
        rows=evidence.catalog([p])
        self.assertTrue(all(x['metadata'].get('outcomeType')!='BUSINESS' for x in rows if x['kind'].startswith('TOOL')))

    def test_checks_keep_expected_actual_without_invented_pass(self):
        p=self.pair();p['checks']=[dict(name='输出文件',expected='存在',actual='缺失')]
        row=next(x for x in evidence.catalog([p]) if x['kind']=='CHECK')
        self.assertIn('缺失',row['text'])
        self.assertEqual(row['metadata']['status'],'UNKNOWN')

    def test_verified_evidence_requires_boolean_and_nonempty_basis(self):
        v=dict(id='v1',source='checker',scope='TASK',targetIds=['u'],criterion='公开检查',
               status='PASS',verified=True,verificationBasis=' ')
        with self.assertRaises(ValueError):evidence.normalize_evaluations([v])
        p=self.pair();p['checks']=[dict(id='check-1',status='PASS',verified='false',verificationBasis='checker')]
        with self.assertRaises(ValueError):evidence.catalog([p])


if __name__=='__main__':unittest.main()
