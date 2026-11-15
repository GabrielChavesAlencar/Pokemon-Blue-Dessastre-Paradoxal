"""Stage 2 tests for authored event templates and safe geometry selection.

Synthetic maps and mocks, never real donor assets or native Game.exe.
"""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))

from build_johto_events import event_page, ruby
from hoenn_presentation import activate_trainer_sight
from pilot_hoenn import (
    RIVAL_NAMES, RIVAL_TEAMS, add_opening, rival_position,
    starter_ball_positions,
)


class HoennStage2Tests(unittest.TestCase):
    def test_counter_starters_are_distinct_and_use_three_unique_versions(self):
        self.assertEqual(RIVAL_NAMES, ("May", "Brendan"))
        self.assertEqual(RIVAL_TEAMS, {
            "TREECKO": ("TORCHIC", 210),
            "TORCHIC": ("MUDKIP", 211),
            "MUDKIP": ("TREECKO", 212),
        })
        self.assertEqual(len({version for _, version in RIVAL_TEAMS.values()}), 3)

    def test_three_physical_balls_and_route103_event_are_authored(self):
        maps = {mid: ruby("RPG::Map", events={}) for mid in (8, 101, 103)}
        balls = [(101, 8, 20), (101, 10, 20), (101, 12, 20)]
        add_opening(maps, balls, (103, 8, 7), "trainer_LASS", 700)
        route = {row.attrs["@name"].decode(): row
                 for row in maps[101].attrs["@events"].values()}
        self.assertEqual(len(route), 5)
        for species in ("TREECKO", "TORCHIC", "MUDKIP"):
            self.assertIn("HN_BirchBag_" + species, route)
            page = route["HN_BirchBag_" + species].attrs["@pages"][0]
            script = page.attrs["@list"][0].attrs["@parameters"][0].decode()
            self.assertIn("choose_birch_ball(:" + species + ")", script)
            self.assertEqual(page.attrs["@trigger"], 0)
        rival = next(iter(maps[103].attrs["@events"].values()))
        self.assertEqual(rival.attrs["@name"], b"HN_Rival_103")
        self.assertEqual(rival.attrs["@pages"][0].attrs["@trigger"], 1)

    def test_trainer_sight_uses_the_pinned_facing_and_keeps_the_event_id(self):
        source_page = event_page(script="nil", sprite="trainer_BUGCATCHER")
        source_page.attrs["@trigger"] = 2
        source_page.attrs["@graphic"].attrs["@direction"] = 8
        source = ruby("RPG::Map", events={
            4: ruby("RPG::Event", id=4, name=b"Bugcatcher Rick Trainer(2)",
                    x=25, y=15, pages=[source_page]),
        })
        installed = event_page(script='BlueHoennPilot.battle(:BUGCATCHER, "Rick")',
                               sprite="trainer_BUGCATCHER")
        rick = ruby("RPG::Event", id=42, name=b"HN_Rick", x=25, y=15, pages=[installed])
        world = ruby("RPG::Map", events={42: rick})
        self.assertEqual(activate_trainer_sight(world, source), 1)
        self.assertEqual(rick.attrs["@id"], 42)
        self.assertEqual(rick.attrs["@name"], b"HN_Rick Trainer(2)")
        live, defeated = rick.attrs["@pages"]
        self.assertEqual(live.attrs["@trigger"], 2)
        self.assertEqual(live.attrs["@graphic"].attrs["@direction"], 8)
        self.assertEqual(live.attrs["@list"][0].attrs["@parameters"][0],
                         b'BlueHoennPilot.challenge_trainer(get_self,:BUGCATCHER,"Rick",102,false)')
        self.assertEqual(defeated.attrs["@trigger"], 0)
        self.assertTrue(defeated.attrs["@condition"].attrs["@self_switch_valid"])

    def test_ball_selector_requires_passable_tiles_and_approach(self):
        maps = {101: ruby("RPG::Map", width=28, height=35)}
        with patch("pilot_hoenn.open_tile", return_value=True), \
             patch("pilot_hoenn.reachable", return_value=None):
            result = starter_ball_positions(maps, {101: object()}, {}, set())
        self.assertEqual(result, [(101, 6, 16), (101, 8, 16), (101, 10, 16)])
        with patch("pilot_hoenn.open_tile", return_value=False):
            with self.assertRaisesRegex(ValueError, "maleta|Maleta"):
                starter_ball_positions(maps, {101: object()}, {}, set())

    def test_rival_anchor_requires_reachable_northern_route(self):
        maps = {103: ruby("RPG::Map", width=20, height=30)}
        with patch("pilot_hoenn.open_tile", return_value=True), \
             patch("pilot_hoenn.reachable", return_value=None):
            result = rival_position(maps, {103: object()}, {}, set(), [])
        self.assertEqual(result, (103, 10, 7))
        with patch("pilot_hoenn.open_tile", return_value=False):
            with self.assertRaisesRegex(ValueError, "Rota 103"):
                rival_position(maps, {103: object()}, {}, set(), [])

    def test_reject_overlapping_ball_and_rescue_trigger(self):
        maps = {mid: ruby("RPG::Map", events={}) for mid in (8, 101, 103)}
        with self.assertRaisesRegex(ValueError, "sobrepõem"):
            add_opening(maps, [(101, 10, 18), (101, 12, 20), (101, 14, 20)],
                        (103, 8, 7), "trainer_LASS", 700)


if __name__ == "__main__":
    unittest.main()
