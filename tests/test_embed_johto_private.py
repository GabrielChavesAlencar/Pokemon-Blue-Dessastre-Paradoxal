"""Synthetic PE overlay tests; no copyrighted assets or private maps in CI."""
import hashlib
import io
import struct
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts.windows import embed_johto_private as emb


def fixture_zip():
    with io.BytesIO() as mem:
        with zipfile.ZipFile(mem, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for mid in range(600, 682):
                archive.writestr(f"Johto_Offline_Fase12/Data/Map{mid:03}.rxdata",
                                 b"synthetic testing only")
        return mem.getvalue()


class PrivateJohtoExecutableTests(unittest.TestCase):
    def test_personal_executable_contains_exact_original_archive_and_footer(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source = folder / "Blue-Story-public.exe"
            archive = folder / "Johto_Offline_Fase12.zip"
            output = folder / "Blue-Story.exe"
            source.write_bytes(b"MZ" + b"synthetic PE fixture")
            data = fixture_zip()
            archive.write_bytes(data)
            with patch.object(emb, "PINNED_SHA256", hashlib.sha256(data).hexdigest()):
                report = emb.package(source, archive, output)
                self.assertEqual(report["johto_bytes"], len(data))
                product = output.read_bytes()
                self.assertEqual(emb.read_embedded(product), data)
                self.assertTrue(product.endswith(emb.MAGIC + struct.pack("<q", len(data))))
                self.assertEqual(source.read_bytes(), b"MZsynthetic PE fixture")
                with self.assertRaisesRegex(ValueError, "já existe"):
                    emb.package(source, archive, output)

    def test_wrong_hash_malformed_payload_and_embedded_source_are_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            source, archive, output = [folder / x for x in
                                       ("base.exe", "pack.zip", "output.exe")]
            source.write_bytes(b"MZEXE")
            data = fixture_zip()
            archive.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "hash privado"):
                emb.package(source, archive, output)
            self.assertFalse(output.exists())
            with patch.object(emb, "PINNED_SHA256", hashlib.sha256(data).hexdigest()):
                emb.package(source, archive, output)
                with self.assertRaisesRegex(ValueError, "já tem um pacote"):
                    emb.package(output, archive, folder / "other.exe")
            with self.assertRaisesRegex(ValueError, "tamanho Johto inválido"):
                emb.read_embedded(b"MZ" + emb.MAGIC + struct.pack("<q", 99_999_999))
            self.assertIsNone(emb.read_embedded(b"MZNormalPE"))


if __name__ == "__main__":
    unittest.main()
