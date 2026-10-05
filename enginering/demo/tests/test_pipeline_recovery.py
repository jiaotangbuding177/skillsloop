import json
import os
import tempfile
import unittest
from unittest.mock import patch

from skilldemo.core import Loop
from skilldemo import request_cache, workflow_bridge, workflow
from skilldemo.server import scheduled_cycle
from test_front_stages import StructuredFixture, messages
from test_workflow import trace


class WorkflowFixture(StructuredFixture):
    def __init__(self, bad_merge=False):
        super().__init__()
        self.bad_merge = bad_merge

    def run(self, purpose, payload, workspace):
        if purpose not in ('workflow_extract','workflow_merge'):
            return super().run(purpose,payload,workspace)
        self.calls.append(purpose)
        if purpose == 'workflow_extract':
            out = {'sourceHash':payload['sourceHash'],
                'frames':[{'id':'f1','traceId':'t1','goal':'按立场审阅并修订合同',
                           'inputContract':['合同','立场'],'outputContract':['建议文本'],
                           'processSketch':['确认立场','审阅风险'],'conditions':[],'parameters':['立场'],
                           'methodIds':['m1']}],
                'methods':[{'id':'m1','frameId':'f1','action':'确认本次角色再核对条款',
                            'inputs':['合同','立场'],'outputs':['建议文本'],'conditions':[],
                            'parameters':['立场'],'completionCheck':'逐项核对','evidenceRefs':['e1'],
                            'evidenceKind':'USER_REQUIREMENT','outcome':'UNKNOWN',
                            'decisionHint':'INCLUDE','reason':'用户要求'}], 'relations':[]}
        else:
            out = {'sourceHash':payload['sourceHash'],
                'workflows':[{'frameIds':['f1'],'title':'按立场审阅合同','trigger':'用户要求审阅合同',
                              'inputs':['合同','立场'],'outputs':['建议文本'],'limitations':['业务结果未知'],
                              'includedMethodIds':['m1'],
                              'steps':[{'id':'s1','methodIds':['m1'],'action':'确认角色后核对条款',
                                        'completionCheck':'逐项核对'}]}],
                'ledger':[] if self.bad_merge else [{'methodId':'m1','disposition':'INCLUDED','reason':'用户要求'}]}
        return {'text':json.dumps(out,ensure_ascii=False),'usage':{'total':100},'modelRequestStarts':1}


