"""Relation fixtures exercise host constraints, not model semantic accuracy."""
from copy import deepcopy
import json
import unittest
from unittest.mock import patch

from skilldemo import intake, relational


def pairs(texts):
    rows = []
    for i, (user, assistant) in enumerate(texts):
        rows.append(dict(id=f'u{i}', sessionId='s', role='user', content=user,
                         sourceOrder=2*i+1))
        if assistant is not None:
            rows.append(dict(id=f'a{i}', sessionId='s', role='assistant', content=assistant,
                             sourceOrder=2*i+2))
    events = [intake.event('alice', r, 'generation', i) for i, r in enumerate(rows)]
    return intake.assemble(events)[0]


def prepared(texts, catalog=None, evaluations=None):
    source = pairs(texts)
    with patch.object(relational, '_catalog', return_value=catalog or []):
        payload, aliases = relational.prepare(source, evaluations=evaluations or [])
    return payload, aliases


def span(payload, pair, side):
    return {'span': next(s['id'] for p in payload['pairs'] if p['id'] == pair
                         for s in p['evidenceSpans'] if s['side'] == side)}


def proposal(payload, assignments=None):
    assignments = assignments or {p['id']: 't1' for p in payload['pairs']}
    first = {}
    for p in payload['pairs']:
        if p['user'].strip():
            first.setdefault(assignments[p['id']], p['id'])
    seeds = [dict(key=k, anchor=q+':f1', goal='work '+k, object='object '+k,
                  deliverable='visible output', constraints=[])
             for k, q in first.items()]
    result = dict(sourceHash=payload['sourceHash'], seeds=seeds, annotations=[],
                  memberships=[], relations=[], observations=[], requirements=[],
                  executionBindings=[], evaluationBindings=[])
    for p in payload['pairs']:
        if not p['user'].strip():
            continue
        task = assignments[p['id']]
        result['annotations'].append(dict(pair=p['id'], fragments=[dict(
            id='f1', quote=p['user'], intent='current task',
            kind='OPEN' if first[task] == p['id'] else 'CONTINUE', task=task,
            alternatives=[], references=[], uncertainty='')]))
        result['memberships'].append(dict(fragment=p['id']+':f1', options=[dict(
            task=task, status='CONFIRMED', score=1, reason='fixture evidence')]))
        if any(s['side']=='assistant' and s['text'].strip() for s in p['evidenceSpans']):
            result['observations'].append(dict(fragment=p['id']+':f1', kind='VISIBLE_TEXT',
                evidence=span(payload,p['id'],'assistant'), description='visible delivery'))
    return result


