"""QA06 isolated Hoenn climate contracts; synthetic maps only, not Game.exe."""
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
from hoenn_qa_phase6 import (
    CAVE_MAPS, CLIMATE_EVENTS, PILLAR_MAPS, RUBY_GUARDS,
    audit_generated, verify_copy, verify_story_events,
)


class HoennClimateQATests(unittest.TestCase):
    def setUp(self):
        ids = set(CAVE_MAPS + PILLAR_MAPS + (83, 236))
        self.maps = {mid: ruby("RPG::Map", width=65, height=65, events={})
                     for mid in ids}
        for mid, x, y, name, script, trigger in CLIMATE_EVENTS:
            page = event_page(script=script, touch=(trigger == 1))
            if trigger == 1:
                page.attrs["@through"] = True
            append_event(self.maps[mid], name, x, y, page)

    def test_climate_sequence_anchors_and_manifest(self):
        summary = audit_generated(self.maps)
        self.assertEqual(summary["verified_climate_events"], 5)
        self.assertEqual(summary["cave_of_origin_source_maps"], [238, 239, 240])
        self.assertEqual(len(summary["sky_pillar_source_maps"]), 8)
        self.assertTrue(summary["map_local_story_guards"])
        for key in ("native_game_exe_tested", "native_weather_visuals_verified",
                    "native_rayquaza_cinematic_verified",
                    "native_sky_pillar_puzzles_verified", "donor_scripts_executed",
                    "native_story_accepted"):
            self.assertIs(summary[key], False)

    def test_wrong_script_rejected(self):
        ev = next(iter(self.maps[248].attrs["@events"].values()))
        ev.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"] = [b"nil"]
        with self.assertRaisesRegex(ValueError, "script"):
            verify_story_events(self.maps)

    def test_missing_or_duplicate_story_rejected(self):
        original = self.maps[83].attrs["@events"]
        with self.assertRaises(ValueError):
            verify_story_events({**self.maps, 83: ruby("RPG::Map", events={})})
        ev = next(iter(original.values()))
        original[999] = ev
        with self.assertRaisesRegex(ValueError, "duplicada"):
            verify_story_events(self.maps)

    def test_wrong_position_and_trigger_rejected(self):
        ev = next(iter(self.maps[241].attrs["@events"].values()))
        ev.attrs["@x"] = 99
        with self.assertRaisesRegex(ValueError, "âncora"):
            verify_story_events(self.maps)
        ev.attrs["@x"] = 13
        ev.attrs["@pages"][0].attrs["@trigger"] = 1
        with self.assertRaisesRegex(ValueError, "trigger"):
            verify_story_events(self.maps)

    def test_cave_map_missing_rejected(self):
        self.maps.pop(239)
        with self.assertRaisesRegex(ValueError, "mapas ausentes"):
            audit_generated(self.maps)

    def test_ruby_guards_present_and_unique(self):
        src = (ROOT / "scripts/regions/HoennPilot.rb").read_text("utf-8")
        for marker in RUBY_GUARDS:
            self.assertIn(marker, src)

    def test_private_copy_mandatory(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, ".blue-work"):
                verify_copy(Path(tmp))


if __name__ == "__main__":
    unittest.main()
