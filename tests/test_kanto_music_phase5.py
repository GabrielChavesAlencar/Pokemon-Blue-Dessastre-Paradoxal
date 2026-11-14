"""F5: confirmed scene BGM only, preserving Decades and unfinished events."""
from __future__ import annotations
import unittest
from test_kanto_music_phase1 import KantoMusicPhaseOneTests, ROOT
from scripts.music import compile_kanto_music as compiler


class PhaseFiveMusicTests(KantoMusicPhaseOneTests):
    def test_all_thirteen_scenes_catalogued_only_five_enabled(self):
        self.assertEqual(self.rules["phase"], 5)
        self.assertEqual(len(self.rules["scenes"]), 13)
        self.assertEqual({x["track"] for x in self.rules["scenes"]},
                         compiler.SCENE_NUMBERS)
        self.assertEqual({x["scene"] for x in self.rules["scenes"] if x["enabled"]},
                         compiler.SCENE_ENABLED_PHASE5)
        self.assertEqual(compiler.phase5_track_numbers(self.project), {3,7,10,30,72})
        self.assertEqual(len(compiler.approved_track_numbers(self.project)),32)
        self.assertEqual(len(compiler.approved_audio_track_numbers(self.project)),38)
        self.assertEqual(sum(not row["enabled"] for row in self.rules["scenes"]),8)
        self.assertTrue(all("pending_reason" in row for row in self.rules["scenes"]
                            if not row["enabled"]))

    def test_compiled_really_existing_mapids_and_verified_scenes(self):
        for number in compiler.approved_audio_track_numbers(self.project):
            self.add_music(number)
        data,report=self.compile()
        lines=data.decode().splitlines()
        scenes=[row.split("\t") for row in lines if row.startswith("SCENE\t")]
        self.assertEqual(report["source_maps"],142)
        self.assertEqual(report["preview_maps"],35)
        self.assertEqual(report["active_map_bindings"],72)
        self.assertEqual(report["active_battle_bindings"],8)
        self.assertEqual(report["active_transport_bindings"],2)
        self.assertEqual(report["active_me_bindings"],6)
        self.assertEqual(report["active_scene_bindings"],5)
        self.assertEqual(report["staged_scenes"],13)
        self.assertEqual(len(report["pending_scenes"]),8)
        self.assertEqual(report["missing_audio"],[])
        self.assertEqual({row[1] for row in scenes},compiler.SCENE_ENABLED_PHASE5)
        self.assertTrue(all(row[2].startswith("Kanto/1-") and
                            row[3:] == ["100","100"] for row in scenes))
        self.assertFalse(any(row.startswith("SCENE\tcredits\t") for row in lines))
        self.assertFalse(any(row.startswith("SCENE\topening_movie\t") for row in lines))
        self.assertNotIn("Kanto/1-73. Staff Credits.mp3",data.decode())
        self.assertIn("SCOPE\t705\tPALLET_TOWN\t0",lines)
        self.assertFalse((self.game/compiler.OUTPUT).exists())

    def test_missing_title_track_keeps_only_title_disabled(self):
        for number in compiler.approved_audio_track_numbers(self.project):
            if number != 3:
                self.add_music(number)
        data,report=self.compile()
        self.assertEqual(report["active_scene_bindings"],4)
        self.assertEqual(report["active_map_bindings"],72)
        self.assertEqual(report["active_battle_bindings"],8)
        self.assertEqual(report["active_me_bindings"],6)
        self.assertIn("Kanto/1-03. Title Screen.mp3",report["missing_audio"])
        self.assertNotIn("SCENE\tpilot_title\t",data.decode())

    def test_unproven_credits_and_cinematic_never_install_or_compile(self):
        for scene in ["credits","opening_movie"]:
            entry=next(row for row in self.rules["scenes"] if row["scene"]==scene)
            entry["enabled"]=True
            self.write_rules()
            with self.assertRaisesRegex(ValueError,"Unverified Kanto scene"):
                self.compile()
            with self.assertRaisesRegex(ValueError,"Unverified Kanto scene"):
                compiler.phase5_track_numbers(self.project)
            entry["enabled"]=False

    def test_duplicate_and_wrong_kind_are_rejected(self):
        row=self.rules["scenes"][0]
        row["track"]=29   # ME badge, not looping BGM
        self.write_rules()
        with self.assertRaisesRegex(ValueError,"Unknown Kanto BGM"):
            self.compile()
        row["track"]=2
        self.rules["scenes"].append(dict(self.rules["scenes"][1]))
        self.write_rules()
        with self.assertRaisesRegex(ValueError,"duplicat"):
            self.compile()

    def test_verified_callsites_do_not_run_on_failed_league_or_decades_title(self):
        pilot=(ROOT/"scripts/regions/KantoPilot.rb").read_text(encoding="utf-8")
        title=(ROOT/"scripts/battle_polish/Title.rb").read_text(encoding="utf-8")
        runtime=(ROOT/"scripts/music/BlueMusic.rb").read_text(encoding="utf-8")
        self.assertIn("return false unless BlueRegions.complete_league(progress",pilot)
        self.assertIn('BlueMusic.with_kanto_scene("hall_of_fame")',pilot)
        self.assertEqual(pilot.count('BlueMusic.with_kanto_scene("oak_talk")'),1)
        self.assertEqual(pilot.count('BlueMusic.with_kanto_scene("rival_appears")'),3)
        self.assertIn("BlueMusic.kanto_pilot_title_audio",title)
        self.assertIn("return super unless BlueParadoxTitle.available_track?",title)
        self.assertIn("!File.file?('Data/blue-kanto-install.json')",runtime)
        self.assertIn("current.name==audio.name",runtime)
        self.assertNotIn('with_kanto_scene("credits")',pilot)
        self.assertNotIn('with_kanto_scene("epilogue")',pilot)
        self.assertNotIn('with_kanto_scene("opening_movie")',pilot)

    def test_user_config_and_pilot_save_bytes_remain_untouched(self):
        for number in compiler.approved_audio_track_numbers(self.project):
            self.add_music(number)
        pref=self.game/"Data/blue-music.rxdata"
        pref.write_bytes(b"my personal Decades music preferences")
        old_pilot=(self.game/"Kanto pilot.json").read_bytes()
        out,report=self.compile()
        compiler.write_safely(self.project,self.game,out)
        self.assertEqual(pref.read_bytes(),b"my personal Decades music preferences")
        self.assertEqual((self.game/"Kanto pilot.json").read_bytes(),old_pilot)
        self.assertEqual(report["active_scene_bindings"],5)


if __name__ == "__main__":
    unittest.main()
