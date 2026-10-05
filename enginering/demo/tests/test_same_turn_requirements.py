"""Source fixtures test same-turn requirement causality, not model accuracy."""
import unittest
from skilldemo import relational
from test_relational import prepared, proposal, span


def split(out, payload, pair, parts, tasks=None):
    tasks = tasks or ['t1'] * len(parts)
    prior = next(a for a in out['annotations'] if a['pair'] == pair)
    initial = prior['fragments'][0]['kind']
    prior['fragments'] = [dict(id='f'+str(i), quote=text, intent='source fixture',
        kind=initial if i == 1 else 'CONTINUE', task=task,
        alternatives=[], references=[], uncertainty='')
        for i, (text, task) in enumerate(zip(parts, tasks), 1)]
    out['memberships'] = [m for m in out['memberships'] if not m['fragment'].startswith(pair+':')]
    out['memberships'] += [dict(fragment=pair+':f'+str(i), options=[dict(
        task=task, status='CONFIRMED', score=1, reason='source fixture')])
        for i, task in enumerate(tasks, 1)]


def requirement(pair, fragment, dimension, op, value, quote, scope='CURRENT_TASK'):
    return dict(fragment=pair+':f'+str(fragment), dimension=dimension, op=op,
        value=value, scope=scope, evidence=[dict(pair=pair, side='user', quote=quote)])


