import hashlib
from pathlib import Path
import tempfile
import unittest

from skilldemo.core import Loop


class HistoryArtifactAgent:
    mode = 'replay'

    def __init__(self):
        self.calls = []

    def run(self, purpose, payload, workspace):
        self.calls.append((payload, Path(workspace)))
        if payload['message'] == '生成初稿':
            target = Path(workspace)/'outputs/review.md'
            target.parent.mkdir(parents=True)
            target.write_text('原始交付', encoding='utf-8')
            artifacts = [{'path': 'outputs/review.md', 'bytes': target.stat().st_size,
                          'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}]
        else:
            artifacts = []
        return {'text': '已交付', 'artifacts': artifacts}


class HistoryArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.agent = HistoryArtifactAgent()
        self.loop = Loop(Path(self.tmp.name), self.agent)

    def test_same_session_hash_checked_copy_is_input_not_new_delivery(self):
        first = self.loop.chat('alice', 'case', '生成初稿')
        second = self.loop.chat('alice', 'case', '修订交付')
        payload, workspace = self.agent.calls[-1]
        item = payload['previous_artifacts'][0]
        self.assertTrue(item['available'])
        self.assertEqual(item['runId'], first['runId'])
        self.assertEqual((workspace/item['localPath']).read_text(encoding='utf-8'), '原始交付')
        self.assertFalse((workspace/'outputs/review.md').exists())
        self.assertEqual(second['artifacts'], [])
        self.assertEqual(second['historyArtifacts'], payload['previous_artifacts'])

    def test_other_session_and_other_member_cannot_receive_history_artifact(self):
        self.loop.chat('alice', 'case', '生成初稿')
        self.loop.chat('alice', 'other', '修订交付')
        self.assertEqual(self.agent.calls[-1][0]['previous_artifacts'], [])
        self.loop.chat('bob', 'bob-case', '修订交付')
        self.assertEqual(self.agent.calls[-1][0]['previous_artifacts'], [])

    def test_changed_registered_file_is_not_silently_copied(self):
        first = self.loop.chat('alice', 'case', '生成初稿')
        original = self.loop.store.root/'workspaces'/first['runId']/'outputs/review.md'
        original.write_text('被篡改', encoding='utf-8')
        self.loop.chat('alice', 'case', '修订交付')
        item = self.agent.calls[-1][0]['previous_artifacts'][0]
        self.assertFalse(item['available'])
        self.assertEqual(item['unavailableReason'], 'HISTORY_ARTIFACT_HASH_CHANGED')
        self.assertNotIn('localPath', item)

    def test_deleted_registered_file_is_marked_unavailable(self):
        first = self.loop.chat('alice', 'case', '生成初稿')
        original = self.loop.store.root/'workspaces'/first['runId']/'outputs/review.md'
        original.unlink()
        self.loop.chat('alice', 'case', '修订交付')
        item = self.agent.calls[-1][0]['previous_artifacts'][0]
        self.assertFalse(item['available'])
        self.assertNotIn('localPath', item)


if __name__ == '__main__':
    unittest.main()
