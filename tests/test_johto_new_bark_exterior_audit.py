"""New Bark v1: verified source-map tile snapshots, NOT verified game doors."""
from __future__ import annotations

import copy
import hashlib
import json
import struct
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from audit_johto_new_bark_exterior import compile_audit, publish
    from stage import serialize
    from server.ruby_marshal import RubyObject, RubyData
finally:
    sys.path.pop(0)


def make_fixture(root):
    spec = json.loads((ROOT / "data/regions/johto-new-bark-exterior-v1.json")
                      .read_text("utf-8"))
    w, h = 22, 48
    count = w * h * 3
    table = [0] * count
    for point in spec["entrances"]:
        x, y = point["x"], point["y"]
        for z in range(3):
            table[z * w * h + y * w + x] = point["expected_door_tiles"][z]
            table[z * w * h + (y+1) * w + x] = point["expected_south_tile"][z]
    table_blob = struct.pack("<5I", 3, w, h, 3, count) + struct.pack(
        "<" + str(count) + "H", *table)
    world = RubyObject("RPG::Map", {"@width":w, "@height":h, "@tileset_id":1,
                                   "@data":RubyData("Table", table_blob), "@events":{}})
    flags = struct.pack("<5I",1,2800,1,1,2800) + b"\0\0" * 2800
    tiles = [None, RubyObject("RPG::Tileset", {
        "@passages":RubyData("Table",flags),
        "@priorities":RubyData("Table",flags)})]
    original = serialize(world)
    tileset_bytes = serialize(tiles)
    archive = root / ".blue-work/johto-source/original.zip"
    archive.parent.mkdir(parents=True)
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED) as zipped:
        zipped.writestr("user-pack/Data/Map079.rxdata", original)
        zipped.writestr("user-pack/Data/Tilesets.rxdata", tileset_bytes)
    spec["map"]["source_sha256"] = hashlib.sha256(original).hexdigest()
    spec["map"]["tileset_id"] = 1
    spec["tilesets_source_sha256"] = hashlib.sha256(tileset_bytes).hexdigest()
    spec["source_archive_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
    return spec, archive


class JohtoExteriorAuditTests(unittest.TestCase):
    def test_real_canonical_v1_id_hash_and_four_unverified_entrances(self):
        spec = json.loads((ROOT / "data/regions/johto-new-bark-exterior-v1.json")
                          .read_text("utf-8"))
        self.assertEqual(spec["map"]["source_id"],79)
        self.assertEqual((spec["map"]["width"],spec["map"]["height"]), (22,48))
        self.assertEqual(spec["map"]["source_sha256"],
                         "e5ffa3a8831101eca319b2567ebc3f6cff22ac673072776a31bf69fceaefc9c9")
        self.assertEqual([(c["x"],c["y"]) for c in spec["entrances"]],
                         [(5,21),(14,23),(4,31),(13,33)])
        self.assertFalse(spec["can_install"])
        self.assertFalse(spec["can_use_for_warps"])
        self.assertFalse(spec["all_door_identifications_verified"])
        self.assertTrue(all(c["verified_position"] is False for c in spec["entrances"]))

    def test_compiles_four_source_tile_checks_without_claiming_gameplay(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            spec, archive=make_fixture(root)
            outcome=compile_audit(archive,spec,root=root)
            self.assertEqual(outcome["status"],
                             "REAL_EXTERIOR_TILES_VERIFIED_DOORS_NOT_PLAYABLE")
            self.assertEqual(outcome["candidates_checked"],4)
            self.assertFalse(outcome["can_install"])
            self.assertFalse(outcome["gameplay_playable"])
            self.assertFalse(outcome["gameplay_tested"])
            self.assertTrue(all(c["source_tiles_confirmed"]
                                for c in outcome["candidates"]))
            self.assertTrue(all(not c["door_identification_verified"]
                                and not c["passability_tested_in_engine"]
                                for c in outcome["candidates"]))
            dest=root / ".blue-work/new-bark-audit.json"
            publish(outcome,dest,root=root)
            self.assertEqual(json.loads(dest.read_text("utf-8"))["candidates_checked"],4)
            with self.assertRaisesRegex(ValueError,"NOVO"):
                publish(outcome,dest,root=root)
            self.assertFalse((root/"game").exists())

    def test_hash_or_tile_id_or_premature_approval_blocks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            spec, archive=make_fixture(root)
            wrong=copy.deepcopy(spec)
            wrong["map"]["source_sha256"]="0"*64
            with self.assertRaisesRegex(ValueError,"mudou"):
                compile_audit(archive,wrong,root=root)
            wrong=copy.deepcopy(spec)
            wrong["entrances"][0]["expected_door_tiles"]=[456,0,0]
            with self.assertRaisesRegex(ValueError,"Tiles de fachada"):
                compile_audit(archive,wrong,root=root)
            wrong=copy.deepcopy(spec)
            wrong["entrances"][0]["verified_position"]=True
            with self.assertRaisesRegex(ValueError,"ja aprovada"):
                compile_audit(archive,wrong,root=root)
            wrong=copy.deepcopy(spec)
            wrong["can_install"]=True
            with self.assertRaisesRegex(ValueError,"sem aprovar"):
                compile_audit(archive,wrong,root=root)
            outside=root / "game/NewBark.json"
            with self.assertRaisesRegex(ValueError,"NOVO"):
                publish({},outside,root=root)

    def test_missing_game_is_not_an_assumption_that_game_is_playable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            spec, archive=make_fixture(root)
            result=compile_audit(archive,spec,root=root)
            self.assertTrue(result["candidates"])
            self.assertFalse((root/"game/Data/MapInfos.rxdata").exists())
            self.assertEqual(result["status"],
                             "REAL_EXTERIOR_TILES_VERIFIED_DOORS_NOT_PLAYABLE")


if __name__ == "__main__":
    unittest.main()
