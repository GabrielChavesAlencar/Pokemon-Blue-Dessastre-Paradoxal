"""Local synthetic coverage of the K06 same-runner archive reuse contract."""
import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from seed_kanto_source_ci import RELATIVE_ARCHIVE, RELATIVE_SOURCE, seed_archive
import ensure_source


PAYLOAD = b"synthetic FRLG archive fixture; not a donor archive"
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()


class KantoCISourceReuseTests(unittest.TestCase):
    def setUp(self):
        fixture = tempfile.TemporaryDirectory()
        self.addCleanup(fixture.cleanup)
        self.root = Path(fixture.name).resolve()
        self.workspace = self.root / "checkout"
        self.source = self.workspace / "k05-recipe"
        self.target = self.workspace / "k06-public-recipe"
        self.source.mkdir(parents=True)
        self.target.mkdir()
        self.donor = self.source / RELATIVE_ARCHIVE
        self.destination = self.target / RELATIVE_ARCHIVE

    def write_donor(self, data=PAYLOAD):
        self.donor.parent.mkdir(parents=True, exist_ok=True)
        self.donor.write_bytes(data)

    def test_one_transfer_then_stock_bootstrap_revalidates_local_copies(self):
        url = "https://example.invalid/FRLG.rar"
        with patch.object(ensure_source, "urlopen", return_value=io.BytesIO(PAYLOAD)) as http:
            ensure_source.download_pinned(url, self.donor, DIGEST)
            self.assertEqual(seed_archive(self.workspace, self.source, self.target, DIGEST),
                             self.destination)
            ensure_source.download_pinned(url, self.donor, DIGEST)
            ensure_source.download_pinned(url, self.destination, DIGEST)
            http.assert_called_once()
        self.destination.write_bytes(b"changed after copying")
        self.assertEqual(self.donor.read_bytes(), PAYLOAD)
        with patch.object(ensure_source, "urlopen", side_effect=AssertionError("no fallback")):
            with self.assertRaisesRegex(RuntimeError, "hash diferente"):
                ensure_source.download_pinned(url, self.destination, DIGEST)
        self.assertEqual(self.destination.read_bytes(), b"changed after copying")
        self.assertFalse((self.target / RELATIVE_SOURCE).exists())

    def test_bad_or_missing_input_does_not_create_target_cache(self):
        with self.assertRaises(FileNotFoundError):
            seed_archive(self.workspace, self.source, self.target, DIGEST)
        self.write_donor(b"tampered input")
        with self.assertRaisesRegex(ValueError, "pinned SHA-256"):
            seed_archive(self.workspace, self.source, self.target, DIGEST)
        self.assertEqual(self.donor.read_bytes(), b"tampered input")
        self.assertFalse(self.destination.parent.exists())

    def test_existing_archive_or_partial_is_preserved(self):
        self.write_donor()
        self.destination.parent.mkdir(parents=True)
        for holder in (self.destination, self.destination.with_suffix(".rar.part")):
            with self.subTest(holder=holder.name):
                holder.write_bytes(b"pre-existing data")
                with self.assertRaisesRegex(ValueError, "overwrite"):
                    seed_archive(self.workspace, self.source, self.target, DIGEST)
                self.assertEqual(holder.read_bytes(), b"pre-existing data")
                holder.unlink()

    def test_existing_extracted_source_is_not_silently_trusted(self):
        self.write_donor()
        extracted = self.target / RELATIVE_SOURCE
        extracted.mkdir(parents=True)
        sentinel = extracted / "edited-map.txt"
        sentinel.write_bytes(b"keep local changes")
        with self.assertRaisesRegex(ValueError, "overwrite"):
            seed_archive(self.workspace, self.source, self.target, DIGEST)
        self.assertFalse(self.destination.exists())
        self.assertEqual(sentinel.read_bytes(), b"keep local changes")

    def test_copy_tamper_is_rejected_and_staging_is_removed(self):
        self.write_donor()
        with patch("seed_kanto_source_ci.shutil.copyfileobj",
                   side_effect=lambda incoming, output, length: output.write(b"tampered copy")):
            with self.assertRaisesRegex(ValueError, "staged FRLG copy"):
                seed_archive(self.workspace, self.source, self.target, DIGEST)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.destination.parent.iterdir()), [])
        self.assertEqual(self.donor.read_bytes(), PAYLOAD)

    def test_destination_created_concurrently_is_never_replaced(self):
        self.write_donor()

        def appears(staged, output):
            output.write_bytes(b"another process owns this path")
            raise FileExistsError("destination already exists")

        with patch("seed_kanto_source_ci.os.link", side_effect=appears):
            with self.assertRaises(FileExistsError):
                seed_archive(self.workspace, self.source, self.target, DIGEST)
        self.assertEqual(self.destination.read_bytes(), b"another process owns this path")
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_only_distinct_roots_inside_same_workspace(self):
        self.write_donor()
        outside = self.root / "different-workspace"
        outside.mkdir()
        for source, target in ((self.source, outside), (outside, self.target),
                               (self.source, self.source)):
            with self.subTest(source=source, target=target):
                with self.assertRaisesRegex(ValueError, "same CI workspace"):
                    seed_archive(self.workspace, source, target, DIGEST)
        self.assertFalse((outside / RELATIVE_ARCHIVE).exists())
        self.assertFalse(self.destination.exists())
