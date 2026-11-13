"""Johto phase 13 battle/HoF state machine, isolated from the Game.exe."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoLeagueRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby runtime unavailable")
    def test_victory_road_elite_four_lance_hof_unlocks_and_kanto_isolation(self):
        command = [
            "ruby", str(ROOT / "tests/johto_league_runtime.rb"),
            str(ROOT / "scripts/regions/JohtoPilot.rb"),
            str(ROOT / "scripts/regions/JohtoLeague.rb"),
        ]
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True,
            text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JOHTO_LEAGUE_RUNTIME_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
