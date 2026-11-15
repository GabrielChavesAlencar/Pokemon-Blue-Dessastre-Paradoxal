"""Hoenn QA teleport source geometry: 199 tested map stops, never guessed."""
from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts/regions"))

from pilot_hoenn import SOURCE_MAPS, build_test_stops, open_tile, serialize_test_stops
from hoenn_qa_teleport_upgrade import COMPILE_REQUEST, PLUGIN, ensure_test_tools, prepare_updates
from server.ruby_marshal import RubyData, RubyObject


class TeleportSourceTests(unittest.TestCase):
    def setUp(self):
        self.maps={}
        self.tiles={}
        self.ids={old:700+i for i,old in enumerate(SOURCE_MAPS)}
        for old in SOURCE_MAPS:
            event=SimpleNamespace(attrs={"@x":4,"@y":4})
            self.maps[old]=SimpleNamespace(attrs={
                "@width":9,"@height":9,"@events":{1:event},
            })
            self.tiles[old]=object()

    @staticmethod
    def open_ground(_map,_tiles,x,y):
        return 0 <= x < 9 and 0 <= y < 9 and (x,y) != (3,3)

    def test_builds_all_199_stops_away_from_NPC_and_blocked_tiles(self):
        with patch("pilot_hoenn.open_tile",side_effect=self.open_ground):
            stops=build_test_stops(self.maps,self.tiles,self.ids)
        self.assertEqual(len(stops),199)
        self.assertEqual({row[0] for row in stops},set(SOURCE_MAPS))
        for old,native,x,y,direction,name in stops:
            self.assertEqual(native,self.ids[old])
            self.assertNotEqual((x,y),(4,4))
            self.assertNotEqual((x,y),(3,3))
            self.assertTrue(1<=x<=7 and 1<=y<=7)
            self.assertEqual(direction,2)
            self.assertTrue(name)
            self.assertNotIn("|",name)
        payload=serialize_test_stops(stops)
        lines=payload.decode("utf-8").splitlines()
        self.assertEqual(lines[0],"BLUE_HOENN_TEST_STOPS_V1")
        self.assertEqual(len(lines),200)
        self.assertEqual(lines[-1].split("|")[0],str(max(SOURCE_MAPS)))

    def test_refuses_missing_map_and_no_safe_tile(self):
        incomplete=dict(self.maps)
        incomplete.pop(next(iter(incomplete)))
        with self.assertRaisesRegex(ValueError,"199"):
            build_test_stops(incomplete,self.tiles,self.ids)
        with patch("pilot_hoenn.open_tile",return_value=False):
            with self.assertRaisesRegex(ValueError,"sem célula"):
                build_test_stops(self.maps,self.tiles,self.ids)

    def test_upgrader_refuses_foreign_or_unscoped_copies(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temporary:
            outside = Path(temporary)
            with self.assertRaisesRegex(ValueError, ".blue-work"):
                prepare_updates(outside, outside)
            with self.assertRaisesRegex(ValueError, ".blue-work"):
                ensure_test_tools(outside, outside)
        with self.assertRaisesRegex(ValueError, "Fase12"):
            prepare_updates(ROOT / ".blue-work/hoenn-qa-fase10", ROOT / "game")

    def test_refreshing_the_pilot_script_schedules_native_recompilation(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy = root / "hoenn-qa-fase12"
            installed = copy / PLUGIN
            installed.parent.mkdir(parents=True)
            installed.write_bytes(b"old plugin")
            observed = {PLUGIN: b"hoenn map display fix"}
            with patch("hoenn_qa_teleport_upgrade.ROOT", root), \
                 patch("hoenn_qa_teleport_upgrade.require_private_path", side_effect=lambda path: path), \
                 patch("hoenn_qa_teleport_upgrade.prepare_updates", side_effect=lambda *_: observed.copy()):
                result = ensure_test_tools(copy, root / "game")
                self.assertEqual(result["files_updated"], 2)
                self.assertEqual(installed.read_bytes(), observed[PLUGIN])
                request = copy / COMPILE_REQUEST
                self.assertTrue(request.is_file())
                request.unlink()  # The successful native compiler clears the request.
                self.assertEqual(ensure_test_tools(copy, root / "game")["files_updated"], 0)
                self.assertFalse(request.exists())

    def test_all_199_stops_required_for_serialization(self):
        with self.assertRaisesRegex(ValueError,"incompleto"):
            serialize_test_stops([(7,700,8,8,2,"Littleroot")])
        with self.assertRaisesRegex(ValueError,"incompleto"):
            serialize_test_stops([(7,700,8,8,2,"Littleroot")]*199)

    def test_loading_a_new_map_with_reused_address_cannot_reuse_its_terrain(self):
        def table(dim, values):
            size=len(values)
            return RubyData("Table",struct.pack("<5I",dim,size,1,1,size)
                            +struct.pack(f"<{size}H",*values))
        tiles=RubyObject("RPG::Tileset",{
            "@passages":table(1,(0,0,15)), "@priorities":table(1,(0,0,0))})
        # Sequential parsing in the QA verifier can reuse a released map's
        # memory address. Make that collision deterministic.
        with patch("pilot_hoenn.id",return_value=-1,create=True):
            self.assertTrue(open_tile(
                RubyObject("RPG::Map",{"@data":table(3,(1,))}),tiles,0,0))
            self.assertFalse(open_tile(
                RubyObject("RPG::Map",{"@data":table(3,(2,))}),tiles,0,0))


if __name__=="__main__":
    unittest.main()
