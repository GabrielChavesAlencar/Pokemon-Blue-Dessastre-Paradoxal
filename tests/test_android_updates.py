"""Offline tests of channel isolation, delta generation and safe installation."""
import json
import tempfile
import unittest
from pathlib import Path
import zipfile

from scripts.android.build_manifest import installed_manifest
from scripts.android.publish_updates import publish
from scripts.android.update_client import apply_patch, read_installed, safe_path, sha256_bytes


class AndroidUpdatesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.a = "a" * 40
        self.b = "b" * 40

    def build_zip(self, revision, content):
        folder = self.root / revision
        folder.mkdir()
        file = folder / "Data/Map001.rxdata"
        file.parent.mkdir()
        file.write_bytes(content)
        game = self.root / (revision + ".zip")
        files = {"Data/Map001.rxdata": file}
        marker = installed_manifest("kanto", revision, files)
        with zipfile.ZipFile(game, "w") as z:
            z.writestr("Pokemon-Blue-Kanto-Android/Data/Map001.rxdata", content)
            z.writestr("Pokemon-Blue-Kanto-Android/Data/blue-update.json", marker)
            z.writestr("Pokemon-Blue-Kanto-Android/ATUALIZAR-ANDROID.py", "# helper\n")
        return game, json.loads(marker)

    def test_rejects_saves_and_traversal(self):
        for name in ("../Data/test.rxdata", "Data/../map", "Data/Game.rxdata",
                     "Data/File A.rxdata", "Data/Auto 1.rxdata", "Data/save1.rxdata",
                     "Saves/File A.rxdata", "mkxp.json", "Data/blue-update.json",
                     "Graphics/../../saves", r"Data\Map001.rxdata"):
            self.assertFalse(safe_path(name), name)
        self.assertTrue(safe_path("Data/Map001.rxdata"))

    def test_incremental_update_and_backup(self):
        old, old_marker = self.build_zip(self.a, b"OLD")
        new, new_marker = self.build_zip(self.b, b"NEW")
        old_metadata = self.root / "old.json"
        old_metadata.write_text(json.dumps(old_marker))
        new_zip = self.root / "Blue-Android-Kanto-Piloto.zip"
        new.rename(new_zip)
        released = publish(new_zip, "kanto", old_metadata)
        self.assertIsNotNone(released["patch"])
        public = json.loads((self.root / "Blue-Android-Kanto-Piloto.update.json").read_text())
        patch = self.root / public["patch"]["asset"]
        self.assertEqual(patch.name, "Blue-Android-Kanto-Piloto.patch.zip")
        game = self.root / "installed"
        (game / "Data").mkdir(parents=True)
        (game / "Data/Map001.rxdata").write_bytes(b"OLD")
        (game / "Data/blue-update.json").write_text(json.dumps(old_marker))
        (game / "Data/File A.rxdata").write_bytes(b"SAVE")
        result = apply_patch(game, read_installed(game), public, patch)
        self.assertEqual(result[:2], (1, 0))
        self.assertEqual((game / "Data/Map001.rxdata").read_bytes(), b"NEW")
        self.assertEqual((game / "Data/File A.rxdata").read_bytes(), b"SAVE")
        self.assertEqual(read_installed(game)["revision"], self.b)
        self.assertEqual((result[2] / "Data/Map001.rxdata").read_bytes(), b"OLD")

    def test_modified_game_refuses_delta_without_touching_files(self):
        old, old_marker = self.build_zip(self.a, b"OLD")
        new, _ = self.build_zip(self.b, b"NEW")
        old_metadata = self.root / "old.json"
        old_metadata.write_text(json.dumps(old_marker))
        new_zip = self.root / "Blue-Android-Kanto-Piloto.zip"
        new.rename(new_zip)
        publish(new_zip, "kanto", old_metadata)
        manifest = json.loads((self.root / "Blue-Android-Kanto-Piloto.update.json").read_text())
        game = self.root / "modified"
        (game / "Data").mkdir(parents=True)
        (game / "Data/Map001.rxdata").write_bytes(b"USER EDIT")
        (game / "Data/blue-update.json").write_text(json.dumps(old_marker))
        with self.assertRaisesRegex(ValueError, "modified"):
            apply_patch(game, read_installed(game), manifest,
                        self.root / "Blue-Android-Kanto-Piloto.patch.zip")
        self.assertEqual((game / "Data/Map001.rxdata").read_bytes(), b"USER EDIT")
        self.assertEqual(read_installed(game)["revision"], self.a)

    def test_no_previous_manifest_means_full_install_baseline_only(self):
        new, _ = self.build_zip(self.b, b"NEW")
        new_zip = self.root / "Blue-Android-Kanto-Piloto.zip"
        new.rename(new_zip)
        result = publish(new_zip, "kanto")
        self.assertIsNone(result["patch"])
        self.assertFalse((self.root / "Blue-Android-Kanto-Piloto.patch.zip").exists())


if __name__ == "__main__":
    unittest.main()
