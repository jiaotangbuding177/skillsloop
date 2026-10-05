import json
import tempfile
import unittest
from pathlib import Path
from skilldemo.core import Loop
from skilldemo.request_cache import request


class SourceBindingTests(unittest.TestCase):
    def test_host_binding_preserves_wrong_echo_and_still_validates_semantics(self):
        class Agent:
            mode = 'replay'
            def run(self, purpose, payload, workspace):
                return {'text': json.dumps({'sourceHash': 'model-typo', 'value': 'source text'})}
        with tempfile.TemporaryDirectory() as root:
            loop = Loop(Path(root), Agent(), task_detection=False, stage_pipeline=False)
            payload = {'sourceHash': 'host-hash', 'tuples': [('a', None)]}
            def validate(value):
                self.assertEqual(value['sourceHash'], 'host-hash')
                self.assertEqual(value['value'], 'source text')
            output, rid = request(loop, 'alice', 'front_analysis', 'detect_pairs', payload, validate)
            with loop.store.tx() as db:
                row = loop.store.get(db, 'front_analysis', rid)
                self.assertFalse(row['sourceBinding']['echoMatched'])
                self.assertEqual(row['sourceBinding']['modelEcho'], 'model-typo')
                raw = json.loads(db.execute('SELECT result FROM runs WHERE id=?', (rid,)).fetchone()[0])
                self.assertEqual(json.loads(raw['text'])['sourceHash'], 'model-typo')
            def reject(value): raise ValueError('invalid quotation')
            with self.assertRaisesRegex(ValueError, 'invalid quotation'):
                request(loop, 'alice', 'front_analysis', 'detect_pairs', {**payload, 'new': True}, reject)

    def test_actual_request_tampering_is_rejected(self):
        class Agent:
            mode = 'replay'
            def run(self, purpose, payload, workspace):
                with self.loop.store.tx() as db: db.execute("UPDATE runs SET request='{}'")
                return {'text': json.dumps({'sourceHash': payload['sourceHash']})}
        with tempfile.TemporaryDirectory() as root:
            agent = Agent()
            loop = Loop(Path(root), agent, task_detection=False, stage_pipeline=False)
            agent.loop = loop
            with self.assertRaisesRegex(ValueError, '绑定不一致'):
                request(loop, 'alice', 'front_analysis', 'detect_pairs', {'sourceHash': 'host-hash'}, lambda x: None)


if __name__ == '__main__': unittest.main()
