"""Hoenn QA08 synthetic/static checks; never a playable Game.exe certificate."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/regions"))

from build_johto_events import command, event_page, ruby
from pilot_hoenn import append_event
from hoenn_qa_phase8 import (
    ACCESS_MAPS, ROAD_MAPS, WALLY_EVENT, LEAGUE_SIGN, WALLY_HEADER,
    audit_generated, inventory_road_obstacles, verify_road_events,
    verify_obstacle_events, verify_wally_pbs, verify_copy,
)
from hoenn_stage10 import WALLY_ROAD_TEAM


class VictoryRoadQA8Tests(unittest.TestCase):
    def setUp(self):
        self.maps = {i: ruby("RPG::Map", width=90, height=90, events={})
                     for i in ACCESS_MAPS}
        for mid, x, y, name, script, trigger in (WALLY_EVENT, LEAGUE_SIGN):
            page = event_page(script=script, touch=(trigger == 1))
            if trigger == 1:
                page.attrs["@through"] = True
            append_event(self.maps[mid], name, x, y, page)
        self.qa4 = {
            "new_safe_obstacles": [],
            "source_obstacles_needing_review": [],
            "source_obstacle_candidates": [],
        }

    def test_map_and_quest_contract(self):
        report = audit_generated(self.maps, self.qa4)
        self.assertEqual(report["victory_road_source_map_ids"], [250,251,252])
        self.assertEqual(report["verified_wally_event"], [250,8,26])
        self.assertEqual(report["verified_league_sign"], [322,23,16])
        self.assertEqual(len(report["wally_reference_party"]), 5)
        self.assertTrue(report["wally_requires_eight_local_badges"])
        self.assertTrue(report["south_entrance_requires_waterfall"])
        self.assertTrue(report["victory_road_exit_requires_wally"])
        for key in ("native_game_exe_tested", "native_wally_battle_verified",
                    "native_strength_puzzles_verified", "native_accepted",
                    "source_event_scripts_reused"):
            self.assertIs(report[key], False)

    def test_missing_cave_map_fails(self):
        self.maps.pop(251)
        with self.assertRaises(ValueError):
            verify_road_events(self.maps)

    def test_wally_wrong_coordinates_or_script_fails(self):
        ev = next(iter(self.maps[250].attrs["@events"].values()))
        ev.attrs["@x"] = 9
        with self.assertRaises(ValueError):
            verify_road_events(self.maps)
        ev.attrs["@x"] = 8
        ev.attrs["@pages"][0].attrs["@list"][0] = command(355, b"BlueHoennPilot.wally_mauville")
        with self.assertRaises(ValueError):
            verify_road_events(self.maps)

    def test_wally_touch_and_league_sign_action_fails_closed(self):
        ev = next(iter(self.maps[250].attrs["@events"].values()))
        ev.attrs["@pages"][0].attrs["@trigger"] = 0
        with self.assertRaises(ValueError):
            verify_road_events(self.maps)
        ev.attrs["@pages"][0].attrs["@trigger"] = 1
        sign = next(iter(self.maps[322].attrs["@events"].values()))
        sign.attrs["@pages"][0].attrs["@list"][0] = command(355, b"nil")
        with self.assertRaises(ValueError):
            verify_road_events(self.maps)

    def test_qa4_road_obstacle_backlog_is_distinguished(self):
        self.qa4["source_obstacle_candidates"] = [
            {"source_map_id": 250, "x": 15, "y": 15, "kind": "strength"},
            {"source_map_id": 251, "x": 11, "y": 15, "kind": "manual_field_review"},
        ]
        self.qa4["source_obstacles_needing_review"] = [
            [251,11,15,"manual_field_review","conditional_original"]
        ]
        page = event_page(script="nil", sprite="Object_Boulder")
        eid = append_event(self.maps[250], "HN_QA4_strength_250_15_15", 15, 15, page)
        page.attrs["@list"][0] = command(355, f"BlueHoennPilot.strength_boulder({eid})".encode("ascii"))
        self.qa4["new_safe_obstacles"] = [[250,15,15,"strength","Object_Boulder",eid]]
        summary = inventory_road_obstacles(self.qa4)
        self.assertEqual(summary["source_road_obstacle_candidates"], 2)
        self.assertEqual(summary["recreated_safe_rock_events"], 1)
        self.assertEqual(summary["obstacle_candidates_for_manual_review"], 1)
        verify_obstacle_events(self.maps, self.qa4)
        page.attrs["@list"][0] = command(355, b"nil")
        with self.assertRaises(ValueError):
            verify_obstacle_events(self.maps, self.qa4)

    def test_qa4_missing_candidate_fails(self):
        self.qa4["source_obstacle_candidates"] = [
            {"source_map_id":250,"x":20,"y":20,"kind":"strength"}
        ]
        with self.assertRaises(ValueError):
            inventory_road_obstacles(self.qa4)

    def test_real_wally_pbs_party_reference_contract(self):
        text = WALLY_HEADER + "\nItems = FULLRESTORE,FULLRESTORE\n" + "".join(
            f"Pokemon = {species},{level}\n" for species, level in WALLY_ROAD_TEAM)
        verify_wally_pbs(text)
        with self.assertRaises(ValueError):
            verify_wally_pbs(text + "\n" + WALLY_HEADER + "\n")
        with self.assertRaises(ValueError):
            verify_wally_pbs(text.replace("GARDEVOIR", "MAGIKARP"))

    def test_private_copy_only(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                verify_copy(Path(directory))


if __name__ == "__main__":
    unittest.main()
