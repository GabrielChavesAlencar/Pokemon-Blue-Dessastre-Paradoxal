"""Windows native-map recompilation is not the same as Johto missing.

Replay the integrated workflow with 100 valid Ruby Marshal maps, a changed
Map600 after Game.exe, installed Johto's original proof and no private ZIP.
Only the two New Bark maps may be patched; Kanto/Hoenn and saves stay intact.
"""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "regions"))
from server.ruby_marshal import RubyObject
from stage import serialize
from test_johto_bedroom_hgss import fixtures, table
import johto_main_preview as preview
import auto_integrate_johto


class JohtoRuntimePreviewTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.game = self.root / "game"
        for folder in ("Data", "Saves", "PBS", preview.PLUGIN):
            (self.game / folder).mkdir(parents=True, exist_ok=True)
        (self.root / ".blue-work").mkdir()
        self.write("Game.exe", b"existing game executable")
        self.write("Saves/File A.rxdata", b"existing user save")
        self.write("Data/Map410.rxdata", b"existing Kanto")
        self.write("Data/Map701.rxdata", b"existing Hoenn")
        self.write(preview.PLUGIN + "/Boot.rb", b"safe compiled Johto boot")
        self.write("PBS/map_metadata_johto_main.txt", b"[674]\n")
        self.write("PBS/map_connections.txt", b"regional connections")
        room, home, sets = fixtures()
        self.write("Data/Tilesets.rxdata", serialize(sets))
        infos = {}
        for mid in preview.PREVIEW_IDS:
            infos[mid] = RubyObject("RPG::MapInfo", {
                "@name": ("[Johto] " + str(mid)).encode("ascii"),
                "@parent_id": 0, "@order": mid})
            if mid == 674: obj = room
            elif mid == 675: obj = home
            else:
                obj = RubyObject("RPG::Map", {
                    "@width": 14, "@height": 11, "@tileset_id":1,
                    "@data": table(14,11,3),
                    "@events": {} })
            self.write(f"Data/Map{mid:03}.rxdata",
                       serialize(obj, preview.johto_qa.EVENT_CLASSES))
        self.write("Data/MapInfos.rxdata", serialize(infos))
        self.write(preview.READY, ("BLUE_JOHTO_PRIVATE_PREVIEW_V1,100," +
            ",".join(map(str, (*preview.START, *preview.TOWN[:3],
                               *preview.NPC[:3])))+"\n").encode("ascii"))
        names = [f"Data/Map{i:03}.rxdata" for i in sorted(preview.PREVIEW_IDS)]
        names += ["Data/Tilesets.rxdata","Data/MapInfos.rxdata",
                  "PBS/map_connections.txt","PBS/map_metadata_johto_main.txt",
                  preview.PLUGIN+"/Boot.rb"]
        proof = {"schema":1,"region":"JOHTO","status":preview.STATUS,
                 "source_bundle_sha256":preview.PINNED_SHA,
                 "map_ids":sorted(preview.PREVIEW_IDS),
                 "start":list(preview.START),"town":list(preview.TOWN),
                 "npc":list(preview.NPC),"file_hashes":{
                     name:preview.sha((self.game/name).read_bytes()) for name in names
                 }}
        self.write(preview.PROOF,preview.raw_json(proof))

    def write(self, relative, data):
        p=self.game/relative
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(data)

    def test_runtime_modified_map_detected_and_blue_story_keeps_johto_available(self):
        # Game.exe added a harmless real event to Map600 after installation.
        p=self.game/"Data/Map600.rxdata"
        modified=bytearray(p.read_bytes())
        # Use a legal RMXP edit, not arbitrary corruption.
        from server.ruby_marshal import loads
        map600=loads(bytes(modified))
        map600.attrs["@bgm"] = RubyObject("RPG::AudioFile", {
            "@name": b"104 New Bark Town", "@volume": 80,"@pitch":100})
        p.write_bytes(serialize(map600,preview.johto_qa.EVENT_CLASSES))
        original={x:(self.game/x).read_bytes() for x in (
            "Saves/File A.rxdata","Data/Map410.rxdata","Data/Map701.rxdata",
            "Data/Map600.rxdata", "Data/MapInfos.rxdata","Data/Tilesets.rxdata")}
        with self.assertRaisesRegex(ValueError,"Map600.rxdata"):
            preview.preview_proof(self.game)
        before=preview.runtime_semantic_preview(self.game)
        self.assertEqual(before["changed_map_ids"], [600])
        report=auto_integrate_johto.integrate(self.root,self.game)
        self.assertEqual(report["status"],
                         "experimental_installed_runtime_modified_not_native_tested")
        self.assertTrue(report["ready"])
        self.assertTrue(report["bedroom_changed"])
        self.assertFalse(report["native_qa"])
        self.assertEqual(report["runtime_modified_map_ids"], [600])
        after=preview.runtime_semantic_preview(self.game)
        self.assertEqual(after["changed_map_ids"], [600])
        self.assertEqual(serialize(loads((self.game/"Data/Map674.rxdata").read_bytes()),
                                   preview.johto_qa.EVENT_CLASSES),
                         (self.game/"Data/Map674.rxdata").read_bytes())
        for x,raw in original.items():
            self.assertEqual((self.game/x).read_bytes(),raw)

    def test_corrupt_map_rejected_without_touching_saves(self):
        self.write("Data/Map600.rxdata", b"INVALID")
        original=self.game.joinpath("Data/Map674.rxdata").read_bytes()
        report=auto_integrate_johto.integrate(self.root,self.game)
        self.assertEqual(report["status"],"existing_install_needs_review")
        self.assertFalse(report["ready"])
        self.assertEqual((self.game/"Data/Map674.rxdata").read_bytes(),original)
        self.assertEqual((self.game/"Saves/File A.rxdata").read_bytes(),
                         b"existing user save")


if __name__ == "__main__":
    unittest.main()
