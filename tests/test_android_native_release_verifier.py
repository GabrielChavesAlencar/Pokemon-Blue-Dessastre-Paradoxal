"""Offline fail-closed tests for the native Android release safety verifier."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from scripts.android import verify_native_multiregion_update as native

NEW = "b" * 40
PREVIEW = native.PREVIEW_REVISION


class NativeReleaseVerifierTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.bundle = self.root / "Blue-Android-Decades-Kanto-Hoenn.zip"
        self.manifest = self.root / "Blue-Android-Decades-Kanto-Hoenn.update.json"
        self.mapping = {str(i): i + 700 for i in range(142)}
        self.music = []
        for i in range(74):
            number = i + 700
            track = native.TRACKS.get(str(i), "Kanto/example.mp3")
            self.music.append(f"MAP\\t{number}\\t{track}\\t100\\t100")
        self.plugin = b"module BlueRegionTravel\\n  def self.agent_map_id(region); 700; end\\nend\\n"
        self.make_zip()
        self.make_manifest()

    def make_zip(self):
        with zipfile.ZipFile(self.bundle, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            entries = {
                native.PREFIX + native.TRAVEL: self.plugin,
                native.PREFIX + native.CACHE: b"fake-Marshal-cache-not-game",
                native.PREFIX + native.MUSIC: ("BLUE_KANTO_MUSIC_V1\\tKANTO\\t" + "a" * 64 +
                                             "\\n" + "\\n".join(self.music) + "\\n").encode(),
                native.PREFIX + native.KANTO_INSTALL: json.dumps({"maps": self.mapping}).encode(),
                native.PREFIX + "Data/blue-update.json": json.dumps(
                    {"revision": NEW, "channel": "multiregion"}).encode(),
            }
            for name, data in entries.items():
                archive.writestr(name, data)

    def make_manifest(self, *, changed=None):
        name = "Blue-Android-Decades-Kanto-Hoenn.patch.zip"
        delta = self.root / name
        changed = changed if changed is not None else {"Data/PluginScripts.rxdata": {"size": 3}}
        with zipfile.ZipFile(delta, "w") as archive:
            archive.writestr("patch.json", json.dumps({
                "schema": 1, "channel": "multiregion",
                "from_revision": PREVIEW, "to_revision": NEW,
                "changed": changed, "removed": [],
            }))
        meta = {
            "asset": name, "size": delta.stat().st_size,
            "sha256": hashlib.sha256(delta.read_bytes()).hexdigest(),
            "from_revision": PREVIEW,
        }
        self.manifest.write_text(json.dumps({
            "schema": 1, "channel": "multiregion", "revision": NEW,
            "patches": [meta]
        }), encoding="utf-8")

    def test_good_native_package_and_preview_delta(self):
        with patch.object(native, "compiled_region", return_value="verified") as verify:
            report = native.verify_zip(self.bundle, NEW)
        self.assertEqual(report, {"music_maps": 74, "kanto_maps": 142, "optimized": True})
        verify.assert_called_once()
        self.assertEqual(native.verify_manifest(self.manifest, NEW)["preview_delta"],
                         "Blue-Android-Decades-Kanto-Hoenn.patch.zip")

    def test_rejects_missing_map_optimization_even_if_cache_is_present(self):
        self.plugin = b"module BlueRegionTravel; end"
        self.make_zip()
        with patch.object(native, "compiled_region") as verify:
            with self.assertRaisesRegex(ValueError, "dispatcher missing"):
                native.verify_zip(self.bundle, NEW)
        verify.assert_not_called()

    def test_compiled_plugin_must_match_source(self):
        with patch.object(native, "compiled_region", side_effect=ValueError("stale compiled plugin")):
            with self.assertRaisesRegex(ValueError, "stale compiled plugin"):
                native.verify_zip(self.bundle, NEW)

    def test_cerulean_and_route4_cannot_be_replaced_by_other_tracks(self):
        self.music[33] = self.music[33].replace(native.TRACKS["33"], "Kanto/wrong.mp3")
        self.make_zip()
        with patch.object(native, "compiled_region"):
            with self.assertRaisesRegex(ValueError, "source map 33"):
                native.verify_zip(self.bundle, NEW)

    def test_missing_one_music_map_rejected(self):
        self.music.pop()
        self.make_zip()
        with patch.object(native, "compiled_region"):
            with self.assertRaisesRegex(ValueError, "74 unique"):
                native.verify_zip(self.bundle, NEW)

    def test_wrong_revision_refused(self):
        with patch.object(native, "compiled_region"):
            with self.assertRaisesRegex(ValueError, "revision/channel"):
                native.verify_zip(self.bundle, "c" * 40)
        with self.assertRaisesRegex(ValueError, "does not match"):
            native.verify_manifest(self.manifest, "c" * 40)

    def test_no_preview_delta_is_never_a_success(self):
        self.make_manifest()
        self.manifest.write_text(json.dumps({
            "schema": 1, "channel": "multiregion",
            "revision": NEW, "patches": []
        }))
        with self.assertRaisesRegex(ValueError, "No unique"):
            native.verify_manifest(self.manifest, NEW)

    def test_missing_or_modified_patch_payload_is_refused(self):
        self.make_manifest()
        (self.root / "Blue-Android-Decades-Kanto-Hoenn.patch.zip").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "wrong size"):
            native.verify_manifest(self.manifest, NEW)

    def test_preview_patch_may_not_modify_native_game_or_saves(self):
        for file in ("Game.exe", "Saves/Slot A.rxdata", "Data/Save001.rxdata"):
            with self.subTest(path=file):
                self.make_manifest(changed={file: {"size": 3}})
                with self.assertRaisesRegex(ValueError, "Game.exe or saves"):
                    native.verify_manifest(self.manifest, NEW)

    def test_known_android_launcher_fixture_is_byte_exact(self):
        project = Path(__file__).resolve().parents[1]
        attrs = (project / ".gitattributes").read_text(encoding="utf-8")
        self.assertIn("tests/fixtures/android_updater_launcher_20261117.py -text", attrs)
        source = (project / "tests/fixtures/android_updater_launcher_20261117.py").read_bytes()
        self.assertEqual(len(source), 1911)
        from scripts.android.update_client import KNOWN_ANDROID_LAUNCHERS
        self.assertIn(hashlib.sha256(source).hexdigest(), KNOWN_ANDROID_LAUNCHERS)


if __name__ == "__main__":
    unittest.main()
