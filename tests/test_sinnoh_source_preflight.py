"""Read-only Sinnoh preflight contracts; requires no game assets or donor ZIP."""
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_source import (
    EXPECTED_BADGES, audit, inspect_directory, inspect_zip,
    validate_registry,
)


class SinnohPreflightTests(unittest.TestCase):
    def make_zip(self, folder: Path, names):
        path = folder / "Sinnoh.zip"
        with zipfile.ZipFile(path, "w") as archive:
            for name in names:
                archive.writestr(name, b"fixture, not an actual map")
        return path

    def test_repository_registry_and_title_are_safe(self):
        registry = validate_registry(ROOT)
        self.assertEqual(registry["status"], "planned")
        self.assertEqual(tuple(registry["badges"]), EXPECTED_BADGES)
        self.assertEqual(registry["league_unlocks"], ["HOENN", "UNOVA"])
        with tempfile.TemporaryDirectory() as tmp:
            report = audit(root=ROOT, game_data=Path(tmp) / "missing-game-data")
        self.assertEqual(report["mode"], "READ_ONLY")
        self.assertEqual(report["title_option"], "WIRED_NO_REAL_PILOT")
        self.assertEqual(report["technical_phases_approved"], 0)
        self.assertFalse(report["map_installation_verified"])
        self.assertIn("Fonte real de Sinnoh não fornecida", report["blockers"])

    def test_zip_only_reads_metadata_and_detects_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            zip_path = self.make_zip(root, [
                "Ancient Platinum/Data/MapInfos.rxdata",
                "Ancient Platinum/Data/Tilesets.rxdata",
                "Ancient Platinum/Data/Map001.rxdata",
                "Ancient Platinum/Data/Map002.rxdata",
            ])
            data = root / "game" / "Data"
            data.mkdir(parents=True)
            (data / "Map001.rxdata").write_bytes(b"native fixture")
            result = audit(root=ROOT, source=zip_path, game_data=data)
            self.assertEqual(result["source"]["source_map_ids"], [1, 2])
            self.assertTrue(result["source"]["empty_or_template_source"])
            self.assertEqual(result["unmapped_id_collisions"], [1])
            self.assertEqual(result["source"]["mode"], "ZIP_METADATA_ONLY")
            self.assertTrue(result["source"]["sha256_zip"])
            self.assertFalse(result["rights_verified"])
            self.assertFalse((root / "Ancient Platinum").exists())

    def test_zip_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.make_zip(Path(tmp), [
                "../Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
                "Data/Map001.rxdata",
            ])
            with self.assertRaisesRegex(ValueError, "inseguro"):
                inspect_zip(path)

    def test_zip_rejects_duplicate_map_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.make_zip(Path(tmp), [
                "Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
                "Data/Map001.rxdata", "Data/Map1.rxdata",
            ])
            with self.assertRaisesRegex(ValueError, "duplicados"):
                inspect_zip(path)

    def test_zip_rejects_multiple_projects(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.make_zip(Path(tmp), [
                "A/Data/MapInfos.rxdata", "A/Data/Tilesets.rxdata",
                "A/Data/Map001.rxdata",
                "B/Data/MapInfos.rxdata", "B/Data/Tilesets.rxdata",
                "B/Data/Map001.rxdata",
            ])
            with self.assertRaisesRegex(ValueError, "exatamente um"):
                inspect_zip(path)

    def test_directory_source_is_not_installed(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "donor"
            data = source / "Data"
            data.mkdir(parents=True)
            for name in ("MapInfos.rxdata", "Tilesets.rxdata", "Map001.rxdata"):
                (data / name).write_bytes(b"fixture")
            result = inspect_directory(source)
            self.assertEqual(result["source_map_ids"], [1])
            self.assertEqual(result["mode"], "LOCAL_DIRECTORY_METADATA_ONLY")
            self.assertFalse(result["permission_confirmed"])
            self.assertEqual(set(file.name for file in data.iterdir()), {
                "MapInfos.rxdata", "Tilesets.rxdata", "Map001.rxdata"
            })

    def test_cannot_use_game_as_source(self):
        with self.assertRaisesRegex(ValueError, "game/"):
            audit(root=ROOT, source=ROOT / "game", game_data=Path("/not-real"))


if __name__ == "__main__":
    unittest.main()
