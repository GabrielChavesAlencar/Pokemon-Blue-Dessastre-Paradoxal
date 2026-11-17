"""L02: 30+ positive/negative documentary-only synthetic scenarios, no native IO."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"scripts/regions"),str(ROOT/"tests")]
import review_sinnoh_l02_evidence as l02
import export_sinnoh_l01_reports as l01
import test_sinnoh_l01_exporter as l01_fixtures

class SinnohL02ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts={k:l02.l00.read_json(ROOT,p) for k,p in l02.l00.CONTRACTS.items()}
        cls.handoff=l02.l00.read_json(ROOT,l02.l00.g12.HANDOFF)
        cls.final=l02.l00.g12.run(ROOT)
        cls.source=l01_fixtures.SinnohL01Tests.complete_fixture()

    def make(self,*stages):
        orig=copy.deepcopy(self.source)
        d=copy.deepcopy(l02.l00.read_json(ROOT,l02.l00.TEMPLATE))
        if "B09" in stages:
            d["reports"]["B09"]=l01.project_b09(orig["b09_receipt"],orig["b09_dry_run"],self.contracts["B09"])
        if "B10" in stages:
            d["reports"]["B10"]=l01.project_b10(orig["b10"])
        if "B11" in stages:
            d["reports"]["B11"]=l01.project_b11(orig["b11_before"],orig["b11_after"],"a"*64)
        if "R07" in stages:
            d["reports"]["R07"]=l01.project_r07(orig["r07"])
        if "R08" in stages:
            d["reports"]["R08"]=l01.project_r08(orig["r08"])
        return d

    def evaluate(self,bundle,contracts=None,handoff=None,final=None):
        return l02.review(bundle,
            copy.deepcopy(self.contracts) if contracts is None else contracts,
            copy.deepcopy(self.handoff) if handoff is None else handoff,
            copy.deepcopy(self.final) if final is None else final)

    def test_01_default_all_five_missing_not_native_approved(self):
        r=self.evaluate(self.make())
        self.assertEqual(r["status"],"INCOMPLETE_DOCUMENTARY_HANDOFF")
        self.assertEqual(r["counts"],{"total":5,"missing":5,"conflicting":0,
                                      "missing_prerequisite":0,
                                      "self_reported_unverified":0,"independently_accepted":0})
        self.assertEqual([x["status"] for x in r["reports"].values()],
                         [l02.STATUS_MISSING]*5)

    def test_02_all_five_valid_synthetic_still_not_authenticated(self):
        r=self.evaluate(self.make(*l02.STAGES))
        self.assertEqual(r["status"],"DOCUMENTARY_REVIEW_ONLY_NATIVE_APPROVAL_PENDING")
        self.assertEqual(r["counts"]["self_reported_unverified"],5)
        self.assertEqual(r["counts"]["independently_accepted"],0)
        self.assertTrue(all(x["human_review_required"] for x in r["reports"].values()))
        self.assertTrue(all(not x["physical_origin_authenticated"] for x in r["reports"].values()))

    def test_03_only_B09_is_self_report_and_four_missing(self):
        r=self.evaluate(self.make("B09"))
        self.assertEqual(r["reports"]["B09"]["status"],l02.STATUS_UNVERIFIED)
        self.assertEqual(r["counts"]["missing"],4)

    def test_04_R07_and_R08_standalone_still_missing_three(self):
        r=self.evaluate(self.make("R07","R08"))
        self.assertEqual(r["counts"]["missing"],3)
        self.assertEqual(r["counts"]["self_reported_unverified"],2)
        self.assertFalse(r["r07_complete"])

    def test_05_B10_without_B09_is_a_blocked_dependency_not_a_pass(self):
        r=self.evaluate(self.make("B10"))
        self.assertEqual(r["reports"]["B10"]["status"],l02.STATUS_DEPENDENCY)
        self.assertEqual(r["reports"]["B10"]["reason_code"],
                         "B09_VALIDATED_RECEIPT_REQUIRED_BEFORE_B10")
        self.assertEqual(r["status"],"BLOCKED_MISSING_CHAIN_PREREQUISITES")

    def test_06_B11_without_B09_B10_never_proves_save_isolation(self):
        r=self.evaluate(self.make("B11"))
        self.assertEqual(r["reports"]["B11"]["status"],l02.STATUS_DEPENDENCY)
        self.assertFalse(r["host_saves_globally_isolated_proven"])

    def test_07_B09_and_B11_without_B10_still_blocked(self):
        r=self.evaluate(self.make("B09","B11"))
        self.assertEqual(r["reports"]["B11"]["status"],l02.STATUS_DEPENDENCY)
        self.assertEqual(r["counts"]["missing_prerequisite"],1)

    def test_08_B09_B10_without_B11_is_incomplete_not_executable(self):
        r=self.evaluate(self.make("B09","B10"))
        self.assertEqual(r["counts"]["self_reported_unverified"],2)
        self.assertEqual(r["reports"]["B11"]["status"],l02.STATUS_MISSING)
        self.assertFalse(r["may_start_game_in_vm"])

    def test_09_B09_plan_SHA_malformed_blocks_both_dependent_receipts(self):
        d=self.make("B09","B10")
        d["reports"]["B09"]["plan_sha256"]="not-a-digest"
        r=self.evaluate(d)
        self.assertEqual(r["reports"]["B09"]["status"],l02.STATUS_BLOCKED)
        self.assertEqual(r["reports"]["B10"]["status"],l02.STATUS_DEPENDENCY)
        self.assertEqual(r["status"],"BLOCKED_CONFLICTING_OR_UNSAFE_REPORTS")

    def test_10_B09_wrong_public_inventory_SHA_is_not_proof(self):
        d=self.make("B09")
        d["reports"]["B09"]["native_inventory_sha256"]="b"*64
        self.assertEqual(self.evaluate(d)["reports"]["B09"]["status"],l02.STATUS_BLOCKED)

    def test_11_B09_703_maps_53_terrain_or_13_PNGs_is_conflict(self):
        for field,val in (("map_ids_clone_total",703),
                          ("b08_maps_validated",53),("b08_pngs_validated",13)):
            with self.subTest(field=field):
                d=self.make("B09")
                d["reports"]["B09"][field]=val
                self.assertEqual(self.evaluate(d)["reports"]["B09"]["status"],l02.STATUS_BLOCKED)

    def test_12_B09_fake_game_running_or_saves_copied_is_conflict(self):
        for field in ("game_exe_executed","saves_copied","safe_to_launch",
                      "can_install_live_game","r07_complete"):
            with self.subTest(field=field):
                d=self.make("B09");d["reports"]["B09"][field]=True
                self.assertEqual(self.evaluate(d)["reports"]["B09"]["status"],l02.STATUS_BLOCKED)

    def test_13_B09_zero_phase_changed_to_one_or_boolean_is_conflict(self):
        for bad in (True,1,-1):
            d=self.make("B09");d["reports"]["B09"]["phase_b_approved"]=bad
            self.assertEqual(self.evaluate(d)["reports"]["B09"]["status"],l02.STATUS_BLOCKED)

    def test_14_B10_SHA_different_from_B09_is_conflict_not_silent_missing(self):
        d=self.make("B09","B10")
        d["reports"]["B10"]["source_clone_sha256"]="c"*64
        r=self.evaluate(d)
        self.assertEqual(r["reports"]["B10"]["status"],l02.STATUS_BLOCKED)
        self.assertFalse(r["may_install_live_game"])

    def test_15_B10_network_clipboard_or_mutable_mount_is_conflict(self):
        for field,bad in (("internet_networking_enabled",True),
                          ("clipboard_enabled",True),("mapped_folders_read_only",False)):
            with self.subTest(field=field):
                d=self.make("B09","B10");d["reports"]["B10"][field]=bad
                self.assertEqual(self.evaluate(d)["reports"]["B10"]["status"],l02.STATUS_BLOCKED)

    def test_16_B10_missing_host_feature_or_clone_SHA_verification_conflict(self):
        for field in ("sandbox_feature_enabled_on_host","all_cloned_files_sha_verified"):
            d=self.make("B09","B10");d["reports"]["B10"][field]=False
            self.assertEqual(self.evaluate(d)["reports"]["B10"]["status"],l02.STATUS_BLOCKED)

    def test_17_B10_fake_VM_started_or_game_run_is_conflict(self):
        for field in ("sandbox_session_started","game_exe_started",
                      "save_write_isolation_runtime_verified",
                      "host_save_directories_mapped","rights_verified"):
            d=self.make("B09","B10");d["reports"]["B10"][field]=True
            self.assertEqual(self.evaluate(d)["reports"]["B10"]["status"],l02.STATUS_BLOCKED)

    def test_18_B10_incorrect_expected_map_counts_conflict(self):
        for field,bad in (("native_map_ids",649),
                          ("sinnoh_terrain_map_ids",55),
                          ("expected_total_maps",703)):
            d=self.make("B09","B10");d["reports"]["B10"][field]=bad
            self.assertEqual(self.evaluate(d)["reports"]["B10"]["status"],l02.STATUS_BLOCKED)

    def test_19_B11_no_changes_does_not_prove_vm_or_global_save_safety(self):
        r=self.evaluate(self.make("B09","B10","B11"))
        self.assertEqual(r["reports"]["B11"]["status"],l02.STATUS_UNVERIFIED)
        self.assertFalse(r["b11_session_link_in_sanitized_sources_available"])
        self.assertFalse(r["host_saves_globally_isolated_proven"])

    def test_20_B11_modified_files_are_documented_but_not_accepted(self):
        d=self.make(*l02.STAGES)
        after=d["reports"]["B11"]["after"]
        after.update(files_changed=1,watch_unchanged=False,
                     status="HOST_WATCHED_FILES_CHANGED_REVIEW_REQUIRED")
        r=self.evaluate(d)
        self.assertEqual(r["reports"]["B11"]["status"],l02.STATUS_UNVERIFIED)
        self.assertFalse(r["may_start_game_in_host"])

    def test_21_B11_changed_files_hidden_behind_watch_unchanged_is_conflict(self):
        d=self.make(*l02.STAGES)
        d["reports"]["B11"]["after"]["files_changed"]=1
        self.assertEqual(self.evaluate(d)["reports"]["B11"]["status"],l02.STATUS_BLOCKED)

    def test_22_B11_before_after_scopes_and_file_count_drift_is_conflict(self):
        for field,bad in (("monitored_files_before",4),
                          ("monitored_directories_count",3),
                          ("default_scopes_not_monitored",2),
                          ("monitored_files_after",4)):
            with self.subTest(field=field):
                d=self.make(*l02.STAGES);d["reports"]["B11"]["after"][field]=bad
                self.assertEqual(self.evaluate(d)["reports"]["B11"]["status"],l02.STATUS_BLOCKED)

    def test_23_B11_claim_of_complete_coverage_or_rights_rejected(self):
        for field,bad in (("coverage_is_partial",False),
                          ("host_saves_globally_isolated_proven",True),
                          ("guest_vm_execution_independently_verified",True),
                          ("assets_rights_verified",True),("gameplay_approved",True),
                          ("phase_d_approved",1)):
            with self.subTest(field=field):
                d=self.make(*l02.STAGES);d["reports"]["B11"]["after"][field]=bad
                self.assertEqual(self.evaluate(d)["reports"]["B11"]["status"],l02.STATUS_BLOCKED)

    def test_24_B11_unrecognized_guest_observation_is_conflict(self):
        d=self.make(*l02.STAGES)
        d["reports"]["B11"]["after"]["guest_observation_self_reported"]="success!"
        self.assertEqual(self.evaluate(d)["reports"]["B11"]["status"],l02.STATUS_BLOCKED)

    def test_25_R07_rights_claim_or_unsafe_reservation_is_conflict(self):
        for field,bad in (("r07_complete",True),
                          ("may_apply_to_main_game",True),
                          ("rights_verified",True),
                          ("candidate_safety_reviewable",True),
                          ("future_regions_with_evidence",4)):
            with self.subTest(field=field):
                d=self.make("R07");d["reports"]["R07"][field]=bad
                self.assertEqual(self.evaluate(d)["reports"]["R07"]["status"],l02.STATUS_BLOCKED)

    def test_26_R07_wrong_native_mapinfos_or_future_collision_is_conflict(self):
        d=self.make("R07")
        r=d["reports"]["R07"]
        r.update(native_snapshot_present=True,native_occupied_count=648,
                 native_mapinfos_sha256="b"*64)
        self.assertEqual(self.evaluate(d)["reports"]["R07"]["status"],l02.STATUS_BLOCKED)

    def test_27_R07_candidate_reviewable_can_only_request_human_review(self):
        d=self.make("R07")
        r=d["reports"]["R07"]
        r.update(status="CANDIDATE_READY_FOR_MANUAL_REVIEW_NOT_APPROVED",
                 native_snapshot_present=True,native_occupied_count=648,
                 native_mapinfos_sha256=self.contracts["B09"]["native_baseline_mapinfos_sha256"],
                 future_regions_with_evidence=3,collisions_count=0,
                 candidate_safety_reviewable=True)
        out=self.evaluate(d)
        self.assertEqual(out["reports"]["R07"]["status"],l02.STATUS_UNVERIFIED)
        self.assertFalse(out["r07_complete"])

    def test_28_R08_all_14_reviews_never_grant_license_or_install(self):
        d=self.make("R08")
        d["reports"]["R08"]["per_asset_licenses_reviewed_count"]=14
        r=self.evaluate(d)
        self.assertEqual(r["reports"]["R08"]["status"],l02.STATUS_UNVERIFIED)
        self.assertFalse(r["r08_complete"])
        self.assertFalse(r["game_installed"])

    def test_29_R08_extra_fake_approval_and_invalid_count_are_conflicts(self):
        for field,bad in (("r08_complete",True),
                          ("can_install",True),
                          ("source_asset_rights_verified",True),
                          ("per_asset_licenses_reviewed_count",15)):
            d=self.make("R08");d["reports"]["R08"][field]=bad
            self.assertEqual(self.evaluate(d)["reports"]["R08"]["status"],l02.STATUS_BLOCKED)

    def test_30_private_paths_watch_ids_and_save_hashes_not_echoed(self):
        d=self.make(*l02.STAGES)
        d["reports"]["B11"]["private-baseline.json"]=r"C:\Users\tester\Save01.rxdata"
        out=json.dumps(self.evaluate(d))
        self.assertNotIn("Save01.rxdata",out)
        self.assertNotIn("C:\\Users",out)
        self.assertNotIn("private-baseline.json",out)
        self.assertNotIn("hmac_key",out)
        self.assertEqual(self.evaluate(d)["reports"]["B11"]["status"],l02.STATUS_BLOCKED)

    def test_31_input_envelope_unknown_keys_or_wrong_stage_fail_closed(self):
        for change in (
            lambda d:d.update(stage="NATIVE_PLAYABLE"),
            lambda d:d["reports"].update(Extra={"secret":"hmac"}),
            lambda d:d.update(private_path="C:\\Users\\tester"),
        ):
            d=self.make()
            change(d)
            with self.assertRaisesRegex(ValueError,"SINNOH_L02_BLOCKED"):
                self.evaluate(d)

    def test_32_G12_forged_native_evidence_prevents_even_documentary_report(self):
        for field,bad in (("game_exe_tested",True),
                          ("completed_native_cases",1),
                          ("phase_b_approved",1)):
            h=copy.deepcopy(self.handoff);h[field]=bad
            with self.assertRaisesRegex(ValueError,"SINNOH_L02_BLOCKED"):
                self.evaluate(self.make(),handoff=h)

    def test_33_public_B09_B10_contracts_tampered_prevents_report(self):
        for stage,key,bad in (("B09","expected_qa_clone_map_count",703),
                              ("B10","network_disabled",False),
                              ("B10","clipboard_disabled",False)):
            c=copy.deepcopy(self.contracts);c[stage][key]=bad
            with self.assertRaisesRegex(ValueError,"SINNOH_L02_BLOCKED"):
                self.evaluate(self.make(),contracts=c)

    def test_34_sanitized_schema_has_no_dates_or_b11_original_session_link(self):
        out=self.evaluate(self.make(*l02.STAGES))
        self.assertFalse(out["chronology_dates_in_sanitized_sources_available"])
        self.assertFalse(out["b11_session_link_in_sanitized_sources_available"])
        self.assertTrue(out["documentary_review_cannot_schedule_native_QA"])
        self.assertFalse(out["independent_receipt_authenticity_proven"])

    def test_35_all_rows_keep_43_windows_and_one_android_at_zero(self):
        out=self.evaluate(self.make(*l02.STAGES))
        self.assertEqual((out["native_cases_total"],out["windows_cases"],
                          out["android_cases"],out["native_cases_completed"]),(44,43,1,0))
        self.assertEqual(out["local_qa_gates"],
                         {f"L{i:02}":"PENDING" for i in range(1,6)})
        for field in ("may_start_game_in_host","may_start_game_in_vm",
                      "may_install_live_game","game_installed","sinnoh_playable",
                      "game_exe_tested","joiplay_tested","windows_sandbox_executed",
                      "host_saves_accessed","auto_uploaded"):
            self.assertIs(out[field],False)

    def test_36_report_never_contains_source_SHA_or_raw_report_values(self):
        out=json.dumps(self.evaluate(self.make(*l02.STAGES)),sort_keys=True)
        self.assertNotIn("plan_sha256",out)
        self.assertNotIn("source_clone_sha256",out)
        self.assertNotIn("sanitized_report_sha256",out)
        self.assertNotIn("native_mapinfos_sha256",out)
        self.assertNotIn("watch_id",out)
        self.assertNotIn("private-baseline.json",out)
        self.assertNotIn("a"*64,out)

    def test_37_CLI_default_public_template_has_no_output_file(self):
        target=ROOT/".blue-work/sinnoh-l02"
        was_present=target.exists()
        proc=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/review_sinnoh_l02_evidence.py")],
            cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(proc.returncode,0,proc.stderr)
        report=json.loads(proc.stdout)
        self.assertEqual(report["counts"]["missing"],5)
        self.assertEqual(report["native_cases_approved"],0)
        self.assertEqual(target.exists(),was_present)

    def test_38_CLI_unknown_path_rejected_without_echo(self):
        private=r"C:\Users\tester\Save01.rxdata"
        proc=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/review_sinnoh_l02_evidence.py"),
            "--file",private],cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(proc.returncode,2)
        self.assertNotIn(private,proc.stdout+proc.stderr)
        self.assertNotIn("C:\\Users",proc.stdout+proc.stderr)
        self.assertIn("SINNOH_L02_BLOCKED",proc.stderr)

    def test_39_optional_fixed_workspace_unavailable_never_scans_PC(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"SINNOH_L00_BLOCKED"):
                l02.l00.read_json(Path(td),l02.l00.PRIVATE_REPORT,maxsize=65536)

    def test_40_no_network_process_or_native_file_reads_in_reviewer_source(self):
        s=(ROOT/"scripts/regions/review_sinnoh_l02_evidence.py").read_text("utf-8")
        for x in ("import subprocess","import socket","import requests","os.system",
                  "os.popen","shutil.copy","Game.exe').read_bytes",
                  "private-baseline.json\").read_text", "os.walk","rglob("):
            self.assertNotIn(x,s)
        self.assertIn("l00.read_json(root,src,maxsize=65536)",s)

if __name__=="__main__":
    unittest.main()
