"""Run the private synthetic Johto trainer runtime test (no Game.exe)."""
from __future__ import annotations
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class JohtoRoutes10RubyTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby interpreter unavailable")
    def test_region_guards_normal_master_save_and_loss(self):
        result=subprocess.run(
            ["ruby",str(ROOT/"tests/johto_routes10_runtime.rb"),
             str(ROOT/"scripts/regions/JohtoRouteTrainers.rb")],
            cwd=ROOT,encoding="utf-8",text=True,capture_output=True,timeout=30
        )
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn("JOHTO_ROUTES10_OFFLINE_RUBY_GUARDS_OK",result.stdout)

if __name__=="__main__":
    unittest.main()
