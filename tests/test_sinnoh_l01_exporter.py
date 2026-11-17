"""L01 exporter: strict metadata projections; no local game, save or private output."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import export_sinnoh_l01_reports as l01


class SinnohL01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=l01.l00.read_json(ROOT,l01.l00.CONTRACTS["B09"])

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="sinnoh-l01-synthetic-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/l01.INPUT_DIR
        self.source.mkdir(parents=True)
        self.fixture=self.complete_fixture()

    @staticmethod
    def complete_fixture():
        a="a"*64
        receipt={
            "status":l01.g01.STATUS,
            "relative_path":l01.g01.STAGE_BASE+"a"*16,
            "files_reused":999,"files_copied":68,"files_repaired":1,
            "native_file_count":1000,"sinnoh_overlay_files":70,
            "map_ids_clone_total":702,"saves_copied":False,
            "game_exe_executed":False,"safe_to_launch":False,
            "phase_b_approved":0,"r07_complete":False,
            "b08_maps_validated":54,"b08_pngs_validated":14,
            "b08_nonzero_terrain_cells":484722,
            "future_reservations_verified":False,"native_game_tested":False,
            "joiplay_tested":False,"can_install_live_game":False,
        }
        dry={
            "status":"B09_DRY_RUN_NO_FILES_WRITTEN","plan_sha256":a,
            "native_files_count":1000,"overlay_files_count":70,
            "estimated_bytes":1500000,"expected_map_count":702,
            "excluded_private_files":3,
            "game_exe_will_be_copied_but_not_launched":True,
            "source_game_untouched":True,"phase_b_approved":0,
            "b08_maps_validated":54,"b08_pngs_validated":14,
            "b08_nonzero_terrain_cells":484722,
            "future_reservations_verified":False,"native_game_tested":False,
            "joiplay_tested":False,"can_install_live_game":False,
            "r07_complete":False,
        }
        b10={
            "schema":1,"region":"SINNOH","stage":"B10",
            "status":"WSB_CONFIG_PREPARED_NOT_LAUNCHED",
            "source_clone_sha256":a,"source_stage_sha256":"c"*64,
            "native_map_ids":648,"sinnoh_terrain_map_ids":54,
            "expected_total_maps":702,"all_cloned_files_sha_verified":True,
            "sandbox_feature_enabled_on_host":True,
            "sandbox_session_started":False,"game_exe_started":False,
            "save_write_isolation_runtime_verified":False,
            "host_save_directories_mapped":False,
            "mapped_folders_read_only":True,"internet_networking_enabled":False,
            "clipboard_enabled":False,"guest_game_copy_completed":False,
            "rights_verified":False,"r07_complete":False,"r08_complete":False,
            "r09_complete":False,"phase_b_approved":0,"phase_c_approved":0,
            "phase_d_approved":0,
            "note":"Host config verified but no VM run.",
            "config_relative_path":".blue-work/sinnoh-b10-sandbox/session-safe/B10_ISOLAMENTO.wsb",
            "guest_instructions":r"Command inside C:\SinnohB10Game; DO NOT SHARE",
            "can_start_game_on_host":False,
        }
        before={
            "stage":"B11","status":"HOST_SAVE_SNAPSHOT_BEFORE_RECORDED_SANDBOX_NOT_RUN",
            "watch_id":"b"*32,"clone_sha256":a,
            "monitored_directories_count":2,"scope_selection_mode":"explicit",
            "default_scopes_not_monitored":None,"monitored_files_before":3,
            "bytes_hashed_before":1337,
            "config_relative_path":".blue-work/sinnoh-b11-save-audit/watch-secret/B11_ISOLAMENTO.wsb",
            "paths_names_and_saves_in_report":False,
            "windows_sandbox_started":False,"Game_exe_started":False,
            "host_saves_runtime_isolation_confirmed":False,
            "coverage_is_partial":True,"r07_complete":False,"phase_b_approved":0,
        }
        after={
            "stage":"B11","status":"HOST_WATCHED_FILES_UNCHANGED_LIMITED_EVIDENCE",
            "watch_id":"b"*32,"monitored_directories_count":2,
            "scope_selection_mode":"explicit","default_scopes_not_monitored":None,
            "coverage_is_partial":True,"monitored_files_before":3,
            "monitored_files_after":3,"bytes_hashed_after":1337,
            "files_added":0,"files_removed":0,"files_changed":0,
            "watch_unchanged":True,"guest_observation_self_reported":"not_run",
            "guest_vm_execution_independently_verified":False,
            "complete_host_save_coverage_verified":False,
            "true_runtime_save_path_in_source_verified":False,
            "host_saves_globally_isolated_proven":False,
            "assets_rights_verified":False,"R07_R08_R09_approved":False,
            "gameplay_approved":False,"phase_b_approved":0,
            "phase_c_approved":0,"phase_d_approved":0,
            "paths_names_and_saves_in_report":False,
            "next_action":"Upload only this JSON summary, never private-baseline.json or save files.",
        }
        r07={
            "schema":1,"region":"SINNOH","task":"S07","substep":"R07",
            "mode":"LOCAL_RESERVATIONS_DIAGNOSTIC_ONLY",
            "status":"BLOCKED_MISSING_NATIVE_RESERVATION_EVIDENCE",
            "native_snapshot_present":False,"native_occupied_count":None,
            "native_mapinfos_sha256":None,
            "future_regional_reservations":{},
            "future_regions_with_evidence":0,
            "future_regions_required":["KANTO","JOHTO","HOENN"],
            "sinnoh_candidate_destination_ids":None,
            "collisions":[],"blockers":["No physical MapInfos yet"],
            "candidate_safety_reviewable":False,
            "r07_complete":False,"r08_real_maps_imported":False,
            "r09_game_exe_joiplay_tested":False,
            "rights_verified":False,"may_apply_to_main_game":False,
            "game_or_saves_modified":False,"native_gameplay_verified":False,
            "note":"not independently approved",
        }
        r08={
            "schema":1,"region":"SINNOH","stage":"R08",
            "kind":"MANUAL_AGGREGATE_REVIEW_COUNT_ONLY",
            "status":"RIGHTS_REVIEW_PENDING",
            "source_expected_png_count":14,
            "per_asset_licenses_reviewed_count":0,
            "source_asset_rights_verified":False,"r08_complete":False,
        }
        return {"b09_receipt":receipt,"b09_dry_run":dry,
                "b10":b10,"b11_before":before,"b11_after":after,
                "r07":r07,"r08":r08}

    def stage(self,*keys):
        for key in keys:
            p=self.source/l01.INPUT_FILES[key]
            p.write_text(json.dumps(self.fixture[key]),encoding="utf-8")

    def bundle(self):
        return l01.collect(self.root,ROOT)

    def fail(self):
        with self.assertRaisesRegex(ValueError,"SINNOH_L01_BLOCKED"):
            self.bundle()

    def test_01_default_no_source_files_never_approves(self):
        b=self.bundle()
        self.assertEqual(set(b["reports"]),set(l01.l00.STAGES))
        self.assertTrue(all(v is None for v in b["reports"].values()))
        self.assertFalse((self.root/l01.DEST).exists())

    def test_02_all_seven_real_source_shapes_project_to_five_safe_records(self):
        self.stage(*l01.INPUT_FILES)
        bundle=self.bundle()
        self.assertTrue(all(v is not None for v in bundle["reports"].values()))
        self.assertEqual(bundle["reports"]["B09"]["map_ids_clone_total"],702)
        self.assertEqual(bundle["reports"]["B10"]["expected_total_maps"],702)
        self.assertTrue(bundle["reports"]["B11"]["after"]["coverage_is_partial"])
        self.assertFalse(bundle["reports"]["B11"]["after"]["host_saves_globally_isolated_proven"])
        self.assertFalse(bundle["reports"]["R07"]["r07_complete"])
        self.assertFalse(bundle["reports"]["R08"]["r08_complete"])

    def test_03_B09_requires_receipt_and_dryrun_pair(self):
        self.stage("b09_receipt")
        self.fail()
        (self.source/l01.INPUT_FILES["b09_receipt"]).unlink()
        self.stage("b09_dry_run")
        self.fail()

    def test_04_B09_source_strict_validator_no_missing_extra_or_private_fields(self):
        self.stage("b09_receipt","b09_dry_run")
        self.fixture["b09_receipt"]["hmac_key"]="secret"
        self.stage("b09_receipt")
        self.fail()
        del self.fixture["b09_receipt"]["hmac_key"]
        self.fixture["b09_receipt"].pop("files_repaired")
        self.stage("b09_receipt")
        self.fail()

    def test_05_B09_receipt_plan_SHA_mismatch_rejected(self):
        self.stage("b09_receipt","b09_dry_run")
        self.fixture["b09_dry_run"]["plan_sha256"]="d"*64
        self.stage("b09_dry_run")
        self.fail()

    def test_06_B09_wrong_count_or_forged_launch_cannot_export(self):
        for name,val in (("map_ids_clone_total",703),
                         ("native_file_count",1),("game_exe_executed",True),
                         ("safe_to_launch",True),("r07_complete",True),
                         ("saves_copied",True),("phase_b_approved",1)):
            with self.subTest(name=name):
                self.fixture=self.complete_fixture()
                self.fixture["b09_receipt"][name]=val
                self.stage("b09_receipt","b09_dry_run")
                self.fail()

    def test_07_B10_without_B09_receipt_not_silently_accepted(self):
        self.stage("b10")
        self.fail()

    def test_08_B10_real_session_source_strict_fields_and_secret_rejected(self):
        self.stage("b09_receipt","b09_dry_run","b10")
        self.fixture["b10"]["private-baseline.json"]="LEAK"
        self.stage("b10")
        self.fail()

    def test_09_B10_network_clipboard_guest_host_and_rights_blocked(self):
        for name,val in (("internet_networking_enabled",True),
                         ("clipboard_enabled",True),("mapped_folders_read_only",False),
                         ("sandbox_session_started",True),
                         ("game_exe_started",True),("host_save_directories_mapped",True),
                         ("guest_game_copy_completed",True),("rights_verified",True),
                         ("phase_c_approved",1),
                         ("can_start_game_on_host",True)):
            with self.subTest(name=name):
                self.fixture=self.complete_fixture()
                self.fixture["b10"][name]=val
                self.stage("b09_receipt","b09_dry_run","b10")
                self.fail()

    def test_10_B10_SHA_cross_plan_mismatch_rejected(self):
        self.fixture["b10"]["source_clone_sha256"]="c"*64
        self.stage("b09_receipt","b09_dry_run","b10")
        self.fail()

    def test_11_B11_requires_before_and_after_pair(self):
        self.stage("b11_before")
        self.fail()
        (self.source/l01.INPUT_FILES["b11_before"]).unlink()
        self.stage("b11_after")
        self.fail()

    def test_12_B11_watch_identifier_and_plan_SHA_match_before_export(self):
        for key,val in (("watch_id","c"*32),("watch_id","private/test"),
                        ("monitored_files_before",4)):
            self.fixture=self.complete_fixture()
            self.fixture["b11_after"][key]=val
            self.stage("b11_before","b11_after")
            with self.subTest(key=key,val=val):self.fail()
        self.fixture=self.complete_fixture()
        self.fixture["b11_before"]["clone_sha256"]="c"*64
        self.stage("b09_receipt","b09_dry_run","b11_before","b11_after")
        self.fail()

    def test_13_B11_unchanged_does_not_prove_global_isolation(self):
        self.stage("b11_before","b11_after")
        bundle=self.bundle()
        record=bundle["reports"]["B11"]
        self.assertTrue(record["after"]["watch_unchanged"])
        self.assertTrue(record["after"]["coverage_is_partial"])
        self.assertFalse(record["after"]["host_saves_globally_isolated_proven"])

    def test_14_B11_changed_files_are_preserved_not_suppressed(self):
        self.fixture["b11_after"].update(
            files_changed=1,watch_unchanged=False,
            status="HOST_WATCHED_FILES_CHANGED_REVIEW_REQUIRED")
        self.stage("b11_before","b11_after")
        b=self.bundle()
        self.assertEqual(b["reports"]["B11"]["after"]["files_changed"],1)
        self.assertFalse(b["reports"]["B11"]["after"]["watch_unchanged"])

    def test_15_B11_hidden_change_or_false_approval_blocked(self):
        for name,val in (("files_changed",1),
                         ("host_saves_globally_isolated_proven",True),
                         ("guest_vm_execution_independently_verified",True),
                         ("coverage_is_partial",False),
                         ("phase_d_approved",1),
                         ("paths_names_and_saves_in_report",True)):
            with self.subTest(name=name):
                self.fixture=self.complete_fixture()
                self.fixture["b11_after"][name]=val
                self.stage("b11_before","b11_after")
                self.fail()

    def test_16_B11_unknown_baseline_fields_rejected(self):
        self.fixture["b11_before"]["hmac_key"]="private"
        self.stage("b11_before","b11_after")
        self.fail()
        self.fixture=self.complete_fixture()
        self.fixture["b11_after"]["baseline"]={"Save01.rxdata":"AAAA"}
        self.stage("b11_before","b11_after")
        self.fail()

    def test_17_B11_report_never_contains_watch_id_or_private_path(self):
        self.stage("b11_before","b11_after")
        raw=json.dumps(self.bundle())
        for forbidden in ("watch_id","clone_sha256","config_relative_path",
                          "private-baseline.json","C:\\SinnohB10Game",
                          "next_action","hmac_key"):
            self.assertNotIn(forbidden,raw)

    def test_18_R07_raw_fields_project_without_ownership_statements(self):
        self.fixture["r07"]["future_regional_reservations"]={
            "KANTO":{"ownership_evidence":"C:\\Users\\tester\\private-note.txt"},
        }
        self.stage("r07")
        raw=json.dumps(self.bundle())
        self.assertNotIn("ownership_evidence",raw)
        self.assertNotIn("C:\\Users",raw)
        self.assertFalse(json.loads(raw)["reports"]["R07"]["r07_complete"])

    def test_19_R07_false_accepted_ownership_or_inventory_blocked(self):
        for name,val in (("r07_complete",True),
                         ("native_snapshot_present",True),
                         ("rights_verified",True),
                         ("future_regions_with_evidence",4),
                         ("candidate_safety_reviewable",True)):
            with self.subTest(name=name):
                self.fixture=self.complete_fixture()
                self.fixture["r07"][name]=val
                self.stage("r07")
                self.fail()

    def test_20_R07_collision_count_is_derived_not_trusted(self):
        self.fixture["r07"]["collisions"]=[{"id":442,"reason":"FUTURE_RESERVED_KANTO"}]
        self.stage("r07")
        b=self.bundle()
        self.assertEqual(b["reports"]["R07"]["collisions_count"],1)
        self.assertFalse(b["reports"]["R07"]["candidate_safety_reviewable"])

    def test_21_R08_minimal_manual_count_only_not_approval(self):
        self.fixture["r08"]["per_asset_licenses_reviewed_count"]=14
        self.stage("r08")
        b=self.bundle()
        self.assertEqual(b["reports"]["R08"]["per_asset_licenses_reviewed_count"],14)
        self.assertFalse(b["reports"]["R08"]["source_asset_rights_verified"])
        self.assertFalse(b["reports"]["R08"]["can_install"])

    def test_22_R08_wrong_status_extra_asset_list_or_false_rights_blocked(self):
        for key,value in (("status","RIGHTS_APPROVED"),
                          ("kind","AUTO_SCAN_REAL_ASSETS"),
                          ("source_asset_rights_verified",True),
                          ("r08_complete",True),
                          ("per_asset_licenses_reviewed_count",15),
                          ("source_expected_png_count",13),
                          ("names",["C:\\Users\\private\\sprites.png"])):
            with self.subTest(key=key):
                self.fixture=self.complete_fixture()
                self.fixture["r08"][key]=value
                self.stage("r08")
                self.fail()

    def test_23_no_recursive_scan_no_game_file_read_or_mutation(self):
        game=self.root/"game"
        game.mkdir()
        (game/"Game.exe").write_bytes(b"FAKE GAME EXECUTABLE")
        (game/"Save01.rxdata").write_bytes(b"private synthetic save bytes")
        (self.root/"private-baseline.json").write_text("SECRET B11",encoding="utf-8")
        self.stage(*l01.INPUT_FILES)
        b=self.bundle()
        self.assertNotIn("private synthetic save bytes",json.dumps(b))
        self.assertEqual((game/"Save01.rxdata").read_bytes(),b"private synthetic save bytes")
        self.assertFalse((self.root/l01.DEST).exists())

    def test_24_preview_is_read_only_write_explicit_creates_only_fixed_file(self):
        self.stage(*l01.INPUT_FILES)
        bundle=self.bundle()
        target=self.root/l01.DEST
        self.assertFalse(target.exists())
        written=l01.write_explicit(self.root,bundle)
        self.assertEqual(written,target)
        self.assertEqual(json.loads(target.read_text("utf-8")),bundle)
        self.assertEqual(set(target.parent.iterdir()),{target})
        if os.name!="nt":
            self.assertEqual(stat.S_IMODE(target.stat().st_mode),0o600)

    def test_25_output_symlink_refused_without_overwriting_target(self):
        self.stage("r08")
        b=self.bundle()
        target=self.root/l01.DEST
        target.parent.mkdir(parents=True)
        victim=self.root/"victim.txt"
        victim.write_text("do not overwrite",encoding="utf-8")
        try:target.symlink_to(victim)
        except (OSError,NotImplementedError):self.skipTest("symlink unsupported")
        with self.assertRaisesRegex(ValueError,"SINNOH_L01_BLOCKED"):
            l01.write_explicit(self.root,b)
        self.assertEqual(victim.read_text("utf-8"),"do not overwrite")

    def test_26_input_symlink_to_private_baseline_refused(self):
        private=self.root/"private-baseline.json"
        private.write_text('{"hmac_key":"SECRET"}',encoding="utf-8")
        link=self.source/l01.INPUT_FILES["b11_before"]
        try:link.symlink_to(private)
        except (OSError,NotImplementedError):self.skipTest("symlink unsupported")
        self.fail()

    def test_27_oversized_or_invalid_JSON_refused_without_echoing_data(self):
        path=self.source/l01.INPUT_FILES["r08"]
        path.write_text("x"*65537,encoding="utf-8")
        self.fail()
        path.write_text('{"secret":"C:\\\\Users\\\\tester\\\\Save01.rxdata"',encoding="utf-8")
        self.fail()

    def test_28_unknown_cli_args_must_not_echo_private_path(self):
        private=r"C:\Users\tester\Save01.rxdata"
        p=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/export_sinnoh_l01_reports.py"),
            "--file",private],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(p.returncode,2)
        self.assertIn("SINNOH_L01_BLOCKED",p.stderr)
        self.assertNotIn(private,p.stderr)
        self.assertNotIn("C:\\Users",p.stderr)

    def test_29_local_default_cli_never_writes_or_uploads(self):
        p=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/export_sinnoh_l01_reports.py")],
            capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(p.returncode,0,p.stderr)
        bundle=json.loads(p.stdout)
        self.assertEqual(bundle["region"],"SINNOH")
        self.assertTrue(all(value is None for value in bundle["reports"].values()))
        self.assertFalse((ROOT/l01.DEST).exists())

    def test_30_no_network_spawn_or_save_read_in_exporter_source(self):
        src=(ROOT/"scripts/regions/export_sinnoh_l01_reports.py").read_text("utf8")
        for forbidden in ("subprocess.","socket.","requests.","urllib.request",
                          "Game.exe').read_bytes", "private-baseline.json\").read",
                          "b11.fingerprint(", "b10.prepare_session(",
                          "os.system(", "os.popen(", "shutil.copytree("):
            self.assertNotIn(forbidden,src)
        self.assertIn('DEST=l00.PRIVATE_REPORT',src)
        self.assertIn("write_explicit",src)


if __name__=="__main__":
    unittest.main()
