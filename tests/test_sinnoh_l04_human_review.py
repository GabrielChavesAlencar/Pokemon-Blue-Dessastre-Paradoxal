"""Sinnoh L04: 35 synthetic positive/negative tests; no physical QA ever."""
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
import audit_sinnoh_l04_human_review as l04
import test_sinnoh_l02_evidence as previous_fixture

class SinnohL04Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=l04.l03.l02.l00.read_json(ROOT,l04.CHECKLIST)
        cls.matrix=l04.l03.l02.l00.read_json(ROOT,l04.l03.MATRIX)
        cls.l03_report=l04.l03.run(ROOT)
        previous_fixture.SinnohL02ReviewTests.setUpClass()
        cls.synthetic=previous_fixture.SinnohL02ReviewTests("test_01_default_all_five_missing_not_native_approved")

    def audit(self,change=None):
        manifest=copy.deepcopy(self.manifest)
        matrix=copy.deepcopy(self.matrix)
        source=copy.deepcopy(self.l03_report)
        if change:change(manifest,matrix,source)
        return l04.audit(manifest,matrix,source)

    def refuse(self,change):
        with self.assertRaisesRegex(ValueError,"SINNOH_L04_BLOCKED"):
            self.audit(change)

    def synthetic_source(self,*stages):
        return l04.l03.reconcile(
            self.matrix,self.synthetic.evaluate(self.synthetic.make(*stages)))

    def test_01_public_default_five_absent(self):
        r=self.audit()
        self.assertEqual(r["status"],"HUMAN_REVIEW_NOT_STARTED_NO_NATIVE_AUTHORIZATION")
        self.assertEqual([x["source_status"] for x in r["source_rows"]],
                         ["MISSING_REPORT"]*5)
        self.assertEqual(r["criteria_reviewed"],0)
        self.assertEqual(r["human_decisions_recorded"],0)

    def test_02_manifest_exact_self_check(self):
        self.assertTrue(l04.validate_checklist(self.manifest))
        self.assertEqual(self.manifest["schema"],1)
        self.assertEqual(self.manifest["stage"],"L04")
        self.assertEqual(self.manifest["version"],1)

    def test_03_twenty_criteria_all_not_reviewed(self):
        r=self.audit()
        self.assertEqual(r["criteria_total"],20)
        self.assertEqual(sum(len(x["criteria"]) for x in r["source_rows"]),20)
        self.assertTrue(all(item["state"]=="NOT_REVIEWED"
                            for row in r["source_rows"] for item in row["criteria"]))
        self.assertTrue(all(item["external_human_review_required"]
                            for row in r["source_rows"] for item in row["criteria"]))

    def test_04_all_unique_ids_and_per_stage_groups(self):
        ids=[c["id"] for row in self.manifest["rows"] for c in row["criteria"]]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual([x["stage"] for x in self.manifest["rows"]],
                         list(l04.STAGES))
        self.assertTrue(all(len(row["criteria"])==4 for row in self.manifest["rows"]))

    def test_05_empty_receipts_never_change_runtime_rights(self):
        r=self.audit()
        for field in ("sinnoh_playable","may_launch_game_exe",
                      "may_launch_joiplay","may_start_windows_sandbox",
                      "may_install_live_game","auto_uploaded"):
            self.assertIs(r[field],False)
        self.assertEqual(r["native_cases_approved"],0)
        self.assertFalse(r["r07_complete"])
        self.assertFalse(r["r08_complete"])
        self.assertFalse(r["r09_complete"])

    def test_06_five_synthetic_valid_receipts_still_unapproved(self):
        r=l04.audit(self.manifest,self.matrix,self.synthetic_source(*l04.STAGES))
        self.assertTrue(all(x["source_status"]=="SELF_REPORTED_AWAITING_HUMAN_REVIEW"
                            for x in r["source_rows"]))
        self.assertTrue(all(x["documentary_action"]=="SCHEDULE_DOCUMENTARY_ANALYSIS"
                            for x in r["source_rows"]))
        self.assertFalse(r["may_launch_game_exe"])

    def test_07_B10_without_B09_is_documentary_dependency(self):
        r=l04.audit(self.manifest,self.matrix,self.synthetic_source("B10"))
        self.assertEqual(r["source_rows"][1]["source_status"],"PREREQUISITE_MISSING_BLOCKED")
        self.assertEqual(r["source_rows"][1]["documentary_action"],"RECONCILE_PREREQUISITES")

    def test_08_B11_without_B09_or_B10_is_documentary_dependency(self):
        r=l04.audit(self.manifest,self.matrix,self.synthetic_source("B11"))
        self.assertEqual(r["source_rows"][2]["source_status"],"PREREQUISITE_MISSING_BLOCKED")
        self.assertFalse(r["source_rows"][2]["runtime_permission"])

    def test_09_B09_B10_mismatched_SHA_is_blocked(self):
        d=self.synthetic.make("B09","B10")
        d["reports"]["B10"]["source_clone_sha256"]="f"*64
        source=l04.l03.reconcile(self.matrix,self.synthetic.evaluate(d))
        r=l04.audit(self.manifest,self.matrix,source)
        self.assertEqual(r["source_rows"][1]["documentary_action"],"BLOCK_AND_REVIEW")

    def test_10_B11_unchanged_still_partial_scope(self):
        r=l04.audit(self.manifest,self.matrix,
                    self.synthetic_source("B09","B10","B11"))
        self.assertFalse(r["source_rows"][2]["independent_proof_confirmed"])
        self.assertTrue(r["independent_human_protocol"]["B11_global_save_coverage_unproven"])
        self.assertFalse(r["may_install_live_game"])

    def test_11_R07_candidate_does_not_reserve_MapIDs(self):
        r=l04.audit(self.manifest,self.matrix,self.synthetic_source("R07"))
        self.assertTrue(r["independent_human_protocol"]["R07_mapids_unreserved"])
        self.assertFalse(r["r07_complete"])

    def test_12_R08_full_review_count_does_not_grant_rights(self):
        d=self.synthetic.make("R08")
        d["reports"]["R08"]["per_asset_licenses_reviewed_count"]=14
        r=l04.audit(self.manifest,self.matrix,
                    l04.l03.reconcile(self.matrix,self.synthetic.evaluate(d)))
        self.assertTrue(r["independent_human_protocol"]["R08_asset_rights_not_approved"])
        self.assertFalse(r["r08_complete"])

    def test_13_manifest_unknown_private_field_refused(self):
        self.refuse(lambda m,d,s:m.update(game_path="C:\\Users\\tester\\Game.exe"))
        self.refuse(lambda m,d,s:m["rows"][0].update(hmac_key="secret"))
        self.refuse(lambda m,d,s:m["rows"][2]["criteria"][0].update(
            save_location="C:\\Users\\tester\\Save01.rxdata"))

    def test_14_manifest_missing_row_reordered_or_duplicated_refused(self):
        self.refuse(lambda m,d,s:m["rows"].pop())
        self.refuse(lambda m,d,s:m["rows"].reverse())
        self.refuse(lambda m,d,s:m["rows"][4].update(stage="R07"))

    def test_15_manifest_version_region_or_source_changed_refused(self):
        for k,v in (("version",2),("region","JOHTO"),("schema",True),
                    ("source_matrix","private-file"),
                    ("source_auditor","scripts/game.py"),
                    ("status","PLAYABLE")):
            with self.subTest(k=k):
                self.refuse(lambda m,d,s,k=k,v=v:m.update({k:v}))

    def test_16_manifest_documentary_action_injection_refused(self):
        self.refuse(lambda m,d,s:m["allowed_documentary_actions"].append("APPROVE_GAME"))
        self.refuse(lambda m,d,s:m["allowed_documentary_actions"].remove("BLOCK"))
        self.refuse(lambda m,d,s:m["review_states"].append("PASSED"))

    def test_17_not_reviewed_cannot_be_pretended_human_reviewed(self):
        for state in ("APPROVED","REVIEWED","NEEDS_INDEPENDENT_PRIVATE_REVIEW",
                      "CONFLICTING_OR_INCOMPLETE"):
            self.refuse(lambda m,d,s,state=state:
                m["rows"][0]["criteria"][0].update(review_state=state))

    def test_18_no_manual_signoff_or_evidence_flag_refused(self):
        self.refuse(lambda m,d,s:m["rows"][0]["criteria"][0].update(
            local_human_signoff=True))
        self.refuse(lambda m,d,s:m["rows"][1]["criteria"][0].update(
            independent_evidence_present=True))

    def test_19_criteria_id_or_description_cannot_be_changed(self):
        self.refuse(lambda m,d,s:m["rows"][0]["criteria"][0].update(id="APPROVE_VM"))
        self.refuse(lambda m,d,s:m["rows"][2]["criteria"][0].update(
            requirement="Global save isolation approved"))
        self.refuse(lambda m,d,s:m["rows"][4]["criteria"].pop())

    def test_20_dependencies_and_stage_types_immutable(self):
        self.refuse(lambda m,d,s:m["rows"][1].update(depends_on=[]))
        self.refuse(lambda m,d,s:m["rows"][2].update(depends_on=["B10"]))
        self.refuse(lambda m,d,s:m["rows"][4].update(documentary_kind="NATIVE_READY"))

    def test_21_no_auto_runtime_or_install_permissions_in_manifest(self):
        for k in ("can_launch_game","can_install_region","sinnoh_playable",
                  "game_exe_tested","joiplay_tested","windows_sandbox_executed",
                  "asset_rights_approved","map_ids_reserved",
                  "global_save_isolation_proven"):
            with self.subTest(k=k):
                self.refuse(lambda m,d,s,k=k:m.update({k:True}))

    def test_22_provenance_and_evidence_required_gates_refused_if_weakened(self):
        for k in ("independent_host_authority_required",
                  "raw_native_evidence_not_in_github",
                  "no_unsigned_or_self_reported_approval",
                  "no_cli_execution_tokens",
                  "no_auto_qa_scheduling","no_upload"):
            with self.subTest(k=k):
                self.refuse(lambda m,d,s,k=k:m.update({k:False}))

    def test_23_manifest_native_counts_and_phases_are_immutable(self):
        for k,v in (("native_cases_total",43),("windows_cases",44),
                    ("android_cases",2),("passed_native_cases",1),
                    ("phase_b_approved",1),("phase_c_approved",True),
                    ("phase_d_approved",1)):
            with self.subTest(k=k):
                self.refuse(lambda m,d,s,k=k,v=v:m.update({k:v}))

    def test_24_l03_missing_source_stage_rejected(self):
        self.refuse(lambda m,d,s:s["source_rows"].pop())
        self.refuse(lambda m,d,s:s["source_rows"].reverse())
        self.refuse(lambda m,d,s:s["source_rows"][4].update(stage="R07"))

    def test_25_l03_physical_origin_forgery_rejected(self):
        self.refuse(lambda m,d,s:s["source_rows"][0].update(
            independent_proof_confirmed=True))
        self.refuse(lambda m,d,s:s["source_rows"][2].update(
            runtime_permission=True))
        self.refuse(lambda m,d,s:s["source_rows"][4].update(
            physical_readiness_approved=True))

    def test_26_l03_native_status_counts_and_phase_forgery_rejected(self):
        for field,value in (("native_cases_approved",1),
                            ("native_cases_completed",1),
                            ("phase_b_approved",True),
                            ("phase_c_approved",1),
                            ("r07_complete",True),
                            ("may_start_windows_sandbox",True),
                            ("sinnoh_playable",True)):
            self.refuse(lambda m,d,s,k=field,v=value:s.update({k:v}))

    def test_27_l03_corrupted_count_or_status_rejected(self):
        self.refuse(lambda m,d,s:s["counts"].update(missing=4))
        self.refuse(lambda m,d,s:s["counts"].update(self_reported_unverified=True))
        self.refuse(lambda m,d,s:s.update(
            source_documentary_status="DOCUMENTARY_REVIEW_ONLY_NATIVE_APPROVAL_PENDING"))

    def test_28_l03_extra_private_data_or_raw_paths_rejected(self):
        self.refuse(lambda m,d,s:s["source_rows"][0].update(
            save_path="C:\\Users\\tester\\Save01.rxdata"))
        self.refuse(lambda m,d,s:s["source_rows"][2].update(
            raw_sha="a"*64))

    def test_29_l03_human_protocol_must_require_separate_acceptance(self):
        self.refuse(lambda m,d,s:s["human_acceptance_protocol"].update(
            separate_future_authorization_required=False))
        self.refuse(lambda m,d,s:s["human_dispositions_only"].append("RUN_GAME"))

    def test_30_l03_next_documentary_action_cannot_be_launch_command(self):
        self.refuse(lambda m,d,s:s["source_rows"][0].update(
            documentary_action="RUN_GAME_EXE"))
        self.refuse(lambda m,d,s:s["source_rows"][0].update(
            documentary_review_kind="AUTHENTICATED"))

    def test_31_l03_criteria_drift_rejected(self):
        self.refuse(lambda m,d,s:s["source_rows"][2].update(
            required_separate_human_checks=[]))
        self.refuse(lambda m,d,s:s["source_rows"][1].update(
            depends_on=[]))

    def test_32_report_omits_private_paths_and_hashes(self):
        s=json.dumps(self.audit(),ensure_ascii=True)
        for private in ("C:\\Users","Save01.rxdata","private-baseline.json",
                        "hmac_key","source_clone_sha256","watch_id","a"*64):
            self.assertNotIn(private,s)

    def test_33_cli_default_read_only_and_no_upload(self):
        p=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_sinnoh_l04_human_review.py")],
            cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(p.returncode,0,p.stderr)
        r=json.loads(p.stdout)
        self.assertEqual(r["criteria_total"],20)
        self.assertEqual(r["criteria_reviewed"],0)
        self.assertEqual(r["native_cases_approved"],0)
        self.assertFalse(r["may_launch_game_exe"])

    def test_34_cli_untrusted_path_argument_rejected_without_echo(self):
        path="C:\\Users\\tester\\Save01.rxdata"
        p=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_sinnoh_l04_human_review.py"),
            "--path",path],cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(p.returncode,2)
        self.assertIn("SINNOH_L04_BLOCKED",p.stderr)
        self.assertNotIn(path,p.stderr)
        self.assertNotIn("C:\\Users",p.stderr)

    def test_35_no_native_io_import_or_transmit_in_L04_code(self):
        source=(ROOT/"scripts/regions/audit_sinnoh_l04_human_review.py").read_text("utf8")
        for x in ("import subprocess","import requests","import socket","os.system(",
                  "os.popen(","os.walk(","rglob(","shutil.copy","Game.exe').read_bytes",
                  "private-baseline.json\").read"):
            self.assertNotIn(x,source)
        self.assertIn("l03.run(root,workspace=workspace)",source)

if __name__=="__main__":
    unittest.main()
