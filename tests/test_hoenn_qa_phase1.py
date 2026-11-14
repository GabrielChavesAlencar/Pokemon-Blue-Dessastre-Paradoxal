"""Hoenn QA 01/12 safe staging tests, with NO game, ROM or donor assets."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import hoenn_qa_phase1 as qa


class HoennQA01Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name) / ".blue-work"
        self.game = Path(self.tmp.name) / "game"
        self.output = self.work / "hoenn-qa-fase01"

    def make_inventory(self):
        paths = {f"Data/Map{n:03}.rxdata" for n in qa.SOURCE_MAPS}
        paths.update(("Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
                      "PBS/map_connections.txt"))
        paths.update(f"Audio/BGM/ORAS {track}.ogg" for track in qa.BGM.values())
        return {"sha": qa.PINNED_TREE, "revision": qa.UPSTREAM,
                "truncated": False,
                "tree": [{"path": path, "type": "blob", "sha": "a" * 40}
                         for path in sorted(paths)]}

    def make_copy(self):
        self.game.mkdir()
        (self.game / "Game.exe").write_bytes(b"blue-native-exe-test-fixture")
        self.output.mkdir(parents=True)
        (self.output / "Game.exe").write_bytes(b"blue-native-exe-test-fixture")
        maps = {str(mid): 700 + i for i, mid in enumerate(qa.SOURCE_MAPS)}
        report = {"kind": "ISOLATED_HOENN_TEST", "source_commit": qa.UPSTREAM,
                  "save_profile": qa.PROFILE, "maps": maps}
        (self.output / "Hoenn pilot.json").write_text(json.dumps(report), encoding="utf8")
        data = self.output / "Data"
        data.mkdir()
        (data / "blue-hoenn-pilot.txt").write_text(
            "BLUE_HOENN_PILOT_V1\n708,25,6\n" +
            "".join(f"{mid},{new}\n" for mid, new in maps.items()),
            encoding="ascii")
        for new in maps.values():
            (data / f"Map{new:03}.rxdata").write_bytes(b"fixture")
        for rel in ("Data/System.rxdata", "Data/Scripts.rxdata",
                    "Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
                    "PBS/trainers_hoenn_pilot.txt",
                    "PBS/trainer_types_hoenn_pilot.txt",
                    "PBS/encounters_hoenn_pilot.txt",
                    "PBS/map_metadata_hoenn_pilot.txt",
                    "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb"):
            path = self.output / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf8")
        names = (
            "[BLUE_HOENN_JUAN,Juan,1087]",
            "[BLUE_HOENN_ARCHIE,Archie,1026]",
            "[BLUE_HOENN_WALLY,Wally,1025]",
            "[BLUE_HOENN_ELITE,Sidney,1094]",
            "[BLUE_HOENN_ELITE,Phoebe,1095]",
            "[BLUE_HOENN_ELITE,Glacia,1096]",
            "[BLUE_HOENN_ELITE,Drake,1097]",
            "[BLUE_HOENN_CHAMPION,Wallace,1098]",
        )
        (self.output / "PBS/trainers_hoenn_pilot.txt").write_text(
            "\n".join(names), encoding="utf8")
        (self.output / "mkxp.json").write_text(
            '{"dataPathApp": "' + qa.PROFILE + '"}', encoding="utf8")
        return maps

    def test_public_tree_requires_pinned_sha_and_199_maps(self):
        result = qa.check_tree(self.make_inventory())
        self.assertEqual(result["source_maps"], 199)
        self.assertEqual(result["revision"], qa.UPSTREAM)
        self.assertEqual(result["required_pinned_files"], 202 + len(qa.BGM))

    def test_missing_donor_map_is_blocker(self):
        tree = self.make_inventory()
        tree["tree"].pop()
        # Remove actual map, not just a generated audio name.
        tree["tree"] = [r for r in tree["tree"] if r["path"] != "Data/Map083.rxdata"]
        with self.assertRaisesRegex(ValueError, "sem.*recursos"):
            qa.check_tree(tree)

    def test_untrusted_tree_revision_and_truncation_fail(self):
        for field, value in (("revision", "0" * 40),
                             ("sha", "b" * 40), ("truncated", True)):
            with self.subTest(field=field):
                tree = self.make_inventory()
                tree[field] = value
                with self.assertRaisesRegex(ValueError, "incompleto|diferente"):
                    qa.check_tree(tree)

    def test_offline_requires_existing_tree_and_never_fetches(self):
        with patch.object(qa, "urlopen", side_effect=AssertionError("network called")):
            with self.assertRaisesRegex(FileNotFoundError, "offline"):
                qa.load_tree(self.work / "missing.json", offline=True)

    def test_output_must_remain_under_ignored_workdir(self):
        self.assertEqual(
            qa.require_private_path(self.work / "test.json", work=self.work),
            self.work / "test.json")
        for location in (self.game / "Game.exe", Path(self.tmp.name) / "outside",
                         self.work):
            with self.assertRaisesRegex(ValueError, ".blue-work"):
                qa.require_private_path(location, work=self.work)

    def test_verify_copy_with_199_maps_does_not_claim_native_approval(self):
        maps = self.make_copy()
        before = (self.game / "Game.exe").read_bytes()
        report = qa.verify_copy(self.output, self.game)
        self.assertEqual(report["maps_present"], 199)
        self.assertEqual(report["trainer_boss_pbs_entries"], 8)
        self.assertFalse(report["game_exe_tested"])
        self.assertFalse(report["gameplay_accepted"])
        self.assertEqual((self.game / "Game.exe").read_bytes(), before)
        self.assertEqual(len(maps), 199)

    def test_missing_remapped_map_fails_closed(self):
        maps = self.make_copy()
        (self.output / f"Data/Map{maps['83']:03}.rxdata").unlink()
        with self.assertRaisesRegex(ValueError, "sem 1 mapas"):
            qa.verify_copy(self.output, self.game)

    def test_bad_regional_marker_is_blocker(self):
        self.make_copy()
        marker = self.output / "Data/blue-hoenn-pilot.txt"
        marker.write_text("BLUE_HOENN_PILOT_V1\n708,25,6\n7,999\n", encoding="ascii")
        with self.assertRaisesRegex(ValueError, "Marcador"):
            qa.verify_copy(self.output, self.game)

    def test_missing_elite_team_is_blocker(self):
        self.make_copy()
        p = self.output / "PBS/trainers_hoenn_pilot.txt"
        p.write_text(p.read_text("utf8").replace(
            "[BLUE_HOENN_ELITE,Drake,1097]", ""), encoding="utf8")
        with self.assertRaisesRegex(ValueError, "Drake"):
            qa.verify_copy(self.output, self.game)

    def test_invalid_profile_and_modified_executable_are_blockers(self):
        self.make_copy()
        cfg = self.output / "mkxp.json"
        cfg.write_text('{"dataPathApp":"Decades"}', encoding="utf8")
        with self.assertRaisesRegex(ValueError, "Perfil"):
            qa.verify_copy(self.output, self.game)
        cfg.write_text('{"dataPathApp":"Hoenn Piloto"}', encoding="utf8")
        (self.output / "Game.exe").write_bytes(b"different-engine")
        with self.assertRaisesRegex(ValueError, "Game.exe"):
            qa.verify_copy(self.output, self.game)

    def test_existing_copy_is_verified_without_rebuild(self):
        self.make_copy()
        from argparse import Namespace
        args = Namespace(game=self.game, archive=Path(self.tmp.name)/"missing.zip",
                         inventory=self.work/"tree.json", output=self.output,
                         report=self.work/"status.json", prepare=True, offline=True)
        with patch.object(qa, "check_game", return_value={"ok": True}), \
             patch.object(qa, "require_private_path", side_effect=lambda p: p), \
             patch.object(qa, "stage", side_effect=AssertionError("stage re-run")):
            result = qa.build(args)
        self.assertEqual(result["status"], "COPY_READY_FOR_NATIVE_TEST")
        self.assertFalse(result["phase_fully_approved"])

    def test_no_archive_prevents_preparation_or_private_asset_upload(self):
        from argparse import Namespace
        args = Namespace(game=self.game, archive=Path(self.tmp.name)/"missing.zip",
                         inventory=self.work/"tree.json", output=self.output,
                         report=self.work/"status.json", prepare=True, offline=True)
        with patch.object(qa, "check_game", return_value={"ok": True}), \
             patch.object(qa, "require_private_path", side_effect=lambda p: p):
            with self.assertRaises(FileNotFoundError):
                qa.build(args)
        self.assertFalse(self.output.exists())
        self.assertFalse((self.work/"hoenn-source").exists())


if __name__ == "__main__":
    unittest.main()
