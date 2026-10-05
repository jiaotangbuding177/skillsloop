import tempfile
import unittest
from pathlib import Path
from skilldemo.core import Loop, Conflict, Forbidden
from skilldemo.runtime import ReplayAgent, validate_bundle
from skilldemo.scenario import scenario
import threading


class LifecycleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.loop = Loop(Path(self.tmp.name), ReplayAgent(), settle_seconds=0, daily_limit=10)
        self.actor = 'alice'

    def tearDown(self):
        self.tmp.cleanup()

    def turn(self, text, skills=None, request_id=None):
        return self.loop.chat(self.actor, 'session-1', text, skills or [], request_id=request_id)

    def create(self):
        self.turn('整理销售周报，必须先扣除退款再汇总收入')
        self.loop.tick()
        rows = self.loop.discover(self.actor)
        self.assertEqual(len(rows), 1)
        candidate = self.loop.generate(self.actor, rows[0]['id'])
        self.assertEqual(candidate['status'], 'READY')
        return candidate

    def test_new_reuse_update_and_rollback(self):
        c = self.create()
        skill = self.loop.accept(self.actor, c['id'])
        self.turn('新任务：整理下一期销售周报', [skill['id']])
        self.loop.tick()
        self.assertEqual(self.loop.discover(self.actor), [])
        self.turn('不对，跨期退款必须单独列出，不能计入本期收入')
        self.loop.tick()
        update = self.loop.discover(self.actor)[0]
        self.assertEqual(update['action'], 'UPDATE')
        self.assertEqual(update['target'], skill['id'])
        self.loop.generate(self.actor, update['id'])
        newer = self.loop.accept(self.actor, update['id'])
        self.assertEqual(newer['version'], 2)
        self.assertIn('跨期退款', newer['files'][0]['content'])
        rolled = self.loop.rollback(self.actor, skill['id'], 1)
        self.assertEqual(rolled['version'], 3)
        self.assertEqual(rolled['hash'], skill['hash'])
        self.assertEqual(self.loop.metrics(self.actor)['learning_calls'], 2)

    def test_noise_unknown_outcome_and_idempotency(self):
        self.turn('你好', request_id='r1')
        self.turn('你好', request_id='r1')
        self.assertEqual(len(self.loop.snapshot(self.actor)['turns']), 1)
        self.loop.tick()
        self.assertEqual(self.loop.discover(self.actor), [])
        c = self.create()
        self.assertEqual(c['input']['trace']['verification'], 'UNKNOWN')

    def test_scope_and_organization_review(self):
        c = self.create()
        with self.assertRaises(Forbidden):
            self.loop.accept('bob', c['id'])
        skill = self.loop.accept('alice', c['id'])
        with self.assertRaises(Forbidden):
            self.loop.chat('bob', 'bob-session', '整理报告', [skill['id']])
        submission = self.loop.submit('alice', c['id'])
        with self.assertRaises(Forbidden):
            self.loop.review('bob', submission['id'], True)
        published = self.loop.review('reviewer', submission['id'], True)
        result = self.loop.chat('bob', 'bob-session', '整理报告', [published['id']])
        self.assertEqual(result['skills'][0]['hash'], published['hash'])

    def test_stale_input_cannot_publish(self):
        c = self.create()
        self.turn('不对，必须改用元而不是万元')
        with self.assertRaises(Conflict):
            self.loop.accept('alice', c['id'])

    def test_budget_preserves_pending_work(self):
        self.loop.daily_limit = 0
        self.turn('整理报告，必须逐行核对金额')
        self.loop.tick()
        c = self.loop.discover('alice')[0]
        blocked = self.loop.generate('alice', c['id'])
        self.assertEqual(blocked['status'], 'QUEUED')
        self.assertEqual(self.loop.metrics('alice')['learning_calls'], 0)

    def test_bundle_paths_are_validated(self):
        with self.assertRaises(ValueError):
            validate_bundle([{'path': '../escape', 'content': 'x'}])

    def test_scenario_repeat_does_not_dispatch_again(self):
        first = scenario(self.loop, review=True)
        second = scenario(self.loop, review=True)
        self.assertEqual(first, second)
        self.assertEqual(self.loop.metrics('alice')['learning_calls'], 2)

    def test_failed_generation_is_not_automatically_retried(self):
        class FailedAgent(ReplayAgent):
            def run(self, purpose, payload, workspace):
                if purpose == 'learn': raise RuntimeError('synthetic failure')
                return super().run(purpose, payload, workspace)
        self.loop.agent = FailedAgent()
        self.turn('整理报告，必须先核对退款再计算收入')
        self.loop.tick()
        c = self.loop.discover('alice')[0]
        self.assertEqual(self.loop.generate('alice', c['id'])['status'], 'FAILED')
        self.loop.generate('alice', c['id'])
        self.assertEqual(self.loop.metrics('alice')['learning_calls'], 1)

    def test_duplicate_running_chat_dispatches_once(self):
        entered, release = threading.Event(), threading.Event()
        class BlockingAgent(ReplayAgent):
            def run(self, purpose, payload, workspace):
                entered.set()
                if not release.wait(5): raise RuntimeError('test timeout')
                return super().run(purpose, payload, workspace)
        self.loop.agent = BlockingAgent()
        worker = threading.Thread(target=lambda: self.turn('整理报告', request_id='same'))
        worker.start()
        try:
            self.assertTrue(entered.wait(3))
            self.assertEqual(self.turn('整理报告', request_id='same')['status'], 'RUNNING')
            with self.assertRaises(Conflict): self.turn('整理其他报告', request_id='different')
        finally:
            release.set(); worker.join(5)
        self.assertEqual(self.loop.metrics('alice')['execution_calls'], 1)

    def test_failed_only_trace_is_deferred(self):
        self.loop.import_turn('alice', {'session':'broken', 'user':'整理报告，必须核对收入', 'assistant':'工具Bug', 'status':'FAILED'})
        self.loop.tick(10**12)
        self.assertEqual(self.loop.discover('alice'), [])
        self.assertEqual(self.loop.snapshot('alice')['traces'][0]['decision']['reason'], 'NO_DELIVERED_MATERIAL')

    def test_mode_contamination_is_rejected(self):
        agent = ReplayAgent(); agent.mode = 'openclaw'
        with self.assertRaises(Conflict): Loop(Path(self.tmp.name), agent)

    def test_organization_update_requires_review_and_preserves_privacy(self):
        c = self.create()
        submission = self.loop.submit('alice', c['id'])
        shared = self.loop.review('reviewer', submission['id'], True)
        self.loop.chat('bob', 'bob-update', '整理销售报告', [shared['id']])
        self.loop.chat('bob', 'bob-update', '不对，跨期退款必须单独列出')
        self.loop.tick()
        update = self.loop.discover('bob')[0]
        self.loop.generate('bob', update['id'])
        pending = self.loop.submit('bob', update['id'])
        self.assertEqual(self.loop.snapshot('alice')['skills'][0]['version'], 1)
        reviewed = self.loop.review('reviewer', pending['id'], True)
        self.assertEqual(reviewed['version'], 2)
        self.assertEqual(self.loop.snapshot('reviewer')['turns'], [])
        self.assertEqual(self.loop.snapshot('outsider')['skills'], [])

    def test_version_compare_and_swap_includes_rollback(self):
        c = self.create(); skill = self.loop.accept('alice', c['id'])
        self.turn('新任务：整理报告', [skill['id']])
        self.turn('不对，必须单独核对退款')
        self.loop.tick(); update = self.loop.discover('alice')[0]
        self.loop.generate('alice', update['id'])
        self.loop.rollback('alice', skill['id'], 1)
        with self.assertRaises(Conflict): self.loop.accept('alice', update['id'])

    def test_explicit_reference_is_owner_scoped(self):
        first = self.turn('整理销售报告')
        linked = self.loop.chat('alice', 'second-session', '补充，必须核对退款', reply_to=first['id'])
        self.assertEqual(linked['taskId'], first['taskId'])
        rejected = self.loop.chat('bob', 'bob-session', '补充，必须核对退款', reply_to=first['id'])
        self.assertNotIn('taskId', rejected)


if __name__ == '__main__':
    unittest.main()
