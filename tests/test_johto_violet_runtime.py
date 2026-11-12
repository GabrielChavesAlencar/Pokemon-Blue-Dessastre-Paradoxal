"""Validate Johto Violet/Falkner story without requiring a game distribution."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoVioletRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby runtime is not installed")
    def test_sprout_falkner_badge_emerald_fields_saves_and_region_isolation(self):
        args = [
            "ruby", str(ROOT / "tests/johto_violet_runtime.rb"),
            str(ROOT / "scripts/regions/JohtoPilot.rb"),
            str(ROOT / "scripts/regions/JohtoViolet.rb"),
        ]
        result = subprocess.run(
            args, cwd=ROOT, capture_output=True, text=True,
            encoding="utf-8", timeout=20
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JOHTO_VIOLET_RUNTIME_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
