"""Safety checks for the user-supplied Kanto ZIP publishing helper."""
from __future__ import annotations

import hashlib
import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts.music import publish_kanto_release as music


class KantoReleaseArchiveTests(unittest.TestCase):
    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.archive = Path(self._directory.name) / "pkm msc kanto.zip"

    def make_archive(self, count=64, malicious=None):
        with zipfile.ZipFile(self.archive, "w", zipfile.ZIP_DEFLATED) as z:
            for n in range(count):
                track_no = n + 1 if n < 60 else 70 + (n - 60)
                name = f"pkm msc kanto/1-{track_no:02d}. Demo.mp3"
                z.writestr(name, b"ID3" + (b"\x00" * 1024))
            if malicious:
                z.writestr(malicious, b"ID3" + (b"\x00" * 1024))
        return hashlib.sha256(self.archive.read_bytes()).hexdigest()

    def test_exact_64_tracks_check_and_dry_run(self):
        # Test a fabricated fixture; never require or redistribute copyrighted MP3s.
        digest = self.make_archive(count=64)
        with patch.object(music, "EXPECTED_ZIP_SHA256", digest):
            manifest = music.inspect_archive(self.archive)
            self.assertEqual(manifest["tracks_count"], 64)
            self.assertEqual(len(manifest["tracks"]), 64)
            self.assertEqual(manifest["archive_sha256"], digest)
            self.assertTrue(manifest["audited_not_uploaded"])
            with patch.object(music, "publish_release") as publish:
                self.assertEqual(music.main(["--archive", str(self.archive)]), 0)
                publish.assert_not_called()

    def test_rejects_missing_track(self):
        digest = self.make_archive(count=63)
        with patch.object(music, "EXPECTED_ZIP_SHA256", digest):
            with self.assertRaisesRegex(ValueError, "64"):
                music.inspect_archive(self.archive)

    def test_rejects_foreign_or_unsafe_zip_paths(self):
        digest = self.make_archive(count=63, malicious="pkm msc kanto/../../foo.mp3")
        with patch.object(music, "EXPECTED_ZIP_SHA256", digest):
            with self.assertRaisesRegex(ValueError, "inseguro"):
                music.inspect_archive(self.archive)

    def test_rejects_modified_archive_hash(self):
        self.make_archive()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            music.inspect_archive(self.archive)

    def test_explicit_rights_required_for_public_publishing(self):
        digest = self.make_archive()
        with patch.object(music, "EXPECTED_ZIP_SHA256", digest):
            with patch.object(music, "publish_release") as publish:
                result = music.main(["--archive", str(self.archive), "--publish"])
                self.assertEqual(result, 2)
                publish.assert_not_called()
                result = music.main(
                    ["--archive", str(self.archive), "--publish", "--confirm-rights"]
                )
                self.assertEqual(result, 0)
                publish.assert_called_once()

    def test_no_replacing_an_existing_release(self):
        from subprocess import CompletedProcess
        digest = self.make_archive()
        with patch.object(music, "EXPECTED_ZIP_SHA256", digest):
            with patch.object(music.shutil, "which", return_value="gh"):
                with patch.object(music.subprocess, "run") as run:
                    run.side_effect = [
                        CompletedProcess(["gh", "auth", "status"], 0),
                        CompletedProcess(["gh", "release", "view"], 0),
                    ]
                    with self.assertRaisesRegex(RuntimeError, "Ja existe"):
                        music.publish_release(self.archive, repo=music.DEFAULT_REPO,
                                              tag=music.DEFAULT_TAG)
                    self.assertEqual(run.call_count, 2)


if __name__ == "__main__":
    unittest.main()
