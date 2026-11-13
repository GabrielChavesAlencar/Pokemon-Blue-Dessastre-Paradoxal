"""Synthetic-only Sinnoh terrain preview tests: never import foreign events/audio."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))

from audit_sinnoh_rxdata import audit_rxdata
from build_johto_events import EVENT_CLASSES, ruby
from convert_sinnoh_geometry import build_geometry
from plan_sinnoh_remap import make_plan
from server.ruby_marshal import RubyData, loads
from sinnoh_staging_transaction import preview, rollback, stage
from stage import serialize

PNG = b"\x89PNG\r\n\x1a\n" + b"synthetic-owned-test-graphic"


def table(w=3, h=3):
    count = w * h * 3
    return RubyData("Table",
                    struct.pack("<5I", 3, w, h, 3, count) +
                    struct.pack(f"<{count}H", *([0] * count)))


def write(root, filename, content):
    path = root / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def fixture(root: Path, *, missing_png=False):
    source = root / "donor"
    game_data = root / "game" / "Data"
    write(source, "Data/MapInfos.rxdata", serialize({
        10: ruby("RPG::MapInfo", name=b"Twinleaf Sample", order=1),
        11: ruby("RPG::MapInfo", name=b"Starter Room Sample", order=2),
    }))
    write(source, "Data/Tilesets.rxdata", serialize([
        None, ruby("RPG::Tileset", id=1, name=b"External Example",
                   tileset_name=b"Terrain", autotile_names=[b"Water"],
                   panorama_name=b"External_Panorama",
                   battleback_name=b"External_BattleBack")
    ]))
    commands = [
        ruby("RPG::EventCommand", code=201,
             parameters=[0, 11, 1, 1, 2, 0]),
        ruby("RPG::EventCommand", code=355,
             parameters=[b"system('DO_NOT_RUN')"]),
    ]
    event = ruby("RPG::Event", pages=[
        ruby("RPG::Event::Page", list=commands)
    ])
    for mid in (10, 11):
        write(source, f"Data/Map{mid:03d}.rxdata", serialize(ruby(
            "RPG::Map", tileset_id=1, width=3, height=3,
            data=table(), events={1: event} if mid == 10 else {},
            autoplay_bgm=True,
            bgm=ruby("RPG::AudioFile", name=b"External Song", volume=90, pitch=100),
        ), EVENT_CLASSES))
    write(source, "Graphics/Tilesets/Terrain.png", PNG)
    if not missing_png:
        write(source, "Graphics/Autotiles/Water.png", PNG)
    write(game_data, "MapInfos.rxdata", serialize({
        1: ruby("RPG::MapInfo", name=b"Native", order=10),
    }))
    write(game_data, "Tilesets.rxdata", serialize([
        None, ruby("RPG::Tileset", id=1, name=b"Native"),
    ]))
    write(game_data, "Map001.rxdata", b"Decades map unaffected")
    write(game_data, "System.rxdata", b"Original protected System")
    report = audit_rxdata(source, game_data)
    req = {
        "schema": 1, "region": "SINNOH",
        "source_mapinfos_sha256": report["mapinfos_sha256"],
        "source_tilesets_sha256": report["tilesets_sha256"],
        "source_zip_sha256": report["source_zip_sha256"],
        "mapping": {"10": 500, "11": 501},
        "symbols": {"10": "SINNOH_SAMPLE_TWINLEAF",
                    "11": "SINNOH_SAMPLE_ROOM"},
        "source_map_hashes": {str(i): x["sha256"] for i, x in
                              ((row["source_id"], row) for row in report["maps"])},
    }
    plan = None if missing_png else make_plan(report, req)
    return source, game_data, report, req, plan


class SinnohGeometryConverterTests(unittest.TestCase):
    def test_geometry_only_strips_foreign_events_music_and_audio(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, game, _, _, plan = fixture(root)
            before = {
                path.relative_to(root): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (root / "game").rglob("*") if path.is_file()
            }
            files, result = build_geometry(source, game, plan, project=root)
            self.assertEqual(result["mode"], "LOCAL_GEOMETRY_ONLY_INERT_PREVIEW")
            self.assertEqual(result["maps_staged_in_memory"], 2)
            self.assertEqual(result["tilesets_prepared"], 1)
            self.assertEqual(result["graphics_prepared"], 2)
            self.assertEqual(result["static_transfers_rewritten"], 0)
            self.assertEqual(result["donor_events_imported"], 0)
            self.assertEqual(result["donor_audio_imported"], 0)
            self.assertFalse(result["runtime_playable"])
            self.assertEqual(set(files), {
                "Data/Map500.rxdata", "Data/Map501.rxdata",
                "Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
                *[p for p in files if p.startswith("Graphics/")],
            })
            self.assertEqual(len([p for p in files if p.startswith("Graphics/")]), 2)
            world = loads(files["Data/Map500.rxdata"]).attrs
            self.assertEqual(world["@events"], {})
            self.assertFalse(world["@autoplay_bgm"])
            self.assertFalse(world["@autoplay_bgs"])
            self.assertEqual(world["@encounter_list"], [])
            self.assertEqual(world["@bgm"].attrs["@name"], b"")
            self.assertEqual(world["@width"], 3)
            info = loads(files["Data/MapInfos.rxdata"])
            self.assertIn(1, info)
            self.assertEqual(info[1].attrs["@name"], b"Native")
            self.assertIn(500, info)
            self.assertIn(501, info)
            tiles = loads(files["Data/Tilesets.rxdata"])
            self.assertEqual(len(tiles), 3)
            self.assertEqual(tiles[1].attrs["@name"], b"Native")
            self.assertEqual(world["@tileset_id"], 2)
            self.assertEqual(tiles[2].attrs["@panorama_name"], b"")
            self.assertEqual(tiles[2].attrs["@battleback_name"], b"")
            after = {
                path.relative_to(root): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in (root / "game").rglob("*") if path.is_file()
            }
            self.assertEqual(after, before)
            self.assertFalse((root / ".blue-work").exists())

    def test_preview_stage_and_rollback_do_not_touch_decades(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, game, _, _, plan = fixture(root)
            files, _ = build_geometry(source, game, plan, project=root)
            dry = preview(root, "sinnoh", files)
            self.assertFalse((root / ".blue-work").exists())
            done = stage(root, "sinnoh", files, dry["plan_sha256"])
            self.assertEqual(done["mode"], "LOCAL_STAGE_ONLY")
            saved = root / done["stage_relative_path"]
            self.assertTrue(saved.joinpath("Data/Map500.rxdata").exists())
            self.assertEqual((game / "Map001.rxdata").read_bytes(),
                             b"Decades map unaffected")
            self.assertTrue(rollback(root, "sinnoh", dry["plan_sha256"])["removed_only_stage"])
            self.assertFalse(saved.exists())
            self.assertEqual((game / "System.rxdata").read_bytes(),
                             b"Original protected System")

    def test_tampered_mapping_and_changed_source_are_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, game, _, _, plan = fixture(root)
            changed = json.loads(json.dumps(plan))
            changed["mapping"]["10"] = 503
            with self.assertRaisesRegex(ValueError, "Plano modificado"):
                build_geometry(source, game, changed, project=root)
            (source / "Data/Map010.rxdata").write_bytes(b"corrupt source")
            with self.assertRaises(ValueError):
                build_geometry(source, game, plan, project=root)

    def test_missing_graphic_blocks_geometry(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, game, report, req, _ = fixture(root, missing_png=True)
            self.assertEqual(report["missing_graphics"],
                             ["Graphics/Autotiles/Water.png"])
            with self.assertRaisesRegex(ValueError, "missing_graphics"):
                make_plan(report, req)

    def test_rejects_source_inside_game(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, game, _, _, plan = fixture(root)
            with self.assertRaisesRegex(ValueError, "jogo principal"):
                build_geometry(root / "game", game, plan, project=root)

    def test_invalid_terrain_table_fails_before_staging(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source, game, report, req, plan = fixture(root)
            world = loads((source / "Data/Map010.rxdata").read_bytes())
            world.attrs["@data"] = RubyData("Table", b"bad table")
            (source / "Data/Map010.rxdata").write_bytes(serialize(world, EVENT_CLASSES))
            changed_audit = audit_rxdata(source, game)
            new_req = dict(req)
            new_req["source_map_hashes"] = {
                str(row["source_id"]): row["sha256"]
                for row in changed_audit["maps"]
            }
            changed_plan = make_plan(changed_audit, new_req)
            with self.assertRaisesRegex(ValueError, "terreno"):
                build_geometry(source, game, changed_plan, project=root)
            self.assertFalse((root / ".blue-work").exists())


if __name__ == "__main__":
    unittest.main()
