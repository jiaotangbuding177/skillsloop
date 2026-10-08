import json
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from trajectory_ingest import normalize

class InputContract(unittest.TestCase):
    def item(self):
        return {'task_id':'fixture-only','instruction':'fixture, never learning data',
            'task_completed':None,'traj':[{'index':0,'image':'0.png',
                'value':{'code':'fixture_action','observation':'publisher text','thought':'excluded'}}]}
    def test_missing_screenshot_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(ValueError,'Missing'):
                normalize(self.item(),Path(root),'fixture-family')
    def test_unknown_outcome_and_synthetic_observation_are_preserved(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root);Image.new('RGB',(2,2),'white').save(p/'0.png')
            data=normalize(self.item(),p,'fixture-family')
            self.assertIsNone(data['task_outcome']['publisher_task_completed'])
            self.assertIsNone(data['task_outcome']['benchmark_score'])
            self.assertNotIn('excluded',json.dumps(data))
            self.assertIn('publisher-synthesized',data['frames'][0]['observation_origin'])
    def test_order_loss_is_rejected(self):
        item=self.item();item['traj'][0]['index']=2
        with self.assertRaisesRegex(ValueError,'ordering'):normalize(item,Path('.'),'fixture-family')
    def test_ambiguous_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root)
            for sub in ('a','b'):
                (p/sub).mkdir();(p/sub/'0.png').write_bytes(b'fixture')
            with self.assertRaisesRegex(ValueError,'ambiguous'):normalize(self.item(),p,'fixture-family')
    def test_unsafe_image_reference_is_rejected(self):
        item=self.item();item['traj'][0]['image']='../0.png'
        with self.assertRaisesRegex(ValueError,'Unsafe'):normalize(item,Path('.'),'fixture-family')
    def test_corrupt_image_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            p=Path(root);(p/'0.png').write_bytes(b'not an image')
            with self.assertRaises(Exception):normalize(self.item(),p,'fixture-family')

if __name__=='__main__':unittest.main()
