"""Phase 4: all fourteen ME catalogued, six triggered by verified success paths."""
from __future__ import annotations
import unittest
from pathlib import Path
from test_kanto_music_phase1 import KantoMusicPhaseOneTests, ROOT
from scripts.music import compile_kanto_music as compiler


class KantoMusicPhase4Tests(KantoMusicPhaseOneTests):
    def test_all_fourteen_me_inventoried_only_six_approved(self):
        self.assertGreaterEqual(self.rules["phase"],4)
        self.assertEqual(len(self.rules["events"]),14)
        numbers={x["track"] for x in self.rules["events"]}
        self.assertEqual(numbers,compiler.ME_NUMBERS)
        approved={x["event"] for x in self.rules["events"] if x["enabled"]}
        self.assertEqual(approved,compiler.ME_ENABLED_PHASE4)
        self.assertEqual(compiler.phase4_track_numbers(self.project),
                         {9,14,23,29,31,54})
        self.assertEqual(len(compiler.approved_track_numbers(self.project)),30)
        self.assertEqual(len(compiler.approved_audio_track_numbers(self.project)),36)
        self.assertEqual(len([r for r in self.rules["events"] if not r["enabled"]]),8)
        self.assertTrue(all("pending_reason" in r for r in self.rules["events"]
                            if not r["enabled"]))

    def test_six_ME_only_with_audio_and_real_map_scope(self):
        for number in compiler.approved_audio_track_numbers(self.project):
            self.add_music(number)
        raw, report = self.compile()
        lines=raw.decode().splitlines()
        self.assertEqual(report["source_maps"],142)
        self.assertEqual(report["preview_maps"],45)
        self.assertEqual(report["active_map_bindings"],50)
        self.assertEqual(report["active_battle_bindings"],8)
        self.assertEqual(report["active_transport_bindings"],2)
        self.assertEqual(report["active_me_bindings"],6)
        self.assertEqual(report["staged_events"],14)
        self.assertEqual(len(report["pending_me_events"]),8)
        self.assertEqual(report["missing_audio"],[])
        me=[line.split("\t") for line in lines if line.startswith("ME\t")]
        self.assertEqual({m[1] for m in me},compiler.ME_ENABLED_PHASE4)
        self.assertEqual({m[2] for m in me},
                         {f"Kanto/{self.track(n)['filename']}" for n in
                          compiler.phase4_track_numbers(self.project)})
        self.assertTrue(all(m[3:] == ["100","100"] for m in me))
        self.assertNotIn("ME\tgame_freak_logo\t",raw.decode())
        self.assertNotIn("ME\tjackpot\t",raw.decode())

    def track(self,number):
        return next(f for f in self.catalog["files"] if f["number"]==number)

    def test_missing_me_fails_closed_without_affecting_battle_or_maps(self):
        for number in compiler.approved_audio_track_numbers(self.project):
            if number != 54: self.add_music(number)
        raw,report=self.compile()
        self.assertEqual(report["active_me_bindings"],5)
        self.assertEqual(report["active_map_bindings"],50)
        self.assertEqual(report["active_battle_bindings"],8)
        self.assertIn("ME/Kanto/1-54. Caught a Pokémon!.mp3",report["missing_audio"])
        self.assertNotIn("ME\tcaught\t",raw.decode())

    def test_preview_and_decades_saves_are_not_changed_by_compiler(self):
        for number in compiler.approved_audio_track_numbers(self.project):
            self.add_music(number)
        old=(self.game/"Kanto pilot.json").read_bytes()
        user=self.game/"Data/blue-music.rxdata"
        user.write_bytes(b"legacy Decades user preferences")
        content,report=self.compile()
        self.assertEqual(report["real_map_ids"]["PALLET_TOWN"],705)
        self.assertFalse((self.game/compiler.OUTPUT).exists())
        compiler.write_safely(self.project,self.game,content)
        self.assertEqual((self.game/"Kanto pilot.json").read_bytes(),old)
        self.assertEqual(user.read_bytes(),b"legacy Decades user preferences")

    def test_unproven_event_must_not_be_activated(self):
        row=next(x for x in self.rules["events"] if x["event"]=="jackpot")
        row["enabled"]=True
        self.write_rules()
        with self.assertRaisesRegex(ValueError,"Unverified Kanto ME event"):
            self.compile()
        with self.assertRaisesRegex(ValueError,"Unverified Kanto ME"):
            compiler.phase4_track_numbers(self.project)

    def test_wrong_kind_and_duplicate_MEs_are_rejected(self):
        self.rules["events"][0]["track"]=11  # Looping trainer battle BGM.
        self.write_rules()
        with self.assertRaisesRegex(ValueError,"Unknown Kanto ME"):
            self.compile()
        self.rules["events"][0]["track"]=1
        self.rules["events"].append(dict(self.rules["events"][1]))
        self.write_rules()
        with self.assertRaisesRegex(ValueError,"duplicate Kanto ME"):
            self.compile()

    def test_only_committed_kanto_pilot_events_have_explicit_audio(self):
        src=(ROOT/"scripts/regions/KantoPilot.rb").read_text(encoding="utf-8")
        self.assertEqual(src.count('BlueMusic.kanto_me_play("badge_awarded")'),8)
        self.assertEqual(src.count('BlueMusic.kanto_me_play("obtained_pokemon")'),2)
        self.assertEqual(src.count('BlueMusic.kanto_me_play("obtained_item")'),6)
        self.assertEqual(src.count('BlueMusic.kanto_me_play("healed")'),2)
        self.assertIn('return unless pbAddPokemonSilent(species, 5)',src)
        self.assertIn('return unless pbAddPokemonSilent(species, 25)',src)
        self.assertIn('elsif type == :BLUE_KANTO_LEADER_BLAINE && BlueRegions.award',src)
        self.assertIn('    unless $bag.add(:MASTERBALL, 1)',src)
        # No audio event is injected into a generic pickup failure, the
        # untouched source Safari preview or League guide menus.
        self.assertNotIn('BlueMusic.kanto_me_play("jackpot")',src)


if __name__=="__main__":
    unittest.main()
