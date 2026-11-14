"""Hoenn QA10 synthetic Hall and circuit contracts; never Game.exe proof."""
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
from hoenn_qa_phase10 import (
    FINAL_MAPS, HALL_EVENT, LEAGUE_EXIT, LEAGUE_GATE_SIGN,
    CORE_REQUIREMENTS, NATIVE_UNVERIFIED, RUBY_REQUIREMENTS,
    audit_generated, verify_final_events, verify_copy,
)


class HoennQA10Tests(unittest.TestCase):
    def setUp(self):
        self.maps = {
            mid: ruby("RPG::Map", width=95, height=90, events={})
            for mid in FINAL_MAPS
        }
        for mid,x,y,name,script,trigger in (
            LEAGUE_EXIT, HALL_EVENT, LEAGUE_GATE_SIGN
        ):
            page = event_page(script=script, touch=trigger == 1)
            if trigger == 1:
                page.attrs["@through"] = True
            append_event(self.maps[mid], name, x, y, page)

    def test_hall_and_circuit_contracts(self):
        report = audit_generated(self.maps)
        self.assertEqual(report["final_source_map_ids"],[93,98,99,322])
        self.assertEqual(report["champion_exit_anchor"],[98,8,4])
        self.assertEqual(report["hall_of_fame_anchor"],[99,9,18])
        self.assertEqual(report["postgame_league_sign_anchor"],[322,23,16])
        self.assertEqual(report["expected_neighbor_unlocks"],["JOHTO","SINNOH"])
        for key in (
            "complete_league_only_after_hall_event",
            "completion_requires_all_8_local_badges",
            "completion_requires_wally_and_elite_four",
            "completion_requires_wallace_victory",
            "completion_requires_original_hall_map",
            "circuit_unlock_not_immediate_travel",
            "preserves_original_decades_badges_and_switches",
            "regional_save_only",
        ):
            self.assertIs(report[key],True,key)
        for key in (*NATIVE_UNVERIFIED,"donor_event_scripts_copied"):
            self.assertIs(report[key],False,key)

    def test_hall_missing_or_wrong_map_rejected(self):
        self.maps.pop(99)
        with self.assertRaisesRegex(ValueError, "mapas finais"):
            verify_final_events(self.maps)

    def test_hall_handler_mismatch_rejected(self):
        hall = next(iter(self.maps[99].attrs["@events"].values()))
        hall.attrs["@pages"][0].attrs["@list"][0] = command(355,b"BlueHoennPilot.champion_wallace")
        with self.assertRaises(ValueError):
            verify_final_events(self.maps)

    def test_hall_trigger_must_remain_touch(self):
        hall = next(iter(self.maps[99].attrs["@events"].values()))
        hall.attrs["@pages"][0].attrs["@trigger"] = 0
        with self.assertRaises(ValueError):
            verify_final_events(self.maps)

    def test_hall_event_duplicate_rejected(self):
        ev = next(iter(self.maps[99].attrs["@events"].values()))
        self.maps[99].attrs["@events"][123] = ev
        with self.assertRaises(ValueError):
            verify_final_events(self.maps)

    def test_no_early_exit_to_hall(self):
        ev = next(iter(self.maps[98].attrs["@events"].values()))
        ev.attrs["@x"] = 7
        with self.assertRaises(ValueError):
            verify_final_events(self.maps)

    def test_postgame_sign_handler_must_be_authored(self):
        sign = next(iter(self.maps[322].attrs["@events"].values()))
        sign.attrs["@pages"][0].attrs["@list"][0] = command(355,b"BlueRegionTravel.travel(:SINNOH)")
        with self.assertRaises(ValueError):
            verify_final_events(self.maps)

    def test_core_and_hall_guards_are_auditable(self):
        self.assertIn('BlueRegions.complete_league(region,"HOENN")',RUBY_REQUIREMENTS)
        self.assertIn('qa9_at_league_map?(99)',RUBY_REQUIREMENTS)
        self.assertIn('def self.unlocked(state)',CORE_REQUIREMENTS)
        self.assertIn('def self.complete_league(state, region)',CORE_REQUIREMENTS)

    def test_copy_cannot_be_outside_ignored_work_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,".blue-work"):
                verify_copy(Path(directory))


if __name__ == "__main__":
    unittest.main()
