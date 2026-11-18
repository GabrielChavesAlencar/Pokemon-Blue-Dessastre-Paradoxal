"""L11 strict public traceability graph and source-chain regression tests."""
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
import audit_sinnoh_l11_traceability as l11
l10 = l11.l10
l09 = l10.l09
l08 = l09.l08


class SinnohL11TraceabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        read = l08.l07.l06.l05.l04.l03.l02.l00.read_json
        cls.sources = {
            stage: read(ROOT, path, maxsize=175000)
            for stage, path, _sha in l08.PINNED
        }
        cls.items = [
            read(ROOT, l11.GRAPH, maxsize=200000),
            read(ROOT, l11.MIRROR, maxsize=200000),
            read(ROOT, l10.INDEX, maxsize=155000),
            read(ROOT, l10.MIRROR, maxsize=155000),
            read(ROOT, l09.PACKET, maxsize=155000),
            read(ROOT, l08.SNAPSHOT, maxsize=125000),
            read(ROOT, l08.DIFF, maxsize=16000),
            cls.sources["G12"], cls.sources["L04"],
            cls.sources["L05"], cls.sources["L06"], cls.sources["L07"],
            cls.sources["L07_SITE"],
            l08.l07.run(ROOT), l08.l07.l06.run(ROOT),
            l08.l07.l06.l05.run(ROOT),
            l08.l07.l06.l05.l04.run(ROOT),
            l08.l07.l06.l05.G12.run(ROOT),
        ]

    def audited(self, mutate=None):
        docs = [copy.deepcopy(x) for x in self.items]
        if mutate is not None:
            mutate(*docs)
        return l11.audit(*docs)

    def rejected(self, mutate):
        with self.assertRaises(ValueError):
            self.audited(mutate)

    def test_01_pinned_L10_git_blob_public(self):
        self.assertTrue(l11.check_l10_blob(ROOT))
        r = self.audited()
        self.assertEqual(r["status"], "PUBLIC_TRACEABILITY_VALID_NATIVE_PENDING")
        self.assertEqual(r["source_l10_git_blob"], l11.L10_BLOB)
        self.assertEqual(r["baseline_commits"]["L10"], l11.L10_MERGE)

    def test_02_real_cases_criteria_and_blockers(self):
        r = self.audited()
        self.assertEqual(len(r["case_ids"]), 44)
        self.assertEqual(len(set(r["case_ids"])), 44)
        self.assertEqual(len(r["criterion_ids"]), 20)
        self.assertEqual(len(set(r["criterion_ids"])), 20)
        self.assertEqual(r["blocker_ids"], ["B09","B10","B11","R07","R08","R09"])
        self.assertEqual(r["case_ids"], [x["id"] for x in self.items[2]["cases"]])
        self.assertEqual(r["criterion_ids"], [x["id"] for x in self.items[2]["criteria"]])

    def test_03_all_1084_edges_and_inverse_links(self):
        r = self.audited()
        self.assertEqual(r["edges_checked"], {
            "case_to_criterion":846,
            "case_to_blocker":218,
            "criterion_to_blocker":20,
        })
        graph = self.items[0]
        self.assertEqual(len(graph["edges"]["case_to_criterion"]),846)
        for criterion in graph["criterion_nodes"]:
            self.assertEqual(
                [e[0] for e in graph["edges"]["case_to_criterion"]
                 if e[1] == criterion["id"]],
                criterion["case_ids"],
            )

    def test_04_R09_remains_global_without_case_edges(self):
        graph = self.items[0]
        self.assertEqual(graph["global_region_gate"]["id"], "R09")
        self.assertEqual(graph["global_region_gate"]["case_ids"], [])
        self.assertIs(graph["global_region_gate"]["is_case_scoped"], False)
        self.assertEqual(graph["blocker_nodes"][-1]["case_ids"], [])
        self.assertFalse(any("R09" in c["blocker_ids"] for c in graph["case_nodes"]))
        self.assertFalse(any("R09" == e[1] for e in graph["edges"]["case_to_blocker"]))

    def test_05_platform_partition_and_B11_scope(self):
        graph = self.items[0]
        self.assertEqual([(p["platform"],len(p["case_ids"])) for p in graph["platform_lanes"]],
                         [("windows",43),("android",1)])
        self.assertEqual(graph["platform_lanes"][1]["case_ids"],["android-joi-play"])
        self.assertFalse(any(z in graph["case_nodes"][-1]["blocker_ids"] for z in ("B10","B11")))
        self.assertTrue(all("B10" in c["blocker_ids"] and "B11" in c["blocker_ids"]
                            for c in graph["case_nodes"][:-1]))

    def test_06_no_physical_approval_or_playability(self):
        r=self.audited()
        self.assertEqual((r["criteria_human_approved"],r["native_cases_completed"],
                          r["native_cases_approved"],r["local_reports"],r["phase_bcd_completed"]),
                         (0,0,0,0,0))
        self.assertIs(r["sinnoh_playable"], False)
        self.assertIs(r["native_qa_authorized"], False)
        for name in ("no_human_review_accepted","no_native_qa_completed","no_game_exe_execution",
                     "no_windows_sandbox_execution","no_joiplay_execution",
                     "watch_unchanged_not_global_save_isolation",
                     "mapids_not_reserved","asset_rights_not_approved","r09_pending",
                     "no_local_save_access","no_private_attachments","no_upload"):
            self.assertIs(r["guards"][name], True)

    def test_07_report_recomputed_from_L10_not_trusted(self):
        same = l10.l09.l08.l07.l06.same
        expected = l11.expected_graph(self.items[2])
        self.assertTrue(same(self.items[0], expected))
        self.assertTrue(same(self.items[1], expected))
        self.assertTrue(same(l11.compare_trace(self.items[2], self.items[0]), l11.AUDIT_EMPTY))

    def test_08_synthetic_missing_reordered_and_platform_drift(self):
        graph = copy.deepcopy(self.items[0])
        graph["case_nodes"][0]["platform"] = "android"
        graph["edges"]["case_to_blocker"].pop()
        changed = l11.compare_trace(self.items[2], graph)
        self.assertGreater(changed["differences_found"],0)
        self.assertIn("ball-TURTWIG",changed["platform_mismatches"])
        self.assertIn("case_to_blocker",changed["missing_links"])
        self.assertFalse(changed["zero_drift"])

    def test_09_public_binary_git_blob_changed_rejected(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-l11-test-") as td:
            root = Path(td)
            for p in (l10.INDEX, l10.MIRROR):
                dst = root / p
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / p, dst)
            self.assertTrue(l11.check_l10_blob(root))
            target = root / l10.MIRROR
            target.write_bytes(target.read_bytes()+b" ")
            with self.assertRaises(ValueError):
                l11.check_l10_blob(root)

    def test_10_cli_fixed_paths_and_no_sensitive_echo(self):
        command = [sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_l11_traceability.py")]
        ok = subprocess.run(command,text=True,capture_output=True,cwd=ROOT,check=False)
        self.assertEqual(ok.returncode,0,ok.stderr)
        self.assertEqual(json.loads(ok.stdout)["counts"]["case_to_criterion_edges"],846)
        bad = subprocess.run(command+["--save",r"C:\\Users\\tester\\Save01.rxdata"],
                             text=True,capture_output=True,cwd=ROOT,check=False)
        self.assertEqual(bad.returncode,2)
        self.assertIn("SINNOH_L11_BLOCKED",bad.stderr)
        self.assertNotIn("Save01.rxdata",bad.stdout+bad.stderr)

    def test_11_source_safe_no_runtime_or_upload(self):
        src = (ROOT/"scripts/regions/audit_sinnoh_l11_traceability.py").read_text("utf8")
        for bad in ("import requests","import subprocess","import socket","httpx",
                    "os.system(","subprocess.run(","os.walk(","rglob(",
                    "shutil.copy(","from urllib","os.environ"):
            self.assertNotIn(bad,src)

    def test_negative_001_missing_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"].pop())

    def test_negative_002_duplicate_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"].append(copy.deepcopy(a["case_nodes"][0])))

    def test_negative_003_reorder_cases(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"].reverse())

    def test_negative_004_fake_case_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0].update(id="ball-FAKE"))

    def test_negative_005_duplicate_case_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][1].update(id=a["case_nodes"][0]["id"]))

    def test_negative_006_fake_case_kind(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0].update(kind="other"))

    def test_negative_007_windows_to_android(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0].update(platform="android"))

    def test_negative_008_android_to_windows(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][-1].update(platform="windows"))

    def test_negative_009_case_criteria_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0]["criteria_ids"].pop())

    def test_negative_010_case_criteria_extra(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0]["criteria_ids"].append("R09_FAKE"))

    def test_negative_011_case_criteria_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0]["criteria_ids"].reverse())

    def test_negative_012_case_blocker_b10_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0]["blocker_ids"].remove("B10"))

    def test_negative_013_case_blocker_b11_removed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0]["blocker_ids"].remove("B11"))

    def test_negative_014_android_blocker_b10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][-1]["blocker_ids"].append("B10"))

    def test_negative_015_android_blocker_b11(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][-1]["blocker_ids"].append("B11"))

    def test_negative_016_case_add_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][-1]["blocker_ids"].append("R09"))

    def test_negative_017_case_blocker_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0]["blocker_ids"].reverse())

    def test_negative_018_case_reviewed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0].update(review_state="APPROVED"))

    def test_negative_019_case_native_passed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0].update(native_status="passed"))

    def test_negative_020_case_signoff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0].update(human_signoff=True))

    def test_negative_021_case_native_qa(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0].update(native_qa_authorized=True))

    def test_negative_022_case_private_file(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["case_nodes"][0].update(save_file="Save01.rxdata"))

    def test_negative_023_criterion_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["criterion_nodes"].pop())

    def test_negative_024_criterion_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["criterion_nodes"].append(copy.deepcopy(a["criterion_nodes"][0])))

    def test_negative_025_criterion_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["criterion_nodes"].reverse())

    def test_negative_026_criterion_fake_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["criterion_nodes"][0].update(id="B09_FAKE"))

    def test_negative_027_criterion_stage_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["criterion_nodes"][0].update(stage="R08"))

    def test_negative_028_criterion_case_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["criterion_nodes"][0]["case_ids"].pop())

    def test_negative_029_criterion_case_extra(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["criterion_nodes"][0]["case_ids"].append("FAKE"))

    def test_negative_030_criterion_case_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["criterion_nodes"][0]["case_ids"].reverse())

    def test_negative_031_criterion_state(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["criterion_nodes"][0].update(review_state="REVIEWED"))

    def test_negative_032_criterion_signoff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["criterion_nodes"][0].update(human_signoff=True))

    def test_negative_033_blocker_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["blocker_nodes"].pop())

    def test_negative_034_blocker_duplicate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["blocker_nodes"].append(copy.deepcopy(a["blocker_nodes"][0])))

    def test_negative_035_blocker_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["blocker_nodes"].reverse())

    def test_negative_036_blocker_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["blocker_nodes"][0].update(id="B12"))

    def test_negative_037_blocker_scope(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["blocker_nodes"][1].update(scope="CROSS_PLATFORM"))

    def test_negative_038_blocker_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["blocker_nodes"][0].update(status="APPROVED"))

    def test_negative_039_blocker_case_missing(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["blocker_nodes"][0]["case_ids"].pop())

    def test_negative_040_blocker_case_added(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["blocker_nodes"][1]["case_ids"].append("android-joi-play"))

    def test_negative_041_blocker_case_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["blocker_nodes"][0]["case_ids"].reverse())

    def test_negative_042_blocker_native_auth(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["blocker_nodes"][0].update(native_qa_authorized=True))

    def test_negative_043_r09_case_fake(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["blocker_nodes"][-1]["case_ids"].append("ball-TURTWIG"))

    def test_negative_044_r09_scope_fake(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["blocker_nodes"][-1].update(scope="CROSS_PLATFORM"))

    def test_negative_045_r09_global_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["global_region_gate"].update(status="APPROVED"))

    def test_negative_046_r09_global_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["global_region_gate"]["case_ids"].append("ball-TURTWIG"))

    def test_negative_047_r09_case_scoped(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["global_region_gate"].update(is_case_scoped=True))

    def test_negative_048_r09_human_reviewed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["global_region_gate"].update(not_human_approved=False))

    def test_negative_049_r09_authorized(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["global_region_gate"].update(native_qa_authorized=True))

    def test_negative_050_edge_missing_case_criterion(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["case_to_criterion"].pop())

    def test_negative_051_edge_extra_case_criterion(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["case_to_criterion"].append(["FAKE","R07_NATIVE"]))

    def test_negative_052_edge_case_criterion_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["case_to_criterion"].reverse())

    def test_negative_053_edge_case_criterion_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["case_to_criterion"][0].__setitem__(1,"R09_FAKE"))

    def test_negative_054_edge_duplicate_case_criterion(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["case_to_criterion"].append(copy.deepcopy(a["edges"]["case_to_criterion"][0])))

    def test_negative_055_edge_missing_case_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["case_to_blocker"].pop())

    def test_negative_056_edge_extra_case_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["case_to_blocker"].append(["android-joi-play","B10"]))

    def test_negative_057_edge_case_blocker_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["case_to_blocker"].reverse())

    def test_negative_058_edge_add_r09_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["case_to_blocker"].append(["ball-TURTWIG","R09"]))

    def test_negative_059_edge_missing_criterion_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["criterion_to_blocker"].pop())

    def test_negative_060_edge_extra_criterion_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["criterion_to_blocker"].append(["FAKE","B09"]))

    def test_negative_061_edge_criterion_blocker_reorder(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["criterion_to_blocker"].reverse())

    def test_negative_062_edge_criterion_misattributed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["edges"]["criterion_to_blocker"][0].__setitem__(1,"R08"))

    def test_negative_063_platform_lane_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["platform_lanes"].pop())

    def test_negative_064_platform_lane_order(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["platform_lanes"].reverse())

    def test_negative_065_platform_lane_windows_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["platform_lanes"][0]["case_ids"].pop())

    def test_negative_066_platform_lane_android_id(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["platform_lanes"][1]["case_ids"].__setitem__(0,"ball-TURTWIG"))

    def test_negative_067_platform_lane_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["platform_lanes"][0].update(approved=True))

    def test_negative_068_platform_lane_status(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["platform_lanes"][1].update(status="APPROVED"))

    def test_negative_069_platform_lane_shared_gate(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["platform_lanes"][0].update(separate_native_gate=False))

    def test_negative_070_source_blob_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["source_l10"].update(git_blob_sha1="0"*40))

    def test_negative_071_source_path_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["source_l10"].update(path="private/save.json"))

    def test_negative_072_anchor_l07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["baseline_commits"].update(L07="0"*40))

    def test_negative_073_anchor_l08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["baseline_commits"].update(L08="0"*40))

    def test_negative_074_anchor_l09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["baseline_commits"].update(L09="0"*40))

    def test_negative_075_anchor_l10(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["baseline_commits"].update(L10="0"*40))

    def test_negative_076_counts_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(cases_total=45))

    def test_negative_077_counts_criteria(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(criteria_total=21))

    def test_negative_078_counts_windows(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(windows=44))

    def test_negative_079_counts_android(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(android=0))

    def test_negative_080_counts_human(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(human_approved=1))

    def test_negative_081_counts_native_completed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(native_completed=1))

    def test_negative_082_counts_native_approved(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(native_approved=1))

    def test_negative_083_counts_local_reports(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(local_reports=5))

    def test_negative_084_counts_bcd(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(phase_bcd_completed=13))

    def test_negative_085_counts_criteria_edges(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(case_to_criterion_edges=845))

    def test_negative_086_counts_blocker_edges(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(case_to_blocker_edges=217))

    def test_negative_087_counts_criterion_blocks(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(criterion_to_blocker_edges=19))

    def test_negative_088_counts_scoped_blockers(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(blockers_case_scoped=6))

    def test_negative_089_counts_global_blockers(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["counts"].update(global_blockers=0))

    def test_negative_090_gate_r07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["gates"].update(r07="APPROVED"))

    def test_negative_091_gate_r08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["gates"].update(r08="APPROVED"))

    def test_negative_092_gate_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["gates"].update(r09="APPROVED"))

    def test_negative_093_gate_b11_global(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["gates"].update(b11_global_save_isolation_proven=True))

    def test_negative_094_gate_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["gates"].update(asset_rights_approved=True))

    def test_negative_095_gate_mapids(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["gates"].update(mapids_reserved=True))

    def test_negative_096_gate_native(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["gates"].update(sinnoh_playable=True))

    def test_negative_097_guarantee_r07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(r07_pending=False))

    def test_negative_098_guarantee_r08(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(r08_pending=False))

    def test_negative_099_guarantee_r09(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(r09_pending=False))

    def test_negative_100_guarantee_windows_android(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(windows_android_independent=False))

    def test_negative_101_guarantee_watch_global(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(watch_unchanged_not_global_save_isolation=False))

    def test_negative_102_guarantee_mapids(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(mapids_not_reserved=False))

    def test_negative_103_guarantee_rights(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(asset_rights_not_approved=False))

    def test_negative_104_guarantee_human(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(no_human_review_accepted=False))

    def test_negative_105_guarantee_qa(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(no_native_qa_completed=False))

    def test_negative_106_guarantee_game(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(no_game_exe_execution=False))

    def test_negative_107_guarantee_sandbox(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(no_windows_sandbox_execution=False))

    def test_negative_108_guarantee_joiplay(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(no_joiplay_execution=False))

    def test_negative_109_guarantee_save(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(no_local_save_access=False))

    def test_negative_110_guarantee_private(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(no_private_attachments=False))

    def test_negative_111_guarantee_installer(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(no_installer=False))

    def test_negative_112_guarantee_upload(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(no_upload=False))

    def test_negative_113_guarantee_playable(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(sinnoh_playable=True))

    def test_negative_114_guarantee_android_l05(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["guarantees"].update(local_android_l05_complete=True))

    def test_negative_115_drift_missing_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["public_drift_audit"]["missing_case_ids"].append("ball-TURTWIG"))

    def test_negative_116_drift_added_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["public_drift_audit"]["added_case_ids"].append("FAKE"))

    def test_negative_117_drift_reordered_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["public_drift_audit"]["reordered_case_ids"].append("ball-TURTWIG"))

    def test_negative_118_drift_missing_criteria(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["public_drift_audit"]["missing_criterion_ids"].append("B09_ORIGIN"))

    def test_negative_119_drift_added_criteria(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["public_drift_audit"]["added_criterion_ids"].append("FAKE"))

    def test_negative_120_drift_missing_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["public_drift_audit"]["missing_links"].append("case_to_blocker"))

    def test_negative_121_drift_unexpected_links(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["public_drift_audit"]["unexpected_links"].append("case_to_criterion"))

    def test_negative_122_drift_platform(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["public_drift_audit"]["platform_mismatches"].append("ball-TURTWIG"))

    def test_negative_123_drift_scope(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["public_drift_audit"]["blocker_scope_mismatches"].append("B11"))

    def test_negative_124_drift_count(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["public_drift_audit"].update(differences_found=1))

    def test_negative_125_drift_zero_flag(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a["public_drift_audit"].update(zero_drift=False))

    def test_negative_126_schema_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a.update(schema=2))

    def test_negative_127_stage_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a.update(stage="L12"))

    def test_negative_128_status_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a.update(status="NATIVE_APPROVED"))

    def test_negative_129_mode_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a.update(mode="CAN_EXECUTE_GAME"))

    def test_negative_130_version_changed(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a.update(version=2))

    def test_negative_131_extra_private(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: a.update(save_file="Save01.rxdata"))

    def test_negative_132_mirror_case_mutated(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: b["case_nodes"][0].update(id="FAKE"))

    def test_negative_133_mirror_edges_mutated(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: b["edges"]["case_to_blocker"].pop())

    def test_negative_134_mirror_signoff_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: b["case_nodes"][0].update(human_signoff=True))

    def test_negative_135_mirror_r09_forged(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: b["global_region_gate"].update(status="APPROVED"))

    def test_negative_136_upstream_l10_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: c["cases"][0].update(approved=True))

    def test_negative_137_upstream_l10_blocker(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: c["blockers"][-1].update(status="APPROVED"))

    def test_negative_138_upstream_l10_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: d["cases"][0].update(id="FAKE"))

    def test_negative_139_upstream_l09_case(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: e["case_handoff"][0].update(native_status="passed"))

    def test_negative_140_upstream_l08_snap(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: f["cases"][0].update(native_qa_authorized=True))

    def test_negative_141_upstream_l08_diff(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: g["comparisons"][0]["added_ids"].append("FAKE"))

    def test_negative_142_upstream_g12(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: h["cases"][0].update(native_status="passed"))

    def test_negative_143_upstream_l04(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: i["rows"][0]["criteria"][0].update(local_human_signoff=True))

    def test_negative_144_upstream_l05(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: j.update(asset_rights_approved=True))

    def test_negative_145_upstream_l06(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: k.update(mapids_reserved=True))

    def test_negative_146_upstream_l07(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: l["cases"][-1].update(platform="windows"))

    def test_negative_147_upstream_l07_mirror(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: m["cases"][0].update(id="FAKE"))

    def test_negative_148_upstream_l07_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: n["counts"].update(native_approved=1))

    def test_negative_149_upstream_l06_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: o.update(native_cases_approved=1))

    def test_negative_150_upstream_l05_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: p.update(native_cases_approved=1))

    def test_negative_151_upstream_l04_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: q.update(criteria_reviewed=1))

    def test_negative_152_upstream_g12_report(self):
        self.rejected(lambda a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,s: s.update(evidence_accepted_cases=1))

if __name__ == '__main__':
    unittest.main()
