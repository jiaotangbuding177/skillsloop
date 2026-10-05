import tempfile
import unittest
import json
from copy import deepcopy
from skilldemo.core import Loop
from skilldemo.runtime import ReplayAgent
from skilldemo import pair_detection, recovery


def messages(session='s'):
    return [dict(id='u1',sessionId=session,role='user',content='审查合同甲',sourceOrder=1,status='done'),
            dict(id='a1',sessionId=session,role='assistant',content='第一版建议',sourceOrder=2,status='done'),
            dict(id='u2',sessionId=session,role='user',content='只给文本',sourceOrder=3,status='done'),
            dict(id='a2',sessionId=session,role='assistant',content='修订后的文本',sourceOrder=4,status='done')]


class StructuredFixture(ReplayAgent):
    """Predefined replies test the host, not semantic model accuracy."""
    def __init__(self, multi=False): self.calls=[]; self.multi=multi

    def run(self,purpose,payload,workspace):
        self.calls.append(purpose)
        if purpose=='detect_pairs':
            seeds=[dict(key='t1',anchor='q1:f1',goal='审查合同甲',object='合同甲',deliverable='文本',constraints=[])]
            annotations=[]
            for i,p in enumerate(payload['pairs']):
                parts=p['user'].split('；') if self.multi else [p['user']]
                fs=[]
                for j,part in enumerate(parts):
                    task='t'+str(j+1)
                    if j and i==0:seeds.append(dict(key=task,anchor=f'q1:f{j+1}',goal='写通知',object='通知',deliverable='文本',constraints=[]))
                    fs.append(dict(id='f'+str(j+1),quote=part,intent=part,kind='OPEN' if i==0 else 'CONTINUE',task=task,alternatives=[],references=[],uncertainty=''))
                annotations.append(dict(pair=p['id'],fragments=fs))
            out=dict(sourceHash=payload['sourceHash'],seeds=seeds,annotations=annotations)
        elif purpose=='recover_trace':
            fs=payload['fragments']; bypair={p['id']:{**p,'assistant':''.join(s['text'] for s in p['evidenceSpans'] if s['side']=='assistant')} for p in payload['pairs']}
            members=[dict(fragment=f['id'],status='CONFIRMED',task=f['candidates'][0],reason='fixture') for f in fs]
            obs=[dict(fragment=f['id'],kind='VISIBLE_TEXT',evidence=dict(pair=f['id'].split(':')[0],side='assistant',quote=bypair[f['id'].split(':')[0]]['assistant'].split('；')[int(f['id'].split(':f')[1])-1] if self.multi else bypair[f['id'].split(':')[0]]['assistant']),description='fixture text') for f in fs]
            relations=[]
            if len(bypair)>1:
                relations=[dict(source='q2:f1',target='q1:f1',kind='CHANGE_OUTPUT',delta='当前交付只给文本',scope='CURRENT_DELIVERY',evidence=[dict(pair='q2',side='user',quote=bypair['q2']['user']),dict(pair='q1',side='assistant',quote=bypair['q1']['assistant'])],explanation='fixture')]
            out=dict(sourceHash=payload['sourceHash'],memberships=members,relations=relations,observations=obs,uncertainties=[])
        else: return super().run(purpose,payload,workspace)
        return dict(text=json.dumps(out,ensure_ascii=False),usage={'total':100},modelRequestStarts=1,mode=self.mode)


