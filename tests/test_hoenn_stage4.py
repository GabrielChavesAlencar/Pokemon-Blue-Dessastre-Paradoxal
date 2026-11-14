"""Stage 04 Hoenn Rustboro/Rusturf regression, no donor assets/Game.exe."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from build_johto_events import ruby
from hoenn_stage4 import (
    SOURCE_MAPS_STAGE4, OFFSET_BORDERS_STAGE4, WARP_PAIRS_STAGE4,
    LAND_ENCOUNTERS_STAGE4, CAVE_ENCOUNTERS_STAGE4, TRAINERS_STAGE4,
    ROXANNE_PBS, ROXANNE_TEAM, TUNNEL_AQUA_PBS, TUNNEL_AQUA_TEAM,
    PICKUPS_STAGE4, SIGNS_STAGE4, NPCS_STAGE4, CUT_TREES_STAGE4,
    RUSTBORO_THEFT_TRIGGERS, TUNNEL_AQUA_EVENT, ROXANNE_EVENT,
)
from pilot_hoenn import SOURCE_MAPS, WARP_PAIRS, add_stage4_events


class HoennStage4Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game = Path(self.temp.name)
        self.maps = {mid: ruby("RPG::Map", events={}) for mid in SOURCE_MAPS_STAGE4}
        needed = {row[3] for row in NPCS_STAGE4} | {row[5] for row in TRAINERS_STAGE4}
        needed.update(["NPC_ORAS_Roxanne", "NPC_RSE_AquaGrunt", "Object_CutTree"])
        for name in needed:
            p = self.game / "Graphics/Characters" / f"{name}.png"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"\x89PNG\r\n\x1a\nsynthetic fixture, not redistributable game graphic")

    def test_ten_new_maps_and_emulated_warps(self):
        self.assertEqual(len(SOURCE_MAPS_STAGE4), 10)
        self.assertEqual(len(SOURCE_MAPS), 28)
        self.assertEqual(len(WARP_PAIRS_STAGE4), 16)
        self.assertEqual(len(WARP_PAIRS), 32)
        self.assertEqual(OFFSET_BORDERS_STAGE4, (
            (104, "North", 110, 21, "South", 0),
            (130, "West", 0, 21, "East", 0),
        ))
        self.assertIn(((21, 27, 19), (21, 27, 20),
                       (27, 7, 22), (27, 7, 21)), WARP_PAIRS_STAGE4)
        self.assertFalse(any(a[0] == 27 and b[0] == 16 for a, _, b, _ in WARP_PAIRS_STAGE4))

    def test_emerald_encounters_percentages_and_stone_battle_team(self):
        self.assertEqual(set(LAND_ENCOUNTERS_STAGE4), {130})
        self.assertEqual(set(CAVE_ENCOUNTERS_STAGE4), {157})
        for table in [*LAND_ENCOUNTERS_STAGE4.values(), *CAVE_ENCOUNTERS_STAGE4.values()]:
            self.assertEqual(sum(row[0] for row in table), 100)
            self.assertTrue(all(1 <= low <= high for _, _, low, high in table))
        self.assertEqual(CAVE_ENCOUNTERS_STAGE4[157], ((100, "WHISMUR", 5, 8),))
        self.assertEqual(ROXANNE_PBS, ("BLUE_HOENN_ROXANNE", "Roxanne", 427))
        self.assertEqual(ROXANNE_TEAM, (
            ("GEODUDE", 12), ("GEODUDE", 12), ("NOSEPASS", 15)))
        self.assertEqual(TUNNEL_AQUA_PBS, ("BLUE_HOENN_AQUA", "Recruta", 405))
        self.assertEqual(TUNNEL_AQUA_TEAM, (("POOCHYENA", 11),))
        self.assertEqual(len(TRAINERS_STAGE4), 14)
        self.assertEqual(len(PICKUPS_STAGE4), 10)
        self.assertEqual(len(CUT_TREES_STAGE4), 5)

    def test_build_real_position_templates_without_event_collisions(self):
        report = add_stage4_events(self.maps, self.game)
        self.assertEqual(report["new_maps"], 10)
        self.assertEqual(report["trainer_battles"], 16)
        self.assertEqual(report["pickups"], 10)
        self.assertEqual(report["cut_trees"], 5)
        self.assertFalse(report["roxanne_sprite_placeholder"])
        self.assertFalse(report["cut_tree_sprite_placeholder"])
        self.assertFalse(report["gameplay_verified"])
        by_name = {}
        for mid, mp in self.maps.items():
            coords = [(e.attrs["@x"], e.attrs["@y"])
                      for e in mp.attrs["@events"].values()]
            self.assertEqual(len(coords), len(set(coords)), f"overlap on Map {mid}")
            for event in mp.attrs["@events"].values():
                by_name[event.attrs["@name"].decode()] = (mid, event)
        gym_mid, roxanne = by_name["HN4_Leader_Roxanne"]
        self.assertEqual(gym_mid, 27)
        self.assertEqual((roxanne.attrs["@x"], roxanne.attrs["@y"]), (7, 4))
        self.assertIn("BlueHoennPilot.roxanne",
                      roxanne.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"][0].decode())
        mid, aqua = by_name["HN4_AquaRusturf"]
        self.assertEqual(mid, 157)
        self.assertIn("rusturf_aqua",
                      aqua.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"][0].decode())
        for x in (21, 24, 28, 30, 32):
            event = next(e for mid, e in by_name.values()
                         if e.attrs["@name"].decode().startswith(f"HN4_CutTree_{x}_"))
            self.assertEqual(len(event.attrs["@pages"]), 2)
            self.assertTrue(event.attrs["@pages"][1].attrs["@through"])
            self.assertIn("BlueHoennPilot.cut_tree",
                          event.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"][0].decode())
        for key in ("ROUTE116_BLACKGLASSES", "RUSTURF_MAX_ETHER"):
            _, item = by_name["HN4_Item_" + key]
            self.assertTrue(item.attrs["@pages"][1].attrs["@condition"].attrs["@self_switch_valid"])
            self.assertTrue(item.attrs["@pages"][1].attrs["@through"])
        for mid, x, y in RUSTBORO_THEFT_TRIGGERS:
            name = f"HN4_Theft_{x}_{y}"
            self.assertIn(name, by_name)
            self.assertEqual(by_name[name][1].attrs["@pages"][0].attrs["@trigger"], 1)

    def test_missing_cut_graphic_does_not_create_invisible_obstacle(self):
        for name in ("Object_CutTree",):
            (self.game / "Graphics/Characters" / f"{name}.png").unlink()
        with self.assertRaisesRegex(ValueError, "árvore|arvore|cortável|Cut"):
            add_stage4_events(self.maps, self.game)

    def test_rusturf_woods_graph_remains_isolated_from_verdanturf(self):
        # Map 48 is Verdanturf, not part of this isolated pilot.
        self.assertNotIn(48, SOURCE_MAPS)
        self.assertIn(157, SOURCE_MAPS)
        self.assertFalse(any(a[0] == 157 and b[0] == 48
                             for a, _, b, _ in WARP_PAIRS))


if __name__ == "__main__":
    unittest.main()
