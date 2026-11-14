"""QA07 synthetic eight-gym checks (never claim Game.exe acceptance)."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/regions"))

from build_johto_events import event_page, ruby
from pilot_hoenn import append_event
from hoenn_qa_phase7 import (
    GYM_EVENTS, GYM_MAPS, BADGES, TRAINERS,
    FIELD_UNLOCKS, audit_generated, verify_copy, verify_gyms,
)


class GymQATests(unittest.TestCase):
    def setUp(self):
        self.maps = {mid: ruby("RPG::Map", width=90, height=90, events={})
                     for mid in GYM_MAPS}
        for mid, x, y, name, badge, _handler, _pbs in GYM_EVENTS:
            append_event(
                self.maps[mid], name, x, y,
                event_page(script=f"BlueHoennPilot.qa7_gym_battle(:{badge})"),
            )

    def test_complete_gym_catalog_and_milestones(self):
        summary = audit_generated(self.maps)
        self.assertEqual(len(GYM_EVENTS), 9)
        self.assertEqual(len(GYM_MAPS), 8)
        self.assertEqual(len(BADGES), 8)
        self.assertEqual(len(TRAINERS), 8)
        self.assertEqual(summary["verified_gym_event_bindings"], 9)
        self.assertEqual(summary["verified_distinct_gym_maps"], 8)
        self.assertEqual(set(summary["reference_field_unlocks"]), set(BADGES))
        self.assertEqual(set(FIELD_UNLOCKS.values()),
                         {"CUT", "FLASH", "ROCKSMASH", "STRENGTH",
                          "SURF", "FLY", "DIVE", "WATERFALL"})
        self.assertTrue(summary["gym_trigger_map_guard"])
        self.assertTrue(summary["base_pbs_levels_not_fixed_gameplay_levels"])
        self.assertEqual(summary["battle_engine"], "Blue/Decades TrainerBattle.start")
        for key in ("native_game_exe_tested", "native_gym_puzzles_verified",
                    "native_badges_in_trainer_card_verified",
                    "native_battle_scaling_verified", "native_story_approved",
                    "source_scripts_copied"):
            self.assertIs(summary[key], False)

    def test_missing_gym_cannot_pass(self):
        self.maps.pop(63)
        with self.assertRaisesRegex(ValueError, "ausente"):
            verify_gyms(self.maps)

    def test_tate_liza_twin_binding_is_required(self):
        pair = self.maps[82].attrs["@events"]
        bad = next(k for k, v in pair.items()
                   if v.attrs["@x"] == 26)
        del pair[bad]
        with self.assertRaisesRegex(ValueError, "Liza"):
            verify_gyms(self.maps)

    def test_wrong_event_script_or_trigger_fails_closed(self):
        ev = next(iter(self.maps[87].attrs["@events"].values()))
        ev.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"] = [b"BlueHoennPilot.juan"]
        with self.assertRaisesRegex(ValueError, "script"):
            verify_gyms(self.maps)
        ev.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"] = [b"BlueHoennPilot.qa7_gym_battle(:RAIN)"]
        ev.attrs["@pages"][0].attrs["@trigger"] = 1
        with self.assertRaisesRegex(ValueError, "trigger"):
            verify_gyms(self.maps)

    def test_event_displaced_or_duplicated_fails_closed(self):
        events = self.maps[27].attrs["@events"]
        ev = next(iter(events.values()))
        ev.attrs["@x"] += 1
        with self.assertRaisesRegex(ValueError, "âncora"):
            verify_gyms(self.maps)
        ev.attrs["@x"] -= 1
        events[999] = ev
        with self.assertRaisesRegex(ValueError, "duplicada"):
            verify_gyms(self.maps)

    def test_private_copy_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, ".blue-work"):
                verify_copy(Path(tmp))


if __name__ == "__main__":
    unittest.main()
