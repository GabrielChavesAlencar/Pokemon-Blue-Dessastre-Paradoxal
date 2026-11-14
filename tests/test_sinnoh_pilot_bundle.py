"""Offline QA overlay tests with synthetic maps/PBS and original Blue handlers."""
from __future__ import annotations

import copy
import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from build_sinnoh_twinleaf_events import compile_events, read_json
from build_sinnoh_barry_pbs import publish as publish_barry
from prepare_sinnoh_pilot_bundle import build, publish, load_stage
from server.ruby_marshal import RubyObject, loads
from sinnoh_staging_transaction import stage, preview
from stage import serialize
from test_sinnoh_twinleaf_events import fixture as story_fixture
from test_sinnoh_barry_pbs import fixture as barry_fixture

TEMPLATE = ROOT / "data/regions/sinnoh-twinleaf-events.json"


def inputs(root):
    geom_first, spec = story_fixture(root)
    # The existing test geometry fixture has nine map files but deliberately
    # only a native MapInfos entry. This test builds a coherent *synthetic*
    # preview with exactly those nine map records in the MERGED copy.
    native_data = root / "game/Data"
    old_info = (geom_first / "Data/MapInfos.rxdata").read_bytes()
    old_tiles = (geom_first / "Data/Tilesets.rxdata").read_bytes()
    (native_data / "MapInfos.rxdata").write_bytes(old_info)
    (native_data / "Tilesets.rxdata").write_bytes(old_tiles)
    files = {
        f.relative_to(geom_first).as_posix(): f.read_bytes()
        for f in geom_first.rglob("*") if f.is_file()
        and f.name != "stage-manifest.json"
    }
    infos = loads(old_info)
    for row in spec["maps"]:
        infos[row["map_id"]] = RubyObject("RPG::MapInfo", {
            "@name": ("[Sinnoh] " + row["symbol"]).encode("utf-8"),
            "@order": row["map_id"],
            "@parent_id": 0,
        })
    files["Data/MapInfos.rxdata"] = serialize(infos)
    second = preview(root, "geometry-v2", files)
    second = stage(root, "geometry-v2", files, second["plan_sha256"])
    geom = root / second["stage_relative_path"]

    report, story = compile_events(geom, spec, project=root)
    story_plan = preview(root, "story", story)
    story_stage = stage(root, "story", story, story_plan["plan_sha256"])
    story_path = root / story_stage["stage_relative_path"]
    game = barry_fixture(root)
    (game / "Game.exe").write_bytes(b"synthetic not executable")
    draft = root / ".blue-work/sinnoh-barry-draft"
    publish_barry(game, draft, root=root)
    plugin = root / "scripts/regions/SinnohPilot.rb"
    plugin.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / "scripts/regions/SinnohPilot.rb", plugin)
    return geom, story_path, spec, draft, game


class SinnohPilotBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sinnoh-bundle-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.geom, self.story, self.spec, self.draft, self.game = inputs(self.root)

    def assembled(self, *, spec=None, geometry=None, story=None, draft=None):
        return build(geometry or self.geom, story or self.story,
                     spec or self.spec, draft or self.draft, self.game,
                     project=self.root)

    def test_assembles_geometry_physical_balls_and_barry_pbs_without_legacy(self):
        before = {
            p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (self.root / "game").rglob("*") if p.is_file()
        }
        report, files = self.assembled()
        self.assertEqual(report["maps"], 9)
        self.assertEqual(report["warps"], 16)
        self.assertEqual(report["author_events"], 24)
        self.assertEqual(report["physical_starter_balls"],
                         ["CHIMCHAR", "PIPLUP", "TURTWIG"])
        self.assertEqual(report["barry_pbs_teams_statistically_verified"], 3)
        self.assertFalse(report["runtime_playable"])
        self.assertFalse(report["native_pbs_compiled"])
        self.assertFalse(report["can_merge_into_main_game"])
        self.assertFalse(report["rights_and_redistribution_approved"])
        self.assertFalse(report["ready_marker_created"])
        self.assertFalse(report["native_game_or_saves_modified"])
        self.assertTrue(all(not name.startswith((
            "Data/Scripts", "Data/System", "Data/blue-sinnoh-rival-ready",
        )) for name in files))
        self.assertFalse(any("SinnohPreview.rb" in name for name in files))
        self.assertEqual(len([x for x in files if x.startswith("Data/Map") and
                              x.endswith(".rxdata") and x != "Data/MapInfos.rxdata"]), 9)
        self.assertIn("PBS/trainers_sinnoh_barry.txt", files)
        self.assertIn("PBS/trainer_types_sinnoh_barry.txt", files)
        self.assertIn("Plugins/ZZZZZ Blue Sinnoh Intro/SinnohPilot.rb", files)
        self.assertIn("Plugins/ZZZZZ Blue Sinnoh Intro/meta.txt", files)
        actual = {
            p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (self.root / "game").rglob("*") if p.is_file()
        }
        self.assertEqual(before, actual)
        self.assertFalse((self.root / ".blue-work/sinnoh-qa-overlay").exists())

    def test_publication_is_private_new_and_does_not_write_game(self):
        report, files = self.assembled()
        destination = self.root / ".blue-work/sinnoh-qa-overlay"
        result = publish(self.root, destination, report, files)
        self.assertTrue(result["created"])
        self.assertFalse(result["runtime_playable"])
        self.assertTrue((destination / "sinnoh-qa-overlay-report.json").is_file())
        self.assertTrue((destination / "Data/Map500.rxdata").is_file())
        self.assertFalse((destination / "Data/System.rxdata").exists())
        self.assertFalse((destination / "Game.exe").exists())
        self.assertFalse((self.game / "Data/Map500.rxdata").exists())
        with self.assertRaises(ValueError):
            publish(self.root, destination, report, files)
        with self.assertRaisesRegex(ValueError, "dentro"):
            publish(self.root, self.game / "PBS/bad", report, files)

    def test_rejects_unverified_template_and_fake_map_ids(self):
        with self.assertRaisesRegex(ValueError, "MapIDs"):
            self.assembled(spec=read_json(TEMPLATE))
        invalid = copy.deepcopy(self.spec)
        invalid["maps"][0]["map_id"] = 800
        with self.assertRaisesRegex(ValueError, "MapIDs"):
            self.assembled(spec=invalid)

    def test_rejects_collision_with_actual_game_data(self):
        (self.game / "Data/Map501.rxdata").write_bytes(b"occupied in Decades")
        with self.assertRaisesRegex(ValueError, "já pertence"):
            self.assembled()

    def test_rejects_collision_reserved_by_native_pbs(self):
        (self.game / "PBS/map_metadata_future.txt").write_text(
            "[507]\nName = Reserved for Hoenn\n", encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "já pertence"):
            self.assembled()

    def test_rejects_geometry_manifest_tamper_or_extra_files(self):
        path = self.geom / "Data/Map500.rxdata"
        path.write_bytes(path.read_bytes() + b"tamper")
        with self.assertRaisesRegex(ValueError, "adulterado"):
            self.assembled()

    def test_rejects_authored_event_overlays_even_if_stage_hashes_recomputed(self):
        files = load_stage(self.root, self.story, geometry=False)
        name = "Data/Map500.rxdata"
        world = loads(files[name])
        world.attrs["@events"] = {}
        files[name] = serialize(world)
        draft_plan = preview(self.root, "story-tampered", files)
        staged = stage(self.root, "story-tampered", files, draft_plan["plan_sha256"])
        with self.assertRaisesRegex(ValueError, "compilador autoral"):
            self.assembled(story=self.root / staged["stage_relative_path"])

    def test_rejects_bad_pbs_or_premature_barry_marker(self):
        pbs = self.draft / "PBS/trainers_sinnoh_barry.txt"
        pbs.write_bytes(pbs.read_bytes() + b"\n# changed")
        with self.assertRaises(ValueError):
            self.assembled()
        # When the draft is valid, the main game marker still blocks assembly.
        pbs.write_bytes(pbs.read_bytes().replace(b"\n# changed", b""))
        marker = self.game / "Data/blue-sinnoh-rival-ready.txt"
        marker.write_bytes(b"BLUE_SINNOH_BARRY_V1_READY")
        with self.assertRaisesRegex(ValueError, "Marcador"):
            self.assembled()

    def test_stage_copy_cannot_escape_workspace_via_symlink(self):
        report, files = self.assembled()
        redirect = self.root / ".blue-work/redirect"
        try:
            redirect.symlink_to(self.game, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("No symlinks available")
        with self.assertRaisesRegex(ValueError, "link simbólico"):
            publish(self.root, redirect / "mystage", report, files)

    def test_deletes_no_legacy_saves_or_native_files(self):
        report, files = self.assembled()
        native = self.game / "Data/System.rxdata"
        native.write_bytes(b"important native system")
        save = self.game / "save.dat"
        save.write_bytes(b"important native save")
        publish(self.root, self.root / ".blue-work/sinnoh-integrated-private",
                report, files)
        self.assertEqual(native.read_bytes(), b"important native system")
        self.assertEqual(save.read_bytes(), b"important native save")


if __name__ == "__main__":
    unittest.main()
