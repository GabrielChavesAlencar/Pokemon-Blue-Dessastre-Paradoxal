"""One-command stage + connections with SYNTHETIC 74-map RMXP ZIP fixtures.

It proves the pipeline writes only into .blue-work, not a playable build.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from prepare_johto_first_playable import run
    from audit_johto import checksum
    from server.ruby_marshal import RubyObject
    from stage import serialize
    from test_johto_stage import fixture, dump
finally:
    sys.path.pop(0)


def make_archive_and_game(root: Path):
    base = fixture(root)
    original = base["source"]
    images = {
        "Graphics/Tilesets/JohtoTerrain.png":
            (original / "Graphics/Tilesets/JohtoTerrain.png").read_bytes(),
        "Graphics/Autotiles/JohtoAuto.png":
            (original / "Graphics/Autotiles/JohtoAuto.png").read_bytes()
    }
    tiles = (original / "Data/Tilesets.rxdata").read_bytes()
    from server.ruby_marshal import loads
    prototype = loads((original / "Data/Map003.rxdata").read_bytes())
    infos = {
        i: RubyObject("RPG::MapInfo", {
            "@name": f"Synthetic Johto {i}".encode("utf-8"),
            "@parent_id": 0, "@order": i
        }) for i in range(79, 153)
    }
    raw_maps = {
        f"Data/Map{i:03d}.rxdata": serialize(prototype, ("RPG::Event",))
        for i in range(79, 153)
    }
    raw = {"Data/MapInfos.rxdata": serialize(infos),
           "Data/Tilesets.rxdata": tiles, **raw_maps, **images}
    # Clean the prior hand-built fixture; use the actual ZIP safe-extractor path.
    shutil.rmtree(original / "Data")
    shutil.rmtree(original / "Graphics")
    archive = original / "original.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for name, payload in sorted(raw.items()):
            z.writestr("synthetic-for-tests/" + name, payload)
    digest = checksum(archive)
    manifest = json.loads((ROOT / "data/regions/johto-source.json").read_text("utf-8"))
    manifest["source"]["archive_sha256"] = digest
    manifest["source"]["accepted_missing_mapinfo_ids"] = []
    graph = json.loads((ROOT / "data/regions/johto-v1-map-connections.json")
                       .read_text("utf-8"))
    graph["source_archive_sha256"] = digest
    (root / "data/regions").mkdir(parents=True)
    (root / "data/regions/johto-source.json").write_text(
        json.dumps(manifest), encoding="utf-8")
    (root / "data/regions/johto-v1-map-connections.json").write_text(
        json.dumps(graph), encoding="utf-8")
    return base, archive


class JohtoFirstPlayablePreflightTests(unittest.TestCase):
    def test_full_74_map_synthetic_stage_and_42_edges_no_game_modification(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base, archive = make_archive_and_game(root)
            game = base["game"]
            originals = {str(p.relative_to(game)): checksum(p)
                         for p in game.rglob("*") if p.is_file()}
            outcome = run(root=root)
            self.assertEqual(outcome["status"],
                             "GEOMETRY_READY_NEW_BARK_PLAYABILITY_PENDING")
            self.assertEqual(outcome["maps_staged"], 74)
            self.assertEqual(outcome["connections_generated"], 42)
            self.assertFalse(outcome["can_install"])
            self.assertFalse(outcome["gameplay_playable"])
            self.assertFalse(outcome["gameplay_tested"])
            self.assertEqual(outcome["new_bark_destination_id"], 601)
            self.assertEqual(outcome["route_29_destination_id"], 626)
            self.assertEqual(outcome["cherrygrove_destination_id"], 602)
            self.assertTrue((root / ".blue-work/johto-staging/Data/Map601.rxdata").is_file())
            self.assertTrue((root / ".blue-work/johto-staging/Data/Map626.rxdata").is_file())
            edges = (root / ".blue-work/johto-connections-preview.txt").read_text("utf-8")
            self.assertEqual(edges.splitlines()[0], "601,West,13,626,East,0")
            self.assertEqual(len(edges.splitlines()), 42)
            actual_report = json.loads((root / ".blue-work/johto-first-playable-readiness.json")
                                       .read_text("utf-8"))
            self.assertEqual(actual_report["status"], outcome["status"])
            self.assertEqual(originals, {str(p.relative_to(game)): checksum(p)
                                         for p in game.rglob("*") if p.is_file()})
            self.assertFalse((root / ".blue-work/johto-pilot/Game.exe").exists())
            with self.assertRaisesRegex(ValueError, "Saida ja existe"):
                run(root=root)

    def test_requires_actual_native_game_and_correct_zip_hash(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, archive = make_archive_and_game(root)
            (root / "game/Data/MapInfos.rxdata").unlink()
            with self.assertRaisesRegex(FileNotFoundError, "game/Data"):
                run(root=root)
            self.assertFalse((root / ".blue-work/johto-staging").exists())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, archive = make_archive_and_game(root)
            archive.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                run(root=root)
            self.assertFalse((root / ".blue-work/johto-source/project").exists())

    def test_batch_uses_safe_one_command_preflight_not_installer(self):
        bat = (ROOT / "JOHTO_PREPARAR_PRIMEIRA_FASE.bat").read_text("utf-8")
        self.assertIn("prepare_johto_first_playable.py", bat)
        self.assertIn("game\\Data\\MapInfos.rxdata", bat)
        self.assertIn("original.zip", bat)
        self.assertNotIn("install_johto.py", bat)
        self.assertNotIn("start \"\" Game.exe", bat)


if __name__ == "__main__":
    unittest.main()
