"""L06 independent negative/positive synthetic documentary-routing tests."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l06_human_evidence as l06
l05 = l06.l05


class SinnohL06Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reader = l05.l04.l03.l02.l00.read_json
        cls.doc = reader(ROOT, l06.MATRIX, maxsize=175000)
        cls.matrix = reader(ROOT, l05.MATRIX, maxsize=150000)
        cls.checklist = reader(ROOT, l05.l04.CHECKLIST, maxsize=65536)
        cls.handoff = reader(ROOT, l05.HANDOFF, maxsize=150000)
        cls.lr = l05.run(ROOT)
        cls.hr = l05.l04.run(ROOT)
        cls.gr = l05.G12.run(ROOT)

    def audited(self, mutate=None):
        values = [copy.deepcopy(x) for x in (
            self.doc, self.matrix, self.checklist, self.handoff,
            self.lr, self.hr, self.gr,
        )]
        if mutate is not None:
            mutate(*values)
        return l06.audit(*values)

    def rejected(self, mutate):
        with self.assertRaises(ValueError):
            self.audited(mutate)

    def test_01_public_documentary_baseline(self):
        result = self.audited()
        self.assertEqual(result["stage"], "L06")
        self.assertEqual(result["status"], "DOCUMENTARY_REVIEW_QUEUE_VALID_44_NATIVE_BLOCKED")
        self.assertEqual(result["mode"], "PUBLIC_GITHUB_ONLY")
        self.assertEqual((result["native_cases_total"], result["native_cases_approved"]), (44, 0))
        self.assertEqual((result["windows_cases"], result["android_cases"]), (43, 1))

    def test_02_every_g12_case_has_identical_identifier_order(self):
        result = self.audited()
        self.assertEqual([r["id"] for r in result["cases"]],
                         [r["id"] for r in self.handoff["cases"]])
        self.assertEqual(len({r["id"] for r in result["cases"]}), 44)

    def test_03_all_20_l04_criteria_routed_and_unreviewed(self):
        self.assertEqual(set(c for r in self.doc["rows"]
                             for c in r["required_criteria_ids"]),
                         set(self.matrix["expected_criteria_ids"]))
        self.assertTrue(all(r["review_state"] == "NOT_REVIEWED" for r in self.doc["rows"]))
        self.assertEqual(self.audited()["criteria_human_approved"], 0)

    def test_04_windows_and_android_not_mutually_authorizing(self):
        result = self.audited()
        self.assertEqual(result["cases"][-1]["platform"], "android")
        self.assertNotIn("B10", result["cases"][-1]["blocked_by"])
        self.assertNotIn("B11", result["cases"][-1]["blocked_by"])
        self.assertTrue(all("B10" in r["blocked_by"] and "B11" in r["blocked_by"]
                            for r in result["cases"][:-1]))
        self.assertTrue(result["windows_android_review_is_independent"])

    def test_05_no_case_is_native_approved(self):
        out = self.audited()
        for r in out["cases"]:
            self.assertEqual(r["action"], "KEEP_PENDING")
            self.assertEqual(r["native_status"], "pending")
            self.assertFalse(r["native_qa_authorized"])
            self.assertFalse(r["evidence_accepted"])
            self.assertTrue(all(s.startswith("REQUEST_") or s.startswith("REVIEW_")
                                for s in r["documentary_check_codes"]))
        for flag in ("may_run_game_exe", "may_run_joiplay",
                     "may_start_windows_sandbox", "may_install_live_game",
                     "sinnoh_playable", "auto_upload"):
            self.assertIs(out[flag], False)

    def test_06_public_output_redacts_private_content(self):
        out = json.dumps(self.audited(), ensure_ascii=True)
        for secret in (r"C:\\Users", "Save01.rxdata", "private-baseline.json",
                       "watch_id", "hmac_key", "source_clone_sha256"):
            self.assertNotIn(secret, out)

    def test_07_cli_valid_only_without_workspace_arguments(self):
        cmd = [sys.executable,
               str(ROOT / "scripts/regions/audit_sinnoh_l06_human_evidence.py")]
        p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(p.returncode, 0, p.stderr)
        out = json.loads(p.stdout)
        self.assertEqual((out["native_cases_total"], out["criteria_human_approved"]), (44, 0))
        self.assertTrue(out["L06_is_not_local_android_L05"])
        denied = subprocess.run(cmd + ["--evidence", r"C:\\Users\\name\\Save01.rxdata"],
                                cwd=ROOT, text=True, capture_output=True, check=False)
        self.assertEqual(denied.returncode, 2)
        self.assertIn("SINNOH_L06_BLOCKED", denied.stderr)
        self.assertNotIn("Save01.rxdata", denied.stdout + denied.stderr)

    def test_08_no_execution_or_upload_code_in_auditor(self):
        script = (ROOT / "scripts/regions/audit_sinnoh_l06_human_evidence.py").read_text("utf8")
        for forbidden in ("import subprocess", "import requests", "import socket",
                          "os.walk(", "rglob(", "os.system(", "shutil.copy(",
                          "subprocess.run(", "from urllib"):
            self.assertNotIn(forbidden, script)

    def test_negative_01_removed_case(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"].pop())

    def test_negative_02_duplicate_case(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"].append(copy.deepcopy(d["rows"][0])))

    def test_negative_03_case_order(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"].reverse())

    def test_negative_04_invented_id(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0].update(case_id="ball-FAKE"))

    def test_negative_05_duplicate_id(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][1].update(case_id=d["rows"][0]["case_id"]))

    def test_negative_06_wrong_kind(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0].update(kind="warp"))

    def test_negative_07_wrong_windows_platform(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0].update(platform="android"))

    def test_negative_08_wrong_android_platform(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][-1].update(platform="windows"))

    def test_negative_09_criterion_removed(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0]["required_criteria_ids"].pop())

    def test_negative_10_criterion_order(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0]["required_criteria_ids"].reverse())

    def test_negative_11_criterion_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0]["required_criteria_ids"].append("B09_FAKE"))

    def test_negative_12_blocking_stage_removed(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0]["blocking_stages"].remove("B11"))

    def test_negative_13_android_windows_stage(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][-1]["blocking_stages"].append("B10"))

    def test_negative_14_windows_queue_swapped(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0].update(human_review_queue="ANDROID_DEVICE_DOCUMENTARY_REVIEW"))

    def test_negative_15_android_queue_swapped(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][-1].update(human_review_queue="WINDOWS_HOST_DOCUMENTARY_REVIEW"))

    def test_negative_16_windows_authorization_gate(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0].update(future_native_gate="WINDOWS_QA_APPROVED"))

    def test_negative_17_android_authorization_gate(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][-1].update(future_native_gate="ANDROID_QA_APPROVED"))

    def test_negative_18_missing_document_request(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0]["documentary_check_codes"].pop())

    def test_negative_19_injected_document_request(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0]["documentary_check_codes"].append("APPROVE_RUNTIME"))

    def test_negative_20_changed_document_request(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][-1]["documentary_check_codes"].__setitem__(0,"REQUEST_APPROVED"))

    def test_negative_21_row_action_removed(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0]["allowed_actions"].pop())

    def test_negative_22_row_action_execution(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0]["allowed_actions"].append("RUN_GAME"))

    def test_negative_23_decision_approved(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0].update(current_action="APPROVE"))

    def test_negative_24_review_marked_done(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0].update(review_state="REVIEWED"))

    def test_negative_25_native_marked_pass(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0].update(native_status="passed"))

    def test_negative_26_evidence_claimed(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0].update(human_evidence_accepted=True))

    def test_negative_27_human_signoff(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0].update(independent_reviewer_signoff=True))

    def test_negative_28_execute_case(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0].update(native_qa_authorized=True))

    def test_negative_29_case_new_field(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["rows"][0].update(private_file="host-save.dat"))

    def test_negative_30_schema_changed(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(schema=2))

    def test_negative_31_stage_changed(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(stage="L07"))

    def test_negative_32_version_changed(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(version=2))

    def test_negative_33_status_ready(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(status="READY"))

    def test_negative_34_locally_received_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(locally_received_reports=5))

    def test_negative_35_human_approved_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(criteria_human_approved=20))

    def test_negative_36_native_count_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(native_cases_completed=44))

    def test_negative_37_native_approved_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(native_cases_approved=1))

    def test_negative_38_phase_b_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(phase_b_approved=1))

    def test_negative_39_phase_c_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(phase_c_approved=1))

    def test_negative_40_phase_d_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(phase_d_approved=1))

    def test_negative_41_r07_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(r07_complete=True))

    def test_negative_42_r08_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(r08_complete=True))

    def test_negative_43_r09_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(r09_complete=True))

    def test_negative_44_global_save_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(global_save_isolation_proven=True))

    def test_negative_45_rights_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(asset_rights_approved=True))

    def test_negative_46_mapids_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(mapids_reserved=True))

    def test_negative_47_sandbox_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(windows_sandbox_executed=True))

    def test_negative_48_joiplay_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(joiplay_tested=True))

    def test_negative_49_upload_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(auto_upload=True))

    def test_negative_50_execute_windows_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(can_execute_windows_qa=True))

    def test_negative_51_execute_android_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(can_execute_android_qa=True))

    def test_negative_52_install_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(can_install_live_game=True))

    def test_negative_53_playable_forged(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(sinnoh_playable=True))

    def test_negative_54_source_l05_swapped(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(source_l05="private/native.json"))

    def test_negative_55_source_l04_swapped(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(source_l04="other.json"))

    def test_negative_56_source_g12_swapped(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(source_g12="other.json"))

    def test_negative_57_top_level_action_execution(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d["allowed_documentary_actions"].append("RUN_JOIPLAY"))

    def test_negative_58_private_payload_top_level(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: d.update(raw_evidence={"Save01.rxdata":"contents"}))

    def test_negative_59_upstream_l05_platform_forgery(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: m["rows"][-1].update(platform="windows"))

    def test_negative_60_upstream_l05_national_rights_forgery(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: m.update(asset_rights_approved=True))

    def test_negative_61_upstream_l04_signoff(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: h["rows"][0]["criteria"][0].update(local_human_signoff=True))

    def test_negative_62_upstream_g12_native_pass(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: g["cases"][0].update(native_status="passed"))

    def test_negative_63_upstream_l05_report_pass(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: lr.update(native_cases_approved=1))

    def test_negative_64_upstream_l04_report_pass(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: hr.update(criteria_reviewed=1))

    def test_negative_65_upstream_g12_report_pass(self):
        self.rejected(lambda d, m, h, g, lr, hr, gr: gr.update(evidence_accepted_cases=1))

if __name__ == "__main__":
    unittest.main()
