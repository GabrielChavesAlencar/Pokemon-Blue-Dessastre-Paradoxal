"""Read-only asset-size audit, covering every installed front and back image."""
import importlib.util
import statistics
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
target=ROOT/'scripts/dessastre_paradoxal/sprite_size_audit.py'
spec=importlib.util.spec_from_file_location('sprite_size_audit',target)
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

class SpriteSizeAuditTests(unittest.TestCase):
    def test_all_front_and_back_images_are_legible_and_report_visible_bounds(self):
        sprites=audit.analyze(ROOT)
        self.assertGreaterEqual(len(sprites),65)
        data=[]
        for mon in sprites:
            if mon['pending']:
                continue
            for side in ('front','back'):
                img=mon['sides'].get(side)
                self.assertIsNotNone(img,f"{mon['id']} missing {side}")
                self.assertTrue(img['frameBoxes'][0],f"{mon['id']} empty {side}")
                bbox=img['frameBoxes'][0]
                width,height=bbox[2]-bbox[0],bbox[3]-bbox[1]
                data.append((mon['id'],side,img['frameWidth'],img['height'],width,height,bbox[0],bbox[1],img['frames']))
        for item in data:
            print('SPRITE_AUDIT',','.join(map(str,item)))
        print('SPRITE_AUDIT_TOTAL',len(data))
        self.assertGreaterEqual(len(data),128)
