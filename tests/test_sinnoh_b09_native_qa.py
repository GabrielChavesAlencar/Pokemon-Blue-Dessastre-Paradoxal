"""Sinnoh B09: synthetic B07+B08→native sandbox, fail-closed + rollback."""
from __future__ import annotations
import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"scripts/regions"),str(ROOT/"tests")]
import build_sinnoh_b09_native_qa as b09
import audit_sinnoh_b08_private_qa as b08
from test_sinnoh_b08_private_qa import B08Tests

class B09Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=b09.load(b09.CONTRACT)
        cls.b08=b09.load(b09.B08)
        cls.b07=b09.load(b09.B07)
        cls.b06=b09.load(b09.B06)
        cls.b00=b09.load(b09.B00)
        cls.b01=b09.load(b09.B01)
        cls.b04=b09.load(b09.B04)
        cls.b05=b09.load(b09.B05)

    def fixture(self):
        helper=B08Tests("test_01_frozen_contract_is_safe")
        self.addCleanup(helper.doCleanups)
        project,files,infos,tiles,dry,rows=helper.fixture()
        report=b08.audit_files(files,infos,tiles,
                [row["candidate_destination_map_id"] for row in rows],
                expected_png_count=3,expected_cells=162)
        b08.prepare_qa(project,dry["plan_sha256"],files,report,
                       live_game_verified=True)
        other=tempfile.TemporaryDirectory()
        self.addCleanup(other.cleanup)
        game=Path(other.name)/"game"
        data=game/"Data";data.mkdir(parents=True)
        (data/"MapInfos.rxdata").write_bytes(infos)
        (data/"Tilesets.rxdata").write_bytes(tiles)
        (data/"Map001.rxdata").write_bytes(b"existing native map")
        (game/"Game.exe").write_bytes(b"MZ\x00synthetic executable - never run")
        (game/"Game.ini").write_bytes(b"[Game]\r\nTitle=Synthetic")
        (game/"Save01.rxdata").write_bytes(b"SECRET SAVE")
        (game/"Saves").mkdir()
        (game/"Saves"/"Save02.rxdata").write_bytes(b"SECRET SAVE 2")
        (game/"Graphics"/"Tilesets").mkdir(parents=True)
        (game/"Graphics"/"Tilesets"/"Native.png").write_bytes(b"native graphic")
        return project,game,files,infos,tiles,dry,rows,report

    def check_real_synthetic_overlay(self,project,dry,infos,tiles,rows):
        def audit(files,native_infos,native_tiles,expected):
            self.assertEqual(native_infos,infos)
            self.assertEqual(native_tiles,tiles)
            return b08.audit_files(files,native_infos,native_tiles,expected,
                                   expected_png_count=3,expected_cells=162)
        with patch.object(b09,"audit_files",side_effect=audit):
            return b09.check_qa_overlay(project,dry["plan_sha256"],
                native_raw={"MapInfos.rxdata":infos,"Tilesets.rxdata":tiles},
                expected_ids=[x["candidate_destination_map_id"] for x in rows])

    def test_01_b09_metadata_safe(self):
        terrain=b09.check_contract(self.c,self.b08,self.b07,self.b06,
                       self.b00,self.b01,self.b04,self.b05)
        self.assertEqual(len(terrain),54)
        self.assertEqual(self.c["expected_qa_clone_map_count"],702)
        self.assertFalse(self.c["runtime_save_isolation_verified"])
        self.assertFalse(self.c["r07_complete"])

    def test_02_cli_metadata_ready_without_stage(self):
        p=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/build_sinnoh_b09_native_qa.py")],
            capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("B09_READY_AWAITING_LOCAL_B07_B08_EVIDENCE",p.stdout)

    def test_03_missing_b08_overlay_blocks(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        target=b08.qa_root(project)/f"qa-{dry['plan_sha256'][:16]}"
        import shutil
        shutil.rmtree(target)
        with self.assertRaisesRegex(ValueError,"SINNOH_B09_BLOCKED"):
            self.check_real_synthetic_overlay(project,dry,infos,tiles,rows)

    def test_04_b08_overlay_and_b07_stage_must_match(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        restored,_=self.check_real_synthetic_overlay(project,dry,infos,tiles,rows)
        self.assertEqual(set(restored),set(files))

    def test_05_altered_b08_overlay_binary_blocks(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        path=b08.qa_root(project)/f"qa-{dry['plan_sha256'][:16]}"/"Data/Map442.rxdata"
        path.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError,"SINNOH_B09_BLOCKED"):
            self.check_real_synthetic_overlay(project,dry,infos,tiles,rows)

    def test_06_altered_b08_manifest_blocks(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        path=b08.qa_root(project)/f"qa-{dry['plan_sha256'][:16]}"/"qa-overlay-manifest.json"
        m=json.loads(path.read_text("utf8"))
        m["rights_verified"]=True
        path.write_text(json.dumps(m),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"SINNOH_B09_BLOCKED"):
            self.check_real_synthetic_overlay(project,dry,infos,tiles,rows)

    def test_07_game_save_exclusion_and_native_scan(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        native,summary=b09.scan_native_game(project,game)
        paths={r["path"] for r in native}
        self.assertIn("Game.exe",paths)
        self.assertIn("Data/Map001.rxdata",paths)
        self.assertNotIn("Save01.rxdata",paths)
        self.assertNotIn("Saves/Save02.rxdata",paths)
        self.assertEqual(summary["skipped_private_or_unrecognized_files"],1)

    def test_08_dry_run_no_write_and_sha_deterministic(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        native,_=b09.scan_native_game(project,game)
        a=b09.plan_clone(native,files,dry["plan_sha256"])
        b=b09.plan_clone(native,files,dry["plan_sha256"])
        self.assertEqual(a["plan_sha256"],b["plan_sha256"])
        self.assertFalse((project/".blue-work/sinnoh-b09-native-qa").exists())
        self.assertEqual(a["overlay_file_count"],len(files))

    def test_09_real_clone_only_inside_private_and_original_untouched(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        native,_=b09.scan_native_game(project,game)
        plan=b09.plan_clone(native,files,dry["plan_sha256"])
        before={p.relative_to(game).as_posix():b09.file_sha(p)
                for p in game.rglob("*") if p.is_file()}
        result=b09.clone_private(project,game,files,plan,plan["plan_sha256"])
        cloned=project/result["relative_path"]
        self.assertEqual((cloned/"Data/Map442.rxdata").read_bytes(),
                         files["Data/Map442.rxdata"])
        self.assertEqual((cloned/"Data/MapInfos.rxdata").read_bytes(),
                         files["Data/MapInfos.rxdata"])
        self.assertTrue((cloned/"Game.exe").is_file())
        self.assertFalse((cloned/"Save01.rxdata").exists())
        self.assertFalse((cloned/"Saves").exists())
        self.assertFalse(result["safe_to_launch"])
        self.assertEqual({p.relative_to(game).as_posix():b09.file_sha(p)
                for p in game.rglob("*") if p.is_file()},before)

    def test_10_clone_requires_matching_plan_sha(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        native,_=b09.scan_native_game(project,game)
        plan=b09.plan_clone(native,files,dry["plan_sha256"])
        with self.assertRaisesRegex(ValueError,"SINNOH_B09_BLOCKED"):
            b09.clone_private(project,game,files,plan,"0"*64)
        self.assertFalse((project/".blue-work/sinnoh-b09-native-qa").exists())

    def test_11_changed_game_exe_blocks_copy(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        native,_=b09.scan_native_game(project,game)
        plan=b09.plan_clone(native,files,dry["plan_sha256"])
        (game/"Game.exe").write_bytes(b"MZ\x00changed since preview")
        with self.assertRaisesRegex(ValueError,"SINNOH_B09_BLOCKED"):
            b09.clone_private(project,game,files,plan,plan["plan_sha256"])
        base=project/".blue-work/sinnoh-b09-native-qa"
        self.assertFalse(any(base.iterdir()) if base.exists() else False)

    def test_12_overlay_map_id_collision_blocks(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        (game/"Data/Map442.rxdata").write_bytes(b"collision")
        native,_=b09.scan_native_game(project,game)
        with self.assertRaisesRegex(ValueError,"SINNOH_B09_BLOCKED"):
            b09.plan_clone(native,files,dry["plan_sha256"])

    def test_13_private_clone_rollback_success(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        native,_=b09.scan_native_game(project,game)
        plan=b09.plan_clone(native,files,dry["plan_sha256"])
        x=b09.clone_private(project,game,files,plan,plan["plan_sha256"])
        result=b09.rollback_clone(project,plan["plan_sha256"])
        self.assertEqual(result["status"],"PRIVATE_CLONE_REMOVED_ONLY")
        self.assertFalse((project/x["relative_path"]).exists())
        self.assertTrue((game/"Game.exe").exists())

    def test_14_clone_rollback_denied_if_save_added(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        native,_=b09.scan_native_game(project,game)
        plan=b09.plan_clone(native,files,dry["plan_sha256"])
        x=b09.clone_private(project,game,files,plan,plan["plan_sha256"])
        (project/x["relative_path"]/"Save01.rxdata").write_bytes(b"new save")
        with self.assertRaisesRegex(ValueError,"SINNOH_B09_BLOCKED"):
            b09.rollback_clone(project,plan["plan_sha256"])
        self.assertTrue((project/x["relative_path"]/"Save01.rxdata").exists())

    def test_15_clone_rollback_denied_if_overlay_modified(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        native,_=b09.scan_native_game(project,game)
        plan=b09.plan_clone(native,files,dry["plan_sha256"])
        x=b09.clone_private(project,game,files,plan,plan["plan_sha256"])
        (project/x["relative_path"]/"Data/Map442.rxdata").write_bytes(b"corrupted")
        with self.assertRaisesRegex(ValueError,"SINNOH_B09_BLOCKED"):
            b09.rollback_clone(project,plan["plan_sha256"])

    def test_16_clone_duplicate_is_not_overwritten(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        native,_=b09.scan_native_game(project,game)
        plan=b09.plan_clone(native,files,dry["plan_sha256"])
        b09.clone_private(project,game,files,plan,plan["plan_sha256"])
        with self.assertRaisesRegex(ValueError,"SINNOH_B09_BLOCKED"):
            b09.clone_private(project,game,files,plan,plan["plan_sha256"])

    def test_17_game_source_cannot_be_project_or_child(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        with self.assertRaisesRegex(ValueError,"SINNOH_B09_BLOCKED"):
            b09.secure_game_dir(project,project)

    def test_18_no_false_R07_or_save_isolation_approval(self):
        for field in ("runtime_save_isolation_verified",
                      "future_reservations_verified","third_party_asset_rights_verified",
                      "game_exe_tested","r07_complete","can_mark_native_playable"):
            with self.subTest(field=field):
                c=copy.deepcopy(self.c);c[field]=True
                with self.assertRaisesRegex(ValueError,"SINNOH_B09_BLOCKED"):
                    b09.check_contract(c,self.b08,self.b07,self.b06,self.b00,
                                       self.b01,self.b04,self.b05)

    def test_19_clone_progress_goes_only_to_stderr(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        native,_=b09.scan_native_game(project,game)
        plan=b09.plan_clone(native,files,dry["plan_sha256"])
        stdout=io.StringIO()
        stderr=io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            result=b09.clone_private(project,game,files,plan,plan["plan_sha256"])
        self.assertEqual(stdout.getvalue(),"")
        self.assertIn("[B09 COPIA]",stderr.getvalue())
        self.assertIn("100% em bytes",stderr.getvalue())
        self.assertIn("Game.exe NAO iniciado",stderr.getvalue())
        self.assertFalse(result["safe_to_launch"])

    def test_20_same_size_source_mutation_blocks_stream_copy(self):
        project,game,files,infos,tiles,dry,rows,report=self.fixture()
        native,_=b09.scan_native_game(project,game)
        plan=b09.plan_clone(native,files,dry["plan_sha256"])
        source=game/"Game.exe"
        raw=source.read_bytes()
        source.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
        self.assertEqual(source.stat().st_size,len(raw))
        with self.assertRaisesRegex(ValueError,"jogo mudou entre dry-run"):
            b09.clone_private(project,game,files,plan,plan["plan_sha256"])
        base=project/".blue-work/sinnoh-b09-native-qa"
        self.assertFalse(any(base.iterdir()) if base.exists() else False)

if __name__=="__main__":unittest.main()
