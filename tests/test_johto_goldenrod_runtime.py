"""Validate phase 07 Johto quest flow without maps or a game distribution."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoGoldenrodRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby interpreter unavailable")
    def test_ilex_cut_radio_whitney_plain_sudowoodo_saves_and_isolation(self):
        command = [
            "ruby", str(ROOT / "tests/johto_goldenrod_runtime.rb"),
            str(ROOT / "scripts/regions/JohtoPilot.rb"),
            str(ROOT / "scripts/regions/JohtoAzalea.rb"),
            str(ROOT / "scripts/regions/JohtoGoldenrod.rb")
        ]
        result = subprocess.run(
            command, capture_output=True, text=True, encoding="utf-8",
            timeout=20, cwd=ROOT
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JOHTO_GOLDENROD_RUNTIME_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
