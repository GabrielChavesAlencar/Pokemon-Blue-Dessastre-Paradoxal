"""Phase 10: execute real Johto Ruby story modules with a temporary mock bag."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoJasmineRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby runtime unavailable")
    def test_ampharos_consumption_jasmine_mineral_whirlpool_and_save(self):
        command = [
            "ruby", str(ROOT / "tests/johto_jasmine_runtime.rb"),
            str(ROOT / "scripts/regions/JohtoPilot.rb"),
            str(ROOT / "scripts/regions/JohtoOlivineCianwood.rb"),
            str(ROOT / "scripts/regions/JohtoJasmine.rb"),
        ]
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True,
            text=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JOHTO_JASMINE_RUNTIME_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
