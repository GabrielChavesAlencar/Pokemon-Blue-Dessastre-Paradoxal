"""Real source atlas is structural evidence only, never import permission."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_e05_source_map_atlas as atlas


class SourceMapAtlasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(atlas.ATLAS.read_text("utf-8"))
        cls.observed=json.loads(atlas.OBSERVATION.read_text("utf-8"))

    def test_01_real_dimensions_and_zero_events(self):
        out=atlas.validate(self.data,self.observed)
        self.assertEqual(out["donor_branch_maps"],64)
        self.assertEqual(out["maps_20x15"],56)
        self.assertEqual(out["maps_larger"],8)
        self.assertEqual(out["events"],0)
        self.assertFalse(out["rights_verified"])
        self.assertFalse(out["may_install"])
        self.assertFalse(out["tiles_drawing_verified"])

    def test_02_mapids_are_donor_only(self):
        self.assertTrue(all(x["destination_map_id"] is None for x in self.data["maps"]))
        self.assertTrue(all(x["game_exe_tested"] is False for x in self.data["maps"]))
        self.assertTrue(all(x["rights_verified"] is False for x in self.data["maps"]))

    def test_03_forged_events_fail(self):
        obj=copy.deepcopy(self.data)
        obj["maps"][0]["event_count"]=1
        with self.assertRaises(ValueError):
            atlas.validate(obj,self.observed)

    def test_04_forged_tile_visual_verification_fail(self):
        obj=copy.deepcopy(self.data)
        obj["maps"][3]["geometry_verified_visually"]=True
        with self.assertRaises(ValueError):
            atlas.validate(obj,self.observed)

    def test_05_fake_destination_mapid_fail(self):
        obj=copy.deepcopy(self.data)
        obj["maps"][4]["destination_map_id"]=999
        with self.assertRaises(ValueError):
            atlas.validate(obj,self.observed)

    def test_06_fake_area_rights_fail(self):
        obj=copy.deepcopy(self.data)
        obj["maps"][4]["rights_verified"]=True
        with self.assertRaises(ValueError):
            atlas.validate(obj,self.observed)

    def test_07_wrong_map_dimensions_fail(self):
        obj=copy.deepcopy(self.data)
        obj["maps"][3]["width_tiles"]=999
        with self.assertRaises(ValueError):
            atlas.validate(obj,self.observed)

    def test_08_missing_map_fail(self):
        obj=copy.deepcopy(self.data)
        obj["maps"].pop()
        with self.assertRaises(ValueError):
            atlas.validate(obj,self.observed)

    def test_09_duplicate_id_fail(self):
        obj=copy.deepcopy(self.data)
        obj["maps"][1]["source_map_id"]=obj["maps"][0]["source_map_id"]
        with self.assertRaises(ValueError):
            atlas.validate(obj,self.observed)

    def test_10_wrong_zip_sha_fails(self):
        obj=copy.deepcopy(self.data)
        obj["source_zip_sha256"]="0"*64
        with self.assertRaises(ValueError):
            atlas.validate(obj,self.observed)

    def test_11_observation_dimension_count_fails(self):
        obs=copy.deepcopy(self.observed)
        obs["source_unova_map_dimensions_20x15"]=55
        with self.assertRaises(ValueError):
            atlas.validate(self.data,obs)

    def test_12_donor_64_is_not_proof_of_tiles_or_gameplay(self):
        out=atlas.validate(self.data,self.observed)
        self.assertFalse(out["gameplay_verified"])
        self.assertEqual(self.data["maps_with_20x15_dimensions"],56)
        self.assertTrue(self.data["dimensions_do_not_verify_tile_content"])


if __name__=="__main__":
    unittest.main()
