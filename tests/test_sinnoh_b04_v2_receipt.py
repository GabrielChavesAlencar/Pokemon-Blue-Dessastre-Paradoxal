"""B04 V2 receipt invariants: 648 IDs genuinely reported, future IDs not approved."""
from __future__ import annotations
import copy
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_b04_v2_receipt as v2

class B04V2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=v2.read(v2.RECEIPT)
        cls.b01=v2.read(v2.B01)
        cls.b05=v2.read(v2.B05)
        cls.old=v2.read(v2.OLD)

    def check(self,doc=None):
        return v2.audit(copy.deepcopy(self.receipt if doc is None else doc),
                        copy.deepcopy(self.b01),copy.deepcopy(self.b05),
                        copy.deepcopy(self.old))

    def reject(self,update):
        doc=copy.deepcopy(self.receipt)
        update(doc)
        with self.assertRaisesRegex(ValueError,"SINNOH_B04_V2_BLOCKED"):
            self.check(doc)

    def test_01_all_648_are_confirmed_as_reported(self):
        report=self.check()
        self.assertEqual(report["physical_map_id_count"],648)
        self.assertEqual(report["previously_missing_ids_now_reported"],31)
        self.assertEqual(self.receipt["missing_map_ids_in_v2"],[])
        self.assertEqual(self.receipt["extra_map_ids_in_v2"],[])

    def test_02_hashes_reconcile_b01(self):
        for key in ("mapinfos_sha256","tilesets_sha256"):
            self.assertEqual(self.receipt[key],self.b01[key])
        self.assertEqual(self.receipt["reference_b01_inventory_sha256"],
                         self.b01["inventory_archive_sha256"])

    def test_03_previous_report_still_historically_incomplete(self):
        self.assertEqual(self.old["current_report_physical_count"],617)
        self.assertEqual(self.receipt["recovered_31_omitted_low_ids"],v2.LOW_MISSED)
        self.assertEqual(len(self.receipt["recovered_31_omitted_low_ids"]),31)

    def test_04_regions_counts_and_ids(self):
        self.assertEqual(self.check()["regional_manifest_counts"],
                         {"KANTO":142,"JOHTO":100,"HOENN":199})

    def test_05_unova_candidates_unchanged(self):
        self.assertEqual(self.check()["unova_candidate_count"],174)
        self.assertEqual(self.check()["unova_candidate_contiguous"],[518,599])
        self.assertEqual(self.check()["sinnoh_admin_hold"],[442,517])

    def test_06_modified_archive_sha_rejected(self):
        self.reject(lambda x:x.update(uploaded_zip_sha256="0"*64))

    def test_07_short_inventory_claim_rejected(self):
        self.reject(lambda x:x.update(new_report_physical_count=617))

    def test_08_fake_missing_or_extra_ids_rejected(self):
        self.reject(lambda x:x.update(missing_map_ids_in_v2=[1]))
        self.reject(lambda x:x.update(extra_map_ids_in_v2=[6000]))

    def test_09_wrong_region_range_rejected(self):
        self.reject(lambda x:x["sources"]["HOENN"].update(
            destination_ranges=[{"start":700,"end":999,"count":300}]))

    def test_10_no_new_map_ids_allocated(self):
        self.reject(lambda x:x.update(unova_ids_allocated=True))
        self.reject(lambda x:x.update(source_and_destination_mapids_not_assigned=False))

    def test_11_no_forged_game_or_R07_approval(self):
        for k in ("future_region_reservations_verified","r07_complete",
                  "r08_complete","r09_complete","game_exe_tested",
                  "joiplay_tested","game_or_saves_modified"):
            with self.subTest(key=k):
                self.reject(lambda x,key=k:x.update({key:True}))

    def test_12_no_forged_b_c_d(self):
        for k in ("phase_b_approved","phase_c_approved","phase_d_approved"):
            with self.subTest(key=k):
                self.reject(lambda x,key=k:x.update({key:1}))

    def test_13_self_report_is_not_attestation(self):
        self.assertTrue(self.receipt["installed_claims_are_self_reported_not_independently_attested"])
        self.reject(lambda x:x.update(installed_claims_are_self_reported_not_independently_attested=False))

if __name__=="__main__":unittest.main()
