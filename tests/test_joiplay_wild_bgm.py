"""Regression for the user-reported JoiPlay crash on entering tall grass."""
from __future__ import annotations
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JoiPlayWildMusicRegression(unittest.TestCase):
    def test_prepare_battle_uses_v21_public_opponent_party_api(self):
        source = (ROOT / "scripts/music/BlueMusic.rb").read_text(encoding="utf8")
        self.assertIn("BlueMusic.kanto_wild_kind(battle.pbParty(1))", source)
        self.assertNotIn("battle.party2", source)

    def test_music_hook_does_not_crash_on_real_battle_shape(self):
        ruby = shutil.which("ruby")
        if not ruby:
            self.skipTest("Ruby unavailable; static API test still runs")
        script = ROOT / "tests/kanto_music_battles.rb"
        result = subprocess.run(
            [ruby, str(script)], cwd=ROOT, capture_output=True, text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout + "\n" + result.stderr)
        self.assertIn("Normal wild encounter prepares without calling party2", result.stdout)
        self.assertIn("Kanto double wild with Legendary", result.stdout)
        self.assertIn("Trainer preparation keeps Kanto leader music", result.stdout)
        self.assertIn("Decades wild preparation does not use Kanto music", result.stdout)


if __name__ == "__main__":
    unittest.main()
