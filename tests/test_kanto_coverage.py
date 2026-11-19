"""Coverage must expose missing locations, not certify a partial catalog."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_kanto_coverage import audit
from stage import serialize
from server.ruby_marshal import RubyData, RubyObject


class KantoCoverageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.source = Path(temporary.name)
        (self.source / "Data").mkdir()
        (self.source / "PBS").mkdir()
        infos = {
            mid: RubyObject("RPG::MapInfo", {
                "@name": name, "@parent_id": parent})
            for mid, parent, name in (
                (1, 0, b"Debug"), (4, 0, b"Kanto"), (5, 4, b"City"),
                (6, 4, b"Preview"), (7, 4, b"Missing route"),
                (8, 4, b"Cave folder"), (9, 8, b"Cave 1F"))}
        self.write_infos(infos)
        table = RubyData("Table", struct.pack("<5i900h", 3, 20, 15, 3, 900,
                                             *([384] * 300 + [0] * 600)))
        transfer = RubyObject("RPG::EventCommand", {
            "@code": 201, "@parameters": [0, 9, 1, 1, 2, 0]})
        event = RubyObject("RPG::Event", {"@pages": [
            RubyObject("RPG::Event::Page", {"@list": [transfer]})]})
        for mid in infos:
            native = RubyObject("RPG::Map", {
                "@width": 20, "@height": 15, "@data": table,
                "@events": {1: event} if mid == 5 else {}})
            (self.source / f"Data/Map{mid:03}.rxdata").write_bytes(serialize(
                native, {"RPG::Event", "RPG::Event::Page", "RPG::EventCommand"}))
        (self.source / "PBS/map_connections.txt").write_text(
            "# Unimported map on either side of a native connection\n"
            "7,West,0,5,East,0\n", encoding="utf8")
        self.manifest = {"maps": {"5": "CITY", "6": "PREVIEW"},
                         "preview_only": [6], "sha256": "a" * 64}

    def write_infos(self, infos):
        (self.source / "Data/MapInfos.rxdata").write_bytes(serialize(infos))

    def test_missing_content_is_separate_from_previews_and_hierarchy(self):
        report = audit(self.source, self.manifest)
        self.assertEqual(report["source_kanto_entries"], 5)
        self.assertEqual(report["catalogued_maps"], 2)
        self.assertEqual(report["preview_only_maps"], 1)
        self.assertEqual([r["source_id"] for r in report["omitted_content"]], [7, 9])
        self.assertEqual([r["source_id"] for r in report["hierarchy_candidates"]], [8])
        self.assertEqual(report["source_files_missing"], [])
        self.assertFalse(report["gameplay_verified"])
        self.assertEqual(report["boundaries"], [
            {"missing_source_id": 7, "name": "Missing route",
             "from": [{"source_id": 5, "kind": "connection"}]},
            {"missing_source_id": 9, "name": "Cave 1F",
             "from": [{"source_id": 5, "kind": "transfer"}]}])

    def test_declared_map_without_native_file_is_reported(self):
        (self.source / "Data/Map005.rxdata").unlink()
        self.assertEqual(audit(self.source, self.manifest)["source_files_missing"], [5])

    def test_unimported_source_without_native_file_is_also_reported(self):
        (self.source / "Data/Map009.rxdata").unlink()
        self.assertEqual(audit(self.source, self.manifest)["source_files_missing"], [9])

    def test_debug_map_cannot_count_as_kanto_coverage(self):
        self.manifest["maps"]["1"] = "DEBUG"
        self.assertEqual(audit(self.source, self.manifest)["catalog_ids_outside_kanto"], [1])

    def test_preview_outside_catalog_is_rejected(self):
        self.manifest["preview_only"].append(7)
        with self.assertRaisesRegex(ValueError, "Preview IDs"):
            audit(self.source, self.manifest)


if __name__ == "__main__":
    unittest.main()
