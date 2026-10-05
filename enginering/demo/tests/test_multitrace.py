import copy
import tempfile
import unittest
from pathlib import Path
from skilldemo.core import Loop, Conflict
from skilldemo.runtime import ReplayAgent, parse_object, digest
from skilldemo.learning import compile_patch


class MultiTraceTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.loop=Loop(Path(self.tmp.name),ReplayAgent(),settle_seconds=0,idle_seconds=0)
    def tearDown(self): self.tmp.cleanup()
    def task(self, session, text, checks=None, actor='alice', answer='先核对规则，再计算结果。'):
        return self.loop.import_turn(actor,{'session':session,'user':text,'assistant':answer,'checks':checks or []})
    def pool(self):
        self.task('a','整理销售周报，必须核对金额单位')
        self.task('b','生成销售月报，必须单独列出跨期退款')
        self.loop.tick()
        return self.loop.discover('alice')[0]
    def test_cluster_complementary_tasks_and_preserve_methods(self):
        c=self.pool()
        self.assertEqual(len(c['input']['traces']),2)
        c=self.loop.generate('alice',c['id']);self.assertEqual(c['status'],'READY',c)
        md=c['files'][0]['content']
        self.assertIn('金额单位',md);self.assertIn('跨期退款',md)
        self.assertEqual(len(c['patchAudit']['analyses']),2)
        self.assertEqual(self.loop.metrics('alice')['learning_calls'],1)
    def test_unrelated_and_cross_owner_not_merged(self):
        self.pool()
        self.task('c','编写招聘面试提纲，必须核对岗位要求')
        self.task('d','整理销售周报，必须核对金额单位',actor='bob')
        self.loop.tick();self.loop.discover('alice');self.loop.discover('bob')
        self.assertEqual(len(self.loop.snapshot('alice')['pools']),2)
        self.assertEqual(len(self.loop.snapshot('bob')['pools']),1)
    def test_secondary_source_revision_blocks_acceptance_and_releases_other(self):
        c=self.pool();self.loop.generate('alice',c['id'])
        self.task('b','不对，跨期退款必须改用新口径')
        with self.assertRaises(Conflict):self.loop.accept('alice',c['id'])
        self.loop.tick();new=self.loop.discover('alice')
        self.assertEqual(sum(len(x['input']['traces']) for x in new),2)
    def test_queued_pool_absorbs_new_arrivals_without_call(self):
        self.task('a','整理销售周报，必须核对金额单位');self.loop.tick()
        first=self.loop.discover('alice')[0]
        self.task('b','整理销售月报，必须核对退款');self.loop.tick()
        self.assertEqual(self.loop.discover('alice'),[])
        c=self.loop.snapshot('alice')['candidates'][0]
        self.assertEqual(c['id'],first['id']);self.assertEqual(len(c['input']['traces']),2)
    def test_outcome_routes_and_unknown_not_dropped(self):
        self.task('a','整理销售报告，必须核对收入',[{'name':'total','expected':90,'actual':90}])
        self.task('b','整理销售报告，必须排除取消订单',[{'name':'total','expected':90,'actual':100}])
        self.task('c','整理销售报告，必须标注单位')
        self.loop.tick();c=self.loop.discover('alice')[0]
        self.assertEqual([e['analyst'] for e in c['input']['evidence']],['success','failure','unknown'])
        self.assertEqual(self.loop.generate('alice',c['id'])['status'],'READY')
    def test_forged_reference_and_omitted_proposal_rejected(self):
        c=self.pool();p=c['input'];o=parse_object(ReplayAgent().run('learn',p,Path(self.tmp.name))['text'])
        bad=copy.deepcopy(o);bad['analyses'][0]['proposals'][0]['evidenceRefs'][0]['quote']='made up'
        with self.assertRaises(ValueError):compile_patch(p,bad)
        bad=copy.deepcopy(o);bad['mergedPatches'].pop()
        with self.assertRaises(ValueError):compile_patch(p,bad)
    def test_failure_guess_cannot_be_applied(self):
        self.task('a','整理销售报告，必须核对收入',[{'name':'total','expected':90,'actual':100}])
        self.loop.tick();c=self.loop.discover('alice')[0];p=c['input']
        o=parse_object(ReplayAgent().run('learn',p,Path(self.tmp.name))['text'])
        o['analyses'][0]['proposals'][0]['evidenceType']='OBSERVED'
        with self.assertRaises(ValueError):compile_patch(p,o)
    def test_conflicting_and_stale_patches_rejected(self):
        c=self.pool();p=c['input'];o=parse_object(ReplayAgent().run('learn',p,Path(self.tmp.name))['text'])
        o['mergedPatches'][0]['operations'][0]['beforeHash']='wrong'
        with self.assertRaises(ValueError):compile_patch(p,o)
    def test_pool_wait_and_budget_preserve_candidate(self):
        self.loop.pool_wait_seconds=3600;c=self.pool()
        self.assertEqual(self.loop.generate('alice',c['id'])['status'],'QUEUED')
        self.assertEqual(self.loop.metrics('alice')['learning_calls'],0)

    def test_two_used_tasks_form_one_update_pool(self):
        c=self.pool();self.loop.generate('alice',c['id']);skill=self.loop.accept('alice',c['id'])
        for session, rule in [('use-a','不对，输出必须包含gross'),('use-b','不对，输出必须包含currency')]:
            self.loop.chat('alice',session,'整理销售报告',[skill['id']])
            self.loop.chat('alice',session,rule)
        self.loop.tick();updates=self.loop.discover('alice')
        self.assertEqual(len(updates),1)
        self.assertEqual(updates[0]['action'],'UPDATE')
        self.assertEqual(len(updates[0]['input']['traces']),2)
        new=self.loop.generate('alice',updates[0]['id']);self.assertEqual(new['status'],'READY',new)
        self.assertIn('gross',new['files'][0]['content']);self.assertIn('currency',new['files'][0]['content'])

    def test_mutually_overlapping_replacements_fail(self):
        c=self.pool();p=c['input'];o=parse_object(ReplayAgent().run('learn',p,Path(self.tmp.name))['text'])
        for index, merged in enumerate(o['mergedPatches']):
            merged['operations']=[{'op':'replace','path':'SKILL.md','beforeHash':p['fileHashes']['SKILL.md'],
                'old':'待补充有依据的步骤。','content':'互斥规则'+str(index)}]
        with self.assertRaises(ValueError):compile_patch(p,o)

    def test_already_published_pool_does_not_release_unmodified_sources(self):
        c=self.pool();self.loop.generate('alice',c['id']);self.loop.accept('alice',c['id'])
        self.task('b','不对，跨期退款必须改用新口径')
        unchanged=next(t for t in self.loop.snapshot('alice')['traces'] if t['session']=='a')
        self.assertEqual(unchanged['decision']['candidateId'],c['id'])

if __name__=='__main__':unittest.main()
