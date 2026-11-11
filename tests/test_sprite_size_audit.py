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

    def test_shiny_front_back_use_the_same_frame_geometry(self):
        sprites=audit.analyze(ROOT)
        checked=0
        for mon in sprites:
            if mon['pending']:continue
            for role in ('front','back'):
                normal=mon['sides'].get(role)
                shiny=mon['sides'].get(role+'-shiny')
                self.assertIsNotNone(shiny,f"{mon['id']} missing {role} shiny")
                self.assertEqual((normal['width'],normal['height'],normal['frames']),
                                 (shiny['width'],shiny['height'],shiny['frames']),
                                 f"{mon['id']} {role} normal/shiny geometry")
                self.assertEqual((normal['frameWidth'],normal['height']),(128,128))
                self.assertTrue(shiny['frameBoxes'][0],f"{mon['id']} {role} shiny blank")
                box=normal['frameBoxes'][0]
                shiny_box=shiny['frameBoxes'][0]
                deviation=max(abs(a-b) for a,b in zip(box,shiny_box))
                if deviation>8:
                    print('SHINY_BOUND_DIFFERENCE',mon['id'],role,box,shiny_box)
                checked+=1
        print('AUDITED_SHINY_PAIRS',checked)
        self.assertEqual(checked,128)

    def test_upstream_decades_reference_sizes_if_available(self):
        """Optional pinned base-game comparison; no network dependency for CI PASS."""
        from urllib.request import Request,urlopen
        commit="ff6091b23603b3298ad72a7584b02a51e1d01c0e"
        for species in ('BULBASAUR','CHARIZARD','GENGAR','SNORLAX','PIKACHU','WALREIN'):
            for role in ('Front','Back'):
                url=("https://raw.githubusercontent.com/HazyCrazy/Pokemon-Decades/"+
                     commit+"/Graphics/Pokemon/"+role+"/"+species+".png")
                try:
                    with urlopen(Request(url,headers={'User-Agent':'blue-sprite-audit'}),timeout=6) as source:
                        parsed=audit.png_bounds(source.read())
                except (OSError,ValueError) as error:
                    print('REFERENCE_UNAVAILABLE',species,role,str(error)[:110])
                    continue
                box=parsed['frameBoxes'][0]
                if box:
                    print('DEC參_REF',species,role,parsed['frameWidth'],parsed['height'],
                          box[2]-box[0],box[3]-box[1],box[0],box[1],parsed['frames'])
