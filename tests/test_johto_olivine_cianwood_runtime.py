"""Phase 09: run isolated Ruby rules for Olivine, Lighthouse, Cianwood and Chuck."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoOlivineCianwoodRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby interpreter unavailable")
    def test_surf_travel_ampharos_medicine_chuck_storm_fly_and_save(self):
        command = [
            "ruby", str(ROOT / "tests/johto_olivine_cianwood_runtime.rb"),
            str(ROOT / "scripts/regions/JohtoPilot.rb"),
            str(ROOT / "scripts/regions/JohtoOlivineCianwood.rb")
        ]
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True,
            text=True, encoding="utf-8", timeout=20
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JOHTO_OLIVINE_CIANWOOD_RUNTIME_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
