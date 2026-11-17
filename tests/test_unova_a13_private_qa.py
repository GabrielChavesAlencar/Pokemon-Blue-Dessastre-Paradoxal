"""A13 private QA copy: synthetic OS-level correctness and no-save safety tests."""
from __future__ import annotations
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_a13_private_qa as a13

class A13CopyTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="unova-a13-")
        self.addCleanup(temp.cleanup)
        root=Path(temp.name)
        self.game=root/"PokemonBlueDessastreParadoxal"/"game"
        self.game.mkdir(parents=True)
        self.qa=root/"qa-copies"
        data=self.game/"Data";data.mkdir()
        (self.game/"Game.exe").write_bytes(b"sample exe not runnable")
        (self.game/"Game.ini").write_text("[Game]\nTitle=Pokemon Blue\n")
        (self.game/"mkxp.json").write_text(
            '{"windowTitle":"Pokemon Blue","dataPathApp":"Decades","dataPathOrg":"BMS"}')
        (data/"MapInfos.rxdata").write_bytes(b"synthetic infos")
        (data/"Map001.rxdata").write_bytes(b"synthetic map")
        (data/"Scripts.rxdata").write_bytes(b"synthetic scripts")
        (data/"System.rxdata").write_bytes(b"synthetic system")
        (data/"Map002.rxdata").write_bytes(b"synthetic other map")
        (self.game/"Graphics"/"Characters").mkdir(parents=True)
        (self.game/"Graphics"/"Characters"/"hero.png").write_bytes(b"png")
        self.a04={"phase":"A04","sources":{"DECADES":{
            "mapinfos_sha256":a13.hash_file(data/"MapInfos.rxdata"),
            "maps":[{"id":1,"source_filename":"Map001.rxdata",
                     "sha256":a13.hash_file(data/"Map001.rxdata")}]}}}
        self.a12={"phase":"A12","status":"A12_SOURCE_REVIEW_DONE_ISOLATED_QA_NOT_CREATED",
            "mapinfos_sha256":self.a04["sources"]["DECADES"]["mapinfos_sha256"],
            "can_install":False,"can_reserve_mapids":False}
    def clone(self):
        return a13.clone(self.game,self.qa,self.a04,self.a12)

    def test_01_real_copy_and_report(self):
        r=self.clone()
        self.assertEqual(r["status"],a13.STATUS)
        cloned=Path(r["path"])
        self.assertTrue((cloned/"Game.exe").is_file())
        self.assertEqual((cloned/"Data/Map001.rxdata").read_bytes(),b"synthetic map")
        self.assertTrue((cloned/a13.INVENTORY_FILE).exists())
        self.assertTrue((cloned/a13.KEEP_FILE).exists())
        self.assertFalse(r["game_exe_launched"])
        self.assertFalse(r["unova_installed"])
    def test_02_QA_namespace_unique(self):
        r=self.clone();p=Path(r["path"])
        config=json.loads((p/"mkxp.json").read_text())
        self.assertNotEqual(config["dataPathApp"],"Decades")
        self.assertNotEqual(config["dataPathOrg"],"BMS")
        self.assertIn("Blue Unova QA",config["windowTitle"])
        self.assertIn(config["windowTitle"],(p/"Game.ini").read_text())
        self.assertEqual(json.loads((p/a13.INVENTORY_FILE).read_text())["runtime_save_isolation_tested"],False)
    def test_03_original_is_untouched(self):
        before={p.relative_to(self.game).as_posix():p.read_bytes()
                for p in self.game.rglob("*") if p.is_file()}
        self.clone()
        after={p.relative_to(self.game).as_posix():p.read_bytes()
                for p in self.game.rglob("*") if p.is_file()}
        self.assertEqual(before,after)
    def test_04_save_folders_and_files_excluded(self):
        (self.game/"Saves").mkdir()
        (self.game/"Saves"/"File1.rxdata").write_bytes(b"PRIVATE SAVE")
        (self.game/"Data"/"File2.rxdata").write_bytes(b"PRIVATE SAVE")
        (self.game/"Data"/"Save3.rxdata").write_bytes(b"PRIVATE SAVE")
        (self.game/"Savedata").mkdir()
        (self.game/"Savedata"/"save.json").write_bytes(b"PRIVATE SAVE")
        path=Path(self.clone()["path"])
        self.assertFalse((path/"Saves").exists())
        self.assertFalse((path/"Savedata").exists())
        self.assertFalse((path/"Data"/"File2.rxdata").exists())
        self.assertFalse((path/"Data"/"Save3.rxdata").exists())
    def test_05_idempotent_verifies_existing_qa(self):
        first=self.clone()
        second=self.clone()
        self.assertEqual(first["path"],second["path"])
        self.assertEqual(second["status"],"QA_BASELINE_EXISTING_VERIFIED_RUNTIME_UNVERIFIED")
    def test_06_tampered_qa_denied_without_deletion(self):
        path=Path(self.clone()["path"])
        (path/"Data/Map002.rxdata").write_bytes(b"tampered")
        with self.assertRaises(ValueError):self.clone()
        self.assertEqual((path/"Data/Map002.rxdata").read_bytes(),b"tampered")
    def test_07_qa_extra_file_denied(self):
        path=Path(self.clone()["path"])
        (path/"evil.exe").write_bytes(b"extra")
        with self.assertRaises(ValueError):self.clone()
    def test_08_no_reuse_qa_without_manifest(self):
        path=Path(self.clone()["path"])
        (path/a13.INVENTORY_FILE).unlink()
        with self.assertRaises(ValueError):self.clone()
        self.assertTrue(path.exists())
    def test_09_bad_game_ini_is_denied(self):
        (self.game/"Game.ini").write_text("[Game]\nSomeKey=missing\n")
        with self.assertRaises(ValueError):self.clone()
    def test_10_save_path_override_denied(self):
        (self.game/"mkxp.json").write_text(
            '{"custom":{"savePath":"C:/Users/Player/saves"},"dataPathApp":"Decades"}')
        with self.assertRaises(ValueError):self.clone()
        self.assertFalse(self.qa.exists())
    def test_11_malformed_mkxp_denied(self):
        (self.game/"mkxp.json").write_text("{bad json")
        with self.assertRaises(ValueError):self.clone()
    def test_12_jsonc_and_trailing_comma(self):
        (self.game/"mkxp.json").write_text(
            '{//comment\n"dataPathApp":"Decades", "dataPathOrg":"Studio",\n}')
        self.assertEqual(self.clone()["status"],a13.STATUS)
    def test_13_changed_mapinfos_denied(self):
        (self.game/"Data/MapInfos.rxdata").write_bytes(b"changed")
        with self.assertRaises(ValueError):self.clone()
        self.assertFalse(self.qa.exists())
    def test_14_changed_map001_denied(self):
        (self.game/"Data/Map001.rxdata").write_bytes(b"changed")
        with self.assertRaises(ValueError):self.clone()
    def test_15_broken_a12_gate_denied(self):
        self.a12["status"]="FORGED_RESERVATION_APPROVED"
        with self.assertRaises(ValueError):self.clone()
    def test_16_reparse_or_symlink_source_denied(self):
        destination=self.game/"Data/Map999.rxdata"
        target=self.game/"Data/Map001.rxdata"
        try:destination.symlink_to(target)
        except OSError:self.skipTest("Symlink unavailable")
        with self.assertRaises(ValueError):self.clone()
    def test_17_private_root_inside_game_denied(self):
        with self.assertRaises(ValueError):
            a13.clone(self.game,self.game/"unova-qa",self.a04,self.a12)
    def test_18_insufficient_disk_space_blocks_without_copy(self):
        sample=type("Space",(),{"free":0})()
        with patch.object(a13.shutil,"disk_usage",return_value=sample):
            with self.assertRaises(ValueError):self.clone()
        self.assertFalse(any(self.qa.iterdir()))
    def test_19_source_changes_midcopy_cleanup_staging(self):
        original=a13.hash_file
        def corrupt_after_first_copied(path):
            if Path(path).parent.name.startswith(".building-qa-unova-a13-"):
                raise ValueError("synthetic disk failure")
            return original(path)
        with patch.object(a13,"hash_file",side_effect=corrupt_after_first_copied):
            with self.assertRaises(ValueError):self.clone()
        self.assertEqual(list(self.qa.iterdir()),[])
    def test_20_missing_executable_denied(self):
        (self.game/"Game.exe").unlink()
        with self.assertRaises(ValueError):self.clone()
    def test_21_symlink_qa_folder_blocked(self):
        destination=self.qa
        external=self.game.parent/"outside"
        external.mkdir()
        try:destination.symlink_to(external,target_is_directory=True)
        except OSError:self.skipTest("Symlink unavailable")
        with self.assertRaises(ValueError):self.clone()
        self.assertEqual(list(external.iterdir()),[])
    def test_22_repeated_diagnostic_report_immutable(self):
        report={"phase":"A13","status":"QA_BASELINE_COPIED_RUNTIME_UNVERIFIED"}
        work=self.game.parent/"work";work.mkdir()
        path=a13.save(work,report)
        self.assertEqual(path,a13.save(work,report))
        self.assertEqual(json.loads(path.read_text()),report)
    def test_23_fake_clean_A12_cannot_install(self):
        self.a12["can_install"]=True
        with self.assertRaises(ValueError):self.clone()
    def test_24_source_contains_private_cache_excludes_it(self):
        cache=self.game/".blue-work";cache.mkdir()
        (cache/"user-secret.json").write_text('{"private":true}')
        path=Path(self.clone()["path"])
        self.assertFalse((path/".blue-work").exists())
        self.assertFalse((path/"Saves").exists())
    def test_26_progress_messages_verify_copy(self):
        messages=[]
        r=a13.clone(self.game,self.qa,self.a04,self.a12,progress=messages.append)
        self.assertEqual(r["status"],a13.STATUS)
        self.assertTrue(any("Iniciando inventario" in m for m in messages))
        self.assertTrue(any("Copia QA criada e verificada" in m for m in messages))
        self.assertTrue(any("perfil" in m for m in messages))

    def test_25_snapshot_report_no_gameplay_approval(self):
        r=self.clone()
        doc=json.loads((Path(r["path"])/a13.INVENTORY_FILE).read_text())
        self.assertFalse(doc["approved_for_gameplay"])
        self.assertFalse(doc["allowed_to_launch_without_manual_qa"])
        self.assertEqual(doc["bar_a_completed"],0)

if __name__=="__main__":
    unittest.main()
