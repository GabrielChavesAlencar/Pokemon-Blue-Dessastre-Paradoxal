"""Check Silver's 3 rival versions in pure Ruby, no Game.exe."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ThreeSilverVersionsRubyTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby interpreter unavailable")
    def test_3_starter_choices_rival_versions_and_save_guards(self):
        result = subprocess.run(
            ["ruby", str(ROOT / "tests/johto_rival_three_versions_runtime.rb"),
             str(ROOT / "scripts/regions/JohtoPilot.rb")],
            capture_output=True, text=True, encoding="utf-8",
            timeout=30, cwd=ROOT
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JOHTO_RIVAL_THREE_VERSIONS_GUARDS_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
