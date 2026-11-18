"""L19 GitHub-public gap consolidation: contract and synthetic-negative tests."""
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
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l19_consolidation as l19
l18 = l19.l18
read = l18.l17.l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json

class SinnohL19PublicGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parts = [
            read(ROOT, l19.REPORT, maxsize=225000),
            read(ROOT, l19.MIRROR, maxsize=225000),
            read(ROOT, l18.REPORT, maxsize=210000),
            read(ROOT, l18.MIRROR, maxsize=210000),
            read(ROOT, l18.l17.INDEX, maxsize=195000),
            read(ROOT, l18.l17.MIRROR, maxsize=195000),
            read(ROOT, l18.l17.l16.MATRIX, maxsize=185000),
            l18.l17.l16.run(ROOT),
        ]

    def audited(self, mutation=None):
        arr = [copy.deepcopy(x) for x in self.parts]
        if mutation: mutation(*arr)
        return l19.audit(*arr)

    def rejected(self, mutation):
        with self.assertRaises(ValueError):
            self.audited(mutation)

    def test_01_parent_git_blob_immutable(self):
        self.assertTrue(l19.check_l18_git_blobs(ROOT))
        result=self.audited()
        self.assertEqual(result["status"],"PUBLIC_GAP_CONSOLIDATION_AUDITED_ALL_BLOCKED")
        self.assertEqual(result["baseline_commits"]["L18"],l19.L18_MERGE)
        self.assertEqual(result["public_sources"][-1],{"stage":"L18","path":l18.REPORT,"git_blob_sha1":l19.L18_BLOB})

    def test_02_exact_88_all_pending_blocked(self):
        d=self.parts[0];r=self.audited()
        self.assertEqual((r["requests"],r["pending"],r["blocked"],r["gaps_open"],r["gaps_closed"]),(88,88,88,88,0))
        self.assertEqual([x["order"] for x in d["records"]],list(range(1,89)))
        self.assertEqual(len({x["request_id"] for x in d["records"]}),88)
        self.assertTrue(all(x["review_state"]=="NOT_REVIEWED" and x["review_gap_status"]=="OPEN_DOCUMENTARY_ONLY" and x["status"]=="PENDING" and x["readiness"]=="BLOCKED" for x in d["records"]))

    def test_03_1084_edges_exact_projection(self):
        r=self.audited()
        self.assertEqual((r["links"],r["case_to_criterion_links"],r["case_to_blocker_links"],r["criterion_to_blocker_links"]),(1084,846,218,20))
        self.assertEqual(sum(x["documentary_dependency_count"] for x in self.parts[0]["records"]),1084)
        self.assertEqual(self.parts[0]["edge_summary"]["total"],1084)

    def test_04_18_anonymous_slots_unassigned(self):
        d=self.parts[0]
        anon=[x for x in d["records"] if x["anonymous_bookkeeping_slot"]]
        self.assertEqual(len(anon),18)
        self.assertTrue(all(x["documentary_dependency_count"]==0 and x["linked_l04_criterion_ids"]==[] and x["anonymous_identity_assigned"] is False for x in anon))

    def test_05_r09_global_and_separate_windows_android(self):
        d=self.parts[0]
        self.assertEqual(d["global_r09"]["case_ids"],[])
        self.assertEqual(d["global_r09"]["documentary_dependency_request_ids"],[])
        self.assertFalse(d["global_r09"]["signoff"])
        native=[x for x in d["records"] if x["kind"]=="NATIVE_CASE"]
        self.assertEqual((len([x for x in native if x["platform"]=="windows"]),len([x for x in native if x["platform"]=="android"])),(43,1))
        android=[x for x in native if x["platform"]=="android"][0]
        self.assertNotIn("B10",android["prerequisite_blocker_ids"])
        self.assertNotIn("B11",android["prerequisite_blocker_ids"])
        self.assertEqual(d["platform_partition"][1]["native_authorization"],False)

    def test_06_preserve_zero_native_and_human_without_playability(self):
        r=self.audited()
        self.assertEqual((r["human_reviews"],r["exit_criteria_met"],r["local_reports_received"],r["human_approved"],r["native_executed"],r["native_approved"],r["phase_bcd_approved"]),(0,0,0,0,0,0,0))
        self.assertEqual(r["phase_bcd_total"],13)
        self.assertTrue(r["r07_pending"] and r["r08_pending"] and r["r09_pending"] and r["no_native_authorization"])
        self.assertFalse(r["sinnoh_playable"])

    def test_07_exact_derivation_from_l18(self):
        expected=l19.expected_report(self.parts[2])
        same=l18.l17.l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.same
        self.assertTrue(same(self.parts[0],expected))
        self.assertTrue(same(self.parts[1],expected))

    def test_08_tampered_pinned_public_blob_fails(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-l19-public-") as temp:
            root=Path(temp)
            for p in (l18.REPORT,l18.MIRROR):
                f=root/p;f.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/p,f)
            self.assertTrue(l19.check_l18_git_blobs(root))
            f=root/l18.MIRROR;f.write_bytes(f.read_bytes()+b" ")
            with self.assertRaises(ValueError):
                l19.check_l18_git_blobs(root)

    def test_09_cli_rejects_host_paths_without_echo(self):
        args=[sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l19_consolidation.py")]
        good=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(json.loads(good.stdout)["requests"],88)
        bad=subprocess.run(args+["--save","C:/private/Save01.rxdata"],cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(bad.returncode,2)
        self.assertIn("SINNOH_L19_BLOCKED",bad.stderr)
        self.assertNotIn("Save01.rxdata",bad.stdout+bad.stderr)

    def test_10_auditor_no_native_io_or_network(self):
        s=(ROOT/"scripts/regions/audit_sinnoh_l19_consolidation.py").read_text("utf8")
        for token in ("import requests","import subprocess","import socket","os.walk(","rglob(","os.system(","subprocess.run(","httpx","os.environ"):
            self.assertNotIn(token,s)
    def test_negative_001_row_deleted(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"].pop())

    def test_negative_002_row_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"].append(copy.deepcopy(a["records"][0])))

    def test_negative_003_row_reverse(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"].reverse())

    def test_negative_004_row_id_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(request_id="FAKE-ID"))

    def test_negative_005_row_id_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][1].update(request_id=a["records"][0]["request_id"]))

    def test_negative_006_row_position_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(order=99))

    def test_negative_007_row_kind_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(kind="NATIVE_CASE"))

    def test_negative_008_row_platform_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][-1].update(platform="windows"))

    def test_negative_009_row_priority_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(priority=4))

    def test_negative_010_row_priority_label_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(priority_label="NATIVE_READY"))

    def test_negative_011_row_subject_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(subject_id="R09"))

    def test_negative_012_row_gap_code_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0]["gap_types"].append("APPROVED"))

    def test_negative_013_row_gap_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0]["gap_types"].pop())

    def test_negative_014_row_gap_reordered(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0]["gap_types"].reverse())

    def test_negative_015_row_next_step_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(next_documentary_step="Execute Game.exe"))

    def test_negative_016_row_exit_fake(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0]["exit_criteria_codes"].append("COMPLETED"))

    def test_negative_017_row_blocker_fake(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0]["prerequisite_blocker_ids"].append("R09"))

    def test_negative_018_row_blocker_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0]["prerequisite_blocker_ids"].pop())

    def test_negative_019_row_human_fake(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][11]["linked_l04_criterion_ids"].append("FABRICATED"))

    def test_negative_020_row_human_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][11]["linked_l04_criterion_ids"].pop())

    def test_negative_021_row_link_extra(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][11]["documentary_dependency_request_ids"].append("L13-GLOBAL-R09"))

    def test_negative_022_row_link_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][-1]["documentary_dependency_request_ids"].pop())

    def test_negative_023_row_count_fake(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][-1].update(documentary_dependency_count=17))

    def test_negative_024_anonymous_deanonymized(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][6].update(anonymous_bookkeeping_slot=False))

    def test_negative_025_anonymous_identified(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][6].update(anonymous_identity_assigned=True))

    def test_negative_026_anonymous_fake_link(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][6]["documentary_dependency_request_ids"].append("L13-BLOCKER-B09"))

    def test_negative_027_anonymous_fake_criterion(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][6]["linked_l04_criterion_ids"].append("B09_ORIGIN"))

    def test_negative_028_android_inherits_B10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][-1]["prerequisite_blocker_ids"].append("B10"))

    def test_negative_029_android_inherits_B11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][-1]["prerequisite_blocker_ids"].append("B11"))

    def test_negative_030_r09_native_link(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][-1]["prerequisite_blocker_ids"].append("R09"))

    def test_negative_031_coverage_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(public_coverage="PHYSICAL_APPROVED"))

    def test_negative_032_missing_evidence_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(missing_evidence="NONE"))

    def test_negative_033_review_state_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(review_state="APPROVED"))

    def test_negative_034_gap_closed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(review_gap_status="CLOSED"))

    def test_negative_035_status_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(status="APPROVED"))

    def test_negative_036_readiness_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(readiness="READY"))

    def test_negative_037_human_signoff_true(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(independent_review_approved=True))

    def test_negative_038_exit_criteria_met_true(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(exit_criteria_met=True))

    def test_negative_039_native_executed_true(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][-1].update(native_qa_executed=True))

    def test_negative_040_physical_received_true(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(physical_evidence_accepted=True))

    def test_negative_041_assigned_reviewer_true(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(assigned_reviewer=True))

    def test_negative_042_assigned_reviewer_name(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["records"][0].update(reviewer_name="PERSON_X"))

    def test_negative_043_kind_summary_deleted(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["kind_summary"].pop())

    def test_negative_044_kind_summary_reordered(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["kind_summary"].reverse())

    def test_negative_045_kind_summary_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["kind_summary"][0].update(independent_signoffs=1))

    def test_negative_046_kind_summary_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["kind_summary"][0].update(requests=4))

    def test_negative_047_kind_summary_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["kind_summary"][-1].update(documentary_edges=0))

    def test_negative_048_kind_summary_coverage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["kind_summary"][0].update(coverage="PHYSICAL_VALIDATED"))

    def test_negative_049_gap_kind_deleted(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["gap_types_by_kind"].pop())

    def test_negative_050_gap_kind_reversed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["gap_types_by_kind"].reverse())

    def test_negative_051_gap_kind_added(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["gap_types_by_kind"][0]["gap_types"].append("AUTHORIZED"))

    def test_negative_052_edge_total_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["edge_summary"].update(total=1083))

    def test_negative_053_edge_criterion_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["edge_summary"].update(case_to_criterion=847))

    def test_negative_054_edge_blocker_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["edge_summary"].update(case_to_blocker=219))

    def test_negative_055_edge_human_blocker_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["edge_summary"].update(criterion_to_blocker=21))

    def test_negative_056_counts_total(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(consolidated_requests=87))

    def test_negative_057_counts_pending(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(consolidated_pending=87))

    def test_negative_058_counts_blocked(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(consolidated_blocked=87))

    def test_negative_059_counts_open(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(consolidated_gaps_open=87))

    def test_negative_060_counts_closed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(consolidated_gaps_closed=1))

    def test_negative_061_counts_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(consolidated_links=1083))

    def test_negative_062_counts_anonymous(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(consolidated_anonymous_slots=17))

    def test_negative_063_counts_human_signoffs(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(consolidated_human_signoffs=1))

    def test_negative_064_counts_native_passes(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(consolidated_native_passes=1))

    def test_negative_065_counts_exit_met(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(consolidated_exit_criteria_met=1))

    def test_negative_066_counts_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(consolidated_physical_evidence_accepted=1))

    def test_negative_067_counts_locals(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(local_reports=5))

    def test_negative_068_counts_human(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(human_approved=20))

    def test_negative_069_counts_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(native_completed=44))

    def test_negative_070_counts_bcd(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["counts"].update(phase_bcd_completed=13))

    def test_negative_071_r07_pretended_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["gates"].update(r07="APPROVED"))

    def test_negative_072_r08_pretended_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["gates"].update(r08="APPROVED"))

    def test_negative_073_r09_pretended_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["gates"].update(r09="APPROVED"))

    def test_negative_074_r09_new_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["global_r09"]["case_ids"].append("fake-case"))

    def test_negative_075_r09_new_link(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["global_r09"]["documentary_dependency_request_ids"].append("L13-NATIVE-fake"))

    def test_negative_076_r09_signoff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["global_r09"].update(signoff=True))

    def test_negative_077_r09_review_complete(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["global_r09"].update(review_complete=True))

    def test_negative_078_android_native_authorization(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["platform_partition"][1].update(native_authorization=True))

    def test_negative_079_android_inherits_B10_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["platform_partition"][1].update(requires_windows_b10_b11=True))

    def test_negative_080_windows_loses_B10_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["platform_partition"][0].update(requires_windows_b10_b11=False))

    def test_negative_081_windows_review_complete(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["platform_partition"][0].update(review_complete=True))

    def test_negative_082_platform_swap(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["platform_partition"].reverse())

    def test_negative_083_policy_no_uploads(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["policy"].update(no_private_uploads=False))

    def test_negative_084_policy_no_game(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["policy"].update(no_game_exe=False))

    def test_negative_085_policy_no_sandbox(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["policy"].update(no_windows_sandbox=False))

    def test_negative_086_policy_no_joiplay(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["policy"].update(no_joiplay=False))

    def test_negative_087_policy_no_saves(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["policy"].update(no_saves=False))

    def test_negative_088_policy_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["policy"].update(R08_asset_rights_not_approved=False))

    def test_negative_089_policy_mapids(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["policy"].update(R07_mapids_not_authorized=False))

    def test_negative_090_policy_isolation(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["policy"].update(B11_watch_unchanged_is_not_global_save_isolation=False))

    def test_negative_091_policy_playable(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["policy"].update(sinnoh_playable=True))

    def test_negative_092_policy_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["policy"].update(r09_global_only_no_case_edges=False))

    def test_negative_093_policy_android(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["policy"].update(android_does_not_inherit_windows_b10_b11=False))

    def test_negative_094_commit_l07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["baseline_commits"].update(L07="0"*40))

    def test_negative_095_commit_l08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["baseline_commits"].update(L08="0"*40))

    def test_negative_096_commit_l09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["baseline_commits"].update(L09="0"*40))

    def test_negative_097_commit_l10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["baseline_commits"].update(L10="0"*40))

    def test_negative_098_commit_l11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["baseline_commits"].update(L11="0"*40))

    def test_negative_099_commit_l12(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["baseline_commits"].update(L12="0"*40))

    def test_negative_100_commit_l13(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["baseline_commits"].update(L13="0"*40))

    def test_negative_101_commit_l14(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["baseline_commits"].update(L14="0"*40))

    def test_negative_102_commit_l15(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["baseline_commits"].update(L15="0"*40))

    def test_negative_103_commit_l16(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["baseline_commits"].update(L16="0"*40))

    def test_negative_104_commit_l17(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["baseline_commits"].update(L17="0"*40))

    def test_negative_105_commit_l18(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["baseline_commits"].update(L18="0"*40))

    def test_negative_106_public_sources_reordered(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["public_sources"].reverse())

    def test_negative_107_l18_blob_change(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["public_sources"][5].update(git_blob_sha1="0"*40))

    def test_negative_108_l18_source_path(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a["public_sources"][5].update(path="private/saves.json"))

    def test_negative_109_schema(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a.update(schema=2))

    def test_negative_110_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a.update(stage="L20"))

    def test_negative_111_version(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a.update(version=2))

    def test_negative_112_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a.update(status="QA_READY"))

    def test_negative_113_mode(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: a.update(mode="UPLOAD_SAVES"))

    def test_negative_114_mirror_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: b["records"][0].update(independent_review_approved=True))

    def test_negative_115_mirror_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: b["records"].pop())

    def test_negative_116_l18_report_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: c["records"][0].update(human_signoff=True))

    def test_negative_117_l18_report_closed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: c["records"][0].update(review_gap_status="CLOSED"))

    def test_negative_118_l18_mirror_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: d["records"][-1].update(native_qa_approved=True))

    def test_negative_119_l17_index_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: e["records"][0].update(independent_signoff=True))

    def test_negative_120_l17_mirror_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: f["records"][0].update(physical_evidence_accepted=True))

    def test_negative_121_l16_inmemory_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: g["records"][0].update(human_review_completed=True))

    def test_negative_122_parent_l16_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h: h.update(r07_pending=False))

if __name__ == '__main__':
    unittest.main()
