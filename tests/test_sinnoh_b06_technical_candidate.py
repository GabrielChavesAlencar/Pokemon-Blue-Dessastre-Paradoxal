"""B06 checks real-map hash candidate is *not* an authorized native allocation."""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_b06_technical_candidate as b06

class B06Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=b06.load(b06.B06)
        cls.b00=b06.load(b06.B00)
        cls.b01=b06.load(b06.B01)
        cls.b04=b06.load(b06.B04)
        cls.b05=b06.load(b06.B05)

    def check(self,m=None,b00=None,b01=None,b04=None,b05=None):
        return b06.audit(
          copy.deepcopy(self.m if m is None else m),
          copy.deepcopy(self.b00 if b00 is None else b00),
          copy.deepcopy(self.b01 if b01 is None else b01),
          copy.deepcopy(self.b04 if b04 is None else b04),
          copy.deepcopy(self.b05 if b05 is None else b05))

    def reject(self,fn):
        m=copy.deepcopy(self.m);fn(m)
        with self.assertRaisesRegex(ValueError,"SINNOH_B06_BLOCKED"):
            self.check(m=m)

    def test_01_all_76_candidates_are_not_installed(self):
        r=self.check()
        self.assertEqual(r["candidate_total"],76)
        self.assertEqual(r["real_terrain"],54)
        self.assertEqual(r["empty_placeholders"],22)
        self.assertFalse(r["may_install"])
        self.assertFalse(r["r07_complete"])

    def test_02_twinleaf_candidate_first_terrain_id(self):
        self.assertEqual(self.check()["twinleaf_candidate"],442)
        self.assertEqual(self.m["remap_preview"][0],{
          "source_map_id":209,"candidate_destination_map_id":442,"category":"TERRAIN"})

    def test_03_terrain_before_22_empty_placeholders(self):
        x=self.m["remap_preview"]
        self.assertEqual(len(x),76)
        self.assertTrue(all(row["category"]=="TERRAIN" for row in x[:54]))
        self.assertTrue(all(row["category"]=="EMPTY_PLACEHOLDER" for row in x[54:]))

    def test_04_no_original_source_ids_as_native_destination(self):
        rows=self.m["remap_preview"]
        self.assertEqual({i["candidate_destination_map_id"] for i in rows},set(range(442,518)))
        self.assertEqual(len({i["source_map_id"] for i in rows}),76)

    def test_05_unova_174_candidates_are_untouched(self):
        self.assertEqual(self.check()["unova_candidate_map_ids_preserved"],174)

    def test_06_duplicated_destination_rejected(self):
        self.reject(lambda x:x["remap_preview"][1].update(candidate_destination_map_id=442))

    def test_07_overwrite_native_kanto_rejected(self):
        self.reject(lambda x:x["remap_preview"][0].update(candidate_destination_map_id=300))

    def test_08_use_unova_destination_rejected(self):
        self.reject(lambda x:x["remap_preview"][0].update(candidate_destination_map_id=518))

    def test_09_bad_source_classification_rejected(self):
        self.reject(lambda x:x["remap_preview"][0].update(category="EMPTY_PLACEHOLDER"))

    def test_10_missing_source_id_rejected(self):
        self.reject(lambda x:x["remap_preview"].pop())

    def test_11_false_future_reservations_rejected(self):
        self.reject(lambda x:x.update(future_kanto_johto_hoenn_reservations_approved=True))

    def test_12_false_rights_or_native_stage_rejected(self):
        for name in ("source_binary_redistribution_allowed",
                     "source_per_asset_rights_verified","stage_written",
                     "native_destinations_allocated","game_data_or_saves_modified"):
            with self.subTest(field=name):
                self.reject(lambda x,k=name:x.update({k:True}))

    def test_13_false_gameplay_or_progress_rejected(self):
        for name in ("game_exe_tested","joiplay_tested","r07_complete",
                     "r08_complete","r09_complete","can_install"):
            with self.subTest(field=name):
                self.reject(lambda x,k=name:x.update({k:True}))
        self.reject(lambda x:x.update(phase_b_technically_approved=1))

    def test_14_tileset_31_must_not_reuse_native_id(self):
        self.assertEqual(self.m["source_tileset_references"],[1,31])
        self.assertEqual(self.m["source_to_native_tileset_mapping"],{})
        self.reject(lambda x:x.update(source_to_native_tileset_mapping={"31":31}))

    def test_15_source_hash_digest_tampering_rejected(self):
        self.reject(lambda x:x.update(source_76_map_sha256_list_digest="f"*64))

    def test_16_native_baseline_change_rejected(self):
        m=copy.deepcopy(self.b01);m["mapinfos_sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"SINNOH_B06_BLOCKED"):
            self.check(b01=m)

    def test_17_b04_v2_inventory_must_be_complete(self):
        m=copy.deepcopy(self.b04);m["new_report_physical_count"]=617
        with self.assertRaisesRegex(ValueError,"SINNOH_B06_BLOCKED"):
            self.check(b04=m)

    def test_18_b05_occupied_set_revalidated(self):
        m=copy.deepcopy(self.b05)
        m["occupied"]["ranges"][0]["end"]=2
        m["occupied"]["ranges"][0]["count"]=2
        with self.assertRaisesRegex(ValueError,"SINNOH_B06_BLOCKED"):
            self.check(b05=m)

    def test_19_cannot_verify_fake_source_zip(self):
        with tempfile.TemporaryDirectory() as directory:
            fake=Path(directory)/"donor.zip"
            fake.write_bytes(b"no donor here")
            with self.assertRaisesRegex(ValueError,"SINNOH_B06_BLOCKED"):
                b06.verify_source_zip(fake,self.m,self.b00)

    def test_20_cannot_verify_fake_native_zip(self):
        with tempfile.TemporaryDirectory() as directory:
            fake=Path(directory)/"native.zip"
            fake.write_bytes(b"no native here")
            with self.assertRaisesRegex(ValueError,"SINNOH_B06_BLOCKED"):
                b06.verify_native_zip(fake,self.m,self.b05)

    def test_21_candidate_must_keep_source_maps_in_full(self):
        m=copy.deepcopy(self.b00)
        m["terrain_filled_ids"]=m["terrain_filled_ids"][:-1]
        with self.assertRaisesRegex(ValueError,"SINNOH_B06_BLOCKED"):
            self.check(b00=m)

if __name__=="__main__":unittest.main()
