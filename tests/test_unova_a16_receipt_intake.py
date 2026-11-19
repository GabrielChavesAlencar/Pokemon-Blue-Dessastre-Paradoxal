"""A16 positive/negative sanitized metadata receipts, SHA lineage and source guards.

All fixtures in this module are synthetic dicts or temporary .json metadata.
No game, save, maps, installers, ZIP, Windows Sandbox or JoiPlay are opened.
"""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_a16_receipt_intake as a16
import audit_unova_a15_native_readiness as a15

class A16ReceiptIntakeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix=a15.read_json(ROOT,a15.FILE)
        cls.audit=a16.audit_catalog()
        cls.fixture=a16.synthetic_fixture(cls.matrix)

    def reject(self,change,*,rehash=False):
        obj=copy.deepcopy(self.fixture)
        change(obj)
        if rehash:self.rehash(obj)
        with self.assertRaises((ValueError,TypeError,KeyError,IndexError)):
            a16.validate_bundle(obj,self.matrix)

    @staticmethod
    def rehash(obj):
        obj["regional_manifests_sha256"]=a16.digest(obj["regional_manifests"])
        obj["intro_map001_sha256"]=a16.digest(obj["intro_map001"])
        baseline=a16.digest(obj["source_baseline"])
        previous=None
        for row in obj["receipts"]:
            row["baseline_sha256"]=baseline
            row["mapinfos_sha256"]=obj["source_baseline"]["mapinfos_sha256"]
            row["mapids_inventory_sha256"]=obj["source_baseline"]["mapid_inventory_sha256"]
            row["source_revision"]=obj["source_baseline"]["source_revision"]
            row["regional_manifests_sha256"]=obj["regional_manifests_sha256"]
            row["map001_evidence_sha256"]=obj["intro_map001_sha256"]
            row["previous_receipt_sha256"]=previous
            row["receipt_sha256"]=a16.receipt_digest(row)
            previous=row["receipt_sha256"]
        obj["bundle_sha256"]=a16.bundle_digest(obj)

    def test_001_schema(self):
        self.assertEqual(self.audit["schema_draft"],"2020-12")
    def test_002_contract_requires_all_eleven(self):
        self.assertEqual(self.audit["stages"],11)
    def test_003_native_gates_zero(self):
        self.assertEqual(self.audit["native_gates_pending"],8)
    def test_004_modes(self):
        self.assertEqual(a16.MODES,("SYNTHETIC_FIXTURE","REDACTED_UNVERIFIED"))
    def test_005_positive_synthetic_chain(self):
        out=a16.validate_bundle(self.fixture,self.matrix)
        self.assertEqual(out["status"],"UNVERIFIED_RECEIPTS_AWAIT_INDEPENDENT_REVIEW")
    def test_006_positive_redacted_unverified(self):
        obj=a16.synthetic_fixture(self.matrix,"REDACTED_UNVERIFIED")
        out=a16.validate_bundle(obj,self.matrix)
        self.assertEqual(out["mode"],"REDACTED_UNVERIFIED")
    def test_007_no_installation(self):
        self.assertFalse(a16.validate_bundle(self.fixture,self.matrix)["can_install"])
    def test_008_no_mapid_reservation(self):
        self.assertFalse(a16.validate_bundle(self.fixture,self.matrix)["can_reserve_mapids"])
    def test_009_no_release(self):
        self.assertFalse(a16.validate_bundle(self.fixture,self.matrix)["can_release"])
    def test_010_native_bars_stay_zero(self):
        out=a16.validate_bundle(self.fixture,self.matrix)
        self.assertEqual(out["native_technical_completed"],0)
        self.assertEqual(out["native_playable_completed"],0)
    def test_011_provenance_not_authenticated(self):
        self.assertFalse(self.audit["can_install"])
        self.assertFalse(a16.validate_bundle(self.fixture,self.matrix)["source_rights_verified"])
    def test_012_mapinfos_user_report_only(self):
        obj=self.fixture
        self.assertEqual(obj["source_baseline"]["mapinfos_sha256"],
             self.matrix["historical_snapshot"]["mapinfos_sha256"])
        self.assertFalse(obj["source_baseline"]["independent_recheck"])
    def test_013_original_mapid_count_648(self):
        self.assertEqual(self.fixture["source_baseline"]["mapids_observed"],648)
    def test_014_unova_preferred_unreserved(self):
        self.assertEqual(self.fixture["source_baseline"]["unova_candidate_range"],
             {"start":518,"end":599,"count":82,"reserved":False})
    def test_015_sinnoh_hold(self):
        self.assertEqual(self.fixture["source_baseline"]["sinnoh_hold"]["count"],76)
    def test_016_no_assigned_mapids(self):
        self.assertEqual(self.fixture["source_baseline"]["assigned_mapids"],[])
    def test_017_regions_exact(self):
        self.assertEqual(set(self.fixture["regional_manifests"]),set(a16.REGIONS))
    def test_018_all_manifests_unverified(self):
        self.assertTrue(all(m["source_status"]=="UNVERIFIED_SOURCE_METADATA_ONLY"
             for m in self.fixture["regional_manifests"].values()))
    def test_019_no_native_map_claim(self):
        self.assertTrue(all(m["native_claims"]==[]
             for m in self.fixture["regional_manifests"].values()))
    def test_020_map001_two_events(self):
        self.assertEqual([e["event_id"] for e in self.fixture["intro_map001"]["events"]],[1,2])
    def test_021_mapid3_unresolved(self):
        self.assertFalse(self.fixture["intro_map001"]["mapid_3_resolved"])
    def test_022_twenty_dynamic_destinations(self):
        self.assertEqual(self.fixture["intro_map001"]["computed_destinations_unresolved"],20)
    def test_023_rights_not_licensed(self):
        self.assertEqual(self.fixture["rights"]["asset_review_status"],"REVIEW_REQUIRED_NOT_LICENSED")
    def test_024_no_human_review(self):
        self.assertEqual(self.fixture["rights"]["human_decision"],"NOT_REVIEWED")
    def test_025_all_protections_false(self):
        self.assertFalse(any(self.fixture["protections"].values()))
    def test_026_stages_exact_order(self):
        self.assertEqual([r["stage"] for r in self.fixture["receipts"]],list(a16.STAGES))
    def test_027_real_dependency_dag(self):
        self.assertEqual([r["depends_on"] for r in self.fixture["receipts"]],
             [s["depends_on"] for s in self.matrix["steps"]])
    def test_028_receipt_hashes_valid(self):
        for row in self.fixture["receipts"]:
            self.assertEqual(row["receipt_sha256"],a16.receipt_digest(row))
    def test_029_prev_receipt_chain(self):
        rows=self.fixture["receipts"]
        self.assertIsNone(rows[0]["previous_receipt_sha256"])
        for before,after in zip(rows,rows[1:]):
            self.assertEqual(after["previous_receipt_sha256"],before["receipt_sha256"])
    def test_030_manifest_hash(self):
        self.assertEqual(self.fixture["regional_manifests_sha256"],
             a16.digest(self.fixture["regional_manifests"]))
    def test_031_intro_hash(self):
        self.assertEqual(self.fixture["intro_map001_sha256"],
             a16.digest(self.fixture["intro_map001"]))
    def test_032_baseline_hash(self):
        self.assertTrue(all(r["baseline_sha256"]==a16.digest(self.fixture["source_baseline"])
             for r in self.fixture["receipts"]))
    def test_033_bundle_hash(self):
        self.assertEqual(self.fixture["bundle_sha256"],a16.bundle_digest(self.fixture))
    def test_034_canonical_independent_of_key_order(self):
        self.assertEqual(a16.digest({"a":1,"b":2}),a16.digest({"b":2,"a":1}))
    def test_035_duplicate_json_keys_blocked(self):
        with self.assertRaises(ValueError):
            a16.safe_decode(b'{"phase":"A16","phase":"A16"}')
    def test_036_nan_json_blocked(self):
        with self.assertRaises(ValueError):a16.safe_decode(b'{"amount":NaN}')
    def test_037_unicode_decode_invalid(self):
        with self.assertRaises(ValueError):a16.safe_decode(b'\xff')
    def test_038_bom_blocked(self):
        with self.assertRaises(ValueError):a16.safe_decode(b'\xef\xbb\xbf{}')
    def test_039_size_limit(self):
        with self.assertRaises(ValueError):a16.safe_decode(b'{"x":"' + b'x'*150000 + b'"}')
    def test_040_empty_json_blocked(self):
        with self.assertRaises(ValueError):a16.safe_decode(b'')
    def test_041_cli_catalog(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_a16_receipt_intake.py"),"--check"],
         capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertFalse(json.loads(p.stdout)["can_install"])
    def test_042_cli_demo_negative(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_a16_receipt_intake.py"),"--simulate-demo"],
         capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertTrue(json.loads(p.stdout)["tamper_rejected"])
    def test_043_cli_print_fixture(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_a16_receipt_intake.py"),"--print-synthetic-fixture"],
         capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(a16.validate_bundle(json.loads(p.stdout),self.matrix)["receipts_verified_for_internal_integrity"],11)
    def test_044_only_sanitized_json_file(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"receipt.json"
            path.write_text(json.dumps(self.fixture),encoding="utf-8")
            self.assertEqual(a16.safe_read_receipt_json(path),self.fixture)
            with self.assertRaises(ValueError):a16.safe_read_receipt_json(Path(td)/"game.exe")
    def test_045_cli_verify_json(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"sanitized.json"
            path.write_text(json.dumps(self.fixture),encoding="utf-8")
            p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_a16_receipt_intake.py"),
                   "--verify-json",str(path)],capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            self.assertEqual(json.loads(p.stdout)["status"],
              "UNVERIFIED_RECEIPTS_AWAIT_INDEPENDENT_REVIEW")
    def test_046_cli_refuses_fake_license(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)/"forged.json"
            d=copy.deepcopy(self.fixture)
            d["rights"]["license_verified"]=True
            self.rehash(d)
            path.write_text(json.dumps(d),encoding="utf-8")
            p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_a16_receipt_intake.py"),
                   "--verify-json",str(path)],capture_output=True,text=True)
            self.assertEqual(p.returncode,2)
            self.assertIn("UNOVA_A16_BLOCKED",p.stdout)
    def test_047_no_source_reads_from_receipt(self):
        self.assertFalse(any("path" in k.lower() for k in self.fixture))
        self.assertTrue(all("source_report_sha256" in row for row in self.fixture["receipts"]))
    def test_048_no_mutation(self):
        old=copy.deepcopy(self.fixture)
        a16.validate_bundle(self.fixture,self.matrix)
        self.assertEqual(old,self.fixture)
    def test_049_no_game_exe_or_joiplay(self):
        for field in ("windows_game_exe_qa","android_joiplay_qa","saves_read","saves_written"):
            self.assertIs(self.fixture["protections"][field],False)
    def test_050_redacted_mode_remains_unapproved(self):
        obj=a16.synthetic_fixture(self.matrix,"REDACTED_UNVERIFIED")
        status=a16.validate_bundle(obj,self.matrix)
        self.assertFalse(status["human_approval_verified"])
        self.assertFalse(status["can_install"])
    def test_051_rehash_chain_does_not_make_fake_install_valid(self):
        self.reject(lambda d:d.update(can_install=True),rehash=True)
    def test_052_accept_unverified_hash_of_report_metadata_only(self):
        obj=copy.deepcopy(self.fixture)
        obj["receipts"][0]["source_report_sha256"]=a16.digest("FIXTURE_ONLY_A04_REPORT")
        self.rehash(obj)
        self.assertEqual(a16.validate_bundle(obj,self.matrix)["status"],
                         "UNVERIFIED_RECEIPTS_AWAIT_INDEPENDENT_REVIEW")
    def test_053_accept_unverified_manifest_hash_without_approval(self):
        obj=copy.deepcopy(self.fixture)
        obj["regional_manifests"]["KANTO"]["source_sha256"]=a16.digest("FIXTURE_ONLY_KANTO_MANIFEST")
        self.rehash(obj)
        status=a16.validate_bundle(obj,self.matrix)
        self.assertFalse(status["regional_manifests_source_verified"])
    def test_054_recalculate_does_not_override_mapid_baseline(self):
        self.reject(lambda d:d["source_baseline"].update(mapinfos_sha256="a"*64),rehash=True)
    def test_055_full_explicit_consent_required(self):
        self.assertIsNone(self.fixture["rights"]["approval_receipt_sha256"])
        self.assertIs(self.fixture["rights"]["redistribution_approved"],False)

# Adversarial source and payload mutations, each MUST be blocked in memory.
NEGATIVE={
 "wrong_version":lambda d:d.update(schema_version=2),
 "other_region":lambda d:d.update(region="SINNOH"),
 "other_phase":lambda d:d.update(phase="A15"),
 "other_campaign":lambda d:d.update(campaign="BLACK2"),
 "unexpected_mode":lambda d:d.update(mode="NATIVE"),
 "unverified_claim_promoted":lambda d:d.update(status="APPROVED"),
 "missing_bundle_hash":lambda d:d.pop("bundle_sha256"),
 "fake_bundle_hash":lambda d:d.update(bundle_sha256="b"*64),
 "unknown_field":lambda d:d.update(game_exe_path="Game.exe"),
 "raw_saves_field":lambda d:d.update(saves={"File1.rxdata":"private"}),
 "native_a_one":lambda d:d.update(native_technical_completed=1),
 "native_playable_one":lambda d:d.update(native_playable_completed=1),
 "can_reserve":lambda d:d.update(can_reserve_mapids=True),
 "can_install":lambda d:d.update(can_install=True),
 "can_release":lambda d:d.update(can_release=True),
 "missing_baseline":lambda d:d.pop("source_baseline"),
 "other_baseline_id":lambda d:d["source_baseline"].update(identity="UNKNOWN"),
 "baseline_other_origin":lambda d:d["source_baseline"].update(evidence_origin="CERTIFIED"),
 "baseline_other_mapinfos":lambda d:d["source_baseline"].update(mapinfos_sha256="a"*64),
 "baseline_wrong_hash_format":lambda d:d["source_baseline"].update(mapid_inventory_sha256="short"),
 "baseline_native_verified":lambda d:d["source_baseline"].update(independent_recheck=True),
 "baseline_revision":lambda d:d["source_baseline"].update(source_revision="real-native-revision"),
 "baseline_wrong_mapid_count":lambda d:d["source_baseline"].update(mapids_observed=649),
 "baseline_boolean_mapid_count":lambda d:d["source_baseline"].update(mapids_observed=True),
 "baseline_candidate_reserved":lambda d:d["source_baseline"]["unova_candidate_range"].update(reserved=True),
 "baseline_candidate_start":lambda d:d["source_baseline"]["unova_candidate_range"].update(start=442),
 "baseline_candidate_count":lambda d:d["source_baseline"]["unova_candidate_range"].update(count=81),
 "sinnoh_hold_modified":lambda d:d["source_baseline"]["sinnoh_hold"].update(end=599),
 "sinnoh_real_reservation":lambda d:d["source_baseline"]["sinnoh_hold"].update(native_reservation=True),
 "mapids_assigned":lambda d:d["source_baseline"].update(assigned_mapids=[518]),
 "no_manifests":lambda d:d["regional_manifests"].clear(),
 "forge_unova_source":lambda d:d["regional_manifests"]["UNOVA"].update(source_status="VERIFIED"),
 "forge_hoenn_version":lambda d:d["regional_manifests"]["HOENN"].update(source_revision="main"),
 "forge_installed_claim":lambda d:d["regional_manifests"]["JOHTO"].update(native_claims=[600]),
 "manifest_hash_invalid":lambda d:d.update(regional_manifests_sha256="c"*64),
 "manifest_hash_missing":lambda d:d.pop("regional_manifests_sha256"),
 "manifest_source_invalid_sha":lambda d:d["regional_manifests"]["KANTO"].update(source_sha256="not-sha"),
 "extra_manifest":lambda d:d["regional_manifests"].update(KALOS={}),
 "missing_manifest":lambda d:d["regional_manifests"].pop("SINNOH"),
 "map001_first_event_forged":lambda d:d["intro_map001"]["events"][0].update(event_id=2),
 "map001_destination_rewritten":lambda d:d["intro_map001"]["events"][1].update(destination_map_id=518),
 "map001_missing_event":lambda d:d["intro_map001"]["events"].pop(),
 "map001_fake_page":lambda d:d["intro_map001"]["events"][0].update(page=2),
 "map001_verified_event":lambda d:d["intro_map001"]["events"][0].update(evidence_status="VERIFIED"),
 "map001_missing_3":lambda d:d["intro_map001"].update(mapid_3_resolved=True),
 "dynamic_transfers_forged":lambda d:d["intro_map001"].update(computed_destinations_unresolved=0),
 "intro_runtime_fake":lambda d:d["intro_map001"].update(script_runtime_verified=True),
 "intro_digest_fake":lambda d:d.update(intro_map001_sha256="d"*64),
 "rights_licensed":lambda d:d["rights"].update(license_verified=True),
 "rights_approved":lambda d:d["rights"].update(redistribution_approved=True),
 "rights_reviewer_forged":lambda d:d["rights"].update(human_decision="APPROVED"),
 "rights_fake_receipt":lambda d:d["rights"].update(approval_receipt_sha256="e"*64),
 "rights_short_sha":lambda d:d["rights"].update(source_rights_sha256="bad"),
 "rights_source_status":lambda d:d["rights"].update(asset_review_status="LICENSED"),
 "no_rights":lambda d:d.pop("rights"),
 "receipt_missing":lambda d:d["receipts"].pop(),
 "receipt_extra":lambda d:d["receipts"].append(copy.deepcopy(d["receipts"][-1])),
 "receipt_reorder":lambda d:d["receipts"].reverse(),
 "receipt_other_step":lambda d:d["receipts"][5].update(stage="A04"),
 "receipt_schema_version":lambda d:d["receipts"][4].update(schema_version=2),
 "receipt_skips_dependency":lambda d:d["receipts"][7].update(depends_on=[]),
 "receipt_other_mode":lambda d:d["receipts"][4].update(mode="NATIVE"),
 "receipt_approved_status":lambda d:d["receipts"][0].update(status="ACCEPTED"),
 "receipt_approved_rights":lambda d:d["receipts"][2].update(rights_status="LICENSED"),
 "receipt_human_review":lambda d:d["receipts"][3].update(human_review="APPROVED"),
 "receipt_runtime_approved":lambda d:d["receipts"][10].update(runtime_qa="WINDOWS_SANDBOX_PASS"),
 "receipt_reserved":lambda d:d["receipts"][1].update(mapids_reserved=True),
 "receipt_installable":lambda d:d["receipts"][4].update(installable=True),
 "receipt_baseline_hash":lambda d:d["receipts"][1].update(baseline_sha256="0"*64),
 "receipt_mapinfos_mismatch":lambda d:d["receipts"][6].update(mapinfos_sha256="0"*64),
 "receipt_manifest_mismatch":lambda d:d["receipts"][6].update(regional_manifests_sha256="0"*64),
 "receipt_intro_mismatch":lambda d:d["receipts"][6].update(map001_evidence_sha256="0"*64),
 "receipt_rev_mismatch":lambda d:d["receipts"][6].update(source_revision="NEW"),
 "receipt_fake_previous":lambda d:d["receipts"][6].update(previous_receipt_sha256="f"*64),
 "receipt_digest_mismatch":lambda d:d["receipts"][6].update(receipt_sha256="f"*64),
 "receipt_invalid_report_sha":lambda d:d["receipts"][6].update(source_report_sha256="untrusted"),
 "receipt_foreign_file":lambda d:d["receipts"][6].update(file_path="../Game.exe"),
 "receipt_wrong_mapid_inventory":lambda d:d["receipts"][2].update(mapids_inventory_sha256="a"*64),
 "receipt_missing_approval":lambda d:d["receipts"][1].pop("human_review"),
 "rights_verified_protected":lambda d:d["protections"].update(rights_verified=True),
 "human_approved_protected":lambda d:d["protections"].update(human_approved=True),
 "mapid_reserved_protected":lambda d:d["protections"].update(mapids_reserved=True),
 "native_install_protected":lambda d:d["protections"].update(native_install_approved=True),
 "windows_qa_protected":lambda d:d["protections"].update(windows_game_exe_qa=True),
 "android_qa_protected":lambda d:d["protections"].update(android_joiplay_qa=True),
 "saves_read_protected":lambda d:d["protections"].update(saves_read=True),
 "saves_write_protected":lambda d:d["protections"].update(saves_written=True),
}
for _name,_mutation in NEGATIVE.items():
    def test_bad(self,mutation=_mutation):
        self.reject(mutation)
    setattr(A16ReceiptIntakeTests,"test_negative_"+_name,test_bad)

# Redigest every hash in the chain, and still refuse forged semantics.
REHASH_NEGATIVE={
  "wrong_mapinfos":NEGATIVE["baseline_other_mapinfos"],
  "mapids_reserved":NEGATIVE["baseline_candidate_reserved"],
  "intro_forged":NEGATIVE["map001_destination_rewritten"],
  "dynamic_resolved":NEGATIVE["dynamic_transfers_forged"],
  "manifest_forged":NEGATIVE["forge_unova_source"],
  "rights_licensed":NEGATIVE["rights_licensed"],
  "human_approved":NEGATIVE["rights_reviewer_forged"],
  "runtime_qa":NEGATIVE["receipt_runtime_approved"],
  "native_install":NEGATIVE["can_install"],
  "stage_dependency":NEGATIVE["receipt_skips_dependency"],
  "native_mapid":NEGATIVE["mapids_assigned"],
  "future_revision":NEGATIVE["baseline_revision"],
  "candidate_changed":NEGATIVE["baseline_candidate_start"],
  "other_region":NEGATIVE["other_region"],
}
for _name,_mutation in REHASH_NEGATIVE.items():
    def test_rehash(self,mutation=_mutation):
        self.reject(mutation,rehash=True)
    setattr(A16ReceiptIntakeTests,"test_rehash_does_not_authorize_"+_name,test_rehash)

if __name__=="__main__":unittest.main()
