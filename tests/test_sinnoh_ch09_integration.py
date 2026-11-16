"""CH09: complete synthetic Sinnoh chain, transaction guards and read-only evidence.

Uses only self-authored fake Ruby Marshal maps and PBS fixtures.  NEVER loads
Pokémon donor assets, runs Game.exe, allocates native MapIDs or installs files
into the shared Decades game. Source IDs 10..18 and candidate 500..508 exist
ONLY in per-test TemporaryDirectory instances; they are not project claims.
"""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))

from audit_sinnoh_rxdata import audit_rxdata
from audit_sinnoh_twinleaf_events import audit as audit_story, read_json as read_story
from build_johto_events import EVENT_CLASSES, ruby
from build_sinnoh_barry_pbs import publish as publish_barry
from build_sinnoh_twinleaf_events import compile_events
from convert_sinnoh_geometry import build_geometry
from plan_sinnoh_remap import make_plan
from prepare_sinnoh_pilot_bundle import (
    build as build_bundle, load_stage, publish as publish_bundle,
)
from server.ruby_marshal import loads
from sinnoh_staging_transaction import preview, rollback, stage
from stage import serialize
from test_sinnoh_barry_pbs import fixture as pbs_fixture
from test_sinnoh_geometry_converter import (
    fixture as two_map_fixture, table as fake_table, write,
)

TEMPLATE = ROOT / "data/regions/sinnoh-twinleaf-events.json"
SCHEMA = ROOT / "data/regions/sinnoh-twinleaf-events.schema.json"
COUNT = 9


def inventory(folder: Path) -> dict[str, str]:
    """Hash every file, including native saves, to detect any unintended write."""
    return {
        p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in folder.rglob("*") if p.is_file()
    }


def synthetic_source(root: Path):
    """Construct NINE source maps with 1 malicious donor command for stripping."""
    source, game_data, _old_audit, _req, _old_plan = two_map_fixture(root)
    ids = tuple(range(10, 19))
    infos = {
        sid: ruby("RPG::MapInfo", name=("Synthetic Sinnoh " + str(sid)).encode("ascii"),
                  order=sid)
        for sid in ids
    }
    write(source, "Data/MapInfos.rxdata", serialize(infos))
    for sid in ids:
        commands = (
            [ruby("RPG::EventCommand", code=201, parameters=[0, 11, 1, 1, 2, 0]),
             ruby("RPG::EventCommand", code=355,
                  parameters=[b"DO_NOT_EXECUTE_DONOR_SCRIPT()"])]
            if sid == 10 else []
        )
        donor_events = (
            {1: ruby("RPG::Event", pages=[
                ruby("RPG::Event::Page", list=commands)])}
            if commands else {}
        )
        write(source, f"Data/Map{sid:03d}.rxdata", serialize(
            ruby("RPG::Map", tileset_id=1, width=30, height=30,
                 data=fake_table(30, 30), events=donor_events,
                 autoplay_bgm=True,
                 bgm=ruby("RPG::AudioFile", name=b"Unlicensed_Donor_Song",
                          volume=100, pitch=100)), EVENT_CLASSES))
    game = pbs_fixture(root)
    (game / "Game.exe").write_bytes(b"synthetic-placeholder-not-executable")
    for region in ("Decades", "Kanto", "Johto", "Hoenn"):
        write(game, "Savedata/" + region + ".sav",
              ("protected:" + region).encode("ascii"))
    write(game, "Plugins/Blue Original/Boot.rb", b"module OriginalBlue; end\n")
    return source, game_data, game


def plan_request(report: dict) -> dict:
    ids = report["source_map_ids"]
    return {
        "schema": 1, "region": "SINNOH",
        "source_zip_sha256": report["source_zip_sha256"],
        "source_mapinfos_sha256": report["mapinfos_sha256"],
        "source_tilesets_sha256": report["tilesets_sha256"],
        "source_map_hashes": {
            str(row["source_id"]): row["sha256"] for row in report["maps"]},
        "mapping": {str(mid): 500 + index for index, mid in enumerate(ids)},
        "symbols": {
            str(mid): read_story(TEMPLATE)["maps"][index]["symbol"]
            for index, mid in enumerate(ids)},
    }