class SameTurnRequirementTests(unittest.TestCase):
    def test_visible_and_tool_attempts_use_all_same_pair_updates(self):
        payload, aliases = prepared([('keep basis; use table', 'report delivered')])
        out = proposal(payload)
        split(out, payload, 'q1', ['keep basis; ', 'use table'])
        out['requirements'] = [requirement('q1', 1, 'content', 'ADD', 'basis', 'keep basis'),
                               requirement('q1', 2, 'format', 'ADD', 'table', 'use table')]
        ref = dict(pairId=aliases['q1']['id'], sourceId='write-c', eventId='write-event', runId='r')
        payload['evidence'] = [dict(id='call', kind='TOOL_CALL', text='write', ref=ref,
            metadata=dict(callId='write-c', name='write', sourceOrder=2, actor='assistant')),
            dict(id='result', kind='TOOL_RESULT', text='written', ref={**ref, 'sourceId':'write-result'},
            metadata=dict(callId='write-c', name='write', sourceOrder=3, status='SUCCEEDED'))]
        out['executionBindings'] = [dict(fragment='q1:f1', evidenceId='call')]
        trace = relational.compile_result(out, payload, aliases)['traces'][0]
        self.assertEqual(len(trace['requirementTimeline']), 1)
        self.assertEqual(trace['requirementTimeline'][0]['values'], dict(content='basis', format='table'))
        by_id = {r['id']:r for r in trace['requirements']}
        self.assertEqual({a['kind'] for a in trace['attempts']}, {'TOOL_CALL', 'VISIBLE_DELIVERY'})
        for attempt in trace['attempts']:
            self.assertEqual(attempt['requirementVersion'], 1)
            self.assertEqual({by_id[r]['dimension'] for r in attempt['requirementIds']}, {'content','format'})

    def test_delivery_scope_cannot_expire_between_fragments(self):
        payload, aliases = prepared([('table this time; preserve numbering', 'table output'),
                                     ('continue', 'next output')])
        out = proposal(payload)
        split(out, payload, 'q1', ['table this time; ', 'preserve numbering'])
        out['requirements'] = [requirement('q1', 1, 'format', 'ADD', 'table', 'table this time', 'CURRENT_DELIVERY'),
                               requirement('q1', 2, 'content', 'ADD', 'numbering', 'preserve numbering')]
        out['observations'].append(dict(fragment='q1:f2', kind='VISIBLE_TEXT',
            evidence=span(payload,'q1','assistant'), description='same source delivery'))
        trace = relational.compile_result(out, payload, aliases)['traces'][0]
        first, second = trace['requirementTimeline']
        self.assertEqual(first['scopeValues']['CURRENT_DELIVERY'], {'format':'table'})
        self.assertFalse(first['scopeExpired'])
        self.assertTrue(second['scopeExpired'])
        self.assertNotIn('format', second['values'])
        by_id = {r['id']:r for r in trace['requirements']}
        same_pair = [a for a in trace['attempts'] if a['pairId'] == aliases['q1']['id']]
        self.assertEqual(len(same_pair), 2)
        self.assertTrue(all(a['requirementVersion'] == first['version'] for a in same_pair))
        self.assertTrue(all(any(by_id[r]['dimension'] == 'format' for r in a['requirementIds']) for a in same_pair))

    def test_requirement_records_and_shared_quote_keep_original_fragments(self):
        payload, aliases = prepared([('keep basis; use table', 'report')])
        out = proposal(payload)
        split(out, payload, 'q1', ['keep basis; ', 'use table'])
        quote = payload['pairs'][0]['user']
        out['requirements'] = [requirement('q1', 1, 'content', 'ADD', 'basis', quote),
                               requirement('q1', 2, 'format', 'ADD', 'table', quote)]
        result = relational.compile_result(out, payload, aliases)
        trace = result['traces'][0]
        fragments = {f['fragmentKey']:f['id'] for a in result['annotations'] for f in a['fragments']}
        records = {r['dimension']:r for r in trace['requirements']}
        self.assertEqual(records['content']['fragmentId'], fragments['q1:f1'])
        self.assertEqual(records['format']['fragmentId'], fragments['q1:f2'])
        source = next(s for s in trace['typedSources'] if s['kind'] == 'USER_REQUIREMENT')
        self.assertEqual(set(source['ref']['fragmentIds']), {fragments['q1:f1'], fragments['q1:f2']})
        self.assertNotIn('fragmentId', source['ref'])
        bindings = {b['requirementId']:b['fragmentId'] for b in source['metadata']['requirementBindings']}
        self.assertEqual(bindings[records['format']['id']], fragments['q1:f2'])

    def test_two_tasks_in_same_pair_have_independent_atomic_updates(self):
        payload, aliases = prepared([('contract plain; notice table', 'contract report; notice report')])
        out = proposal(payload)
        split(out, payload, 'q1', ['contract plain; ', 'notice table'], ['t1','t2'])
        out['annotations'][0]['fragments'][1]['kind'] = 'OPEN'
        out['seeds'].append(dict(key='t2', anchor='q1:f2', goal='notice', object='notice',
                                deliverable='table', constraints=[]))
        out['observations'] = [dict(fragment='q1:f'+str(i), kind='VISIBLE_TEXT',
            evidence=dict(pair='q1', side='assistant', quote=q), description='source delivery')
            for i,q in enumerate(['contract report','notice report'],1)]
        out['requirements'] = [requirement('q1', 1, 'format', 'ADD', 'plain', 'contract plain'),
                               requirement('q1', 2, 'format', 'ADD', 'table', 'notice table')]
        traces = relational.compile_result(out, payload, aliases)['traces']
        self.assertEqual(len(traces), 2)
        self.assertEqual({t['requirementTimeline'][0]['values']['format'] for t in traces}, {'plain','table'})
        self.assertTrue(all(len(t['requirements']) == 1 for t in traces))
        self.assertTrue(all(t['attempts'][0]['requirementVersion'] == 1 for t in traces))

    def test_same_turn_replace_retract_future_and_later_noop(self):
        payload, aliases = prepared([('plain with details','draft'),
            ('use table; withdraw details; future numbering','table output'), ('continue','next output')])
        out = proposal(payload)
        split(out, payload, 'q2', ['use table; ', 'withdraw details; ', 'future numbering'])
        out['requirements'] = [requirement('q1', 1, 'format', 'ADD', 'plain', 'plain'),
            requirement('q1', 1, 'detail', 'ADD', 'full', 'details'),
            requirement('q2', 1, 'format', 'REPLACE', 'table', 'use table'),
            requirement('q2', 2, 'detail', 'RETRACT', None, 'withdraw details'),
            requirement('q2', 3, 'format', 'ADD', 'numbered', 'future numbering', 'FUTURE_TASKS')]
        trace = relational.compile_result(out, payload, aliases)['traces'][0]
        self.assertEqual(len(trace['requirementTimeline']), 2)
        self.assertEqual(trace['requirementTimeline'][-1]['values'], {'format':'table'})
        self.assertEqual(trace['requirementTimeline'][-1]['futureValues'], {'format':'numbered'})
        self.assertEqual([a['requirementVersion'] for a in trace['attempts']], [1,2,2])
        records = {r['value']:r for r in trace['requirements']}
        self.assertEqual(records['plain']['status'], 'SUPERSEDED')
        self.assertEqual(records['full']['status'], 'WITHDRAWN')
        self.assertEqual(records['numbered']['scope'], 'FUTURE_TASKS')
        self.assertTrue(all(records['numbered']['id'] not in a['requirementIds'] for a in trace['attempts']))


if __name__ == '__main__':
    unittest.main()
