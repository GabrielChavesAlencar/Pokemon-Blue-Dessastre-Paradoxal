"""Phase 08: run Johto Ecruteak story guards using the real Ruby modules."""
from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoEcruteakRuntimeTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby interpreter unavailable")
    def test_routes_burned_tower_rival_morty_fog_surf_save_and_isolation(self):
        command = [
            "ruby", str(ROOT / "tests/johto_ecruteak_runtime.rb"),
            str(ROOT / "scripts/regions/JohtoPilot.rb"),
            str(ROOT / "scripts/regions/JohtoEcruteak.rb")
        ]
        result = subprocess.run(
            command, cwd=ROOT, capture_output=True,
            text=True, encoding="utf-8", timeout=20
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("JOHTO_ECRUTEAK_RUNTIME_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
