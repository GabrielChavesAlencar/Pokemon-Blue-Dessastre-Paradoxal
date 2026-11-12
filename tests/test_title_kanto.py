"""Verify that the downloaded Game.exe displays and dispatches Testar Kanto.

The runtime fixture emulates Essentials and the Decades Auto Multi Save
signature without touching the original saves or launching processes.
"""
import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts/battle_polish/TitleKanto.rb"


class TitleKantoTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("ruby"), "Ruby is required for title compatibility checks")
    def test_real_essentials_and_decades_command_contracts(self):
        result = subprocess.run(
            ["ruby", str(ROOT / "tests/title_kanto_runtime.rb"), str(SOURCE)],
            capture_output=True, text=True, encoding="utf-8", timeout=25
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Third title option", result.stdout)

    def test_installer_and_compiler_include_main_game_title_option(self):
        importer = (ROOT / "scripts/battle_polish/install.py").read_text("utf-8")
        metadata = (ROOT / "scripts/battle_polish/meta.txt").read_text("utf-8")
        setup = (ROOT / "scripts/battle_polish/Story.rb").read_text("utf-8")
        launcher = (ROOT / "KANTO_JOGAR_EXPERIMENTAL.bat").read_text("utf-8")
        assert "'TitleKanto.rb'" in importer, "Blue installer omitted new title plugin"
        assert "TitleKanto.rb" in metadata, "Plugin compilation metadata omitted menu script"
        assert "BlueKantoTitle.install" in setup, "Plugin was not activated"
        assert "ensure_source.py" in launcher, "Kanto launcher can't bootstrap source maps"
        assert "--launch-only" in launcher, "Experimental launch needs no Win32 window probe"
        self.assertNotIn("game\\data", launcher.lower(), "The pilot BAT must not overwrite main game saves")


if __name__ == "__main__":
    unittest.main()