class RelationalTests(unittest.TestCase):
    def test_host_links_unique_ordered_result_only_for_bound_call(self):
        source=pairs([('write the report','Written')])
        ref={'pairId':source[0]['id'],'runId':'run-1','sourceId':'write-1'}
        catalog=[dict(id='call',kind='TOOL_CALL',text='write',ref=ref,metadata={
            'callId':'write-1','name':'write','sourceOrder':8,'status':'SUCCEEDED'}),
            dict(id='result',kind='TOOL_RESULT',text='success',ref=ref,metadata={
                'callId':'write-1','name':'write','sourceOrder':9,'status':'SUCCEEDED'}),
            dict(id='read-call',kind='TOOL_CALL',text='read',ref=ref,metadata={
                'callId':'read-1','name':'read','sourceOrder':6,'status':'SUCCEEDED'}),
            dict(id='read-result',kind='TOOL_RESULT',text='body',ref=ref,metadata={
                'callId':'read-1','name':'read','sourceOrder':7,'status':'SUCCEEDED'})]
        with patch.object(relational,'_catalog',return_value=catalog):
            payload,aliases=relational.prepare(source)
        out=proposal(payload);out['executionBindings']=[dict(evidenceId='call',fragment='q1:f1')]
        result=relational.compile_result(out,payload,aliases);trace=result['traces'][0]
        attempt=next(a for a in trace['attempts'] if a['kind']=='TOOL_CALL')
        self.assertEqual(attempt['executionStatus'],'SUCCESS')
        self.assertEqual(attempt['businessOutcome'],'UNKNOWN')
        self.assertEqual(attempt['executionRefs']['toolEventIds'],['call','result'])
        link=trace['hostExecutionBindings'][0]
        self.assertEqual(link['basis'],'HOST_EXPLICIT_CALL_RESULT_LINK')
        self.assertEqual(link['attemptId'],attempt['id'])
        raw=next(s for s in trace['typedSources'] if s['id']=='result')
        self.assertEqual(raw['metadata']['status'],'SUCCEEDED')
        self.assertEqual(raw['ref']['attemptId'],attempt['id'])
        technical=next(e for e in trace['outcomeEvidence'] if e['sourceEvidenceId']=='result')
        self.assertEqual((technical['status'],technical['scope'],technical['outcomeType']),
                         ('SUCCESS','TECHNICAL','TECHNICAL'))
        self.assertFalse(technical['verified'])
        unresolved={u.get('evidenceId') for u in result['unresolved']}
        self.assertNotIn('result',unresolved)
        self.assertTrue({'read-call','read-result'} <= unresolved)
        self.assertEqual(catalog[1]['ref'],ref)  # The source catalog is never mutated.

    def test_host_result_link_defers_ambiguous_missing_and_cross_source_cases(self):
        source=pairs([('write the report','Written')])
        ref={'pairId':source[0]['id'],'runId':'run-1'}
        base=[dict(id='call',kind='TOOL_CALL',text='write',ref=ref,metadata={
            'callId':'write-1','name':'write','sourceOrder':8,'status':'SUCCEEDED'}),
            dict(id='result',kind='TOOL_RESULT',text='success',ref=ref,metadata={
                'callId':'write-1','name':'write','sourceOrder':9,'status':'SUCCEEDED'})]
        def change(row,section,key,value):row[section][key]=value
        cases=[('cross-pair',lambda c:change(c[1],'ref','pairId','other-pair')),
            ('cross-run',lambda c:change(c[1],'ref','runId','other-run')),
            ('missing-run',lambda c:change(c[0],'ref','runId',None)),
            ('missing-order',lambda c:change(c[1],'metadata','sourceOrder',None)),
            ('reverse-order',lambda c:change(c[1],'metadata','sourceOrder',7)),
            ('equal-order',lambda c:change(c[1],'metadata','sourceOrder',8)),
            ('bool-order',lambda c:change(c[0],'metadata','sourceOrder',True)),
            ('name-conflict',lambda c:change(c[1],'metadata','name','other')),
            ('duplicate-call',lambda c:c.append({**deepcopy(c[0]),'id':'call-2'})),
            ('duplicate-result',lambda c:c.append({**deepcopy(c[1]),'id':'result-2'}))]
        for name,mutate in cases:
            with self.subTest(name=name):
                catalog=deepcopy(base);catalog[1]['ref']=deepcopy(catalog[1]['ref']);mutate(catalog)
                with patch.object(relational,'_catalog',return_value=catalog):
                    payload,aliases=relational.prepare(source)
                out=proposal(payload);out['executionBindings']=[dict(evidenceId='call',fragment='q1:f1')]
                result=relational.compile_result(out,payload,aliases);trace=result['traces'][0]
                attempt=next(a for a in trace['attempts'] if a['kind']=='TOOL_CALL')
                self.assertEqual(attempt['executionStatus'],'UNKNOWN')
                self.assertEqual(trace['hostExecutionBindings'],[])
                self.assertTrue(any(u.get('evidenceId')=='result' for u in result['unresolved']))

    def test_host_result_link_does_not_rebind_explicit_result(self):
        ref={'pairId':'pair-1','runId':'run-1'}
        call=dict(id='call',kind='TOOL_CALL',ref=ref,metadata={
            'callId':'c','name':'write','sourceOrder':1})
        result=dict(id='result',kind='TOOL_RESULT',ref=ref,metadata={
            'callId':'c','name':'write','sourceOrder':2})
        self.assertIsNone(relational._explicit_call_result(call,{'call':call,'result':result},
            {'call':'q1:f1','result':'q1:f2'},'q1:f1'))

    def test_prompt_full_json_template_passes_real_compile_contract(self):
        # Replace source placeholders only; do not repair the template's semantics/shape.
        payload,aliases=prepared([('请写一则会议通知，用纯文本。','会议通知：周五开会。'),
                                  ('把这则通知的标题改为会议安排。','会议安排：周五开会。')])
        text=relational.OUTPUT_TEMPLATE
        replacements={'__INPUT_SOURCE_HASH__':payload['sourceHash'],
            '__Q1_USER__':payload['pairs'][0]['user'],'__Q2_USER__':payload['pairs'][1]['user'],
            '__Q1_USER_SPAN__':span(payload,'q1','user')['span'],
            '__Q2_USER_SPAN__':span(payload,'q2','user')['span'],
            '__Q1_ASSISTANT_SPAN__':span(payload,'q1','assistant')['span'],
            '__Q2_ASSISTANT_SPAN__':span(payload,'q2','assistant')['span']}
        for old,new in replacements.items():text=text.replace(old,new)
        output=json.loads(text)
        self.assertIn(relational.OUTPUT_TEMPLATE,relational.INSTRUCTIONS)
        self.assertTrue(all(isinstance(output[k],list) for k in (
            'seeds','annotations','memberships','relations','observations','requirements',
            'executionBindings','evaluationBindings')))
        self.assertEqual(sum(f['kind']=='OPEN' for a in output['annotations'] for f in a['fragments']),1)
        result=relational.compile_result(output,payload,aliases)
        self.assertEqual(len(result['traces']),1)
        self.assertEqual(len(result['traces'][0]['members']),2)
        self.assertTrue(result['traces'][0]['requirements'])

    def test_prompt_future_rule_and_current_application_keep_distinct_sources(self):
        payload,aliases=prepared([('请列本次审阅发现。','一、需要核实交付标准。'),
            ('以后每次报告都逐项列依据，并单列未确认项。\n请据此更新本次报告。','一、依据记录列发现与未确认项。')])
        user_spans=[s for s in payload['pairs'][1]['evidenceSpans'] if s['side']=='user']
        text=relational.SCOPE_OUTPUT_TEMPLATE
        replacements={'__INPUT_SOURCE_HASH__':payload['sourceHash'],
            '__Q1_USER__':payload['pairs'][0]['user'],'__Q2_USER__':payload['pairs'][1]['user'],
            '__FUTURE_RULE_SPAN__':user_spans[0]['id'],'__CURRENT_APPLICATION_SPAN__':user_spans[1]['id'],
            '__Q1_ASSISTANT_SPAN__':span(payload,'q1','assistant')['span'],
            '__Q2_ASSISTANT_SPAN__':span(payload,'q2','assistant')['span']}
        for old,new in replacements.items():text=text.replace(old,json.dumps(new,ensure_ascii=False)[1:-1])
        output=json.loads(text)
        trace=relational.compile_result(output,payload,aliases)['traces'][0]
        future=[r for r in trace['requirements'] if r['scope']=='FUTURE_TASKS']
        delivery=[r for r in trace['requirements'] if r['scope']=='CURRENT_DELIVERY']
        self.assertEqual(len(future),2);self.assertEqual(len(delivery),2)
        self.assertTrue(all(len(r['evidenceRefs'])==1 for r in future))
        self.assertTrue(all(len(r['evidenceRefs'])==2 for r in delivery))
        self.assertEqual(set(trace['attempts'][1]['requirementIds']),{r['id'] for r in delivery})
        self.assertTrue(all(r['id'] not in trace['attempts'][1]['requirementIds'] for r in future))
        self.assertEqual(trace['feedbackEdges'][0]['scope'],'CURRENT_DELIVERY')

    def test_late_feedback_remains_in_its_task(self):
        payload, aliases = prepared([('review document A','draft A'),
                                     ('write meeting notice','notice'),
                                     ('document A is wrong','corrected A')])
        out = proposal(payload, {'q1':'t1','q2':'t2','q3':'t1'})
        out['relations'] = [dict(id='r1',source='q3:f1',options=[dict(
            target='q1:f1',kind='REJECT_RESULT',score=1,delta='',scope='CURRENT_DELIVERY',
            evidence=[span(payload,'q3','user'),span(payload,'q1','assistant')],reason='explicit A')])]
        result = relational.compile_result(out,payload,aliases)
        trace = next(t for t in result['traces'] if len(t['members']) == 2)
        self.assertEqual(len(trace['feedbackEdges']),1)
        self.assertEqual(trace['feedbackEdges'][0]['targetPairId'],aliases['q1']['id'])
        self.assertEqual(trace['relationalSchema'],'relational-trace-v1')

    def test_dimension_replacement_inherits_and_retraction_removes(self):
        payload, aliases = prepared([('client; risks only','risks'),
                                     ('supplier; other requirements unchanged','supplier risks'),
                                     ('remove the stance constraint','risks')])
        out = proposal(payload)
        out['requirements'] = [
            dict(fragment='q1:f1',dimension='stance',op='ADD',value='client',evidence=[span(payload,'q1','user')]),
            dict(fragment='q1:f1',dimension='output',op='ADD',value='risks only',evidence=[span(payload,'q1','user')]),
            dict(fragment='q2:f1',dimension='stance',op='REPLACE',value='supplier',evidence=[span(payload,'q2','user')]),
            dict(fragment='q3:f1',dimension='stance',op='RETRACT',value=None,evidence=[span(payload,'q3','user')])]
        trace = relational.compile_result(out,payload,aliases)['traces'][0]
        self.assertEqual(trace['requirementTimeline'][1]['values'],{'stance':'supplier','output':'risks only'})
        self.assertEqual(trace['requirementTimeline'][2]['values'],{'output':'risks only'})
        self.assertEqual(trace['attempts'][1]['requirementVersion'],2)
        by_id={r['id']:r for r in trace['requirements']}
        self.assertEqual({by_id[r]['dimension'] for r in trace['attempts'][2]['requirementIds']},{'output'})
        stance=[r for r in trace['requirements'] if r['dimension']=='stance']
        self.assertEqual([r['status'] for r in stance],['SUPERSEDED','WITHDRAWN'])
        source_ids={s['id'] for s in trace['typedSources']}
        self.assertTrue(all(r['evidenceRefs'] and set(r['evidenceRefs']) <= source_ids for r in by_id.values()))
        self.assertTrue(any(r['type']=='REPLACES_REQUIREMENT' for r in trace['typedRelations']))
        self.assertTrue(any(r['type']=='RETRACTS_REQUIREMENT' for r in trace['typedRelations']))

    def test_progress_and_missing_answer_do_not_become_attempts(self):
        payload, aliases = prepared([('do work','Please wait.'),('status?',None)])
        out = proposal(payload)
        out['observations'][0]['kind']='PROGRESS_TEXT'
        result = relational.compile_result(out,payload,aliases)
        self.assertEqual(result['traces'][0]['attempts'],[])
        self.assertTrue(result['unresolved'])
        self.assertEqual(result['traces'][0]['businessOutcome'],'UNKNOWN')

    def test_tool_failure_does_not_get_overwritten_by_claim_or_task_pass(self):
        catalog = [dict(id='call',kind='TOOL_CALL',text='exchange',ref={'pairId':None},
                        metadata={'callId':'c1','name':'exchange'}),
                   dict(id='result',kind='TOOL_RESULT',text='invalid item',ref={'pairId':None},
                        metadata={'callId':'c1','name':'exchange','status':'FAILURE','verified':True}),
                   dict(id='v',kind='EVALUATION',text='task passed',ref={},
                        metadata={'scope':'TASK','status':'PASSED','outcomeType':'BUSINESS','verified':True})]
        payload, aliases = prepared([('exchange item','I successfully exchanged it.')],catalog)
        for item in payload['evidence'][:2]:item['ref']['pairId']=aliases['q1']['id']
        payload['evidence'][2]['metadata']['targetIds']=[aliases['q1']['sourceUserMessageId']]
        out = proposal(payload)
        out['observations'][0]['kind']='EXECUTION_CLAIM'
        out['executionBindings']=[dict(evidenceId=k,fragment='q1:f1') for k in ('call','result')]
        out['evaluationBindings']=[dict(evaluationId='v',fragment='q1:f1',scope='TASK',requirementVersion=1)]
        trace = relational.compile_result(out,payload,aliases)['traces'][0]
        self.assertEqual(len(trace['attempts']),1)
        self.assertEqual(trace['attempts'][0]['executionStatus'],'FAILURE')
        self.assertEqual(trace['attempts'][0]['businessOutcome'],'UNKNOWN')
        task_evaluation = next(e for e in trace['outcomeEvidence'] if e['scope']=='TASK')
        self.assertEqual(task_evaluation['targetIds'],[trace['id']])
        self.assertNotIn('v',trace['attempts'][0].get('evaluationIds',[]))
        call=next(s for s in trace['typedSources'] if s['id']=='call')
        self.assertEqual(call['ref']['attemptId'],trace['attempts'][0]['id'])

    def test_results_never_pair_with_a_different_call_id(self):
        catalog=[dict(id='call',kind='TOOL_CALL',text='read',ref={},metadata={'callId':'c1'}),
                 dict(id='result',kind='TOOL_RESULT',text='ok',ref={},
                      metadata={'callId':'c2','status':'PASSED','verified':True})]
        payload, aliases=prepared([('read item','I have read it')],catalog)
        payload['evidence'][0]['ref']['pairId']=aliases['q1']['id']
        # Both source records belong to this pair; their distinct call IDs
        # still prevent linking. Completely orphaned results are rejected
        # separately by the action-only/source-binding acceptance tests.
        payload['evidence'][1]['ref']['pairId']=aliases['q1']['id']
        out=proposal(payload)
        out['observations'][0]['kind']='EXECUTION_CLAIM'
        out['executionBindings']=[dict(evidenceId=k,fragment='q1:f1') for k in ('call','result')]
        trace=relational.compile_result(out,payload,aliases)['traces'][0]
        self.assertEqual(trace['attempts'][0]['executionStatus'],'UNKNOWN')
        self.assertTrue(any(e['unknownReason']=='CALL_NOT_OBSERVED' for e in trace['outcomeEvidence']))

    def test_close_membership_alternatives_stay_unresolved(self):
        payload, aliases=prepared([('work A','A output'),('work B','B output'),('this needs correcting','correction')])
        out=proposal(payload,{'q1':'t1','q2':'t2','q3':'t1'})
        out['annotations'][2]['fragments'][0]['alternatives']=['t2']
        out['memberships'][2]['options'].append(dict(task='t2',status='CONFIRMED',score=1,reason='also possible'))
        result=relational.compile_result(out,payload,aliases)
        member=next(m for m in result['memberships'] if m['pairId']==aliases['q3']['id'])
        self.assertIsNone(member['taskId'])
        self.assertEqual(len(member['alternativeTaskIds']),2)
        self.assertGreaterEqual(result['searchAudit']['retainedCount'],2)
        self.assertLessEqual(result['searchAudit']['retainedCount'],8)
        self.assertTrue(all(any(u.get('candidateScope') for u in t['unresolved']) for t in result['traces']))
        self.assertTrue(all(t['recoveryProgress']=='PROCESSED_WITH_UNCERTAINTIES' for t in result['traces']))

    def test_cross_task_future_and_invalid_sources_are_not_selected(self):
        payload, aliases=prepared([('A','a'),('B','b')])
        out=proposal(payload,{'q1':'t1','q2':'t2'})
        out['relations']=[dict(id='r',source='q1:f1',options=[dict(
            target='q2:f1',kind='REJECT_RESULT',score=1,delta='',scope='CURRENT_DELIVERY',
            evidence=[span(payload,'q1','user'),span(payload,'q2','assistant')],reason='invalid future'),
            dict(target=None,kind='UNKNOWN',score=0.1,reason='unknown')])]
        result=relational.compile_result(out,payload,aliases)
        self.assertTrue(result['unresolved'])
        self.assertTrue(all(not t['feedbackEdges'] for t in result['traces']))
        broken=deepcopy(out);broken['observations'][0]['evidence']={'span':'nonexistent'}
        with self.assertRaises(ValueError):relational.compile_result(broken,payload,aliases)

    def test_missing_user_is_pending_without_fabricated_fragment(self):
        source=pairs([('', 'orphan answer'),('visible request','visible answer')])
        with patch.object(relational,'_catalog',return_value=[]):payload, aliases=relational.prepare(source)
        out=proposal(payload)
        result=relational.compile_result(out,payload,aliases)
        self.assertTrue(any(u.get('pairId')==aliases['q1']['id'] for u in result['unresolved']))
        self.assertEqual(len(result['annotations']),1)

    def test_source_hash_and_user_coverage_are_required(self):
        payload, aliases=prepared([('all the user text','answer')])
        out=proposal(payload)
        out['annotations'][0]['fragments'][0]['quote']='all'
        with self.assertRaises(ValueError):relational.compile_result(out,payload,aliases)
        self.assertNotIn('assistant',payload['pairs'][0])
        out=proposal(payload);out['sourceHash']='wrong'
        with self.assertRaises(ValueError):relational.compile_result(out,payload,aliases)

    def test_only_recorded_live_reply_is_projected(self):
        source=pairs([('A','a'),('B','b'),('feedback A','c')])
        source[0]['sourceTurnId']='turn-A';source[1]['sourceTurnId']='turn-B'
        source[2]['sourceReplyReference']={'targetTurnId':'turn-A',
            'basis':'RECORDED_LIVE_CHAT_INPUT','status':'SOURCE_RESOLVED'}
        with patch.object(relational,'_catalog',return_value=[]):
            payload,_=relational.prepare(source)
        self.assertEqual(payload['pairs'][2]['sourceReplyReference']['targetPair'],'q1')
        source[2]['sourceReplyReference']={'targetTurnId':'missing',
            'basis':'RECORDED_LIVE_CHAT_INPUT','status':'UNRESOLVED'}
        source[1]['replyTo']='turn-A'
        with patch.object(relational,'_catalog',return_value=[]):
            payload,_=relational.prepare(source)
        self.assertIsNone(payload['pairs'][2]['sourceReplyReference']['targetPair'])
        self.assertNotIn('sourceReplyReference',payload['pairs'][1])

    def test_real_catalog_contract_and_step_target_are_source_local(self):
        source=pairs([('execute operation','It is complete')])
        source[0]['toolEvents']=[dict(id='tool-source',sourceId='tool-source',eventType='CALL',
            callId='real-call',name='operation',arguments={'item':'example'})]
        evaluations=[dict(id='step-v',source='offline check fixture',scope='STEP',
            targetIds=['real-call'],criterion='tool action invariant',status='SUCCESS',
            outcomeType='TECHNICAL',verified=True,verificationBasis='explicit fixture assertion',requirementVersion=1)]
        payload,aliases=relational.prepare(source,evaluations=evaluations)
        out=proposal(payload);out['observations'][0]['kind']='EXECUTION_CLAIM'
        call=next(e for e in payload['evidence'] if e['kind']=='TOOL_CALL')
        out['executionBindings']=[dict(evidenceId=call['id'],fragment='q1:f1')]
        out['evaluationBindings']=[dict(evaluationId='step-v',fragment='q1:f1',scope='STEP',requirementVersion=1)]
        trace=relational.compile_result(out,payload,aliases)['traces'][0]
        step=next(e for e in trace['outcomeEvidence'] if e['scope']=='STEP')
        self.assertEqual(step['targetIds'],[call['id']])
        self.assertTrue(step['verified'])
        self.assertNotEqual(step['targetIds'],[trace['attempts'][0]['id']])

    def test_evaluation_target_source_and_version_are_not_overridden(self):
        catalog=[dict(id='v',kind='EVALUATION',text='passed',ref={},metadata={
            'scope':'ATTEMPT','status':'SUCCESS','verified':True,'requirementVersion':1,
            'targetIds':['unobserved-call']})]
        payload,aliases=prepared([('request','answer')],catalog)
        out=proposal(payload)
        out['evaluationBindings']=[dict(evaluationId='v',fragment='q1:f1',scope='ATTEMPT',requirementVersion=1)]
        trace=relational.compile_result(out,payload,aliases)['traces'][0]
        value=trace['outcomeEvidence'][0]
        self.assertEqual(value['status'],'UNKNOWN')
        self.assertFalse(value['verified'])
        self.assertEqual(value['targetIds'],[])
        out['evaluationBindings'][0]['requirementVersion']=2
        with self.assertRaises(ValueError):relational.compile_result(out,payload,aliases)

    def test_unbound_evaluation_remains_unknown_in_candidate_task(self):
        source=pairs([('request','answer')])
        evaluations=[dict(id='v',source='fixture check',scope='TASK',
            targetIds=[source[0]['sourceUserMessageId']],criterion='whole task',status='SUCCESS',
            verified=True,verificationBasis='fixture')]
        payload,aliases=relational.prepare(source,evaluations=evaluations)
        result=relational.compile_result(proposal(payload),payload,aliases)
        trace=result['traces'][0]
        self.assertTrue(any(u['status']=='EVALUATION_BINDING_UNRESOLVED' for u in trace['unresolved']))
        self.assertEqual(trace['outcomeEvidence'][0]['status'],'UNKNOWN')
        self.assertEqual(trace['outcomeEvidence'][0]['unknownReason'],'EVALUATION_BINDING_MISSING')
        self.assertEqual(trace['outcomeEvidence'][0]['reportedStatus'],'SUCCESS')
        self.assertFalse(trace['outcomeEvidence'][0]['verified'])
        self.assertEqual(trace['businessOutcome'],'UNKNOWN')

    def test_explicit_future_scope_and_feedback_sources_survive(self):
        payload,aliases=prepared([('draft','output'),('every future output must keep numbering','corrected')])
        out=proposal(payload)
        out['requirements']=[dict(fragment='q2:f1',dimension='numbering',op='ADD',value='keep',
            scope='FUTURE_TASKS',evidence=[span(payload,'q2','user')])]
        out['relations']=[dict(id='feedback',source='q2:f1',options=[dict(target='q1:f1',
            kind='CHANGE_OUTPUT',score=1,reason='explicit future user rule',delta='keep numbering',
            scope='FUTURE_TASKS',evidence=[span(payload,'q2','user'),span(payload,'q1','assistant')])])]
        trace=relational.compile_result(out,payload,aliases)['traces'][0]
        req=next(r for r in trace['requirements'] if r['dimension']=='numbering')
        self.assertEqual(req['scope'],'FUTURE_TASKS')
        self.assertNotIn(req['id'],trace['attempts'][1]['requirementIds'])
        feedback=next(s for s in trace['typedSources'] if s['kind']=='USER_FEEDBACK')
        self.assertEqual(feedback['metadata']['scope'],'FUTURE_TASKS')
        self.assertTrue(feedback['ref']['targetFragmentId'])
        self.assertEqual(trace['typedRelations'][0]['type'],'CHANGE_OUTPUT')

    def test_feedback_target_claim_is_not_promoted_to_visible_process(self):
        payload,aliases=prepared([('run operation','I completed operation'),('thanks','acknowledged')])
        out=proposal(payload);out['observations'][0]['kind']='EXECUTION_CLAIM'
        out['relations']=[dict(id='accept',source='q2:f1',options=[dict(target='q1:f1',
            kind='ACCEPT_RESULT',score=1,reason='thanks to stated result',delta='',scope='CURRENT_DELIVERY',
            evidence=[span(payload,'q2','user'),span(payload,'q1','assistant')])])]
        trace=relational.compile_result(out,payload,aliases)['traces'][0]
        claim_refs=[s for s in trace['typedSources'] if s['ref'].get('pairId')==aliases['q1']['id']
                    and s['ref'].get('side')=='assistant']
        self.assertTrue(claim_refs)
        self.assertTrue(all(s['kind']=='ASSISTANT_CLAIM' for s in claim_refs))

    def test_delivery_scope_expires_even_when_value_matches_task_scope(self):
        payload,aliases=prepared([('plain text','text'),('this delivery plain text','text'),('continue','text')])
        out=proposal(payload)
        out['requirements']=[dict(fragment='q1:f1',dimension='format',op='ADD',value='plain',
            evidence=[span(payload,'q1','user')]),dict(fragment='q2:f1',dimension='format',op='ADD',
            value='plain',scope='CURRENT_DELIVERY',evidence=[span(payload,'q2','user')])]
        trace=relational.compile_result(out,payload,aliases)['traces'][0]
        by_id={r['id']:r for r in trace['requirements']}
        self.assertEqual(by_id[trace['attempts'][1]['requirementIds'][0]]['scope'],'CURRENT_DELIVERY')
        self.assertEqual(by_id[trace['attempts'][2]['requirementIds'][0]]['scope'],'CURRENT_TASK')
        self.assertTrue(trace['requirementTimeline'][-1]['scopeExpired'])

    def test_same_dimension_adds_coexist_across_turns_and_keep_reaffirmation_sources(self):
        payload,aliases=prepared([('list the basis of each item','draft'),
                                 ('list unknowns separately; keep listing each basis','revision')])
        out=proposal(payload)
        out['requirements']=[dict(fragment='q1:f1',dimension='content',op='ADD',value='basis per item',
            evidence=[span(payload,'q1','user')]),dict(fragment='q2:f1',dimension='content',op='ADD',
            value='unknowns separately',evidence=[span(payload,'q2','user')]),
            dict(fragment='q2:f1',dimension='content',op='ADD',value='basis per item',evidence=[span(payload,'q2','user')])]
        trace=relational.compile_result(out,payload,aliases)['traces'][0]
        self.assertEqual(trace['requirementTimeline'][0]['values']['content'],'basis per item')
        self.assertEqual(trace['requirementTimeline'][1]['values']['content'],['basis per item','unknowns separately'])
        records=[r for r in trace['requirements'] if r['dimension']=='content']
        self.assertEqual(len(records),2)
        self.assertTrue(all(r['status']=='ACTIVE' for r in records))
        repeated=next(r for r in records if r['value']=='basis per item')
        self.assertEqual(len(repeated['evidenceRefs']),2)
        self.assertEqual(len(trace['attempts'][1]['requirementIds']),2)

    def test_two_adds_in_one_fragment_then_replace_supersedes_only_that_dimension_scope(self):
        payload,aliases=prepared([('list basis and unknowns; use plain text; future output keep numbering','draft'),
                                 ('replace content with conclusions only','conclusions')])
        out=proposal(payload)
        out['requirements']=[dict(fragment='q1:f1',dimension='content',op='ADD',value=v,
            evidence=[span(payload,'q1','user')]) for v in ('basis per item','unknowns separately')]
        out['requirements'] += [dict(fragment='q1:f1',dimension='format',op='ADD',value='plain',
            evidence=[span(payload,'q1','user')]),dict(fragment='q1:f1',dimension='content',op='ADD',
            value='preserve numbering',scope='FUTURE_TASKS',evidence=[span(payload,'q1','user')]),
            dict(fragment='q2:f1',dimension='content',op='REPLACE',value='conclusions only',evidence=[span(payload,'q2','user')])]
        trace=relational.compile_result(out,payload,aliases)['traces'][0]
        self.assertEqual(trace['requirementTimeline'][1]['values'],{'content':'conclusions only','format':'plain'})
        old=[r for r in trace['requirements'] if r['value'] in ('basis per item','unknowns separately')]
        self.assertTrue(all(r['status']=='SUPERSEDED' for r in old))
        future=next(r for r in trace['requirements'] if r['scope']=='FUTURE_TASKS')
        self.assertEqual(future['status'],'ACTIVE')
        self.assertNotIn(future['id'],trace['attempts'][1]['requirementIds'])
        self.assertEqual(sum(r['type']=='REPLACES_REQUIREMENT' for r in trace['typedRelations']),2)

    def test_different_scopes_keep_independent_dimension_values(self):
        payload,aliases=prepared([('current basis; this delivery unknowns; future preserve numbering','working'),
                                 ('for this delivery replace unknowns with explicit caveats','result')])
        out=proposal(payload);out['observations'][0]['kind']='PROGRESS_TEXT'
        out['requirements']=[dict(fragment='q1:f1',dimension='content',op='ADD',value=v,scope=s,
            evidence=[span(payload,'q1','user')]) for s,v in (
                ('CURRENT_TASK','basis'),('CURRENT_DELIVERY','unknowns'),('FUTURE_TASKS','numbering'))]
        out['requirements'].append(dict(fragment='q2:f1',dimension='content',op='REPLACE',value='caveats',
            scope='CURRENT_DELIVERY',evidence=[span(payload,'q2','user')]))
        trace=relational.compile_result(out,payload,aliases)['traces'][0]
        by_value={r['value']:r for r in trace['requirements']}
        self.assertEqual(by_value['basis']['status'],'ACTIVE')
        self.assertEqual(by_value['numbering']['status'],'ACTIVE')
        self.assertEqual(by_value['unknowns']['status'],'SUPERSEDED')
        self.assertEqual(by_value['caveats']['status'],'ACTIVE')
        self.assertEqual(trace['requirementTimeline'][-1]['scopeValues']['CURRENT_TASK']['content'],'basis')
        self.assertEqual(trace['requirementTimeline'][-1]['scopeValues']['CURRENT_DELIVERY']['content'],'caveats')
        self.assertEqual(set(trace['attempts'][0]['requirementIds']),{by_value['basis']['id'],by_value['caveats']['id']})

    def test_beam_pruning_is_reported_and_not_confused_with_certainty(self):
        payload,aliases=prepared([('A','a'),('B','b'),('this','x'),('this','y'),('this','z'),('this','w')])
        out=proposal(payload,{'q1':'t1','q2':'t2','q3':'t1','q4':'t1','q5':'t1','q6':'t1'})
        for i in range(2,6):
            out['annotations'][i]['fragments'][0]['alternatives']=['t2']
            out['memberships'][i]['options'].append(dict(task='t2',status='CONFIRMED',score=.5,reason='plausible second'))
        result=relational.compile_result(out,payload,aliases)
        self.assertTrue(result['searchAudit']['approximate'])
        self.assertTrue(result['searchAudit']['beamPruned'])
        self.assertTrue(any(u['status']=='SEARCH_PRUNED_UNRESOLVED' for u in result['unresolved']))


if __name__=='__main__':unittest.main()
