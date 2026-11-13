"""Proof that Sinnoh staging transactions cannot replace native game files."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from sinnoh_staging_transaction import preview, stage, rollback


class SinnohStagingTransactionTests(unittest.TestCase):
    def files(self):
        # Only owned synthetic test fixtures, never source-game bytes.
        return {
            "Data/Map001.rxdata": b"\x04\x08synthetic sample",
            "Graphics/Tilesets/Sample.png": b"\x89PNG\r\n\x1a\nsynthetic sample",
        }

    def test_dry_run_never_creates_workspace_or_game(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan = preview(root, "first", self.files())
            self.assertEqual(plan["mode"], "DRY_RUN_NO_WRITES")
            self.assertFalse(plan["writes_to_main_game"])
            self.assertFalse(plan["may_install_into_game"])
            self.assertFalse((root / ".blue-work").exists())
            self.assertFalse((root / "game").exists())
            self.assertEqual(len(plan["files"]), 2)

    def test_apply_and_rollback_are_confined_to_a_new_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            game = root / "game" / "Data"
            game.mkdir(parents=True)
            game_map = game / "Map001.rxdata"
            game_map.write_bytes(b"existing game map, do not overwrite")
            before = hashlib.sha256(game_map.read_bytes()).hexdigest()
            files = self.files()
            dry = preview(root, "first", files)
            result = stage(root, "first", files, dry["plan_sha256"])
            stage_dir = root / result["stage_relative_path"]
            self.assertEqual(result["mode"], "LOCAL_STAGE_ONLY")
            self.assertTrue(stage_dir.is_dir())
            self.assertEqual((stage_dir / "Data/Map001.rxdata").read_bytes(),
                             files["Data/Map001.rxdata"])
            self.assertTrue((stage_dir / "stage-manifest.json").exists())
            self.assertEqual(hashlib.sha256(game_map.read_bytes()).hexdigest(), before)
            reverted = rollback(root, "first", dry["plan_sha256"])
            self.assertTrue(reverted["removed_only_stage"])
            self.assertFalse(stage_dir.exists())
            self.assertEqual(hashlib.sha256(game_map.read_bytes()).hexdigest(), before)

    def test_requires_verified_dry_run_hash_and_unique_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dry = preview(root, "pilot", self.files())
            with self.assertRaisesRegex(ValueError, "dry-run"):
                stage(root, "pilot", self.files(), "0" * 64)
            stage(root, "pilot", self.files(), dry["plan_sha256"])
            with self.assertRaises(FileExistsError):
                stage(root, "pilot", self.files(), dry["plan_sha256"])
            self.assertEqual(rollback(root, "pilot", dry["plan_sha256"])["mode"],
                             "LOCAL_ROLLBACK")

    def test_banned_filenames_never_touch_the_game(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ("../game/Data/Map001.rxdata", "Data/Scripts.rxdata",
                         "Data/System.rxdata", "/game/Data/Map001.rxdata",
                         "Plugins/Sinnoh.rb"):
                with self.subTest(name=name):
                    with self.assertRaisesRegex(ValueError, "inválido"):
                        preview(root, "safe", {name: b"no"})
            self.assertFalse((root / ".blue-work").exists())

    def test_modified_stage_cannot_be_rolled_back_blindly(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            dry = preview(root, "pilot", self.files())
            result = stage(root, "pilot", self.files(), dry["plan_sha256"])
            stage_dir = root / result["stage_relative_path"]
            (stage_dir / "Data/Map001.rxdata").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash divergente"):
                rollback(root, "pilot", dry["plan_sha256"])
            self.assertTrue(stage_dir.is_dir())
            (stage_dir / "Data/Map001.rxdata").write_bytes(self.files()["Data/Map001.rxdata"])
            (stage_dir / "extra.bin").write_bytes(b"not part of the plan")
            with self.assertRaisesRegex(ValueError, "conteúdo extra"):
                rollback(root, "pilot", dry["plan_sha256"])
            self.assertTrue(stage_dir.is_dir())

    def test_symlink_workdir_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            root.joinpath("outside").mkdir()
            try:
                root.joinpath(".blue-work").symlink_to(root / "outside", target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlink creation unavailable")
            with self.assertRaisesRegex(ValueError, "symlinks"):
                preview(root, "safe", self.files())


if __name__ == "__main__":
    unittest.main()
