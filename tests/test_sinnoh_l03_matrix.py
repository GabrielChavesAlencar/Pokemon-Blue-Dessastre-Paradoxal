"""L03: offline documentary human-decision protocol, never native QA approval."""
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
import audit_sinnoh_l03_matrix as l03
import test_sinnoh_l02_evidence as fixture_module

class SinnohL03MatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=l03.l02.l00.read_json(ROOT,l03.MATRIX,maxsize=65536)
        cls.public_review=l03.l02.run(ROOT)
        fixture_module.SinnohL02ReviewTests.setUpClass()
        cls.fixtures=fixture_module.SinnohL02ReviewTests(
            "test_01_default_all_five_missing_not_native_approved")

    def merged(self,mutation=None):
        m=copy.deepcopy(self.manifest)
        l=copy.deepcopy(self.public_review)
        if mutation:mutation(m,l)
        return l03.reconcile(m,l)

    def rejected(self,mutation):
        with self.assertRaisesRegex(ValueError,"SINNOH_L03_BLOCKED"):
            self.merged(mutation)

    def all_sources(self,*stages):
        return self.fixtures.evaluate(self.fixtures.make(*stages))

    def test_01_public_default_five_missing_and_no_native(self):
        r=self.merged()
        self.assertEqual(r["counts"]["missing"],5)
        self.assertEqual(r["status"],"DOCUMENTARY_HANDOFF_REQUIRES_SEPARATE_HUMAN_REVIEW")
        self.assertEqual(r["native_cases_approved"],0)
        self.assertFalse(r["sinnoh_playable"])

    def test_02_exact_source_order_and_no_duplicates(self):
        r=self.merged()
        self.assertEqual([x["stage"] for x in r["rows"]],list(l03.STAGES))
        self.assertEqual(len(set(x["stage"] for x in r["rows"])),5)

    def test_03_versions_and_inputs_are_public_fixed_paths(self):
        self.assertTrue(l03.validate_manifest(self.manifest))
        self.assertEqual(self.manifest["version"],1)
        self.assertEqual(self.manifest["source_envelope"],l03.l02.l00.TEMPLATE)
        self.assertEqual(self.manifest["stage"],"L03")

    def test_04_status_map_all_four_states_are_safe_actions(self):
        self.assertEqual(set(l03.ACTIONS),set(l03.STATUSES))
        self.assertEqual(self.manifest["status_actions"],l03.ACTIONS)
        self.assertTrue(all("APPROVE" not in v and "EXECUTE" not in v
                            for v in l03.ACTIONS.values()))

    def test_05_all_five_self_reported_still_block_native(self):
        result=l03.reconcile(self.manifest,self.all_sources(*l03.STAGES))
        self.assertEqual(result["counts"]["self_reported_unverified"],5)
        self.assertEqual(result["counts"]["human_physical_evidence_accepted"],0)
        self.assertTrue(all(x["safe_next_action"]=="SCHEDULE_DOCUMENTARY_ANALYSIS"
                            for x in result["rows"]))
        self.assertFalse(result["may_start_windows_sandbox"])

    def test_06_B10_missing_B09_remains_prerequisite_block(self):
        result=l03.reconcile(self.manifest,self.all_sources("B10"))
        rows={x["stage"]:x for x in result["rows"]}
        self.assertEqual(rows["B10"]["status"],l03.l02.STATUS_DEPENDENCY)
        self.assertEqual(rows["B10"]["safe_next_action"],"RECONCILE_PREREQUISITES")

    def test_07_B11_missing_B09_B10_remains_prerequisite_block(self):
        result=l03.reconcile(self.manifest,self.all_sources("B11"))
        rows={x["stage"]:x for x in result["rows"]}
        self.assertEqual(rows["B11"]["status"],l03.l02.STATUS_DEPENDENCY)
        self.assertEqual(rows["B11"]["depends_on"],["B09","B10"])

    def test_08_B09_invalid_hash_conflict_is_blocked_without_echo(self):
        d=self.fixtures.make("B09","B10")
        d["reports"]["B09"]["plan_sha256"]="private-value-123"
        r=l03.reconcile(self.manifest,self.fixtures.evaluate(d))
        rows={x["stage"]:x for x in r["rows"]}
        self.assertEqual(rows["B09"]["status"],l03.l02.STATUS_BLOCKED)
        self.assertEqual(rows["B10"]["status"],l03.l02.STATUS_DEPENDENCY)
        self.assertNotIn("private-value-123",json.dumps(r))

    def test_09_B10_SHA_mismatch_conflict_in_L03(self):
        d=self.fixtures.make("B09","B10")
        d["reports"]["B10"]["source_clone_sha256"]="f"*64
        result=l03.reconcile(self.manifest,self.fixtures.evaluate(d))
        self.assertEqual(result["counts"]["conflicting"],1)
        self.assertFalse(result["may_install_live_game"])

    def test_10_B11_watch_unchanged_never_global_isolation(self):
        result=l03.reconcile(self.manifest,self.all_sources("B09","B10","B11"))
        self.assertTrue(result["human_acceptance_protocol"]["b11_session_link_not_verified"])
        self.assertEqual(result["rows"][2]["documentary_review_kind"],"LIMITED_SAVE_SCOPE")
        self.assertFalse(result["physical_qa_preapproved"])

    def test_11_R07_candidate_is_never_allocated_MapID(self):
        d=self.fixtures.make("R07")
        x=d["reports"]["R07"]
        x.update(status="CANDIDATE_READY_FOR_MANUAL_REVIEW_NOT_APPROVED",
                 native_snapshot_present=True,native_occupied_count=648,
                 native_mapinfos_sha256=self.fixtures.contracts["B09"]["native_baseline_mapinfos_sha256"],
                 future_regions_with_evidence=3,collisions_count=0,candidate_safety_reviewable=True)
        r=l03.reconcile(self.manifest,self.fixtures.evaluate(d))
        self.assertEqual(r["rows"][3]["status"],l03.l02.STATUS_UNVERIFIED)
        self.assertFalse(r["r07_complete"])

    def test_12_R08_fourteen_reviews_are_not_licenses(self):
        d=self.fixtures.make("R08")
        d["reports"]["R08"]["per_asset_licenses_reviewed_count"]=14
        r=l03.reconcile(self.manifest,self.fixtures.evaluate(d))
        self.assertEqual(r["rows"][4]["status"],l03.l02.STATUS_UNVERIFIED)
        self.assertFalse(r["r08_complete"])
        self.assertFalse(r["may_install_live_game"])

    def test_13_missing_row_and_duplicate_stage_manifest_rejected(self):
        self.rejected(lambda m,l:m["rows"].pop())
        self.rejected(lambda m,l:m["rows"][4].update(stage="R07"))
        self.rejected(lambda m,l:m["rows"].reverse())

    def test_14_private_extra_manifest_data_rejected(self):
        self.rejected(lambda m,l:m.update(save_path="C:\\Users\\tester\\Save01.rxdata"))
        self.rejected(lambda m,l:m["rows"][0].update(hmac_key="private"))
        self.rejected(lambda m,l:m["rows"][2].update(watch_id="a"*32))

    def test_15_manifest_schema_version_and_region_cannot_change(self):
        for key,val in (("schema",2),("schema",True),("stage","R09"),
                        ("region","KANTO"),("version",2)):
            with self.subTest(key=key):
                self.rejected(lambda m,l,k=key,v=val:m.update({k:v}))

    def test_16_missing_protocol_rule_rejected(self):
        self.rejected(lambda m,l:m.pop("status_actions"))
        self.rejected(lambda m,l:m["status_actions"].pop(l03.l02.STATUS_BLOCKED))

    def test_17_injected_executable_action_rejected(self):
        self.rejected(lambda m,l:m["status_actions"].update({
            l03.l02.STATUS_UNVERIFIED:"EXECUTE_GAME_EXE"}))
        self.rejected(lambda m,l:m["allowed_human_dispositions"].append("APPROVE_NATIVE_QA"))

    def test_18_dependency_mutations_blocked(self):
        self.rejected(lambda m,l:m["rows"][1].update(depends_on=[]))
        self.rejected(lambda m,l:m["rows"][2].update(depends_on=["B10"]))
        self.rejected(lambda m,l:m["rows"][4].update(depends_on=["B09"]))

    def test_19_changed_review_criteria_blocked(self):
        self.rejected(lambda m,l:m["rows"][0]["criteria"].append("native_ready"))
        self.rejected(lambda m,l:m["rows"][2].update(review_kind="FULL_SAVE_COVERAGE"))
        self.rejected(lambda m,l:m["rows"][3].update(criteria=[]))

    def test_20_premature_review_acceptance_blocked(self):
        self.rejected(lambda m,l:m["rows"][0].update(independent_evidence_accepted=True))
        self.rejected(lambda m,l:m["rows"][2].update(physical_ready=True))
        self.rejected(lambda m,l:m["rows"][4].update(baseline_status=l03.l02.STATUS_UNVERIFIED))

    def test_21_manifest_false_gates_cannot_turn_true(self):
        for key in l03.FIXED_FALSE:
            with self.subTest(field=key):
                self.rejected(lambda m,l,k=key:m.update({k:True}))

    def test_22_manifest_safety_requirements_cannot_turn_false(self):
        for key in l03.FIXED_TRUE:
            with self.subTest(field=key):
                self.rejected(lambda m,l,k=key:m.update({k:False}))

    def test_23_all_native_case_and_phase_counts_must_remain_unchanged(self):
        for key,val in (("native_test_cases_total",43),("windows_cases",44),
                        ("android_cases",2),("passed_native_cases",1),
                        ("phase_b_approved",True),("phase_c_approved",1),
                        ("phase_d_approved",1)):
            with self.subTest(field=key):
                self.rejected(lambda m,l,k=key,v=val:m.update({k:v}))

    def test_24_extra_L02_stage_rejected(self):
        self.rejected(lambda m,l:l["reports"].update(JOHTO={"status":"MISSING_REPORT"}))
        self.rejected(lambda m,l:l["reports"].pop("B09"))

    def test_25_L02_native_approval_flags_rejected(self):
        for key in ("r07_complete","r08_complete","r09_complete",
                    "game_exe_tested","joiplay_tested","windows_sandbox_executed",
                    "host_saves_accessed","host_saves_globally_isolated_proven",
                    "game_installed","may_start_game_in_host","may_start_game_in_vm",
                    "may_install_live_game","sinnoh_playable","auto_uploaded"):
            with self.subTest(field=key):
                self.rejected(lambda m,l,k=key:l.update({k:True}))

    def test_26_L02_wrong_global_status_cannot_be_reflected(self):
        self.rejected(lambda m,l:l.update(status="PRIVATE_PATH_C:\\Users\\tester"))
        self.rejected(lambda m,l:l.update(status="DOCUMENTARY_REVIEW_ONLY_NATIVE_APPROVAL_PENDING"))

    def test_27_L02_fake_counts_and_bool_as_int_rejected(self):
        self.rejected(lambda m,l:l["counts"].update(total=4))
        self.rejected(lambda m,l:l["counts"].update(missing=4))
        self.rejected(lambda m,l:l["counts"].update(independently_accepted=1))
        self.rejected(lambda m,l:l["counts"].update(missing=True))
        self.rejected(lambda m,l:l["counts"].update(private="secret"))

    def test_28_L02_stage_human_review_and_authentication_cannot_advance(self):
        self.rejected(lambda m,l:l["reports"]["B09"].update(native_approval=True))
        self.rejected(lambda m,l:l["reports"]["B09"].update(physical_origin_authenticated=True))
        self.rejected(lambda m,l:l["reports"]["B09"].update(human_review_required=False))

    def test_29_L02_status_unknown_or_malformed_rejected(self):
        self.rejected(lambda m,l:l["reports"]["B09"].update(status="APPROVED"))
        self.rejected(lambda m,l:l["reports"]["B09"].update(reason_code={}))
        self.rejected(lambda m,l:l["reports"]["B09"].update(private_snapshot="secret"))

    def test_30_L02_review_kind_action_text_is_fixed_no_raw_echo(self):
        d=copy.deepcopy(self.public_review)
        d["reports"]["B09"]["reason_code"]="C:\\Users\\tester\\Save01.rxdata"
        r=l03.reconcile(self.manifest,d)
        self.assertNotIn("Save01.rxdata",json.dumps(r))
        self.assertNotIn("C:\\Users",json.dumps(r))
        self.assertEqual(r["rows"][0]["safe_next_action"],"REQUEST_NEW_SANITIZED_REPORT")

    def test_31_L02_wrong_human_next_action_is_rejected(self):
        self.rejected(lambda m,l:l["reports"]["B09"].update(next_human_action="Run Game.exe"))

    def test_32_L02_missing_chronology_or_fake_session_link_rejected(self):
        self.rejected(lambda m,l:l.update(chronology_dates_in_sanitized_sources_available=True))
        self.rejected(lambda m,l:l.update(b11_session_link_in_sanitized_sources_available=True))
        self.rejected(lambda m,l:l.update(independent_receipt_authenticity_proven=True))

    def test_33_L02_gates_and_phases_cannot_advance(self):
        self.rejected(lambda m,l:l["local_qa_gates"].update(L01="APPROVED"))
        self.rejected(lambda m,l:l.update(phase_b_approved=1))
        self.rejected(lambda m,l:l.update(phase_c_approved=True))

    def test_34_human_protocol_is_not_automatic_acceptance(self):
        r=self.merged()
        protocol=r["human_acceptance_protocol"]
        self.assertTrue(all(protocol.values()))
        self.assertEqual(r["counts"]["human_physical_evidence_accepted"],0)
        self.assertFalse(r["may_run_game_exe"])
        self.assertFalse(r["may_run_joiplay"])

    def test_35_public_JSON_omits_private_values_and_digests(self):
        data=json.dumps(self.merged(),sort_keys=True)
        for forbidden in ("source_clone_sha256","native_mapinfos_sha256",
                          "watch_id","private-baseline.json","hmac_key",
                          "Save01.rxdata","C:\\Users", "a"*64):
            self.assertNotIn(forbidden,data)

    def test_36_default_CLI_is_read_only_no_workspace_created(self):
        p=ROOT/".blue-work/sinnoh-l03"
        old=p.exists()
        proc=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l03_matrix.py")],
                            cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(proc.returncode,0,proc.stderr)
        r=json.loads(proc.stdout)
        self.assertEqual(r["counts"]["missing"],5)
        self.assertFalse(p.exists() and not old)

    def test_37_CLI_rejects_private_input_flag_without_echo(self):
        raw="C:\\Users\\test\\Save01.rxdata"
        proc=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l03_matrix.py"),
                             "--file",raw],cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(proc.returncode,2)
        self.assertNotIn(raw,proc.stderr)
        self.assertIn("SINNOH_L03_BLOCKED",proc.stderr)

    def test_38_workspace_input_optional_fixed_path_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/".blue-work/sinnoh-l00-input").mkdir(parents=True)
            p=root/".blue-work/sinnoh-l00-input/public-reports.json"
            p.write_text(json.dumps(self.fixtures.make("R08")),encoding="utf-8")
            d=l03.l02.l00.read_json(root,l03.l02.l00.PRIVATE_REPORT,maxsize=65536)
            self.assertIsNotNone(d["reports"]["R08"])
            self.assertFalse((root/"Game.exe").exists())

    def test_39_no_network_process_save_png_or_game_read_in_L03_source(self):
        s=(ROOT/"scripts/regions/audit_sinnoh_l03_matrix.py").read_text("utf-8")
        for forbidden in ("import requests","import socket","import subprocess",
                          "os.system(","os.popen(","os.walk(","rglob(",
                          "Game.exe').read_bytes","private-baseline.json\").read"):
            self.assertNotIn(forbidden,s)

    def test_40_L02_invalid_report_detected_by_actual_parent_before_handoff(self):
        d=self.fixtures.make("B09")
        d["reports"]["B09"]["phase_b_approved"]=1
        r=self.fixtures.evaluate(d)
        out=l03.reconcile(self.manifest,r)
        self.assertEqual(out["rows"][0]["status"],l03.l02.STATUS_BLOCKED)
        self.assertEqual(out["rows"][0]["safe_next_action"],"BLOCK_AND_REVIEW")

if __name__=="__main__":
    unittest.main()
