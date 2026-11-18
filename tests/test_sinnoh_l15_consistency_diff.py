"""Sinnoh L15 public consistency / delta report regression tests."""
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
import audit_sinnoh_l15_consistency_diff as l15
l14 = l15.l14
l13 = l14.l13
l08 = l13.l12.l11.l10.l09.l08


class SinnohL15PublicDiffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read = l08.l07.l06.l05.l04.l03.l02.l00.read_json
        docs = {stage: read(ROOT, path, maxsize=175000)
                for stage, path, _ in l08.PINNED}
        cls.items = [
            read(ROOT, l15.REPORT, maxsize=145000),
            read(ROOT, l15.MIRROR, maxsize=145000),
            read(ROOT, l14.MATRIX, maxsize=180000),
            read(ROOT, l14.MIRROR, maxsize=180000),
            read(ROOT, l13.QUEUE, maxsize=190000),
            read(ROOT, l13.MIRROR, maxsize=190000),
            read(ROOT, l13.l12.REPORT, maxsize=145000),
            read(ROOT, l13.l12.MIRROR, maxsize=145000),
            read(ROOT, l13.l12.l11.GRAPH, maxsize=200000),
            read(ROOT, l13.l12.l11.MIRROR, maxsize=200000),
            read(ROOT, l13.l12.l11.l10.INDEX, maxsize=155000),
            read(ROOT, l13.l12.l11.l10.MIRROR, maxsize=155000),
            read(ROOT, l13.l12.l11.l10.l09.PACKET, maxsize=155000),
            read(ROOT, l08.SNAPSHOT, maxsize=125000),
            read(ROOT, l08.DIFF, maxsize=16000),
            docs["G12"], docs["L04"], docs["L05"], docs["L06"],
            docs["L07"], docs["L07_SITE"],
            l08.l07.run(ROOT), l08.l07.l06.run(ROOT),
            l08.l07.l06.l05.run(ROOT),
            l08.l07.l06.l05.l04.run(ROOT),
            l08.l07.l06.l05.G12.run(ROOT),
        ]

    def audited(self, mutation=None):
        items = [copy.deepcopy(x) for x in self.items]
        if mutation: mutation(*items)
        return l15.audit(*items)

    def rejected(self, mutation):
        with self.assertRaises(ValueError):
            self.audited(mutation)

    def test_01_pinned_public_sha_L13_L14_and_commits(self):
        self.assertTrue(l15.check_l13_l14_blobs(ROOT))
        result = self.audited()
        self.assertEqual(result["status"], "PUBLIC_CONSISTENCY_VALID_PHYSICAL_QA_PENDING")
        self.assertEqual(result["baseline_commits"]["L14"], l15.L14_MERGE)
        self.assertEqual(result["public_source_blobs"], [
            {"stage": stage, "path": path, "git_blob_sha1": sha}
            for stage, path, sha in l15.PINNED
        ])
        self.assertEqual(len(result["baseline_commits"]), 8)

    def test_02_88_ordered_requests_identity_consistency(self):
        r = self.audited()
        self.assertEqual((r["request_rows_matched"],
                          r["id_priority_platform_status_drift"]), (88, 0))
        rows = self.items[0]["records"]
        self.assertEqual(len(rows), 88)
        self.assertEqual(len({x["request_id"] for x in rows}), 88)
        self.assertEqual([x["order"] for x in rows], list(range(1, 89)))
        self.assertEqual([x["request_id"] for x in rows],
                         [x["request_id"] for x in self.items[2]["rows"]])

    def test_03_1084_l14_links_additions_not_native_progress(self):
        r = self.audited()
        self.assertEqual((r["new_l14_documentary_projection"],
                          r["documentary_links"]), (1084, 1084))
        self.assertEqual((r["case_criterion_links"], r["case_blocker_links"],
                          r["criterion_blocker_links"]), (846, 218, 20))
        cats = self.items[0]["change_categories"]
        self.assertEqual(cats[2]["baseline"], 0)
        self.assertEqual(cats[2]["added"], 1084)
        self.assertEqual(cats[2]["state"],
                         "ADDED_DOCUMENTARY_PROJECTION_NOT_NATIVE_EVIDENCE")
        self.assertEqual(cats[3]["observed"], 0)
        self.assertEqual(cats[3]["state"], "NO_REAL_EVIDENCE_RECEIVED")

    def test_04_anonymous_slots_stay_unassigned_without_new_links(self):
        r = self.audited()
        self.assertEqual(r["anonymous_slots_unassigned"], 18)
        rows = [x for x in self.items[0]["records"]
                if x["anonymous_bookkeeping_slot"]]
        self.assertEqual(len(rows), 18)
        self.assertTrue(all(x["l14_documentary_projection_added"] == 0
                            and x["l14_documentary_dependency_count"] == 0
                            for x in rows))

    def test_05_windows_android_and_r09_are_separate(self):
        r = self.audited()
        self.assertEqual((r["windows_native_pending"],
                          r["android_native_pending"]), (43, 1))
        self.assertTrue(r["r09_global_only"])
        self.assertEqual(self.items[0]["global_r09"]["case_ids"], [])
        self.assertEqual(self.items[0]["global_r09"]
                         ["documentary_dependency_request_ids"], [])
        self.assertFalse(self.items[0]["platform_partition"][1]
                         ["requires_windows_b10_b11"])
        self.assertTrue(self.items[0]["platform_partition"][0]
                        ["requires_windows_b10_b11"])

    def test_06_all_real_evidence_remains_missing_and_no_qa(self):
        r = self.audited()
        self.assertEqual((r["local_reports_received"], r["human_approved"],
                          r["native_executed"], r["native_approved"],
                          r["phase_bcd_approved"]), (0, 0, 0, 0, 0))
        self.assertEqual(r["phase_bcd_total"], 13)
        self.assertTrue(all((r["r07_pending"], r["r08_pending"],
                             r["r09_pending"], r["no_private_uploads"],
                             r["no_physical_evidence"])))
        self.assertFalse(r["sinnoh_playable"])

    def test_07_expected_report_recomputed_from_two_ancestors(self):
        strict = l14.l13.l12.l11.l10.l09.l08.l07.l06.same
        expected = l15.expected_report(self.items[4], self.items[2])
        self.assertTrue(strict(self.items[0], expected))
        self.assertTrue(strict(self.items[1], expected))

    def test_08_public_blob_change_refused_even_when_json_parseable(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-l15-public-") as td:
            root = Path(td)
            for p in (l13.QUEUE, l13.MIRROR, l14.MATRIX, l14.MIRROR):
                dest = root / p
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / p, dest)
            self.assertTrue(l15.check_l13_l14_blobs(root))
            path = root / l14.MIRROR
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaises(ValueError):
                l15.check_l13_l14_blobs(root)

    def test_09_cli_rejects_arbitrary_private_input_without_echo(self):
        command = [sys.executable, str(ROOT / "scripts/regions/"
                                      "audit_sinnoh_l15_consistency_diff.py")]
        good = subprocess.run(command, capture_output=True, text=True,
                              cwd=ROOT, check=False)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertEqual(json.loads(good.stdout)["request_rows_matched"], 88)
        bad = subprocess.run(command + ["--save", "C:/private/Save01.rxdata"],
                             capture_output=True, text=True,
                             cwd=ROOT, check=False)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("SINNOH_L15_BLOCKED", bad.stderr)
        self.assertNotIn("Save01.rxdata", bad.stdout + bad.stderr)

    def test_10_no_native_execution_network_or_path_discovery(self):
        source = (ROOT / "scripts/regions/"
                  "audit_sinnoh_l15_consistency_diff.py").read_text("utf8")
        for banned in ("import requests", "import subprocess", "import socket",
                       "os.walk(", "rglob(", "os.system(", "subprocess.run(",
                       "shutil.copy(", "from urllib", "httpx", "os.environ"):
            self.assertNotIn(banned, source)

    def test_negative_001_missing_record(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"].pop())

    def test_negative_002_duplicate_record(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"].append(copy.deepcopy(a["records"][0])))

    def test_negative_003_reverse_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"].reverse())

    def test_negative_004_faked_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(request_id="L13-FAKE"))

    def test_negative_005_duplicated_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][1].update(request_id=a["records"][0]["request_id"]))

    def test_negative_006_row_order_zero(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(order=0))

    def test_negative_007_row_subject(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(subject_id="R10"))

    def test_negative_008_row_kind(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(kind="NATIVE_CASE"))

    def test_negative_009_row_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(platform="android"))

    def test_negative_010_row_priority(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(priority=4))

    def test_negative_011_row_priority_label(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(priority_label="P0_NATIVE_READY"))

    def test_negative_012_l13_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(source_l13_status="APPROVED"))

    def test_negative_013_l14_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(source_l14_status="APPROVED"))

    def test_negative_014_readiness(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(readiness="READY"))

    def test_negative_015_comparison(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(comparison_status="NATIVE_APPROVED"))

    def test_negative_016_identity_drift(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0]["identity_drift"].append("changed"))

    def test_negative_017_priority_drift(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0]["priority_drift"].append("changed"))

    def test_negative_018_platform_drift(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0]["platform_drift"].append("changed"))

    def test_negative_019_status_drift(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0]["status_drift"].append("changed"))

    def test_negative_020_blockers_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(l13_blockers_count=0))

    def test_negative_021_criteria_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(l13_criteria_count=0))

    def test_negative_022_documentary_link_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][11].update(l14_documentary_dependency_count=0))

    def test_negative_023_documentary_added(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][11].update(l14_documentary_projection_added=0))

    def test_negative_024_projection_only_false(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][11].update(projection_only_no_physical_change=False))

    def test_negative_025_anonymous_slot_true(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(anonymous_bookkeeping_slot=True))

    def test_negative_026_human_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][11].update(human_approved=True))

    def test_negative_027_native_authorized(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][44].update(native_qa_authorized=True))

    def test_negative_028_native_passed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][44].update(accepted_evidence=True))

    def test_negative_029_private_received(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][44].update(private_file_received=True))

    def test_negative_030_private_attached(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][0].update(attachment="private.zip"))

    def test_negative_031_r09_per_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][-1].update(l13_blockers_count=4))

    def test_negative_032_android_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][-1].update(platform="windows"))

    def test_negative_033_android_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][-1].update(readiness="READY"))

    def test_negative_034_android_native_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][-1].update(l14_documentary_dependency_count=25))

    def test_negative_035_report_anonymity(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][6].update(anonymous_bookkeeping_slot=False))

    def test_negative_036_report_fake_dependency(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][6].update(l14_documentary_projection_added=1))

    def test_negative_037_bcd_anonymity(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][31].update(anonymous_bookkeeping_slot=False))

    def test_negative_038_bcd_fake_link(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["records"][31].update(l14_documentary_dependency_count=1))

    def test_negative_039_group_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["group_summary"].pop())

    def test_negative_040_group_duplicated(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["group_summary"].append(copy.deepcopy(a["group_summary"][0])))

    def test_negative_041_group_reversed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["group_summary"].reverse())

    def test_negative_042_group_fake(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["group_summary"][0].update(kind="FAKE"))

    def test_negative_043_group_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["group_summary"][0].update(ready=1))

    def test_negative_044_group_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["group_summary"][0].update(actual_evidence_received=1))

    def test_negative_045_group_blocked(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["group_summary"][0].update(blocked=4))

    def test_negative_046_group_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["group_summary"][3].update(documentary_dependency_links=19))

    def test_negative_047_group_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["group_summary"][5].update(category_status="READY"))

    def test_negative_048_group_native_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["group_summary"][-1].update(requests=43))

    def test_negative_049_group_criterion_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["group_summary"][3].update(requests=21))

    def test_negative_050_category_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["change_categories"].pop())

    def test_negative_051_category_reversed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["change_categories"].reverse())

    def test_negative_052_category_identity_added(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["change_categories"][0].update(added=1))

    def test_negative_053_category_identity_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["change_categories"][0].update(removed=1))

    def test_negative_054_category_identity_drift(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["change_categories"][0].update(drift=1))

    def test_negative_055_category_priority_drift(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["change_categories"][1].update(drift=1))

    def test_negative_056_category_projection_wrong(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["change_categories"][2].update(observed=0))

    def test_negative_057_category_projection_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["change_categories"][2].update(added=1083))

    def test_negative_058_category_projection_fake_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["change_categories"][2].update(state="NATIVE_QA_COMPLETE"))

    def test_negative_059_category_real_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["change_categories"][3].update(observed=1))

    def test_negative_060_category_real_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["change_categories"][3].update(state="NATIVE_COMPLETE"))

    def test_negative_061_category_new(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["change_categories"].append(copy.deepcopy(a["change_categories"][0])))

    def test_negative_062_counts_comparisons(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(reported_comparisons=87))

    def test_negative_063_counts_matched(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(source_records_matched=87))

    def test_negative_064_counts_added(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(source_records_added=1))

    def test_negative_065_counts_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(source_records_removed=1))

    def test_negative_066_counts_reordered(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(source_records_reordered=1))

    def test_negative_067_counts_id_drift(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(id_drift_count=1))

    def test_negative_068_counts_priority_drift(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(priority_drift_count=1))

    def test_negative_069_counts_platform_drift(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(platform_drift_count=1))

    def test_negative_070_counts_status_drift(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(status_drift_count=1))

    def test_negative_071_counts_physical_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(physical_approval_change_count=1))

    def test_negative_072_counts_projection_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(l14_documentary_projection_links=0))

    def test_negative_073_counts_projection_fake(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(l14_metadata_projection_added=1000))

    def test_negative_074_counts_real_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(actual_evidence_received=1))

    def test_negative_075_counts_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(documentary_links_verified=1083))

    def test_negative_076_counts_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(native_completed=44))

    def test_negative_077_counts_human(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(human_approved=20))

    def test_negative_078_counts_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(local_reports=5))

    def test_negative_079_counts_bcd(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(phase_bcd_completed=13))

    def test_negative_080_counts_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(rows_ready=1))

    def test_negative_081_counts_anonymous(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["counts"].update(anonymous_rows_unassigned=17))

    def test_negative_082_priority_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["priority_rules"].pop())

    def test_negative_083_priority_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["priority_rules"][0].update(priority=4))

    def test_negative_084_gates_r07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["gates"].update(r07="APPROVED"))

    def test_negative_085_gates_r08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["gates"].update(r08="APPROVED"))

    def test_negative_086_gates_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["gates"].update(r09="APPROVED"))

    def test_negative_087_r09_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["global_r09"].update(status="APPROVED"))

    def test_negative_088_r09_added_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["global_r09"]["case_ids"].append("ball-TURTWIG"))

    def test_negative_089_r09_added_dep(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["global_r09"]["documentary_dependency_request_ids"].append("L13-NATIVE-ball-TURTWIG"))

    def test_negative_090_r09_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["global_r09"].update(approved=True))

    def test_negative_091_r09_global_flag(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["global_r09"].update(global_gate_only=False))

    def test_negative_092_r09_fake_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["global_r09"].update(id="R10"))

    def test_negative_093_platform_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["platform_partition"].reverse())

    def test_negative_094_platform_android_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["platform_partition"][1].update(requires_windows_b10_b11=True))

    def test_negative_095_platform_windows_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["platform_partition"][0].update(requires_windows_b10_b11=False))

    def test_negative_096_platform_android_authorized(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["platform_partition"][1].update(authorization=True))

    def test_negative_097_platform_windows_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["platform_partition"][0].update(native_approved=1))

    def test_negative_098_platform_native_complete(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["platform_partition"][0].update(native_completed=43))

    def test_negative_099_platform_windows_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["platform_partition"][0].update(native_requests=44))

    def test_negative_100_platform_android_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["platform_partition"][1]["case_ids"].__setitem__(0,"ball-TURTWIG"))

    def test_negative_101_policy_physical(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(zero_documentary_drift_does_not_mean_physical_approval=False))

    def test_negative_102_policy_projection(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(new_links_are_l14_projection_only=False))

    def test_negative_103_policy_priority(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(p0_p4_not_native_execution_order=False))

    def test_negative_104_policy_no_upload(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(no_uploads=False))

    def test_negative_105_policy_private(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(no_private_files=False))

    def test_negative_106_policy_saves(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(no_saves=False))

    def test_negative_107_policy_game(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(no_game_exe=False))

    def test_negative_108_policy_sandbox(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(no_windows_sandbox=False))

    def test_negative_109_policy_joiplay(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(no_joiplay=False))

    def test_negative_110_policy_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(asset_rights_not_approved=False))

    def test_negative_111_policy_mapids(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(mapids_not_reserved=False))

    def test_negative_112_policy_watch(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(watch_unchanged_not_global_save_isolation=False))

    def test_negative_113_policy_android(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(android_not_covered_by_windows_b10_b11=False))

    def test_negative_114_policy_playable(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(sinnoh_playable=True))

    def test_negative_115_policy_anonymous(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["policy"].update(anonymous_slots_unassigned=False))

    def test_negative_116_source_l13_sha(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["public_source_blobs"][0].update(git_blob_sha1="0"*40))

    def test_negative_117_source_l14_sha(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["public_source_blobs"][1].update(git_blob_sha1="0"*40))

    def test_negative_118_source_l13_path(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["public_source_blobs"][0].update(path="private/install.json"))

    def test_negative_119_source_l14_path(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["public_source_blobs"][1].update(path="private/assets.json"))

    def test_negative_120_source_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["public_source_blobs"].reverse())

    def test_negative_121_anchor_l07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["baseline_commits"].update(L07="0"*40))

    def test_negative_122_anchor_l08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["baseline_commits"].update(L08="0"*40))

    def test_negative_123_anchor_l09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["baseline_commits"].update(L09="0"*40))

    def test_negative_124_anchor_l10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["baseline_commits"].update(L10="0"*40))

    def test_negative_125_anchor_l11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["baseline_commits"].update(L11="0"*40))

    def test_negative_126_anchor_l12(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["baseline_commits"].update(L12="0"*40))

    def test_negative_127_anchor_l13(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["baseline_commits"].update(L13="0"*40))

    def test_negative_128_anchor_l14(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a["baseline_commits"].update(L14="0"*40))

    def test_negative_129_schema(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a.update(schema=2))

    def test_negative_130_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a.update(stage="L16"))

    def test_negative_131_version(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a.update(version=2))

    def test_negative_132_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a.update(status="NATIVE_APPROVED"))

    def test_negative_133_mode(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: a.update(mode="UPLOAD_PRIVATE"))

    def test_negative_134_mirror_approval(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: b["records"][0].update(human_approved=True))

    def test_negative_135_mirror_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: b["records"].pop())

    def test_negative_136_mirror_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: b["global_r09"].update(status="APPROVED"))

    def test_negative_137_matrix_l14_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: c["rows"][0].update(readiness="READY"))

    def test_negative_138_matrix_l14_mirror_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: d["rows"][0].update(readiness="READY"))

    def test_negative_139_queue_l13_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: e["queue"][0].update(status="APPROVED"))

    def test_negative_140_queue_l13_mirror_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: f["queue"][0].update(status="APPROVED"))

    def test_negative_141_report_l12_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: g["case_handoff"][0].update(native_qa_state="PASSED"))

    def test_negative_142_graph_l11_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: i["case_nodes"][0].update(native_qa_authorized=True))

    def test_negative_143_index_l10_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: k["cases"][0].update(approved=True))

    def test_negative_144_packet_l09_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa: m["case_handoff"][0].update(native_status="passed"))

if __name__ == '__main__':
    unittest.main()
