"""Diagnostic ZIP exporter: never ship saves, only Map600/674/675 + details."""
from __future__ import annotations

import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "regions"))
from server.ruby_marshal import RubyData, RubyObject
from stage import serialize
from build_johto_events import EVENT_CLASSES
from export_johto_map_diagnostics import bundle, event_summary


def room(map_id: int):
    data = RubyData("Table",
        struct.pack("<5I", 3, 14, 11, 3, 14*11*3) + b"\0\0" * (14*11*3))
    command = RubyObject("RPG::EventCommand",
        {"@code":355,"@parameters":[b"pbTransferPlayer(674,9,7)"]})
    page = RubyObject("RPG::Event::Page",
        {"@trigger":1,"@list":[command]})
    event = RubyObject("RPG::Event",
        {"@name":b"JH_HOME1F_TO_2F", "@x":11, "@y":9,
         "@id":1, "@pages":[page]})
    return serialize(RubyObject("RPG::Map", {
        "@width":14,"@height":11,"@tileset_id":1,"@data":data,
        "@events":{1:event} if map_id==675 else {}
    }),EVENT_CLASSES)


class DiagnosticExporterTests(unittest.TestCase):
    def test_bundle_exports_only_three_map_data_files_and_omits_saves(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            game=root/"game"
            (game/"Data").mkdir(parents=True)
            (game/"Saves").mkdir()
            (root/".blue-work").mkdir()
            (game/"Game.exe").write_bytes(b"test launcher")
            (game/"Saves/File A.rxdata").write_bytes(b"PERSONAL SAVE DO NOT EXPORT")
            for mid in (600,674,675):
                (game/f"Data/Map{mid:03}.rxdata").write_bytes(room(mid))
            zip_path=root/".blue-work/JOHTO_DIAGNOSTICO_MAPAS.zip"
            result=bundle(root,game,zip_path)
            self.assertFalse(result["contains_saves"])
            self.assertTrue(zip_path.exists())
            with zipfile.ZipFile(zip_path) as output:
                names=set(output.namelist())
                self.assertEqual(names,{
                    "Data/Map600.rxdata","Data/Map674.rxdata","Data/Map675.rxdata",
                    "DIAGNOSTICO_JOHTO.json","LEIA-ME.txt"})
                self.assertFalse(any("save" in name.lower() for name in names))
                data=json.loads(output.read("DIAGNOSTICO_JOHTO.json"))
                self.assertEqual(data["diagnostic"]["game_found"],True)
                self.assertTrue(data["events"]["Data/Map675.rxdata"]["events"])
                self.assertEqual(data["events"]["Data/Map675.rxdata"]["events"][0]
                                 ["pages"][0]["commands"][0]["code"],355)
                self.assertNotIn(b"PERSONAL SAVE DO NOT EXPORT",output.read("Data/Map674.rxdata"))
            second = bundle(root,game,zip_path)
            self.assertNotEqual(second["zip"], str(zip_path))
            self.assertTrue(Path(second["zip"]).is_file())
            self.assertIn("(1).zip", second["zip"])
            self.assertTrue(zip_path.is_file())  # original intact

    def test_missing_johto_maps_can_be_reported_repeatedly_without_saves(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            game=root/"game"
            game.mkdir()
            (root/".blue-work").mkdir()
            (game/"Game.exe").write_bytes(b"test")
            output=root/".blue-work/JOHTO_DIAGNOSTICO_MAPAS.zip"
            first=bundle(root,game,output)
            second=bundle(root,game,output)
            self.assertEqual(first["maps"],[])
            self.assertEqual(len(first["missing_maps"]),3)
            self.assertTrue(Path(second["zip"]).exists())
            self.assertNotEqual(first["zip"],second["zip"])
            with zipfile.ZipFile(second["zip"]) as archive:
                self.assertEqual(set(archive.namelist()),{
                    "DIAGNOSTICO_JOHTO.json","LEIA-ME.txt"})
                data=json.loads(archive.read("DIAGNOSTICO_JOHTO.json"))
                self.assertTrue(data["files"]["Data/Map674.rxdata"]["missing"])

    def test_bundle_cannot_be_written_into_game_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"game").mkdir()
            (root/"game/Game.exe").write_bytes(b"test")
            with self.assertRaisesRegex(ValueError,"dentro de .blue-work"):
                bundle(root,root/"game",root/"game/bad.zip")


if __name__ == "__main__":
    unittest.main()
