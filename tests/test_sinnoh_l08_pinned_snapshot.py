"""Sinnoh L08: pinned Git blobs, 44-case/20-criterion semantic drift, negative gates."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts/regions"))
import audit_sinnoh_l08_pinned_snapshot as l08
l07 = l08.l07
l06 = l07.l06
l05 = l06.l05

class SinnohL08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read = l05.l04.l03.l02.l00.read_json
        cls.docs = {stage: read(ROOT, path, maxsize=175000)
                    for stage,path,sha in l08.PINNED}
        cls.args = (
            read(ROOT,l08.SNAPSHOT,maxsize=125000),
            read(ROOT,l08.DIFF,maxsize=16000),
            cls.docs["G12"], cls.docs["L04"], cls.docs["L05"],
            cls.docs["L06"], cls.docs["L07"], cls.docs["L07_SITE"],
            l07.run(ROOT), l06.run(ROOT), l05.run(ROOT),
            l05.l04.run(ROOT), l05.G12.run(ROOT),
        )

    def audited(self, mutation=None):
        values=[copy.deepcopy(x) for x in self.args]
        if mutation is not None:
            mutation(*values)
        return l08.audit(*values)

    def rejected(self, mutation):
        with self.assertRaises(ValueError):
            self.audited(mutation)

    def test_01_baseline_pinned_blob_integrity(self):
        self.assertTrue(l08.check_pinned_blobs(ROOT))
        report=self.audited()
        self.assertEqual(report["baseline_commit"],l08.ANCHOR)
        self.assertEqual(report["source_public_git_blobs_checked"],6)
        self.assertEqual(report["public_semantic_comparisons"],5)

    def test_02_exact_case_and_criterion_sets(self):
        result=self.audited()
        self.assertEqual(len(result["case_ids"]),44)
        self.assertEqual(len(set(result["case_ids"])),44)
        self.assertEqual(len(result["criterion_ids"]),20)
        self.assertEqual(len(set(result["criterion_ids"])),20)
        self.assertEqual(result["case_ids"],[x["id"] for x in self.docs["G12"]["cases"]])
        self.assertEqual(result["criterion_ids"],[x["id"] for r in self.docs["L04"]["rows"] for x in r["criteria"]])

    def test_03_semantic_diffs_are_recomputed_not_trusted(self):
        result=l08.expected_diff(self.docs["G12"],self.docs["L04"],self.docs["L05"],
                                 self.docs["L06"],self.docs["L07"],self.args[0])
        self.assertTrue(l06.same(result,self.args[1]))
        self.assertEqual(result["counts"]["comparisons_checked"],5)
        self.assertEqual(result["counts"]["differences_found"],0)
        self.assertTrue(all(c["status"]=="NO_PUBLIC_DOCUMENTARY_DRIFT" for c in result["comparisons"]))
        self.assertEqual([x["checked"] for x in result["comparisons"]],[44,20,44,44,44])

    def test_04_platform_isolation(self):
        snap=self.args[0]
        self.assertEqual([(x["platform"],x["count"]) for x in snap["platform_queues"]],[("windows",43),("android",1)])
        self.assertEqual(snap["platform_queues"][1]["case_ids"],["android-joi-play"])
        self.assertNotIn("B11",snap["cases"][-1]["blocked_by"])
        self.assertNotIn("B10",snap["cases"][-1]["blocked_by"])
        self.assertTrue(all("B11" in x["blocked_by"] and "B10" in x["blocked_by"] for x in snap["cases"][:-1]))

    def test_05_immutability_of_human_and_native_gates(self):
        result=self.audited()
        self.assertEqual(result["counts"]["native_completed"],0)
        self.assertEqual(result["counts"]["native_approved"],0)
        self.assertEqual(result["counts"]["human_approved"],0)
        self.assertEqual(result["counts"]["local_reports"],0)
        self.assertEqual(result["counts"]["phase_bcd_completed"],0)
        for field in ("human_evidence_approved","can_run_windows_sandbox",
                      "can_run_game_exe","can_run_joiplay","can_install_region",
                      "b11_global_save_isolation_proven","r07_mapids_reserved",
                      "r08_asset_rights_approved","r09_complete",
                      "sinnoh_playable","android_local_l05_completed"):
            self.assertIs(result[field],False)

    def test_06_only_safe_public_projection_no_private_fields(self):
        data=json.dumps(self.audited(),ensure_ascii=True)
        for value in ("Save01.rxdata","private-baseline.json","watch_id",
                      "hmac_key","raw_save_path","source_clone_sha256"):
            self.assertNotIn(value,data)
        self.assertEqual(set(self.args[0]["cases"][0]),set(l08.CASE_KEYS))
        self.assertEqual(set(self.args[0]["criteria"][0]),set(l08.CRITERION_KEYS))

    def test_07_git_blob_hash_rejects_changed_public_file_offline(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-l08-synthetic-") as td:
            temp=Path(td)
            for _stage,relative,_sha in l08.PINNED:
                target=temp/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/relative,target)
            self.assertTrue(l08.check_pinned_blobs(temp))
            changed=temp/l08.PINNED[0][1]
            changed.write_bytes(changed.read_bytes()+b" ")
            with self.assertRaises(ValueError):
                l08.check_pinned_blobs(temp)

    def test_08_cli_no_user_paths_or_native_execution(self):
        command=[sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l08_pinned_snapshot.py")]
        ok=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(ok.returncode,0,ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["status"],"PUBLIC_PINNED_SNAPSHOT_VALID_ZERO_DRIFT_NATIVE_PENDING")
        blocked=subprocess.run(command+["--save",r"C:\\Users\\tester\\Save01.rxdata"],
                               cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(blocked.returncode,2)
        self.assertIn("SINNOH_L08_BLOCKED",blocked.stderr)
        self.assertNotIn("Save01.rxdata",blocked.stderr+blocked.stdout)

    def test_09_source_code_has_no_runtime_or_network_calls(self):
        content=(ROOT/"scripts/regions/audit_sinnoh_l08_pinned_snapshot.py").read_text("utf8")
        for forbidden in ("import subprocess","import requests","import socket","os.walk(",
                          "rglob(","os.system(","shutil.copy(","subprocess.run(","urllib",
                          "os.environ","eval(","httpx"):
            self.assertNotIn(forbidden,content)

    def test_10_drift_helper_detects_synthetic_differences(self):
        left=[{"id":"A","kind":"starter"},{"id":"B","kind":"barry"}]
        right=[{"id":"B","kind":"barry"},{"id":"A","kind":"warp"}]
        d=l08.compare_rows(left,right,("id","kind"))
        self.assertTrue(d["reordered_ids"])
        self.assertIn("A",d["modified_ids"])
        self.assertFalse(d["added_ids"])
        self.assertFalse(d["missing_ids"])

    def test_negative_01_snapshot_case_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"].pop())

    def test_negative_02_snapshot_case_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"].append(copy.deepcopy(a["cases"][0])))

    def test_negative_03_snapshot_case_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"].reverse())

    def test_negative_04_snapshot_case_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0].update(id="ball-FAKE"))

    def test_negative_05_snapshot_case_kind(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0].update(kind="warp"))

    def test_negative_06_snapshot_windows_to_android(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0].update(platform="android"))

    def test_negative_07_snapshot_android_to_windows(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][-1].update(platform="windows"))

    def test_negative_08_snapshot_criteria_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0]["required_criteria_ids"].pop())

    def test_negative_09_snapshot_criteria_extra(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0]["required_criteria_ids"].append("R07_FAKE"))

    def test_negative_10_snapshot_criteria_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0]["required_criteria_ids"].reverse())

    def test_negative_11_snapshot_blocker_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0]["blocked_by"].remove("B10"))

    def test_negative_12_snapshot_android_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][-1]["blocked_by"].append("B11"))

    def test_negative_13_snapshot_future_gate_passed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0].update(future_native_gate="WINDOWS_QA_APPROVED"))

    def test_negative_14_snapshot_review_state_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0].update(review_state="APPROVED"))

    def test_negative_15_snapshot_native_status_passed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0].update(native_status="passed"))

    def test_negative_16_snapshot_evidence_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0].update(evidence_accepted=True))

    def test_negative_17_snapshot_qa_allowed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0].update(native_qa_authorized=True))

    def test_negative_18_snapshot_unexpected_save_path(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["cases"][0].update(save_path="Save01.rxdata"))

    def test_negative_19_snapshot_criteria_row_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["criteria"].pop())

    def test_negative_20_snapshot_criteria_row_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["criteria"].append(copy.deepcopy(a["criteria"][0])))

    def test_negative_21_snapshot_criteria_row_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["criteria"].reverse())

    def test_negative_22_snapshot_criterion_id_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["criteria"][0].update(id="B09_FAKE"))

    def test_negative_23_snapshot_criterion_status_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["criteria"][0].update(status="APPROVED"))

    def test_negative_24_snapshot_criterion_signoff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["criteria"][0].update(human_signoff=True))

    def test_negative_25_snapshot_criterion_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["criteria"][0].update(physical_evidence_accepted=True))

    def test_negative_26_snapshot_windows_dep_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["criteria"][0].update(windows_dependencies=0))

    def test_negative_27_snapshot_android_dep_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["criteria"][0].update(android_dependencies=2))

    def test_negative_28_snapshot_dep_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["criteria"][0].update(dependent_cases=45))

    def test_negative_29_snapshot_queue_counts(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["platform_queues"][0].update(count=44))

    def test_negative_30_snapshot_queue_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["platform_queues"][0].update(approved=True))

    def test_negative_31_snapshot_android_queue_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["platform_queues"][1].update(approved=True))

    def test_negative_32_snapshot_queue_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["platform_queues"].reverse())

    def test_negative_33_snapshot_queue_missing_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["platform_queues"][0]["case_ids"].pop())

    def test_negative_34_snapshot_queue_android_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["platform_queues"][1]["case_ids"].__setitem__(0,"ball-TURTWIG"))

    def test_negative_35_snapshot_ignored_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(b11_global_save_isolation_proven=True))

    def test_negative_36_snapshot_r07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(r07="APPROVED"))

    def test_negative_37_snapshot_r08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(r08="APPROVED"))

    def test_negative_38_snapshot_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(r09="APPROVED"))

    def test_negative_39_snapshot_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(asset_rights_approved=True))

    def test_negative_40_snapshot_mapids(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(mapids_reserved=True))

    def test_negative_41_snapshot_sandbox(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(windows_sandbox_executed=True))

    def test_negative_42_snapshot_joiplay(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(joiplay_tested=True))

    def test_negative_43_snapshot_phase_b(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(phase_b_approved=1))

    def test_negative_44_snapshot_phase_c(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(phase_c_approved=1))

    def test_negative_45_snapshot_phase_d(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(phase_d_approved=1))

    def test_negative_46_snapshot_game(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(can_launch_game_exe=True))

    def test_negative_47_snapshot_joiplay_allowed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(can_launch_joiplay=True))

    def test_negative_48_snapshot_sandbox_allowed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(can_start_windows_sandbox=True))

    def test_negative_49_snapshot_installer_allowed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(can_install_live_game=True))

    def test_negative_50_snapshot_playability(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(sinnoh_playable=True))

    def test_negative_51_snapshot_upload(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["gates"].update(auto_upload=True))

    def test_negative_52_snapshot_native_completed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["counts"].update(native_completed=1))

    def test_negative_53_snapshot_native_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["counts"].update(native_approved=1))

    def test_negative_54_snapshot_humans_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["counts"].update(human_approved=1))

    def test_negative_55_snapshot_reports(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["counts"].update(local_reports=5))

    def test_negative_56_snapshot_bcd(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["counts"].update(phase_bcd_completed=13))

    def test_negative_57_snapshot_case_total(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["counts"].update(cases_total=45))

    def test_negative_58_snapshot_anchor(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a.update(baseline_commit="0"*40))

    def test_negative_59_snapshot_blob_sha(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["sources"][0].update(blob_sha="0"*40))

    def test_negative_60_snapshot_blob_path(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["sources"][0].update(path="private/save.json"))

    def test_negative_61_snapshot_blob_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["sources"].reverse())

    def test_negative_62_snapshot_source_added(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a["sources"].append(copy.deepcopy(a["sources"][0])))

    def test_negative_63_snapshot_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a.update(stage="L09"))

    def test_negative_64_snapshot_version(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a.update(version=2))

    def test_negative_65_snapshot_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a.update(status="NATIVE_APPROVED"))

    def test_negative_66_snapshot_physical(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a.update(physical_evidence_accepted=True))

    def test_negative_67_snapshot_human(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a.update(human_approval_issued=True))

    def test_negative_68_snapshot_native_qa(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a.update(native_qa_authorized=True))

    def test_negative_69_snapshot_android_l05(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a.update(android_local_l05_completed=True))

    def test_negative_70_snapshot_hmac(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: a.update(hmac_key="secret"))

    def test_negative_71_diff_missing_comparison(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b["comparisons"].pop())

    def test_negative_72_diff_extra_comparison(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b["comparisons"].append(copy.deepcopy(b["comparisons"][0])))

    def test_negative_73_diff_comparisons_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b["comparisons"].reverse())

    def test_negative_74_diff_fake_change(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b["comparisons"][0]["added_ids"].append("FAKE"))

    def test_negative_75_diff_false_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b["comparisons"][0]["missing_ids"].append("ball-TURTWIG"))

    def test_negative_76_diff_reordered(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b["comparisons"][1]["reordered_ids"].append("B09_CLONE"))

    def test_negative_77_diff_modified(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b["comparisons"][2]["modified_ids"].append("ball-TURTWIG"))

    def test_negative_78_diff_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b["comparisons"][0].update(status="APPROVED"))

    def test_negative_79_diff_checked(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b["comparisons"][1].update(checked=44))

    def test_negative_80_diff_bad_scope(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b["comparisons"][1].update(scope="native_execution"))

    def test_negative_81_diff_bad_baseline(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b.update(baseline_commit="f"*40))

    def test_negative_82_diff_forged_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b["counts"].update(differences_found=1))

    def test_negative_83_diff_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b.update(can_authorize_qa=True))

    def test_negative_84_diff_playability(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b.update(sinnoh_playable=True))

    def test_negative_85_diff_private(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b.update(private_evidence_read=True))

    def test_negative_86_diff_raw_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: b.update(raw_save_file="Save01.rxdata"))

    def test_negative_87_g12_status_mutated(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: c["cases"][0].update(native_status="passed"))

    def test_negative_88_g12_platform_mutated(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: c["cases"][-1].update(platform="windows"))

    def test_negative_89_l04_signoff_mutated(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: d["rows"][0]["criteria"][0].update(local_human_signoff=True))

    def test_negative_90_l04_id_mutated(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: d["rows"][0]["criteria"][0].update(id="B09_FAKE"))

    def test_negative_91_l05_mapid_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: e.update(mapids_reserved=True))

    def test_negative_92_l05_platform_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: e["rows"][-1].update(platform="windows"))

    def test_negative_93_l06_session_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: f.update(global_save_isolation_proven=True))

    def test_negative_94_l06_rights_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: f.update(asset_rights_approved=True))

    def test_negative_95_l07_gate_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: g["gates"].update(r08="APPROVED"))

    def test_negative_96_l07_case_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: g["cases"][0].update(native_qa_authorized=True))

    def test_negative_97_l07_mirror_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: h["cases"][0].update(id="ball-FAKE"))

    def test_negative_98_l07_report_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: i["counts"].update(native_approved=1))

    def test_negative_99_l06_report_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: j.update(native_cases_approved=1))

    def test_negative_100_l05_report_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: k.update(native_cases_approved=1))

    def test_negative_101_l04_report_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: l.update(criteria_reviewed=1))

    def test_negative_102_g12_report_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m: m.update(evidence_accepted_cases=1))

if __name__=="__main__":
    unittest.main()
