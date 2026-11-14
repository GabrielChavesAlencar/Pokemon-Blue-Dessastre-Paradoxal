"""Original Twinleaf events: synthetic-only geometry, real positions remain null."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))

from build_sinnoh_twinleaf_events import (
    MAPS, HANDLERS, STARTERS, compile_events, read_json,
)
from server.ruby_marshal import RubyObject, loads
from sinnoh_staging_transaction import preview, stage, rollback
from stage import serialize

SPEC = ROOT / "data/regions/sinnoh-twinleaf-events.json"


def fixture(root: Path):
    original = read_json(SPEC)
    native = root / "game" / "Data"
    native.mkdir(parents=True)
    native.joinpath("Map001.rxdata").write_bytes(b"Decades must stay unchanged")
    native.joinpath("System.rxdata").write_bytes(b"native system")
    content = {
        "Data/MapInfos.rxdata": serialize({
            1: RubyObject("RPG::MapInfo", {"@name": b"native"}),
        }),
        "Data/Tilesets.rxdata": serialize([
            None, RubyObject("RPG::Tileset", {"@id": 1}),
        ]),
    }
    for number, row in enumerate(original["maps"], start=500):
        path = f"Data/Map{number:03d}.rxdata"
        content[path] = serialize(RubyObject("RPG::Map", {
            "@width": 30, "@height": 30, "@tileset_id": 1,
            "@events": {}, "@autoplay_bgm": False, "@autoplay_bgs": False,
        }))
        row["map_id"] = number
        row["map_sha256"] = hashlib.sha256(content[path]).hexdigest()
        for index, event in enumerate(row["events"]):
            event["x"], event["y"] = index + 2, 4
            event["verified_position"] = True
            if event["kind"] == "warp":
                event["arrival_x"] = 8
                event["arrival_y"] = 9
                event["verified_arrival"] = True
            else:
                event["sprite"] = "OwnPreviewSprite"
                event["verified_sprite"] = True
    original["start"] = {
        "symbol": "SINNOH_PLAYER_BEDROOM",
        "map_id": 500, "x": 10, "y": 11,
        "verified_position": True, "passability_verified": True,
    }
    dry = preview(root, "geometry", content)
    created = stage(root, "geometry", content, dry["plan_sha256"])
    return root / created["stage_relative_path"], original


class SinnohTwinleafEventTests(unittest.TestCase):
    def test_template_contains_no_fake_mapids_positions_or_approved_flags(self):
        spec = read_json(SPEC)
        self.assertEqual(spec["status"], "EVENT_COORDINATES_REQUIRE_REAL_MAP_AUDIT")
        self.assertFalse(spec["approved_for_install"])
        self.assertFalse(spec["gameplay_verified"])
        self.assertEqual(len(spec["maps"]), 9)
        self.assertEqual({row["symbol"] for row in spec["maps"]}, set(MAPS))
        self.assertIsNone(spec["start"]["map_id"])
        self.assertIsNone(spec["start"]["x"])
        self.assertIsNone(spec["start"]["y"])
        self.assertFalse(spec["start"]["passability_verified"])
        self.assertTrue(all(row["map_id"] is None and row["map_sha256"] is None
                            for row in spec["maps"]))
        events = [event for row in spec["maps"] for event in row["events"]]
        self.assertEqual(len(events), 24)
        self.assertEqual(sum(e["kind"] == "warp" for e in events), 16)
        self.assertEqual({e["handler"] for e in events if e["kind"] == "handler"},
                         set(HANDLERS))
        self.assertEqual({e["species"] for e in events if e["kind"] == "starter_ball"},
                         set(STARTERS))
        self.assertTrue(all(e["x"] is None and e["y"] is None
                            and e["verified_position"] is False for e in events))
        self.assertTrue(all(e["arrival_x"] is None
                            and e["verified_arrival"] is False
                            for e in events if e["kind"] == "warp"))

    def test_story_compiles_only_author_handlers_from_audited_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, spec = fixture(root)
            before = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in (root / "game").rglob("*") if p.is_file()}
            report, files = compile_events(folder, spec, project=root)
            self.assertFalse(report["can_install"])
            self.assertTrue(report["not_playable"])
            self.assertEqual(report["warp_count"], 16)
            self.assertEqual(report["starter_balls"], sorted(STARTERS))
            self.assertEqual(report["start"], [500, 10, 11])
            self.assertEqual(len(files), 9)
            scripts = []
            for name, raw in files.items():
                world = loads(raw)
                self.assertEqual(world.name, "RPG::Map")
                self.assertFalse(world.attrs["@autoplay_bgm"])
                for event in world.attrs["@events"].values():
                    page = event.attrs["@pages"][0]
                    commands = page.attrs["@list"]
                    self.assertEqual(commands[-1].attrs["@code"], 0)
                    for command in commands:
                        if command.attrs["@code"] == 355:
                            scripts.append(command.attrs["@parameters"][0].decode("ascii"))
                            self.assertTrue(
                                scripts[-1] in HANDLERS.values() or
                                scripts[-1].startswith("BlueSinnohPilot.choose_starter_from_ball(:")
                            )
                            self.assertNotIn("BlueJohtoPilot", scripts[-1])
                            self.assertNotIn("system(", scripts[-1])
            self.assertEqual(len(scripts), 8)
            self.assertEqual(sum("choose_starter_from_ball" in s for s in scripts), 3)
            after = {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in (root / "game").rglob("*") if p.is_file()}
            self.assertEqual(before, after)
            self.assertFalse((root / "game/Data/Map500.rxdata").exists())

    def test_template_cannot_compile_without_real_coordinates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, _ = fixture(root)
            with self.assertRaisesRegex(ValueError, "MapID/hash/símbolo"):
                compile_events(folder, read_json(SPEC), project=root)

    def test_rejects_invalid_event_coordinates_or_unverified_starter_sprites(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, spec = fixture(root)
            e = spec["maps"][5]["events"][1]
            self.assertEqual(e["species"], "TURTWIG")
            e["verified_sprite"] = False
            with self.assertRaisesRegex(ValueError, "Sprite próprio"):
                compile_events(folder, spec, project=root)
            e["verified_sprite"] = True
            e["x"] = 3000
            with self.assertRaisesRegex(ValueError, "Posição"):
                compile_events(folder, spec, project=root)

    def test_rejects_unverified_spawn_and_warp_arrival(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, spec = fixture(root)
            spec["start"]["passability_verified"] = False
            with self.assertRaisesRegex(ValueError, "Spawn"):
                compile_events(folder, spec, project=root)
            spec["start"]["passability_verified"] = True
            spec["maps"][0]["events"][0]["verified_arrival"] = False
            with self.assertRaisesRegex(ValueError, "Chegada do warp"):
                compile_events(folder, spec, project=root)

    def test_rejects_foreign_scripts_duplicate_starter_and_missing_handlers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, spec = fixture(root)
            spec["maps"][1]["events"][0]["handler"] = "BlueJohtoPilot.elm"
            with self.assertRaisesRegex(ValueError, "não confiável"):
                compile_events(folder, spec, project=root)
            spec["maps"][1]["events"][0]["handler"] = "mother"
            spec["maps"][5]["events"][2]["species"] = "TURTWIG"
            with self.assertRaisesRegex(ValueError, "iniciais únicos"):
                compile_events(folder, spec, project=root)
            spec["maps"][5]["events"][2]["species"] = "CHIMCHAR"
            spec["maps"][5]["events"].pop(4)
            with self.assertRaisesRegex(ValueError, "5 handlers"):
                compile_events(folder, spec, project=root)

    def test_rejects_tampered_geometry_and_foreign_existing_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, spec = fixture(root)
            (folder / "Data/Map500.rxdata").write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "alterado"):
                compile_events(folder, spec, project=root)

    def test_rejects_stages_outside_isolated_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, spec = fixture(root)
            fake = root / "game"
            with self.assertRaisesRegex(ValueError, "sinnoh-stage"):
                compile_events(fake, spec, project=root)

    def test_story_dry_run_and_rollback_never_change_geometry_or_native(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder, spec = fixture(root)
            before = (folder / "Data/Map500.rxdata").read_bytes()
            report, files = compile_events(folder, spec, project=root)
            dry = preview(root, "sinnoh-story", files)
            self.assertFalse((root / dry["stage_relative_path"]).exists())
            created = stage(root, "sinnoh-story", files, dry["plan_sha256"])
            target = root / created["stage_relative_path"]
            self.assertTrue((target / "Data/Map500.rxdata").is_file())
            self.assertEqual((folder / "Data/Map500.rxdata").read_bytes(), before)
            reverted = rollback(root, "sinnoh-story", dry["plan_sha256"])
            self.assertTrue(reverted["removed_only_stage"])
            self.assertFalse(target.exists())
            self.assertEqual((root / "game/Data/Map001.rxdata").read_bytes(),
                             b"Decades must stay unchanged")


if __name__ == "__main__":
    unittest.main()
