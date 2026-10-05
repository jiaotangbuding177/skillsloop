import tempfile
import unittest
from pathlib import Path
from skilldemo.core import Loop, Conflict
from skilldemo.runtime import ReplayAgent, digest
from skilldemo.learning import initial_files, compile_patch
from skilldemo.evolution import enqueue


class EvolutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.loop = Loop(Path(self.tmp.name), ReplayAgent(), stage_pipeline=True)
        files = initial_files(None, '条款格式整理')
        self.base = {'id': 's1', 'owner': 'alice', 'org': 'acme', 'version': 1,
                     'hash': digest(files), 'title': '条款格式整理', 'files': files}
        self.target = ['s1', 1, self.base['hash']]
        self.trace = {'id': 't1', 'owner': 'alice', 'org': 'acme', 'session': 'live1',
                      'schemaVersion': 'task-trace-v2', 'purposeSplit': 'live', 'state': 'SEALED', 'hash': 'th', 'revision': 1,
                      'skillUseReceipts': [{'skills': [{'id': 's1', 'version': 1, 'hash': self.base['hash'], 'status': 'FILE_READ'}]}]}
        self.w = {'id': 'w1', 'owner': 'alice', 'action': 'UPDATE', 'status': 'FROZEN', 'targetBase': self.target,
                  'sourceRefs': [{'id': 't1', 'revision': 1, 'hash': 'th'}], 'analysisId': 'a1',
                  'workflow': {'includedMethodIds': ['m1']}}
        self.w['workflowHash'] = digest(self.w['workflow'])
        self.analysis = {'id': 'a1', 'owner': 'alice', 'validatedOutput': {'methods': [
            {'id': 'm1', 'evidenceRefs': ['e1'], 'action': '保留原编号'}]},
            'catalog': {'e1': {'traceId': 't1', 'kind': 'USER_FEEDBACK', 'text': '以后保留原编号',
                                'ref': {'sourcePairId': 'p2'}, 'scope': 'FUTURE_TASKS'}}}
        with self.loop.store.tx() as db:
            for kind, value in [('skill', self.base), ('trace', self.trace), ('workflow', self.w), ('workflow_analysis', self.analysis)]:
                self.loop.store.put(db, kind, value)

    def tearDown(self):
        self.tmp.cleanup()

    def test_exact_version_queue_idempotent_and_unknown_evidence(self):
        c = enqueue(self.loop, 'alice')[0]
        self.assertEqual((c['action'], c['target'], c['baseVersion']), ('UPDATE', 's1', 1))
        self.assertEqual(c['input']['evidence'][0]['analyst'], 'unknown')
        self.assertEqual(c['input']['evidence'][0]['events'][0]['kind'], 'user')
        self.assertEqual(enqueue(self.loop, 'alice'), [])

    def test_selected_only_cannot_update(self):
        self.trace['skillUseReceipts'][0]['skills'][0]['status'] = 'SELECTED'
        with self.loop.store.tx() as db: self.loop.store.put(db, 'trace', self.trace)
        with self.assertRaises(ValueError): enqueue(self.loop, 'alice')

    def test_stale_base_is_preserved_not_overwritten(self):
        self.base['version'] = 2
        with self.loop.store.tx() as db: self.loop.store.put(db, 'skill', self.base)
        self.assertEqual(enqueue(self.loop, 'alice'), [])
        with self.loop.store.tx() as db:
            self.assertEqual(self.loop.store.get(db, 'workflow', 'w1')['status'], 'STALE_BASE')

    def test_two_workflows_same_target_make_one_update(self):
        other = {**self.w, 'id': 'w2'}
        with self.loop.store.tx() as db: self.loop.store.put(db, 'workflow', other)
        rows = enqueue(self.loop, 'alice')
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]['input']['workflowRefs']), 2)

    def test_changed_workflow_blocks_commit_and_unknown_observation_cannot_patch(self):
        c = enqueue(self.loop, 'alice')[0]
        evidence = c['input']['evidence'][0]
        proposal = {'id': 'p1', 'lesson': '保留编号', 'applicability': '条款输出', 'evidenceType': 'OBSERVED',
                    'evidenceRefs': [{'eventId': evidence['events'][0]['id'], 'quote': '以后保留原编号'}]}
        output = {'analyses': [{'taskId': 't1', 'analyst': 'unknown', 'proposals': [proposal]}],
                  'mergedPatches': [{'proposalIds': ['p1'], 'operations': [{'op': 'append', 'path': 'SKILL.md',
                      'beforeHash': c['input']['fileHashes']['SKILL.md'], 'content': '\n保留编号'}]}]}
        with self.assertRaises(ValueError): compile_patch(c['input'], output)
        self.w['workflow']['title'] = 'changed'
        with self.loop.store.tx() as db:
            self.loop.store.put(db, 'workflow', self.w)
            with self.assertRaises(Conflict): self.loop._current(db, c)


if __name__ == '__main__': unittest.main()
