"""Private HGSS tilesheets: genuine source tiles, Johto-only scope, secure atlases."""
from __future__ import annotations
import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from build_johto_elm_lab_v1 import encode_png, table_values
from johto_hgss_assets import (INTERIORS, compile_private_art, map_kind,
                                private_sources, FOLDER)
from server.ruby_marshal import RubyData, RubyObject, loads
from stage import serialize
from build_johto_events import EVENT_CLASSES


def table(count, *, w=None, h=1, z=1):
    w = w or count
    dim = 3 if z == 3 else 1
    return RubyData("Table", struct.pack("<5I", dim,w,h,z,count) + b"\0\0"*count)


def rgba_png(width, height, color=(44, 125, 214, 255)):
    return encode_png(width, [bytes(color)*(width) for _ in range(height)])


def map_fixture(mid, w=14, h=11):
    return RubyObject("RPG::Map", {
        "@width": w, "@height": h, "@tileset_id": 1,
        "@data": table(w*h*3, w=w, h=h, z=3),
        "@events": {
            1: RubyObject("RPG::Event", {"@x":6,"@y":7, "@name":b"SAFETY_EVENT"})
        } if mid == 674 else {}
    })


class JohtoHgssAssetsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.folder = self.root / FOLDER
        self.folder.mkdir(parents=True)
        self.inside = rgba_png(256, 64, (70, 60, 45, 255))
        self.donor = rgba_png(32, 32, (4, 60, 220, 255))
        (self.folder / "Akizakura16_Indoor.png").write_bytes(self.donor)
        self.set_manifest([
            {"map":674,"source":"akizakura16", "sheet_col":0,
             "sheet_row":0,"x":5,"y":5,"layer":0,"passable":True},
            {"map":681,"source":"akizakura16", "sheet_col":0,
             "sheet_row":0,"x":6,"y":6,"layer":2,"passable":False},
        ])
        self.base_set = RubyObject("RPG::Tileset", {
            "@tileset_name": b"Inside",
            "@name": b"Inside", "@id":1,
            "@autotile_names": [b""] * 7,
            "@passages": table(400), "@priorities": table(400),
            "@terrain_tags": table(400),
        })
        self.maps = {674:map_fixture(674), 681:map_fixture(681)}
        self.tilesets = [None,self.base_set]

    def set_manifest(self, placements):
        data = {"schema":1,"sources":{"akizakura16":{
            "filename":"Akizakura16_Indoor.png",
            "sha256":hashlib.sha256(self.donor).hexdigest(),
            "tile_px":32,"credit":"Akizakura16"
        }},"placements":placements}
        (self.folder/"manifest.json").write_text(json.dumps(data),encoding="utf8")

    def read_graphic(self, folder, name):
        self.assertEqual((folder, name), ("Tilesets","Inside"))
        return self.inside

    def test_private_real_pixels_are_appended_and_only_johto_maps_referenced(self):
        added = {}
        report = compile_private_art(self.maps,self.tilesets,added,self.read_graphic,self.root)
        self.assertEqual(report["status"],"private_art_compiled")
        self.assertEqual(report["maps"],[674,681])
        self.assertEqual(report["credits"],["Akizakura16"])
        self.assertEqual(len(added),1)
        self.assertTrue(next(iter(added.values())).startswith(b"\x89PNG"))
        self.assertEqual(self.maps[674].attrs["@tileset_id"],2)
        self.assertEqual(self.maps[681].attrs["@tileset_id"],2)
        self.assertEqual(len(self.tilesets),3)
        _, cells = table_values(self.maps[674].attrs["@data"].data, 3)
        self.assertEqual(cells[5+14*5],400)
        _, cells = table_values(self.maps[681].attrs["@data"].data, 3)
        self.assertEqual(cells[6+14*(6+11*2)],401)
        self.assertEqual(loads(serialize(self.maps[674], EVENT_CLASSES)),self.maps[674])

    def test_blocking_tile_cannot_cover_spawn_or_event(self):
        self.set_manifest([{"map":674,"source":"akizakura16", "sheet_col":0,
             "sheet_row":0,"x":6,"y":7,"layer":2,"passable":False}])
        with self.assertRaisesRegex(ValueError,"bloqueia evento/spawn"):
            compile_private_art(self.maps,self.tilesets,{},self.read_graphic,self.root)

    def test_wrong_hash_or_unknown_id_fails_without_writes(self):
        (self.folder/"Akizakura16_Indoor.png").write_bytes(b"broken")
        with self.assertRaisesRegex(ValueError,"Checksum"):
            compile_private_art(self.maps,self.tilesets,{},self.read_graphic,self.root)
        self.assertEqual(len(self.tilesets),2)
        self.assertEqual(self.maps[674].attrs["@tileset_id"],1)

    def test_no_assets_keeps_originals_untouched(self):
        (self.folder/"manifest.json").unlink()
        before = serialize(self.maps[674], EVENT_CLASSES)
        result = compile_private_art(self.maps,self.tilesets,{},self.read_graphic,self.root)
        self.assertEqual(result["status"],"no_private_art")
        self.assertEqual(before,serialize(self.maps[674], EVENT_CLASSES))

    def test_interior_scopes_exclude_hoenn_ids(self):
        self.assertEqual(min(INTERIORS),674)
        self.assertEqual(max(INTERIORS),699)
        self.assertEqual(map_kind(674),"bedroom")
        self.assertEqual(map_kind(676),"lab")
        self.assertEqual(map_kind(684),"center")
        self.assertEqual(map_kind(685),"mart")
        self.assertEqual(map_kind(693),"house")
        self.assertIsNone(map_kind(702))


if __name__ == "__main__":
    unittest.main()
