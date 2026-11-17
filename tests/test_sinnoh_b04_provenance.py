"""B04 synthetic ZIP validations: source claims do not authorize gameplay."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_b04_provenance as b04

class B04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=b04.load(b04.SPEC_PATH)
        cls.b01=b04.load(b04.B01_PATH)
        cls.b03=b04.load(b04.B03_PATH)

    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp=Path(tmp.name)
        self.zip=self.tmp/"SINNOH_B04_PROVENIENCIA_REGIONAL.zip"
        self.report=self.fixture()

    def fixture(self):
        p=list(range(1,350))+list(range(600,700))+list(range(700,899))
        reg={}
        for name in b04.REGIONS:
            n=self.spec["expected_regions"][name]["expected_map_count"]
            dest=(list(range(600,700)) if name=="JOHTO" else
                  list(range(700,899)) if name=="HOENN" else
                  list(range(1,143)))
            reg[name]={
                "presence":"FOUND_PARSED",
                "source_file":self.spec["expected_regions"][name]["filename"],
                "sha256":"a"*64,"reported_schema":1,
                "reported_region":None if name=="KANTO" else name,
                "manifest_status":self.spec["expected_regions"][name]["required_manifest_status"],
                "source_map_count":n,"destination_map_ids":dest,
                "source_to_destination":{} if name=="JOHTO"
                    else {str(i+1):v for i,v in enumerate(dest)},
                "invalid_map_entries":0,"duplicate_destination_ids":False,
                "source_id_mapping_is_complete_proof":False,
                "future_reservations_proven":False,
                "native_gameplay_tested":False,
            }
        return {
            "schema":1,"mode":"SINNOH_B04_LOCAL_REGIONAL_PROVENANCE_READ_ONLY",
            "region":"SINNOH",
            "reference_mapinfos_sha256":self.b01["mapinfos_sha256"],
            "reference_tilesets_sha256":self.b01["tilesets_sha256"],
            "mapinfos_sha256":self.b01["mapinfos_sha256"],
            "tilesets_sha256":self.b01["tilesets_sha256"],
            "same_b01_baseline":True,
            "physical_map_ids":p,"regions":reg,
            "future_reservation_manifests_included":False,
            "future_reservations_fully_verified":False,
            "may_allocate_sinnoh_ids":False,"can_install":False,
            "game_or_saves_modified":False,"native_gameplay_tested":False,
            "source_paths_included":False,"raw_manifests_included":False,
        }

    def pack(self,report=None,extra=None):
        report=self.report if report is None else report
        files={"native_provenance.json":b"\xef\xbb\xbf"+json.dumps(report).encode("utf8"),
               "LEIA_ME.txt":b"Resumo local; nao contem arquivos do jogo"}
        if extra:files.update(extra)
        with zipfile.ZipFile(self.zip,"w",zipfile.ZIP_DEFLATED) as z:
            for name,data in files.items():z.writestr(name,data)

    def run_check(self,report=None):
        self.pack(report)
        return b04.audit_zip(self.zip,self.spec,self.b01,self.b03)

    def assert_blocked(self,report=None,extra=None):
        self.pack(report,extra)
        with self.assertRaisesRegex(ValueError,"SINNOH_B04_BLOCKED"):
            b04.audit_zip(self.zip,self.spec,self.b01,self.b03)

    def test_01_no_input_preflight_is_safe(self):
        self.assertEqual(self.spec["status"],
                         "ONE_CLICK_COLLECTOR_READY_LOCAL_PROVENANCE_NOT_RECEIVED")
        self.assertFalse(self.spec["can_install"])
        b04.checked_contract(self.spec,self.b01,self.b03)

    def test_02_three_installation_manifests_do_not_prove_future(self):
        result=self.run_check()
        self.assertEqual(result["installed_region_claims_matching_contract"],3)
        self.assertEqual(result["status"],
          "THREE_INSTALLED_MANIFESTS_REPORTED_FUTURE_RESERVATIONS_STILL_UNKNOWN")
        self.assertFalse(result["future_reservations_proven"])
        self.assertFalse(result["r07_complete"])
        self.assertFalse(result["can_install"])
        self.assertEqual(result["phase_b_approved"],0)

    def test_03_current_snapshot_648_ids(self):
        result=self.run_check()
        self.assertTrue(result["b01_baseline_matches_current_hashes"])
        self.assertEqual(result["physical_map_ids_reported"],648)
        self.assertEqual(result["conflicting_installed_destination_ids"],[])

    def test_04_missing_johto_manifest_is_not_failure_or_approval(self):
        r=self.report["regions"]["JOHTO"]
        r.update(presence="MISSING",sha256=None,reported_schema=None,
                 reported_region=None,manifest_status=None,
                 source_map_count=0,destination_map_ids=[],
                 source_to_destination={},invalid_map_entries=0)
        self.assertEqual(self.run_check()["status"],
                         "PARTIAL_OR_INVALID_REGIONAL_PROVENANCE")

    def test_05_updated_decades_baseline_requires_new_b01(self):
        self.report["mapinfos_sha256"]="0"*64
        self.report["same_b01_baseline"]=False
        self.assertEqual(self.run_check()["status"],"BASELINE_CHANGED_REQUIRES_NEW_B01")

    def test_06_forged_same_baseline_rejected(self):
        self.report["tilesets_sha256"]="0"*64
        self.assert_blocked()

    def test_07_forged_map_count_rejected(self):
        self.report["physical_map_ids"].pop()
        self.assert_blocked()

    def test_08_installed_map_id_collision_reported_but_not_approved(self):
        k=self.report["regions"]["KANTO"]
        k["source_to_destination"]["1"]=600
        k["destination_map_ids"]=sorted(set(k["source_to_destination"].values()))
        result=self.run_check()
        self.assertIn(600,result["conflicting_installed_destination_ids"])
        self.assertEqual(result["status"],
                         "INSTALLED_REGIONAL_ID_COLLISIONS_NEED_REVIEW")
        self.assertFalse(result["can_install"])

    def test_09_forged_reservations_rejected(self):
        for key in ("future_reservations_fully_verified",
                    "future_reservation_manifests_included",
                    "may_allocate_sinnoh_ids"):
            with self.subTest(key=key):
                r=copy.deepcopy(self.report);r[key]=True
                self.assert_blocked(r)

    def test_10_no_private_source_or_save_files_allowed(self):
        for key in ("source_paths_included","raw_manifests_included",
                    "game_or_saves_modified","native_gameplay_tested"):
            with self.subTest(key=key):
                r=copy.deepcopy(self.report);r[key]=True
                self.assert_blocked(r)

    def test_11_reject_extra_files_inside_zip(self):
        self.assert_blocked(extra={"Save01.rxdata":b"NEVER SHARE"})

    def test_12_reject_zip_slip(self):
        self.assert_blocked(extra={"../game/Data/Map001.rxdata":b"NO"})

    def test_13_reject_duplicate_zip_entries(self):
        self.pack()
        with zipfile.ZipFile(self.zip,"a") as z:
            z.writestr("native_provenance.json",b"overwritten")
        with self.assertRaises(ValueError):
            b04.read_zip(self.zip)

    def test_14_reject_mapping_with_non_numeric_path(self):
        k=self.report["regions"]["KANTO"]
        k["source_to_destination"]["C:/Users/secret"]=1
        self.assert_blocked()

    def test_15_johto_cannot_claim_foreign_map_id(self):
        j=self.report["regions"]["JOHTO"]
        j["destination_map_ids"][0]=500
        j["destination_map_ids"].sort()
        result=self.run_check()
        self.assertFalse(result["regional_installation_claims"]["JOHTO"]
                         ["installed_claim_matches_known_contract"])
        self.assertFalse(result["can_install"])

    def test_16_native_manifest_sha_must_have_valid_shape(self):
        self.report["regions"]["KANTO"]["sha256"]="not a sha"
        self.assert_blocked()

    def test_17_reject_unreported_missing_json_file(self):
        self.pack()
        with zipfile.ZipFile(self.zip,"w") as z:
            z.writestr("LEIA_ME.txt","no report")
        with self.assertRaisesRegex(ValueError,"SINNOH_B04_BLOCKED"):
            b04.read_zip(self.zip)

    def test_18_bytes_unchanged_by_auditor(self):
        self.pack()
        before=hashlib.sha256(self.zip.read_bytes()).hexdigest()
        for i in range(2):
            b04.audit_zip(self.zip,self.spec,self.b01,self.b03)
        self.assertEqual(hashlib.sha256(self.zip.read_bytes()).hexdigest(),before)

    def test_19_contract_approval_tampering_refused(self):
        s=copy.deepcopy(self.spec);s["phase_b_approved"]=1
        with self.assertRaisesRegex(ValueError,"SINNOH_B04_BLOCKED"):
            b04.checked_contract(s,self.b01,self.b03)

    def test_20_reserved_tileset_and_map_cannot_appear_from_zip(self):
        self.report["regions"]["HOENN"]["future_reservations_proven"]=True
        self.assert_blocked()

    def test_21_invalid_region_report_is_not_valid_installation(self):
        self.report["regions"]["HOENN"]["reported_region"]="SINNOH"
        result=self.run_check()
        self.assertEqual(result["installed_region_claims_matching_contract"],2)
        self.assertFalse(result["can_install"])

    def test_22_extra_region_rejected(self):
        self.report["regions"]["SINNOH"]={}
        self.assert_blocked()

    def test_23_old_collector_missed_31_low_ids_is_recognized_not_certified(self):
        # Actual uploaded B04 had exact long-ID subset and no maps 1..99.
        self.report["physical_map_ids"]=(
            list(range(100,276))+list(range(300,442))+list(range(600,899)))
        report=self.run_check()
        self.assertEqual(report["physical_map_ids_reported"],617)
        self.assertTrue(report["legacy_collector_short_ids_omitted"])
        self.assertEqual(len(report["legacy_b01_known_omitted_ids"]),31)
        self.assertEqual(report["installed_region_claims_matching_contract"],3)
        self.assertEqual(report["status"],
            "LEGACY_B04_COLLECTOR_OMITTED_SHORT_MAP_IDS_RESCAN_REQUIRED")
        self.assertFalse(report["future_reservations_proven"])
        self.assertFalse(report["can_install"])

    def test_24_other_short_incomplete_scan_cannot_pass_as_legacy(self):
        self.report["physical_map_ids"]=(
            list(range(101,276))+list(range(300,442))+list(range(600,899)))
        self.assert_blocked()

if __name__=="__main__":unittest.main()