def filled_spec(geom_files: dict[str, bytes]) -> dict:
    authored = read_story(TEMPLATE)
    for index, row in enumerate(authored["maps"]):
        mid = 500 + index
        row["map_id"] = mid
        row["map_sha256"] = hashlib.sha256(
            geom_files[f"Data/Map{mid:03d}.rxdata"]).hexdigest()
        for event_index, e in enumerate(row["events"]):
            e["x"], e["y"], e["verified_position"] = event_index + 2, 4, True
            if e["kind"] == "warp":
                e["arrival_x"], e["arrival_y"], e["verified_arrival"] = 8, 9, True
            else:
                e["sprite"], e["verified_sprite"] = "SyntheticOwnSprite", True
    authored["start"].update(
        symbol="SINNOH_PLAYER_BEDROOM", map_id=500, x=10, y=11,
        verified_position=True, passability_verified=True)
    return authored


class SinnohFullSyntheticPipelineCH09(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sinnoh-ch09-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source, self.native, self.game = synthetic_source(self.root)
        self.native_before = inventory(self.game)
        self.source_before = inventory(self.source)

    def must_be_untouched(self):
        self.assertEqual(self.native_before, inventory(self.game))
        self.assertEqual(self.source_before, inventory(self.source))
        self.assertFalse((self.game / "Data/Map500.rxdata").exists())
        self.assertFalse((self.game / "Data/blue-sinnoh-rival-ready.txt").exists())

    def audited_plan(self):
        inspected = audit_rxdata(self.source, self.native)
        self.assertEqual(inspected["source_map_count"], COUNT)
        self.assertEqual(inspected["source_map_ids"], list(range(10, 19)))
        self.assertGreaterEqual(inspected["untrusted_script_commands_not_executed"], 1)
        self.assertFalse(inspected["import_allowed"])
        self.assertEqual(inspected["missing_map_files"], [])
        self.assertEqual(inspected["orphan_map_files"], [])
        self.assertEqual(inspected["missing_graphics"], [])
        explicit = plan_request(inspected)
        reservations = {"schema": 1, "region": "SINNOH",
                        "protected_ids": [510, 580, 600, 800]}
        proposal = make_plan(inspected, explicit, reserved=reservations)
        self.assertEqual(proposal["mode"], "REMAP_CANDIDATE_ONLY")
        self.assertFalse(proposal["can_install"])
        self.assertFalse(proposal["other_region_reservations_fully_verified"])
        self.assertEqual(len(proposal["mapping"]), COUNT)
        return inspected, explicit, proposal

    def geometry(self):
        audited, request, plan = self.audited_plan()
        geom, state = build_geometry(self.source, self.native, plan,
                                     project=self.root)
        self.assertEqual(state["maps_staged_in_memory"], COUNT)
        self.assertEqual(state["donor_events_imported"], 0)
        self.assertEqual(state["donor_audio_imported"], 0)
        self.assertFalse(state["runtime_playable"])
        for mid in range(500, 509):
            obj = loads(geom[f"Data/Map{mid:03d}.rxdata"])
            self.assertEqual(obj.attrs["@events"], {})
            self.assertFalse(obj.attrs["@autoplay_bgm"])
            self.assertEqual(obj.attrs["@bgm"].attrs["@name"], b"")
        dry = preview(self.root, "ch09-geometry", geom)
        self.assertFalse((self.root / dry["stage_relative_path"]).exists())
        actual = stage(self.root, "ch09-geometry", geom, dry["plan_sha256"])
        folder = self.root / actual["stage_relative_path"]
        self.assertEqual(load_stage(self.root, folder, geometry=True), geom)
        self.must_be_untouched()
        return plan, geom, dry, folder

    def complete(self):
        plan, geom, dry, geometry_folder = self.geometry()
        spec = filled_spec(geom)
        dimensions = {row["symbol"]: [30, 30] for row in spec["maps"]}
        structure = audit_story(spec, read_story(SCHEMA), dimensions=dimensions)
        self.assertEqual((structure["maps"], structure["events"], structure["warps"]),
                         (9, 24, 16))
        self.assertFalse(structure["can_install"])
        story_report, story_files = compile_events(
            geometry_folder, spec, project=self.root)
        self.assertEqual(story_report["warp_count"], 16)
        self.assertEqual(sum(story_report["event_counts"].values()), 24)
        story_dry = preview(self.root, "ch09-story", story_files)
        story_stage = stage(self.root, "ch09-story",
                            story_files, story_dry["plan_sha256"])
        story_folder = self.root / story_stage["stage_relative_path"]
        draft = self.root / ".blue-work/sinnoh-ch09-barry"
        published_barry = publish_barry(self.game, draft, root=self.root)
        self.assertFalse(published_barry["can_install"])
        script = self.root / "scripts/regions/SinnohPilot.rb"
        script.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / "scripts/regions/SinnohPilot.rb", script)
        report, outputs = build_bundle(
            geometry_folder, story_folder, spec, draft, self.game,
            project=self.root)
        self.must_be_untouched()
        return {
            "plan": plan, "geom": geom, "geometry_dry": dry,
            "geometry_stage": geometry_folder, "spec": spec,
            "story_files": story_files, "story_dry": story_dry,
            "story_stage": story_folder, "barry_draft": draft,
            "bundle_report": report, "bundle_files": outputs,
        }

    def test_all_real_modules_audit_remap_geometry_events_bundle_hashes(self):
        data = self.complete()
        plan, output = data["bundle_report"], data["bundle_files"]
        self.assertEqual(plan["maps"], 9)
        self.assertEqual(plan["warps"], 16)
        self.assertEqual(plan["author_events"], 24)
        self.assertEqual(plan["barry_pbs_teams_statistically_verified"], 3)
        self.assertEqual(plan["physical_starter_balls"],
                         ["CHIMCHAR", "PIPLUP", "TURTWIG"])
        for key in ("runtime_playable", "can_merge_into_main_game",
                    "native_pbs_compiled", "ready_marker_created",
                    "native_game_or_saves_modified",
                    "rights_and_redistribution_approved"):
            self.assertFalse(plan[key], key)
        self.assertTrue(all(hashlib.sha256(payload).hexdigest() ==
                            plan["files_sha256"][path]
                            for path, payload in output.items()))
        self.assertNotIn("Data/Scripts.rxdata", output)
        self.assertNotIn("Data/System.rxdata", output)
        self.assertFalse(any("SinnohPreview.rb" in p for p in output))
        self.assertNotIn(b"DO_NOT_EXECUTE_DONOR_SCRIPT()",
                         b"".join(output.values()))
        self.assertNotIn(b"Unlicensed_Donor_Song", b"".join(output.values()))
        self.assertFalse((self.root / ".blue-work/sinnoh-ch09-overlay").exists())
        folder = self.root / ".blue-work/sinnoh-ch09-overlay"
        published = publish_bundle(self.root, folder, plan, output)
        self.assertTrue(published["created"])
        self.assertFalse(published["runtime_playable"])
        self.assertEqual(len([p for p in folder.glob("Data/Map*.rxdata")
                              if p.name != "MapInfos.rxdata"]), 9)
        for rel, sha in plan["files_sha256"].items():
            self.assertEqual(hashlib.sha256((folder / rel).read_bytes()).hexdigest(), sha)
        with self.assertRaises(ValueError):
            publish_bundle(self.root, folder, plan, output)
        self.must_be_untouched()
        # Roll back ONLY disposable staged copies; the assembled package is
        # independent and its provenance remains readable for review.
        back_story = rollback(self.root, "ch09-story",
                              data["story_dry"]["plan_sha256"])
        back_geom = rollback(self.root, "ch09-geometry",
                             data["geometry_dry"]["plan_sha256"])
        self.assertTrue(back_story["removed_only_stage"])
        self.assertTrue(back_geom["removed_only_stage"])
        self.assertFalse(data["story_stage"].exists())
        self.assertFalse(data["geometry_stage"].exists())
        self.assertTrue(folder.exists())
        self.must_be_untouched()

    def test_audit_source_missing_graphic_blocks_before_plan_or_staging(self):
        (self.source / "Graphics/Autotiles/Water.png").unlink()
        record = audit_rxdata(self.source, self.native)
        self.assertEqual(record["missing_graphics"],
                         ["Graphics/Autotiles/Water.png"])
        with self.assertRaisesRegex(ValueError, "missing_graphics"):
            make_plan(record, plan_request(record))
        self.assertFalse((self.root / ".blue-work").exists())

    def test_hash_pinned_plan_blocks_modified_source_and_johto_ids(self):
        audited, req, proposal = self.audited_plan()
        corrupt = copy.deepcopy(req)
        corrupt["mapping"]["10"] = 800
        with self.assertRaisesRegex(ValueError, "legado"):
            make_plan(audited, corrupt)
        corrupt = copy.deepcopy(req)
        corrupt["mapping"]["10"] = 600
        with self.assertRaises(ValueError):
            make_plan(audited, corrupt)
        corrupt = copy.deepcopy(req)
        corrupt["mapping"]["10"] = 1
        with self.assertRaisesRegex(ValueError, "ocupado"):
            make_plan(audited, corrupt)
        corrupt = copy.deepcopy(req)
        corrupt["source_map_hashes"]["10"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash diverge"):
            make_plan(audited, corrupt)
        from_source = self.source / "Data/Map010.rxdata"
        original = from_source.read_bytes()
        from_source.write_bytes(original + b"tampered")
        with self.assertRaises(ValueError):
            build_geometry(self.source, self.native, proposal, project=self.root)
        self.assertFalse((self.root / ".blue-work").exists())
        # The fixture itself deliberately changed the donor; restore it
        # before asserting that the converter did not write to either side.
        from_source.write_bytes(original)
        self.must_be_untouched()

    def test_stage_fsync_failure_is_atomic_no_partial_output(self):
        _audit, _req, plan = self.audited_plan()
        geom, _ = build_geometry(self.source, self.native, plan, project=self.root)
        dry = preview(self.root, "ch09-fsync", geom)
        with patch("sinnoh_staging_transaction.os.fsync",
                   side_effect=OSError("synthetic disk failure")):
            with self.assertRaisesRegex(OSError, "synthetic disk failure"):
                stage(self.root, "ch09-fsync", geom, dry["plan_sha256"])
        self.assertFalse((self.root / dry["stage_relative_path"]).exists())
        temporary = self.root / ".blue-work/sinnoh-stage"
        self.assertFalse(any(p.name.startswith(".sinnoh-staging-")
                             for p in temporary.iterdir()))
        self.must_be_untouched()
        accepted = stage(self.root, "ch09-fsync", geom, dry["plan_sha256"])
        self.assertTrue((self.root / accepted["stage_relative_path"]).is_dir())
        with self.assertRaises(ValueError):
            rollback(self.root, "ch09-fsync", "0" * 64)
        self.assertTrue(rollback(self.root, "ch09-fsync",
                                 dry["plan_sha256"])["removed_only_stage"])
        self.must_be_untouched()

    def test_corrupt_stage_hash_rejects_bundle_and_blocks_unsafe_rollback(self):
        record = self.complete()
        filename = record["story_stage"] / "Data/Map500.rxdata"
        untouched = filename.read_bytes()
        filename.write_bytes(untouched + b"CH09 CORRUPTION")
        with self.assertRaises(ValueError):
            build_bundle(record["geometry_stage"], record["story_stage"],
                         record["spec"], record["barry_draft"],
                         self.game, project=self.root)
        with self.assertRaisesRegex(ValueError, "modificado|hash"):
            rollback(self.root, "ch09-story",
                     record["story_dry"]["plan_sha256"])
        self.assertTrue(record["story_stage"].exists())
        filename.write_bytes(untouched)
        self.assertTrue(rollback(self.root, "ch09-story",
                                 record["story_dry"]["plan_sha256"])["removed_only_stage"])
        self.assertTrue(rollback(self.root, "ch09-geometry",
                                 record["geometry_dry"]["plan_sha256"])["removed_only_stage"])
        self.must_be_untouched()

    def test_changed_barry_pbs_or_native_collision_blocks_bundle(self):
        record = self.complete()
        pbs = record["barry_draft"] / "PBS/trainers_sinnoh_barry.txt"
        original = pbs.read_bytes()
        pbs.write_bytes(original + b"\n# modified")
        with self.assertRaises(ValueError):
            build_bundle(record["geometry_stage"], record["story_stage"],
                         record["spec"], record["barry_draft"],
                         self.game, project=self.root)
        pbs.write_bytes(original)
        self.assertFalse((self.root / ".blue-work/sinnoh-ch09-overlay").exists())
        native_map = self.game / "Data/Map501.rxdata"
        native_map.write_bytes(b"Protected Johto/Hoenn map")
        with self.assertRaisesRegex(ValueError, "já pertence"):
            build_bundle(record["geometry_stage"], record["story_stage"],
                         record["spec"], record["barry_draft"],
                         self.game, project=self.root)
        native_map.unlink()
        self.must_be_untouched()

    def test_bundle_publish_fault_cleans_temp_and_never_writes_shared_game(self):
        record = self.complete()
        dest = self.root / ".blue-work/sinnoh-ch09-overlay"
        with patch("prepare_sinnoh_pilot_bundle.os.fsync",
                   side_effect=OSError("CH09 synthetic bundle disk failure")):
            with self.assertRaisesRegex(OSError, "CH09 synthetic bundle disk failure"):
                publish_bundle(self.root, dest, record["bundle_report"],
                               record["bundle_files"])
        self.assertFalse(dest.exists())
        self.assertFalse(any(p.name.startswith(".sinnoh-assembly-")
                             for p in dest.parent.iterdir()))
        self.must_be_untouched()
        published = publish_bundle(self.root, dest, record["bundle_report"],
                                   record["bundle_files"])
        self.assertTrue(published["created"])
        self.must_be_untouched()


if __name__ == "__main__":
    unittest.main()
