"""L10 public blocker index: independent strict positive and synthetic negative tests."""
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
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_l10_public_index as l10
l09=l10.l09
l08=l09.l08

class SinnohL10IndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reader=l08.l07.l06.l05.l04.l03.l02.l00.read_json
        cls.docs={stage:reader(ROOT,path,maxsize=175000) for stage,path,_sha in l08.PINNED}
        cls.inputs=[
            reader(ROOT,l10.INDEX,maxsize=155000),
            reader(ROOT,l10.MIRROR,maxsize=155000),
            reader(ROOT,l09.PACKET,maxsize=155000),
            reader(ROOT,l08.SNAPSHOT,maxsize=125000),
            reader(ROOT,l08.DIFF,maxsize=16000),
            cls.docs["G12"],cls.docs["L04"],cls.docs["L05"],cls.docs["L06"],
            cls.docs["L07"],cls.docs["L07_SITE"],
            l08.l07.run(ROOT),l08.l07.l06.run(ROOT),
            l08.l07.l06.l05.run(ROOT),l08.l07.l06.l05.l04.run(ROOT),
            l08.l07.l06.l05.G12.run(ROOT),
        ]

    def audited(self, mutate=None):
        values=[copy.deepcopy(x) for x in self.inputs]
        if mutate:
            mutate(*values)
        return l10.audit(values[0],values[1],values[2],*values[3:])

    def rejected(self,mutate):
        with self.assertRaises(ValueError):
            self.audited(mutate)

    def test_01_public_blob_pinning_and_success(self):
        self.assertTrue(l10.check_l09_blob(ROOT))
        r=self.audited()
        self.assertEqual(r["status"],"PUBLIC_INDEX_VALID_NATIVE_PENDING")
        self.assertEqual(r["source_l09_blob_verified"],l10.L09_BLOB)
        self.assertEqual(r["baseline_commits"]["L09"],l10.L09_MERGE)

    def test_02_44_real_ids_20_criteria_and_order(self):
        r=self.audited()
        self.assertEqual(r["cases_total"],44)
        self.assertEqual(r["criteria_total"],20)
        self.assertEqual(r["case_ids"],[x["case_id"] for x in self.inputs[2]["case_handoff"]])
        self.assertEqual(r["criteria_ids"],[x["criterion_id"] for x in self.inputs[2]["review_tasks"]])
        self.assertEqual(len(set(r["case_ids"])),44)
        self.assertEqual(len(set(r["criteria_ids"])),20)

    def test_03_43_windows_and_1_android_not_mixed(self):
        r=self.audited()
        self.assertEqual((r["windows_cases"],r["android_cases"]),(43,1))
        self.assertTrue(r["windows_android_review_independent"])
        p=self.inputs[0]
        self.assertEqual(p["cases"][-1]["id"],"android-joi-play")
        self.assertFalse(any(x in p["cases"][-1]["blocked_by"] for x in ("B10","B11")))
        self.assertTrue(all("B10" in x["blocked_by"] and "B11" in x["blocked_by"] for x in p["cases"][:-1]))

    def test_04_all_six_blockers_distinct_R09_global(self):
        p=self.inputs[0]
        self.assertEqual([x["id"] for x in p["blockers"]],["B09","B10","B11","R07","R08","R09"])
        self.assertEqual([(x["windows_cases"],x["android_cases"]) for x in p["blockers"]],[(43,1),(43,0),(43,0),(43,1),(43,1),(0,0)])
        self.assertEqual(p["blockers"][-1]["scope"],"GLOBAL_REGION_PENDING_NOT_CASE_GATE")
        self.assertEqual(p["blockers"][-1]["case_ids"],[])
        self.assertTrue(all(x["status"]=="PENDING" for x in p["blockers"]))

    def test_05_all_gates_still_blocked(self):
        r=self.audited()
        self.assertEqual((r["criteria_human_approved"],r["native_completed"],r["native_approved"],r["local_reports"]),(0,0,0,0))
        self.assertEqual((r["cases_pending"],r["criteria_unreviewed"]),(44,20))
        for flag in ("b11_global_isolation_proven","mapids_reserved","asset_rights_approved",
                     "can_run_game_exe","can_run_windows_sandbox","can_run_joiplay",
                     "can_install_live_game","sinnoh_playable"):
            self.assertIs(r[flag],False)
        self.assertTrue(all(r[s] for s in ("r07_pending","r08_pending","r09_pending")))

    def test_06_index_and_mirror_strict_equality(self):
        same=l09.l08.l07.l06.same
        self.assertTrue(same(self.inputs[0],self.inputs[1]))
        self.assertTrue(same(self.inputs[0],l10.expected_index(self.inputs[2])))
        self.assertEqual(self.audited()["blocker_ids"],["B09","B10","B11","R07","R08","R09"])

    def test_07_synthetic_public_blob_mutation_rejected(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-l10-public-test-") as td:
            target=Path(td)/l09.PACKET
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/l09.PACKET,target)
            self.assertTrue(l10.check_l09_blob(Path(td)))
            target.write_bytes(target.read_bytes()+b" ")
            with self.assertRaises(ValueError):
                l10.check_l09_blob(Path(td))

    def test_08_cli_does_not_echo_private_or_user_input(self):
        cmd=[sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l10_public_index.py")]
        good=subprocess.run(cmd,text=True,capture_output=True,cwd=ROOT,check=False)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(json.loads(good.stdout)["stage"],"L10")
        bad=subprocess.run(cmd+["--save",r"C:\\Users\\name\\Save01.rxdata"],
                           text=True,capture_output=True,cwd=ROOT,check=False)
        self.assertEqual(bad.returncode,2)
        self.assertIn("SINNOH_L10_BLOCKED",bad.stderr)
        self.assertNotIn("Save01.rxdata",bad.stdout+bad.stderr)

    def test_09_auditor_never_launches_runtimes_or_uploads(self):
        s=(ROOT/"scripts/regions/audit_sinnoh_l10_public_index.py").read_text("utf8")
        for x in ("import subprocess","import socket","import requests","os.walk(",
                  "rglob(","os.system(","subprocess.run(","shutil.copy(",
                  "from urllib","requests.post(","httpx","os.environ"):
            self.assertNotIn(x,s)

    def test_10_navigable_page_and_safe_read_only_js(self):
        html=(ROOT/"site/public/sinnoh-l10-bloqueios.html").read_text("utf8")
        js=(ROOT/"site/public/assets/sinnoh-l10-blocker-index.js").read_text("utf8")
        for field in ("blockers","casos","criterios","search","platform","kind",
                      "blocker","criterion","caseRows","criterionRows","reset","status"):
            self.assertIn('id="'+field+'"',html)
        self.assertIn("/data/sinnoh-l10-public-blocker-index.json",js)
        self.assertIn("document.createElement",js)
        self.assertIn("textContent",js)
        self.assertNotIn("innerHTML",js)
        self.assertNotIn("FormData",js)
        self.assertNotIn("localStorage",js)
        self.assertNotIn("eval(",js)

    def test_negative_001_case_missing(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"].pop())

    def test_negative_002_case_duplicated(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"].append(copy.deepcopy(a["cases"][0])))

    def test_negative_003_case_order(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"].reverse())

    def test_negative_004_case_id(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0].update(id="ball-FAKE"))

    def test_negative_005_case_duplicate_id(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][1].update(id=a["cases"][0]["id"]))

    def test_negative_006_case_kind(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0].update(kind="npc"))

    def test_negative_007_win_becomes_android(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0].update(platform="android"))

    def test_negative_008_android_becomes_windows(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][-1].update(platform="windows"))

    def test_negative_009_case_criterion_missing(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0]["criteria"].pop())

    def test_negative_010_case_criterion_extra(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0]["criteria"].append("R09_FAKE"))

    def test_negative_011_case_criteria_order(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0]["criteria"].reverse())

    def test_negative_012_case_b10_missing(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0]["blocked_by"].remove("B10"))

    def test_negative_013_case_b11_missing(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0]["blocked_by"].remove("B11"))

    def test_negative_014_android_b10_added(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][-1]["blocked_by"].append("B10"))

    def test_negative_015_android_b11_added(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][-1]["blocked_by"].append("B11"))

    def test_negative_016_android_r09_case_added(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][-1]["blocked_by"].append("R09"))

    def test_negative_017_case_blocked_by_order(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0]["blocked_by"].reverse())

    def test_negative_018_case_queue_forged(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][-1].update(queue="WINDOWS_INDEPENDENT_HOST_DOCUMENTARY_REVIEW"))

    def test_negative_019_case_gate_forged(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0].update(native_gate="QA_APPROVED"))

    def test_negative_020_case_reviewed(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0].update(review_state="APPROVED"))

    def test_negative_021_case_action_execute(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0].update(action="RUN_GAME"))

    def test_negative_022_case_native_passed(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0].update(native_status="passed"))

    def test_negative_023_case_approved(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0].update(approved=True))

    def test_negative_024_case_authorized(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0].update(native_execution_authorized=True))

    def test_negative_025_case_privately_attached(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["cases"][0].update(save_path="Save01.rxdata"))

    def test_negative_026_criteria_missing(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"].pop())

    def test_negative_027_criteria_duplicate(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"].append(copy.deepcopy(a["criteria"][0])))

    def test_negative_028_criteria_order(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"].reverse())

    def test_negative_029_criteria_id(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"][0].update(id="B09_FAKE"))

    def test_negative_030_criteria_stage(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"][0].update(stage="R08"))

    def test_negative_031_criteria_requirement(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"][0].update(requirement="No review needed"))

    def test_negative_032_criteria_case_missing(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"][0]["case_ids"].pop())

    def test_negative_033_criteria_case_extra(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"][0]["case_ids"].append("FAKE"))

    def test_negative_034_criteria_case_order(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"][0]["case_ids"].reverse())

    def test_negative_035_criteria_windows_count(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"][0].update(windows_cases=0))

    def test_negative_036_criteria_android_count(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"][0].update(android_cases=20))

    def test_negative_037_criteria_reviewed(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"][0].update(review_state="REVIEWED"))

    def test_negative_038_criteria_signoff(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["criteria"][0].update(signoff=True))

    def test_negative_039_blocker_missing(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"].pop())

    def test_negative_040_blocker_duplicated(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"].append(copy.deepcopy(a["blockers"][0])))

    def test_negative_041_blocker_order(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"].reverse())

    def test_negative_042_blocker_id(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"][0].update(id="B12"))

    def test_negative_043_blocker_description(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"][0].update(description="Approved"))

    def test_negative_044_blocker_scope(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"][1].update(scope="CROSS_PLATFORM"))

    def test_negative_045_blocker_case_missing(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"][0]["case_ids"].pop())

    def test_negative_046_blocker_case_duplicated(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"][0]["case_ids"].append(a["blockers"][0]["case_ids"][0]))

    def test_negative_047_blocker_windows_count(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"][1].update(windows_cases=44))

    def test_negative_048_blocker_android_count(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"][2].update(android_cases=1))

    def test_negative_049_blocker_status(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"][0].update(status="APPROVED"))

    def test_negative_050_blocker_auto_approval(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"][0].update(not_a_native_approval=False))

    def test_negative_051_r09_global_scope(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"][-1].update(scope="CROSS_PLATFORM"))

    def test_negative_052_r09_fake_case(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"][-1]["case_ids"].append("ball-TURTWIG"))

    def test_negative_053_r09_fake_windows(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["blockers"][-1].update(windows_cases=43))

    def test_negative_054_mirror_case_id(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: c["cases"][0].update(id="OTHER"))

    def test_negative_055_mirror_case_approved(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: c["cases"][0].update(approved=True))

    def test_negative_056_mirror_missing(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: c["criteria"].pop())

    def test_negative_057_mirror_r09(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: c["blockers"][-1].update(status="APPROVED"))

    def test_negative_058_mirror_rights(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: c["gates"].update(asset_rights_approved=True))

    def test_negative_059_mirror_secret(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: c.update(private_save="Save01.rxdata"))

    def test_negative_060_index_schema(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(schema=2))

    def test_negative_061_index_version(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(version=2))

    def test_negative_062_index_stage(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(stage="L11"))

    def test_negative_063_index_region(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(region="UNOVA"))

    def test_negative_064_index_status(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(status="NATIVE_READY"))

    def test_negative_065_index_mode(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(mode="HOST_QA"))

    def test_negative_066_anchor_l07(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["baseline_commits"].update(L07="0"*40))

    def test_negative_067_anchor_l08(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["baseline_commits"].update(L08="0"*40))

    def test_negative_068_anchor_l09(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["baseline_commits"].update(L09="0"*40))

    def test_negative_069_source_l09_path(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["source_l09"].update(path="private.json"))

    def test_negative_070_source_l09_sha(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["source_l09"].update(git_blob_sha1="0"*40))

    def test_negative_071_source_l09_unexpected(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["source_l09"].update(token="secret"))

    def test_negative_072_count_cases(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["counts"].update(cases_total=45))

    def test_negative_073_count_windows(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["counts"].update(windows=44))

    def test_negative_074_count_android(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["counts"].update(android=2))

    def test_negative_075_count_criteria(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["counts"].update(criteria_total=21))

    def test_negative_076_count_human(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["counts"].update(human_approved=1))

    def test_negative_077_count_native_completed(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["counts"].update(native_completed=1))

    def test_negative_078_count_native_approved(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["counts"].update(native_approved=1))

    def test_negative_079_count_reports(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["counts"].update(local_reports=5))

    def test_negative_080_count_bcd(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["counts"].update(phase_bcd_completed=13))

    def test_negative_081_gate_r07(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(r07="APPROVED"))

    def test_negative_082_gate_r08(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(r08="APPROVED"))

    def test_negative_083_gate_r09(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(r09="APPROVED"))

    def test_negative_084_gate_rights(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(asset_rights_approved=True))

    def test_negative_085_gate_mapids(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(mapids_reserved=True))

    def test_negative_086_gate_b11_global(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(b11_global_save_isolation_proven=True))

    def test_negative_087_gate_windows_sandbox(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(windows_sandbox_executed=True))

    def test_negative_088_gate_joiplay(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(joiplay_tested=True))

    def test_negative_089_gate_phase_b(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(phase_b_approved=1))

    def test_negative_090_gate_phase_c(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(phase_c_approved=1))

    def test_negative_091_gate_phase_d(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(phase_d_approved=1))

    def test_negative_092_gate_game(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(can_launch_game_exe=True))

    def test_negative_093_gate_sandbox(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(can_start_windows_sandbox=True))

    def test_negative_094_gate_joiplay_launch(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(can_launch_joiplay=True))

    def test_negative_095_gate_install(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(can_install_live_game=True))

    def test_negative_096_gate_playable(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(sinnoh_playable=True))

    def test_negative_097_gate_upload(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["gates"].update(auto_upload=True))

    def test_negative_098_global_r09_false(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(global_r09_pending=False))

    def test_negative_099_windows_android_false(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(windows_android_review_independent=False))

    def test_negative_100_b11_watch_forged(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(watch_unchanged_not_global_isolation=False))

    def test_negative_101_rights_forged(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(asset_rights_not_approved=False))

    def test_negative_102_mapids_reserved(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(mapids_not_reserved=False))

    def test_negative_103_l10_game_allowed(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(can_run_game_exe=True))

    def test_negative_104_l10_sandbox_allowed(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(can_run_windows_sandbox=True))

    def test_negative_105_l10_joiplay_allowed(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(can_run_joiplay=True))

    def test_negative_106_l10_install_allowed(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(can_install_live_game=True))

    def test_negative_107_l10_playable(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(sinnoh_playable=True))

    def test_negative_108_l10_android_l05(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(local_android_l05_completed=True))

    def test_negative_109_l10_raw_evidence(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a.update(raw_evidence={"Save01.rxdata":"secret"}))

    def test_negative_110_bool_forged_count(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: a["counts"].update(native_approved=False))

    def test_negative_111_upstream_l09_case(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: d["case_handoff"][0].update(native_status="passed"))

    def test_negative_112_upstream_l09_criterion(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: d["review_tasks"][0].update(local_human_signoff=True))

    def test_negative_113_upstream_l08_case(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: e["cases"][0].update(native_qa_authorized=True))

    def test_negative_114_upstream_l08_diff(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: f["comparisons"][0]["added_ids"].append("FAKE"))

    def test_negative_115_upstream_g12(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: g["cases"][0].update(native_status="passed"))

    def test_negative_116_upstream_l04(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: h["rows"][0]["criteria"][0].update(local_human_signoff=True))

    def test_negative_117_upstream_l05(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: i.update(mapids_reserved=True))

    def test_negative_118_upstream_l06(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: j.update(asset_rights_approved=True))

    def test_negative_119_upstream_l07(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: k["cases"][-1].update(platform="windows"))

    def test_negative_120_upstream_site(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: l["cases"][0].update(id="OTHER"))

    def test_negative_121_upstream_l07_report(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: m["counts"].update(native_approved=1))

    def test_negative_122_upstream_l06_report(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: n.update(native_cases_approved=1))

    def test_negative_123_upstream_l05_report(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: o.update(native_cases_approved=1))

    def test_negative_124_upstream_l04_report(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: p.update(criteria_reviewed=1))

    def test_negative_125_upstream_g12_report(self):
        self.rejected(lambda a,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q: q.update(evidence_accepted_cases=1))

if __name__=='__main__':
    unittest.main()
