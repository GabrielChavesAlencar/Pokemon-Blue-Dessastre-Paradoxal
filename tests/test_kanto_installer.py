"""Isolated transaction tests: no Decades download, native map files or saves."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT / "scripts/regions"))
try:
    import install_kanto as installer
finally:
    sys.path.remove(str(PROJECT / "scripts/regions"))


class KantoInstallerTest(unittest.TestCase):
    def with_game(self, folder):
        root = Path(folder)
        game = root / "game"
        src = root / ".blue-work/payload"
        for name in ["Data", "PBS", "saves"]:
            (game / name).mkdir(parents=True, exist_ok=True)
        src.mkdir(parents=True)
        (game / "Data/MapInfos.rxdata").write_bytes(b"original maps")
        (game / "Data/Tilesets.rxdata").write_bytes(b"original tiles")
        (game / "saves/old.rxdata").write_bytes(b"precious save")
        (game / "Game.exe").write_bytes(b"precious exe")
        (game / "Game.ini").write_bytes(b"precious ini")
        (game / "mkxp.json").write_bytes(b"precious config")
        (src / "new-infos").write_bytes(b"expanded maps")
        (src / "map-300").write_bytes(b"kanto pallet")
        files = {Path("Data/MapInfos.rxdata"): src / "new-infos",
                 Path("Data/Map300.rxdata"): src / "map-300"}
        return root, game, src, files

    def test_all_regional_trainer_portraits_are_mandatory_and_not_general_graphics(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            graphics = root / "Graphics/Trainers"
            graphics.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError, "Missing or invalid"):
                installer.trainer_portraits(root)
            for name in installer.PORTRAITS:
                (graphics / name).write_bytes(b"\x89PNG\r\n\x1a\n" + name.encode())
            portraits = installer.trainer_portraits(root)
            self.assertEqual(len(portraits), len(installer.PORTRAITS))
            self.assertEqual(set(p.name for p in portraits), set(installer.PORTRAITS))

    def test_existing_kanto_install_can_repair_missing_portraits_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root, game, src, files = self.with_game(folder)
            (game / installer.MARKER).write_text("installed")
            install_manifest = game / "Data/blue-kanto-install.json"
            install_manifest.write_text('{"schema":1,"installed_sha256":{}}')
            graphics = game / "Graphics/Trainers"
            graphics.mkdir(parents=True)
            for kind, base in installer.TYPES.items():
                (graphics / f"{base}.png").write_bytes(b"\x89PNG\r\n\x1a\n" + base.encode())
            with mock.patch.object(installer, "ROOT", root):
                preview = installer.repair_portraits(game, False)
                self.assertEqual(len(preview["missing_portraits"]), len(installer.PORTRAITS))
                self.assertEqual(installer.repair_portraits(game, True)["status"], "repaired")
                self.assertEqual(installer.repair_portraits(game, True)["status"], "already_correct")
            self.assertEqual((game / "Data/MapInfos.rxdata").read_bytes(), b"original maps")
            self.assertEqual((game / "Data/Tilesets.rxdata").read_bytes(), b"original tiles")
            self.assertEqual((game / "saves/old.rxdata").read_bytes(), b"precious save")
            self.assertEqual(len(list(graphics.glob("BLUE_KANTO_*.png"))), len(installer.PORTRAITS))
            data = __import__("json").loads(install_manifest.read_text())
            self.assertEqual(len(data["installed_sha256"]), len(installer.PORTRAITS))

    def test_portrait_repair_does_not_overwrite_user_edited_image(self):
        with tempfile.TemporaryDirectory() as folder:
            root, game, src, files = self.with_game(folder)
            (game / installer.MARKER).write_text("installed")
            (game / "Data/blue-kanto-install.json").write_text('{"schema":1}')
            graphics = game / "Graphics/Trainers"
            graphics.mkdir(parents=True)
            for kind, base in installer.TYPES.items():
                (graphics / f"{base}.png").write_bytes(b"\x89PNG\r\n\x1a\n" + base.encode())
            (graphics / "BLUE_KANTO_RIVAL.png").write_bytes(b"\x89PNG\r\n\x1a\ncustom")
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                installer.repair_portraits(game, True)
            self.assertFalse((graphics / "BLUE_KANTO_CAMPER.png").exists())

    def test_dry_run_never_writes_into_game(self):
        with tempfile.TemporaryDirectory() as folder:
            root, game, src, files = self.with_game(folder)
            with mock.patch.object(installer, "manifest", return_value=(files, {5: 300}, {})):
                result = installer.apply_install(game, src, False)
            self.assertEqual(result["status"], "dry_run")
            self.assertEqual((game / "Data/MapInfos.rxdata").read_bytes(), b"original maps")
            self.assertFalse((game / "Data/Map300.rxdata").exists())
            self.assertFalse((game / installer.MARKER).exists())

    def test_commit_preserves_native_files_and_player_save(self):
        with tempfile.TemporaryDirectory() as folder:
            root, game, src, files = self.with_game(folder)
            with mock.patch.object(installer, "ROOT", root), mock.patch.object(
                    installer, "manifest", return_value=(files, {5: 300}, {})):
                result = installer.apply_install(game, src, True)
            self.assertEqual(result["status"], "installed")
            self.assertEqual((game / "Data/MapInfos.rxdata").read_bytes(), b"expanded maps")
            self.assertEqual((game / "Data/Map300.rxdata").read_bytes(), b"kanto pallet")
            self.assertEqual((game / "Data/blue-kanto-start.txt").read_text().strip(),
                             "BLUE_KANTO_START_V1,KANTO,300,28,14")
            for filename, previous in (("Game.exe",b"precious exe"),
                                       ("Game.ini",b"precious ini"),
                                       ("mkxp.json",b"precious config"),
                                       ("saves/old.rxdata",b"precious save")):
                self.assertEqual((game / filename).read_bytes(), previous)
            self.assertTrue((Path(result["backup"]) / "Data/MapInfos.rxdata").is_file())

    def test_failure_rolls_back_partial_map_and_keeps_saves(self):
        with tempfile.TemporaryDirectory() as folder:
            root, game, src, files = self.with_game(folder)
            real_atomic = installer.atomic

            def fail_on_map(path, raw):
                if path == game / "Data/Map300.rxdata":
                    raise OSError("simulated full disk during map installation")
                real_atomic(path, raw)

            with mock.patch.object(installer, "ROOT", root), mock.patch.object(
                    installer, "manifest", return_value=(files, {5: 300}, {})), mock.patch.object(
                    installer, "atomic", side_effect=fail_on_map):
                with self.assertRaisesRegex(OSError, "simulated full disk"):
                    installer.apply_install(game, src, True)
            self.assertEqual((game / "Data/MapInfos.rxdata").read_bytes(), b"original maps")
            self.assertFalse((game / "Data/Map300.rxdata").exists())
            self.assertFalse((game / installer.MARKER).exists())
            self.assertEqual((game / "saves/old.rxdata").read_bytes(), b"precious save")


if __name__ == "__main__":
    unittest.main()
