"""Inert Sinnoh deep audit tests with synthetic RMXP data, not donor assets."""
from __future__ import annotations

import hashlib
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_rxdata import audit_rxdata
from build_johto_events import ruby, EVENT_CLASSES
from stage import serialize


def fixture_files(include_graphics=True):
    maps = {
        "Data/MapInfos.rxdata": serialize({
            1: ruby("RPG::MapInfo", name=b"Twinleaf Town"),
            2: ruby("RPG::MapInfo", name=b"Route 201"),
        }),
        "Data/Tilesets.rxdata": serialize([
            None, ruby("RPG::Tileset", tileset_name=b"Sample",
                       autotile_names=[b"Water"])])
    }
    commands = [
        ruby("RPG::EventCommand", code=201, parameters=[0, 2, 4, 5, 2, 0]),
        ruby("RPG::EventCommand", code=201, parameters=[1, 44, 45, 46, 2, 0]),
        ruby("RPG::EventCommand", code=355, parameters=[b"do_not_execute()"]),
    ]
    event = ruby("RPG::Event", pages=[ruby("RPG::Event::Page", list=commands)])
    maps["Data/Map001.rxdata"] = serialize(ruby(
        "RPG::Map", width=20, height=22, tileset_id=1, events={1: event}
    ), EVENT_CLASSES)
    maps["Data/Map003.rxdata"] = serialize(ruby(
        "RPG::Map", width=15, height=12, tileset_id=1, events={}
    ), EVENT_CLASSES)
    if include_graphics:
        maps["Graphics/Tilesets/Sample.png"] = b"\x89PNG\r\n\x1a\nfake fixture"
    return maps


class SinnohDeepAuditTests(unittest.TestCase):
    def make_directory(self, root: Path):
        source = root / "sinnoh-source"
        for name, raw in fixture_files().items():
            dest = source / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(raw)
        return source

    def make_zip(self, root: Path):
        source = root / "sinnoh.zip"
        with zipfile.ZipFile(source, "w") as archive:
            for rel, raw in fixture_files().items():
                archive.writestr("Ancient Platinum/" + rel, raw)
        return source

    def assert_read_only_report(self, report):
        self.assertEqual(report["source_map_count"], 2)
        self.assertEqual(report["source_map_ids"], [1, 3])
        self.assertEqual(report["missing_map_files"], [2])
        self.assertEqual(report["orphan_map_files"], [3])
        self.assertEqual(report["unresolved_static_transfer_ids"], [2])
        self.assertEqual(report["untrusted_script_commands_not_executed"], 1)
        self.assertEqual(report["dynamic_transfer_commands"], 1)
        self.assertEqual(report["missing_graphics"], ["Graphics/Autotiles/Water.png"])
        self.assertEqual(report["invalid_graphic_names"], [])
        self.assertEqual(report["maps"][0]["name"], "Twinleaf Town")
        self.assertEqual(report["maps"][0]["event_pages"], 1)
        self.assertFalse(report["rights_verified"])
        self.assertFalse(report["import_allowed"])
        self.assertFalse(report["pilot_verified"])

    def test_directory_parses_maps_and_detects_dangling_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_directory(root)
            original = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in source.rglob("*") if p.is_file()}
            native = root / "game" / "Data"
            native.mkdir(parents=True)
            (native / "Map001.rxdata").write_bytes(b"existing Decades map")
            report = audit_rxdata(source, native)
            self.assertEqual(report["unmapped_id_collisions"], [1])
            self.assert_read_only_report(report)
            latest = {p.relative_to(source).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in source.rglob("*") if p.is_file()}
            self.assertEqual(original, latest)
            self.assertEqual((native / "Map001.rxdata").read_bytes(), b"existing Decades map")

    def test_zip_parses_directly_without_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.make_zip(root)
            original_digest = hashlib.sha256(source.read_bytes()).hexdigest()
            report = audit_rxdata(source)
            self.assert_read_only_report(report)
            self.assertEqual(report["source_mode"], "ZIP_METADATA_ONLY")
            self.assertEqual(report["source_zip_sha256"], original_digest)
            self.assertFalse((root / "Ancient Platinum").exists())

    def test_rejects_corrupt_source_marshal(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.make_directory(Path(directory))
            (source / "Data/Map001.rxdata").write_bytes(b"not a marshal archive")
            with self.assertRaisesRegex(ValueError, "Ruby Marshal inválido"):
                audit_rxdata(source)

    def test_rejects_unresolved_tileset_not_silently_import(self):
        with tempfile.TemporaryDirectory() as directory:
            source = self.make_directory(Path(directory))
            (source / "Data/Tilesets.rxdata").write_bytes(
                serialize([None, ruby("RPG::Tileset",
                                      tileset_name=b"Sample", autotile_names=[])]))
            (source / "Data/Map003.rxdata").write_bytes(
                serialize(ruby("RPG::Map", width=16, height=16,
                               tileset_id=5, events={})))
            with self.assertRaisesRegex(ValueError, "tileset 5 inexistente"):
                audit_rxdata(source)

    def test_rejects_zip_traversal(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("../Ancient Platinum/Data/MapInfos.rxdata", b"fake")
                archive.writestr("Data/Tilesets.rxdata", b"fake")
            with self.assertRaisesRegex(ValueError, "inseguro"):
                audit_rxdata(path)


if __name__ == "__main__":
    unittest.main()
