"""B04 re-execution receipt must not invent 648 IDs or approved reservations."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
RERUN=ROOT/"data/regions/sinnoh-b04-rerun-receipt.json"
B01=ROOT/"data/regions/sinnoh-b01-actual-native.json"
B05=ROOT/"data/regions/sinnoh-b05-mapid-planning.json"

class B04RerunReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=json.loads(RERUN.read_text("utf-8"))
        cls.b01=json.loads(B01.read_text("utf-8"))
        cls.b05=json.loads(B05.read_text("utf-8"))

    def test_01_baseline_hashes_match_original(self):
        self.assertEqual(self.r["mapinfos_sha256"],self.b01["mapinfos_sha256"])
        self.assertEqual(self.r["tilesets_sha256"],self.b01["tilesets_sha256"])
        self.assertEqual(self.r["prior_zip_sha256"],self.b05["evidence"]["b04_provenance_zip_sha256"])
        self.assertRegex(self.r["uploaded_zip_sha256"],r"^[0-9a-f]{64}$")

    def test_02_second_report_does_not_claim_648_ids(self):
        self.assertTrue(self.r["json_payload_identical_to_prior"])
        self.assertEqual(self.r["current_report_physical_count"],617)
        self.assertEqual(self.r["reference_b01_physical_count"],648)
        self.assertEqual(self.r["ids_missing_relative_to_b01"],
                         self.b05["evidence"]["b04_unreported_b01_map_ids"])
        self.assertEqual(len(self.r["ids_missing_relative_to_b01"]),31)

    def test_03_planning_hold_and_unova_candidates_unchanged(self):
        self.assertEqual(self.r["sinnoh_planning_hold_range"],[442,517])
        self.assertEqual(self.r["unova_physical_candidates_count"],174)
        self.assertEqual(self.r["unova_largest_candidate_range"],[518,599])
        self.assertEqual(self.r["sinnoh_planning_hold_range"],
              [self.b05["sinnoh"]["administrative_planning_hold"]["start"],
               self.b05["sinnoh"]["administrative_planning_hold"]["end"]])

    def test_04_v2_not_claimed_as_windows_tested(self):
        self.assertFalse(self.r["new_collector_executed_on_users_windows"])
        self.assertEqual(self.r["new_collect_script_package"],"SINNOH_B04_COLETOR_V2_VALIDADO.zip")
        self.assertTrue(self.r["new_collector_guards_648_ids_when_hashes_equal"])

    def test_05_bars_and_native_work_still_blocked(self):
        for name in ("future_reservations_fully_verified","sinnoh_mapids_allocated",
                     "unova_mapids_allocated","r07_complete","game_exe_tested",
                     "joiplay_tested","main_game_files_or_saves_modified"):
            self.assertIs(self.r[name],False,name)
        for name in ("phase_b_approved","phase_c_approved","phase_d_approved"):
            self.assertEqual(self.r[name],0,name)

if __name__=="__main__":unittest.main()
