"""Johto phase 14: isolate HGSS/Crystal legendary events from native game files."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoLegendariesRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby interpreter unavailable")
    def test_variants_roamers_kimono_legendary_rematches_ruins_and_saves(self):
        command = [
            "ruby", str(ROOT / "tests/johto_legendaries_runtime.rb"),
            str(ROOT / "scripts/regions/JohtoPilot.rb"),
            str(ROOT / "scripts/regions/JohtoLegendaries.rb"),
        ]
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True,
            text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JOHTO_LEGENDARIES_RUNTIME_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
