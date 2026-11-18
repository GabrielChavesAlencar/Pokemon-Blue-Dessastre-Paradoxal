"""Sinnoh L07 public triage: strict source provenance, mirror parity, negative QA gates."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l07_public_triage as l07
l06 = l07.l06
l05 = l06.l05


class SinnohL07PublicTriageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read = l05.l04.l03.l02.l00.read_json
        cls.args = (
            read(ROOT, l07.SOURCE, maxsize=175000),
            read(ROOT, l07.MIRROR, maxsize=175000),
            read(ROOT, l06.MATRIX, maxsize=175000),
            read(ROOT, l05.MATRIX, maxsize=150000),
            read(ROOT, l05.l04.CHECKLIST, maxsize=65536),
            read(ROOT, l05.HANDOFF, maxsize=150000),
            l06.run(ROOT),
            l05.run(ROOT),
            l05.l04.run(ROOT),
            l05.G12.run(ROOT),
        )

    def report(self, mutate=None):
        args = [copy.deepcopy(x) for x in self.args]
        if mutate is not None:
            mutate(*args)
        return l07.audit(*args)

    def rejected(self, mutate):
        with self.assertRaises(ValueError):
            self.report(mutate)

    def test_01_strict_document_and_mirror(self):
        report = self.report()
        self.assertEqual(report["stage"], "L07")
        self.assertEqual(report["counts"], l07.COUNTS)
        self.assertEqual(report["gates"], l07.GATES)
        self.assertTrue(l06.same(self.args[0], self.args[1]))
        self.assertTrue(l06.same(self.args[0], l07.expected_document(self.args[2], self.args[4])))

    def test_02_exact_ids_and_source_order(self):
        report = self.report()
        self.assertEqual([x["id"] for x in report["cases"]],
                         [x["case_id"] for x in self.args[2]["rows"]])
        self.assertEqual(len({x["id"] for x in report["cases"]}), 44)
        self.assertEqual([x["id"] for x in report["criteria"]],
                         [c["id"] for r in self.args[4]["rows"] for c in r["criteria"]])

    def test_03_platform_partition_and_independent_gates(self):
        report = self.report()
        self.assertEqual([(x["platform"], x["count"]) for x in report["platform_queues"]],
                         [("windows", 43), ("android", 1)])
        self.assertEqual(report["platform_queues"][1]["case_ids"], ["android-joi-play"])
        self.assertTrue(all("B11" in x["blocked_by"] for x in report["cases"][:-1]))
        self.assertNotIn("B11", report["cases"][-1]["blocked_by"])
        self.assertTrue(report["windows_android_review_is_independent"])

    def test_04_criteria_coverage_and_counts(self):
        doc = self.args[0]
        self.assertEqual(len(doc["criteria"]), 20)
        for row in doc["criteria"]:
            cases = [c for c in doc["cases"] if row["id"] in c["required_criteria_ids"]]
            self.assertEqual(row["dependent_cases"], len(cases))
            self.assertEqual(row["windows_dependencies"], sum(x["platform"] == "windows" for x in cases))
            self.assertEqual(row["android_dependencies"], sum(x["platform"] == "android" for x in cases))
            self.assertFalse(row["physical_evidence_accepted"])
            self.assertFalse(row["human_signoff"])

    def test_05_only_documentary_actions_available(self):
        doc = self.args[0]
        self.assertEqual(doc["allowed_documentary_actions"], list(l06.ACTIONS))
        self.assertEqual(doc["current_action"], "KEEP_PENDING")
        for case in doc["cases"]:
            self.assertEqual(case["action"], "KEEP_PENDING")
            self.assertEqual(case["native_status"], "pending")
            self.assertFalse(case["evidence_accepted"])
            self.assertFalse(case["native_qa_authorized"])

    def test_06_no_native_or_playability_permission(self):
        r = self.report()
        self.assertFalse(r["native_qa_authorized"])
        self.assertFalse(r["sinnoh_playable"])
        self.assertFalse(r["physical_proof_accepted"])
        self.assertFalse(r["global_save_isolation_proven"])
        self.assertTrue(r["l07_is_not_android_g12_local_l05"])
        self.assertEqual((r["counts"]["local_reports"], r["counts"]["native_approved"],
                          r["counts"]["human_approved"], r["counts"]["phase_bcd_completed"]), (0,0,0,0))

    def test_07_public_payload_no_secrets(self):
        raw=json.dumps(self.report(),ensure_ascii=True)
        for private in ("Save01.rxdata", "private-baseline.json", "hmac_key",
                        "watch_id", "source_clone_sha256", "C:\\\\Users"):
            self.assertNotIn(private, raw)

    def test_08_cli_rejects_arbitrary_input_without_echo(self):
        cmd=[sys.executable, str(ROOT/"scripts/regions/audit_sinnoh_l07_public_triage.py")]
        p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout)["counts"]["cases_total"],44)
        deny=subprocess.run(cmd+["--path",r"C:\\Users\\tester\\Save01.rxdata"],
                            cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(deny.returncode,2)
        self.assertIn("SINNOH_L07_BLOCKED",deny.stderr)
        self.assertNotIn("Save01.rxdata",deny.stderr+deny.stdout)

    def test_09_read_only_static_dashboard_structure(self):
        html=(ROOT/"site/public/sinnoh-l07-triagem.html").read_text("utf8")
        js=(ROOT/"site/public/assets/sinnoh-l07-triage.js").read_text("utf8")
        for field in ('id="q"', 'id="platform"', 'id="kind"', 'id="criterion"', 'id="blocker"',
                      'id="cases"', 'id="criteria"', 'id="reset"'):
            self.assertIn(field, html)
        self.assertIn("/data/sinnoh-l07-public-triage.json", js)
        self.assertIn("document.createElement",js)
        self.assertIn("textContent",js)
        self.assertNotIn("innerHTML",js)
        self.assertNotIn("localStorage",js)
        self.assertNotIn("eval(",js)
        self.assertNotIn('method: "POST"',js)
        self.assertNotIn("FormData",js)

    def test_10_auditor_no_host_access_or_upload(self):
        src=(ROOT/"scripts/regions/audit_sinnoh_l07_public_triage.py").read_text("utf8")
        for forbidden in ("import subprocess","import requests","import socket","os.walk(",
                          "rglob(","os.system(","shutil.copy(","subprocess.run(",
                          "from urllib","httpx","upload_file("):
            self.assertNotIn(forbidden,src)

    def test_negative_01_drop_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"].pop())

    def test_negative_02_duplicate_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"].append(copy.deepcopy(a["cases"][0])))

    def test_negative_03_reverse_cases(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"].reverse())

    def test_negative_04_invent_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0].update(id="ball-FAKE"))

    def test_negative_05_duplicate_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][1].update(id=a["cases"][0]["id"]))

    def test_negative_06_wrong_kind(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0].update(kind="barry"))

    def test_negative_07_wrong_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0].update(platform="android"))

    def test_negative_08_android_windows(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][-1].update(platform="windows"))

    def test_negative_09_missing_criterion(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0]["required_criteria_ids"].pop())

    def test_negative_10_reordered_criteria(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0]["required_criteria_ids"].reverse())

    def test_negative_11_fake_criterion(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0]["required_criteria_ids"].append("R07_FAKE"))

    def test_negative_12_removed_b10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0]["blocked_by"].remove("B10"))

    def test_negative_13_removed_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0]["blocked_by"].remove("B11"))

    def test_negative_14_android_b10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][-1]["blocked_by"].append("B10"))

    def test_negative_15_android_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][-1]["blocked_by"].append("B11"))

    def test_negative_16_fake_queue(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][-1].update(review_queue="WINDOWS_HOST_DOCUMENTARY_REVIEW"))

    def test_negative_17_fake_gate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0].update(future_native_gate="WINDOWS_APPROVED"))

    def test_negative_18_fake_document_code(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0]["documentary_check_codes"].append("RUN_GAME"))

    def test_negative_19_evidence_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0].update(evidence_accepted=True))

    def test_negative_20_case_runtime_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0].update(native_qa_authorized=True))

    def test_negative_21_case_action_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0].update(action="APPROVED"))

    def test_negative_22_case_reviewed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0].update(review_state="REVIEWED"))

    def test_negative_23_case_passed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0].update(native_status="passed"))

    def test_negative_24_case_secret(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["cases"][0].update(save_path="Save01.rxdata"))

    def test_negative_25_missing_criteria_row(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["criteria"].pop())

    def test_negative_26_duplicate_criteria_row(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["criteria"].append(copy.deepcopy(a["criteria"][0])))

    def test_negative_27_reverse_criteria(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["criteria"].reverse())

    def test_negative_28_criterion_id_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["criteria"][0].update(id="B09_FAKE"))

    def test_negative_29_criterion_signoff_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["criteria"][0].update(human_signoff=True))

    def test_negative_30_criterion_physical_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["criteria"][0].update(physical_evidence_accepted=True))

    def test_negative_31_criterion_state_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["criteria"][0].update(status="APPROVED"))

    def test_negative_32_criterion_windows_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["criteria"][0].update(windows_dependencies=44))

    def test_negative_33_criterion_android_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["criteria"][0].update(android_dependencies=43))

    def test_negative_34_criterion_total_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["criteria"][0].update(dependent_cases=0))

    def test_negative_35_criterion_requirement_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["criteria"][0].update(requirement="ALL APPROVED"))

    def test_negative_36_queue_windows_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["platform_queues"][0].update(approved=True))

    def test_negative_37_queue_android_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["platform_queues"][1].update(approved=True))

    def test_negative_38_queue_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["platform_queues"][1].update(count=2))

    def test_negative_39_queue_cases_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["platform_queues"][0]["case_ids"].pop())

    def test_negative_40_queue_cases_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["platform_queues"][0]["case_ids"].__setitem__(1,a["platform_queues"][0]["case_ids"][0]))

    def test_negative_41_queue_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["platform_queues"].reverse())

    def test_negative_42_queue_android_native_gate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["platform_queues"][1].update(native_gate="ANDROID_TESTED"))

    def test_negative_43_queue_windows_native_gate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["platform_queues"][0].update(native_gate="WINDOWS_TESTED"))

    def test_negative_44_mirror_case_tamper(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: b["cases"][0].update(kind="android"))

    def test_negative_45_mirror_approval(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: b["gates"].update(r08="APPROVED"))

    def test_negative_46_mirror_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: b["cases"].pop())

    def test_negative_47_top_schema(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a.update(schema=2))

    def test_negative_48_top_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a.update(stage="L08"))

    def test_negative_49_top_version(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a.update(version=2))

    def test_negative_50_top_region(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a.update(region="UNOVA"))

    def test_negative_51_top_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a.update(status="GAMEPLAY_READY"))

    def test_negative_52_top_source_l06(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a.update(source_l06="../private.json"))

    def test_negative_53_top_source_l04(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a.update(source_l04="fake.json"))

    def test_negative_54_action_injected(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["allowed_documentary_actions"].append("RUN_SANDBOX"))

    def test_negative_55_action_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a.update(current_action="APPROVE"))

    def test_negative_56_local_reports_claim(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["counts"].update(local_reports=5))

    def test_negative_57_criteria_approved_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["counts"].update(human_approved=1))

    def test_negative_58_native_completed_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["counts"].update(native_completed=1))

    def test_negative_59_native_approved_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["counts"].update(native_approved=1))

    def test_negative_60_phase_bcd_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["counts"].update(phase_bcd_completed=13))

    def test_negative_61_phase_bcd_total(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["counts"].update(phase_bcd_total=12))

    def test_negative_62_r07_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(r07="APPROVED"))

    def test_negative_63_r08_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(r08="APPROVED"))

    def test_negative_64_r09_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(r09="APPROVED"))

    def test_negative_65_b11_global_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(b11_global_save_isolation_proven=True))

    def test_negative_66_mapids_reserved_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(mapids_reserved=True))

    def test_negative_67_rights_approved_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(asset_rights_approved=True))

    def test_negative_68_sandbox_executed_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(windows_sandbox_executed=True))

    def test_negative_69_joiplay_executed_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(joiplay_tested=True))

    def test_negative_70_phase_b(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(phase_b_approved=1))

    def test_negative_71_phase_c(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(phase_c_approved=1))

    def test_negative_72_phase_d(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(phase_d_approved=1))

    def test_negative_73_playable_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(sinnoh_playable=True))

    def test_negative_74_game_allowed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(can_launch_game_exe=True))

    def test_negative_75_joiplay_allowed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(can_launch_joiplay=True))

    def test_negative_76_sandbox_allowed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(can_start_windows_sandbox=True))

    def test_negative_77_installer_allowed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(can_install_live_game=True))

    def test_negative_78_auto_upload(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["gates"].update(auto_upload=True))

    def test_negative_79_unexpected_secret(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a.update(hmac_key="secret"))

    def test_negative_80_bool_int_counter(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: a["counts"].update(native_approved=False))

    def test_negative_81_upstream_l06_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: c["rows"][0].update(native_qa_authorized=True))

    def test_negative_82_upstream_l05_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: d.update(asset_rights_approved=True))

    def test_negative_83_upstream_l04_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: e["rows"][0]["criteria"][0].update(local_human_signoff=True))

    def test_negative_84_upstream_g12_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: f["cases"][0].update(native_status="passed"))

    def test_negative_85_upstream_l06_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: g.update(native_cases_approved=1))

    def test_negative_86_upstream_l05_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: h.update(native_cases_approved=1))

    def test_negative_87_upstream_l04_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: i.update(criteria_reviewed=1))

    def test_negative_88_upstream_g12_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j: j.update(evidence_accepted_cases=1))

if __name__ == "__main__":
    unittest.main()
