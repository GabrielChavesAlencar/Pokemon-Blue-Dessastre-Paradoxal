"""L14 deterministic blocked-only documentary dependency matrix tests."""
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
import audit_sinnoh_l14_readiness as l14
l13=l14.l13
l08=l13.l12.l11.l10.l09.l08

class SinnohL14ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read=l08.l07.l06.l05.l04.l03.l02.l00.read_json
        docs={stage:read(ROOT,path,maxsize=175000) for stage,path,_ in l08.PINNED}
        cls.items=[
            read(ROOT,l14.MATRIX,maxsize=180000),
            read(ROOT,l14.MIRROR,maxsize=180000),
            read(ROOT,l13.QUEUE,maxsize=190000),
            read(ROOT,l13.MIRROR,maxsize=190000),
            read(ROOT,l13.l12.REPORT,maxsize=145000),
            read(ROOT,l13.l12.MIRROR,maxsize=145000),
            read(ROOT,l13.l12.l11.GRAPH,maxsize=200000),
            read(ROOT,l13.l12.l11.MIRROR,maxsize=200000),
            read(ROOT,l13.l12.l11.l10.INDEX,maxsize=155000),
            read(ROOT,l13.l12.l11.l10.MIRROR,maxsize=155000),
            read(ROOT,l13.l12.l11.l10.l09.PACKET,maxsize=155000),
            read(ROOT,l08.SNAPSHOT,maxsize=125000),
            read(ROOT,l08.DIFF,maxsize=16000),
            docs["G12"],docs["L04"],docs["L05"],docs["L06"],
            docs["L07"],docs["L07_SITE"],
            l08.l07.run(ROOT),l08.l07.l06.run(ROOT),
            l08.l07.l06.l05.run(ROOT),
            l08.l07.l06.l05.l04.run(ROOT),
            l08.l07.l06.l05.G12.run(ROOT),
        ]

    def audited(self,change=None):
        items=[copy.deepcopy(x) for x in self.items]
        if change: change(*items)
        return l14.audit(*items)

    def rejected(self,change):
        with self.assertRaises(ValueError):
            self.audited(change)

    def test_01_l13_git_sha_and_L07_L13_anchors(self):
        self.assertTrue(l14.check_l13_public_blobs(ROOT))
        out=self.audited()
        self.assertEqual(out["status"],"PUBLIC_DOCUMENTARY_DEPENDENCIES_VALID_ALL_BLOCKED")
        self.assertEqual(out["source_l13_git_blob"],l14.L13_BLOB)
        self.assertEqual(out["baseline_commits"]["L13"],l14.L13_MERGE)
        self.assertEqual(len(out["baseline_commits"]),7)

    def test_02_exact_88_blocked_and_none_ready(self):
        out=self.audited()
        self.assertEqual((out["requests_total"],out["requests_pending"],out["requests_ready"]),(88,88,0))
        rows=self.items[0]["rows"]
        self.assertEqual([x["order"] for x in rows],list(range(1,89)))
        self.assertEqual(len(set(x["request_id"] for x in rows)),88)
        self.assertTrue(all(x["status"]=="PENDING" and x["readiness"]=="BLOCKED" for x in rows))

    def test_03_full_1084_public_links_exactly_pinned(self):
        report=self.audited()
        self.assertEqual((report["documentary_links"],report["case_to_criterion_links"],
           report["case_to_blocker_links"],report["criterion_to_blocker_links"]),(1084,846,218,20))
        self.assertEqual(sum(x["documentary_dependency_count"] for x in self.items[0]["rows"]),1084)
        self.assertTrue(all(x["documentary_dependency_count"]==len(x["documentary_dependency_request_ids"])
                            for x in self.items[0]["rows"]))

    def test_04_no_invented_slots_dependencies_or_permission(self):
        rows=self.items[0]["rows"]
        anon=[x for x in rows if x["anonymous_bookkeeping_slot"]]
        self.assertEqual(len(anon),18)
        self.assertTrue(all(not x["documentary_dependency_request_ids"] for x in anon))
        self.assertTrue(all(not x["scope_known"] for x in anon))
        self.assertTrue(all(not x["physical_evidence_received"] and not x["human_approval"]
                            and not x["native_qa_authorized"] for x in rows))

    def test_05_platform_separation_and_global_R09(self):
        report=self.audited()
        self.assertEqual((report["windows_native_pending"],report["android_native_pending"]),(43,1))
        self.assertTrue(report["r09_global_only"])
        self.assertEqual(self.items[0]["global_r09"]["dependency_request_ids"],[])
        self.assertFalse(any("L13-GLOBAL-R09" in x["documentary_dependency_request_ids"]
                             for x in self.items[0]["rows"]))
        native=[x for x in self.items[0]["rows"] if x["kind"]=="NATIVE_CASE"]
        self.assertEqual(len(native),44)
        self.assertEqual(native[-1]["platform"],"android")
        self.assertNotIn("L13-BLOCKER-B10",native[-1]["documentary_dependency_request_ids"])
        self.assertNotIn("L13-BLOCKER-B11",native[-1]["documentary_dependency_request_ids"])

    def test_06_no_change_in_native_human_bcd_or_mapid_gates(self):
        out=self.audited()
        self.assertEqual((out["local_reports_received"],out["human_criteria_approved"],
                          out["native_executed"],out["native_approved"],
                          out["phase_bcd_approved"]),(0,0,0,0,0))
        self.assertEqual(out["phase_bcd_total"],13)
        self.assertTrue(out["r07_pending"] and out["r08_pending"] and out["r09_pending"])
        self.assertFalse(out["sinnoh_playable"])

    def test_07_mirror_strictly_equals_pure_projection(self):
        same=l13.l12.l11.l10.l09.l08.l07.l06.same
        self.assertTrue(same(self.items[0],self.items[1]))
        self.assertTrue(same(self.items[0],l14.expected_matrix(self.items[2])))

    def test_08_public_blob_mutation_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-l14-public-") as td:
            root=Path(td)
            for rel in (l13.QUEUE,l13.MIRROR):
                dst=root/rel
                dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/rel,dst)
            self.assertTrue(l14.check_l13_public_blobs(root))
            p=root/l13.QUEUE
            p.write_bytes(p.read_bytes()+b" ")
            with self.assertRaises(ValueError):
                l14.check_l13_public_blobs(root)

    def test_09_cli_fixed_paths_and_no_untrusted_echo(self):
        cmd=[sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l14_readiness.py")]
        good=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(json.loads(good.stdout)["requests_total"],88)
        bad=subprocess.run(cmd+["--save",r"C:\\Users\\User\\Save01.rxdata"],
                           cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(bad.returncode,2)
        self.assertIn("SINNOH_L14_BLOCKED",bad.stderr)
        self.assertNotIn("Save01.rxdata",bad.stdout+bad.stderr)

    def test_10_no_runtime_network_or_private_file_discovery(self):
        source=(ROOT/"scripts/regions/audit_sinnoh_l14_readiness.py").read_text("utf8")
        for bad in ("import requests","import subprocess","import socket",
                    "os.walk(","rglob(","os.system(","subprocess.run(",
                    "shutil.copy(","from urllib","httpx","os.environ"):
            self.assertNotIn(bad,source)

    def test_negative_001_row_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"].pop())

    def test_negative_002_duplicate_row(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"].append(copy.deepcopy(a["rows"][0])))

    def test_negative_003_reorder_rows(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"].reverse())

    def test_negative_004_fake_request_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(request_id="L13-FAKE"))

    def test_negative_005_duplicate_request_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][1].update(request_id=a["rows"][0]["request_id"]))

    def test_negative_006_order_zero(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(order=0))

    def test_negative_007_priority_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(priority=4))

    def test_negative_008_priority_label(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(priority_label="NATIVE_READY"))

    def test_negative_009_kind_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(kind="NATIVE_CASE"))

    def test_negative_010_subject_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(subject_id="NEW"))

    def test_negative_011_platform_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(platform="android"))

    def test_negative_012_dependency_on_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0]["documentary_dependency_request_ids"].append("L13-BLOCKER-B10"))

    def test_negative_013_dependency_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(documentary_dependency_count=1))

    def test_negative_014_dependency_interpretation(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(dependency_interpretation="NATIVE_APPROVED"))

    def test_negative_015_scope_known(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(scope_known=False))

    def test_negative_016_anonymous_slot_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(anonymous_bookkeeping_slot=True))

    def test_negative_017_readiness_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(readiness="READY"))

    def test_negative_018_status_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(status="APPROVED"))

    def test_negative_019_human_approval(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(human_approval=True))

    def test_negative_020_physical_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(physical_evidence_received=True))

    def test_negative_021_native_authorized(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(native_qa_authorized=True))

    def test_negative_022_private_allowed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(private_submission_allowed=True))

    def test_negative_023_add_private_field(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][0].update(save_file="save01"))

    def test_negative_024_human_missing_dependency(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][11]["documentary_dependency_request_ids"].pop())

    def test_negative_025_human_invalid_dependency(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][11]["documentary_dependency_request_ids"].__setitem__(0,"L13-GLOBAL-R09"))

    def test_negative_026_native_missing_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][44]["documentary_dependency_request_ids"].pop())

    def test_negative_027_native_wrong_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][44]["documentary_dependency_request_ids"].__setitem__(0,"L13-GLOBAL-R09"))

    def test_negative_028_native_reverse_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][44]["documentary_dependency_request_ids"].reverse())

    def test_negative_029_native_fake_link(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][44]["documentary_dependency_request_ids"].append("L13-FAKE"))

    def test_negative_030_native_fake_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][44].update(documentary_dependency_count=0))

    def test_negative_031_android_windows_b10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][-1]["documentary_dependency_request_ids"].append("L13-BLOCKER-B10"))

    def test_negative_032_android_windows_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][-1]["documentary_dependency_request_ids"].append("L13-BLOCKER-B11"))

    def test_negative_033_android_windows_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][-1].update(platform="windows"))

    def test_negative_034_report_anonymous_false(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][6].update(anonymous_bookkeeping_slot=False))

    def test_negative_035_report_fake_dependency(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][6]["documentary_dependency_request_ids"].append("L13-NATIVE-ball-TURTWIG"))

    def test_negative_036_report_fake_scope(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][6].update(scope_known=True))

    def test_negative_037_bcd_fake_dependency(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][31]["documentary_dependency_request_ids"].append("L13-BLOCKER-B09"))

    def test_negative_038_bcd_false_scope(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["rows"][31].update(scope_known=True))

    def test_negative_039_counts_rows(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(readiness_rows=87))

    def test_negative_040_counts_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(rows_ready=1))

    def test_negative_041_counts_blocked(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(rows_blocked=87))

    def test_negative_042_counts_pending(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(rows_pending=0))

    def test_negative_043_counts_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(request_documentary_links=1083))

    def test_negative_044_counts_c2c(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(case_to_criterion_request_links=845))

    def test_negative_045_counts_c2b(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(case_to_blocker_request_links=219))

    def test_negative_046_counts_cr2b(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(criterion_to_blocker_request_links=21))

    def test_negative_047_counts_anonymous(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(anonymous_rows_unassigned=17))

    def test_negative_048_counts_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(native_approved=1))

    def test_negative_049_counts_human(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(human_approved=1))

    def test_negative_050_counts_local(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(local_reports=5))

    def test_negative_051_counts_bcd(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(phase_bcd_completed=13))

    def test_negative_052_counts_total_requests(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["counts"].update(evidence_requests_total=89))

    def test_negative_053_gates_r07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["gates"].update(r07="APPROVED"))

    def test_negative_054_gates_r08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["gates"].update(r08="APPROVED"))

    def test_negative_055_gates_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["gates"].update(r09="APPROVED"))

    def test_negative_056_r09_case_added(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["global_r09"]["case_ids"].append("ball-TURTWIG"))

    def test_negative_057_r09_dependency_added(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["global_r09"]["dependency_request_ids"].append("L13-NATIVE-ball-TURTWIG"))

    def test_negative_058_r09_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["global_r09"].update(status="APPROVED"))

    def test_negative_059_r09_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["global_r09"].update(readiness="READY"))

    def test_negative_060_r09_flag(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["global_r09"].update(not_case_scoped=False))

    def test_negative_061_platform_win_authorized(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["platform_partition"][0].update(authorization=True))

    def test_negative_062_platform_android_authorized(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["platform_partition"][1].update(authorization=True))

    def test_negative_063_platform_win_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["platform_partition"][0].update(readiness="READY"))

    def test_negative_064_platform_android_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["platform_partition"][1].update(readiness="READY"))

    def test_negative_065_platform_android_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["platform_partition"][1].update(requires_windows_sandbox_b10_b11=True))

    def test_negative_066_platform_win_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["platform_partition"][0].update(requires_windows_sandbox_b10_b11=False))

    def test_negative_067_platform_android_complete(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["platform_partition"][1].update(native_completed=1))

    def test_negative_068_platform_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["platform_partition"].reverse())

    def test_negative_069_semantics_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["dependency_semantics"].update(links_are_documentary_only=False))

    def test_negative_070_semantics_priority(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["dependency_semantics"].update(priority_is_not_execution_order=False))

    def test_negative_071_semantics_anonymous(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["dependency_semantics"].update(no_derived_dependencies_for_anonymous_slots=False))

    def test_negative_072_semantics_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["dependency_semantics"].update(no_r09_per_case_links=False))

    def test_negative_073_semantics_auth(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["dependency_semantics"].update(readiness_never_infers_auth=False))

    def test_negative_074_semantics_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["dependency_semantics"].update(readiness_state="READY"))

    def test_negative_075_disclaimer_game(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["disclaimer"].update(no_game_execution=False))

    def test_negative_076_disclaimer_joiplay(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["disclaimer"].update(no_joiplay_execution=False))

    def test_negative_077_disclaimer_windows(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["disclaimer"].update(no_windows_sandbox_execution=False))

    def test_negative_078_disclaimer_upload(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["disclaimer"].update(no_upload_or_attachments=False))

    def test_negative_079_disclaimer_save(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["disclaimer"].update(no_local_paths_or_saves=False))

    def test_negative_080_disclaimer_isolation(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["disclaimer"].update(watch_unchanged_is_not_global_save_isolation=False))

    def test_negative_081_disclaimer_mapid(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["disclaimer"].update(mapids_not_reserved=False))

    def test_negative_082_disclaimer_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["disclaimer"].update(asset_rights_not_approved=False))

    def test_negative_083_disclaimer_playable(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["disclaimer"].update(sinnoh_playable=True))

    def test_negative_084_disclaimer_none_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["disclaimer"].update(none_ready=False))

    def test_negative_085_disclaimer_physical(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["disclaimer"].update(none_physically_approved=False))

    def test_negative_086_priority_rule_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["priority_rules"].pop())

    def test_negative_087_priority_rule_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["priority_rules"].reverse())

    def test_negative_088_priority_rule_code(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["priority_rules"][0].update(code="P0_READY"))

    def test_negative_089_priority_version(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a.update(priority_rule_version=2))

    def test_negative_090_baseline_l07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["baseline_commits"].update(L07="0"*40))

    def test_negative_091_baseline_l08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["baseline_commits"].update(L08="0"*40))

    def test_negative_092_baseline_l09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["baseline_commits"].update(L09="0"*40))

    def test_negative_093_baseline_l10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["baseline_commits"].update(L10="0"*40))

    def test_negative_094_baseline_l11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["baseline_commits"].update(L11="0"*40))

    def test_negative_095_baseline_l12(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["baseline_commits"].update(L12="0"*40))

    def test_negative_096_baseline_l13(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["baseline_commits"].update(L13="0"*40))

    def test_negative_097_source_blob(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["source_l13"].update(git_blob_sha1="0"*40))

    def test_negative_098_source_path(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a["source_l13"].update(path="private/path.json"))

    def test_negative_099_schema(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a.update(schema=2))

    def test_negative_100_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a.update(stage="L15"))

    def test_negative_101_version(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a.update(version=2))

    def test_negative_102_mode(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a.update(mode="UPLOAD"))

    def test_negative_103_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: a.update(status="NATIVE_APPROVED"))

    def test_negative_104_mirror_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: b["rows"][0].update(readiness="READY"))

    def test_negative_105_mirror_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: b["rows"].pop())

    def test_negative_106_mirror_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: b["global_r09"].update(readiness="READY"))

    def test_negative_107_parent_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: c["queue"][-1].update(native_qa_authorized=True))

    def test_negative_108_parent_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: d["queue"][-1].update(status="PASSED"))

    def test_negative_109_l12_false_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: e["case_handoff"][0].update(native_qa_state="PASSED"))

    def test_negative_110_l12_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: f["case_handoff"][0].update(id="FAKE"))

    def test_negative_111_l11_false_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: g["case_nodes"][0].update(native_qa_authorized=True))

    def test_negative_112_l11_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: h["case_nodes"][0].update(id="FAKE"))

    def test_negative_113_l10_false_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: i["cases"][0].update(approved=True))

    def test_negative_114_l10_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: j["cases"][0].update(id="FAKE"))

    def test_negative_115_l09_false_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: k["case_handoff"][0].update(native_status="passed"))

    def test_negative_116_l08_snapshot(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: l["cases"][0].update(native_qa_authorized=True))

    def test_negative_117_l08_diff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: m["comparisons"][0]["added_ids"].append("FAKE"))

    def test_negative_118_g12_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: n["cases"][0].update(native_status="passed"))

    def test_negative_119_l04_signoff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: o["rows"][0]["criteria"][0].update(local_human_signoff=True))

    def test_negative_120_l05_reserved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: p.update(mapids_reserved=True))

    def test_negative_121_l06_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: q.update(asset_rights_approved=True))

    def test_negative_122_l07_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: s["cases"][-1].update(platform="windows"))

    def test_negative_123_l07_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: t["cases"][0].update(id="FAKE"))

    def test_negative_124_l07_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: u["counts"].update(native_approved=1))

    def test_negative_125_l06_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: v.update(native_cases_approved=1))

    def test_negative_126_l05_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: w.update(native_cases_approved=1))

    def test_negative_127_l04_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: x.update(criteria_reviewed=1))

    def test_negative_128_g12_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y: y.update(evidence_accepted_cases=1))

if __name__ == '__main__':
    unittest.main()
