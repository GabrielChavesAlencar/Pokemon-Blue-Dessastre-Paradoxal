"""Native-RMXP-shaped regressions for the HGSS-inspired Johto bedroom.

Tests the real tile-writing and 2F/1F Player Touch event relocation without
running Game.exe or using the private Pokémon tileset or saves.
"""
from __future__ import annotations

import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from server.ruby_marshal import RubyData, RubyObject, loads

# This project loads region scripts from scripts/regions as top-level modules.
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import johto_main_preview as preview
import johto_visual as visual
from build_johto_bedroom_v1 import tile
from build_johto_elm_lab_v1 import table_values
from stage import serialize
from diagnose_johto_bedroom import inspect as inspect_bedroom


def table(w, h=1, z=1, value=0):
    count = w * h * z
    return RubyData("Table", struct.pack("<5I", 3 if z == 3 else 1,
                                         w, h, z, count)
                    + struct.pack("<%dH" % count, *([value] * count)))


def event(name, x, y, destination, trigger=1):
    page = RubyObject("RPG::Event::Page", {
        "@trigger": trigger,
        "@list": [RubyObject("RPG::EventCommand", {
            "@code": 201,
            "@parameters": [0, destination[0], destination[1], destination[2], 2, 0],
        })],
    })
    return RubyObject("RPG::Event", {
        "@name": name.encode("ascii"), "@x": x, "@y": y, "@pages": [page]
    })


def fixtures():
    upstairs = RubyObject("RPG::Map", {
        "@width": 14, "@height": 11, "@tileset_id": 1,
        "@data": table(14, 11, 3),
        "@events": {
            1: event("JH_HOME2F_TO_1F", 9, 8, (675, 11, 8)),
            2: event("JH_NEW_GAME_PROFILE", 6, 7, (674, 6, 7), trigger=3),
        },
    })
    downstairs = RubyObject("RPG::Map", {
        "@width": 16, "@height": 13, "@tileset_id": 1,
        "@data": table(16, 13, 3),
        "@events": {
            1: event("JH_HOME1F_TO_2F", 11, 9, (674, 9, 7)),
        },
    })
    # 24 appended Blue Johto tiles (four furniture + two 3x3 rugs padded).
    tilesets = [None, RubyObject("RPG::Tileset", {
        "@tileset_name": b"BLUE_JOHTO_OPENING_INSIDE",
        "@passages": table(5200),
    })]
    return upstairs, downstairs, tilesets


class BedroomMapTests(unittest.TestCase):
    def test_room_matches_hgss_reference_and_stairs_are_real_warps(self):
        room, home, tilesets = fixtures()
        report = visual.style_bedroom_hgss(room, home, 5176)
        _, cells = table_values(room.attrs["@data"].data, 3)

        def at(x, y, z):
            return cells[x + 14 * (y + 11 * z)]

        self.assertEqual(report["layout"], "hgss-inspired-v1")
        self.assertEqual(at(2, 3, 2), tile(238, 1))  # staircase left
        self.assertEqual(at(2, 6, 2), tile(275, 0))  # lower-left bed
        self.assertEqual(at(7, 1, 2), tile(297, 0))  # top computer
        self.assertEqual(at(11, 2, 2), tile(296, 0))  # top television
        self.assertEqual(at(11, 7, 2), tile(270, 3))  # plant right
        self.assertEqual(at(4, 4, 1), 5179)  # red landing mat
        self.assertEqual(at(6, 6, 1), 5176 + 4 + 4)  # blue rug
        self.assertEqual(at(10, 7, 2), 0)  # old stair tiles cleared
        self.assertEqual((room.attrs["@events"][1].attrs["@x"],
                          room.attrs["@events"][1].attrs["@y"]), (4, 4))
        back = home.attrs["@events"][1].attrs["@pages"][0].attrs["@list"][0]
        self.assertEqual(back.attrs["@parameters"][2:4], [4, 5])
        # The transparent game initializer remains in the old, safe start tile.
        self.assertEqual((room.attrs["@events"][2].attrs["@x"],
                          room.attrs["@events"][2].attrs["@y"]), (6, 7))
        self.assertEqual(loads(serialize(room, preview.johto_qa.EVENT_CLASSES)), room)

    def test_unknown_existing_warp_is_not_silently_rewritten(self):
        room, home, _ = fixtures()
        room.attrs["@events"][1].attrs["@x"] = 1
        with self.assertRaisesRegex(ValueError, "Warps originais"):
            visual.style_bedroom_hgss(room, home, 5176)


class InstalledBedroomTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.game = self.root / "game"
        (self.game / "Data").mkdir(parents=True)
        for folder in ("PBS", "Saves", preview.PLUGIN):
            (self.game / folder).mkdir(parents=True)
        self.write("Game.exe", b"original game.exe")
        self.write("Saves/File A.rxdata", b"untouched save")
        room, home, sets = fixtures()
        self.write("Data/Map674.rxdata", serialize(room, preview.johto_qa.EVENT_CLASSES))
        self.write("Data/Map675.rxdata", serialize(home, preview.johto_qa.EVENT_CLASSES))
        self.write("Data/Tilesets.rxdata", serialize(sets))
        self.write("Data/MapInfos.rxdata", b"world unchanged")
        self.write("PBS/map_connections.txt", b"connections unchanged")
        self.write("PBS/map_metadata_johto_main.txt", b"metadata unchanged")
        self.write(preview.PLUGIN + "/Boot.rb", b"existing boot")
        names = ["Data/Map674.rxdata", "Data/Map675.rxdata",
                 "Data/Tilesets.rxdata", "Data/MapInfos.rxdata",
                 "PBS/map_connections.txt", "PBS/map_metadata_johto_main.txt",
                 preview.PLUGIN + "/Boot.rb"]
        for mid in sorted(preview.PREVIEW_IDS - {674, 675}):
            name = f"Data/Map{mid:03d}.rxdata"
            self.write(name, ("region map " + str(mid)).encode())
            names.append(name)
        self.write(preview.READY, ("BLUE_JOHTO_PRIVATE_PREVIEW_V1,100,"
                     + ",".join(map(str, (*preview.START, *preview.TOWN[:3],
                                           *preview.NPC[:3]))) + "\n").encode())
        proof = {
            "schema": 1, "region": "JOHTO", "status": preview.STATUS,
            "source_bundle_sha256": preview.PINNED_SHA,
            "map_ids": sorted(preview.PREVIEW_IDS),
            "start": list(preview.START), "town": list(preview.TOWN),
            "npc": list(preview.NPC),
            "file_hashes": {name: preview.sha((self.game/name).read_bytes())
                            for name in names},
        }
        self.write(preview.PROOF, preview.raw_json(proof))

    def write(self, name, content):
        path = self.game / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def test_blues_story_updates_only_room_and_staircase_idempotently(self):
        saved = {name: (self.game/name).read_bytes() for name in
                 ("Game.exe", "Saves/File A.rxdata", "Data/Map600.rxdata",
                  "Data/Tilesets.rxdata", "Data/MapInfos.rxdata",
                  "PBS/map_connections.txt")}
        self.assertIsNotNone(preview.preview_proof(self.game))
        report = preview.refresh_installed_bedroom(self.game, self.root)
        self.assertTrue(report["changed"])
        self.assertEqual(report["bedroom_layout"], "hgss-inspired-v1")
        patched = preview.preview_proof(self.game)
        self.assertEqual(patched["bedroom_layout"], "hgss-inspired-v1")
        self.assertEqual(loads((self.game/"Data/Map674.rxdata").read_bytes())
                         .attrs["@events"][1].attrs["@x"], 4)
        self.assertEqual(loads((self.game/"Data/Map675.rxdata").read_bytes())
                         .attrs["@events"][1].attrs["@pages"][0].attrs["@list"][0]
                         .attrs["@parameters"][2:4], [4, 5])
        for name, original in saved.items():
            self.assertEqual((self.game/name).read_bytes(), original)
        self.assertFalse(preview.refresh_installed_bedroom(self.game, self.root)["changed"])
        self.assertTrue((Path(report["backup_folder"]) / preview.PROOF).is_file())

    def test_diagnostic_distinguishes_old_room_from_real_new_map_and_missing_art(self):
        before = inspect_bedroom(self.root,self.game)
        self.assertEqual(before["status"], "OLD_OR_DIFFERENT_BEDROOM")
        self.assertEqual(before["actual_stairs_warp_xy"], [9,8])
        self.assertEqual(before["preview_integrity"], "OK")
        self.assertTrue(before["safe_to_apply"])
        self.preview = preview
        preview.refresh_installed_bedroom(self.game,self.root)
        after = inspect_bedroom(self.root,self.game)
        self.assertEqual(after["status"], "LAYOUT_HGSS_APPLIED")
        self.assertEqual(after["return_xy"], [4,5])
        self.assertEqual(after["private_hgss_status"], "no_private_art")
        self.assertFalse(after["safe_to_apply"])
        self.assertIn("faltam PNGs", after["next_action"])

    def test_manual_repair_accepts_hash_verified_maps_after_global_region_drift(self):
        # Regional integration can update the shared PBS after private Johto
        # was installed. Do not certify the whole game, but allow an explicit
        # backed-up room-only fix when BOTH Johto map hashes are pristine.
        before_pbs = b"PBS changed later by the other regions"
        self.write("PBS/map_connections.txt", before_pbs)
        before = inspect_bedroom(self.root,self.game)
        self.assertEqual(before["status"], "OLD_OR_DIFFERENT_BEDROOM")
        self.assertEqual(before["preview_integrity"], "SCOPED_OK_GLOBAL_FILES_CHANGED")
        self.assertTrue(before["safe_to_apply"])
        report = preview.refresh_installed_bedroom(
            self.game,self.root,allow_global_drift=True)
        self.assertTrue(report["changed"])
        self.assertTrue(report["global_integrity_drift"])
        after = inspect_bedroom(self.root,self.game)
        self.assertEqual(after["status"], "LAYOUT_HGSS_APPLIED")
        self.assertEqual((self.game/"PBS/map_connections.txt").read_bytes(),before_pbs)
        self.assertEqual((self.game/"Saves/File A.rxdata").read_bytes(),
                         b"untouched save")
        self.assertEqual(after["preview_integrity"], "SCOPED_OK_GLOBAL_FILES_CHANGED")
        self.assertFalse(after["safe_to_apply"])

    def test_diagnostic_rejects_unverified_modified_room(self):
        self.write("Data/Map674.rxdata", b"modified native map")
        result = inspect_bedroom(self.root,self.game)
        self.assertEqual(result["status"], "MAP_READ_ERROR")
        self.assertEqual(result["preview_integrity"], "FAILED")
        self.assertFalse(result["safe_to_apply"])

    def test_failure_while_swapping_restores_both_maps_and_manifest(self):
        original = {name: (self.game/name).read_bytes() for name in
                    ("Data/Map674.rxdata", "Data/Map675.rxdata", preview.PROOF)}
        replace = preview.os.replace
        calls = 0

        def fail(source, destination):
            nonlocal calls
            calls += 1
            if calls == 3:
                raise OSError("simulated interrupted layout update")
            return replace(source, destination)

        with patch.object(preview.os, "replace", side_effect=fail):
            with self.assertRaisesRegex(OSError, "interrupted"):
                preview.refresh_installed_bedroom(self.game, self.root)
        for name, blob in original.items():
            self.assertEqual((self.game/name).read_bytes(), blob)
        self.assertIsNotNone(preview.preview_proof(self.game))

    def test_changed_map_is_rejected_and_left_untouched(self):
        self.write("Data/Map674.rxdata", b"changed by external editor")
        before = (self.game/"Data/Map674.rxdata").read_bytes()
        with self.assertRaises(ValueError):
            preview.refresh_installed_bedroom(self.game, self.root)
        self.assertEqual((self.game/"Data/Map674.rxdata").read_bytes(), before)
        self.assertEqual((self.game/"Saves/File A.rxdata").read_bytes(),
                         b"untouched save")


if __name__ == "__main__":
    unittest.main()
