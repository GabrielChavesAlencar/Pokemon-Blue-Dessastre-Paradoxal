"""Sinnoh L05: synthetic-only, 44 native cases remain blocked by 20 L04 criteria."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_l05_native_dependencies as l05


class SinnohL05Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read=l05.l04.l03.l02.l00.read_json
        cls.matrix=read(ROOT,l05.MATRIX,maxsize=150000)
        cls.checklist=read(ROOT,l05.l04.CHECKLIST,maxsize=65536)
        cls.handoff=read(ROOT,l05.HANDOFF,maxsize=150000)
        cls.l04_report=l05.l04.run(ROOT)
        cls.g12_report=l05.G12.run(ROOT)

    def report(self,mutator=None):
        m=copy.deepcopy(self.matrix)
        h=copy.deepcopy(self.checklist)
        g=copy.deepcopy(self.handoff)
        l=copy.deepcopy(self.l04_report)
        g12=copy.deepcopy(self.g12_report)
        if mutator:
            mutator(m,h,g,l,g12)
        return l05.audit(m,h,g,l,g12)

    def rejected(self,mutator):
        with self.assertRaisesRegex(ValueError,"SINNOH_L05_BLOCKED"):
            self.report(mutator)

    def test_01_all_44_CH20_cases_present_and_pending(self):
        r=self.report()
        self.assertEqual(len(r["cases"]),44)
        self.assertEqual(r["native_cases_completed"],0)
        self.assertEqual(r["native_cases_approved"],0)
        self.assertTrue(all(x["state"]=="NATIVE_QA_NOT_AUTHORIZED" for x in r["cases"]))

    def test_02_all_20_L04_criteria_mapped(self):
        r=self.report()
        used=set(x for item in r["cases"] for x in item["required_criteria_ids"])
        self.assertEqual(used,set(self.matrix["expected_criteria_ids"]))
        self.assertEqual((r["criteria_total"],r["criteria_human_approved"]),(20,0))

    def test_03_actual_G12_order_and_ids_preserved(self):
        self.assertEqual(
            [r["case_id"] for r in self.matrix["rows"]],
            [r["id"] for r in self.handoff["cases"]])
        self.assertEqual(len(set(r["case_id"] for r in self.matrix["rows"])),44)

    def test_04_43_windows_one_android_not_merged(self):
        r=self.report()
        self.assertEqual((r["windows_cases"],r["android_cases"]),(43,1))
        self.assertEqual(r["cases"][-1]["id"],"android-joi-play")
        self.assertEqual(r["cases"][-1]["platform"],"android")
        self.assertNotIn("B10",r["cases"][-1]["blocked_by"])
        self.assertNotIn("B11",r["cases"][-1]["blocked_by"])

    def test_05_real_kind_distribution_from_G12(self):
        self.assertEqual(self.report()["cases_by_kind"],
                         {"starter":3,"barry":12,"save_reload":3,"warp":16,
                          "npc":5,"regression":4,"android":1})

    def test_06_windows_require_isolation_and_save_scope(self):
        for row in self.matrix["rows"]:
            if row["platform"]=="windows":
                self.assertIn("B10_LINK",row["required_criteria_ids"])
                self.assertIn("B11_SCOPE",row["required_criteria_ids"])
                self.assertIn("B11_LIMIT",row["required_criteria_ids"])

    def test_07_warps_require_real_topology_and_rights(self):
        for row in self.matrix["rows"]:
            if row["kind"]=="warp":
                self.assertIn("R07_TOPOLOGY",row["required_criteria_ids"])
                self.assertIn("R08_LICENSE",row["required_criteria_ids"])
                self.assertIn("R08_EVENTS",row["required_criteria_ids"])

    def test_08_Barry_and_starters_require_real_PBS(self):
        for row in self.matrix["rows"]:
            if row["kind"] in ("barry","starter"):
                self.assertIn("R08_PBS",row["required_criteria_ids"])

    def test_09_all_platforms_still_requires_independent_human_gate(self):
        r=self.report()
        self.assertTrue(r["review_handoff"]["separate_human_gate_for_future_native_QA_required"])
        self.assertTrue(r["review_handoff"]["L05_documentary_is_not_android_local_gate_L05"])
        for key in ("native_test_can_start","may_run_game_exe",
                    "may_run_joiplay","may_start_windows_sandbox",
                    "may_install_live_game","auto_uploaded","sinnoh_playable"):
            self.assertIs(r[key],False)

    def test_10_human_l04_is_not_accepted_even_if_JSON_consistent(self):
        self.assertEqual(self.l04_report["criteria_reviewed"],0)
        self.assertEqual(self.l04_report["human_evidence_independently_authenticated"],0)
        self.assertEqual(self.report()["criteria_human_approved"],0)

    def test_11_missing_case_fails_closed(self):
        self.rejected(lambda m,h,g,l,gg:m["rows"].pop())

    def test_12_duplicate_case_id_fails_closed(self):
        self.rejected(lambda m,h,g,l,gg:m["rows"][1].update(case_id=m["rows"][0]["case_id"]))

    def test_13_case_order_changed_fails_closed(self):
        self.rejected(lambda m,h,g,l,gg:m["rows"].reverse())

    def test_14_invented_case_id_rejected(self):
        self.rejected(lambda m,h,g,l,gg:m["rows"][0].update(case_id="warp-SN_FAKE_ID"))

    def test_15_change_case_kind_or_platform_rejected(self):
        self.rejected(lambda m,h,g,l,gg:m["rows"][0].update(kind="barry"))
        self.rejected(lambda m,h,g,l,gg:m["rows"][0].update(platform="android"))
        self.rejected(lambda m,h,g,l,gg:m["rows"][-1].update(platform="windows"))

    def test_16_native_status_forgery_in_L05_rejected(self):
        for state in ("passed","approved","native_playable"):
            self.rejected(lambda m,h,g,l,gg,s=state:m["rows"][0].update(native_status=s))

    def test_17_native_evidence_or_execution_forgery_rejected(self):
        for k in ("native_evidence_accepted","independent_criteria_satisfied",
                  "native_execution_authorized"):
            self.rejected(lambda m,h,g,l,gg,k=k:m["rows"][0].update({k:True}))

    def test_18_unknown_fields_private_paths_rejected(self):
        self.rejected(lambda m,h,g,l,gg:m["rows"][0].update(
            save_path="C:\\Users\\tester\\Save01.rxdata"))
        self.rejected(lambda m,h,g,l,gg:m.update(private_baseline="hmac_secret"))
        self.rejected(lambda m,h,g,l,gg:m["rows"][-1].update(
            screenshot="private_png_bytes"))

    def test_19_missing_criterion_link_rejected(self):
        self.rejected(lambda m,h,g,l,gg:m["rows"][0]["required_criteria_ids"].pop())
        self.rejected(lambda m,h,g,l,gg:m["rows"][-1]["required_criteria_ids"].pop())

    def test_20_reordered_or_duplicate_criterion_link_rejected(self):
        self.rejected(lambda m,h,g,l,gg:m["rows"][0]["required_criteria_ids"].reverse())
        self.rejected(lambda m,h,g,l,gg:m["rows"][0]["required_criteria_ids"].append("B09_ORIGIN"))

    def test_21_wrong_criterion_for_kind_rejected(self):
        self.rejected(lambda m,h,g,l,gg:m["rows"][-1]["required_criteria_ids"].append("B10_READONLY"))
        self.rejected(lambda m,h,g,l,gg:m["rows"][18]["required_criteria_ids"].append("R08_PBS"))

    def test_22_wrong_blocking_stages_rejected(self):
        self.rejected(lambda m,h,g,l,gg:m["rows"][0]["blocking_stages"].remove("B11"))
        self.rejected(lambda m,h,g,l,gg:m["rows"][0]["blocking_stages"].append("JOHTO"))
        self.rejected(lambda m,h,g,l,gg:m["rows"][-1]["blocking_stages"].append("B10"))

    def test_23_platform_gate_cannot_be_approved(self):
        self.rejected(lambda m,h,g,l,gg:m["rows"][0].update(platform_gate="WINDOWS_QA_APPROVED"))
        self.rejected(lambda m,h,g,l,gg:m["rows"][-1].update(platform_gate="JOIPLAY_TESTED"))

    def test_24_review_state_cannot_be_marked_completed(self):
        self.rejected(lambda m,h,g,l,gg:m["rows"][0].update(review_state="REVIEWED"))

    def test_25_top_level_stage_version_and_source_files_immutable(self):
        for k,v in (("schema",2),("region","KANTO"),("stage","L06"),
                    ("version",2),("status","NATIVE_READY"),
                    ("source_g12","private/results.json"),
                    ("source_l04","another/checklist.json")):
            with self.subTest(k=k):
                self.rejected(lambda m,h,g,l,gg,k=k,v=v:m.update({k:v}))

    def test_26_total_counts_and_phase_guards_immutable(self):
        for k,v in (("criteria_total",19),("criteria_reviewed",1),
                    ("native_cases_total",45),("windows_cases",44),
                    ("android_cases",2),("native_cases_approved",1),
                    ("native_cases_completed",True),("phase_b_approved",1),
                    ("phase_c_approved",True),("phase_d_approved",1)):
            with self.subTest(k=k):
                self.rejected(lambda m,h,g,l,gg,k=k,v=v:m.update({k:v}))

    def test_27_false_map_rights_or_runtime_flags_rejected(self):
        for k in l05.FALSE_FIELDS:
            with self.subTest(k=k):
                self.rejected(lambda m,h,g,l,gg,k=k:m.update({k:True}))

    def test_28_L04_criterion_list_drift_detected(self):
        self.rejected(lambda m,h,g,l,gg:h["rows"][0]["criteria"][0].update(id="B09_APPROVED"))
        self.rejected(lambda m,h,g,l,gg:m["expected_criteria_ids"].reverse())
        self.rejected(lambda m,h,g,l,gg:m["expected_criteria_ids"].append("EXTRA_FAKE"))

    def test_29_L04_false_human_signoff_detected(self):
        self.rejected(lambda m,h,g,l,gg:h["rows"][0]["criteria"][0].update(local_human_signoff=True))
        self.rejected(lambda m,h,g,l,gg:h["rows"][0]["criteria"][0].update(independent_evidence_present=True))

    def test_30_G12_case_forgery_detected(self):
        self.rejected(lambda m,h,g,l,gg:g["cases"][0].update(native_status="approved"))
        self.rejected(lambda m,h,g,l,gg:g["cases"][0].update(evidence="fake"))
        self.rejected(lambda m,h,g,l,gg:g["cases"][-1].update(platform="windows"))

    def test_31_G12_hand_off_completion_forgery_detected(self):
        self.rejected(lambda m,h,g,l,gg:g.update(completed_native_cases=1))
        self.rejected(lambda m,h,g,l,gg:g.update(can_launch_game_now=True))
        self.rejected(lambda m,h,g,l,gg:g.update(phase_b_approved=1))
        self.rejected(lambda m,h,g,l,gg:g.update(r07_complete=True))

    def test_32_G12_audited_native_evidence_forgery_rejected(self):
        self.rejected(lambda m,h,g,l,gg:gg["native_case_matrix"][0].update(status="passed"))
        self.rejected(lambda m,h,g,l,gg:gg["native_case_matrix"][0].update(evidence="fake"))
        self.rejected(lambda m,h,g,l,gg:gg.update(evidence_accepted_cases=1))

    def test_33_L04_auditor_false_native_review_rejected(self):
        self.rejected(lambda m,h,g,l,gg:l.update(criteria_reviewed=1))
        self.rejected(lambda m,h,g,l,gg:l.update(human_decisions_recorded=1))
        self.rejected(lambda m,h,g,l,gg:l.update(native_cases_approved=1))
        self.rejected(lambda m,h,g,l,gg:l["source_rows"][0].update(runtime_permission=True))

    def test_34_L04_source_missing_or_reordered_rejected(self):
        self.rejected(lambda m,h,g,l,gg:l["source_rows"].pop())
        self.rejected(lambda m,h,g,l,gg:l["source_rows"].reverse())
        self.rejected(lambda m,h,g,l,gg:l["source_rows"][0]["criteria"][0].update(state="APPROVED"))

    def test_35_all_cases_after_mutation_remain_not_executable(self):
        output=self.report()
        self.assertTrue(all(not x["human_physical_evidence_accepted"]
                            for x in output["cases"]))
        self.assertTrue(all(x["state"]=="NATIVE_QA_NOT_AUTHORIZED"
                            for x in output["cases"]))

    def test_36_private_values_not_echoed_in_report(self):
        text=json.dumps(self.report(),ensure_ascii=True)
        for forbidden in ("C:\\Users","Save01.rxdata","private-baseline.json",
                          "hmac_key","watch_id","source_clone_sha256","a"*64):
            self.assertNotIn(forbidden,text)

    def test_37_default_CLI_only_public_metadata(self):
        p=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_sinnoh_l05_native_dependencies.py")],
            cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(p.returncode,0,p.stderr)
        result=json.loads(p.stdout)
        self.assertEqual(result["status"],"DOCUMENTARY_MATRIX_VALID_NATIVE_44_ALL_PENDING")
        self.assertEqual((result["native_cases_total"],result["native_cases_approved"]),(44,0))
        self.assertEqual(result["criteria_human_approved"],0)

    def test_38_cli_does_not_echo_bad_path(self):
        private=r"C:\Users\tester\Save01.rxdata"
        p=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_sinnoh_l05_native_dependencies.py"),
            "--data",private],cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(p.returncode,2)
        self.assertNotIn(private,p.stdout+p.stderr)
        self.assertIn("SINNOH_L05_BLOCKED",p.stderr)

    def test_39_no_private_file_or_network_access_in_source(self):
        source=(ROOT/"scripts/regions/audit_sinnoh_l05_native_dependencies.py").read_text("utf8")
        for forbidden in ("import requests","import socket","import subprocess",
                          "os.system(","os.popen(","os.walk(","rglob(","shutil.copy",
                          "Game.exe').read_bytes","private-baseline.json\").read"):
            self.assertNotIn(forbidden,source)
        self.assertIn("l04.run(root,workspace=workspace)",source)

    def test_40_every_case_status_grounded_in_real_CH20_ID(self):
        self.assertEqual([x["id"] for x in self.report()["cases"]],
                         [x["id"] for x in self.g12_report["native_case_matrix"]])
        self.assertTrue(all(x["native_status"]=="pending" for x in self.handoff["cases"]))

if __name__=="__main__":
    unittest.main()
