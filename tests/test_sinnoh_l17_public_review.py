"""Sinnoh L17 public review guidance index: synthetic negatives and strict invariants."""
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
import audit_sinnoh_l17_public_review as l17
l16=l17.l16

class SinnohL17PublicReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read=l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
        cls.parts=[
            read(ROOT,l17.INDEX,maxsize=195000),
            read(ROOT,l17.MIRROR,maxsize=195000),
            read(ROOT,l16.MATRIX,maxsize=185000),
            l16.run(ROOT),
        ]

    def audited(self,mutation=None):
        data=[copy.deepcopy(x) for x in self.parts]
        if mutation: mutation(*data)
        return l17.audit(*data)

    def rejected(self,mutation):
        with self.assertRaises(ValueError):
            self.audited(mutation)

    def test_01_pinned_L16_blob(self):
        self.assertTrue(l17.check_l16_blob(ROOT))
        self.assertEqual(self.audited()["status"],"PUBLIC_REVIEW_GUIDANCE_VERIFIED_ALL_UNREVIEWED")

    def test_02_all_88_unreviewed_and_0_signoffs(self):
        x=self.audited()
        self.assertEqual((x["indexed_requests"],x["pending_blocked"],x["human_reviewed"],x["exit_criteria_met"]),(88,88,0,0))
        self.assertEqual(len(self.parts[0]["records"]),88)
        self.assertTrue(all(y["review_state"]=="NOT_REVIEWED" and y["status"]=="PENDING"
          and y["readiness"]=="BLOCKED" and not y["independent_signoff"]
          and not y["physical_evidence_accepted"] and not y["native_qa_authorized"]
          for y in self.parts[0]["records"]))

    def test_03_1084_public_links_18_unassigned(self):
        x=self.parts[0]
        self.assertEqual(sum(y["documentary_dependency_count"] for y in x["records"]),1084)
        anon=[y for y in x["records"] if y["anonymous_bookkeeping_slot"]]
        self.assertEqual(len(anon),18)
        self.assertTrue(all(not y["documentary_dependency_request_ids"]
          and not y["linked_l04_criterion_ids"] and not y["assigned_reviewer"]
          for y in anon))

    def test_04_r09_global_and_platform_separation(self):
        d=self.parts[0]
        self.assertEqual(d["global_r09"]["case_ids"],[])
        self.assertEqual(d["global_r09"]["documentary_dependency_request_ids"],[])
        self.assertFalse(d["global_r09"]["independent_review_complete"])
        native=[y for y in d["records"] if y["kind"]=="NATIVE_CASE"]
        self.assertEqual(len([y for y in native if y["platform"]=="windows"]),43)
        android=[y for y in native if y["platform"]=="android"]
        self.assertEqual(len(android),1)
        self.assertNotIn("B10",android[0]["prerequisite_blocker_ids"])
        self.assertNotIn("B11",android[0]["prerequisite_blocker_ids"])

    def test_05_public_ancestry_commits_and_blobs(self):
        report=self.audited()
        self.assertEqual(len(report["baseline_commits"]),10)
        self.assertEqual(report["baseline_commits"]["L16"],l17.L16_MERGE)
        self.assertEqual(report["public_sources"][-1],{
         "stage":"L16","path":l16.MATRIX,"git_blob_sha1":l17.L16_BLOB})
        self.assertEqual([x["stage"] for x in report["public_sources"]],["L13","L14","L15","L16"])

    def test_06_no_reports_human_or_native_execution(self):
        result=self.audited()
        self.assertEqual((result["local_reports_received"],result["human_approved"],
           result["native_executed"],result["native_approved"],result["phase_bcd_approved"]),(0,0,0,0,0))
        self.assertEqual(result["phase_bcd_total"],13)
        self.assertTrue(result["r07_pending"] and result["r08_pending"] and result["r09_pending"])
        self.assertTrue(result["no_private_uploads"] and result["no_native_authorization"])
        self.assertFalse(result["sinnoh_playable"])

    def test_07_derived_strictly_from_L16(self):
        same=l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.same
        expected=l17.expected_index(self.parts[2])
        self.assertTrue(same(self.parts[0],expected))
        self.assertTrue(same(self.parts[1],expected))

    def test_08_pinned_git_blob_mutation_fails(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-l17-public-") as td:
            root=Path(td)
            for path in [l16.MATRIX,l16.MIRROR]:
                dest=root/path
                dest.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/path,dest)
            self.assertTrue(l17.check_l16_blob(root))
            dest=root/l16.MIRROR
            dest.write_bytes(dest.read_bytes()+b" ")
            with self.assertRaises(ValueError):
                l17.check_l16_blob(root)

    def test_09_cli_no_private_paths_or_echo(self):
        cmd=[sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l17_public_review.py")]
        good=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(json.loads(good.stdout)["indexed_requests"],88)
        bad=subprocess.run(cmd+["--save","C:/private/Save01.rxdata"],
          cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(bad.returncode,2)
        self.assertIn("SINNOH_L17_BLOCKED",bad.stderr)
        self.assertNotIn("Save01.rxdata",bad.stderr+bad.stdout)

    def test_10_no_network_native_or_private_input_side_effects(self):
        source=(ROOT/"scripts/regions/audit_sinnoh_l17_public_review.py").read_text("utf8")
        for bad in ("import requests","import subprocess","import socket","os.walk(",
          "rglob(","os.system(","subprocess.run(","from urllib","httpx","os.environ"):
            self.assertNotIn(bad,source)

    def test_negative_001_missing_row(self):
        self.rejected(lambda a,b,c,d: a["records"].pop())

    def test_negative_002_duplicate_row(self):
        self.rejected(lambda a,b,c,d: a["records"].append(copy.deepcopy(a["records"][0])))

    def test_negative_003_reverse_rows(self):
        self.rejected(lambda a,b,c,d: a["records"].reverse())

    def test_negative_004_duplicate_id(self):
        self.rejected(lambda a,b,c,d: a["records"][1].update(request_id=a["records"][0]["request_id"]))

    def test_negative_005_fake_id(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(request_id="FAKE"))

    def test_negative_006_wrong_order(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(order=9))

    def test_negative_007_subject_changed(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(subject_id="R09"))

    def test_negative_008_kind_changed(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(kind="NATIVE_CASE"))

    def test_negative_009_platform_changed(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(platform="android"))

    def test_negative_010_priority_changed(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(priority=4))

    def test_negative_011_priority_label(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(priority_label="NATIVE"))

    def test_negative_012_wrong_exit_code(self):
        self.rejected(lambda a,b,c,d: a["records"][0]["exit_criteria_codes"].append("READY"))

    def test_negative_013_drop_exit_code(self):
        self.rejected(lambda a,b,c,d: a["records"][0]["exit_criteria_codes"].pop())

    def test_negative_014_wrong_blocker(self):
        self.rejected(lambda a,b,c,d: a["records"][0]["prerequisite_blocker_ids"].append("R09"))

    def test_negative_015_drop_blocker(self):
        self.rejected(lambda a,b,c,d: a["records"][0]["prerequisite_blocker_ids"].pop())

    def test_negative_016_add_human_criterion(self):
        self.rejected(lambda a,b,c,d: a["records"][11]["linked_l04_criterion_ids"].append("FAKE"))

    def test_negative_017_drop_human_criterion(self):
        self.rejected(lambda a,b,c,d: a["records"][11]["linked_l04_criterion_ids"].pop())

    def test_negative_018_r09_fake_human(self):
        self.rejected(lambda a,b,c,d: a["records"][5]["linked_l04_criterion_ids"].append("B09_ORIGIN"))

    def test_negative_019_r09_fake_case(self):
        self.rejected(lambda a,b,c,d: a["records"][5]["documentary_dependency_request_ids"].append("L13-HUMAN-R07_NATIVE"))

    def test_negative_020_r09_wrong_blocker(self):
        self.rejected(lambda a,b,c,d: a["records"][5]["prerequisite_blocker_ids"].append("B10"))

    def test_negative_021_android_windows_b10(self):
        self.rejected(lambda a,b,c,d: a["records"][-1]["prerequisite_blocker_ids"].append("B10"))

    def test_negative_022_android_windows_b11(self):
        self.rejected(lambda a,b,c,d: a["records"][-1]["prerequisite_blocker_ids"].append("B11"))

    def test_negative_023_android_windows_link(self):
        self.rejected(lambda a,b,c,d: a["records"][-1]["documentary_dependency_request_ids"].append("L13-BLOCKER-B11"))

    def test_negative_024_android_windows_platform(self):
        self.rejected(lambda a,b,c,d: a["records"][-1].update(platform="windows"))

    def test_negative_025_remove_document_link(self):
        self.rejected(lambda a,b,c,d: a["records"][-1]["documentary_dependency_request_ids"].pop())

    def test_negative_026_add_document_link(self):
        self.rejected(lambda a,b,c,d: a["records"][11]["documentary_dependency_request_ids"].append("L13-GLOBAL-R09"))

    def test_negative_027_wrong_link_total(self):
        self.rejected(lambda a,b,c,d: a["records"][-1].update(documentary_dependency_count=0))

    def test_negative_028_anonymous_false(self):
        self.rejected(lambda a,b,c,d: a["records"][6].update(anonymous_bookkeeping_slot=False))

    def test_negative_029_anonymous_extra_link(self):
        self.rejected(lambda a,b,c,d: a["records"][6]["documentary_dependency_request_ids"].append("L13-BLOCKER-B09"))

    def test_negative_030_anonymous_fake_criterion(self):
        self.rejected(lambda a,b,c,d: a["records"][6]["linked_l04_criterion_ids"].append("B09_ORIGIN"))

    def test_negative_031_anonymous_name(self):
        self.rejected(lambda a,b,c,d: a["records"][6].update(reviewer_name="Person X"))

    def test_negative_032_guidance_wrong(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(reviewer_guidance="Approved"))

    def test_negative_033_scope_wrong(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(review_scope="NATIVE_EXECUTION_ALLOWED"))

    def test_negative_034_review_completed(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(review_state="APPROVED"))

    def test_negative_035_status_passed(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(status="PASSED"))

    def test_negative_036_readiness_ready(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(readiness="READY"))

    def test_negative_037_exit_met(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(exit_criteria_met=True))

    def test_negative_038_independent_signoff(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(independent_signoff=True))

    def test_negative_039_physical_evidence(self):
        self.rejected(lambda a,b,c,d: a["records"][44].update(physical_evidence_accepted=True))

    def test_negative_040_native_authorized(self):
        self.rejected(lambda a,b,c,d: a["records"][-1].update(native_qa_authorized=True))

    def test_negative_041_assigned_reviewer(self):
        self.rejected(lambda a,b,c,d: a["records"][11].update(assigned_reviewer=True))

    def test_negative_042_private_ref(self):
        self.rejected(lambda a,b,c,d: a["records"][44].update(private_document_reference=True))

    def test_negative_043_private_path(self):
        self.rejected(lambda a,b,c,d: a["records"][0].update(file_path="C:/private/save.rxdata"))

    def test_negative_044_reviewer_guidance_template_missing(self):
        self.rejected(lambda a,b,c,d: a["review_guidance_templates"].pop())

    def test_negative_045_reviewer_guidance_template_reorder(self):
        self.rejected(lambda a,b,c,d: a["review_guidance_templates"].reverse())

    def test_negative_046_reviewer_guidance_template_kind(self):
        self.rejected(lambda a,b,c,d: a["review_guidance_templates"][0].update(kind="EXTERNAL"))

    def test_negative_047_reviewer_guidance_template_approve(self):
        self.rejected(lambda a,b,c,d: a["review_guidance_templates"][0].update(guidance="approved"))

    def test_negative_048_version_changed(self):
        self.rejected(lambda a,b,c,d: a.update(review_guidance_version=2))

    def test_negative_049_group_removed(self):
        self.rejected(lambda a,b,c,d: a["group_summary"].pop())

    def test_negative_050_group_reorder(self):
        self.rejected(lambda a,b,c,d: a["group_summary"].reverse())

    def test_negative_051_group_count(self):
        self.rejected(lambda a,b,c,d: a["group_summary"][0].update(requests=4))

    def test_negative_052_group_blocked(self):
        self.rejected(lambda a,b,c,d: a["group_summary"][0].update(blocked=4))

    def test_negative_053_group_links(self):
        self.rejected(lambda a,b,c,d: a["group_summary"][-1].update(documentary_links=999))

    def test_negative_054_group_reviewed(self):
        self.rejected(lambda a,b,c,d: a["group_summary"][3].update(independent_reviews_completed=20))

    def test_negative_055_group_evidence(self):
        self.rejected(lambda a,b,c,d: a["group_summary"][5].update(physical_evidence_accepted=1))

    def test_negative_056_group_approved(self):
        self.rejected(lambda a,b,c,d: a["group_summary"][3].update(review_state="APPROVED"))

    def test_negative_057_count_indexed(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(indexed_requests=87))

    def test_negative_058_count_pending(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(requests_pending=87))

    def test_negative_059_count_blocked(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(requests_blocked=87))

    def test_negative_060_count_reviewed(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(reviews_completed=1))

    def test_negative_061_count_signoffs(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(physical_signoffs=1))

    def test_negative_062_count_exit(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(exit_criteria_fulfilled=1))

    def test_negative_063_count_anonymous(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(anonymous_slots_unassigned=17))

    def test_negative_064_count_links(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(review_index_documentary_links=1083))

    def test_negative_065_count_windows(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(windows_native_pending=44))

    def test_negative_066_count_android(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(android_native_pending=0))

    def test_negative_067_count_native(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(native_approved=44))

    def test_negative_068_count_human(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(human_approved=20))

    def test_negative_069_count_local(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(local_reports=5))

    def test_negative_070_count_bcd(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(phase_bcd_completed=13))

    def test_negative_071_count_real_evidence(self):
        self.rejected(lambda a,b,c,d: a["counts"].update(actual_evidence_received=1))

    def test_negative_072_global_R09_case(self):
        self.rejected(lambda a,b,c,d: a["global_r09"]["case_ids"].append("ball-TURTWIG"))

    def test_negative_073_global_R09_link(self):
        self.rejected(lambda a,b,c,d: a["global_r09"]["documentary_dependency_request_ids"].append("L13-BLOCKER-B09"))

    def test_negative_074_global_R09_status(self):
        self.rejected(lambda a,b,c,d: a["global_r09"].update(status="APPROVED"))

    def test_negative_075_global_R09_review(self):
        self.rejected(lambda a,b,c,d: a["global_r09"].update(independent_review_complete=True))

    def test_negative_076_global_R09_approval(self):
        self.rejected(lambda a,b,c,d: a["global_r09"].update(approval=True))

    def test_negative_077_global_R09_scoped(self):
        self.rejected(lambda a,b,c,d: a["global_r09"].update(global_gate_only=False))

    def test_negative_078_windows_authorized(self):
        self.rejected(lambda a,b,c,d: a["platform_partition"][0].update(native_authorization=True))

    def test_negative_079_android_authorized(self):
        self.rejected(lambda a,b,c,d: a["platform_partition"][1].update(native_authorization=True))

    def test_negative_080_windows_reviewed(self):
        self.rejected(lambda a,b,c,d: a["platform_partition"][0].update(independent_review_complete=True))

    def test_negative_081_android_reviewed(self):
        self.rejected(lambda a,b,c,d: a["platform_partition"][1].update(independent_review_complete=True))

    def test_negative_082_android_B10(self):
        self.rejected(lambda a,b,c,d: a["platform_partition"][1].update(requires_windows_b10_b11=True))

    def test_negative_083_windows_B10_missing(self):
        self.rejected(lambda a,b,c,d: a["platform_partition"][0].update(requires_windows_b10_b11=False))

    def test_negative_084_platform_reversed(self):
        self.rejected(lambda a,b,c,d: a["platform_partition"].reverse())

    def test_negative_085_policy_review(self):
        self.rejected(lambda a,b,c,d: a["policy"].update(independent_review_not_performed=False))

    def test_negative_086_policy_signoff(self):
        self.rejected(lambda a,b,c,d: a["policy"].update(review_guidance_is_not_signoff=False))

    def test_negative_087_policy_private(self):
        self.rejected(lambda a,b,c,d: a["policy"].update(no_private_uploads=False))

    def test_negative_088_policy_upload(self):
        self.rejected(lambda a,b,c,d: a["policy"].update(no_evidence_intake=False))

    def test_negative_089_policy_joiplay(self):
        self.rejected(lambda a,b,c,d: a["policy"].update(no_joiplay=False))

    def test_negative_090_policy_windows(self):
        self.rejected(lambda a,b,c,d: a["policy"].update(no_windows_sandbox=False))

    def test_negative_091_policy_native(self):
        self.rejected(lambda a,b,c,d: a["policy"].update(no_native_test_authority=False))

    def test_negative_092_policy_rights(self):
        self.rejected(lambda a,b,c,d: a["policy"].update(rights_not_approved=False))

    def test_negative_093_policy_mapids(self):
        self.rejected(lambda a,b,c,d: a["policy"].update(mapids_not_reserved=False))

    def test_negative_094_policy_isolation(self):
        self.rejected(lambda a,b,c,d: a["policy"].update(watch_unchanged_not_global_save_isolation=False))

    def test_negative_095_policy_playable(self):
        self.rejected(lambda a,b,c,d: a["policy"].update(sinnoh_playable=True))

    def test_negative_096_policy_r09(self):
        self.rejected(lambda a,b,c,d: a["policy"].update(r09_global_only=False))

    def test_negative_097_gate_r07(self):
        self.rejected(lambda a,b,c,d: a["gates"].update(r07="APPROVED"))

    def test_negative_098_gate_r08(self):
        self.rejected(lambda a,b,c,d: a["gates"].update(r08="APPROVED"))

    def test_negative_099_gate_r09(self):
        self.rejected(lambda a,b,c,d: a["gates"].update(r09="APPROVED"))

    def test_negative_100_anchor_l07(self):
        self.rejected(lambda a,b,c,d: a["baseline_commits"].update(L07="0"*40))

    def test_negative_101_anchor_l08(self):
        self.rejected(lambda a,b,c,d: a["baseline_commits"].update(L08="0"*40))

    def test_negative_102_anchor_l09(self):
        self.rejected(lambda a,b,c,d: a["baseline_commits"].update(L09="0"*40))

    def test_negative_103_anchor_l10(self):
        self.rejected(lambda a,b,c,d: a["baseline_commits"].update(L10="0"*40))

    def test_negative_104_anchor_l11(self):
        self.rejected(lambda a,b,c,d: a["baseline_commits"].update(L11="0"*40))

    def test_negative_105_anchor_l12(self):
        self.rejected(lambda a,b,c,d: a["baseline_commits"].update(L12="0"*40))

    def test_negative_106_anchor_l13(self):
        self.rejected(lambda a,b,c,d: a["baseline_commits"].update(L13="0"*40))

    def test_negative_107_anchor_l14(self):
        self.rejected(lambda a,b,c,d: a["baseline_commits"].update(L14="0"*40))

    def test_negative_108_anchor_l15(self):
        self.rejected(lambda a,b,c,d: a["baseline_commits"].update(L15="0"*40))

    def test_negative_109_anchor_l16(self):
        self.rejected(lambda a,b,c,d: a["baseline_commits"].update(L16="0"*40))

    def test_negative_110_blob_l13(self):
        self.rejected(lambda a,b,c,d: a["public_sources"][0].update(git_blob_sha1="0"*40))

    def test_negative_111_blob_l14(self):
        self.rejected(lambda a,b,c,d: a["public_sources"][1].update(git_blob_sha1="0"*40))

    def test_negative_112_blob_l15(self):
        self.rejected(lambda a,b,c,d: a["public_sources"][2].update(git_blob_sha1="0"*40))

    def test_negative_113_blob_l16(self):
        self.rejected(lambda a,b,c,d: a["public_sources"][3].update(git_blob_sha1="0"*40))

    def test_negative_114_source_path(self):
        self.rejected(lambda a,b,c,d: a["public_sources"][3].update(path="private/saves.json"))

    def test_negative_115_source_reorder(self):
        self.rejected(lambda a,b,c,d: a["public_sources"].reverse())

    def test_negative_116_priority_rule_reorder(self):
        self.rejected(lambda a,b,c,d: a["priority_rules"].reverse())

    def test_negative_117_schema(self):
        self.rejected(lambda a,b,c,d: a.update(schema=2))

    def test_negative_118_stage(self):
        self.rejected(lambda a,b,c,d: a.update(stage="L18"))

    def test_negative_119_status(self):
        self.rejected(lambda a,b,c,d: a.update(status="NATIVE_QA_COMPLETE"))

    def test_negative_120_mode(self):
        self.rejected(lambda a,b,c,d: a.update(mode="UPLOAD"))

    def test_negative_121_version(self):
        self.rejected(lambda a,b,c,d: a.update(version=2))

    def test_negative_122_mirror_remove(self):
        self.rejected(lambda a,b,c,d: b["records"].pop())

    def test_negative_123_mirror_approved(self):
        self.rejected(lambda a,b,c,d: b["records"][0].update(independent_signoff=True))

    def test_negative_124_source_l16_approved(self):
        self.rejected(lambda a,b,c,d: c["records"][0].update(human_review_completed=True))

    def test_negative_125_source_l16_corrupt(self):
        self.rejected(lambda a,b,c,d: c["records"].pop())

    def test_negative_126_parent_r07(self):
        self.rejected(lambda a,b,c,d: d.update(r07_pending=False))

    def test_negative_127_parent_approval(self):
        self.rejected(lambda a,b,c,d: d.update(native_approved=44))

if __name__ == '__main__':
    unittest.main()
