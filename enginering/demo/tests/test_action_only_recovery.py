"""Source position remains distinct from semantic attribution of real user actions."""
from copy import deepcopy
import unittest
from skilldemo import intake, relational
from test_relational import proposal


def prepare(action_text='', target_after=False, other_session=False):
    rows = [
        {'id':'u1','sessionId':'s','role':'user','sourceOrder':1,'runId':'r',
         'content':'请恢复手机上网，先分别检查账户漫游与手机漫游。'},
        {'id':'a1','sessionId':'s','role':'assistant','sourceOrder':2,'runId':'r',
         'content':'账户允许漫游，请打开手机数据漫游后复查。'},
        {'id':'u2','sessionId':'s','role':'user','sourceOrder':3,'runId':'r','content':action_text,
         'toolCalls':[{'id':'c1','name':'toggle_roaming','arguments':{},'objectIds':['phone']}]},
        {'id':'result','sessionId':'s','role':'tool','sourceOrder':4,'runId':'r','callId':'c1',
         'name':'toggle_roaming','content':'Data Roaming is now ON','executionStatus':'SUCCEEDED'},
    ]
    if target_after:
        rows.extend([{'id':'u3','sessionId':'s','role':'user','sourceOrder':5,'content':'现在写一份通知。'},
                     {'id':'a3','sessionId':'s','role':'assistant','sourceOrder':6,'content':'通知正文。'}])
    events=[intake.event('fixture',r,'generation',i) for i,r in enumerate(rows,1)]
    pairs,_=intake.assemble(events)
    if other_session:
        pairs[1]['session']='different-source-session'
    payload,aliases=relational.prepare(pairs)
    return payload,aliases


class ActionOnlyRecoveryTests(unittest.TestCase):
    def test_actual_user_action_is_attributed_without_fabricating_a_request(self):
        payload,aliases=prepare()
        raw=proposal(payload)
        call=next(e for e in payload['evidence'] if e['kind']=='TOOL_CALL')
        raw['executionBindings']=[{'evidenceId':call['id'],'fragment':'q1:f1'}]
        trace=relational.compile_result(raw,payload,aliases)['traces'][0]
        attempt=next(a for a in trace['attempts'] if a['kind']=='TOOL_CALL')
        self.assertEqual(attempt['actor'],'user')
        self.assertEqual(attempt['executionStatus'],'SUCCESS')
        self.assertNotEqual(attempt['originPairId'],attempt['pairId'])
        self.assertEqual(aliases['q2']['user'],'')
        self.assertEqual(len(raw['annotations']),1)
        source=next(s for s in trace['typedSources'] if s['id']==call['id'])
        self.assertEqual(source['ref']['pairId'],aliases['q2']['id'])
        self.assertEqual(source['semanticBinding']['basis'],'MODEL_TASK_ATTRIBUTION_OF_ACTION_ONLY_SOURCE')
        self.assertIn('u2',trace['sourceMessageIds'])

    def test_text_pair_keeps_strict_source_boundary(self):
        payload,aliases=prepare('顺便完成另一件事。')
        raw=proposal(payload)
        call=next(e for e in payload['evidence'] if e['kind']=='TOOL_CALL')
        raw['executionBindings']=[{'evidenceId':call['id'],'fragment':'q1:f1'}]
        with self.assertRaisesRegex(ValueError,'越明确来源pair'):
            relational.compile_result(raw,payload,aliases)

    def test_action_cannot_be_attributed_to_future_request(self):
        payload,aliases=prepare(target_after=True)
        raw=proposal(payload)
        call=next(e for e in payload['evidence'] if e['kind']=='TOOL_CALL')
        raw['executionBindings']=[{'evidenceId':call['id'],'fragment':'q3:f1'}]
        with self.assertRaisesRegex(ValueError,'越明确来源pair'):
            relational.compile_result(raw,payload,aliases)

    def test_ambiguous_action_stays_unbound(self):
        payload,aliases=prepare()
        recovered=relational.compile_result(proposal(payload),payload,aliases)
        self.assertFalse(any(a['kind']=='TOOL_CALL' for t in recovered['traces'] for a in t['attempts']))
        self.assertTrue(any(u['status']=='EXECUTION_BINDING_UNRESOLVED' for u in recovered['unresolved']))

    def test_action_cannot_cross_source_session(self):
        payload,aliases=prepare(other_session=True)
        raw=proposal(payload)
        call=next(e for e in payload['evidence'] if e['kind']=='TOOL_CALL')
        raw['executionBindings']=[{'evidenceId':call['id'],'fragment':'q1:f1'}]
        with self.assertRaisesRegex(ValueError,'越明确来源pair'):
            relational.compile_result(raw,payload,aliases)

    def test_orphan_receipt_cannot_be_bound_by_semantic_guessing(self):
        payload,aliases=prepare()
        raw=proposal(payload)
        result=next(e for e in payload['evidence'] if e['kind']=='TOOL_RESULT')
        result['ref'].update(pairId=None,originPairId=None,session='unrelated-session')
        raw['executionBindings']=[{'evidenceId':result['id'],'fragment':'q1:f1'}]
        with self.assertRaisesRegex(ValueError,'孤立工具证据'):
            relational.compile_result(raw,payload,aliases)
