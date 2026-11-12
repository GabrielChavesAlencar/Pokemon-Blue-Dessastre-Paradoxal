"""Johto phase 06 story regression: no RMXP maps, installation or ROM required."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoAzaleaRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby runtime is not installed")
    def test_slowpoke_well_kurt_rocket_bugsy_hive_cut_and_saves(self):
        commands = [
            "ruby", str(ROOT / "tests/johto_azalea_runtime.rb"),
            str(ROOT / "scripts/regions/JohtoPilot.rb"),
            str(ROOT / "scripts/regions/JohtoViolet.rb"),
            str(ROOT / "scripts/regions/JohtoAzalea.rb"),
        ]
        result = subprocess.run(
            commands, capture_output=True, text=True, encoding="utf-8",
            timeout=20, cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JOHTO_AZALEA_RUNTIME_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
