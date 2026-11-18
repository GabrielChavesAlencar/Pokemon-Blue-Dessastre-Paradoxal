"""No-network tests for the opt-in regional map performance preview."""
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch, MagicMock
from scripts.android import preview_update as preview


class PreviewUpdateSafetyTests(unittest.TestCase):
    def test_preview_is_never_a_stable_android_release(self):
        self.assertIsNone(preview.PREVIEW.fullmatch("android-multiregion-hotfix-27-767347c"))
        self.assertIsNone(preview.PREVIEW.fullmatch("android-map-perf-preview-1234567/unsafe"))
        self.assertIsNone(preview.PREVIEW.fullmatch("android-map-perf-preview-123456"))
        self.assertIsNotNone(preview.PREVIEW.fullmatch("android-map-perf-preview-1234567"))

    def test_wrong_release_identity_or_commit_rejected_without_installation(self):
        good = {
            "tag_name": "android-map-perf-preview-1234567",
            "prerelease": True,
            "draft": False,
            "target_commitish": "1234567" + "a" * 33,
        }
        with patch.object(preview, "get_json", return_value=good):
            self.assertEqual(preview.trusted_preview(good["tag_name"])[1],
                             good["target_commitish"])
        for changes in (
            {"draft": True}, {"prerelease": False},
            {"target_commitish": "b" * 40}, {"tag_name": "android-other"},
            {"target_commitish": "not-a-commit"},
        ):
            with self.subTest(changes=changes), patch.object(
                preview, "get_json", return_value={**good, **changes}
            ):
                with self.assertRaises(ValueError):
                    preview.trusted_preview(good["tag_name"])

    def test_missing_compatible_delta_refuses_full_download(self):
        release = {"tag_name": "android-map-perf-preview-1234567"}
        sha = "1234567" + "a" * 33
        client = MagicMock()
        client.CHANNELS = {
            "multiregion": ("Blue-Android-Decades-Kanto-Hoenn.zip", "manifest.json")
        }
        client.read_installed.return_value = {
            "schema": 1, "channel": "multiregion", "revision": "c" * 40
        }
        client.asset_url.return_value = "https://github.com/example/manifest"
        client.get_json.return_value = {
            "schema": 1, "channel": "multiregion",
            "revision": sha, "files": {}
        }
        client.compatible_patch.return_value = None
        with tempfile.TemporaryDirectory() as folder, patch.object(
            preview, "trusted_preview", return_value=(release, sha)
        ), patch.object(preview, "load_pinned_updater", return_value=client):
            with self.assertRaisesRegex(ValueError, "Não há delta validado"):
                preview.install(Path(folder), "android-map-perf-preview-1234567", apply=True)
        client.download.assert_not_called()
        client.apply_patch.assert_not_called()

    def test_dry_run_never_writes_and_matching_revision_is_no_op(self):
        release = {"tag_name": "android-map-perf-preview-1234567"}
        sha = "1234567" + "a" * 33
        client = MagicMock()
        client.CHANNELS = {"multiregion": ("archive.zip", "manifest.json")}
        client.read_installed.return_value = {
            "schema": 1, "channel": "multiregion", "revision": "b" * 40
        }
        client.asset_url.return_value = "https://github.com/example/file"
        client.get_json.return_value = {
            "schema": 1, "channel": "multiregion",
            "revision": sha, "files": {}
        }
        client.compatible_patch.return_value = {
            "asset": "patch.zip", "sha256": "a" * 64, "size": 99
        }
        with tempfile.TemporaryDirectory() as folder, patch.object(
            preview, "trusted_preview", return_value=(release, sha)
        ), patch.object(preview, "load_pinned_updater", return_value=client):
            self.assertEqual(preview.install(Path(folder),
                            "android-map-perf-preview-1234567"), 0)
            client.apply_patch.assert_not_called()
            client.download.assert_not_called()
            client.read_installed.return_value["revision"] = sha
            self.assertEqual(preview.install(Path(folder),
                            "android-map-perf-preview-1234567", apply=True), 0)
            client.apply_patch.assert_not_called()
            client.download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
