"""L18: 88 public-only review gaps, strictly blocked and synthetic negative tests."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_l18_review_gaps as l18
l17=l18.l17

class SinnohL18ReviewGapsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read=l17.l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
        cls.parts=[
            read(ROOT,l18.REPORT,maxsize=205000),
            read(ROOT,l18.MIRROR,maxsize=205000),
            read(ROOT,l17.INDEX,maxsize=195000),
            read(ROOT,l17.MIRROR,maxsize=195000),
            read(ROOT,l17.l16.MATRIX,maxsize=185000),
            l17.l16.run(ROOT),
        ]

    def audited(self,mutation=None):
        p=[copy.deepcopy(x) for x in self.parts]
        if mutation: mutation(*p)
        return l18.audit(*p)

    def rejected(self,mutation):
        with self.assertRaises(ValueError):
            self.audited(mutation)

    def test_01_fixed_public_L17_git_blob_and_ancestry(self):
        self.assertTrue(l18.check_l17_blob(ROOT))
        report=self.audited()
        self.assertEqual(report["status"],"PUBLIC_REVIEW_GAPS_VALID_ALL_OPEN_NO_REAL_QA")
        self.assertEqual(report["baseline_commits"]["L17"],l18.L17_MERGE)
        self.assertEqual(report["public_sources"][-1],{
            "stage":"L17","path":l17.INDEX,"git_blob_sha1":l18.L17_BLOB})
        self.assertEqual(len(report["baseline_commits"]),11)

    def test_02_88_open_gaps_zero_progress(self):
        report=self.audited()
        self.assertEqual((report["requests"],report["requests_blocked"],report["review_gaps_open"],
                          report["review_gaps_closed"],report["exit_criteria_met"]),(88,88,88,0,0))
        self.assertEqual(len(self.parts[0]["records"]),88)
        self.assertTrue(all(x["review_state"]=="NOT_REVIEWED"
            and x["review_gap_status"]=="OPEN_DOCUMENTARY_ONLY" and x["status"]=="PENDING"
            and x["readiness"]=="BLOCKED" for x in self.parts[0]["records"]))

    def test_03_exact_1084_metadata_links_18_anonymous(self):
        report=self.audited()
        self.assertEqual((report["links"],report["anonymous_slots"]),(1084,18))
        self.assertEqual((report["case_to_criterion_links"],report["case_to_blocker_links"],
                          report["criterion_to_blocker_links"]),(846,218,20))
        anon=[x for x in self.parts[0]["records"] if x["anonymous_bookkeeping_slot"]]
        self.assertEqual(len(anon),18)
        self.assertTrue(all(x["documentary_dependency_count"]==0
            and not x["documentary_dependency_request_ids"] for x in anon))

    def test_04_windows_and_android_separate(self):
        report=self.audited()
        self.assertEqual((report["windows_native_pending"],report["android_native_pending"]),(43,1))
        windows=[x for x in self.parts[0]["records"] if x["kind"]=="NATIVE_CASE" and x["platform"]=="windows"]
        android=[x for x in self.parts[0]["records"] if x["kind"]=="NATIVE_CASE" and x["platform"]=="android"]
        self.assertEqual(len(windows),43);self.assertEqual(len(android),1)
        self.assertTrue(all("B10" in x["prerequisite_blocker_ids"] and "B11" in x["prerequisite_blocker_ids"] for x in windows))
        self.assertTrue(all("B10" not in x["prerequisite_blocker_ids"] and "B11" not in x["prerequisite_blocker_ids"] for x in android))

    def test_05_r09_global_has_no_case_edges(self):
        d=self.parts[0]
        self.assertEqual(d["global_r09"]["case_ids"],[])
        self.assertEqual(d["global_r09"]["documentary_dependency_request_ids"],[])
        self.assertEqual(d["global_r09"]["gaps_open"],1)
        self.assertTrue(self.audited()["r09_global_only"])
        self.assertTrue(all("R09" not in x["prerequisite_blocker_ids"] for x in d["records"] if x["kind"]=="NATIVE_CASE"))

    def test_06_no_reports_reviews_native_tests_bcd_rights_mapids(self):
        report=self.audited()
        self.assertEqual((report["local_reports_received"],report["human_approved"],report["native_executed"],
            report["native_approved"],report["phase_bcd_approved"]),(0,0,0,0,0))
        self.assertEqual(report["phase_bcd_total"],13)
        self.assertTrue(report["r07_pending"] and report["r08_pending"] and report["r09_pending"])
        self.assertFalse(report["sinnoh_playable"])

    def test_07_derivation_from_only_L17(self):
        same=l17.l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.same
        expected=l18.expected_report(self.parts[2])
        self.assertTrue(same(self.parts[0],expected))
        self.assertTrue(same(self.parts[1],expected))

    def test_08_mutated_public_git_blob_rejected(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-l18-public-") as td:
            root=Path(td)
            for p in (l17.INDEX,l17.MIRROR):
                target=root/p;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/p,target)
            self.assertTrue(l18.check_l17_blob(root))
            target=root/l17.MIRROR
            target.write_bytes(target.read_bytes()+b" ")
            with self.assertRaises(ValueError):
                l18.check_l17_blob(root)

    def test_09_cli_only_accepts_fixed_public_inputs(self):
        cmd=[sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l18_review_gaps.py")]
        good=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(json.loads(good.stdout)["review_gaps_open"],88)
        bad=subprocess.run(cmd+["--save","C:/private/Save01.rxdata"],
           cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(bad.returncode,2)
        self.assertIn("SINNOH_L18_BLOCKED",bad.stderr)
        self.assertNotIn("Save01.rxdata",bad.stderr+bad.stdout)

    def test_10_no_native_io_network_or_private_file_discovery(self):
        source=(ROOT/"scripts/regions/audit_sinnoh_l18_review_gaps.py").read_text("utf8")
        for ban in ("import requests","import subprocess","import socket","os.walk(",
          "rglob(","os.system(","subprocess.run(","from urllib","httpx","os.environ"):
            self.assertNotIn(ban,source)
    def test_negative_001_remove_row(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"].pop())

    def test_negative_002_append_duplicate_row(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"].append(copy.deepcopy(a["records"][0])))

    def test_negative_003_reverse_row_order(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"].reverse())

    def test_negative_004_change_id(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(request_id="FAKE"))

    def test_negative_005_duplicate_id(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][1].update(request_id=a["records"][0]["request_id"]))

    def test_negative_006_row_number(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(order=9))

    def test_negative_007_subject_id(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(subject_id="FAKE"))

    def test_negative_008_kind_change(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(kind="NATIVE_CASE"))

    def test_negative_009_platform_change(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(platform="android"))

    def test_negative_010_priority_change(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(priority=3))

    def test_negative_011_priority_label(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(priority_label="NATIVE"))

    def test_negative_012_gap_type_removed(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0]["gap_types"].pop())

    def test_negative_013_gap_type_added(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0]["gap_types"].append("AUTHORIZED"))

    def test_negative_014_gap_type_reordered(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0]["gap_types"].reverse())

    def test_negative_015_gap_wrong(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0]["gap_types"][0]="AUTHORIZATION")

    def test_negative_016_next_step_qa(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][44].update(next_documentary_step="Execute Game.exe"))

    def test_negative_017_next_step_blank(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(next_documentary_step=""))

    def test_negative_018_criterion_added(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0]["exit_criteria_codes"].append("AUTHORIZED"))

    def test_negative_019_criterion_missing(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0]["exit_criteria_codes"].pop())

    def test_negative_020_blocker_added(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0]["prerequisite_blocker_ids"].append("R09"))

    def test_negative_021_blocker_removed(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0]["prerequisite_blocker_ids"].pop())

    def test_negative_022_human_extra(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][11]["linked_l04_criterion_ids"].append("FAKE"))

    def test_negative_023_human_removed(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][11]["linked_l04_criterion_ids"].pop())

    def test_negative_024_native_dependency_extra(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][-1]["documentary_dependency_request_ids"].append("L13-BLOCKER-B10"))

    def test_negative_025_native_dependency_removed(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][-1]["documentary_dependency_request_ids"].pop())

    def test_negative_026_native_link_count(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][-1].update(documentary_dependency_count=99))

    def test_negative_027_r09_native_gate(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][-1]["prerequisite_blocker_ids"].append("R09"))

    def test_negative_028_android_b10(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][-1]["prerequisite_blocker_ids"].append("B10"))

    def test_negative_029_android_b11(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][-1]["prerequisite_blocker_ids"].append("B11"))

    def test_negative_030_anonymous_unflag(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][6].update(anonymous_bookkeeping_slot=False))

    def test_negative_031_anonymous_add_link(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][6]["documentary_dependency_request_ids"].append("L13-BLOCKER-B09"))

    def test_negative_032_anonymous_add_human(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][6]["linked_l04_criterion_ids"].append("B09_ORIGIN"))

    def test_negative_033_review_state(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(review_state="APPROVED"))

    def test_negative_034_review_gap_closed(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(review_gap_status="CLOSED"))

    def test_negative_035_step_scope(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(next_step_scope="NATIVE_ALLOWED"))

    def test_negative_036_status_approved(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(status="APPROVED"))

    def test_negative_037_readiness(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(readiness="READY"))

    def test_negative_038_exit_met(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(exit_criteria_met=True))

    def test_negative_039_human_signoff(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(human_signoff=True))

    def test_negative_040_native_executed(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][-1].update(native_qa_executed=True))

    def test_negative_041_native_approved(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][-1].update(native_qa_approved=True))

    def test_negative_042_report_received(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][6].update(local_report_received=True))

    def test_negative_043_reviewer_named(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(assigned_reviewer=True))

    def test_negative_044_source_authentication(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(source_authenticated=True))

    def test_negative_045_private_path(self):
        self.rejected(lambda a,b,c,d,e,f: a["records"][0].update(private_path="private/Save01.rxdata"))

    def test_negative_046_group_reorder(self):
        self.rejected(lambda a,b,c,d,e,f: a["group_summary"].reverse())

    def test_negative_047_group_remove(self):
        self.rejected(lambda a,b,c,d,e,f: a["group_summary"].pop())

    def test_negative_048_group_count(self):
        self.rejected(lambda a,b,c,d,e,f: a["group_summary"][5].update(requests=45))

    def test_negative_049_group_ready(self):
        self.rejected(lambda a,b,c,d,e,f: a["group_summary"][5].update(ready=1))

    def test_negative_050_group_links(self):
        self.rejected(lambda a,b,c,d,e,f: a["group_summary"][5].update(documentary_links=1000))

    def test_negative_051_group_reviewed(self):
        self.rejected(lambda a,b,c,d,e,f: a["group_summary"][3].update(reviewed=20))

    def test_negative_052_group_accepted(self):
        self.rejected(lambda a,b,c,d,e,f: a["group_summary"][3].update(physical_evidence_accepted=1))

    def test_negative_053_group_status(self):
        self.rejected(lambda a,b,c,d,e,f: a["group_summary"][3].update(gap_status="CLOSED"))

    def test_negative_054_taxonomy_remove(self):
        self.rejected(lambda a,b,c,d,e,f: a["gap_templates"].pop())

    def test_negative_055_taxonomy_swap(self):
        self.rejected(lambda a,b,c,d,e,f: a["gap_templates"].reverse())

    def test_negative_056_taxonomy_kind(self):
        self.rejected(lambda a,b,c,d,e,f: a["gap_templates"][0].update(kind="FAKE"))

    def test_negative_057_taxonomy_gap_code(self):
        self.rejected(lambda a,b,c,d,e,f: a["gap_templates"][0]["gap_types"].append("DONE"))

    def test_negative_058_taxonomy_step(self):
        self.rejected(lambda a,b,c,d,e,f: a["gap_templates"][0].update(next_documentary_step="Execute nativo"))

    def test_negative_059_taxonomy_version(self):
        self.rejected(lambda a,b,c,d,e,f: a.update(gap_taxonomy_version=2))

    def test_negative_060_counts_total(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(gaps_total_requests=87))

    def test_negative_061_counts_open(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(review_gaps_open=87))

    def test_negative_062_counts_closed(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(review_gaps_closed=1))

    def test_negative_063_counts_steps(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(documentary_next_steps=87))

    def test_negative_064_counts_independent(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(independent_reviews_completed=1))

    def test_negative_065_counts_exit(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(exit_criteria_met=1))

    def test_negative_066_counts_physical(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(physical_evidence_accepted=1))

    def test_negative_067_counts_links(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(links_preserved=1083))

    def test_negative_068_counts_anonymous(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(unassigned_anonymous_slots=17))

    def test_negative_069_counts_local(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(local_reports=5))

    def test_negative_070_counts_human(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(human_approved=20))

    def test_negative_071_counts_native(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(native_completed=44))

    def test_negative_072_counts_bcd(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(phase_bcd_completed=13))

    def test_negative_073_counts_windows(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(windows_native_pending=44))

    def test_negative_074_counts_android(self):
        self.rejected(lambda a,b,c,d,e,f: a["counts"].update(android_native_pending=0))

    def test_negative_075_r07_approved(self):
        self.rejected(lambda a,b,c,d,e,f: a["gates"].update(r07="APPROVED"))

    def test_negative_076_r08_approved(self):
        self.rejected(lambda a,b,c,d,e,f: a["gates"].update(r08="APPROVED"))

    def test_negative_077_r09_approved(self):
        self.rejected(lambda a,b,c,d,e,f: a["gates"].update(r09="APPROVED"))

    def test_negative_078_r09_case(self):
        self.rejected(lambda a,b,c,d,e,f: a["global_r09"]["case_ids"].append("SINNOH_TEST"))

    def test_negative_079_r09_dependency(self):
        self.rejected(lambda a,b,c,d,e,f: a["global_r09"]["documentary_dependency_request_ids"].append("L13-NATIVE-SINNOH"))

    def test_negative_080_r09_review(self):
        self.rejected(lambda a,b,c,d,e,f: a["global_r09"].update(review_completed=True))

    def test_negative_081_r09_gap_zero(self):
        self.rejected(lambda a,b,c,d,e,f: a["global_r09"].update(gaps_open=0))

    def test_negative_082_r09_approval(self):
        self.rejected(lambda a,b,c,d,e,f: a["global_r09"].update(approval=True))

    def test_negative_083_r09_status(self):
        self.rejected(lambda a,b,c,d,e,f: a["global_r09"].update(gap_status="CLOSED"))

    def test_negative_084_android_inherits_b11(self):
        self.rejected(lambda a,b,c,d,e,f: a["platform_partition"][1].update(requires_windows_b10_b11=True))

    def test_negative_085_windows_b11_removed(self):
        self.rejected(lambda a,b,c,d,e,f: a["platform_partition"][0].update(requires_windows_b10_b11=False))

    def test_negative_086_native_authorization(self):
        self.rejected(lambda a,b,c,d,e,f: a["platform_partition"][1].update(native_authorization=True))

    def test_negative_087_platform_review(self):
        self.rejected(lambda a,b,c,d,e,f: a["platform_partition"][0].update(review_completed=True))

    def test_negative_088_platform_open_zero(self):
        self.rejected(lambda a,b,c,d,e,f: a["platform_partition"][0].update(gaps_open=0))

    def test_negative_089_platform_swap(self):
        self.rejected(lambda a,b,c,d,e,f: a["platform_partition"].reverse())

    def test_negative_090_policy_review(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(gaps_are_not_human_signoffs=False))

    def test_negative_091_policy_execution(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(next_steps_are_not_native_instructions=False))

    def test_negative_092_policy_global(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(no_new_case_links_to_r09=False))

    def test_negative_093_policy_anonymous(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(anonymous_slots_unassigned=False))

    def test_negative_094_policy_android(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(android_separate_from_windows_b10_b11=False))

    def test_negative_095_policy_rights(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(asset_rights_not_approved=False))

    def test_negative_096_policy_mapids(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(mapids_not_reserved=False))

    def test_negative_097_policy_isolation(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(watch_unchanged_not_global_save_isolation=False))

    def test_negative_098_policy_private(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(no_private_evidence_intake=False))

    def test_negative_099_policy_upload(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(no_uploads=False))

    def test_negative_100_policy_game(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(no_game_exe=False))

    def test_negative_101_policy_sandbox(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(no_windows_sandbox=False))

    def test_negative_102_policy_joiplay(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(no_joiplay=False))

    def test_negative_103_policy_playable(self):
        self.rejected(lambda a,b,c,d,e,f: a["policy"].update(sinnoh_playable=True))

    def test_negative_104_priority_rules(self):
        self.rejected(lambda a,b,c,d,e,f: a["priority_rules"].reverse())

    def test_negative_105_public_source_reorder(self):
        self.rejected(lambda a,b,c,d,e,f: a["public_sources"].reverse())

    def test_negative_106_public_source_sha(self):
        self.rejected(lambda a,b,c,d,e,f: a["public_sources"][4].update(git_blob_sha1="0"*40))

    def test_negative_107_public_source_path(self):
        self.rejected(lambda a,b,c,d,e,f: a["public_sources"][4].update(path="private/ROM.zip"))

    def test_negative_108_commit_l07(self):
        self.rejected(lambda a,b,c,d,e,f: a["baseline_commits"].update(L07="0"*40))

    def test_negative_109_commit_l08(self):
        self.rejected(lambda a,b,c,d,e,f: a["baseline_commits"].update(L08="0"*40))

    def test_negative_110_commit_l09(self):
        self.rejected(lambda a,b,c,d,e,f: a["baseline_commits"].update(L09="0"*40))

    def test_negative_111_commit_l10(self):
        self.rejected(lambda a,b,c,d,e,f: a["baseline_commits"].update(L10="0"*40))

    def test_negative_112_commit_l11(self):
        self.rejected(lambda a,b,c,d,e,f: a["baseline_commits"].update(L11="0"*40))

    def test_negative_113_commit_l12(self):
        self.rejected(lambda a,b,c,d,e,f: a["baseline_commits"].update(L12="0"*40))

    def test_negative_114_commit_l13(self):
        self.rejected(lambda a,b,c,d,e,f: a["baseline_commits"].update(L13="0"*40))

    def test_negative_115_commit_l14(self):
        self.rejected(lambda a,b,c,d,e,f: a["baseline_commits"].update(L14="0"*40))

    def test_negative_116_commit_l15(self):
        self.rejected(lambda a,b,c,d,e,f: a["baseline_commits"].update(L15="0"*40))

    def test_negative_117_commit_l16(self):
        self.rejected(lambda a,b,c,d,e,f: a["baseline_commits"].update(L16="0"*40))

    def test_negative_118_commit_l17(self):
        self.rejected(lambda a,b,c,d,e,f: a["baseline_commits"].update(L17="0"*40))

    def test_negative_119_schema(self):
        self.rejected(lambda a,b,c,d,e,f: a.update(schema=2))

    def test_negative_120_stage(self):
        self.rejected(lambda a,b,c,d,e,f: a.update(stage="L19"))

    def test_negative_121_status(self):
        self.rejected(lambda a,b,c,d,e,f: a.update(status="ALL_APPROVED"))

    def test_negative_122_mode(self):
        self.rejected(lambda a,b,c,d,e,f: a.update(mode="UPLOAD"))

    def test_negative_123_version(self):
        self.rejected(lambda a,b,c,d,e,f: a.update(version=2))

    def test_negative_124_mirror_approval(self):
        self.rejected(lambda a,b,c,d,e,f: b["records"][0].update(human_signoff=True))

    def test_negative_125_mirror_removed(self):
        self.rejected(lambda a,b,c,d,e,f: b["records"].pop())

    def test_negative_126_l17_review_forged(self):
        self.rejected(lambda a,b,c,d,e,f: c["records"][0].update(independent_signoff=True))

    def test_negative_127_l17_state_forged(self):
        self.rejected(lambda a,b,c,d,e,f: c["records"][0].update(review_state="APPROVED"))

    def test_negative_128_l17_platform_changed(self):
        self.rejected(lambda a,b,c,d,e,f: c["records"][-1].update(platform="windows"))

    def test_negative_129_l17_mirror_forged(self):
        self.rejected(lambda a,b,c,d,e,f: d["records"][-1].update(native_qa_authorized=True))

    def test_negative_130_l16_parent_r07(self):
        self.rejected(lambda a,b,c,d,e,f: f.update(r07_pending=False))

    def test_negative_131_l16_parent_native(self):
        self.rejected(lambda a,b,c,d,e,f: f.update(native_approved=44))

    def test_negative_132_l16_inmemory_approval(self):
        self.rejected(lambda a,b,c,d,e,f: e["records"][0].update(human_review_completed=True))

    def test_negative_133_l16_mirror_source(self):
        self.rejected(lambda a,b,c,d,e,f: e["records"].pop())

if __name__ == '__main__':
    unittest.main()
