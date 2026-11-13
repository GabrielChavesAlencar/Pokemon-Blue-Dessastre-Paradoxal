"""No-source-required regression for the isolated, read-only Johto map auditor.

These tests create tiny artificial RMXP data; no copyrighted maps or saves.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    import audit_johto
    from stage import serialize
    from server.ruby_marshal import RubyObject
finally:
    sys.path.remove(str(ROOT / "scripts/regions"))


class JohtoSourceAuditTests(unittest.TestCase):
    @staticmethod
    def make_fixture(base: Path, *, event=True) -> Path:
        source = base / ".blue-work/johto-source"
        data = source / "Data"
        data.mkdir(parents=True)
        info = {1: RubyObject("RPG::MapInfo", {
            "@name": b"New Bark Town", "@parent_id": 0})}
        tiles = [None, RubyObject("RPG::Tileset", {})]
        events = {}
        if event:
            commands = [
                RubyObject("RPG::EventCommand", {
                    "@code": 201, "@parameters": [0, 2, 1, 1, 2, 0]
                }),
                RubyObject("RPG::EventCommand", {
                    "@code": 355, "@parameters": [b"Kernel.system('nope')"]
                })
            ]
            events = {1: RubyObject("RPG::Event", {
                "@pages": [RubyObject("RPG::Event::Page", {"@list": commands})]
            })}
        stage_extras = ("RPG::Event", "RPG::Event::Page", "RPG::EventCommand")
        data.joinpath("MapInfos.rxdata").write_bytes(serialize(info))
        data.joinpath("Tilesets.rxdata").write_bytes(serialize(tiles))
        data.joinpath("Map001.rxdata").write_bytes(serialize(RubyObject(
            "RPG::Map", {"@width": 20, "@height": 18,
                         "@tileset_id": 1, "@events": events}), stage_extras))
        return source

    def test_manifest_cannot_enable_johto_by_itself(self):
        manifest = json.loads((ROOT / "data/regions/johto-source.json").read_text("utf-8"))
        self.assertEqual(manifest["region"], "JOHTO")
        self.assertFalse(manifest["import_enabled"])
        self.assertTrue(manifest["mapping_verified"])
        self.assertEqual(manifest["source"]["archive_sha256"],
                         "5d5697e9c3bf5db6ca7039d4af65697dd8b231f4b1305f14731e35ac324b6715")
        self.assertEqual(len(manifest["maps"]), 74)
        self.assertEqual(manifest["maps"]["79"], "JOHTO_NEW_BARK_TOWN")
        self.assertEqual(manifest["maps"]["104"], "JOHTO_ROUTE_29")
        self.assertEqual(manifest["maps"]["102"], "JOHTO_MT_SILVER")
        self.assertEqual(manifest["source"]["accepted_missing_mapinfo_ids"], [1])
        self.assertFalse(manifest["source"]["distribution_approved"])

    def test_inert_reader_detects_maps_scripts_missing_transfers_and_does_not_modify_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_fixture(root)
            source_map = source / "Data/Map001.rxdata"
            original = hashlib.sha256(source_map.read_bytes()).hexdigest()
            report = audit_johto.audit(
                source, ROOT / "data/regions/johto-source.json")
            self.assertEqual(report["mode"], "READ_ONLY_NO_INSTALL")
            self.assertEqual(report["map_count"], 1)
            self.assertFalse(report["can_install"])
            self.assertFalse(report["archive_hash_pinned_and_verified"])
            self.assertEqual(report["maps"][0]["width"], 20)
            self.assertEqual(report["named_area_candidates"]["New Bark"], [1])
            self.assertEqual(report["unresolved_transfer_ids"], [2])
            self.assertEqual(report["untrusted_script_commands"], 1)
            self.assertEqual(hashlib.sha256(source_map.read_bytes()).hexdigest(), original)
            with patch.object(audit_johto, "ROOT", root):
                output = root / ".blue-work/report.json"
                audit_johto.write_report(output, report)
                audit_johto.write_report(output, report)  # idempotent
                self.assertEqual(json.loads(output.read_text("utf-8"))["map_count"], 1)
                with self.assertRaises(FileExistsError):
                    audit_johto.write_report(output, {**report, "map_count": 999})
                with self.assertRaisesRegex(ValueError, "inside .blue-work"):
                    audit_johto.write_report(root / "game/Data/Map001.rxdata", report)

    def test_game_snapshot_is_read_only_and_reports_colliding_source_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.make_fixture(root, event=False)
            game = root / "game"
            data = game / "Data"
            data.mkdir(parents=True)
            # The main Blue game is read as hashes; its source may differ.
            data.joinpath("Map001.rxdata").write_bytes(b"private saved map")
            data.joinpath("System.rxdata").write_bytes(b"protected")
            report = audit_johto.audit(
                source, ROOT / "data/regions/johto-source.json", game=game)
            self.assertEqual(report["map_id_overlap_before_remapping"], [1])
            self.assertEqual(report["game"]["protected_hashes"]["Data/System.rxdata"],
                             hashlib.sha256(b"protected").hexdigest())
            self.assertEqual(data.joinpath("Map001.rxdata").read_bytes(),
                             b"private saved map")
            self.assertFalse(report["can_install"])

    def test_bad_map_rejected_without_touching_johto_or_decades(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = self.make_fixture(Path(tmp))
            source.joinpath("Data/Map001.rxdata").write_bytes(b"bad payload")
            with self.assertRaises(ValueError):
                audit_johto.audit(source, ROOT / "data/regions/johto-source.json")

    def test_missing_source_is_explicitly_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / ".blue-work/johto-source"
            with self.assertRaises((FileNotFoundError, ValueError)):
                audit_johto.audit(source, ROOT / "data/regions/johto-source.json")


if __name__ == "__main__":
    unittest.main()
