"""Phase 11 Johto state machine regression using Ruby and mock battle adapters."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoMahoganyRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby interpreter unavailable")
    def test_lake_of_rage_rocket_hq_pryce_glacier_radio_and_saves(self):
        command = [
            "ruby", str(ROOT / "tests/johto_mahogany_runtime.rb"),
            str(ROOT / "scripts/regions/JohtoPilot.rb"),
            str(ROOT / "scripts/regions/JohtoMahogany.rb")
        ]
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True,
            text=True, encoding="utf-8", timeout=20
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JOHTO_MAHOGANY_RUNTIME_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
