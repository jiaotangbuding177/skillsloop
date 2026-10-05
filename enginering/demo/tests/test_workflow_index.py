"""Lossless model-wire indexing; no model calls or acceptance-run writes."""
import json
import unittest
from copy import deepcopy

from skilldemo import workflow, workflow_index
from test_relational_workflow import trace, extracted, merged_view


class WorkflowIndexTests(unittest.TestCase):
    def material(self):
        body = 'VISIBLE_TOOL_RESULT_' + 'A' * 4096
        receipt = {'id':'tool-a', 'status':'FAILED', 'result':body,
                   'arguments':{'content':body}, 'sourceRef':{'sourceId':'event-a'}}
        return {'algorithm':'test-v1', 'sourceHash':'h' * 64, 'traces':[
            {'traceId':'trace-a', 'allowedEvidenceIds':['e1'],
             'requirements':[{'id':'r1', 'scope':'FUTURE_TASKS', 'sourceRefs':[{'quote':body}]}],
             'typedRelations':[{'id':'rel1', 'from':'a1', 'to':'r1', 'status':'UNRESOLVED'}],
             'outcomeEvidence':[{'id':'v1', 'scope':'STEP', 'targetIds':['event-a'], 'verified':False}],
             'evidence':[{'id':'e1', 'text':body, 'metadata':deepcopy(receipt)}],
             'attempts':[{'id':f'a{i}', 'executionRefs':deepcopy(receipt)} for i in range(8)]}]}

    def test_round_trip_keeps_all_facts_and_source_identities(self):
        original = self.material()
        indexed = workflow_index.compact(original)
        self.assertEqual(workflow_index.expand(indexed), original)
        self.assertEqual(original, self.material())
        self.assertEqual(indexed['sourceHash'], original['sourceHash'])
        self.assertEqual(indexed['traces'][0]['allowedEvidenceIds'], ['e1'])
        self.assertEqual(indexed['traces'][0]['traceId'], 'trace-a')

    def test_body_once_and_repeated_receipts_once(self):
        original = self.material()
        indexed = workflow_index.compact(original)
        body = original['traces'][0]['evidence'][0]['text']
        wire = json.dumps(indexed, ensure_ascii=False)
        self.assertEqual(wire.count(body), 1)
        self.assertLess(len(wire), len(json.dumps(original,ensure_ascii=False)) * .4)
        self.assertTrue(indexed['contentIndex']['records'])
        self.assertEqual(workflow_index.expand(indexed)['traces'][0]['attempts'][7]['executionRefs']['status'], 'FAILED')

    def test_stable_content_ids_and_existing_literal_ref_objects(self):
        original = self.material()
        original['literal'] = {'$workflowText':'literal-business-value'}
        first = workflow_index.compact(original)
        second = workflow_index.compact(dict(reversed(list(original.items()))))
        self.assertEqual(set(first['contentIndex']['texts']), set(second['contentIndex']['texts']))
        self.assertEqual(set(first['contentIndex']['records']), set(second['contentIndex']['records']))
        self.assertEqual(workflow_index.expand(first), original)

    def test_missing_and_tampered_index_are_rejected(self):
        for change in ('missing','tampered'):
            indexed = workflow_index.compact(self.material())
            key = next(iter(indexed['contentIndex']['texts']))
            if change == 'missing': del indexed['contentIndex']['texts'][key]
            else: indexed['contentIndex']['texts'][key] += 'modified'
            with self.assertRaises(ValueError): workflow_index.expand(indexed)

    def test_old_unindexed_inputs_are_compatible(self):
        original = self.material()
        self.assertEqual(workflow_index.expand(original), original)

    def test_wire_uses_index_only_when_it_reduces_complete_json(self):
        small = {'algorithm':'test', 'sourceHash':'fixed', 'traces':[{'traceId':'t1','text':'short'}]}
        self.assertEqual(workflow_index.wire(small), small)
        large = self.material()
        selected = workflow_index.wire(large)
        self.assertEqual(selected['indexFormat'], workflow_index.VERSION)
        self.assertEqual(workflow_index.expand(selected), large)

    def large_trace(self):
        t = trace()
        body = 'one-complete-tool-result-' + 'A' * 19000
        receipt = {'status':'AVAILABLE', 'tools':[{'id':'call-a', 'name':'read',
                    'arguments':{'path':'inputs/evidence.txt'}, 'result':body, 'status':'FAILED'}],
                   'skills':[]}
        t['typedSources'][1].update(kind='TOOL_RESULT', text=body,
                                    metadata={'result':body, 'status':'FAILED'})
        t['attempts'] = [{'id':f'a{i}', 'pairId':'p1', 'fragmentId':'f1',
                         'requirementIds':['r1'], 'requirementVersion':1, 'evidenceRefs':['process1'],
                         'executionRefs':{'skillEvidence':deepcopy(receipt)}} for i in range(8)]
        return t

    def test_prepare_indexes_redundancy_with_original_budget_and_private_catalog(self):
        payload, catalog = workflow.prepare([self.large_trace()])
        self.assertEqual(payload['indexFormat'], workflow_index.VERSION)
        self.assertLess(len(json.dumps(payload,ensure_ascii=False)), 110000)
        full = workflow_index.expand(payload)
        self.assertEqual(len(full['traces'][0]['attempts']), 8)
        self.assertEqual(len(full['traces'][0]['typedSources'][1]['text']), 19025)
        row = next(r for r in catalog.values() if r.get('sourceId')=='process1')
        self.assertEqual(row['text'], full['traces'][0]['typedSources'][1]['text'])

    def test_unique_large_fact_still_defers_whole_input(self):
        t = trace()
        t['typedSources'][1]['text'] = 'one-unique-body-' + 'Q' * 120000
        with self.assertRaisesRegex(ValueError, 'STAGE4_INPUT_BUDGET'):
            workflow.prepare([t])

    def test_original_extract_and_merge_compilers_accept_indexed_payload(self):
        payload, catalog, ext = extracted(trace())
        self.assertEqual(ext['methods'][0]['supportAssessment']['supportStatus'], 'OBSERVED_UNVERIFIED')
        ext, view, output = merged_view(trace())
        self.assertEqual(workflow_index.expand(view)['clusters'][0]['methods'][0]['id'], 'm1')
        workflows, _ = workflow.validate_merge(output, view, ext)
        self.assertEqual(workflows[0]['includedMethodIds'], ['m1'])


if __name__ == '__main__':
    unittest.main()
