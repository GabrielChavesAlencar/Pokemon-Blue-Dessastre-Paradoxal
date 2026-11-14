"""Stage 05 read-only code contracts: Dewford, Granite Cave, Slateport.

All synthetic fixtures; this does not open Game.exe or import original sprites.
"""
from __future__ import annotations
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))

from build_johto_events import ruby
from hoenn_stage5 import (
    SOURCE_MAPS_STAGE5, OFFSET_BORDERS_STAGE5, WARP_PAIRS_STAGE5,
    BOAT_POINTS_STAGE5, CAVE_ENCOUNTERS_STAGE5, TRAINERS_STAGE5,
    BRAWLY_PBS, BRAWLY_TEAM, MUSEUM_AQUA, NPCS_STAGE5,
    MUSEUM_FEE_GATE, SLATEPORT_NORTH_GATE, SIGNS_STAGE5, PICKUPS_STAGE5,
)
from pilot_hoenn import (
    SOURCE_MAPS, WARP_PAIRS, add_stage5_events, validate_geometry,
)


class HoennStage5Tests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.game = Path(self.temporary.name)
        sprites = {row[3] for row in NPCS_STAGE5} | {row[5] for row in TRAINERS_STAGE5}
        sprites.update(("NPC_RSE_AquaGrunt",))
        for sprite in sprites:
            path = self.game / "Graphics/Characters" / f"{sprite}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic test")

        self.maps = {mid: ruby("RPG::Map", events={}) for mid in SOURCE_MAPS_STAGE5}

    def test_map_inventory_boat_and_original_museum_two_doorway_contract(self):
        self.assertEqual(len(SOURCE_MAPS_STAGE5), 20)
        self.assertEqual(len(SOURCE_MAPS), 58)
        self.assertEqual(len(WARP_PAIRS_STAGE5), 27)
        self.assertEqual(len(WARP_PAIRS), 68)
        self.assertEqual(OFFSET_BORDERS_STAGE5, (
            (108, "South", 170, 28, "North", 0),
            (111, "North", 0, 32, "South", 0),
        ))
        self.assertEqual(BOAT_POINTS_STAGE5, (
            (105, 11, 6), (28, 12, 10), (111, 21, 23)))
        self.assertIn(((32, 30, 26), (32, 30, 27),
                       (39, 11, 11), (39, 11, 10)), WARP_PAIRS_STAGE5)
        self.assertIn(((32, 31, 26), (32, 31, 27),
                       (39, 12, 11), (39, 12, 10)), WARP_PAIRS_STAGE5)
        self.assertNotIn(107, SOURCE_MAPS)
        self.assertNotIn(109, SOURCE_MAPS)
        self.assertNotIn(110, SOURCE_MAPS)
        self.assertNotIn(113, SOURCE_MAPS)

    def test_granite_cave_encounters_and_brawly_original_team(self):
        self.assertEqual(set(CAVE_ENCOUNTERS_STAGE5), {159, 160, 161, 162})
        for mid, table in CAVE_ENCOUNTERS_STAGE5.items():
            self.assertEqual(sum(weight for weight, *_ in table), 100, mid)
            self.assertTrue(all(low > 0 and low <= high
                                for _, _, low, high in table))
        self.assertEqual(BRAWLY_PBS, ("BLUE_HOENN_BRAWLY", "Brawly", 531))
        self.assertEqual(BRAWLY_TEAM,
                         (("MACHOP", 16), ("MEDITITE", 16), ("MAKUHITA", 19)))
        self.assertEqual([r[2] for r in MUSEUM_AQUA], [539, 540])
        self.assertEqual(len(TRAINERS_STAGE5), 8)

    def test_event_templates_no_collisions_and_fee_guards(self):
        summary = add_stage5_events(self.maps, self.game)
        self.assertEqual(summary["maps"], 20)
        self.assertEqual(summary["boat_stops"], 3)
        self.assertEqual(summary["trainers"], 11)
        self.assertEqual(summary["pickup_events"], 2)
        self.assertFalse(summary["museum_aqua_sprite_placeholder"])
        self.assertFalse(summary["gameplay_verified"])
        by_name = {}
        for mid, mp in self.maps.items():
            coords = [(e.attrs["@x"], e.attrs["@y"])
                      for e in mp.attrs["@events"].values()]
            self.assertEqual(len(coords), len(set(coords)), f"overlap on Map {mid}")
            for e in mp.attrs["@events"].values():
                by_name[e.attrs["@name"].decode()] = (mid, e)
        for name, expected in (("HN5_NPC_31_6_5", "BlueHoennPilot.brawly"),
                               ("HN5_NPC_162_11_11", "BlueHoennPilot.steven_letter"),
                               ("HN5_NPC_39_43_8", "BlueHoennPilot.stern"),
                               ("HN5_NPC_105_11_5", None)):
            if expected is None:
                self.assertNotIn(name, by_name)  # Briney is from stage 3.
                continue
            _, ev = by_name[name]
            script = ev.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"][0].decode()
            self.assertEqual(script, expected)
        for index in (1, 2):
            _, ev = by_name[f"HN5_AquaMuseum_{index}"]
            script = ev.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"][0].decode()
            self.assertIn(f"museum_aqua({index})", script)
        self.assertEqual(len(MUSEUM_FEE_GATE), 2)
        for mid, x, y in MUSEUM_FEE_GATE:
            ev = by_name[f"HN5_MuseumFee_{x}"][1]
            self.assertEqual(ev.attrs["@pages"][0].attrs["@trigger"], 1)
        for mid, x, y in SLATEPORT_NORTH_GATE:
            self.assertIn(f"HN5_NorthGate_{x}", by_name)
        for _, _, _, key, _, _ in PICKUPS_STAGE5:
            _, ev = by_name[f"HN5_Item_{key}"]
            self.assertEqual(len(ev.attrs["@pages"]), 2)
            self.assertTrue(ev.attrs["@pages"][1].attrs["@through"])
            self.assertTrue(ev.attrs["@pages"][1].attrs["@condition"].attrs["@self_switch_valid"])

    def test_missing_aqua_art_is_explicitly_unapproved_fallback(self):
        (self.game / "Graphics/Characters/NPC_RSE_AquaGrunt.png").unlink()
        summary = add_stage5_events(self.maps, self.game)
        self.assertTrue(summary["museum_aqua_sprite_placeholder"])
        self.assertEqual(summary["museum_aqua_sprite"], "trainer_YOUNGSTER")
        self.assertFalse(summary["gameplay_verified"])

    def test_event_overlap_aborts_before_install(self):
        from build_johto_events import ruby
        self.maps[39].attrs["@events"][1] = ruby(
            "RPG::Event", id=1, name=b"CONFLICT", x=35, y=7, pages=[])
        with self.assertRaisesRegex(ValueError, "sobrepõem"):
            add_stage5_events(self.maps, self.game)

    def test_boat_connects_three_source_maps_on_synthetic_geometry(self):
        sizes = {
            7:(20,20),8:(40,40),11:(20,20),12:(20,20),13:(20,20),
            14:(20,20),16:(30,30),17:(20,20),18:(20,20),19:(60,20),
            20:(80,60),21:(40,60),22:(20,20),23:(20,20),24:(80,80),
            25:(20,20),26:(80,20),27:(20,40),28:(20,20),29:(20,20),
            30:(60,20),31:(30,40),32:(40,60),33:(40,20),34:(20,20),
            35:(20,20),36:(40,40),37:(20,20),38:(60,20),39:(60,20),
            40:(20,20),101:(20,20),102:(50,20),103:(80,20),
            104:(150,80),105:(20,20),106:(20,20),108:(190,20),
            111:(40,63),112:(20,15),130:(100,20),131:(20,20),
            156:(58,46),157:(45,33),159:(52,22),160:(46,34),
            161:(46,34),162:(23,20),
            41:(40,20),42:(20,20),43:(20,20),44:(40,20),
            45:(20,20),46:(40,20),47:(20,40),113:(40,100),
            114:(44,100),115:(20,30),
        }
        maps = {mid:ruby("RPG::Map", width=w, height=h)
                for mid,(w,h) in sizes.items()}
        def can_walk(m, tile, x, y):
            mid = next(mid for mid, value in maps.items() if value is m)
            w,h = sizes[mid]
            return 0 <= x < w and 0 <= y < h
        with patch("pilot_hoenn.open_tile", side_effect=can_walk):
            edges, required = validate_geometry(
                maps, {mid:object() for mid in maps})
        for p in BOAT_POINTS_STAGE5:
            self.assertIn(p, required)
        self.assertIn(BOAT_POINTS_STAGE5[1], edges[BOAT_POINTS_STAGE5[0]])
        self.assertIn(BOAT_POINTS_STAGE5[2], edges[BOAT_POINTS_STAGE5[1]])


if __name__ == "__main__":
    unittest.main()
