"""S31: verify native-acceptance REPORTING, not pretend native gameplay."""
from __future__ import annotations
import copy
import json
import sys
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_s31_acceptance as s31
from audit_sinnoh_android_ch20 import audit as ch20

class S31AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=json.loads(s31.CONTRACT.read_text("utf-8"))
        cls.progress=json.loads((ROOT/"data/regions/sinnoh-progress.json").read_text("utf-8"))
        cls.static=ch20(root=ROOT)

    def verify(self,contract=None,progress=None,static=None):
        return s31.reconcile(
            copy.deepcopy(self.contract if contract is None else contract),
            copy.deepcopy(self.progress if progress is None else progress),
            copy.deepcopy(self.static if static is None else static))

    def test_01_empty_native_proofs_are_explicitly_blocked(self):
        result=self.verify()
        self.assertEqual(result["expected_native_cases"],44)
        self.assertEqual(result["observations_with_consistent_evidence"],0)
        self.assertEqual(result["remaining_cases"],44)
        self.assertEqual(result["status"],"BLOCKED_NO_COMPILED_QA")
        self.assertFalse(result["can_mark_playable"])
        self.assertFalse(result["automatic_approval"])
        self.assertFalse(result["joiplay_independently_verified"])
        self.assertFalse(result["native_game_exe_independently_verified"])

    def test_02_all_44_groups_accounted(self):
        self.assertEqual(self.contract["expected_by_kind"],
            {"starter":3,"barry":12,"save_reload":3,"warp":16,
             "npc":5,"regression":4,"android":1})
        self.assertEqual(sum(self.contract["expected_by_kind"].values()),44)

    def test_03_cli_prints_report_without_native_claim(self):
        run=subprocess.run([sys.executable,str(s31.ROOT/"scripts/regions/audit_sinnoh_s31_acceptance.py")],
                           capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(run.returncode,0,run.stderr)
        x=json.loads(run.stdout)
        self.assertEqual(x["status"],"BLOCKED_NO_COMPILED_QA")
        self.assertEqual(x["remaining_cases"],44)

    def test_04_require_native_causes_nonzero_exit(self):
        p=subprocess.run([sys.executable,str(s31.ROOT/"scripts/regions/audit_sinnoh_s31_acceptance.py"),
                          "--require-native"],capture_output=True,cwd=ROOT)
        self.assertEqual(p.returncode,2)

    def test_05_rejects_forged_release_flags(self):
        for key in ("release_marker_allowed","native_game_exe_tested",
                    "native_joiplay_tested","gameplay_playable","auto_accept",
                    "phase_approval_allowed","source_rights_verified",
                    "physical_maps_verified"):
            with self.subTest(key=key):
                x=copy.deepcopy(self.contract);x[key]=True
                with self.assertRaisesRegex(ValueError,"SINNOH_S31_BLOCKED"):
                    self.verify(contract=x)

    def test_06_rejects_fake_native_evidence_count(self):
        x=copy.deepcopy(self.contract);x["native_observations_verified"]=44
        with self.assertRaisesRegex(ValueError,"SINNOH_S31_BLOCKED"):
            self.verify(contract=x)

    def test_07_rejects_other_region(self):
        x=copy.deepcopy(self.contract);x["region"]="KANTO"
        with self.assertRaisesRegex(ValueError,"SINNOH_S31_BLOCKED"):
            self.verify(contract=x)

    def test_08_rejects_wrong_platform_counts(self):
        x=copy.deepcopy(self.contract);x["windows_cases_required"]=44
        with self.assertRaisesRegex(ValueError,"SINNOH_S31_BLOCKED"):
            self.verify(contract=x)

    def test_09_rejects_removed_case(self):
        x=copy.deepcopy(self.static);x["cases"].pop()
        with self.assertRaisesRegex(ValueError,"SINNOH_S31_BLOCKED"):
            self.verify(static=x)

    def test_10_rejects_reordered_or_duplicated_case(self):
        x=copy.deepcopy(self.static)
        x["cases"][0]=x["cases"][1]
        with self.assertRaisesRegex(ValueError,"SINNOH_S31_BLOCKED"):
            self.verify(static=x)

    def test_11_rejects_forged_static_completion(self):
        x=copy.deepcopy(self.static);x["completed_native_cases"]=44
        with self.assertRaisesRegex(ValueError,"SINNOH_S31_BLOCKED"):
            self.verify(static=x)

    def test_12_rejects_forged_phase_gate_even_after_32(self):
        x=copy.deepcopy(self.progress);x["phase_gates"]["fully_tested_native"]=13
        with self.assertRaisesRegex(ValueError,"SINNOH_S31_BLOCKED"):
            self.verify(progress=x)

    def test_13_rejects_fake_joiplay_claim(self):
        x=copy.deepcopy(self.progress)
        x["native_playtest_workstream"]["android_joi_play_tested"]=True
        with self.assertRaisesRegex(ValueError,"SINNOH_S31_BLOCKED"):
            self.verify(progress=x)

    def test_14_rejects_fake_review_or_ready_marker(self):
        for key in ("manual_evidence_accepted","ready_marker_created","native_qa_approved"):
            with self.subTest(key=key):
                x=copy.deepcopy(self.progress);x["native_playtest_workstream"][key]=True
                with self.assertRaisesRegex(ValueError,"SINNOH_S31_BLOCKED"):
                    self.verify(progress=x)

    def test_15_rejects_false_T05_to_T07_progress(self):
        x=copy.deepcopy(self.progress)
        x["native_playtest_workstream"]["substeps"][4]["complete"]=True
        with self.assertRaisesRegex(ValueError,"SINNOH_S31_BLOCKED"):
            self.verify(progress=x)

    def test_16_rejects_spoofed_100_percent_without_all_tasks(self):
        x=copy.deepcopy(self.progress)
        x["tasks"][30]["status"]="partial"
        with self.assertRaisesRegex(ValueError,"SINNOH_S31_BLOCKED"):
            self.verify(progress=x)

    def test_17_private_QA_fixture_is_not_native_approval(self):
        from test_sinnoh_playtest_audit import SinnohManualPlaytestAuditTests
        fake=SinnohManualPlaytestAuditTests(methodName="test_empty_evidence_is_pending_not_native_success")
        fake.setUp()
        try:
            result=s31.run(root=ROOT,qa=fake.qa,qa_project=fake.project)
            self.assertEqual(result["status"],"PENDING_REAL_QA_EVIDENCE")
            self.assertTrue(result["private_compiled_qa_profile_checked"])
            self.assertEqual(result["remaining_cases"],44)
            plan=json.loads(fake.file.read_text("utf-8"))
            c=plan["cases"][0]
            fake.attach(c,{"species":c["starter"],"second_ball_denied":True})
            fake.save(plan)
            report=s31.run(root=ROOT,qa=fake.qa,qa_project=fake.project)
            self.assertEqual(report["observations_with_consistent_evidence"],1)
            self.assertFalse(report["native_game_exe_independently_verified"])
            self.assertFalse(report["can_mark_playable"])
        finally:
            fake.doCleanups()

    def test_18_missing_or_unverified_qa_rejected(self):
        with self.assertRaises(ValueError):
            s31.run(root=ROOT,qa=ROOT/"game",qa_project=ROOT)

    def test_19_native_gate_zero_on_full_development_bar(self):
        x=self.progress
        self.assertEqual((x["development"]["done"],x["development"]["partial"],
                          x["development"]["pending"],x["development"]["percent_complete"]),
                         (32,0,0,100))
        self.assertEqual(x["native_playtest_workstream"]["complete"],4)
        self.assertEqual(x["intro_workstream"]["complete"],5)
        self.assertEqual(x["remap_workstream"]["complete"],6)
        self.assertEqual(x["phase_gates"]["playable_in_game_executable"],0)

if __name__=="__main__":unittest.main()
