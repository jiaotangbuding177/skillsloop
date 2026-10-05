from copy import deepcopy
import unittest
from skilldemo import relational
from test_relational import prepared, proposal


class SamePairOpenTests(unittest.TestCase):
    def test_redundant_open_keeps_model_task_and_raw_response_unchanged(self):
        payload,aliases=prepared([('请审阅协议。保留原编号。','按原编号给出审阅文本。')])
        raw=proposal(payload);first=raw['annotations'][0]['fragments'][0]
        second=deepcopy(first);first['quote']='请审阅协议。'
        second.update(id='f2',quote='保留原编号。')
        raw['annotations'][0]['fragments'].append(second)
        member=deepcopy(raw['memberships'][0]);member['fragment']='q1:f2'
        raw['memberships'].append(member)
        before=deepcopy(raw)
        recovered=relational.compile_result(raw,payload,aliases)
        self.assertEqual(raw,before)
        self.assertEqual(len(recovered['traces']),1)
        self.assertEqual(len(recovered['traces'][0]['members']),2)
        self.assertEqual(recovered['normalizationAudit'][0]['normalizedKind'],'CONTINUE')
        self.assertEqual(recovered['normalizationAudit'][0]['task'],'t1')

    def test_cross_pair_open_is_not_silently_repaired(self):
        payload,aliases=prepared([('审阅协议。','初稿。'),('继续审阅。','修订稿。')])
        raw=proposal(payload)
        raw['annotations'][1]['fragments'][0]['kind']='OPEN'
        with self.assertRaisesRegex(ValueError,'起点'):
            relational.compile_result(raw,payload,aliases)

    def test_missing_seed_anchor_is_not_invented(self):
        payload,aliases=prepared([('审阅协议。','初稿。')]);raw=proposal(payload)
        raw['seeds'][0]['anchor']='q1:f99'
        with self.assertRaisesRegex(ValueError,'起点'):
            relational.compile_result(raw,payload,aliases)

    def test_repair_note_does_not_rewrite_requirements(self):
        payload,aliases=prepared([('审阅协议。','编号1。'),('编号应保留2.1。','编号2.1。')])
        raw=proposal(payload)
        raw['relations']=[{'id':'repair','source':'q2:f1','options':[{
            'kind':'REVISES','target':'q1:f1','score':1,'reason':'明确编号修订',
            'delta':'编号应保留2.1','scope':'CURRENT_TASK',
            'evidence':[{'span':'q2:u1'},{'span':'q1:a1'}]}]}]
        recovered=relational.compile_result(raw,payload,aliases)
        edge=next(e for e in recovered['traces'][0]['typedRelations'] if e['type']=='REVISES')
        self.assertEqual(edge['delta'],'')
        self.assertEqual(edge['reportedDelta'],'编号应保留2.1')
        self.assertFalse(any(r.get('value')=='编号应保留2.1' for r in recovered['traces'][0]['requirements']))


if __name__=='__main__':unittest.main()