class FrontContractTests(unittest.TestCase):
    def test_demo_exposes_event_intake(self):
        with tempfile.TemporaryDirectory() as root:
            loop = Loop(root, ReplayAgent())
            self.assertTrue(callable(getattr(loop, 'import_events', None)),
                            'Stage 1 must accept original events, not pre-labelled traces')

    def make(self,root,limit=20,multi=False):
        agent=StructuredFixture(multi)
        return Loop(root,agent,settle_seconds=0,daily_limit=limit,stage_pipeline=True),agent

    def test_intake_preserves_sources_and_duplicate_import(self):
        with tempfile.TemporaryDirectory() as root:
            loop,agent=self.make(root)
            self.assertEqual(loop.import_events('alice',messages())['addedEvents'],4)
            self.assertEqual(loop.import_events('alice',messages())['addedEvents'],0)
            state=loop.snapshot('alice')
            self.assertEqual(len(state['pairs']),2)
            self.assertEqual({s['sourceId'] for p in state['pairs'] for s in p['assistantSegments']},{'a1','a2'})
            self.assertEqual(agent.calls,[])
            changed=messages();changed[0]['content']='另一个正文'
            with self.assertRaises(ValueError):loop.import_events('alice',changed)
            self.assertEqual(loop.snapshot('alice')['pairs'][0]['user'],'审查合同甲')

    def test_explicit_late_response_and_orphan_not_latest(self):
        with tempfile.TemporaryDirectory() as root:
            loop,_=self.make(root)
            rows=messages()+[dict(id='late',sessionId='s',role='assistant',content='延迟修复',sourceOrder=5,responseTo='u1',status='done'),
                             dict(id='orphan',sessionId='s',role='tool',content='工具结果',sourceOrder=6,responseTo='missing')]
            loop.import_events('alice',rows)
            st=loop.snapshot('alice')
            p=next(p for p in st['pairs'] if p['sourceUserMessageId']=='u1')
            self.assertEqual([s['sourceId'] for s in p['assistantSegments']],['a1','late'])
            self.assertEqual(len(st['intakes'][0]['unassignedEvents']),1)

    def test_pipeline_handoff_unknown_cache_and_budget(self):
        with tempfile.TemporaryDirectory() as root:
            loop,agent=self.make(root,limit=1)
            loop.import_events('alice',messages(),initialization={'status':'KNOWN_NONE','basis':'fixture initialization'})
            r=loop.run_stages('alice')['sessions'][0]
            self.assertEqual(r['stage2'],'ANNOTATED');self.assertEqual(r['stage3'],'DEFERRED_OR_INVALID')
            self.assertEqual(agent.calls,['detect_pairs'])
            loop.daily_limit=2
            r=loop.run_stages('alice')['sessions'][0]
            self.assertEqual(r['stage3'],'RECOVERED')
            t=loop.snapshot('alice')['traces'][0]
            self.assertEqual(t['businessOutcome'],'UNKNOWN')
            self.assertEqual(t['feedbackEdges'][0]['kind'],'CHANGE_OUTPUT')
            self.assertEqual(len(t['requirementTimeline']),2)
            self.assertEqual(len(t['attempts']),2)
            self.assertEqual(t['sourceMessageIds'],['u1','a1','u2','a2'])
            loop.run_stages('alice');self.assertEqual(len(agent.calls),2)
            self.assertEqual(loop.discover('alice'),[])
            self.assertEqual(loop.snapshot('bob')['pairs'],[])

    def test_missing_content_and_split_isolation(self):
        with tempfile.TemporaryDirectory() as root:
            loop,agent=self.make(root)
            rows=messages();rows[1]['content']=None
            loop.import_events('alice',rows,'holdout')
            p=loop.snapshot('alice')['pairs'][0]
            self.assertEqual(p['contentStatus'],'MISSING_CONTENT')
            with self.assertRaises(ValueError):loop.import_events('alice',messages(),'generation')
            self.assertEqual(agent.calls,[])

    def test_multigoal_same_pair_gets_distinct_task_ids(self):
        with tempfile.TemporaryDirectory() as root:
            loop,agent=self.make(root,multi=True)
            rows=messages()[:2];rows[0]['content']='审查合同甲；另外写通知'
            rows[1]['content']='合同修改；会议通知'
            loop.import_events('alice',rows)
            status=loop.run_stages('alice')['sessions'][0]
            self.assertEqual(status['stage3'],'RECOVERED',status)
            traces=loop.snapshot('alice')['traces']
            self.assertEqual(len({t['id'] for t in traces}),2)
            self.assertTrue(all('；' not in t['turns'][0]['user'] for t in traces))

    def test_invalid_model_output_is_preserved_without_paid_retry(self):
        class Bad(StructuredFixture):
            def run(self,purpose,payload,workspace):
                r=super().run(purpose,payload,workspace)
                if purpose=='detect_pairs':
                    data=json.loads(r['text']);data['annotations']=[];r['text']=json.dumps(data)
                return r
        with tempfile.TemporaryDirectory() as root:
            agent=Bad();loop=Loop(root,agent,settle_seconds=0,stage_pipeline=True)
            loop.import_events('alice',messages());loop.run_stages('alice');loop.run_stages('alice')
            self.assertEqual(agent.calls,['detect_pairs']);self.assertEqual(loop.snapshot('alice')['traces'],[])

    def test_stale_inflight_result_cannot_overwrite_new_source(self):
        with tempfile.TemporaryDirectory() as root:
            loop,agent=self.make(root)
            original=agent.run
            def racing(purpose,payload,workspace):
                if purpose=='recover_trace':
                    loop.import_events('alice',[dict(id='u3',sessionId='s',role='user',content='新要求',sourceOrder=5)])
                return original(purpose,payload,workspace)
            agent.run=racing
            loop.import_events('alice',messages())
            r=loop.run_stages('alice')['sessions'][0]
            self.assertIn('SOURCE_CHANGED',r.get('error',''))
            self.assertEqual(loop.snapshot('alice')['traces'],[])

    def test_no_artificial_replyto_in_model_and_complete_assistant_text(self):
        with tempfile.TemporaryDirectory() as root:
            loop,agent=self.make(root)
            rows=messages();rows[2]['replyTo']='forged'
            loop.import_events('alice',rows)
            payload,*_=pair_detection.prepare(loop.snapshot('alice')['pairs'])
            self.assertNotIn('forged',str(payload))
            self.assertEqual(payload['pairs'][0]['assistant'],'第一版建议')

    def test_run_id_resolves_late_assistant_without_replyto(self):
        with tempfile.TemporaryDirectory() as root:
            loop,_=self.make(root)
            rows=messages();rows[0]['runId']='r1';rows[2]['runId']='r2'
            rows.append(dict(id='late',sessionId='s',role='assistant',content='迟到结果',runId='r1',sourceOrder=5))
            loop.import_events('alice',rows)
            p=next(p for p in loop.snapshot('alice')['pairs'] if p['sourceUserMessageId']=='u1')
            self.assertIn('late',p['sourceMessageIds'])

    def test_online_cannot_contaminate_imported_holdout(self):
        with tempfile.TemporaryDirectory() as root:
            loop,agent=self.make(root)
            loop.import_events('alice',messages(),'holdout')
            with self.assertRaises(ValueError):loop.chat('alice','s','继续任务')
            self.assertEqual(agent.calls,[])

    def test_multigoal_cannot_duplicate_whole_answer(self):
        class Duplicate(StructuredFixture):
            def run(self,purpose,payload,workspace):
                r=super().run(purpose,payload,workspace)
                if purpose=='recover_trace':
                    data=json.loads(r['text'])
                    for o in data['observations']:o['evidence']['quote']=''.join(s['text'] for s in payload['pairs'][0]['evidenceSpans'] if s['side']=='assistant')
                    r['text']=json.dumps(data)
                return r
        with tempfile.TemporaryDirectory() as root:
            agent=Duplicate(multi=True);loop=Loop(root,agent,settle_seconds=0,stage_pipeline=True)
            rows=messages()[:2];rows[0]['content']='审查合同甲；另外写通知';rows[1]['content']='合同修改；会议通知'
            loop.import_events('alice',rows)
            status=loop.run_stages('alice')['sessions'][0]
            self.assertEqual(status['stage3'],'DEFERRED_OR_INVALID')
            self.assertEqual(loop.snapshot('alice')['traces'],[])

    def test_explicit_missing_body_repair_preserves_history(self):
        with tempfile.TemporaryDirectory() as root:
            loop,_=self.make(root);rows=messages();rows[1]['content']=None
            loop.import_events('alice',rows)
            repair={**messages()[1],'repairMissingContent':True}
            loop.import_events('alice',[repair])
            self.assertTrue(all(p['contentStatus']=='READABLE' for p in loop.snapshot('alice')['pairs']))
            with loop.store.tx() as db:
                saved=loop.store.rows(db,'source_event_history','alice')
                self.assertEqual(len(saved),1);self.assertIsNone(saved[0]['content'])

    def test_initial_requirements_do_not_copy_final_seed_summary(self):
        with tempfile.TemporaryDirectory() as root:
            loop,_=self.make(root);rows=messages();rows[0]['content']='审查合同甲并交付Word文件'
            loop.import_events('alice',rows);loop.run_stages('alice')
            initial=loop.snapshot('alice')['traces'][0]['requirementTimeline'][0]
            self.assertEqual(initial['requestedText'],rows[0]['content'])
            self.assertNotIn('deliverable',initial)

    def test_span_protocol_multigoal_and_repeated_text_offsets(self):
        class Spans(StructuredFixture):
            def run(self,purpose,payload,workspace):
                r=super().run(purpose,payload,workspace)
                if purpose=='recover_trace':
                    data=json.loads(r['text']);spans=[s for s in payload['pairs'][0]['evidenceSpans'] if s['side']=='assistant']
                    for i,o in enumerate(data['observations']):o['evidence']={'span':spans[i]['id']}
                    r['text']=json.dumps(data)
                return r
        with tempfile.TemporaryDirectory() as root:
            agent=Spans(multi=True);loop=Loop(root,agent,settle_seconds=0,stage_pipeline=True)
            rows=messages()[:2];rows[0]['content']='审查合同甲；另外写通知';rows[1]['content']='合同修改；会议通知'
            loop.import_events('alice',rows)
            self.assertEqual(loop.run_stages('alice')['sessions'][0]['stage3'],'RECOVERED')
            pair=loop.snapshot('alice')['pairs'][0];pair['assistant']='done\ndone'
            spans=recovery.evidence_spans('q1',pair)
            payload={'pairs':[{'id':'q1','user':pair['user'],'evidenceSpans':spans}]}
            ref=pair_detection.quote_ref({'span':'q1:a2'},payload,{'q1':pair},{})
            self.assertEqual(ref['viewOffset'],5)
        with tempfile.TemporaryDirectory() as root:
            agent=Spans(multi=True);loop=Loop(root,agent,settle_seconds=0,stage_pipeline=True)
            rows=messages()[:2];rows[0]['content']='计算第一项；计算第二项';rows[1]['content']='142；42'
            loop.import_events('alice',rows)
            self.assertEqual(loop.run_stages('alice')['sessions'][0]['stage3'],'RECOVERED')

    def test_recovery_prompt_change_does_not_reuse_old_semantics(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root:
            loop,agent=self.make(root);loop.import_events('alice',messages());loop.run_stages('alice')
            with patch.object(recovery,'INSTRUCTIONS',recovery.INSTRUCTIONS+' changed semantics'):
                loop.run_stages('alice')
            self.assertEqual(agent.calls,['detect_pairs','recover_trace','recover_trace'])

    def test_selecting_direction_does_not_verify_its_realization(self):
        class Selection(StructuredFixture):
            def run(self,purpose,payload,workspace):
                r=super().run(purpose,payload,workspace)
                if purpose=='recover_trace':
                    data=json.loads(r['text']);data['relations'][0].update(kind='SELECT_OPTION',delta='',scope='CURRENT_TASK')
                    r['text']=json.dumps(data)
                return r
        with tempfile.TemporaryDirectory() as root:
            loop=Loop(root,Selection(),settle_seconds=0,stage_pipeline=True)
            rows=messages();rows[2]['content']='按中间方案处理'
            loop.import_events('alice',rows);loop.run_stages('alice')
            t=loop.snapshot('alice')['traces'][0]
            self.assertEqual(t['recoveryProgress'],'PROCESSED_WITH_UNCERTAINTIES')
            self.assertEqual(t['unresolved'][0]['status'],'OPTION_REALIZATION_UNVERIFIED')
            self.assertEqual(t['businessOutcome'],'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
