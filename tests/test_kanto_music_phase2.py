"""F2: only non-preview compiled maps, real regional BGM and safe fallbacks."""
from __future__ import annotations

import json
import unittest
from test_kanto_music_phase1 import KantoMusicPhaseOneTests
from scripts.music import compile_kanto_music as compiler


class PhaseTwoMusicTests(KantoMusicPhaseOneTests):
    """Reuse the 142-map synthetic pilot without copyrighted audio recordings."""

    def test_phase2_has_only_approved_maps_and_exact_required_tracks(self):
        enabled = [row for row in self.rules["maps"] if row["enabled"]]
        disabled = {row["map"] for row in self.rules["maps"] if not row["enabled"]}
        self.assertGreaterEqual(self.rules["phase"], 2)
        self.assertEqual(len(enabled), 49)
        self.assertEqual(disabled, {"ROUTE_4", "SILPH_LOBBY"})
        self.assertEqual(compiler.phase2_track_numbers(self.project),
                         {6, 8, 13, 15, 17, 21, 25, 34, 35, 36, 37, 40,
                          47, 50, 52, 55, 56})
        self.assertEqual(sum(x["enabled"] for x in self.rules["battles"]), 8)
        self.assertEqual(sum(x["enabled"] for x in self.rules["events"]),6)
        self.assertEqual(sum(x["enabled"] for x in self.rules["scenes"]), 5)

    def test_real_compiled_ids_emit_49_maps_2_vehicles_no_decades(self):
        for number in compiler.phase2_track_numbers(self.project):
            self.add_music(number)
        content, report = self.compile()
        lines = content.decode().splitlines()
        maps = [row.split("\t") for row in lines if row.startswith("MAP\t")]
        modes = [row.split("\t") for row in lines if row.startswith("TRANSPORT\t")]
        self.assertEqual(len(maps), 49)
        self.assertEqual(len(modes), 2)
        self.assertEqual(report["active_map_bindings"], 49)
        self.assertEqual(report["active_transport_bindings"], 2)
        self.assertEqual(report["active_battle_bindings"], 0)
        # This fixture installs only 17 F2 tracks. Missing F3 tracks must
        # remain non-binding while F2 MAP and TRANSPORT still compile.
        self.assertEqual(len(report["missing_audio"]),19)
        self.assertTrue(all(name.startswith(("Kanto/", "ME/Kanto/")) for name in report["missing_audio"]))
        self.assertEqual({row[1] for row in modes}, {"bicycle", "surf"})
        self.assertTrue(all(int(row[1]) >= 705 for row in maps))
        self.assertFalse(any(row.startswith("BATTLE\t") for row in lines))
        self.assertEqual(report["real_map_ids"]["PALLET_TOWN"], 705)
        self.assertIn(["MAP", "705", "Kanto/1-06. Pallet Town.mp3", "100", "100"],maps)
        forbidden = {report["real_map_ids"][s] for s in ("SILPH_LOBBY", "ROUTE_4")}
        self.assertTrue(forbidden.isdisjoint({int(row[1]) for row in maps}))
        self.assertIn(["TRANSPORT", "bicycle",
                       "Kanto/1-37. Cycling.mp3", "100", "100"], modes)
        self.assertIn(["TRANSPORT", "surf",
                       "Kanto/1-52. Surfing.mp3", "100", "100"], modes)

    def test_missing_file_uses_original_map_audio_instead_of_fake_binding(self):
        for number in compiler.phase2_track_numbers(self.project):
            self.add_music(number)
        pallet = self.game / next(item["game_path"] for item in
                                  self.catalog["files"] if item["number"] == 6)
        pallet.unlink()
        content, report = self.compile()
        self.assertEqual(report["active_map_bindings"], 48)
        self.assertEqual(report["active_transport_bindings"], 2)
        self.assertFalse(any(row.startswith("MAP\t705\t") for row in
                             content.decode().splitlines()))
        self.assertIn("Kanto/1-06. Pallet Town.mp3",report["missing_audio"])

    def test_preview_remains_excluded_even_if_enabled_and_mp3_exists(self):
        for number in compiler.phase2_track_numbers(self.project):
            self.add_music(number)
        row=next(row for row in self.rules["maps"] if row["map"]=="SILPH_LOBBY")
        row["enabled"]=True
        self.write_rules()
        content, report=self.compile()
        self.assertEqual(report["active_map_bindings"],49)
        self.assertIn("SILPH_LOBBY",report["preview_skipped"])
        self.assertFalse(any(row.startswith(f"MAP\t{self.mapping['177']}\t") for
                             row in content.decode().splitlines()))

    def test_compiler_does_not_include_music_that_was_not_approved(self):
        for number in compiler.phase2_track_numbers(self.project):
            self.add_music(number)
        generated,_=self.compile()
        self.assertNotIn("Kanto/1-32.",generated.decode())
        self.assertNotIn("Kanto/1-38.",generated.decode())
        self.assertNotIn("Kanto/1-59.",generated.decode())


if __name__=="__main__":
    unittest.main()
