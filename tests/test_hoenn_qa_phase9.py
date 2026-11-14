"""QA09 synthetic checks for Hoenn Elite Four and Champion; NO Game.exe."""
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
from hoenn_qa_phase9 import (
    ELITE_NAMES, LEAGUE_MAPS, LEAGUE_BOSS_EVENTS, LEAGUE_EXIT,
    HOF_ENTRY, headers_and_teams, audit_generated, verify_league_events,
    verify_league_pbs, verify_copy,
)


class LeagueQA09Tests(unittest.TestCase):
    def setUp(self):
        self.maps = {mid: ruby("RPG::Map", width=80, height=80, events={})
                     for mid in LEAGUE_MAPS}
        for mid, x, y, name, script, trigger in (
            *LEAGUE_BOSS_EVENTS, LEAGUE_EXIT, HOF_ENTRY
        ):
            page = event_page(script=script, touch=(trigger == 1))
            if trigger == 1:
                page.attrs["@through"] = True
            append_event(self.maps[mid], name, x, y, page)

    def test_all_five_boss_rooms_and_lobby_maps(self):
        report = audit_generated(self.maps)
        self.assertEqual(report["league_source_map_ids"], list(range(93,101)))
        self.assertEqual(report["verified_league_boss_events"], 5)
        self.assertEqual(report["verified_champion_exit_and_hall_entry"], 2)
        self.assertEqual(report["elite_four_order"], ["Sidney","Phoebe","Glacia","Drake"])
        self.assertEqual(report["pbs_reference_party_sizes"], [5,5,5,5,6])
        self.assertTrue(report["all_previous_elite_victories_required"])
        self.assertTrue(report["map_local_boss_event_guards"])
        self.assertTrue(report["champion_requires_four_complete_victories"])
        self.assertEqual(report["battle_engine_owned_by_blue_decades"], True)
        for key in ("native_game_exe_tested","native_elite_battles_verified",
                    "native_champion_battle_verified","native_dynamic_balance_verified",
                    "native_league_warps_verified","native_league_ui_verified",
                    "native_hall_of_fame_verified","native_story_approved",
                    "source_event_scripts_reused"):
            self.assertIs(report[key], False)

    def test_missing_lobby_map_fails(self):
        self.maps.pop(93)
        with self.assertRaisesRegex(ValueError, "faltam mapas"):
            verify_league_events(self.maps)

    def test_missing_elite_npc_fails(self):
        self.maps[96].attrs["@events"].clear()
        with self.assertRaisesRegex(ValueError, "Glacia"):
            verify_league_events(self.maps)

    def test_wrong_elite_binding_fails(self):
        ev = next(iter(self.maps[97].attrs["@events"].values()))
        ev.attrs["@pages"][0].attrs["@list"][0] = command(
            355, b"BlueHoennPilot.elite_four(0)"
        )
        with self.assertRaisesRegex(ValueError, "Drake"):
            verify_league_events(self.maps)

    def test_out_of_position_or_touch_trigger_fails(self):
        ev = next(iter(self.maps[95].attrs["@events"].values()))
        ev.attrs["@x"] += 1
        with self.assertRaisesRegex(ValueError, "Phoebe"):
            verify_league_events(self.maps)
        ev.attrs["@x"] -= 1
        ev = next(iter(self.maps[98].attrs["@events"].values()))
        ev.attrs["@pages"][0].attrs["@trigger"] = 1
        with self.assertRaisesRegex(ValueError, "Wallace"):
            verify_league_events(self.maps)

    def test_hall_exit_and_champion_exit_must_be_separate(self):
        ev = next(iter(self.maps[99].attrs["@events"].values()))
        ev.attrs["@pages"][0].attrs["@list"][0] = command(
            355, b"BlueHoennPilot.champion_wallace"
        )
        with self.assertRaisesRegex(ValueError, "HallOfFame"):
            verify_league_events(self.maps)

    def test_duplicate_boss_event_fails(self):
        events = self.maps[94].attrs["@events"]
        events[999] = next(iter(events.values()))
        with self.assertRaisesRegex(ValueError, "Sidney"):
            verify_league_events(self.maps)

    def test_correct_pbs_lineups_and_duplicate_rejection(self):
        sections = []
        for header, team in headers_and_teams():
            sections.append(header + "\nLoseText = Vitoria!\n" + "".join(
                f"Pokemon = {species},{level}\n" for species,level in team
            ))
        text = "".join(sections)
        verify_league_pbs(text)
        with self.assertRaisesRegex(ValueError, "duplicado"):
            verify_league_pbs(text + sections[0])
        with self.assertRaisesRegex(ValueError, "Wallace"):
            verify_league_pbs(text.replace("MILOTIC,58", "MAGIKARP,58"))
        with self.assertRaisesRegex(ValueError, "Glacia"):
            verify_league_pbs(text.replace("[BLUE_HOENN_ELITE,Glacia,1096]", "[BLUE_HOENN_ELITE,Glacia,1099]"))

    def test_tampered_party_length_is_not_accepted(self):
        headers = headers_and_teams()
        self.assertEqual([len(v) for _,v in headers],[5,5,5,5,6])
        self.assertEqual(ELITE_NAMES,("Sidney","Phoebe","Glacia","Drake"))

    def test_private_copy_only(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, ".blue-work"):
                verify_copy(Path(folder))


if __name__ == "__main__":
    unittest.main()
