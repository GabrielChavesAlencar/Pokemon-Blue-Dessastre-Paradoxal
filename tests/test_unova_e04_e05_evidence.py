"""Evidence gates: real external-source observations do not approve gameplay."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_e04_e05_evidence as evidence


class ObservationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.observed=json.loads(evidence.DEFAULT.read_text("utf-8"))

    def changed(self,field,value):
        row=copy.deepcopy(self.observed)
        row[field]=value
        with self.assertRaises(ValueError):
            evidence.validate(row)

    def test_01_real_snapshot_passes_without_license(self):
        result=evidence.validate(self.observed)
        self.assertTrue(result["e04_completed"])
        self.assertTrue(result["e05_completed"])
        self.assertEqual(result["unova_candidate_maps_read"],64)
        self.assertEqual(result["unova_events_found"],0)
        self.assertFalse(result["redistribution_allowed"])
        self.assertFalse(result["can_install"])
        self.assertFalse(result["gameplay_verified"])

    def test_02_source_sha_changed_fails(self):
        self.changed("archive_sha256","0"*64)

    def test_03_archive_size_changed_fails(self):
        self.changed("archive_size_bytes",208057673)

    def test_04_cannot_forge_one_npc_event(self):
        self.changed("unova_parent_event_containers",1)

    def test_05_cannot_forge_source_map_parsing(self):
        self.changed("unova_parent_maps_parsed",65)

    def test_06_cannot_approve_game_exe(self):
        self.changed("game_exe_tested",True)

    def test_07_cannot_forge_asset_redistribution(self):
        self.changed("music_rights_verified",True)

    def test_08_cannot_infer_author_signed_hash(self):
        self.changed("source_sha256_published_by_author",True)

    def test_09_cannot_forge_destination_mapids(self):
        self.changed("destination_mapids_assigned",True)

    def test_10_cannot_miscount_other_regions_as_unova(self):
        self.changed("source_area_matches_inside_unova_parent",41)

    def test_11_forged_origin_link_fails(self):
        self.changed("source_published_by_author","https://evil.example")

    def test_12_source_map_examples_must_be_real_ids(self):
        row=copy.deepcopy(self.observed)
        row["source_map_examples"]["Nuvema_Town"]=999
        with self.assertRaises(ValueError):
            evidence.validate(row)

    def test_13_source_rights_remain_pending(self):
        self.changed("e06_asset_rights_completed",True)

    def test_14_android_not_tested(self):
        self.changed("android_tested",True)

    def test_15_evidence_run_must_be_exact(self):
        row=copy.deepcopy(self.observed)
        row["evidence"]["source_audit_run"]="https://example.com/fake"
        with self.assertRaises(ValueError):
            evidence.validate(row)


if __name__=="__main__":
    unittest.main()
