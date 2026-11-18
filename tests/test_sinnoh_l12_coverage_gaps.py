"""L12: documentary coverage vs absent physical evidence, fail-closed tests."""
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
import audit_sinnoh_l12_coverage_gaps as l12
l11=l12.l11
l10=l11.l10
l08=l10.l09.l08


class SinnohL12CoverageGapsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read=l08.l07.l06.l05.l04.l03.l02.l00.read_json
        cls.src={stage:read(ROOT,path,maxsize=175000)
                 for stage,path,_sha in l08.PINNED}
        cls.items=[
            read(ROOT,l12.REPORT,maxsize=145000),
            read(ROOT,l12.MIRROR,maxsize=145000),
            read(ROOT,l11.GRAPH,maxsize=200000),
            read(ROOT,l11.MIRROR,maxsize=200000),
            read(ROOT,l10.INDEX,maxsize=155000),
            read(ROOT,l10.MIRROR,maxsize=155000),
            read(ROOT,l10.l09.PACKET,maxsize=155000),
            read(ROOT,l08.SNAPSHOT,maxsize=125000),
            read(ROOT,l08.DIFF,maxsize=16000),
            cls.src["G12"],cls.src["L04"],cls.src["L05"],
            cls.src["L06"],cls.src["L07"],cls.src["L07_SITE"],
            l08.l07.run(ROOT),l08.l07.l06.run(ROOT),
            l08.l07.l06.l05.run(ROOT),
            l08.l07.l06.l05.l04.run(ROOT),
            l08.l07.l06.l05.G12.run(ROOT)
        ]

    def audited(self, mutate=None):
        v=[copy.deepcopy(x) for x in self.items]
        if mutate: mutate(*v)
        return l12.audit(*v)

    def rejected(self, mutate):
        with self.assertRaises(ValueError):
            self.audited(mutate)

    def test_01_public_baseline_and_sources(self):
        self.assertTrue(l12.check_public_l11_blobs(ROOT))
        r=self.audited()
        self.assertEqual(r["status"],"PUBLIC_COVERAGE_AUDITED_REAL_EVIDENCE_MISSING")
        self.assertEqual(r["baseline_commits"]["L11"],l12.L11_MERGE)
        self.assertEqual(r["source_l11_git_blob"],l12.L11_BLOB)
        self.assertEqual(len(r["baseline_commits"]),5)

    def test_02_documentary_coverage_is_not_native_coverage(self):
        r=self.audited()
        self.assertEqual(r["public_documentary"],{
           "case_ids_checked":44,"criteria_ids_checked":20,
           "edges_checked":1084,"missing_public_edges":0})
        self.assertEqual(r["missing_evidence"],{
           "local_reports":5,"human_signoffs":20,
           "windows_native_qa":43,"android_native_qa":1,
           "native_qa_total":44,"bcd_approvals":13})

    def test_03_counters_44_20_43_1_and_zero_native(self):
        r=self.audited()
        self.assertEqual((r["cases_total"],r["criteria_total"],r["windows_cases"],r["android_cases"]),(44,20,43,1))
        self.assertEqual((r["native_approved"],r["human_approved"],r["local_reports_received"],r["phase_bcd_approved"]),(0,0,0,0))
        self.assertFalse(r["human_qa_authorized"])
        self.assertFalse(r["native_qa_authorized"])
        self.assertFalse(r["sinnoh_playable"])

    def test_04_no_false_approval_in_each_case_or_criterion(self):
        d=self.items[0]
        self.assertEqual(len(d["case_handoff"]),44)
        self.assertEqual(len(d["criterion_handoff"]),20)
        self.assertTrue(all(c["native_qa_state"]=="NOT_EXECUTED" and not c["authorized_native_qa"]
                            and not c["evidence_accepted"] for c in d["case_handoff"]))
        self.assertTrue(all(c["independent_review_state"]=="NOT_REVIEWED" and
                            not c["accepted_evidence"] and not c["human_signoff"]
                            for c in d["criterion_handoff"]))

    def test_05_windows_android_are_independent(self):
        d=self.items[0]
        self.assertEqual([(x["platform"],x["native_cases_missing"]) for x in d["platform_handoff"]],[("windows",43),("android",1)])
        self.assertTrue(d["platform_handoff"][0]["requires_windows_b10_b11"])
        self.assertFalse(d["platform_handoff"][1]["requires_windows_b10_b11"])
        self.assertTrue(all("B10" in x["pending_gates"] and "B11" in x["pending_gates"] for x in d["case_handoff"] if x["platform"]=="windows"))
        self.assertTrue(all("B10" not in x["pending_gates"] and "B11" not in x["pending_gates"] for x in d["case_handoff"] if x["platform"]=="android"))

    def test_06_r09_global_is_not_a_new_case(self):
        r=self.audited()
        self.assertTrue(r["r09_global_only"])
        self.assertEqual(r["blocker_ids"],["B09","B10","B11","R07","R08","R09"])
        self.assertEqual(self.items[0]["global_r09"]["case_ids"],[])
        self.assertTrue(self.items[0]["global_r09"]["not_a_new_case"])
        self.assertFalse(any("R09" in c["pending_gates"] for c in self.items[0]["case_handoff"]))

    def test_07_exact_layers_are_recomputed_from_L11(self):
        same=l11.l10.l09.l08.l07.l06.same
        self.assertTrue(same(self.items[0],l12.expected_report(self.items[2])))
        self.assertTrue(same(self.items[0],self.items[1]))
        self.assertEqual([(x["expected"],x["observed"],x["missing"])
                           for x in self.items[0]["coverage_layers"]],
                         [(1084,1084,0),(20,0,20),(43,0,43),(1,0,1),(5,0,5),(13,0,13)])

    def test_08_modified_public_git_blob_is_refused_offline(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-l12-public-test-") as td:
            root=Path(td)
            for path in (l11.GRAPH,l11.MIRROR):
                dst=root/path
                dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/path,dst)
            self.assertTrue(l12.check_public_l11_blobs(root))
            q=root/l11.MIRROR
            q.write_bytes(q.read_bytes()+b" ")
            with self.assertRaises(ValueError):
                l12.check_public_l11_blobs(root)

    def test_09_cli_no_untrusted_path_and_sanitized_output(self):
        cmd=[sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l12_coverage_gaps.py")]
        good=subprocess.run(cmd,text=True,capture_output=True,cwd=ROOT,check=False)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(json.loads(good.stdout)["missing_evidence"]["native_qa_total"],44)
        bad=subprocess.run(cmd+["--save",r"C:\\Users\\tester\\Save01.rxdata"],
                            text=True,capture_output=True,cwd=ROOT,check=False)
        self.assertEqual(bad.returncode,2)
        self.assertIn("SINNOH_L12_BLOCKED",bad.stderr)
        self.assertNotIn("Save01.rxdata",bad.stdout+bad.stderr)

    def test_10_auditor_never_runs_game_or_uploads(self):
        source=(ROOT/"scripts/regions/audit_sinnoh_l12_coverage_gaps.py").read_text("utf8")
        for forbidden in ("import requests","import subprocess","import socket",
                          "os.walk(","rglob(","subprocess.run(","os.system(",
                          "shutil.copy(","from urllib","httpx","os.environ"):
            self.assertNotIn(forbidden,source)

    def test_11_gates_and_counts_still_pending(self):
        d=self.items[0]
        self.assertEqual([d["gates"][x] for x in ("r07","r08","r09")],["PENDING"]*3)
        self.assertEqual(d["counts"]["phase_bcd_completed"],0)
        self.assertEqual(d["counts"]["phase_bcd_total"],13)
        self.assertFalse(d["guardrails"]["sinnoh_playable"])
        self.assertTrue(d["guardrails"]["watch_unchanged_not_global_save_isolation"])
        self.assertTrue(d["guardrails"]["asset_rights_not_approved"])
        self.assertTrue(d["guardrails"]["mapids_not_reserved"])

    def test_negative_001_missing_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"].pop())

    def test_negative_002_duplicate_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"].append(copy.deepcopy(a["case_handoff"][0])))

    def test_negative_003_reorder_cases(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"].reverse())

    def test_negative_004_fake_case_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0].update(id="FAKE"))

    def test_negative_005_duplicate_case_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][1].update(id=a["case_handoff"][0]["id"]))

    def test_negative_006_fake_case_kind(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0].update(kind="TEST_FAKE"))

    def test_negative_007_windows_to_android(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0].update(platform="android"))

    def test_negative_008_android_to_windows(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][-1].update(platform="windows"))

    def test_negative_009_case_criteria_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0]["criterion_ids"].pop())

    def test_negative_010_case_criteria_extra(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0]["criterion_ids"].append("R09_FAKE"))

    def test_negative_011_case_criteria_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0]["criterion_ids"].reverse())

    def test_negative_012_case_blocker_b10_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0]["blocker_ids"].remove("B10"))

    def test_negative_013_case_blocker_b11_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0]["blocker_ids"].remove("B11"))

    def test_negative_014_case_android_b10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][-1]["blocker_ids"].append("B10"))

    def test_negative_015_case_android_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][-1]["blocker_ids"].append("B11"))

    def test_negative_016_case_add_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][-1]["blocker_ids"].append("R09"))

    def test_negative_017_case_criteria_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0].update(documentary_criterion_links=0))

    def test_negative_018_case_blocker_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0].update(documentary_blocker_links=0))

    def test_negative_019_case_documentary_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0].update(documentary_link_status="NATIVE_APPROVED"))

    def test_negative_020_case_reviewed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0].update(independent_human_review_state="APPROVED"))

    def test_negative_021_case_native_completed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0].update(native_qa_state="PASSED"))

    def test_negative_022_case_native_auth(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0].update(authorized_native_qa=True))

    def test_negative_023_case_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0].update(evidence_accepted=True))

    def test_negative_024_case_pending_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0]["pending_gates"].pop())

    def test_negative_025_case_pending_extra(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0]["pending_gates"].append("R09"))

    def test_negative_026_case_private(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["case_handoff"][0].update(save="Save01.rxdata"))

    def test_negative_027_criteria_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"].pop())

    def test_negative_028_criteria_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"].append(copy.deepcopy(a["criterion_handoff"][0])))

    def test_negative_029_criteria_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"].reverse())

    def test_negative_030_criteria_fake_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"][0].update(id="R09_FAKE"))

    def test_negative_031_criteria_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"][0].update(stage="R08"))

    def test_negative_032_criteria_case_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"][0]["case_ids"].pop())

    def test_negative_033_criteria_case_extra(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"][0]["case_ids"].append("FAKE"))

    def test_negative_034_criteria_case_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"][0]["case_ids"].reverse())

    def test_negative_035_criteria_link_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"][0].update(documentary_links=0))

    def test_negative_036_criteria_documentary_state(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"][0].update(documentary_link_state="PHYSICAL_PROVEN"))

    def test_negative_037_criteria_review(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"][0].update(independent_review_state="ACCEPTED"))

    def test_negative_038_criteria_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"][0].update(accepted_evidence=True))

    def test_negative_039_criteria_signoff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["criterion_handoff"][0].update(human_signoff=True))

    def test_negative_040_blocker_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["blockers"].pop())

    def test_negative_041_blocker_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["blockers"].append(copy.deepcopy(a["blockers"][0])))

    def test_negative_042_blocker_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["blockers"].reverse())

    def test_negative_043_blocker_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["blockers"][0].update(id="B12"))

    def test_negative_044_blocker_scope(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["blockers"][1].update(scope="CROSS_PLATFORM"))

    def test_negative_045_blocker_case_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["blockers"][0]["case_ids"].pop())

    def test_negative_046_blocker_case_extra(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["blockers"][0]["case_ids"].append("FAKE"))

    def test_negative_047_blocker_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["blockers"][1].update(pending_cases=44))

    def test_negative_048_blocker_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["blockers"][0].update(approved=True))

    def test_negative_049_blocker_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["blockers"][0].update(state="APPROVED"))

    def test_negative_050_r09_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["blockers"][-1]["case_ids"].append("ball-TURTWIG"))

    def test_negative_051_r09_scope(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["blockers"][-1].update(scope="WINDOWS_ONLY"))

    def test_negative_052_global_r09_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["global_r09"].update(state="APPROVED"))

    def test_negative_053_global_r09_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["global_r09"]["case_ids"].append("ball-TURTWIG"))

    def test_negative_054_global_r09_newcase(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["global_r09"].update(not_a_new_case=False))

    def test_negative_055_global_r09_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["global_r09"].update(approved=True))

    def test_negative_056_global_r09_scope(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["global_r09"].update(scope="CROSS_PLATFORM"))

    def test_negative_057_global_r09_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["global_r09"].update(id="R10"))

    def test_negative_058_coverage_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"].pop())

    def test_negative_059_coverage_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"].append(copy.deepcopy(a["coverage_layers"][0])))

    def test_negative_060_coverage_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"].reverse())

    def test_negative_061_coverage_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][0].update(id="NATIVE_APPROVED"))

    def test_negative_062_coverage_public_expected(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][0].update(expected=0))

    def test_negative_063_coverage_public_observed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][0].update(observed=0))

    def test_negative_064_coverage_public_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][0].update(missing=1))

    def test_negative_065_coverage_public_state(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][0].update(state="ALL_EVIDENCE_APPROVED"))

    def test_negative_066_coverage_public_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][0].update(native_evidence=True))

    def test_negative_067_coverage_human_observed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][1].update(observed=20))

    def test_negative_068_coverage_human_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][1].update(missing=0))

    def test_negative_069_coverage_human_state(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][1].update(state="APPROVED"))

    def test_negative_070_coverage_win_observed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][2].update(observed=43))

    def test_negative_071_coverage_win_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][2].update(missing=0))

    def test_negative_072_coverage_android_observed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][3].update(observed=1))

    def test_negative_073_coverage_android_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][3].update(missing=0))

    def test_negative_074_coverage_local_observed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][4].update(observed=5))

    def test_negative_075_coverage_local_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][4].update(missing=0))

    def test_negative_076_coverage_bcd_observed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][5].update(observed=13))

    def test_negative_077_coverage_bcd_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["coverage_layers"][5].update(missing=0))

    def test_negative_078_windows_native_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["platform_handoff"][0].update(native_cases_tested=43))

    def test_negative_079_android_native_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["platform_handoff"][1].update(native_cases_tested=1))

    def test_negative_080_platform_native_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["platform_handoff"][0].update(native_cases_missing=0))

    def test_negative_081_platform_android_b10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["platform_handoff"][1].update(requires_windows_b10_b11=True))

    def test_negative_082_platform_windows_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["platform_handoff"][0].update(requires_windows_b10_b11=False))

    def test_negative_083_platform_shared_auth(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["platform_handoff"][0].update(shares_android_approval=True))

    def test_negative_084_platform_android_shared_auth(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["platform_handoff"][1].update(shares_android_approval=True))

    def test_negative_085_platform_wrong_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["platform_handoff"][1]["case_ids"].__setitem__(0,"ball-TURTWIG"))

    def test_negative_086_platform_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["platform_handoff"].reverse())

    def test_negative_087_platform_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["platform_handoff"][0].update(state="APPROVED"))

    def test_negative_088_integrity_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"].update(links_checked=1083))

    def test_negative_089_integrity_added_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"]["added_links"].append("FAKE"))

    def test_negative_090_integrity_missing_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"]["missing_links"].append("B09_ORIGIN"))

    def test_negative_091_integrity_reordered(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"]["reordered_links"].append("R08"))

    def test_negative_092_integrity_case_drift(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"]["case_id_drift"].append("FAKE"))

    def test_negative_093_integrity_criterion_drift(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"]["criterion_id_drift"].append("FAKE"))

    def test_negative_094_integrity_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"]["platform_drift"].append("android-joi-play"))

    def test_negative_095_integrity_blocker_scope(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"]["blocker_scope_drift"].append("B11"))

    def test_negative_096_integrity_differences(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"].update(differences_found=1))

    def test_negative_097_integrity_false_physical(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"].update(physical_source_authenticated=True))

    def test_negative_098_integrity_false_human(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"].update(human_review_completed=True))

    def test_negative_099_integrity_false_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"].update(native_qa_completed=True))

    def test_negative_100_integrity_false_public(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["documentary_integrity"].update(verified_public_metadata_only=False))

    def test_negative_101_counts_links_verified(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["counts"].update(documentary_links_verified=0))

    def test_negative_102_counts_links_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["counts"].update(documentary_links_missing=1))

    def test_negative_103_counts_native_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["counts"].update(native_tests_missing=0))

    def test_negative_104_counts_human_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["counts"].update(human_evidence_missing=0))

    def test_negative_105_counts_local_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["counts"].update(local_reports_missing=0))

    def test_negative_106_counts_bcd_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["counts"].update(phase_bcd_missing=0))

    def test_negative_107_counts_native_completed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["counts"].update(native_completed=1))

    def test_negative_108_counts_human_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["counts"].update(human_approved=1))

    def test_negative_109_counts_native_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["counts"].update(native_approved=1))

    def test_negative_110_counts_bcd_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["counts"].update(phase_bcd_completed=1))

    def test_negative_111_counts_bool_forge(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["counts"].update(native_approved=False))

    def test_negative_112_gates_r07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["gates"].update(r07="APPROVED"))

    def test_negative_113_gates_r08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["gates"].update(r08="APPROVED"))

    def test_negative_114_gates_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["gates"].update(r09="APPROVED"))

    def test_negative_115_gates_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["gates"].update(asset_rights_approved=True))

    def test_negative_116_gates_mapids(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["gates"].update(mapids_reserved=True))

    def test_negative_117_gates_global_save(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["gates"].update(b11_global_save_isolation_proven=True))

    def test_negative_118_gates_playable(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["gates"].update(sinnoh_playable=True))

    def test_negative_119_guardrails_r07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(r07_pending=False))

    def test_negative_120_guardrails_r08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(r08_pending=False))

    def test_negative_121_guardrails_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(r09_pending=False))

    def test_negative_122_guardrails_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(watch_unchanged_not_global_save_isolation=False))

    def test_negative_123_guardrails_private(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(private_handoff_not_authorized=False))

    def test_negative_124_guardrails_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(asset_rights_not_approved=False))

    def test_negative_125_guardrails_mapids(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(mapids_not_reserved=False))

    def test_negative_126_guardrails_human(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(human_criteria_approved=20))

    def test_negative_127_guardrails_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(native_cases_completed=44))

    def test_negative_128_guardrails_local(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(local_reports_received=5))

    def test_negative_129_guardrails_bcd(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(bcd_approved=13))

    def test_negative_130_guardrails_joiplay(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(no_joiplay_execution=False))

    def test_negative_131_guardrails_game(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(no_game_exe_execution=False))

    def test_negative_132_guardrails_sandbox(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(no_windows_sandbox_execution=False))

    def test_negative_133_guardrails_playable(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(sinnoh_playable=True))

    def test_negative_134_guardrails_android(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["guardrails"].update(local_android_l05_complete=True))

    def test_negative_135_source_l11_blob(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["source_l11"].update(git_blob_sha1="0"*40))

    def test_negative_136_source_l11_path(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["source_l11"].update(path="private/save.json"))

    def test_negative_137_source_l11_unknown(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["source_l11"].update(secret="HMAC"))

    def test_negative_138_anchor_l07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["baseline_commits"].update(L07="0"*40))

    def test_negative_139_anchor_l08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["baseline_commits"].update(L08="0"*40))

    def test_negative_140_anchor_l09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["baseline_commits"].update(L09="0"*40))

    def test_negative_141_anchor_l10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["baseline_commits"].update(L10="0"*40))

    def test_negative_142_anchor_l11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a["baseline_commits"].update(L11="0"*40))

    def test_negative_143_report_schema(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a.update(schema=2))

    def test_negative_144_report_version(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a.update(version=2))

    def test_negative_145_report_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a.update(stage="L13"))

    def test_negative_146_report_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a.update(status="NATIVE_APPROVED"))

    def test_negative_147_report_mode(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a.update(mode="NATIVE_EXECUTION"))

    def test_negative_148_report_private(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: a.update(save_path="C:\\Users\\tester\\Save01.rxdata"))

    def test_negative_149_mirror_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: b["case_handoff"][0].update(id="FAKE"))

    def test_negative_150_mirror_approval(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: b["case_handoff"][0].update(authorized_native_qa=True))

    def test_negative_151_mirror_criteria(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: b["criterion_handoff"].pop())

    def test_negative_152_mirror_gates(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: b["gates"].update(r08="APPROVED"))

    def test_negative_153_mirror_coverage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: b["coverage_layers"][1].update(missing=0))

    def test_negative_154_upstream_l11_graph(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: c["case_nodes"][0].update(native_qa_authorized=True))

    def test_negative_155_upstream_l11_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: d["case_nodes"][0].update(id="FAKE"))

    def test_negative_156_upstream_l10_index(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: e["cases"][0].update(approved=True))

    def test_negative_157_upstream_l10_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: f["cases"][0].update(id="FAKE"))

    def test_negative_158_upstream_l09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: g["case_handoff"][0].update(native_status="passed"))

    def test_negative_159_upstream_l08_snapshot(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: h["cases"][0].update(native_qa_authorized=True))

    def test_negative_160_upstream_l08_diff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: i["comparisons"][0]["added_ids"].append("FAKE"))

    def test_negative_161_upstream_g12(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: j["cases"][0].update(native_status="passed"))

    def test_negative_162_upstream_l04(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: k["rows"][0]["criteria"][0].update(local_human_signoff=True))

    def test_negative_163_upstream_l05(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: l.update(mapids_reserved=True))

    def test_negative_164_upstream_l06(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: m.update(asset_rights_approved=True))

    def test_negative_165_upstream_l07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: n["cases"][-1].update(platform="windows"))

    def test_negative_166_upstream_l07_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: o["cases"][0].update(id="FAKE"))

    def test_negative_167_upstream_l07_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: p["counts"].update(native_approved=1))

    def test_negative_168_upstream_l06_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: q.update(native_cases_approved=1))

    def test_negative_169_upstream_l05_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: s.update(native_cases_approved=1))

    def test_negative_170_upstream_l04_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: t.update(criteria_reviewed=1))

    def test_negative_171_upstream_g12_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u: u.update(evidence_accepted_cases=1))

if __name__=='__main__':
    unittest.main()
