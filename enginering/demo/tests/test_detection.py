import json
import tempfile
import unittest
from pathlib import Path

from skilldemo.core import Loop
from skilldemo.detection import prepare, validate
from skilldemo.runtime import ReplayAgent


class ScriptedDetector(ReplayAgent):
    """Structured model response fixture; exercises host stitching, not semantics."""
    mode = 'openclaw'

    def __init__(self): self.detect_calls = 0

    def run(self, purpose, payload, workspace):
        if purpose != 'detect': return super().run(purpose, payload, workspace)
        self.detect_calls += 1
        anchor = payload['messages'][0]
        result = {'sourceHash':payload['sourceHash'],
            'seeds':[{'key':'t1','anchor':anchor['id'],'goal':'审查合同重大风险',
                'object':'合同','deliverable':'必要修改建议',
                'evidenceQuote':anchor['user'][:8]}],
            'assignments':[{'message':m['id'],'kind':'TASK_ANCHOR' if i == 0 else 'RELATED_HINT',
                'task':'t1'} for i,m in enumerate(payload['messages'])]}
        return {'text':json.dumps(result,ensure_ascii=False),'usage':{'total':100},
                'modelRequestStarts':1,'status':'ok','mode':self.mode}


class DetectionTests(unittest.TestCase):
    def test_source_coverage_and_quote_are_required(self):
        turns = [{'id':'a','user':'从委托方角度审查危废协议','assistant':'','status':'COMPLETED'},
                 {'id':'b','user':'实际还有第二厂区','assistant':'','status':'COMPLETED'}]
        payload, aliases, prior = prepare('alice','s',turns,[])
        proposal = {'sourceHash':payload['sourceHash'],
            'seeds':[{'key':'t1','anchor':'u1','goal':'审查协议','evidenceQuote':'委托方角度'}],
            'assignments':[{'message':'u1','kind':'TASK_ANCHOR','task':'t1'},
                           {'message':'u2','kind':'RELATED_HINT','task':'t1'}]}
        self.assertEqual(len(validate(proposal,payload,aliases,prior)[1]),2)
        omitted = {**proposal,'assignments':proposal['assignments'][:1]}
        with self.assertRaises(ValueError): validate(omitted,payload,aliases,prior)
        bad = {**proposal,'seeds':[{**proposal['seeds'][0],'evidenceQuote':'模型编造'}]}
        with self.assertRaises(ValueError): validate(bad,payload,aliases,prior)

    def test_llm_seed_and_host_join_without_replyto(self):
        with tempfile.TemporaryDirectory() as root:
            agent = ScriptedDetector()
            loop = Loop(Path(root),agent,settle_seconds=0,task_detection=True)
            for session, lines in [('supplier',['审查供应商协议重大风险','考虑买方接受程度','改成折中条款','只给条款文本']),
                                   ('client',['从委托方角度审查危废协议','这条是排他条款','实际还有第二厂区','按此事实怎么改'])]:
                for i, line in enumerate(lines):
                    loop.import_turn('alice',{'session':session,'requestId':f'{session}-{i}',
                        'user':line,'assistant':'已记录','status':'COMPLETED'})
            self.assertEqual(loop.snapshot('alice')['traces'],[])
            loop.tick()
            state = loop.snapshot('alice')
            self.assertEqual(agent.detect_calls,2)
            self.assertEqual(sorted(len(t['turns']) for t in state['traces']),[4,4])
            self.assertTrue(all(t['verification']=='UNKNOWN' for t in state['traces']))
            self.assertEqual(len(state['detections']),2)
            loop.tick()
            self.assertEqual(agent.detect_calls,2)

    def test_bad_model_output_never_falls_back_to_keywords(self):
        class InvalidDetector(ScriptedDetector):
            def run(self,purpose,payload,workspace):
                result = super().run(purpose,payload,workspace)
                if purpose == 'detect':
                    data = json.loads(result['text']);data['assignments']=[]
                    result['text']=json.dumps(data)
                return result
        with tempfile.TemporaryDirectory() as root:
            agent=InvalidDetector()
            loop=Loop(Path(root),agent,settle_seconds=0,task_detection=True)
            loop.import_turn('alice',{'session':'s','user':'请整理报告','assistant':'已完成'})
            loop.tick()
            state=loop.snapshot('alice')
            self.assertEqual(state['traces'],[])
            self.assertEqual(state['detections'][0]['status'],'INVALID')
            loop.tick()
            self.assertEqual(agent.detect_calls,1)

    def test_new_live_turn_reuses_validated_prefix(self):
        class FollowupDetector(ScriptedDetector):
            def run(self,purpose,payload,workspace):
                if purpose == 'detect' and payload['priorTasks']:
                    self.detect_calls += 1
                    return {'text':json.dumps({'sourceHash':payload['sourceHash'],
                        'seeds':[], 'assignments':[{'message':m['id'],
                            'kind':'RELATED_HINT','task':payload['priorTasks'][-1]['key']}
                            for m in payload['messages']]},ensure_ascii=False),
                        'usage':{'total':50},'modelRequestStarts':1,'status':'ok','mode':self.mode}
                return super().run(purpose,payload,workspace)
        with tempfile.TemporaryDirectory() as root:
            agent = FollowupDetector()
            loop = Loop(Path(root),agent,settle_seconds=0,task_detection=True)
            loop.import_turn('alice',{'session':'s','requestId':'1','user':'审查质量协议','assistant':'初稿'})
            loop.tick()
            self.assertEqual(agent.detect_calls,1)
            loop.import_turn('alice',{'session':'s','requestId':'2','user':'只改重大风险条款','assistant':'修订'})
            loop.tick()
            state=loop.snapshot('alice')
            self.assertEqual(agent.detect_calls,2)
            self.assertEqual(len(state['detections']),2)
            self.assertEqual([len(t['turns']) for t in state['traces']],[2])
            loop.tick()
            self.assertEqual(agent.detect_calls,2)


if __name__ == '__main__': unittest.main()
