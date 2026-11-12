"""Run isolated Ruby story checks for the future Johto map pilot."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoStoryRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby interpreter unavailable")
    def test_starters_elm_rival_region_isolation_and_save_reload(self):
        result = subprocess.run(
            ["ruby", str(ROOT / "tests/johto_pilot_runtime.rb"),
             str(ROOT / "scripts/regions/JohtoPilot.rb")],
            capture_output=True, text=True, encoding="utf-8", timeout=20,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JOHTO_PILOT_STORY_GUARDS_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
