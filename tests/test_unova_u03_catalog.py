"""U03 guards against false Unova integration in site catalog."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/regions'))
import audit_unova_u03_catalog as u03


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json.loads((ROOT/'data/regions/unova-u03-areas.json').read_text('utf-8'))
        cls.registry=json.loads((ROOT/'site/public/data/regions.json').read_text('utf-8'))['regions']['UNOVA']

    def check_bad(self, mutate):
        obj=copy.deepcopy(self.catalog)
        reg=copy.deepcopy(self.registry)
        mutate(obj,reg)
        with self.assertRaises(ValueError):
            u03.validate(obj,reg)

    def test_01_reference_catalog_valid_but_not_playable(self):
        r=u03.validate(self.catalog,self.registry)
        self.assertEqual(r['catalog_route_count'],18)
        self.assertEqual(r['catalog_gym_count'],8)
        self.assertGreaterEqual(r['catalog_areas'],50)
        self.assertEqual(r['areas_with_real_map_ids'],0)
        self.assertFalse(r['can_install'])
        self.assertFalse(r['game_exe_tested'])

    def test_02_cannot_enable_unova(self):
        self.check_bad(lambda obj,reg: reg.update(status='playable'))

    def test_03_cannot_fake_installer_approval(self):
        self.check_bad(lambda obj,reg: obj.update(may_install=True))

    def test_04_cannot_fake_source_mapid(self):
        self.check_bad(lambda obj,reg: obj['areas'][0].update(source_map_id=123))

    def test_05_cannot_fake_destination_mapid(self):
        self.check_bad(lambda obj,reg: obj['areas'][0].update(destination_map_id=800))

    def test_06_cannot_fake_license(self):
        self.check_bad(lambda obj,reg: obj['areas'][0].update(distribution_rights_verified=True))

    def test_07_cannot_fake_native_game_exe(self):
        self.check_bad(lambda obj,reg: obj['areas'][0].update(game_exe_tested=True))

    def test_08_cannot_hide_route(self):
        self.check_bad(lambda obj,reg: obj['areas'].remove(next(x for x in obj['areas'] if x['key']=='UNOVA_ROUTE_10')))

    def test_09_cannot_remove_gym(self):
        self.check_bad(lambda obj,reg: obj['areas'].remove(next(x for x in obj['areas'] if x['key']=='UNOVA_OPELUCID_GYM')))

    def test_10_cannot_duplicate_area_key(self):
        self.check_bad(lambda obj,reg: obj['areas'].append(copy.deepcopy(obj['areas'][0])))

    def test_11_cannot_silently_change_badge_list(self):
        self.check_bad(lambda obj,reg: reg.update(milestones=['BOULDER']))

    def test_12_cannot_change_white_to_black2(self):
        self.check_bad(lambda obj,reg: obj.update(reference_version='BLACK2'))

    def test_13_cannot_mark_event_as_verified(self):
        self.check_bad(lambda obj,reg: obj['areas'][1].update(npc_events_verified=True))

    def test_14_cannot_forge_phase(self):
        self.check_bad(lambda obj,reg: obj['areas'][0].update(phase='U99'))


if __name__=='__main__':
    unittest.main()
