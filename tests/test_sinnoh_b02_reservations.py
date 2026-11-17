"""B02: real B00/B01 metadata crossed against documented CH05 claims."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_b02_reservations as b02

class B02Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=b02.read(b02.B02)
        cls.b00=b02.read(b02.SOURCE)
        cls.b01=b02.read(b02.NATIVE)
        cls.ch05=b02.read(b02.CH05)

    def check(self,d=None,b00=None,b01=None,ch05=None,inventory=None):
        return b02.reconcile(
           copy.deepcopy(self.d if d is None else d),
           copy.deepcopy(self.b00 if b00 is None else b00),
           copy.deepcopy(self.b01 if b01 is None else b01),
           copy.deepcopy(self.ch05 if ch05 is None else ch05),
           inventory=inventory)

    def test_01_b02_real_snapshot_is_consistent(self):
        x=self.check()
        self.assertEqual(x["unoccupied_low_range_count"],250)
        self.assertEqual(x["occupied_johto_range"],100)
        self.assertEqual(x["occupied_hoenn_range"],199)
        self.assertEqual(x["original_sinnoh_id_collisions"],72)
        self.assertFalse(x["r07_complete"])
        self.assertFalse(x["can_install"])

    def test_02_cli_offline_is_informational(self):
        p=subprocess.run([sys.executable,str(b02.ROOT/"scripts/regions/audit_sinnoh_b02_reservations.py")],
                         cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("SINNOH_B02_RESERVATIONS_AUDITED_NOT_APPROVED",p.stdout)

    def test_03_no_fictitious_kanto_future_claims(self):
        self.assertEqual(self.d["kanto_installer_mapping_status"],
                         "DYNAMIC_NO_FUTURE_RESERVATION_MANIFEST")
        self.assertFalse(self.d["kanto_future_reservation_evidence"])
        self.assertEqual(self.d["sinnoh_destination_map_ids"],{})

    def test_04_all_three_future_reservations_unverified(self):
        for field in ("kanto_future_reservation_evidence",
                      "johto_future_reservation_evidence",
                      "hoenn_future_reservation_evidence",
                      "all_future_reservations_verified"):
            x=copy.deepcopy(self.d);x[field]=True
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"B02_BLOCKED"):
                self.check(d=x)

    def test_05_no_false_install_or_native_flags(self):
        for field in ("can_allocate","can_install","r07_complete",
                      "r08_complete","r09_complete","per_asset_rights_verified",
                      "reservation_manifest_reviewed_by_user",
                      "native_playtest_performed","source_mapids_reused_as_destinations"):
            x=copy.deepcopy(self.d);x[field]=True
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"B02_BLOCKED"):
                self.check(d=x)

    def test_06_physical_vacancy_cannot_be_allocated(self):
        for data in ([442],[442,443],{"209":442}):
            x=copy.deepcopy(self.d);x["sinnoh_destination_map_ids"]=data
            with self.subTest(data=data),self.assertRaisesRegex(ValueError,"B02_BLOCKED"):
                self.check(d=x)

    def test_07_protected_johto_hoenn_legacy_range(self):
        x=copy.deepcopy(self.d)
        x["protected_code_claims"][0]["start"]=601
        with self.assertRaises(ValueError):self.check(d=x)
        self.assertEqual(self.d["protected_code_claims_total_slots"],400)

    def test_08_spoofed_map_snapshot_hash(self):
        x=copy.deepcopy(self.d);x["native_mapinfos_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"B02_BLOCKED"):self.check(d=x)

    def test_09_spoofed_real_b01_range_count(self):
        x=copy.deepcopy(self.b01);x["native_occupied_by_range"]["600-699"]=99
        with self.assertRaisesRegex(ValueError,"B02_BLOCKED"):self.check(b01=x)

    def test_10_spoofed_empty_intervals(self):
        x=copy.deepcopy(self.b01);x["conservative_1_to_599_physically_vacant_ranges"][-1]["count"]=159
        with self.assertRaisesRegex(ValueError,"B02_BLOCKED"):self.check(b01=x)

    def test_11_spoofed_donor_collision(self):
        x=copy.deepcopy(self.b01);x["sinnoh_original_ids_not_physically_occupied"].append(209)
        with self.assertRaisesRegex(ValueError,"B02_BLOCKED"):self.check(b01=x)

    def test_12_spoofed_ch05_native_ownership(self):
        x=copy.deepcopy(self.ch05);x["native_snapshot"]["status"]="LOCAL_READ_ONLY"
        with self.assertRaises(ValueError):self.check(ch05=x)

    def test_13_spoofed_hoenn_reservation_scope(self):
        x=copy.deepcopy(self.ch05);x["documented_shared_reservations"][1]["start"]=701
        with self.assertRaises(ValueError):self.check(ch05=x)

    def test_14_modified_labels_are_not_proofs(self):
        x=copy.deepcopy(self.d);x["native_label_samples"]["800"]="Sinnoh"
        with self.assertRaisesRegex(ValueError,"B02_BLOCKED"):self.check(d=x)

    def test_15_inventory_without_real_zip_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError,"B02_BLOCKED"):
                self.check(inventory=Path(folder)/"inventario-inexistente.zip")

    def test_16_b_c_d_never_approved(self):
        for field in ("phase_b_approved","phase_c_approved","phase_d_approved"):
            x=copy.deepcopy(self.d);x[field]=1
            with self.subTest(field=field),self.assertRaisesRegex(ValueError,"B02_BLOCKED"):
                self.check(d=x)
        self.assertEqual(self.check()["phase_b_approved"],0)

if __name__=="__main__":unittest.main()
