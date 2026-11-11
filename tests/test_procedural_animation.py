"""Static verification of opt-in procedural animation integration."""
import importlib.util
import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
OPTIONS = ROOT / "scripts" / "battle_options"

class ProceduralAnimationTests(unittest.TestCase):
    def test_ruby_syntax(self):
        ruby = shutil.which("ruby")
        if not ruby:
            self.skipTest("Ruby not installed on this test host")
        for name in ("ProceduralAnimation.rb", "Rules.rb", "Menus.rb"):
            result = subprocess.run([ruby, "-c", str(OPTIONS / name)],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_plugin_installs_with_battle_options(self):
        spec = importlib.util.spec_from_file_location("options_install", OPTIONS / "install.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIn("ProceduralAnimation.rb", module.FILES)
        meta = (OPTIONS / "meta.txt").read_text()
        self.assertIn("ProceduralAnimation.rb", meta)

    def test_no_bitmap_replacement_and_static_gate(self):
        source = (OPTIONS / "ProceduralAnimation.rb").read_text()
        self.assertIn("wrapper.length == 1", source)
        self.assertIn("count == 1", source)
        self.assertIn("DessastreParadoxal", source)
        self.assertIn("blue_procedural_restore", source)
        self.assertNotIn("Bitmap.new", source)

if __name__ == "__main__":
    unittest.main()
