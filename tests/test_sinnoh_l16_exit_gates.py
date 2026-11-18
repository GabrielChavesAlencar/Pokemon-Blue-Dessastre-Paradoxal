"""L16: immutable public-document exit gate tests; never native approval."""
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
import audit_sinnoh_l16_exit_gates as l16
l15=l16.l15
l08=l15.l14.l13.l12.l11.l10.l09.l08

class SinnohL16PublicExitGatesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read=l08.l07.l06.l05.l04.l03.l02.l00.read_json
        src={k:read(ROOT,p,maxsize=175000) for k,p,_ in l08.PINNED}
        cls.items=[
            read(ROOT,l16.MATRIX,maxsize=185000),
            read(ROOT,l16.MIRROR,maxsize=185000),
            read(ROOT,l15.REPORT,maxsize=145000),
            read(ROOT,l15.MIRROR,maxsize=145000),
            read(ROOT,l15.l14.MATRIX,maxsize=180000),
            read(ROOT,l15.l14.MIRROR,maxsize=180000),
            read(ROOT,l15.l14.l13.QUEUE,maxsize=190000),
            read(ROOT,l15.l14.l13.MIRROR,maxsize=190000),
            read(ROOT,l15.l14.l13.l12.REPORT,maxsize=145000),
            read(ROOT,l15.l14.l13.l12.MIRROR,maxsize=145000),
            read(ROOT,l15.l14.l13.l12.l11.GRAPH,maxsize=200000),
            read(ROOT,l15.l14.l13.l12.l11.MIRROR,maxsize=200000),
            read(ROOT,l15.l14.l13.l12.l11.l10.INDEX,maxsize=155000),
            read(ROOT,l15.l14.l13.l12.l11.l10.MIRROR,maxsize=155000),
            read(ROOT,l15.l14.l13.l12.l11.l10.l09.PACKET,maxsize=155000),
            read(ROOT,l08.SNAPSHOT,maxsize=125000),
            read(ROOT,l08.DIFF,maxsize=16000),
            src["G12"],src["L04"],src["L05"],src["L06"],
            src["L07"],src["L07_SITE"],
            l08.l07.run(ROOT),l08.l07.l06.run(ROOT),
            l08.l07.l06.l05.run(ROOT),
            l08.l07.l06.l05.l04.run(ROOT),
            l08.l07.l06.l05.G12.run(ROOT),
        ]

    def audited(self,mutation=None):
        parts=[copy.deepcopy(x) for x in self.items]
        if mutation: mutation(*parts)
        return l16.audit(*parts)

    def rejected(self,mutation):
        with self.assertRaises(ValueError):
            self.audited(mutation)

    def test_01_all_public_source_blobs_and_anchors_pinned(self):
        self.assertTrue(l16.check_public_blobs(ROOT))
        result=self.audited()
        self.assertEqual(result["status"],"PUBLIC_EXIT_GATES_VALID_ALL_UNMET")
        self.assertEqual(result["baseline_commits"]["L15"],l16.L15_MERGE)
        self.assertEqual(result["public_sources"],[
            {"stage":k,"path":p,"git_blob_sha1":sha} for k,p,sha,_ in l16.PINNED])
        self.assertEqual(len(result["baseline_commits"]),9)

    def test_02_all_88_requests_remain_pending_blocked(self):
        d=self.items[0]
        self.assertEqual(len(d["records"]),88)
        self.assertEqual([x["order"] for x in d["records"]],list(range(1,89)))
        self.assertEqual(len({x["request_id"] for x in d["records"]}),88)
        self.assertTrue(all(x["status"]=="PENDING" and x["readiness"]=="BLOCKED"
          and x["exit_criteria_met"] is False and x["action_authorization"]=="NONE"
          for x in d["records"]))

    def test_03_exact_documentary_links_anonymous_slots(self):
        d=self.items[0]
        self.assertEqual(sum(x["documentary_dependency_count"] for x in d["records"]),1084)
        slots=[x for x in d["records"] if x["anonymous_bookkeeping_slot"]]
        self.assertEqual(len(slots),18)
        self.assertTrue(all(not x["documentary_dependency_request_ids"] and
          not x["linked_l04_criterion_ids"] for x in slots))
        self.assertEqual(d["counts"]["exit_ready"],0)

    def test_04_R09_is_global_no_native_or_case_links(self):
        d=self.items[0]
        r09=d["records"][5]
        self.assertEqual(r09["kind"],"GLOBAL_REGIONAL_GATE")
        self.assertEqual(r09["prerequisite_blocker_ids"],["R09"])
        self.assertFalse(r09["documentary_dependency_request_ids"])
        self.assertFalse(r09["linked_l04_criterion_ids"])
        self.assertEqual(d["global_r09"]["case_ids"],[])
        self.assertEqual(d["global_r09"]["documentary_dependency_request_ids"],[])
        self.assertFalse(any("R09" in x["prerequisite_blocker_ids"] for x in d["records"] if x["kind"]=="NATIVE_CASE"))

    def test_05_windows_android_independent_physical_gate(self):
        d=self.items[0]
        p=d["platform_partition"]
        self.assertEqual([(x["platform"],x["native_requests"]) for x in p],[("windows",43),("android",1)])
        self.assertTrue(p[0]["requires_windows_b10_b11"])
        self.assertFalse(p[1]["requires_windows_b10_b11"])
        self.assertEqual(p[1]["exit_met"],0)
        self.assertFalse(p[1]["native_authorization"])
        android=d["records"][-1]
        self.assertEqual(android["platform"],"android")
        self.assertNotIn("B10",android["prerequisite_blocker_ids"])
        self.assertNotIn("B11",android["prerequisite_blocker_ids"])

    def test_06_gates_and_real_evidence_zero(self):
        r=self.audited()
        self.assertEqual((r["requests_total"],r["requests_blocked"],r["exit_criteria_met"]),(88,88,0))
        self.assertEqual((r["local_reports_received"],r["human_approved"],r["native_executed"],
                          r["native_approved"],r["phase_bcd_approved"]),(0,0,0,0,0))
        self.assertTrue(r["r07_pending"] and r["r08_pending"] and r["r09_pending"])
        self.assertTrue(r["no_private_uploads"] and r["no_native_authorization"])
        self.assertFalse(r["sinnoh_playable"])

    def test_07_derived_strictly_from_L13_L14_L15(self):
        same=l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.same
        expected=l16.expected_matrix(self.items[6],self.items[4],self.items[2])
        self.assertTrue(same(self.items[0],expected))
        self.assertTrue(same(self.items[1],expected))

    def test_08_synthetic_public_blob_change_rejected(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-l16-public-") as td:
            root=Path(td)
            for _stage,p,_sha,mirror in l16.PINNED:
                for f in (p,mirror):
                    dest=root/f
                    dest.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copyfile(ROOT/f,dest)
            self.assertTrue(l16.check_public_blobs(root))
            p=root/l15.MIRROR
            p.write_bytes(p.read_bytes()+b" ")
            with self.assertRaises(ValueError):
                l16.check_public_blobs(root)

    def test_09_cli_fails_closed_and_never_echoes_private_paths(self):
        cmd=[sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l16_exit_gates.py")]
        good=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(json.loads(good.stdout)["requests_total"],88)
        bad=subprocess.run(cmd+["--save","C:/private/Save01.rxdata"],
                           cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(bad.returncode,2)
        self.assertIn("SINNOH_L16_BLOCKED",bad.stderr)
        self.assertNotIn("Save01.rxdata",bad.stderr+bad.stdout)

    def test_10_auditor_no_network_or_runtime_side_effects(self):
        src=(ROOT/"scripts/regions/audit_sinnoh_l16_exit_gates.py").read_text("utf8")
        for disallowed in ("import requests","import subprocess","import socket","os.walk(",
                           "rglob(","os.system(","subprocess.run(","shutil.copy(",
                           "from urllib","httpx","os.environ"):
            self.assertNotIn(disallowed,src)

    def test_negative_001_missing_row(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"].pop())

    def test_negative_002_duplicate_row(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"].append(copy.deepcopy(a["records"][0])))

    def test_negative_003_reverse_rows(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"].reverse())

    def test_negative_004_fake_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0].update(request_id="FAKE"))

    def test_negative_005_duplicate_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][1].update(request_id=a["records"][0]["request_id"]))

    def test_negative_006_wrong_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0].update(order=0))

    def test_negative_007_wrong_subject(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0].update(subject_id="R09"))

    def test_negative_008_wrong_kind(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0].update(kind="NATIVE_CASE"))

    def test_negative_009_wrong_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0].update(platform="android"))

    def test_negative_010_wrong_priority(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0].update(priority=3))

    def test_negative_011_wrong_priority_label(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0].update(priority_label="P4_NATIVE"))

    def test_negative_012_removed_link(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][11]["documentary_dependency_request_ids"].pop())

    def test_negative_013_extra_link(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][11]["documentary_dependency_request_ids"].append("L13-GLOBAL-R09"))

    def test_negative_014_fake_link_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][11].update(documentary_dependency_count=9))

    def test_negative_015_add_r09_link(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][-1]["documentary_dependency_request_ids"].append("L13-GLOBAL-R09"))

    def test_negative_016_android_b10_link(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][-1]["documentary_dependency_request_ids"].append("L13-BLOCKER-B10"))

    def test_negative_017_android_b11_gate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][-1]["prerequisite_blocker_ids"].append("B11"))

    def test_negative_018_wrong_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0]["prerequisite_blocker_ids"].append("R09"))

    def test_negative_019_wrong_criterion(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][11]["linked_l04_criterion_ids"].append("FAKE"))

    def test_negative_020_remove_criterion(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][11]["linked_l04_criterion_ids"].pop())

    def test_negative_021_reverse_criteria(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][-1]["linked_l04_criterion_ids"].reverse())

    def test_negative_022_missing_exit_code(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0]["exit_criteria_codes"].pop())

    def test_negative_023_extra_exit_code(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0]["exit_criteria_codes"].append("NATIVE_APPROVED"))

    def test_negative_024_exit_code_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0]["exit_criteria_codes"].reverse())

    def test_negative_025_change_description(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0].update(criterion_description="Aprovado"))

    def test_negative_026_anonymous_slot_change(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][6].update(anonymous_bookkeeping_slot=False))

    def test_negative_027_anonymous_scope(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][6].update(scope_known=True))

    def test_negative_028_anonymous_new_link(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][6]["documentary_dependency_request_ids"].append("L13-BLOCKER-B09"))

    def test_negative_029_r09_add_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][5]["linked_l04_criterion_ids"].append("B09_ORIGIN"))

    def test_negative_030_r09_fake_dep(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][5]["documentary_dependency_request_ids"].append("L13-HUMAN-B09_ORIGIN"))

    def test_negative_031_r09_fake_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][5]["prerequisite_blocker_ids"].append("B11"))

    def test_negative_032_documentary_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0].update(documentary_check="NATIVE_APPROVED"))

    def test_negative_033_physical_verified(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][0].update(physical_source_verified=True))

    def test_negative_034_human_reviewed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][11].update(human_review_completed=True))

    def test_negative_035_physical_received(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][44].update(physical_evidence_received=True))

    def test_negative_036_native_authorized(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][44].update(native_execution_approved=True))

    def test_negative_037_exit_met(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][44].update(exit_criteria_met=True))

    def test_negative_038_readiness_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][44].update(readiness="READY"))

    def test_negative_039_status_passed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][44].update(status="PASSED"))

    def test_negative_040_action_authorized(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][44].update(action_authorization="EXECUTE_GAME"))

    def test_negative_041_extra_private_path(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["records"][44].update(private_file="Save01.rxdata"))

    def test_negative_042_exit_codes_template_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["exit_code_templates"].pop())

    def test_negative_043_exit_codes_template_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["exit_code_templates"].reverse())

    def test_negative_044_exit_codes_template_new_kind(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["exit_code_templates"][0].update(kind="FAKE"))

    def test_negative_045_exit_codes_template_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["exit_code_templates"][0]["exit_criteria_codes"].append("NATIVE_READY"))

    def test_negative_046_exit_criteria_version(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a.update(exit_criteria_version=2))

    def test_negative_047_group_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["group_summary"].pop())

    def test_negative_048_group_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["group_summary"].reverse())

    def test_negative_049_group_wrong_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["group_summary"][5].update(requests=43))

    def test_negative_050_group_passed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["group_summary"][0].update(criteria_met=1))

    def test_negative_051_group_signoff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["group_summary"][3].update(physical_signoffs=1))

    def test_negative_052_group_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["group_summary"][5].update(documentary_links=1))

    def test_negative_053_group_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["group_summary"][5].update(state="READY"))

    def test_negative_054_count_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(exit_ready=1))

    def test_negative_055_count_blocked(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(exit_blocked=87))

    def test_negative_056_count_rows(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(exit_rows=87))

    def test_negative_057_count_criteria_met(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(exit_criteria_met=1))

    def test_negative_058_count_human_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(human_approved=20))

    def test_negative_059_count_native_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(native_approved=44))

    def test_negative_060_count_native_executed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(native_completed=44))

    def test_negative_061_count_reports(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(local_reports=5))

    def test_negative_062_count_bcd(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(phase_bcd_completed=13))

    def test_negative_063_count_anonymous(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(anonymous_unassigned=17))

    def test_negative_064_count_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(documentary_link_count=1083))

    def test_negative_065_count_global(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(global_r09_pending=0))

    def test_negative_066_count_human_pending(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(required_human_reviews_pending=19))

    def test_negative_067_count_native_pending(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(required_native_cases_pending=43))

    def test_negative_068_count_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["counts"].update(physical_evidence_accepted=1))

    def test_negative_069_r07_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["gates"].update(r07="APPROVED"))

    def test_negative_070_r08_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["gates"].update(r08="APPROVED"))

    def test_negative_071_r09_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["gates"].update(r09="APPROVED"))

    def test_negative_072_global_r09_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["global_r09"].update(approval=True))

    def test_negative_073_global_r09_met(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["global_r09"].update(exit_met=True))

    def test_negative_074_global_r09_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["global_r09"].update(status="APPROVED"))

    def test_negative_075_global_r09_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["global_r09"].update(id="R10"))

    def test_negative_076_global_r09_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["global_r09"]["case_ids"].append("ball-TURTWIG"))

    def test_negative_077_global_r09_dependency(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["global_r09"]["documentary_dependency_request_ids"].append("L13-NATIVE-ball-TURTWIG"))

    def test_negative_078_global_r09_scoped(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["global_r09"].update(global_gate_only=False))

    def test_negative_079_platform_android_inherits_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["platform_partition"][1].update(requires_windows_b10_b11=True))

    def test_negative_080_platform_windows_loses_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["platform_partition"][0].update(requires_windows_b10_b11=False))

    def test_negative_081_platform_android_authorized(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["platform_partition"][1].update(native_authorization=True))

    def test_negative_082_platform_windows_complete(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["platform_partition"][0].update(native_completed=43))

    def test_negative_083_platform_exit(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["platform_partition"][0].update(exit_met=43))

    def test_negative_084_platform_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["platform_partition"][0].update(exit_state="READY"))

    def test_negative_085_platform_swap(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["platform_partition"].reverse())

    def test_negative_086_policy_upload(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(no_uploads=False))

    def test_negative_087_policy_game(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(no_game_exe=False))

    def test_negative_088_policy_sandbox(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(no_windows_sandbox=False))

    def test_negative_089_policy_joiplay(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(no_joiplay=False))

    def test_negative_090_policy_saves(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(no_saves=False))

    def test_negative_091_policy_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(asset_rights_not_approved=False))

    def test_negative_092_policy_mapids(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(mapids_not_reserved=False))

    def test_negative_093_policy_watch(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(watch_unchanged_not_global_save_isolation=False))

    def test_negative_094_policy_playable(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(sinnoh_playable=True))

    def test_negative_095_policy_global(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(r09_is_global_not_case_scoped=False))

    def test_negative_096_policy_anonymous(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(anonymous_slots_not_mapped=False))

    def test_negative_097_policy_priority(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(priority_is_not_native_execution_order=False))

    def test_negative_098_policy_physical(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(links_do_not_authenticate_physical_evidence=False))

    def test_negative_099_policy_human(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(human_criteria_approved=True))

    def test_negative_100_policy_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["policy"].update(native_cases_executed=True))

    def test_negative_101_source_l15_sha(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["public_sources"][2].update(git_blob_sha1="0"*40))

    def test_negative_102_source_l14_sha(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["public_sources"][1].update(git_blob_sha1="0"*40))

    def test_negative_103_source_l13_sha(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["public_sources"][0].update(git_blob_sha1="0"*40))

    def test_negative_104_source_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["public_sources"].reverse())

    def test_negative_105_source_private(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["public_sources"][2].update(path="C:/private/save.rxdata"))

    def test_negative_106_commit_l07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["baseline_commits"].update(L07="0"*40))

    def test_negative_107_commit_l08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["baseline_commits"].update(L08="0"*40))

    def test_negative_108_commit_l09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["baseline_commits"].update(L09="0"*40))

    def test_negative_109_commit_l10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["baseline_commits"].update(L10="0"*40))

    def test_negative_110_commit_l11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["baseline_commits"].update(L11="0"*40))

    def test_negative_111_commit_l12(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["baseline_commits"].update(L12="0"*40))

    def test_negative_112_commit_l13(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["baseline_commits"].update(L13="0"*40))

    def test_negative_113_commit_l14(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["baseline_commits"].update(L14="0"*40))

    def test_negative_114_commit_l15(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a["baseline_commits"].update(L15="0"*40))

    def test_negative_115_schema(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a.update(schema=2))

    def test_negative_116_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a.update(stage="L17"))

    def test_negative_117_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a.update(status="NATIVE_READY"))

    def test_negative_118_mode(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a.update(mode="UPLOAD_PRIVATE"))

    def test_negative_119_version(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: a.update(version=2))

    def test_negative_120_mirror_approval(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: b["records"][0].update(human_review_completed=True))

    def test_negative_121_mirror_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: b["records"].pop())

    def test_negative_122_l15_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: c["records"][-1].update(native_qa_authorized=True))

    def test_negative_123_l15_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: d["records"][0].update(accepted_evidence=True))

    def test_negative_124_l14_ready(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: e["rows"][0].update(readiness="READY"))

    def test_negative_125_l14_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: f["rows"][0].update(readiness="READY"))

    def test_negative_126_l13_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: g["queue"][0].update(status="APPROVED"))

    def test_negative_127_l13_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: h["queue"][0].update(status="APPROVED"))

    def test_negative_128_l12_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: i["case_handoff"][0].update(native_qa_state="PASSED"))

    def test_negative_129_l11_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: k["case_nodes"][0].update(native_qa_authorized=True))

    def test_negative_130_l10_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w,x,y,z,aa,ab,ac: m["cases"][0].update(approved=True))

if __name__ == '__main__':
    unittest.main()
