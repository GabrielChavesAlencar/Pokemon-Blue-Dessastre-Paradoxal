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




class ExistingGamePrivateHgssTests(JohtoHgssAssetsTests):
    """The actual incremental updater must not edit other regions or saves."""

    def setUp(self):
        super().setUp()
        import johto_main_preview as preview
        from build_johto_events import EVENT_CLASSES
        self.preview = preview
        self.game = self.root / "game"
        for name in ("Data", "Saves", "PBS", "Graphics/Tilesets", preview.PLUGIN):
            (self.game / name).mkdir(parents=True, exist_ok=True)
        self.write("Game.exe", b"the unchanged user executable")
        self.write("Saves/File A.rxdata", b"the unchanged user save")
        self.write("Data/Map410.rxdata", b"the unchanged Kanto map")
        self.write("Data/Map702.rxdata", b"the unchanged Hoenn map")
        self.write("Graphics/Tilesets/Inside.png", self.inside)
        self.write("Data/Tilesets.rxdata", serialize(self.tilesets))
        self.write("Data/MapInfos.rxdata", b"the original regional registry")
        self.write("PBS/map_connections.txt", b"the original region connections")
        self.write("PBS/map_metadata_johto_main.txt", b"Johto metadata")
        self.write(preview.PLUGIN + "/Boot.rb", b"original boot")
        names = ["Data/Tilesets.rxdata", "Data/MapInfos.rxdata",
                 "PBS/map_connections.txt","PBS/map_metadata_johto_main.txt",
                 preview.PLUGIN + "/Boot.rb"]
        for mid in sorted(preview.PREVIEW_IDS):
            name = f"Data/Map{mid:03}.rxdata"
            if mid in INTERIORS:
                self.write(name, serialize(map_fixture(mid), EVENT_CLASSES))
            else:
                self.write(name, ("unchanged Johto map " + str(mid)).encode())
            names.append(name)
        self.write(preview.READY, (
            "BLUE_JOHTO_PRIVATE_PREVIEW_V1,100," +
            ",".join(map(str, (*preview.START, *preview.TOWN[:3], *preview.NPC[:3]))) +
            "\n").encode("ascii"))
        proof = {
            "schema":1, "region":"JOHTO","status":preview.STATUS,
            "source_bundle_sha256":preview.PINNED_SHA,
            "map_ids":sorted(preview.PREVIEW_IDS), "start":list(preview.START),
            "town":list(preview.TOWN), "npc":list(preview.NPC),
            "private_hgss":{"status":"no_private_art","maps":[]},
            "file_hashes": {name:preview.sha((self.game/name).read_bytes())
                            for name in names}
        }
        self.write(preview.PROOF,preview.raw_json(proof))

    def write(self, name, blob):
        path = self.game / name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(blob)

    def test_original_maps_and_save_survive_upgrade_and_reinstall_is_noop(self):
        protected = ["Game.exe","Saves/File A.rxdata","Data/Map410.rxdata",
                     "Data/Map702.rxdata","Data/MapInfos.rxdata",
                     "PBS/map_connections.txt","Data/Map600.rxdata"]
        before = {x:(self.game/x).read_bytes() for x in protected}
        self.assertIsNotNone(self.preview.preview_proof(self.game))
        result = self.preview.refresh_installed_private_hgss(self.game,self.root)
        self.assertTrue(result["changed"])
        self.assertEqual(result["maps"],[674,681])
        self.assertTrue(self.preview.preview_proof(self.game)["private_hgss"]
                        ["status"] == "private_art_compiled")
        for path in protected:
            self.assertEqual((self.game/path).read_bytes(), before[path])
        self.assertEqual(self.preview.refresh_installed_private_hgss(self.game,self.root)
                         ["changed"],False)

    def test_mid_commit_error_rolls_back_all_art_and_maps(self):
        from unittest.mock import patch
        before = {name:(self.game/name).read_bytes() for name in
                  ["Data/Map674.rxdata","Data/Map681.rxdata",
                   "Data/Tilesets.rxdata", self.preview.PROOF,
                   "Saves/File A.rxdata"]}
        original = self.preview.os.replace
        count = 0

        def fail_on_third(source,destination):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError("HGSS simulated interrupted write")
            return original(source,destination)

        with patch.object(self.preview.os,"replace",side_effect=fail_on_third):
            with self.assertRaisesRegex(OSError,"interrupted"):
                self.preview.refresh_installed_private_hgss(self.game,self.root)
        for name, data in before.items():
            self.assertEqual((self.game/name).read_bytes(),data)
        self.assertIsNotNone(self.preview.preview_proof(self.game))
        self.assertFalse(list((self.game/"Graphics/Tilesets").glob("BLUE_JOHTO_HGSS_PRIVATE_*")))


if __name__ == "__main__":
    unittest.main()
