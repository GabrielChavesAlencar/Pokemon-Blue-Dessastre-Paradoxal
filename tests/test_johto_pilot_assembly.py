"""Piloto Johto: testa montar cópia RMXP com dados SINTÉTICOS e saves separados."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from pilot_johto import assemble, plan, SAVE_APP, SAVE_ORG
    from audit_johto import checksum
    from stage import serialize
    from server.ruby_marshal import RubyObject
    from test_johto_event_build import make_fixture
finally:
    sys.path.pop(0)


def rmxp(class_name, **kwargs):
    return RubyObject(class_name, {"@" + k: v for k, v in kwargs.items()})


def make_game(root):
    game = root / "game"
    for dir_name in ("Audio", "Data", "Fonts", "Graphics", "PBS", "Plugins"):
        (game / dir_name).mkdir(parents=True)
    (game / "Graphics/Characters").mkdir()
    (game / "Graphics/Trainers").mkdir()
    for sprite in ("Graphics/Characters/Test_Character.png",
                   "Graphics/Trainers/RIVAL1.png"):
        (game / sprite).write_bytes(b"\x89PNG\r\n\x1a\n" + b"synthetic")
    (game / "Game.exe").write_bytes(b"synthetic exe is never executed")
    (game / "Game.ini").write_text("Title=Blue Test\n", encoding="utf-8")
    (game / "mkxp.json").write_text('{"windowTitle":"Blue Test"}', encoding="utf-8")
    (game / "Data/System.rxdata").write_bytes(
        serialize(rmxp("RPG::System", start_map_id=1, start_x=3, start_y=4),
                  {"RPG::System"}))
    (game / "Data/MapInfos.rxdata").write_bytes(
        serialize({1: rmxp("RPG::MapInfo", name=b"Decades")}))
    (game / "Data/Map001.rxdata").write_bytes(
        serialize(rmxp("RPG::Map", width=10, height=10,
                       tileset_id=1, events={})))
    old_tiles = [None, rmxp("RPG::Tileset", id=1),
                 rmxp("RPG::Tileset", id=2)]
    (game / "Data/Tilesets.rxdata").write_bytes(serialize(old_tiles))
    (game / "PBS/trainer_types.txt").write_text(
        "[RIVAL1]\nName = Rival\nGender = Male\nBaseMoney = 100\n"
        "SkillLevel = 50\n", encoding="utf-8")
    (game / "PBS/pokemon.txt").write_text(
        "[CHIKORITA]\nName = Chikorita\n"
        "[CYNDAQUIL]\nName = Cyndaquil\n"
        "[TOTODILE]\nName = Totodile\n", encoding="utf-8")
    (game / "PBS/trainers.txt").write_text(
        "[YOUNGSTER,Other]\nPokemon = RATTATA,5\n", encoding="utf-8")
    presentation = game / "Plugins/ZZZZ Blue Story and Presentation"
    presentation.mkdir()
    (presentation / "Regions.rb").write_text("module BlueRegions; end\n", "utf-8")
    return game


def make_prepared(root):
    preview, spec = make_fixture(root)
    game = make_game(root)
    data = preview / "Data"
    base_info = {1: rmxp("RPG::MapInfo", name=b"Decades")}
    merged = dict(base_info)
    for row in spec["maps"]:
        merged[row["map_id"]] = rmxp("RPG::MapInfo", name=row["symbol"].encode())
    (data / "MapInfos.rxdata").write_bytes(serialize(merged))
    (data / "Tilesets.rxdata").write_bytes(serialize(
        [None, rmxp("RPG::Tileset", id=1),
         rmxp("RPG::Tileset", id=2), rmxp("RPG::Tileset", id=3)]))
    stage_file = preview / "johto-stage.json"
    stage = json.loads(stage_file.read_text("utf-8"))
    stage["native_mapinfos_sha256"] = checksum(game / "Data/MapInfos.rxdata")
    stage["native_tilesets_sha256"] = checksum(game / "Data/Tilesets.rxdata")
    stage_file.write_text(json.dumps(stage), encoding="utf-8")
    spec["start"] = {
        "symbol": "JOHTO_NEW_BARK_PLAYER_HOME_2F",
        "x": 13, "y": 13, "verified_position": True,
        "passability_verified": True,
    }
    for rel in ("scripts/regions/JohtoPilot.rb",
                "scripts/regions/JohtoPilotStart.rb"):
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, path)
    return game, preview, spec


class JohtoPilotAssemblyTests(unittest.TestCase):
    def test_real_manifest_cannot_boot_without_start_positions(self):
        spec = json.loads((ROOT / "data/regions/johto-new-bark-events.json").read_text("utf-8"))
        self.assertIsNone(spec["start"]["x"])
        self.assertFalse(spec["start"]["verified_position"])
        self.assertFalse(spec["start"]["passability_verified"])

    def test_build_isolated_copy_preserves_main_game_and_save_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game, preview, spec = make_prepared(root)
            native = {p: checksum(game / p) for p in (
                "Data/System.rxdata", "Data/MapInfos.rxdata",
                "Data/Tilesets.rxdata", "PBS/trainers.txt")}
            destination = root / ".blue-work/johto-pilot"
            outcome = assemble(preview, game, destination, spec, root=root)
            self.assertEqual(outcome["status"], "EXPERIMENTAL_COPY_ASSEMBLED_UNTESTED")
            self.assertEqual(outcome["start"], [601, 13, 13])
            self.assertFalse(outcome["gameplay_verified"])
            self.assertTrue((destination / "Game.exe").is_file())
            self.assertTrue((destination / "Data/Map601.rxdata").is_file())
            self.assertTrue((destination / "Data/Map605.rxdata").is_file())
            self.assertTrue((destination / "PBS/trainers_johto.txt").is_file())
            self.assertTrue((destination / "Graphics/Trainers/BLUE_JOHTO_RIVAL.png").is_file())
            self.assertTrue((destination / "Plugins/ZZZZZ Blue Johto Pilot/JohtoPilotBoot.rb").is_file())
            self.assertFalse((destination / "Data/blue-johto-install.json").exists())
            self.assertFalse((destination / "Data/blue-johto-start.txt").exists())
            self.assertFalse((destination / "Data/blue-johto-rival-ready.txt").exists())
            self.assertEqual(native, {p: checksum(game / p) for p in native})
            mkxp = json.loads((destination / "mkxp.json").read_text("utf-8"))
            self.assertEqual(mkxp["dataPathApp"], SAVE_APP)
            self.assertEqual(mkxp["dataPathOrg"], SAVE_ORG)
            self.assertNotIn("dataPathApp", (game / "mkxp.json").read_text("utf-8"))
            meta = json.loads((destination / "Data/blue-johto-pilot-proof.json").read_text("utf-8"))
            self.assertEqual(meta["status"], "EXPERIMENTAL_UNTESTED")
            for name, sha in meta["file_hashes"].items():
                self.assertEqual(checksum(destination / name), sha)
            with self.assertRaisesRegex(ValueError, "não é novo"):
                assemble(preview, game, destination, spec, root=root)

    def test_block_missing_source_rights_tampered_preview_and_unsafe_warp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game, preview, spec = make_prepared(root)
            wrong = copy.deepcopy(spec)
            wrong["maps"][0]["events"][0]["destination"] = "JOHTO_ROUTE_29"
            with self.assertRaisesRegex(ValueError, "Warp sem retorno"):
                plan(preview, game, wrong, root=root)
            wrong = copy.deepcopy(spec)
            wrong["start"]["passability_verified"] = False
            with self.assertRaisesRegex(ValueError, "Spawn real"):
                plan(preview, game, wrong, root=root)
            (preview / "Data/Map601.rxdata").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "RPG::Map|map|RMXP|Source|preview|Cannot|staged"):
                plan(preview, game, spec, root=root)

    def test_block_nonisolated_output_and_reuse_of_main_saves(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game, preview, spec = make_prepared(root)
            with self.assertRaisesRegex(ValueError, "Workspace"):
                assemble(preview, game, root / "game/new-pilot", spec, root=root)
            (game / "mkxp.json").write_text(
                '{"dataPathApp":"Decades Save","dataPathOrg":"Decades"}', "utf-8")
            with self.assertRaisesRegex(ValueError, "perfil de save"):
                plan(preview, game, spec, root=root)

    def test_ruby_guard_only_accepts_signed_local_pilot(self):
        if not shutil.which("ruby"):
            self.skipTest("Ruby indisponível")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game, preview, spec = make_prepared(root)
            output = root / ".blue-work/johto-pilot"
            assemble(preview, game, output, spec, root=root)
            script = (
                "module BlueRegionStart; def self.johto_spawn; nil; end; end\n"
                "def pbRgssExists?(file); File.file?(file); end\n"
                "load 'Plugins/ZZZZZ Blue Johto Pilot/JohtoPilotBoot.rb'\n"
                "print BlueRegionStart.johto_spawn.inspect\n"
            )
            before = subprocess.run(["ruby", "-e", script], cwd=output,
                                    text=True, capture_output=True, check=True)
            self.assertEqual(before.stdout, "[601, 13, 13]")
            (output / "Data/Map601.rxdata").write_bytes(b"bad")
            after = subprocess.run(["ruby", "-e", script], cwd=output,
                                   text=True, capture_output=True, check=True)
            self.assertEqual(after.stdout, "nil")


if __name__ == "__main__":
    unittest.main()
