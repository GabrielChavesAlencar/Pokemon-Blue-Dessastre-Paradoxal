"""Verify the real B01 inventory receipt cannot promote native approval."""
import copy
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RECEIPT=ROOT/"data/regions/sinnoh-b01-actual-native.json"
SOURCE=ROOT/"data/regions/sinnoh-b00-actual-source.json"
SHA=re.compile(r"[0-9a-f]{64}\Z")

class RealB01ReceiptTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=json.loads(RECEIPT.read_text("utf-8"))
        cls.source=json.loads(SOURCE.read_text("utf-8"))

    def test_01_real_source_is_pinned(self):
        r=self.receipt
        self.assertEqual(r["source_sinnoh_archive_sha256"],
                         self.source["source_zip_sha256"])
        self.assertEqual(r["sinnoh_source_map_count"],len(self.source["sinnoh_map_ids"]))
        self.assertEqual(r["sinnoh_source_map_count"],76)
        for k in ("source_sinnoh_archive_sha256","inventory_archive_sha256",
                  "mapinfos_sha256","tilesets_sha256"):
            self.assertIsNotNone(SHA.fullmatch(r[k]),k)

    def test_02_collision_partition_matches_exact_b00_ids(self):
        r=self.receipt
        source=set(self.source["sinnoh_map_ids"])
        collisions=set(r["sinnoh_original_ids_colliding_with_decades"])
        not_occupied=set(r["sinnoh_original_ids_not_physically_occupied"])
        self.assertEqual(len(source),76)
        self.assertEqual(len(collisions),72)
        self.assertEqual(not_occupied,{5,899,900,906})
        self.assertFalse(collisions & not_occupied)
        self.assertEqual(collisions | not_occupied,source)
        self.assertEqual(r["sinnoh_original_ids_outside_conservative_1_to_599"],
            sorted(source-set(range(1,600))))

    def test_03_native_mapinfos_and_files_are_consistent(self):
        r=self.receipt
        self.assertEqual(r["native_registered_map_count"],648)
        self.assertEqual(r["native_physical_map_count"],648)
        self.assertEqual(r["native_occupied_map_count"],648)
        self.assertEqual(r["native_indexed_without_physical_map"],[])
        self.assertEqual(r["native_physical_without_index"],[])
        self.assertEqual(sum(r["native_occupied_by_range"].values()),648)

    def test_04_vacant_ranges_only_report_occupancy(self):
        r=self.receipt
        bands=r["conservative_1_to_599_physically_vacant_ranges"]
        self.assertEqual(sum(x["count"] for x in bands),250)
        self.assertEqual(bands[-1],{"first":442,"last":599,"count":158})
        self.assertEqual(r["native_occupied_by_range"]["1-599"]+250,599)
        self.assertTrue(r["enough_physical_ids_for_76"])
        self.assertFalse(r["future_kanto_johto_hoenn_reservations_verified"])
        self.assertFalse(r["destination_ids_allocated"])

    def test_05_do_not_reuse_donor_tileset_ids(self):
        r=self.receipt
        self.assertEqual(r["donor_tilesets"]["31"],"SinnohCompleteTileset")
        self.assertEqual(r["installed_tilesets"]["31"],"FRLG_Preview_Mart interior")
        self.assertFalse(r["native_and_donor_tileset_names_match"])

    def test_06_receipt_never_claims_installed_or_playable(self):
        r=self.receipt
        for field in ("individual_asset_rights_verified","stage_or_remap_performed",
                      "destination_ids_allocated","can_install","can_mark_native_playable",
                      "user_saves_modified","game_exe_tested","joiplay_tested"):
            with self.subTest(field=field):
                self.assertIs(r[field],False)
        for field in ("phase_b_technically_approved","phase_c_playable_approved",
                      "phase_d_native_approved"):
            self.assertEqual(r[field],0)

if __name__=="__main__":unittest.main()
