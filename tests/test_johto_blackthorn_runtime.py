"""Phase 12: run Blackthorn story logic against temporary Ruby game stubs."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoBlackthornRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby runtime unavailable")
    def test_ice_path_clair_dragon_master_rising_waterfall_and_isolation(self):
        command = [
            "ruby", str(ROOT / "tests/johto_blackthorn_runtime.rb"),
            str(ROOT / "scripts/regions/JohtoPilot.rb"),
            str(ROOT / "scripts/regions/JohtoBlackthorn.rb"),
        ]
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True,
            text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JOHTO_BLACKTHORN_RUNTIME_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
