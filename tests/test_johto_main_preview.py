"""Regression tests for the strictly local, unapproved Johto early-access build.

No ROM, Game.exe launch, or licensed graphics are needed for these
transaction/guard tests. Native gameplay MUST be tested separately.
"""
from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "scripts/regions/johto_main_preview.py"
SPEC = importlib.util.spec_from_file_location("johto_main_preview_test", FILE)
preview = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preview)


class JohtoMainPreviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game = self.root / "game"
        (self.game / "Data").mkdir(parents=True)
        (self.game / "PBS").mkdir()
        (self.game / "Game.exe").write_bytes(b"unchanged")
        (self.game / "Data/MapInfos.rxdata").write_bytes(b"old-infos")
        (self.game / "Data/Tilesets.rxdata").write_bytes(b"old-tiles")
        (self.game / "PBS/map_connections.txt").write_bytes(b"old-connections")

    def fixture_overlay(self):
        return {
            "Data/MapInfos.rxdata": b"merged-infos",
            "Data/Tilesets.rxdata": b"merged-tiles",
            "PBS/map_connections.txt": b"merged-connections",
            "Data/Map600.rxdata": b"private-map",
            preview.PROOF: b'{"status":"EXPERIMENTAL_PRIVATE_UNVERIFIED"}',
            preview.READY: b"BLUE_JOHTO_PRIVATE_PREVIEW_V1",
        }

    def test_new_bark_audited_autorun_at_spawn_is_allowed(self):
        from server.ruby_marshal import RubyObject
        def event(name, trigger=3, sprite=b""):
            page = RubyObject("RPG::Event::Page", {
                "@trigger": trigger,
                "@graphic": RubyObject("RPG::Event::Page::Graphic", {
                    "@character_name": sprite
                })
            })
            return RubyObject("RPG::Event", {
                "@name": name, "@x": 6, "@y": 7, "@pages": [page]
            })
        original = RubyObject("RPG::Map", {
            "@events": {1: event(b"JH_NEW_GAME_PROFILE")}
        })
        # The original package's New Bark intro contains this autorun at
        # 674:6,7. Previously the importer rejected its own authored event.
        preview.assert_spawn_not_blocked(original)
        for replacement in (event(b"BLOCKING_NPC", 0, b"Actor1"),
                            event(b"JH_NEW_GAME_PROFILE", 0),
                            event(b"JH_NEW_GAME_PROFILE", 3, b"Actor1")):
            original.attrs["@events"][2] = replacement
            with self.assertRaisesRegex(ValueError, "Spawn do jogador bloqueado"):
                preview.assert_spawn_not_blocked(original)

    def test_hoenn_map_ids_are_never_included_in_preview(self):
        self.assertEqual(preview.STAGED_IDS, frozenset(range(600, 682)))
        self.assertEqual(preview.PREVIEW_IDS, frozenset(range(600, 700)))
        self.assertTrue(preview.PREVIEW_IDS.isdisjoint(set(range(700, 1000))))

    def test_invalid_private_archive_never_modifies_main_game(self):
        package = self.root / "fake.zip"
        package.write_bytes(b"not an audited package")
        before = (self.game / "Data/MapInfos.rxdata").read_bytes()
        with self.assertRaises((OSError, ValueError)):
            preview.build_overlay(self.game, package, self.root)
        self.assertEqual(before, (self.game / "Data/MapInfos.rxdata").read_bytes())
        self.assertFalse((self.game / preview.READY).exists())

    def test_dry_run_never_writes_game_or_saves(self):
        files = self.fixture_overlay()
        with patch.object(preview, "build_overlay", return_value=(files, {})):
            result = preview.install(self.game, self.root / "fake.zip", self.root, apply=False)
        self.assertEqual(result["status"], "PLAN_VALIDATED_NOT_INSTALLED")
        self.assertFalse((self.game / "Data/Map600.rxdata").exists())
        self.assertEqual((self.game / "Data/MapInfos.rxdata").read_bytes(), b"old-infos")
        self.assertFalse((self.game / preview.READY).exists())

    def test_transaction_backs_up_and_commits_marker_last(self):
        files = self.fixture_overlay()
        order = []
        original = preview.os.replace

        def record_replace(source, target):
            order.append(str(target))
            return original(source, target)

        with patch.object(preview, "build_overlay", return_value=(files, {})), \
             patch.object(preview.os, "replace", side_effect=record_replace):
            result = preview.install(self.game, self.root / "fake.zip", self.root, apply=True)
        self.assertEqual(result["status"], "EXPERIMENTAL_INSTALLED_NOT_NATIVE_TESTED")
        self.assertTrue(order[-1].endswith("blue-johto-preview-ready.txt"))
        self.assertEqual((self.game / "Data/MapInfos.rxdata").read_bytes(), b"merged-infos")
        self.assertEqual((self.game / "Data/Map600.rxdata").read_bytes(), b"private-map")
        backup = Path(result["backup_folder"])
        self.assertEqual((backup / "Data/MapInfos.rxdata").read_bytes(), b"old-infos")
        self.assertEqual((backup / "PBS/map_connections.txt").read_bytes(), b"old-connections")

    def test_transaction_rolls_back_partial_write(self):
        files = self.fixture_overlay()
        original = preview.os.replace
        count = 0

        def break_second(source, target):
            nonlocal count
            count += 1
            if count == 3:
                raise OSError("disk interrupted")
            return original(source, target)

        with patch.object(preview, "build_overlay", return_value=(files, {})), \
             patch.object(preview.os, "replace", side_effect=break_second):
            with self.assertRaisesRegex(OSError, "disk interrupted"):
                preview.install(self.game, self.root / "fake.zip", self.root, apply=True)
        self.assertEqual((self.game / "Data/MapInfos.rxdata").read_bytes(), b"old-infos")
        self.assertEqual((self.game / "Data/Tilesets.rxdata").read_bytes(), b"old-tiles")
        self.assertEqual((self.game / "PBS/map_connections.txt").read_bytes(), b"old-connections")
        self.assertFalse((self.game / "Data/Map600.rxdata").exists())
        self.assertFalse((self.game / preview.READY).exists())

    def test_does_not_overwrite_existing_map_or_johto_plugin(self):
        files = self.fixture_overlay()
        existing = self.game / "Data/Map600.rxdata"
        existing.write_bytes(b"another-region-map")
        with patch.object(preview, "build_overlay", return_value=(files, {})):
            with self.assertRaisesRegex(ValueError, "não sobrescrever"):
                preview.install(self.game, self.root / "fake.zip", self.root, apply=True)
        self.assertEqual(existing.read_bytes(), b"another-region-map")
        self.assertEqual((self.game / "Data/MapInfos.rxdata").read_bytes(), b"old-infos")
        self.assertFalse((self.game / preview.READY).exists())

    def test_ch03_foreign_sinnoh_maps_rejected_before_any_write(self):
        original_infos = (self.game / "Data/MapInfos.rxdata").read_bytes()
        for extra in ("Data/Map800.rxdata", "Data/Map805.rxdata",
                      "Data/Map700.rxdata", "Data/Map1000.rxdata"):
            for apply in (False, True):
                with self.subTest(extra=extra, apply=apply):
                    files = self.fixture_overlay()
                    files[extra] = b"foreign-sinnoh-or-other-region"
                    with patch.object(preview, "build_overlay", return_value=(files, {})):
                        with self.assertRaisesRegex(ValueError, "MapID"):
                            preview.install(self.game, self.root / "fake.zip",
                                            self.root, apply=apply)
                    self.assertFalse((self.game / extra).exists())
                    self.assertFalse((self.game / preview.READY).exists())
                    self.assertFalse((self.root / ".blue-backups").exists())
                    self.assertEqual(
                        (self.game / "Data/MapInfos.rxdata").read_bytes(), original_infos
                    )

    def test_ch03_existing_hoenn_800_file_not_mistaken_for_new_sinnoh(self):
        # A different region may already own this number in the native game.
        original = self.game / "Data/Map800.rxdata"
        original.write_bytes(b"existing-Hoenn-map")
        with patch.object(preview, "build_overlay",
                          return_value=(self.fixture_overlay(), {})):
            result = preview.install(self.game, self.root / "fake.zip",
                                     self.root, apply=True)
        self.assertEqual(result["status"], "EXPERIMENTAL_INSTALLED_NOT_NATIVE_TESTED")
        self.assertEqual(original.read_bytes(), b"existing-Hoenn-map")
        self.assertTrue((self.game / "Data/Map600.rxdata").exists())

    def test_preview_proof_rejects_forged_marker_without_maps(self):
        (self.game / preview.PROOF).write_text(
            '{"schema":1,"region":"JOHTO","status":"EXPERIMENTAL_PRIVATE_UNVERIFIED",'
            '"source_bundle_sha256":"' + preview.PINNED_SHA + '",'
            '"map_ids":' + __import__("json").dumps(sorted(preview.PREVIEW_IDS)) + ','
            '"start":[674,6,7],"town":[600,10,26,2],"npc":[600,10,25,2],'
            '"file_hashes":{}}')
        (self.game / preview.READY).write_text("BLUE_JOHTO_PRIVATE_PREVIEW_V1,100")
        with self.assertRaises(ValueError):
            preview.preview_proof(self.game)


if __name__ == "__main__":
    unittest.main()
