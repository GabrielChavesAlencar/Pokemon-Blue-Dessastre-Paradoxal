"""L13 public metadata request queue strict tests (no physical receipt intake)."""
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
import audit_sinnoh_l13_public_queue as l13
l12=l13.l12
l11=l12.l11
l08=l11.l10.l09.l08

class SinnohL13PublicQueueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read=l08.l07.l06.l05.l04.l03.l02.l00.read_json
        docs={stage:read(ROOT,path,maxsize=175000) for stage,path,_ in l08.PINNED}
        cls.items=[
            read(ROOT,l13.QUEUE,maxsize=190000),
            read(ROOT,l13.MIRROR,maxsize=190000),
            read(ROOT,l12.REPORT,maxsize=145000),
            read(ROOT,l12.MIRROR,maxsize=145000),
            read(ROOT,l11.GRAPH,maxsize=200000),
            read(ROOT,l11.MIRROR,maxsize=200000),
            read(ROOT,l11.l10.INDEX,maxsize=155000),
            read(ROOT,l11.l10.MIRROR,maxsize=155000),
            read(ROOT,l11.l10.l09.PACKET,maxsize=155000),
            read(ROOT,l08.SNAPSHOT,maxsize=125000),
            read(ROOT,l08.DIFF,maxsize=16000),
            docs["G12"],docs["L04"],docs["L05"],docs["L06"],
            docs["L07"],docs["L07_SITE"],
            l08.l07.run(ROOT),l08.l07.l06.run(ROOT),
            l08.l07.l06.l05.run(ROOT),
            l08.l07.l06.l05.l04.run(ROOT),
            l08.l07.l06.l05.G12.run(ROOT),
        ]

    def audited(self,mutate=None):
        entries=[copy.deepcopy(x) for x in self.items]
        if mutate is not None:
            mutate(*entries)
        return l13.audit(*entries)

    def rejected(self,mutate):
        with self.assertRaises(ValueError):
            self.audited(mutate)

    def test_01_pinned_l12_public_blobs_and_anchors(self):
        self.assertTrue(l13.check_l12_public_blobs(ROOT))
        result=self.audited()
        self.assertEqual(result["status"],"PUBLIC_QUEUE_AUDITED_ALL_REQUESTS_PENDING")
        self.assertEqual(result["baseline_commits"]["L12"],l13.L12_MERGE)
        self.assertEqual(result["source_l12_git_blob"],l13.L12_BLOB)
        self.assertEqual(len(result["baseline_commits"]),6)

    def test_02_88_request_counts_and_priority_order(self):
        r=self.audited()
        self.assertEqual(r["request_counts"],{
            "evidence_requests_total":88,
            "blocker_requests":5,"global_gate_requests":1,
            "report_slots":5,"human_criterion_requests":20,
            "bcd_slots":13,"native_case_requests":44,
            "requests_pending":88,"requests_approved":0,
        })
        items=self.items[0]["queue"]
        self.assertEqual([x["order"] for x in items],list(range(1,89)))
        self.assertEqual([x["priority"] for x in items],sorted(x["priority"] for x in items))
        self.assertEqual(len(set(x["request_id"] for x in items)),88)

    def test_03_real_44_cases_and_20_criteria_stay_in_sync(self):
        items=self.items[0]["queue"]
        native=[x for x in items if x["kind"]=="NATIVE_CASE"]
        human=[x for x in items if x["kind"]=="HUMAN_CRITERION"]
        self.assertEqual([x["subject_id"] for x in native],[x["id"] for x in self.items[2]["case_handoff"]])
        self.assertEqual([x["subject_id"] for x in human],[x["id"] for x in self.items[2]["criterion_handoff"]])
        self.assertEqual([x["platform"] for x in native].count("windows"),43)
        self.assertEqual([x["platform"] for x in native].count("android"),1)

    def test_04_R09_is_global_and_not_native_case_blocker(self):
        q=self.items[0]
        row=[x for x in q["queue"] if x["kind"]=="GLOBAL_REGIONAL_GATE"]
        self.assertEqual(len(row),1)
        self.assertEqual(row[0]["subject_id"],"R09")
        self.assertEqual(row[0]["case_ids"],[])
        self.assertEqual(q["global_r09"]["case_ids"],[])
        self.assertTrue(q["global_r09"]["not_case_scoped"])
        self.assertFalse(any("R09" in c["blocker_ids"] for c in q["queue"] if c["kind"]=="NATIVE_CASE"))

    def test_05_local_reports_and_bcd_are_anonymous_not_real_evidence(self):
        q=self.items[0]["queue"]
        reports=[x for x in q if x["kind"]=="LOCAL_REPORT_SLOT"]
        bcd=[x for x in q if x["kind"]=="BCD_PENDING_SLOT"]
        self.assertEqual(len(reports),5)
        self.assertEqual(len(bcd),13)
        self.assertTrue(all(x["placeholder_not_a_real_artifact"] for x in reports+bcd))
        self.assertTrue(all(not x["case_ids"] and not x["criterion_ids"] for x in reports+bcd))
        self.assertTrue(all(not x["accepted_evidence"] for x in reports+bcd))

    def test_06_no_native_or_human_approval_and_no_upload(self):
        r=self.audited()
        self.assertEqual((r["human_criteria_approved"],r["native_cases_approved"],
                          r["native_cases_executed"],r["local_reports_received"],
                          r["bcd_approved"]),(0,0,0,0,0))
        self.assertTrue(r["no_private_uploads"])
        self.assertTrue(r["no_runtime_authorization"])
        self.assertFalse(r["sinnoh_playable"])
        for x in self.items[0]["queue"]:
            self.assertEqual(x["status"],"PENDING")
            self.assertFalse(x["accepted_evidence"])
            self.assertFalse(x["human_approved"])
            self.assertFalse(x["native_qa_authorized"])
            self.assertEqual(x["request_mode"],"SANITIZED_PUBLIC_STATUS_ONLY")

    def test_07_reconstructed_queue_equals_public_mirror(self):
        same=l12.l11.l10.l09.l08.l07.l06.same
        self.assertTrue(same(self.items[0],self.items[1]))
        self.assertTrue(same(self.items[0],l13.expected_queue(self.items[2])))

    def test_08_synthetic_public_blob_drift_is_rejected(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-l13-public-") as td:
            root=Path(td)
            for rel in (l12.REPORT,l12.MIRROR):
                p=root/rel
                p.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/rel,p)
            self.assertTrue(l13.check_l12_public_blobs(root))
            p=root/l12.REPORT
            p.write_bytes(p.read_bytes()+b" ")
            with self.assertRaises(ValueError):
                l13.check_l12_public_blobs(root)

    def test_09_cli_rejects_external_paths_without_echo(self):
        cmd=[sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l13_public_queue.py")]
        good=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(json.loads(good.stdout)["request_counts"]["evidence_requests_total"],88)
        bad=subprocess.run(cmd+["--save",r"C:\\Users\\User\\Save01.rxdata"],
                           cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(bad.returncode,2)
        self.assertIn("SINNOH_L13_BLOCKED",bad.stderr)
        self.assertNotIn("Save01.rxdata",bad.stderr+bad.stdout)

    def test_10_auditor_no_network_or_native_runtime(self):
        source=(ROOT/"scripts/regions/audit_sinnoh_l13_public_queue.py").read_text("utf8")
        for s in ("import requests","import subprocess","import socket",
                  "os.walk(","rglob(","subprocess.run(","os.system(",
                  "shutil.copy(","from urllib","httpx","os.environ"):
            self.assertNotIn(s,source)

    def test_negative_001_missing_queue(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"].pop())

    def test_negative_002_duplicate_queue(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"].append(copy.deepcopy(a["queue"][0])))

    def test_negative_003_reorder_queue(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"].reverse())

    def test_negative_004_request_id_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(request_id="FAKE"))

    def test_negative_005_request_id_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][1].update(request_id=a["queue"][0]["request_id"]))

    def test_negative_006_sequence_zero(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(order=0))

    def test_negative_007_sequence_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][1].update(order=1))

    def test_negative_008_wrong_priority(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(priority=3))

    def test_negative_009_wrong_priority_label(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(priority_label="P4_NATIVE_QA_UNAUTHORIZED"))

    def test_negative_010_wrong_kind(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(kind="NATIVE_CASE"))

    def test_negative_011_wrong_subject(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(subject_id="FAKE"))

    def test_negative_012_wrong_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(platform="android"))

    def test_negative_013_missing_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0]["blocker_ids"].pop())

    def test_negative_014_extra_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0]["blocker_ids"].append("B10"))

    def test_negative_015_missing_criterion(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0]["criterion_ids"].pop())

    def test_negative_016_wrong_criterion(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0]["criterion_ids"].__setitem__(0,"FAKE"))

    def test_negative_017_criteria_reordered(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0]["criterion_ids"].reverse())

    def test_negative_018_missing_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0]["case_ids"].pop())

    def test_negative_019_wrong_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0]["case_ids"].__setitem__(0,"FAKE"))

    def test_negative_020_case_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0]["case_ids"].reverse())

    def test_negative_021_blocker_priority_not_authorized(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(status="APPROVED"))

    def test_negative_022_blocker_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(accepted_evidence=True))

    def test_negative_023_blocker_human_signoff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(human_approved=True))

    def test_negative_024_blocker_native_auth(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(native_qa_authorized=True))

    def test_negative_025_blocker_readonly_false(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(read_only=False))

    def test_negative_026_blocker_upload_mode(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(request_mode="UPLOAD_SAVES"))

    def test_negative_027_blocker_reason_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][0].update(reason="Approved"))

    def test_negative_028_global_r09_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][5]["case_ids"].append("ball-TURTWIG"))

    def test_negative_029_global_r09_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][5].update(platform="windows"))

    def test_negative_030_global_r09_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][5]["blocker_ids"].append("R07"))

    def test_negative_031_global_r09_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][5].update(status="PASSED"))

    def test_negative_032_report_slot_name(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][6].update(subject_id="C:/save/Save01.rxdata"))

    def test_negative_033_report_slot_nonplaceholder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][6].update(placeholder_not_a_real_artifact=False))

    def test_negative_034_report_slot_path(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][6].update(path="private/Save01.rxdata"))

    def test_negative_035_report_slot_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][6]["case_ids"].append("ball-TURTWIG"))

    def test_negative_036_report_slot_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][6].update(platform="windows"))

    def test_negative_037_report_slot_accepted(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][6].update(accepted_evidence=True))

    def test_negative_038_report_slot_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][6].update(status="RECEIVED"))

    def test_negative_039_report_slot_identity(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][6].update(request_id="L13-REPORT-99"))

    def test_negative_040_criterion_reviewed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][11].update(status="REVIEWED"))

    def test_negative_041_criterion_approval(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][11].update(human_approved=True))

    def test_negative_042_criterion_wrong_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][11]["blocker_ids"].__setitem__(0,"B10"))

    def test_negative_043_criterion_wrong_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][11].update(subject_id="R09_NEW"))

    def test_negative_044_criterion_missing_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][11]["case_ids"].pop())

    def test_negative_045_criterion_case_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][11]["case_ids"].reverse())

    def test_negative_046_criterion_wrong_priority(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][11].update(priority=1))

    def test_negative_047_criterion_private_attachment(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][11].update(attachment="private_asset.png"))

    def test_negative_048_bcd_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][31].update(human_approved=True))

    def test_negative_049_bcd_role_fabricated(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][31].update(stage="B02"))

    def test_negative_050_bcd_placeholder_false(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][31].update(placeholder_not_a_real_artifact=False))

    def test_negative_051_bcd_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][31].update(subject_id="OTHER"))

    def test_negative_052_bcd_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][31].update(priority=2))

    def test_negative_053_native_case_completed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][44].update(status="PASSED"))

    def test_negative_054_native_case_authorized(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][44].update(native_qa_authorized=True))

    def test_negative_055_native_case_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][44].update(accepted_evidence=True))

    def test_negative_056_native_case_human_reviewed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][44].update(human_approved=True))

    def test_negative_057_native_case_wrong_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][44].update(subject_id="FAKE"))

    def test_negative_058_native_case_kind(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][44].update(kind="HUMAN_CRITERION"))

    def test_negative_059_native_case_android_b10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][-1]["blocker_ids"].append("B10"))

    def test_negative_060_native_case_android_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][-1]["blocker_ids"].append("B11"))

    def test_negative_061_native_case_android_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][-1].update(platform="windows"))

    def test_negative_062_native_case_android_missing_criterion(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][-1]["criterion_ids"].pop())

    def test_negative_063_native_case_invalid_reason(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["queue"][-1].update(reason="JoiPlay already passed"))

    def test_negative_064_queue_total_zero(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(evidence_requests_total=0))

    def test_negative_065_queue_total_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(requests_approved=1))

    def test_negative_066_queue_pending_zero(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(requests_pending=0))

    def test_negative_067_queue_criteria_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(human_criterion_requests=21))

    def test_negative_068_queue_native_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(native_case_requests=45))

    def test_negative_069_queue_report_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(report_slots=6))

    def test_negative_070_queue_bcd_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(bcd_slots=12))

    def test_negative_071_queue_blocker_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(blocker_requests=4))

    def test_negative_072_queue_global_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(global_gate_requests=0))

    def test_negative_073_queue_verified_edges(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(public_edges_verified=1000))

    def test_negative_074_queue_human_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(human_approved=20))

    def test_negative_075_queue_native_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(native_approved=44))

    def test_negative_076_queue_reports_received(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(local_reports=5))

    def test_negative_077_queue_bcd_complete(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(phase_bcd_completed=13))

    def test_negative_078_queue_bool_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["counts"].update(native_approved=False))

    def test_negative_079_priority_rules_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["priority_rules"].pop())

    def test_negative_080_priority_rules_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["priority_rules"].reverse())

    def test_negative_081_priority_rules_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["priority_rules"][0].update(priority=4))

    def test_negative_082_priority_rule_version(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a.update(priority_rule_version=2))

    def test_negative_083_priority_new_kind(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["priority_rules"][0]["kinds"].append("GAME_EXE"))

    def test_negative_084_priority_label_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["priority_rules"][0].update(code="P0_NATIVE_READY"))

    def test_negative_085_priority_interpretation(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["priority_rules"][0].update(interpretation="Approval granted"))

    def test_negative_086_platform_queue_windows_native_complete(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["platform_queues"][0].update(native_completed=43))

    def test_negative_087_platform_queue_android_native_complete(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["platform_queues"][1].update(native_completed=1))

    def test_negative_088_platform_queue_windows_auth(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["platform_queues"][0].update(authorization=True))

    def test_negative_089_platform_queue_android_auth(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["platform_queues"][1].update(authorization=True))

    def test_negative_090_platform_queue_android_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["platform_queues"][1].update(requires_windows_sandbox_b10_b11=True))

    def test_negative_091_platform_queue_windows_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["platform_queues"][0].update(requires_windows_sandbox_b10_b11=False))

    def test_negative_092_platform_queue_android_cases(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["platform_queues"][1]["case_ids"].append("ball-TURTWIG"))

    def test_negative_093_platform_queue_android_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["platform_queues"][1].update(platform="windows"))

    def test_negative_094_platform_queues_reversed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["platform_queues"].reverse())

    def test_negative_095_platform_requests_wrong(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["platform_queues"][0].update(native_requests=44))

    def test_negative_096_global_r09_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["global_r09"].update(status="APPROVED"))

    def test_negative_097_global_r09_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["global_r09"]["case_ids"].append("ball-TURTWIG"))

    def test_negative_098_global_r09_case_scoped(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["global_r09"].update(not_case_scoped=False))

    def test_negative_099_global_r09_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["global_r09"].update(approved=True))

    def test_negative_100_global_r09_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["global_r09"].update(id="R10"))

    def test_negative_101_disclaimer_upload(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["disclaimer"].update(no_upload_or_attachments=False))

    def test_negative_102_disclaimer_games(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["disclaimer"].update(no_game_execution=False))

    def test_negative_103_disclaimer_sandbox(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["disclaimer"].update(no_windows_sandbox_execution=False))

    def test_negative_104_disclaimer_joiplay(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["disclaimer"].update(no_joiplay_execution=False))

    def test_negative_105_disclaimer_private(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["disclaimer"].update(no_local_paths_or_saves=False))

    def test_negative_106_disclaimer_isolation(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["disclaimer"].update(watch_unchanged_is_not_global_save_isolation=False))

    def test_negative_107_disclaimer_mapids(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["disclaimer"].update(mapids_not_reserved=False))

    def test_negative_108_disclaimer_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["disclaimer"].update(asset_rights_not_approved=False))

    def test_negative_109_disclaimer_android(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["disclaimer"].update(android_local_l05_not_completed=False))

    def test_negative_110_disclaimer_playable(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["disclaimer"].update(sinnoh_playable=True))

    def test_negative_111_disclaimer_reports(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["disclaimer"].update(no_reports_received=False))

    def test_negative_112_disclaimer_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["disclaimer"].update(no_acceptance_of_private_evidence=False))

    def test_negative_113_gates_r07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["gates"].update(r07="APPROVED"))

    def test_negative_114_gates_r08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["gates"].update(r08="APPROVED"))

    def test_negative_115_gates_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["gates"].update(r09="APPROVED"))

    def test_negative_116_gates_mapids(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["gates"].update(mapids_reserved=True))

    def test_negative_117_gates_assets(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["gates"].update(asset_rights_approved=True))

    def test_negative_118_gates_global_saves(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["gates"].update(b11_global_save_isolation_proven=True))

    def test_negative_119_gates_playable(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["gates"].update(sinnoh_playable=True))

    def test_negative_120_l07_anchor(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["baseline_commits"].update(L07="0"*40))

    def test_negative_121_l08_anchor(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["baseline_commits"].update(L08="0"*40))

    def test_negative_122_l09_anchor(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["baseline_commits"].update(L09="0"*40))

    def test_negative_123_l10_anchor(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["baseline_commits"].update(L10="0"*40))

    def test_negative_124_l11_anchor(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["baseline_commits"].update(L11="0"*40))

    def test_negative_125_l12_anchor(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["baseline_commits"].update(L12="0"*40))

    def test_negative_126_source_l12_blob(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["source_l12"].update(git_blob_sha1="f"*40))

    def test_negative_127_source_l12_path(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a["source_l12"].update(path="private/Source.zip"))

    def test_negative_128_schema(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a.update(schema=2))

    def test_negative_129_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a.update(status="NATIVE_READY"))

    def test_negative_130_mode(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a.update(mode="UPLOAD_RECEIPT"))

    def test_negative_131_version(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a.update(version=2))

    def test_negative_132_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a.update(stage="L14"))

    def test_negative_133_extra_private_key(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: a.update(secret="private"))

    def test_negative_134_mirror_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: b["queue"][0].update(status="APPROVED"))

    def test_negative_135_mirror_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: b["queue"][-1].update(platform="windows"))

    def test_negative_136_mirror_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: b["global_r09"].update(approved=True))

    def test_negative_137_mirror_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: b["counts"].update(native_approved=1))

    def test_negative_138_upstream_l12_source(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: c["case_handoff"][0].update(native_qa_state="PASSED"))

    def test_negative_139_upstream_l12_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: d["case_handoff"][0].update(id="FAKE"))

    def test_negative_140_upstream_l11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: e["case_nodes"][0].update(native_qa_authorized=True))

    def test_negative_141_upstream_l11_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: f["case_nodes"][0].update(id="FAKE"))

    def test_negative_142_upstream_l10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: g["cases"][0].update(approved=True))

    def test_negative_143_upstream_l10_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: h["cases"][0].update(id="FAKE"))

    def test_negative_144_upstream_l09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: i["case_handoff"][0].update(native_status="passed"))

    def test_negative_145_upstream_l08_snapshot(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: j["cases"][0].update(native_qa_authorized=True))

    def test_negative_146_upstream_l08_diff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: k["comparisons"][0]["added_ids"].append("FAKE"))

    def test_negative_147_upstream_g12(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: l["cases"][0].update(native_status="passed"))

    def test_negative_148_upstream_l04(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: m["rows"][0]["criteria"][0].update(local_human_signoff=True))

    def test_negative_149_upstream_l05(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: n.update(mapids_reserved=True))

    def test_negative_150_upstream_l06(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: o.update(asset_rights_approved=True))

    def test_negative_151_upstream_l07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: p["cases"][-1].update(platform="windows"))

    def test_negative_152_upstream_l07_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: q["cases"][0].update(id="FAKE"))

    def test_negative_153_upstream_l07_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: s["counts"].update(native_approved=1))

    def test_negative_154_upstream_l06_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: t.update(native_cases_approved=1))

    def test_negative_155_upstream_l05_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: u.update(native_cases_approved=1))

    def test_negative_156_upstream_l04_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: v.update(criteria_reviewed=1))

    def test_negative_157_upstream_g12_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s,t,u,v,w: w.update(evidence_accepted_cases=1))

if __name__=='__main__':
    unittest.main()
