import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from skilldemo.bootstrap import initialize, package, draft_files
from skilldemo.core import Loop, Forbidden
from skilldemo.runtime import ReplayAgent

class PackagingTests(unittest.TestCase):
    def test_creator_maintenance_does_not_recursively_generate_another_skill(self):
        with tempfile.TemporaryDirectory() as d:
            loop=Loop(Path(d),ReplayAgent(),settle_seconds=0)
            t=loop.chat('alice','manual','/skill-creator 生成周报技能，必须核对退款')
            loop.tick();self.assertEqual(loop.discover('alice'),[])
            self.assertEqual(t['association'],'MAINTENANCE')
            self.assertEqual(loop.metrics('alice')['learning_calls'],0)

    def test_draft_excludes_generated_python_cache(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);p=root/'draft/scripts/__pycache__/helper.pyc'
            p.parent.mkdir(parents=True);p.write_bytes(b'\x80\xff')
            (p.parent.parent/'helper.py').write_text('print(1)',encoding='utf-8')
            self.assertEqual([f['path'] for f in draft_files(root)],['scripts/helper.py'])

    def test_official_creator_packages_valid_skill_and_download_is_scoped(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);initialize(root)
            self.assertTrue((root/'.foundation/skill-creator/SKILL.md').exists())
            loop=Loop(root/'db',ReplayAgent(),settle_seconds=0)
            loop.chat('alice','s','整理报告，必须核对退款');loop.tick()
            c=loop.discover('alice')[0];c=loop.generate('alice',c['id']);s=loop.accept('alice',c['id'])
            packed=package(root,s['files'])
            with zipfile.ZipFile(root/packed['path']) as z: self.assertTrue(any(n.endswith('/SKILL.md') for n in z.namelist()))
            with zipfile.ZipFile(io.BytesIO(loop.export_skill('alice',s['id']))) as z: self.assertIn(s['id']+'/SKILL.md',z.namelist())
            with self.assertRaises(Forbidden):loop.export_skill('bob',s['id'])

    def test_artifact_requires_owner_and_registered_path(self):
        with tempfile.TemporaryDirectory() as d:
            loop=Loop(Path(d),ReplayAgent());r='r1'
            p=loop.store.root/'workspaces'/r/'outputs/a.txt';p.parent.mkdir(parents=True);p.write_text('ok')
            with loop.store.tx() as db:
                db.execute('INSERT INTO runs(id,owner,purpose,mode,status,started,request,result) VALUES(?,?,?,?,?,?,?,?)',
                    (r,'alice','chat','replay','COMPLETED',0,'{}',json.dumps({'artifacts':[{'path':'outputs/a.txt'}]})))
            self.assertEqual(loop.artifact('alice',r,'outputs/a.txt').read_text(),'ok')
            for actor,path in [('bob','outputs/a.txt'),('alice','../.env')]:
                with self.assertRaises(Forbidden):loop.artifact(actor,r,path)
