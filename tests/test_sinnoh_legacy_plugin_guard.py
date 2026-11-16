"""CH04 negative regressions for the legacy standalone Sinnoh plugin."""
from __future__ import annotations
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts.regions.sinnoh_legacy_plugin_guard import (
    assert_no_legacy_sinnoh_overlay, assert_no_legacy_sinnoh_shared,
)

ROOT = Path(__file__).resolve().parents[1]


class SinnohLegacyPluginTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "game"
        (self.game / "Plugins/Blue Main").mkdir(parents=True)
        (self.game / "Data").mkdir()
        (self.game / "Data/Map800.rxdata").write_bytes(b"existing Hoenn map")
        (self.game / "Plugins/Blue Main/meta.txt").write_bytes(
            b"Name = Blue Main\nScripts = Boot.rb\n")

    def create(self, rel, value=b"unchanged"):
        path = self.game / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        return path

    def test_normal_main_and_hoenn_id800_are_allowed(self):
        assert_no_legacy_sinnoh_shared(self.game)
        assert_no_legacy_sinnoh_shared(self.root / "absent")
        self.create("Plugins/Blue Main/SinnohPilot.rb", b"module BlueSinnohPilot\nend")
        assert_no_legacy_sinnoh_shared(self.game)

    def test_rejects_old_plugin_under_original_or_renamed_folder(self):
        for rel, value in (
            ("Plugins/ZZZZZ Blue Sinnoh Pilot/SinnohPreview.rb", b"legacy"),
            ("Plugins/Other/SinnohPreview.rb", b"legacy"),
            ("Plugins/Other/Renamed.rb", b"module BlueSinnohPreview\nend\n"),
            ("Plugins/Other/meta.txt", b"Scripts = SinnohPreview.rb\n"),
        ):
            with self.subTest(path=rel):
                path = self.create(rel, value)
                with self.assertRaisesRegex(ValueError, "não permitido"):
                    assert_no_legacy_sinnoh_shared(self.game)
                path.unlink()
        (self.game / "Plugins/ZZZZZ Blue Sinnoh Pilot").mkdir(exist_ok=True)
        with self.assertRaisesRegex(ValueError, "não permitido"):
            assert_no_legacy_sinnoh_shared(self.game)

    def test_markers_and_profiles_block_without_writes(self):
        for rel, value in (
            ("Sinnoh pilot.json", b"{}"),
            ("Data/blue-sinnoh-compile-request.txt", b"compiled"),
            ("Data/blue-sinnoh-compiled.txt", b"compiled"),
            ("Data/blue-sinnoh-rival-ready.txt", b"ready"),
            ("Data/blue-sinnoh-qa-engine-check.json", b"{}"),
            ("Game.ini", b"[Game]\nTitle=Sinnoh Piloto\n"),
            ("mkxp.json", b'{"dataPathApp":"Sinnoh Piloto"}'),
        ):
            with self.subTest(path=rel):
                path = self.create(rel, value)
                with self.assertRaisesRegex(ValueError, "não permitido"):
                    assert_no_legacy_sinnoh_shared(self.game)
                self.assertEqual(path.read_bytes(), value)
                path.unlink()

    def test_case_insensitive_data_directory_and_marker_names(self):
        for rel in ("DATA/BLUE-SINNOH-COMPILE-REQUEST.TXT",
                    "Data/BLUE-SINNOH-COMPILED.TXT"):
            with self.subTest(path=rel):
                path = self.create(rel, b"legacy marker")
                with self.assertRaisesRegex(ValueError, "não permitido"):
                    assert_no_legacy_sinnoh_shared(self.game)
                self.assertEqual(path.read_bytes(), b"legacy marker")
                path.unlink()

    def test_rejects_suspicious_shared_overlays(self):
        for rel, content in (
            ("Plugins/Other/SinnohPreview.rb", b"legacy"),
            ("Plugins/Other/Renamed.rb", b"module BlueSinnohPreview\nend"),
            ("Plugins/Other/meta.txt", b"Scripts = SinnohPreview.rb\n"),
            ("Sinnoh pilot.json", b"{}"),
            ("Data/blue-sinnoh-compile-request.txt", b"compile"),
            ("Game.ini", b"Title=Sinnoh Piloto\n"),
            ("mkxp.json", b'{"dataPathApp":"Sinnoh Piloto"}'),
            ("Data/Scripts.rxdata", b"legacy"),
        ):
            with self.subTest(path=rel), self.assertRaisesRegex(ValueError, "não permitido"):
                assert_no_legacy_sinnoh_overlay({rel: content})
        assert_no_legacy_sinnoh_overlay({
            "Data/Map800.rxdata": b"Hoenn can own this",
            "Plugins/New/SinnohPilot.rb": b"module BlueSinnohPilot\nend",
        })

    def test_main_installer_preflight_before_download_or_writes(self):
        spec = importlib.util.spec_from_file_location(
            "ch04_install_game", ROOT / "scripts/install_game.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        old = self.create("Plugins/Other/SinnohPreview.rb")
        with patch.object(mod, "ensure_base", side_effect=AssertionError("base changed")):
            with self.assertRaisesRegex(ValueError, "não permitido"):
                mod.install(self.root, self.game, hub_only=True)
        self.assertEqual(old.read_bytes(), b"unchanged")
        self.assertFalse((self.root / ".blue-work").exists())

    def test_campaign_launcher_blocks_before_plugin_install(self):
        spec = importlib.util.spec_from_file_location(
            "ch04_launch_game", ROOT / "scripts/launch_game.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.create("Data/blue-sinnoh-compile-request.txt")
        with patch.object(mod.importlib.util, "spec_from_file_location",
                          side_effect=AssertionError("plugin install attempted")):
            with self.assertRaisesRegex(ValueError, "não permitido"):
                mod.prepare(self.root, self.game)

    def test_legacy_standalone_builder_remains_unchanged(self):
        source = (ROOT / "scripts/regions/pilot_sinnoh.py").read_text("utf-8")
        self.assertIn("IDS = dict(zip(NAMES, range(800, 806)))", source)
        self.assertIn('overlay[f"{PLUGIN}/SinnohPreview.rb"]', source)
        self.assertIn("install_copy(pending, game, output, overlay)", source)
        self.assertNotIn("assert_no_legacy_sinnoh_shared", source)


if __name__ == "__main__":
    unittest.main()
