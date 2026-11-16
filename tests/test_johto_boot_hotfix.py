"""An already-installed Johto preview must update Boot.rb without reinstalling maps."""
from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "scripts/regions/johto_main_preview.py"
SPEC = importlib.util.spec_from_file_location("johto_boot_hotfix_test", FILE)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class JohtoBootHotfixTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.game = self.folder / "game"
        self.root = self.folder
        for directory in ("Data", "PBS", mod.PLUGIN, "Saves"):
            (self.game / directory).mkdir(parents=True, exist_ok=True)
        self.existing_plugin = b"module CompilerHook; def main; super; end; end\n"
        self.write(f"{mod.PLUGIN}/Boot.rb", self.existing_plugin)
        self.write("PBS/map_connections.txt", b"original-regional-connections")
        self.write("PBS/map_metadata_johto_main.txt", b"Johto metadata")
        self.write("Data/MapInfos.rxdata", b"Decades+Kanto+Hoenn+Johto infos")
        self.write("Data/Tilesets.rxdata", b"native tilesets")
        self.write("Saves/File A.rxdata", b"do not touch this user save")
        names = [
            f"{mod.PLUGIN}/Boot.rb",
            "Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
            "PBS/map_connections.txt", "PBS/map_metadata_johto_main.txt",
        ]
        for mid in sorted(mod.PREVIEW_IDS):
            relative = f"Data/Map{mid:03}.rxdata"
            self.write(relative, f"JOHTO MAP {mid}".encode())
            names.append(relative)
        self.write(mod.READY, ("BLUE_JOHTO_PRIVATE_PREVIEW_V1,100," +
                              ",".join(map(str, (*mod.START, *mod.TOWN[:3], *mod.NPC[:3]))) +
                              "\n").encode("ascii"))
        self.proof = {
            "schema": 1, "region": "JOHTO", "status": mod.STATUS,
            "source_bundle_sha256": mod.PINNED_SHA,
            "map_ids": sorted(mod.PREVIEW_IDS), "start": list(mod.START),
            "town": list(mod.TOWN), "npc": list(mod.NPC),
            "file_hashes": {
                name: mod.sha((self.game / name).read_bytes()) for name in names
            },
        }
        self.write(mod.PROOF, mod.raw_json(self.proof))

    def write(self, name, blob):
        p = self.game / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)

    def test_hotfix_updates_copied_plugin_only(self):
        before_map = (self.game / "Data/Map600.rxdata").read_bytes()
        before_infos = (self.game / "Data/MapInfos.rxdata").read_bytes()
        before_save = (self.game / "Saves/File A.rxdata").read_bytes()
        self.assertIsNotNone(mod.preview_proof(self.game))
        result = mod.refresh_installed_runtime(self.game, ROOT)
        self.assertTrue(result["changed"])
        installed_boot = (self.game / mod.PLUGIN / "Boot.rb").read_bytes()
        self.assertNotIn(b"Compiler.singleton_class.prepend(", installed_boot)
        self.assertIn(b"blue_johto_main_compile_status", installed_boot)
        self.assertEqual((self.game / "Data/Map600.rxdata").read_bytes(), before_map)
        self.assertEqual((self.game / "Data/MapInfos.rxdata").read_bytes(), before_infos)
        self.assertEqual((self.game / "Saves/File A.rxdata").read_bytes(), before_save)
        self.assertEqual(mod.preview_proof(self.game)["runtime_hotfix"],
                         "johto-compiler-no-prepend-v2")
        backup = Path(result["backup_folder"])
        self.assertEqual((backup / mod.PLUGIN / "Boot.rb").read_bytes(),
                         self.existing_plugin)
        self.assertEqual(mod.refresh_installed_runtime(self.game, ROOT)["changed"], False)

    def test_rollback_when_second_file_swap_fails(self):
        original_manifest = (self.game / mod.PROOF).read_bytes()
        original_boot = (self.game / mod.PLUGIN / "Boot.rb").read_bytes()
        original_replace = mod.os.replace
        count = 0

        def fail_on_manifest(source, destination):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError("simulate interrupted manifest commit")
            return original_replace(source, destination)

        with patch.object(mod.os, "replace", side_effect=fail_on_manifest):
            with self.assertRaisesRegex(OSError, "interrupted"):
                mod.refresh_installed_runtime(self.game, ROOT)
        self.assertEqual((self.game / mod.PROOF).read_bytes(), original_manifest)
        self.assertEqual((self.game / mod.PLUGIN / "Boot.rb").read_bytes(), original_boot)
        self.assertIsNotNone(mod.preview_proof(self.game))

    def test_untrusted_modified_plugin_denied(self):
        self.write(f"{mod.PLUGIN}/Boot.rb", b"tampered by another installer")
        with self.assertRaisesRegex(ValueError, "alterado|inexistente|Arquivo de Johto"):
            mod.refresh_installed_runtime(self.game, ROOT)
        self.assertIn(b"tampered", (self.game / mod.PLUGIN / "Boot.rb").read_bytes())

    def test_no_johto_manifest_does_not_modify_game(self):
        (self.game / mod.PROOF).unlink()
        self.assertFalse(mod.refresh_installed_runtime(self.game, ROOT)["changed"])

    def test_no_compiler_alias_in_source(self):
        source = (ROOT / "scripts/regions/JohtoMainCompile.rb").read_text("utf-8")
        self.assertIn("EventHandlers.add(:on_enter_map", source)
        self.assertNotIn("Compiler.singleton_class.prepend(", source)


if __name__ == "__main__":
    unittest.main()
