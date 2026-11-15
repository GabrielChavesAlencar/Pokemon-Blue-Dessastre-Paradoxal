"""Offline tests of channel isolation, delta generation and safe installation."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile

from scripts.android.build_manifest import installed_manifest
from scripts.android.publish_updates import publish
from scripts.android.update_client import (apply_patch, apply_full_archive,
                                           main, read_installed, safe_path,
                                           sha256_bytes)


class AndroidUpdatesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.a = "a" * 40
        self.b = "b" * 40

    def build_zip(self, revision, content, kanto_data=None):
        folder = self.root / revision
        folder.mkdir()
        file = folder / "Data/Map001.rxdata"
        file.parent.mkdir()
        file.write_bytes(content)
        game = self.root / (revision + ".zip")
        files = {"Data/Map001.rxdata": file}
        if kanto_data is not None:
            files["Kanto pilot.json"] = kanto_data
        marker = installed_manifest("kanto", revision, files)
        with zipfile.ZipFile(game, "w") as z:
            z.writestr("Pokemon-Blue-Kanto-Android/Data/Map001.rxdata", content)
            if kanto_data is not None:
                z.writestr("Pokemon-Blue-Kanto-Android/Kanto pilot.json", kanto_data)
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
        self.assertTrue(safe_path("Kanto pilot.json"))
        self.assertTrue(safe_path("LEIA-ME-ANDROID.txt"))
        self.assertTrue(safe_path("LEIA-ME-ANDROID-KANTO.txt"))

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

    def test_kanto_source_metadata_is_updated_with_maps(self):
        old, old_marker = self.build_zip(self.a, b"OLD", b'{"maps":{"1":1}}')
        new, _ = self.build_zip(self.b, b"NEW", b'{"maps":{"1":1,"2":2}}')
        previous = self.root / "old.json"
        previous.write_text(json.dumps(old_marker))
        target = self.root / "Blue-Android-Kanto-Piloto.zip"
        new.rename(target)
        result = publish(target, "kanto", previous)
        self.assertIsNotNone(result["patch"])
        patch = self.root / "Blue-Android-Kanto-Piloto.patch.zip"
        with zipfile.ZipFile(patch) as archive:
            self.assertEqual(archive.read("files/Kanto pilot.json"), b'{"maps":{"1":1,"2":2}}')

    def test_incompatible_save_profile_requires_full_zip(self):
        old, old_marker = self.build_zip(self.a, b"OLD")
        old_marker["immutable"] = {"mkxp.json": {"sha256": "0" * 64, "size": 8}}
        new, _ = self.build_zip(self.b, b"NEW")
        previous = self.root / "old.json"
        previous.write_text(json.dumps(old_marker))
        target = self.root / "Blue-Android-Kanto-Piloto.zip"
        new.rename(target)
        result = publish(target, "kanto", previous)
        self.assertIsNone(result["patch"])
        self.assertFalse((self.root / "Blue-Android-Kanto-Piloto.patch.zip").exists())

    def test_corrupt_patch_manifest_is_refused(self):
        old, old_marker = self.build_zip(self.a, b"OLD")
        new, _ = self.build_zip(self.b, b"NEW")
        previous = self.root / "old.json"
        previous.write_text(json.dumps(old_marker))
        target = self.root / "Blue-Android-Kanto-Piloto.zip"
        new.rename(target)
        publish(target, "kanto", previous)
        manifest = json.loads((self.root / "Blue-Android-Kanto-Piloto.update.json").read_text())
        patch = self.root / manifest["patch"]["asset"]
        # A patch whose file table omits a changed file must not advance the marker.
        invalid = self.root / "invalid.zip"
        with zipfile.ZipFile(invalid, "w") as archive:
            archive.writestr("patch.json", json.dumps({
                "schema": 1, "channel": "kanto", "from_revision": self.a,
                "to_revision": self.b, "changed": {}, "removed": []}))
        game = self.root / "installed"
        (game / "Data").mkdir(parents=True)
        (game / "Data/Map001.rxdata").write_bytes(b"OLD")
        (game / "Data/blue-update.json").write_text(json.dumps(old_marker))
        with self.assertRaisesRegex(ValueError, "complete delta"):
            apply_patch(game, read_installed(game), manifest, invalid)
        self.assertEqual(read_installed(game)["revision"], self.a)

    def test_no_previous_manifest_means_full_install_baseline_only(self):
        new, _ = self.build_zip(self.b, b"NEW")
        new_zip = self.root / "Blue-Android-Kanto-Piloto.zip"
        new.rename(new_zip)
        result = publish(new_zip, "kanto")
        self.assertIsNone(result["patch"])
        self.assertFalse((self.root / "Blue-Android-Kanto-Piloto.patch.zip").exists())


    def full_zip_fixture(self, revision, map_content, exe_content):
        """A minimal real-channel ZIP with immutable root and update manifest."""
        prefix = "Pokemon-Blue-Kanto-Android/"
        files = {"Data/Map001.rxdata": map_content,
                 "Game.exe": exe_content,
                 "ATUALIZAR-ANDROID.py": b"# updater\n"}
        manifest = json.loads(installed_manifest("kanto", revision, files))
        target = self.root / "Blue-Android-Kanto-Piloto.zip"
        with zipfile.ZipFile(target, "w") as archive:
            for name, content in files.items():
                archive.writestr(prefix + name, content)
            archive.writestr(prefix + "Data/blue-update.json",
                             json.dumps(manifest))
        return target, manifest

    def installed_full_fixture(self):
        game = self.root / "installed"
        (game / "Data").mkdir(parents=True)
        (game / "Data/Map001.rxdata").write_bytes(b"OLD MAP")
        (game / "Game.exe").write_bytes(b"OLD EXE")
        (game / "ATUALIZAR-ANDROID.py").write_bytes(b"# updater\n")
        previous = json.loads(installed_manifest("kanto", self.a, {
            "Data/Map001.rxdata": b"OLD MAP",
            "Game.exe": b"OLD EXE",
            "ATUALIZAR-ANDROID.py": b"# updater\n",
        }))
        (game / "Data/blue-update.json").write_text(json.dumps(previous))
        (game / "Data/File A.rxdata").write_bytes(b"IMPORTANT SAVE")
        (game / "Game.rxdata.bak").write_bytes(b"OTHER SAVE BACKUP")
        (game / "personal-note.txt").write_text("old user data")
        return game, previous

    def test_full_zip_fallback_keeps_saves_and_original_game(self):
        game, old = self.installed_full_fixture()
        archive, _ = self.full_zip_fixture(self.b, b"NEW MAP", b"NEW EXE")
        public = publish(archive, "kanto")
        self.assertIsNone(public["patch"])
        manifest = json.loads((self.root / "Blue-Android-Kanto-Piloto.update.json").read_text())
        backup, saved = apply_full_archive(game, old, manifest, archive)
        self.assertEqual(saved, 2)
        self.assertEqual((game / "Data/Map001.rxdata").read_bytes(), b"NEW MAP")
        self.assertEqual((game / "Game.exe").read_bytes(), b"NEW EXE")
        self.assertEqual((game / "Data/File A.rxdata").read_bytes(), b"IMPORTANT SAVE")
        self.assertEqual((game / "Game.rxdata.bak").read_bytes(), b"OTHER SAVE BACKUP")
        self.assertEqual(read_installed(game)["revision"], self.b)
        self.assertEqual((backup / "Data/Map001.rxdata").read_bytes(), b"OLD MAP")
        self.assertEqual((backup / "personal-note.txt").read_text(), "old user data")

    def test_rejects_corrupted_full_zip_without_affecting_installed_game(self):
        game, old = self.installed_full_fixture()
        archive, _ = self.full_zip_fixture(self.b, b"NEW MAP", b"NEW EXE")
        publish(archive, "kanto")
        manifest = json.loads((self.root / "Blue-Android-Kanto-Piloto.update.json").read_text())
        with zipfile.ZipFile(archive, "a") as destination:
            destination.writestr("Pokemon-Blue-Kanto-Android/../../unsafe.txt", "BAD")
        with self.assertRaisesRegex(ValueError, "Unsafe|Invalid"):
            apply_full_archive(game, old, manifest, archive)
        self.assertEqual(read_installed(game)["revision"], self.a)
        self.assertEqual((game / "Data/File A.rxdata").read_bytes(), b"IMPORTANT SAVE")

    def test_termux_update_automatically_uses_full_zip_when_no_patch(self):
        game, _ = self.installed_full_fixture()
        archive, _ = self.full_zip_fixture(self.b, b"NEW MAP", b"NEW EXE")
        publish(archive, "kanto")
        manifest = json.loads((self.root / "Blue-Android-Kanto-Piloto.update.json").read_text())
        asset_name = "Blue-Android-Kanto-Piloto.zip"
        url = ("https://github.com/GabrielChavesAlencar/"
               "Pokemon-Blue-Dessastre-Paradoxal/releases/download/"
               "kanto-android-test/" + asset_name)
        release = {"assets": [{"name": asset_name, "state": "uploaded",
                               "browser_download_url": url}]}
        def fake_download(_url, destination, sha, size, **kwargs):
            self.assertEqual(size, archive.stat().st_size)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(archive, destination)
        with (patch("scripts.android.update_client.remote_update",
                    return_value=(release, manifest)),
              patch("scripts.android.update_client.download",
                    side_effect=fake_download)):
            self.assertEqual(main(["--game-dir", str(game), "--update"]), 0)
        self.assertEqual((game / "Data/Map001.rxdata").read_bytes(), b"NEW MAP")
        self.assertEqual((game / "Data/File A.rxdata").read_bytes(), b"IMPORTANT SAVE")

if __name__ == "__main__":
    unittest.main()
