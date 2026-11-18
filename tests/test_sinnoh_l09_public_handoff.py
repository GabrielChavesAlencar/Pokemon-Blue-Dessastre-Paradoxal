"""L09 synthetic negative tests for strict independent human-documentary handoff."""
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
import audit_sinnoh_l09_public_handoff as l09
l08=l09.l08
l07=l08.l07


class SinnohL09PublicHandoffTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read=l07.l06.l05.l04.l03.l02.l00.read_json
        cls.docs={stage:read(ROOT, path, maxsize=175000) for stage,path,sha in l08.PINNED}
        cls.input=[
            read(ROOT,l09.PACKET,maxsize=155000),
            read(ROOT,l08.SNAPSHOT,maxsize=125000),
            read(ROOT,l08.DIFF,maxsize=16000),
            cls.docs["G12"], cls.docs["L04"], cls.docs["L05"], cls.docs["L06"],
            cls.docs["L07"],cls.docs["L07_SITE"],
            l07.run(ROOT), l07.l06.run(ROOT), l07.l06.l05.run(ROOT),
            l07.l06.l05.l04.run(ROOT), l07.l06.l05.G12.run(ROOT),
        ]

    def audited(self, change=None):
        data=[copy.deepcopy(x) for x in self.input]
        if change is not None:
            change(*data)
        return l09.audit(*data)

    def rejected(self, change):
        with self.assertRaises(ValueError):
            self.audited(change)

    def test_01_public_baseline_and_sha(self):
        result=self.audited()
        self.assertEqual(result["status"],"PUBLIC_HUMAN_HANDOFF_VALID_NO_APPROVAL")
        self.assertEqual(result["baseline_commit_l08"],l09.L08_MERGE)
        self.assertEqual(result["baseline_commit_l07"],l08.ANCHOR)
        self.assertTrue(l09.check_source_blobs(ROOT))
        self.assertEqual(result["public_git_blobs_pinned"],3)
        self.assertEqual(result["upstream_public_drift"],0)

    def test_02_44_real_cases_match_snapshot(self):
        result=self.audited()
        self.assertEqual(result["cases_total"],44)
        self.assertEqual(len(result["case_review_queue"]),44)
        self.assertEqual([c["id"] for c in result["case_review_queue"]],
                         [c["id"] for c in self.input[1]["cases"]])
        self.assertEqual(len({c["id"] for c in result["case_review_queue"]}),44)
        self.assertEqual(result["windows_cases"],43)
        self.assertEqual(result["android_cases"],1)

    def test_03_20_real_criteria_match_L04(self):
        result=self.audited()
        self.assertEqual([c["id"] for c in result["human_review_tasks"]],
                         [c["id"] for stage in self.input[4]["rows"] for c in stage["criteria"]])
        self.assertEqual(result["criteria_total"],20)
        self.assertEqual(result["criteria_reviewed"],0)
        self.assertTrue(all(c["state"]=="NOT_REVIEWED" for c in result["human_review_tasks"]))

    def test_04_windows_and_android_never_share_VM_acceptance(self):
        p=self.input[0]
        self.assertEqual(p["case_handoff"][-1]["case_id"],"android-joi-play")
        self.assertEqual(p["case_handoff"][-1]["platform"],"android")
        self.assertNotIn("B10",p["case_handoff"][-1]["blocked_by"])
        self.assertNotIn("B11",p["case_handoff"][-1]["blocked_by"])
        self.assertTrue(all("B10" in row["blocked_by"] and "B11" in row["blocked_by"]
                            for row in p["case_handoff"][:-1]))
        self.assertTrue(p["review_safety"]["windows_android_review_independent"])

    def test_05_no_human_or_native_authorization(self):
        r=self.audited()
        for k in ("human_reviews_accepted","native_cases_completed","native_cases_approved",
                  "local_reports_received","phase_bcd_approved"):
            self.assertEqual(r[k],0)
        for k in ("r07_complete","r08_complete","r09_complete",
                  "b11_global_isolation_proven","asset_rights_approved","mapids_reserved",
                  "may_run_game_exe","may_start_windows_sandbox","may_run_joiplay",
                  "may_install_live_game","auto_uploaded","android_local_l05_complete",
                  "sinnoh_playable"):
            self.assertIs(r[k],False)
        self.assertTrue(all(not x["native_execution_authorized"] for x in r["case_review_queue"]))

    def test_06_public_only_and_no_sensitive_echo(self):
        data=json.dumps(self.audited(),ensure_ascii=True)
        for s in ("Save01.rxdata","private-baseline.json","hmac_key","watch_id",
                  "source_clone_sha256","C:\\\\Users"):
            self.assertNotIn(s,data)
        self.assertTrue(all(not r["private_file_attached"] for r in self.input[0]["case_handoff"]))

    def test_07_public_blob_mutation_is_detected(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-l09-synthetic-") as td:
            root=Path(td)
            for _stage,relative,_sha in l09.PINNED_PUBLIC:
                target=root/relative
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT/relative,target)
            self.assertTrue(l09.check_source_blobs(root))
            file=root/l09.PINNED_PUBLIC[0][1]
            file.write_bytes(file.read_bytes()+b" ")
            with self.assertRaises(ValueError):
                l09.check_source_blobs(root)

    def test_08_cli_rejects_path_and_private_data_without_echo(self):
        cmd=[sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l09_public_handoff.py")]
        ok=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(ok.returncode,0,ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["cases_total"],44)
        denied=subprocess.run(cmd+["--save",r"C:\\Users\\tester\\Save01.rxdata"],
                              cwd=ROOT,text=True,capture_output=True,check=False)
        self.assertEqual(denied.returncode,2)
        self.assertIn("SINNOH_L09_BLOCKED",denied.stderr)
        self.assertNotIn("Save01.rxdata",denied.stderr+denied.stdout)

    def test_09_source_never_executes_game_or_network(self):
        source=(ROOT/"scripts/regions/audit_sinnoh_l09_public_handoff.py").read_text("utf8")
        for forbidden in ("import requests","import socket","import subprocess",
                          "os.walk(","rglob(","subprocess.run(","os.system(",
                          "shutil.copy(","from urllib","requests.get(","httpx"):
            self.assertNotIn(forbidden,source)

    def test_10_review_tasks_and_queues_represent_only_pending_states(self):
        p=self.input[0]
        self.assertTrue(all(t["reviewer_action"]=="KEEP_PENDING"
              and t["review_state"]=="NOT_REVIEWED" and not t["local_human_signoff"]
              and not t["independent_evidence_accepted"] for t in p["review_tasks"]))
        self.assertTrue(all(c["reviewer_action"]=="KEEP_PENDING"
              and c["native_status"]=="pending" and not c["native_qa_authorized"]
              and not c["human_signoff"] for c in p["case_handoff"]))
        self.assertEqual(p["human_review_completed"],0)
        self.assertEqual(p["independent_signoffs"],0)
        self.assertEqual(p["physical_evidence_received"],0)
        self.assertTrue(p["review_safety"]["L09_documental_not_G12_android_local_L05"])

    def test_negative_001_missing_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"].pop())

    def test_negative_002_duplicate_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"].append(copy.deepcopy(a["case_handoff"][0])))

    def test_negative_003_reorder_cases(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"].reverse())

    def test_negative_004_invent_case_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(case_id="ball-FAKE"))

    def test_negative_005_duplicate_case_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][1].update(case_id=a["case_handoff"][0]["case_id"]))

    def test_negative_006_case_kind(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(kind="npc"))

    def test_negative_007_windows_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(platform="android"))

    def test_negative_008_android_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][-1].update(platform="windows"))

    def test_negative_009_criteria_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0]["required_criteria_ids"].pop())

    def test_negative_010_criteria_extra(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0]["required_criteria_ids"].append("B09_FAKE"))

    def test_negative_011_criteria_reordered(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0]["required_criteria_ids"].reverse())

    def test_negative_012_blocker_b10_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0]["blocked_by"].remove("B10"))

    def test_negative_013_blocker_b11_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0]["blocked_by"].remove("B11"))

    def test_negative_014_android_b10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][-1]["blocked_by"].append("B10"))

    def test_negative_015_android_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][-1]["blocked_by"].append("B11"))

    def test_negative_016_android_lane(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][-1].update(reviewer_lane="WINDOWS_INDEPENDENT_HOST_DOCUMENTARY_REVIEW"))

    def test_negative_017_windows_lane(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(reviewer_lane="ANDROID_INDEPENDENT_DEVICE_DOCUMENTARY_REVIEW"))

    def test_negative_018_native_gate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(future_native_gate="QA_APPROVED"))

    def test_negative_019_review_codes_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0]["expected_review_codes"].pop())

    def test_negative_020_review_codes_injected(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0]["expected_review_codes"].append("APPROVE_RUNTIME"))

    def test_negative_021_review_codes_reordered(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0]["expected_review_codes"].reverse())

    def test_negative_022_case_signoff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(human_signoff=True))

    def test_negative_023_case_review_state(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(review_state="APPROVED"))

    def test_negative_024_case_action(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(reviewer_action="RUN_GAME"))

    def test_negative_025_case_native_pass(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(native_status="passed"))

    def test_negative_026_case_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(real_evidence_accepted=True))

    def test_negative_027_case_auth(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(native_qa_authorized=True))

    def test_negative_028_case_private_attachment(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(private_file_attached=True))

    def test_negative_029_case_private_path(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["case_handoff"][0].update(save_path="Save01.rxdata"))

    def test_negative_030_missing_task(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"].pop())

    def test_negative_031_duplicate_task(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"].append(copy.deepcopy(a["review_tasks"][0])))

    def test_negative_032_reorder_tasks(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"].reverse())

    def test_negative_033_task_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(criterion_id="B09_FAKE"))

    def test_negative_034_task_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(stage="R08"))

    def test_negative_035_task_kind(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(kind="RIGHTS_APPROVED"))

    def test_negative_036_task_requirement(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(public_requirement="Approve without review"))

    def test_negative_037_task_state(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(review_state="ACCEPTED"))

    def test_negative_038_task_action(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(reviewer_action="APPROVE"))

    def test_negative_039_task_review_required(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(needs_external_independent_human_review=False))

    def test_negative_040_task_accepted(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(independent_evidence_accepted=True))

    def test_negative_041_task_signoff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(local_human_signoff=True))

    def test_negative_042_task_case_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(matching_case_count=0))

    def test_negative_043_task_windows_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(windows_cases=0))

    def test_negative_044_task_android_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(android_cases=2))

    def test_negative_045_tasks_private_evidence(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_tasks"][0].update(private_log="HMAC"))

    def test_negative_046_sources_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["public_sources"].pop())

    def test_negative_047_sources_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["public_sources"].append(copy.deepcopy(a["public_sources"][0])))

    def test_negative_048_sources_reordered(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["public_sources"].reverse())

    def test_negative_049_sources_blob(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["public_sources"][0].update(git_blob_sha1="f"*40))

    def test_negative_050_sources_path(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["public_sources"][0].update(path="private/save.json"))

    def test_negative_051_sources_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["public_sources"][0].update(stage="OTHER"))

    def test_negative_052_l07_anchor(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(baseline_commit_l07="f"*40))

    def test_negative_053_l08_anchor(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(baseline_commit_l08="f"*40))

    def test_negative_054_schema(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(schema=2))

    def test_negative_055_stage(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(stage="L10"))

    def test_negative_056_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(status="HUMAN_APPROVED"))

    def test_negative_057_version(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(version=2))

    def test_negative_058_native_completed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["counts"].update(native_completed=44))

    def test_negative_059_native_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["counts"].update(native_approved=1))

    def test_negative_060_human_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["counts"].update(human_approved=20))

    def test_negative_061_local_reports(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["counts"].update(local_reports=5))

    def test_negative_062_phase_bcd(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["counts"].update(phase_bcd_completed=13))

    def test_negative_063_windows_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["counts"].update(windows=44))

    def test_negative_064_android_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["counts"].update(android=0))

    def test_negative_065_r07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(r07="APPROVED"))

    def test_negative_066_r08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(r08="APPROVED"))

    def test_negative_067_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(r09="APPROVED"))

    def test_negative_068_global_save(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(b11_global_save_isolation_proven=True))

    def test_negative_069_mapids(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(mapids_reserved=True))

    def test_negative_070_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(asset_rights_approved=True))

    def test_negative_071_sandbox_run(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(windows_sandbox_executed=True))

    def test_negative_072_joiplay_run(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(joiplay_tested=True))

    def test_negative_073_phase_b(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(phase_b_approved=1))

    def test_negative_074_phase_c(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(phase_c_approved=1))

    def test_negative_075_phase_d(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(phase_d_approved=1))

    def test_negative_076_may_game(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(can_launch_game_exe=True))

    def test_negative_077_may_joiplay(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(can_launch_joiplay=True))

    def test_negative_078_may_sandbox(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(can_start_windows_sandbox=True))

    def test_negative_079_may_install(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(can_install_live_game=True))

    def test_negative_080_playable(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(sinnoh_playable=True))

    def test_negative_081_auto_upload(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["gates"].update(auto_upload=True))

    def test_negative_082_action_extra(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["allowed_documentary_actions"].append("LAUNCH_GAME"))

    def test_negative_083_action_current(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(default_action="APPROVED"))

    def test_negative_084_review_complete(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(human_review_completed=20))

    def test_negative_085_signoffs(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(independent_signoffs=20))

    def test_negative_086_evidence_received(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(physical_evidence_received=1))

    def test_negative_087_external_auth(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(external_human_authorization_present=True))

    def test_negative_088_may_start(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(can_start_native_qa=True))

    def test_negative_089_review_policy_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_safety"].update(unchanged_watch_not_global_save_isolation=False))

    def test_negative_090_review_policy_android(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_safety"].update(windows_android_review_independent=False))

    def test_negative_091_review_policy_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_safety"].update(asset_listing_not_license_approval=False))

    def test_negative_092_review_policy_upload(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_safety"].update(no_auto_upload=False))

    def test_negative_093_review_policy_runtime(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a["review_safety"].update(no_game_execution=False))

    def test_negative_094_unexpected_secret(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: a.update(private_secret="HMAC"))

    def test_negative_095_upstream_l08_snapshot(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: b["cases"][0].update(native_qa_authorized=True))

    def test_negative_096_upstream_l08_diff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: c["comparisons"][0]["added_ids"].append("FAKE"))

    def test_negative_097_upstream_g12(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: d["cases"][0].update(native_status="passed"))

    def test_negative_098_upstream_l04(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: e["rows"][0]["criteria"][0].update(local_human_signoff=True))

    def test_negative_099_upstream_l05(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: f.update(asset_rights_approved=True))

    def test_negative_100_upstream_l06(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: g.update(mapids_reserved=True))

    def test_negative_101_upstream_l07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: h["cases"][-1].update(platform="windows"))

    def test_negative_102_upstream_site(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: i["cases"][0].update(id="OTHER"))

    def test_negative_103_upstream_l07_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: j["counts"].update(native_approved=1))

    def test_negative_104_upstream_l06_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: k.update(native_cases_approved=1))

    def test_negative_105_upstream_l05_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: l.update(native_cases_approved=1))

    def test_negative_106_upstream_l04_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: m.update(criteria_reviewed=1))

    def test_negative_107_upstream_g12_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n: n.update(evidence_accepted_cases=1))

if __name__=='__main__':
    unittest.main()
