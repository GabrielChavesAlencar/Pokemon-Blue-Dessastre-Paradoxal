"""Offline save-safe tests for updating Kanto's installed Ruby plugin only."""
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REGIONS = ROOT / "scripts/regions"
sys.path.insert(0, str(REGIONS))
try:
    spec = importlib.util.spec_from_file_location("blue_installed_kanto", REGIONS / "install_kanto.py")
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
finally:
    sys.path.remove(str(REGIONS))


def sha(data):
    return hashlib.sha256(data).hexdigest()


class RuntimeSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="kanto-runtime-update-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "game"
        self.plugin_rel = Path("Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb")
        self.plugin = self.game / self.plugin_rel
        self.plugin.parent.mkdir(parents=True)
        (self.root / "scripts/regions").mkdir(parents=True)
        self.source = self.root / "scripts/regions/KantoPilot.rb"
        (self.game / "Data").mkdir(parents=True)
        self.plugin.write_bytes(b"# original Kanto runtime\n")
        self.source.write_bytes(b"# Kanto runtime updated by maintainer\n")
        self.manifest = self.game / "Data/blue-kanto-install.json"
        self.manifest.write_text(json.dumps({
            "schema": 1, "source": "Essentials FRLG 21.1",
            "maps": {"7": 300}, "installed_sha256": {
                str(self.plugin_rel): sha(self.plugin.read_bytes())
            },
        }), encoding="utf8")
        self.existing_save = self.game / "Save.rxdata"
        self.existing_save.write_bytes(b"do not touch save")
        self.compiled = self.game / "Data/PluginScripts.rxdata"
        self.compiled.write_bytes(b"old compiled scripts")
        self.patcher_root = patch.object(installer, "ROOT", self.root)
        self.patcher_verify = patch.object(installer, "verify_installed", return_value={"maps": 142})
        self.patcher_root.start()
        self.patcher_verify.start()
        self.addCleanup(self.patcher_root.stop)
        self.addCleanup(self.patcher_verify.stop)

    def test_preview_does_not_change_game(self):
        info = installer.sync_runtime(self.game)
        self.assertEqual(info["status"], "runtime_update_preview")
        self.assertEqual(self.plugin.read_bytes(), b"# original Kanto runtime\n")
        self.assertEqual(self.compiled.read_bytes(), b"old compiled scripts")

    def test_safe_update_backs_up_plugin_and_recompiles(self):
        info = installer.sync_runtime(self.game, commit=True)
        self.assertEqual(info["status"], "runtime_updated")
        self.assertEqual(self.plugin.read_bytes(), self.source.read_bytes())
        manifest = json.loads(self.manifest.read_text())
        self.assertEqual(manifest["installed_sha256"][str(self.plugin_rel)],
                         sha(self.source.read_bytes()))
        backup = Path(info["backup"])
        self.assertEqual((backup / self.plugin_rel).read_bytes(),
                         b"# original Kanto runtime\n")
        self.assertFalse(self.compiled.exists())
        self.assertEqual((self.game / "Data/blue-compile-request.txt").read_bytes(),
                         b"compile")
        self.assertEqual(self.existing_save.read_bytes(), b"do not touch save")
        self.assertEqual(installer.sync_runtime(self.game)["status"], "runtime_current")

    def test_locally_edited_plugin_blocks_overwrite(self):
        self.plugin.write_bytes(b"# modified by player\n")
        with self.assertRaisesRegex(ValueError, "edited locally"):
            installer.sync_runtime(self.game, commit=True)
        self.assertEqual(self.plugin.read_bytes(), b"# modified by player\n")
        self.assertEqual(self.existing_save.read_bytes(), b"do not touch save")


if __name__ == "__main__":
    unittest.main()
