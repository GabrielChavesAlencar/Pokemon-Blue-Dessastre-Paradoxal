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
                                           compatible_patch,
                                           main, read_installed, safe_path,
                                           sha256_bytes, release_for,
                                           verify_forward_revision)


class AndroidUpdatesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.a = "a" * 40
        self.b = "b" * 40

    def build_zip(self, revision, content, kanto_data=None, updater=b"# helper\\n"):
        folder = self.root / revision
        folder.mkdir()
        file = folder / "Data/Map001.rxdata"
        file.parent.mkdir()
        file.write_bytes(content)
        game = self.root / (revision + ".zip")
        files = {"Data/Map001.rxdata": file, "ATUALIZAR-ANDROID.py": updater}
        if kanto_data is not None:
            files["Kanto pilot.json"] = kanto_data
        marker = installed_manifest("kanto", revision, files)
        with zipfile.ZipFile(game, "w") as z:
            z.writestr("Pokemon-Blue-Kanto-Android/Data/Map001.rxdata", content)
            if kanto_data is not None:
                z.writestr("Pokemon-Blue-Kanto-Android/Kanto pilot.json", kanto_data)
            z.writestr("Pokemon-Blue-Kanto-Android/Data/blue-update.json", marker)
            z.writestr("Pokemon-Blue-Kanto-Android/ATUALIZAR-ANDROID.py", updater)
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

    def _launcher_patch_fixture(self, local_updater):
        _, old = self.build_zip(self.a, b"OLD MAP", updater=b"# packaged old updater\n")
        new, _ = self.build_zip(self.b, b"NEW MAP", updater=b"# patched new updater\n")
        previous = self.root / "old.json"
        previous.write_text(json.dumps(old))
        new_path = self.root / "Blue-Android-Kanto-Piloto.zip"
        new.rename(new_path)
        published = publish(new_path, "kanto", previous)
        assert published["patch"]
        manifest = json.loads((self.root / "Blue-Android-Kanto-Piloto.update.json").read_text())
        game = self.root / "installed"
        (game / "Data").mkdir(parents=True)
        (game / "Data/Map001.rxdata").write_bytes(b"OLD MAP")
        (game / "Data/blue-update.json").write_text(json.dumps(old))
        (game / "Data/File A.rxdata").write_bytes(b"SAVE CONTENT")
        (game / "ATUALIZAR-ANDROID.py").write_bytes(local_updater)
        return game, manifest, self.root / published["patch"]["asset"]

    def test_known_1911_byte_android_launcher_can_update_without_backup(self):
        # This is exactly the user-shared launcher placed in their phone.
        launcher = (Path(__file__).parent / "fixtures" /
                    "android_updater_launcher_20261117.py").read_bytes()
        self.assertEqual(len(launcher), 1911)
        from scripts.android.update_client import KNOWN_ANDROID_LAUNCHERS
        import hashlib
        self.assertIn(hashlib.sha256(launcher).hexdigest(), KNOWN_ANDROID_LAUNCHERS)
        game, manifest, patch_file = self._launcher_patch_fixture(launcher)
        count, removed, backup = apply_patch(game, read_installed(game), manifest, patch_file)
        self.assertEqual((count, removed, backup), (2, 0, None))
        self.assertEqual((game / "ATUALIZAR-ANDROID.py").read_bytes(), b"# patched new updater\n")
        self.assertEqual((game / "Data/Map001.rxdata").read_bytes(), b"NEW MAP")
        self.assertEqual((game / "Data/File A.rxdata").read_bytes(), b"SAVE CONTENT")
        self.assertEqual(read_installed(game)["revision"], self.b)
        self.assertFalse((game / ".blue-android-update-backups").exists())

    def test_unrecognized_modified_updater_still_refused_and_game_untouched(self):
        game, manifest, patch_file = self._launcher_patch_fixture(b"# arbitrary edited script\n")
        with self.assertRaisesRegex(ValueError, "ATUALIZAR-ANDROID.py"):
            apply_patch(game, read_installed(game), manifest, patch_file)
        self.assertEqual((game / "Data/Map001.rxdata").read_bytes(), b"OLD MAP")
        self.assertEqual((game / "ATUALIZAR-ANDROID.py").read_bytes(), b"# arbitrary edited script\n")
        self.assertEqual((game / "Data/File A.rxdata").read_bytes(), b"SAVE CONTENT")
        self.assertEqual(read_installed(game)["revision"], self.a)

    def test_known_launcher_cannot_bypass_other_modified_file(self):
        launcher = (Path(__file__).parent / "fixtures" /
                    "android_updater_launcher_20261117.py").read_bytes()
        game, manifest, patch_file = self._launcher_patch_fixture(launcher)
        (game / "Data/Map001.rxdata").write_bytes(b"CUSTOM MAP")
        with self.assertRaisesRegex(ValueError, "Data/Map001.rxdata"):
            apply_patch(game, read_installed(game), manifest, patch_file)
        self.assertEqual((game / "ATUALIZAR-ANDROID.py").read_bytes(), launcher)
        self.assertEqual((game / "Data/Map001.rxdata").read_bytes(), b"CUSTOM MAP")
        self.assertEqual(read_installed(game)["revision"], self.a)

    def test_incremental_update_without_backup(self):
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
        self.assertIsNone(result[2])
        self.assertFalse((game / ".blue-android-update-backups").exists())
        self.assertFalse(any(self.root.glob("installed.blue-backup-*")))

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

    def test_manual_full_zip_changes_only_different_files(self):
        game, old = self.installed_full_fixture()
        archive, _ = self.full_zip_fixture(self.b, b"NEW MAP", b"NEW EXE")
        public = publish(archive, "kanto")
        self.assertIsNone(public["patch"])
        manifest = json.loads((self.root / "Blue-Android-Kanto-Piloto.update.json").read_text())
        backup, changed = apply_full_archive(game, old, manifest, archive)
        self.assertIsNone(backup)
        self.assertEqual(changed, 2)
        self.assertEqual((game / "Data/Map001.rxdata").read_bytes(), b"NEW MAP")
        self.assertEqual((game / "Game.exe").read_bytes(), b"NEW EXE")
        self.assertEqual((game / "Data/File A.rxdata").read_bytes(), b"IMPORTANT SAVE")
        self.assertEqual((game / "Game.rxdata.bak").read_bytes(), b"OTHER SAVE BACKUP")
        self.assertEqual(read_installed(game)["revision"], self.b)
        self.assertEqual((game / "personal-note.txt").read_text(), "old user data")
        self.assertFalse(any(self.root.glob("installed.blue-backup-*")))

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

    def test_no_automatic_full_zip_without_patch_explicit_only(self):
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
                    side_effect=fake_download) as downloader,
              patch("scripts.android.update_client.verify_forward_revision")
                    as ancestry):
            self.assertEqual(main(["--game-dir", str(game), "--update"]), 2)
            downloader.assert_not_called()
            self.assertEqual((game / "Data/Map001.rxdata").read_bytes(), b"OLD MAP")
            self.assertEqual(main(["--game-dir", str(game), "--full", "--update"]), 0)
            ancestry.assert_called_with(self.a, self.b)
        self.assertEqual((game / "Data/Map001.rxdata").read_bytes(), b"NEW MAP")
        self.assertEqual((game / "Data/File A.rxdata").read_bytes(), b"IMPORTANT SAVE")


    def test_migrate_legacy_immutable_updater_by_small_patch(self):
        _, previous = self.build_zip(self.a, b"OLD")
        new, _ = self.build_zip(self.b, b"NEW", updater=b"# new updater\\n")
        previous["immutable"]["ATUALIZAR-ANDROID.py"] = previous["files"].pop("ATUALIZAR-ANDROID.py")
        previous_file = self.root / "legacy.json"
        previous_file.write_text(json.dumps(previous))
        archive = self.root / "Blue-Android-Kanto-Piloto.zip"
        new.rename(archive)
        published = publish(archive, "kanto", previous_file)
        self.assertIsNotNone(published["patch"])
        manifest = json.loads((self.root / "Blue-Android-Kanto-Piloto.update.json").read_text())
        game = self.root / "legacy"
        (game / "Data").mkdir(parents=True)
        (game / "ATUALIZAR-ANDROID.py").write_bytes(b"# helper\\n")
        (game / "Data/Map001.rxdata").write_bytes(b"OLD")
        (game / "Data/blue-update.json").write_text(json.dumps(previous))
        update = self.root / published["patch"]["asset"]
        changed, removed, backup = apply_patch(game, read_installed(game), manifest, update)
        self.assertEqual((changed, removed, backup), (2, 0, None))
        self.assertEqual((game / "ATUALIZAR-ANDROID.py").read_bytes(), b"# new updater\\n")
        self.assertNotIn("ATUALIZAR-ANDROID.py", read_installed(game)["immutable"])
        self.assertIn("ATUALIZAR-ANDROID.py", read_installed(game)["files"])
        self.assertFalse((game / ".blue-android-update-backups").exists())

    def test_interrupted_patch_resume_does_not_rewrite_existing_new_file(self):
        old, old_marker = self.build_zip(self.a, b"OLD")
        new, _ = self.build_zip(self.b, b"NEW")
        previous = self.root / "previous.json"
        previous.write_text(json.dumps(old_marker))
        full = self.root / "Blue-Android-Kanto-Piloto.zip"
        new.rename(full)
        publish(full, "kanto", previous)
        manifest = json.loads((self.root / "Blue-Android-Kanto-Piloto.update.json").read_text())
        game = self.root / "partial"
        (game / "Data").mkdir(parents=True)
        (game / "Data/blue-update.json").write_text(json.dumps(old_marker))
        # The new file was already atomically installed; manifest was not.
        (game / "Data/Map001.rxdata").write_bytes(b"NEW")
        with patch("scripts.android.update_client._replace_from_zip") as write:
            updated, removed, backup = apply_patch(
                game, read_installed(game), manifest,
                self.root / "Blue-Android-Kanto-Piloto.patch.zip")
            write.assert_not_called()
        self.assertEqual((updated, removed, backup), (0, 0, None))
        self.assertEqual(read_installed(game)["revision"], self.b)
        self.assertFalse((game / ".blue-android-update-backups").exists())

    def test_publish_multiple_revisions_and_select_matching_patch(self):
        _, a_manifest = self.build_zip(self.a, b"OLD A")
        _, b_manifest = self.build_zip(self.b, b"OLD B")
        new_revision = "c" * 40
        new, _ = self.build_zip(new_revision, b"LATEST")
        oldpath = self.root / "a-prev.json"
        middlepath = self.root / "b-prev.json"
        oldpath.write_text(json.dumps(a_manifest))
        middlepath.write_text(json.dumps(b_manifest))
        full = self.root / "Blue-Android-Kanto-Piloto.zip"
        new.rename(full)
        published = publish(full, "kanto", oldpath, [middlepath])
        self.assertEqual(len(published["patches"]), 2)
        manifest = json.loads((self.root / "Blue-Android-Kanto-Piloto.update.json").read_text())
        release = {"assets": [
            {"name": p["asset"], "state": "uploaded",
             "browser_download_url": (
                "https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/download/test/"
                + p["asset"])}
            for p in published["patches"]]}
        selected = compatible_patch(release, b_manifest, manifest)
        self.assertEqual(selected["from_revision"], self.b)
        self.assertIn(".from-" + self.b[:12], selected["asset"])

    def test_manual_full_does_not_rewrite_identical_content(self):
        game, old = self.installed_full_fixture()
        source = game / "Data/Map001.rxdata"
        original_time = source.stat().st_mtime_ns
        full, _ = self.full_zip_fixture(self.b, b"OLD MAP", b"OLD EXE")
        publish(full, "kanto")
        manifest = json.loads((self.root / "Blue-Android-Kanto-Piloto.update.json").read_text())
        _, changed = apply_full_archive(game, old, manifest, full)
        self.assertEqual(changed, 0)
        self.assertEqual(source.stat().st_mtime_ns, original_time)
        self.assertEqual((game / "personal-note.txt").read_text(), "old user data")

    def _release(self, tag, published, revision=None, draft=False):
        name = "Blue-Android-Decades-Kanto-Hoenn"
        url = ("https://github.com/GabrielChavesAlencar/"
               "Pokemon-Blue-Dessastre-Paradoxal/releases/download/" +
               tag + "/")
        return {"tag_name": tag, "published_at": published,
                "draft": draft, "target_commitish": revision or self.a,
                "assets": [
                    {"name": name + ".zip", "state": "uploaded",
                     "browser_download_url": url + name + ".zip"},
                    {"name": name + ".update.json", "state": "uploaded",
                     "browser_download_url": url + name + ".update.json"},
                ]}

    def test_multiregion_release_chooses_newest_not_first_in_api(self):
        # Actual Nov 15 response order was 9, 3, 15. 9 is OLDER than 15.
        releases = [
            self._release("android-multiregion-9-af0c494",
                          "2026-11-15T21:52:28Z"),
            self._release("android-multiregion-3-7893358",
                          "2026-11-15T20:42:52Z"),
            self._release("android-multiregion-15-125155e",
                          "2026-11-15T22:19:12Z"),
        ]
        with patch("scripts.android.update_client.get_json",
                   return_value=releases):
            best = release_for("multiregion")
        self.assertEqual(best["tag_name"], "android-multiregion-15-125155e")

    def test_kanto_release_is_found_on_fourth_github_page(self):
        # Battle-hub releases pushed the last valid Kanto publication to
        # page 4 (Nov 18, 2026). A three-page reader would demand a full ZIP.
        unrelated = [self._release("battle-hub-900-release",
                                   "2026-11-18T16:00:00Z") for _ in range(100)]
        old = self._release("kanto-android-1205-f4b574e",
                            "2026-11-16T12:00:00Z")
        pages = [unrelated, unrelated, unrelated, [old]]
        with patch("scripts.android.update_client.get_json",
                   side_effect=pages) as request:
            found = release_for("kanto")
        self.assertEqual(found["tag_name"], old["tag_name"])
        self.assertEqual(request.call_count, 4)
        self.assertTrue(request.call_args.args[0].endswith("&page=4"))

    def test_release_selector_ignores_drafts_and_missing_manifest(self):
        releases = [
            self._release("android-multiregion-20-draft",
                          "2026-11-15T23:00:00Z", draft=True),
            self._release("android-multiregion-19-incomplete",
                          "2026-11-15T22:45:00Z"),
            self._release("android-multiregion-15-valid",
                          "2026-11-15T22:19:12Z"),
        ]
        releases[1]["assets"] = releases[1]["assets"][:1]
        with patch("scripts.android.update_client.get_json",
                   return_value=releases):
            best = release_for("multiregion")
        self.assertEqual(best["tag_name"], "android-multiregion-15-valid")

    def test_github_ancestry_blocks_downgrade_before_any_download(self):
        # The candidate may be published but a stale API entry may still
        # target an older commit. Never trust tag numbers alone.
        for status in ("behind", "diverged", "identical", None):
            with self.subTest(status=status):
                with patch("scripts.android.update_client.get_json",
                           return_value={"status": status}):
                    with self.assertRaisesRegex(ValueError,
                                                "Atualizacao BLOQUEADA"):
                        verify_forward_revision(self.b, self.a)

    def test_github_ancestry_allows_ahead_and_same_revision(self):
        with patch("scripts.android.update_client.get_json",
                   return_value={"status": "ahead"}) as request:
            verify_forward_revision(self.a, self.b)
            request.assert_called_once_with(
                "https://api.github.com/repos/"
                "GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/"
                "compare/" + self.a + "..." + self.b)
        with patch("scripts.android.update_client.get_json",
                   side_effect=RuntimeError("No API call allowed")):
            verify_forward_revision(self.a, self.a)

    def test_termux_refuses_downgrade_before_downloading_zip(self):
        game, _ = self.installed_full_fixture()
        manifest = {
            "schema": 1, "channel": "kanto", "revision": self.b,
            "files": {}, "immutable": {}, "patch": None,
            "full": {"asset": "Blue-Android-Kanto-Piloto.zip",
                     "size": 100, "sha256": "0" * 64},
        }
        with (patch("scripts.android.update_client.remote_update",
                    return_value=({"assets": []}, manifest)),
              patch("scripts.android.update_client.get_json",
                    return_value={"status": "behind"}),
              patch("scripts.android.update_client.download") as download):
            with self.assertRaisesRegex(ValueError, "Atualizacao BLOQUEADA"):
                main(["--game-dir", str(game), "--update"])
            download.assert_not_called()
        self.assertEqual(read_installed(game)["revision"], self.a)

if __name__ == "__main__":
    unittest.main()
