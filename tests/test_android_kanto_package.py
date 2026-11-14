"""Regression checks for the Kanto-specific JoiPlay release gate."""
import hashlib
import json
import tempfile
import zlib
from scripts.official_rules.prepare_restore import RubyString, dump
from scripts.android.early_input import EARLY_BOOTSTRAP
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.android import package_kanto as k

SHA = "a" * 40


class KantoJoiPlayPackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.game = Path(self.tmp.name) / "pilot"
        self.output = Path(self.tmp.name) / k.ASSET
        self.game.mkdir()
        manifest = json.loads((k.ROOT / "data/regions/kanto-source.json").read_text(encoding="utf8"))["maps"]
        self.mapping = {source: 600 + index for index, source in enumerate(manifest)}
        self.meta = {"save_app": "Kanto Piloto", "save_org": "Dessastre Paradoxal Kanto Testes",
                     "maps": self.mapping}
        self.write("Kanto pilot.json", json.dumps(self.meta))
        self.write("Game.exe", "exe")
        self.write("Game.ini", "Title=Kanto Piloto\n")
        self.write("mkxp.json", '// mkxp-z aceita comentários na configuração\n{\n  // não confundir com esta linha:\n  // "dataPathApp": "Decades",\n  "dataPathApp": "Kanto Piloto", "dataPathOrg": "Dessastre Paradoxal Kanto Testes"\n}\n')
        self.write("Data/blue-kanto-start.txt", "BLUE_KANTO_START_V1,KANTO," + str(self.mapping["7"]) + ",25,7\n")
        for file in k.CORE_FILES:
            if file not in {"Kanto pilot.json", "Game.exe", "Game.ini", "mkxp.json",
                            "Data/blue-kanto-start.txt"}:
                self.write(file, "stub")
        for mid in self.mapping.values():
            self.write(f"Data/Map{mid:03d}.rxdata", "map")
        # The actual JoiPlay ZIP carries an RGSS Input script, not a stub.
        scripts = [[1, RubyString(b"Input"),
                    RubyString(zlib.compress((EARLY_BOOTSTRAP + "module Input; end\n").encode("utf8")))]]
        (self.game / "Data/Scripts.rxdata").write_bytes(b"\x04\x08" + dump(scripts))
        self.write("Data/blue-android-compiled.txt", "expected")
        self.write("Data/blue-kanto-proof.txt", "CI diagnostic must not be shipped")
        self.write("Data/blue-kanto-failure.log", "CI diagnostic must not be shipped")

    def write(self, name, content):
        path = self.game / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content.encode("utf8"))

    def test_mkxp_json_with_comments_and_no_save_overlap(self):
        config = (self.game / "mkxp.json").read_text(encoding="utf8")
        self.assertTrue(k._kanto_save_profile(config))
        self.assertFalse(k._kanto_save_profile(config.replace('"dataPathApp": "Kanto Piloto"', '"dataPathApp": "Decades"')))
        self.assertFalse(k._kanto_save_profile(config.replace('"dataPathOrg"', '"dataPathApp": "Kanto Piloto", "dataPathOrg"')))

    def test_refuses_main_game_without_pilot_marker(self):
        (self.game / "Kanto pilot.json").unlink()
        with self.assertRaisesRegex(ValueError, "metadata"):
            k._metadata(self.game)

    def test_refuses_missing_kanto_map(self):
        (self.game / f"Data/Map{self.mapping['5']:03d}.rxdata").unlink()
        with self.assertRaisesRegex(ValueError, "Kanto map"):
            k._metadata(self.game)

    def test_does_not_select_test_diagnostics_or_saves(self):
        self.write("Data/Game.rxdata", "save")
        self.write("Saves/Auto 1.rxdata", "save")
        selected = k.select_files(self.game)
        self.assertIn("Kanto pilot.json", selected)
        self.assertIn("Data/blue-kanto-start.txt", selected)
        self.assertIn("Data/blue-kanto-npc-dialogues.dat", selected)
        self.assertIn("Data/blue-pt-br.dat", selected)
        self.assertNotIn("Data/Game.rxdata", selected)
        self.assertNotIn("Saves/Auto 1.rxdata", selected)
        self.assertNotIn("Data/blue-kanto-proof.txt", selected)
        self.assertNotIn("Data/blue-kanto-failure.log", selected)

    def test_build_and_verify_with_mock_native_compilation(self):
        def checked(game):
            return ("expected", "mobile-sha")
        with patch.object(k, "_metadata", return_value=self.meta), patch.object(k, "_compiled", side_effect=checked), patch.object(k, "compiled_mobile", return_value="mobile-sha"), patch.object(k, "compiled_kanto", return_value="kanto-sha"):
            result = k.build(self.game, self.output, SHA)
            self.assertEqual(result["revision"], SHA)
            self.assertEqual(k.verify_archive(self.output, SHA)["maps"], len(self.mapping))
        import zipfile
        with zipfile.ZipFile(self.output) as archive:
            self.assertEqual(archive.read(k.FOLDER + "Data/blue-mobile.txt"), b"experimental-v1\n")
            self.assertIn(k.FOLDER + "Data/Scripts.rxdata", archive.namelist())
            self.assertIn(k.FOLDER + "ATUALIZAR-ANDROID.py", archive.namelist())
        # A ZIP with the Mobile.rb compiled but without the enabling marker
        # must be rejected (this reproduced Input line 28 on real JoiPlay).
        import zipfile
        broken = Path(self.tmp.name) / "missing-mobile.zip"
        with zipfile.ZipFile(self.output) as source, zipfile.ZipFile(broken, "w") as target:
            for entry in source.infolist():
                if entry.filename != k.FOLDER + "Data/blue-mobile.txt":
                    target.writestr(entry, source.read(entry.filename))
        with patch.object(k, "compiled_mobile", return_value="mobile-sha"), patch.object(k, "compiled_kanto", return_value="kanto-sha"):
            with self.assertRaisesRegex(KeyError, "blue-mobile.txt"):
                k.verify_archive(broken, SHA)
        self.assertTrue(self.output.with_name(self.output.name + ".sha256").is_file())
        with self.assertRaisesRegex(ValueError, "Existing"):
            with patch.object(k, "_metadata", return_value=self.meta), patch.object(k, "_compiled", side_effect=checked):
                k.build(self.game, self.output, SHA)
        with patch.object(k, "compiled_mobile", return_value="mobile-sha"), patch.object(k, "compiled_kanto", return_value="kanto-sha"):
            with self.assertRaisesRegex(ValueError, "revision"):
                k.verify_archive(self.output, "b" * 40)


class KantoBootstrapCompatibilityTests(unittest.TestCase):
    def test_kanto_start_is_not_blocked_by_missing_ruby_stdlib(self):
        runtime = (k.ROOT / "scripts/battle_polish/RegionStart.rb").read_text(encoding="utf8")
        self.assertFalse(runtime.lstrip().startswith('require "json"'))
        self.assertIn('def self.johto_install_proof', runtime)
        self.assertIn('require "json" unless defined?(JSON)', runtime)
        self.assertIn('require "digest" unless defined?(Digest::SHA256)', runtime)
        self.assertIn('rescue LoadError', runtime)
        self.assertIn('def self.kanto_spawn', runtime)


if __name__ == "__main__":
    unittest.main()
