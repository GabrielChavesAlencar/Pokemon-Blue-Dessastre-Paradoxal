"""Phase 3: battle/victory BGM only on compiled Kanto scope; factory-pool detection."""
from __future__ import annotations
import hashlib
import json
from test_kanto_music_phase1 import KantoMusicPhaseOneTests
from scripts.music import compile_kanto_music as compiler


class PhaseThreeMusicTests(KantoMusicPhaseOneTests):
    def test_eight_battle_victory_rules_require_exact_mp3s(self):
        enabled = [x for x in self.rules["battles"] if x["enabled"]]
        self.assertGreaterEqual(self.rules["phase"], 3)
        self.assertEqual(len(enabled),8)
        self.assertEqual({x["category"] for x in enabled},
                         {"wild","trainer","gym","legendary","champion",
                          "wildVictory","trainerVictory","gymVictory"})
        self.assertEqual(compiler.phase3_track_numbers(self.project),
                         {11,12,18,19,27,28,53,70})
        self.assertEqual(len(compiler.phase2_track_numbers(self.project)),17)
        self.assertEqual(len(compiler.approved_track_numbers(self.project)),25)
        self.assertEqual(sum(x["enabled"] for x in self.rules["events"]),6)
        self.assertFalse(any(x["enabled"] for x in self.rules["scenes"]))

    def test_all_25_assets_activate_eight_battles_and_keep_phase2(self):
        for number in compiler.approved_track_numbers(self.project):
            self.add_music(number)
        data, report = self.compile()
        lines = data.decode("utf-8").splitlines()
        self.assertEqual(report["active_map_bindings"],49)
        self.assertEqual(report["active_transport_bindings"],2)
        self.assertEqual(report["active_battle_bindings"],8)
        self.assertEqual(report["default_global_pool_signatures"],3)
        # This fixture installs only the 25 BGM; six verified ME are absent.
        self.assertEqual(len(report["missing_audio"]),6)
        self.assertTrue(all(x.startswith("ME/Kanto/") for x in report["missing_audio"]))
        self.assertEqual(len([x for x in lines if x.startswith("BATTLE\t")]),8)
        self.assertEqual(len([x for x in lines if x.startswith("BASEPOOL\t")]),3)
        self.assertFalse(any(x.startswith("ME\t") for x in lines))
        for row in self.rules["battles"]:
            match = [line for line in lines if line.startswith("BATTLE\t"+row["category"]+"\t")]
            self.assertEqual(len(match),1)
            self.assertIn("Kanto/",match[0])
        self.assertEqual({line.split("\t")[1] for line in lines
                          if line.startswith("BASEPOOL\t")},{"wild","trainer","gym"})

    def test_decades_global_defaults_signatures_match_real_factory_config(self):
        self.add_music(18)
        manifest,_=self.compile()
        rows={line.split("\t")[1]:line.split("\t")[2] for line in
              manifest.decode("utf-8").splitlines() if line.startswith("BASEPOOL\t")}
        defaults=self.read("data/shared-music.json")["config"]["global"]
        for key in ("wild","trainer","gym"):
            self.assertEqual(defaults[key]["mode"],"random")
            payload=[str(defaults[key]["volume"]),str(defaults[key]["pitch"]),*defaults[key]["tracks"]]
            self.assertEqual(rows[key],hashlib.sha256("\n".join(payload).encode("utf-8")).hexdigest())
        user=self.game/"Data/blue-music.rxdata"
        user.write_bytes(b"custom user config must never be mutated")
        out,_=self.compile()
        compiler.write_safely(self.project,self.game,out)
        self.assertEqual(user.read_bytes(),b"custom user config must never be mutated")

    def test_missing_legendary_mp3_omits_only_legendary_binding(self):
        for number in compiler.approved_track_numbers(self.project):
            if number!=53:
                self.add_music(number)
        data,report=self.compile()
        self.assertEqual(report["active_map_bindings"],49)
        self.assertEqual(report["active_battle_bindings"],7)
        self.assertIn("Kanto/1-53. Battle! (Legendary Pokémon).mp3",report["missing_audio"])
        self.assertNotIn("BATTLE\tlegendary\t",data.decode("utf-8"))

    def test_bad_battle_kind_or_duplicate_rule_rejected(self):
        row=self.rules["battles"][0]
        row["track"]=29  # Gym badge fanfare is ME, not looping battle BGM
        self.write_rules()
        with self.assertRaisesRegex(ValueError,"Unknown Kanto BGM"):
            self.compile()
        row["track"]=18
        self.rules["battles"].append(dict(row))
        self.write_rules()
        with self.assertRaisesRegex(ValueError,"duplicated|Invalid"):
            self.compile()

    def test_legacy_save_and_preview_never_create_map_or_state_changes(self):
        for number in compiler.approved_track_numbers(self.project):
            self.add_music(number)
        before=(self.game/"Kanto pilot.json").read_bytes()
        data,report=self.compile()
        self.assertEqual(report["source_maps"],142)
        self.assertEqual(report["preview_maps"],45)
        self.assertFalse((self.game/compiler.OUTPUT).exists())
        self.assertEqual((self.game/"Kanto pilot.json").read_bytes(),before)


if __name__=="__main__":
    import unittest
    unittest.main()