class PipelineRecoveryTests(unittest.TestCase):
    def test_stop_on_failure_prevents_later_session_and_batch_dispatch(self):
        class FailFirst(StructuredFixture):
            def run(self,purpose,payload,workspace):
                self.calls.append(purpose)
                raise ValueError('fixed failed fixture; no retry')
        with tempfile.TemporaryDirectory() as root:
            agent=FailFirst();loop=Loop(root,agent,settle_seconds=0,stage_pipeline=True)
            loop.import_events('alice',messages('session-a'))
            loop.import_events('alice',messages('session-b'))
            result=loop.front.process('alice',stop_on_failure=True)
            self.assertEqual(len(result['sessions']),1)
            self.assertEqual(agent.calls,['detect_pairs'])
            self.assertEqual(len(loop.snapshot('alice')['stageStatus']),1)
        with tempfile.TemporaryDirectory() as root:
            agent=FailFirst();loop=Loop(root,agent,stage_pipeline=True)
            with loop.store.tx() as db:
                for i in range(1,10):loop.store.put(db,'trace',{**trace(i),'updated':0})
            self.assertEqual(workflow_bridge.discover(loop,'alice',stop_on_failure=True),[])
            self.assertEqual(agent.calls,['workflow_extract'])
            with loop.store.tx() as db:
                statuses=loop.store.rows(db,'stage4_status','alice')
                self.assertEqual(len(statuses),1)
                self.assertEqual(len(statuses[0]['traceIds']),8)

    def test_invalid_front_output_never_ready_and_retry_preserves_original(self):
        class Bad(StructuredFixture):
            bad = True
            def run(self,purpose,payload,workspace):
                result = super().run(purpose,payload,workspace)
                if purpose == 'detect_pairs' and self.bad:
                    output=json.loads(result['text']);output['annotations']=[]
                    result['text']=json.dumps(output)
                return result
        with tempfile.TemporaryDirectory() as root:
            agent=Bad();loop=Loop(root,agent,settle_seconds=0,stage_pipeline=True)
            loop.import_events('alice',messages())
            loop.run_stages('alice');loop.run_stages('alice')
            with loop.store.tx() as db:
                attempts=loop.store.rows(db,'front_analysis','alice')
                index=loop.store.rows(db,'front_analysis_request','alice')[0]
            self.assertEqual(agent.calls,['detect_pairs'])
            self.assertEqual(attempts[0]['state'],'FAILED')
            self.assertEqual(index['state'],'FAILED')
            old_run=attempts[0]['id']
            agent.bad=False
            request_cache.retry_request(loop,'alice','front_analysis',index['id'],'predeclared one retry',2)
            state=loop.run_stages('alice')['sessions'][0]
            self.assertEqual(state['stage3'],'RECOVERED',state)
            with loop.store.tx() as db:
                self.assertEqual(loop.store.get(db,'front_analysis',old_run)['state'],'FAILED')
                index=loop.store.get(db,'front_analysis_request',index['id'])
                self.assertEqual(index['attemptCount'],2)
                self.assertNotEqual(index['attempts'][0],index['attempts'][1])
            with self.assertRaises(ValueError):
                request_cache.retry_request(loop,'alice','front_analysis',index['id'],'third forbidden',2)

    def test_recovery_validation_precedes_ready(self):
        class BadRecovery(StructuredFixture):
            def run(self,purpose,payload,workspace):
                result=super().run(purpose,payload,workspace)
                if purpose=='recover_trace':
                    output=json.loads(result['text']);output['memberships']=[]
                    result['text']=json.dumps(output)
                return result
        with tempfile.TemporaryDirectory() as root:
            agent=BadRecovery();loop=Loop(root,agent,settle_seconds=0,stage_pipeline=True)
            loop.import_events('alice',messages());loop.run_stages('alice');loop.run_stages('alice')
            with loop.store.tx() as db:
                attempts=loop.store.rows(db,'front_analysis','alice')
            self.assertEqual([(a['purpose'],a['state']) for a in attempts],
                             [('detect_pairs','READY'),('recover_trace','FAILED')])
            self.assertEqual(agent.calls,['detect_pairs','recover_trace'])

    def test_stage4_budget_is_resumable_without_learning_decision(self):
        with tempfile.TemporaryDirectory() as root:
            agent=WorkflowFixture();loop=Loop(root,agent,daily_limit=0,stage_pipeline=True)
            with loop.store.tx() as db:loop.store.put(db,'trace',{**trace(1),'updated':0})
            self.assertEqual(loop.discover('alice'),[])
            with loop.store.tx() as db:
                self.assertFalse(loop.store.get(db,'trace','t1').get('decision'))
                index=loop.store.rows(db,'workflow_analysis_request','alice')[0]
                self.assertEqual(index['state'],'WAITING_BUDGET');self.assertEqual(index['attemptCount'],0)
            self.assertEqual(agent.calls,[])
            loop.daily_limit=2
            created=loop.discover('alice')
            self.assertEqual(len(created),1,loop.snapshot('alice'))
            self.assertEqual(created[0]['status'],'QUEUED')
            self.assertEqual(loop.discover('alice'),[])
            self.assertEqual(agent.calls,['workflow_extract','workflow_merge'])
            self.assertEqual(len(loop.snapshot('alice')['candidates']),1)

    def test_invalid_merge_not_cached_ready_or_permanent_trace_decision(self):
        with tempfile.TemporaryDirectory() as root:
            agent=WorkflowFixture(True);loop=Loop(root,agent,stage_pipeline=True)
            with loop.store.tx() as db:loop.store.put(db,'trace',{**trace(1),'updated':0})
            loop.discover('alice');loop.discover('alice')
            with loop.store.tx() as db:
                self.assertFalse(loop.store.get(db,'trace','t1').get('decision'))
                self.assertEqual(loop.store.rows(db,'stage4_status','alice')[0]['state'],'FAILED')
                index=next(x for x in loop.store.rows(db,'workflow_analysis_request','alice') if x['purpose']=='workflow_merge')
                old=loop.store.get(db,'workflow_analysis',index['attempts'][0])
                self.assertEqual(old['status'],'FAILED')
            self.assertEqual(agent.calls,['workflow_extract','workflow_merge'])
            agent.bad_merge=False
            request_cache.retry_request(loop,'alice','workflow_analysis',index['id'],'predeclared retry',2)
            self.assertEqual(len(loop.discover('alice')),1)
            self.assertEqual(agent.calls,['workflow_extract','workflow_merge','workflow_merge'])
            with loop.store.tx() as db:self.assertEqual(loop.store.get(db,'workflow_analysis',old['id'])['status'],'FAILED')

    def test_provider_and_prompt_are_part_of_request_identity(self):
        with tempfile.TemporaryDirectory() as root:
            agent=StructuredFixture();loop=Loop(root,agent,settle_seconds=0,stage_pipeline=True)
            loop.import_events('alice',messages());loop.run_stages('alice')
            with patch.dict(os.environ,{'DEMO_BASE_URL':'https://changed.example.invalid/v1'}):
                loop.run_stages('alice')
            self.assertEqual(agent.calls,['detect_pairs','recover_trace','detect_pairs','recover_trace'])
            with loop.store.tx() as db:
                rows=loop.store.rows(db,'front_analysis_request','alice')
                self.assertEqual(len(rows),4)
                self.assertTrue(all(r['configurationHash'] for r in rows))

    def test_interrupted_request_requires_explicit_retry(self):
        with tempfile.TemporaryDirectory() as root:
            agent=StructuredFixture();loop=Loop(root,agent,settle_seconds=0,stage_pipeline=True)
            payload={'sourceHash':'fake'}
            cfg=request_cache.configuration(loop,'detect_pairs')
            from skilldemo.runtime import digest
            rid='detect_pairs-'+digest(['alice',payload,cfg])[:24]
            with loop.store.tx() as db:
                loop._reserve(db,'alice','detect_pairs',rid,payload)
                loop.store.put(db,'front_analysis_request',{'id':rid,'owner':'alice','state':'RUNNING',
                    'purpose':'detect_pairs','attemptCount':1,'attempts':[rid]})
            with self.assertRaises(ValueError):request_cache.retry_request(loop,'alice','front_analysis',rid,'retry',2)
            loop.recover_interrupted()
            authorized=request_cache.retry_request(loop,'alice','front_analysis',rid,'process interrupted; one retry',2)
            self.assertEqual(authorized['state'],'RETRY_AUTHORIZED')
            self.assertEqual(agent.calls,[])

    def test_paused_scheduler_does_not_dispatch_any_stage(self):
        calls=[]
        scheduled_cycle({'autoLearn':False},lambda:calls.append('cycle'))
        self.assertEqual(calls,[])
        scheduled_cycle({'autoLearn':True},lambda:calls.append('cycle'))
        self.assertEqual(calls,['cycle'])


if __name__=='__main__':unittest.main()
