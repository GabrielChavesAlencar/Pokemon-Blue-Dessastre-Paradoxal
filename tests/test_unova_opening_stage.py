"""Compile an original corridor against a minimal, otherwise untouched RMXP base."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/regions"))
from build_johto_events import command, ruby
from server.ruby_marshal import loads
from stage import serialize
import unova_opening_stage as opening


class OpeningStageTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.game = self.root / "game"
        self.data = self.game / "Data"
        self.data.mkdir(parents=True)
        (self.game / opening.MAP_INFOS).write_bytes(
            serialize({1: ruby("RPG::MapInfo", name=b"Decades", order=1)}))
        (self.game / opening.TILESETS).write_bytes(
            serialize([None, ruby("RPG::Tileset", id=1, name=b"Existing")]))
        (self.data / "Map001.rxdata").write_bytes(
            serialize(ruby("RPG::Map", events={})))
        (self.data / "CommonEvents.rxdata").write_bytes(serialize([None]))
        (self.data / "System.rxdata").write_bytes(
            serialize(ruby("RPG::System", start_map_id=1), {"RPG::System"}))
        for name, content in (("map_metadata.dat", {}), ("metadata.dat", {}), ("map_connections.dat", [])):
            (self.data / name).write_bytes(serialize(content))
        self.manifest = self.root / "android.json"
        self.android_maps(1)

    def android_maps(self, *ids):
        sha = {"sha256": "a" * 64}
        self.manifest.write_text(json.dumps({
            "schema": 1, "channel": "multiregion", "revision": "b" * 40,
            "files": {"Data/MapInfos.rxdata": sha, **{f"Data/Map{i:03d}.rxdata": sha for i in ids}},
        }), encoding="utf-8")

    def test_native_events_and_existing_indexes(self):
        original = {path.name: path.read_bytes() for path in self.data.iterdir()}
        files, report = opening.compile_overlay(self.game, self.manifest)
        self.assertFalse(report["publishable"])
        self.assertEqual(len(report["doors"]), 12)
        self.assertEqual(loads(files[opening.MAP_INFOS])[1], loads(original["MapInfos.rxdata"])[1])
        self.assertEqual(loads(files[opening.TILESETS])[:-1], loads(original["Tilesets.rxdata"]))
        for door in report["doors"]:
            map_file = f"Data/Map{door['source']:03d}.rxdata"
            world = loads(files[map_file])
            event = world.attrs["@events"][door["event"]]
            page, = event.attrs["@pages"]
            commands = page.attrs["@list"]
            transfer, = [op for op in commands if op.attrs["@code"] == 201]
            self.assertEqual([event.attrs["@x"], event.attrs["@y"]], list(door["threshold"]))
            self.assertEqual(page.attrs["@trigger"], 1)
            self.assertEqual(transfer.attrs["@parameters"][1:4], [door["destination"], *door["arrival"]])
            self.assertEqual(commands[-1].attrs["@code"], 0)
            guarded = door["source"] == report["map_ids"]["UNOVA_NUVEMA_TOWN"] and (
                door["destination"] == report["map_ids"]["UNOVA_ROUTE_01"])
            if guarded:
                self.assertEqual([op.attrs["@code"] for op in commands], [111, 201, 411, 355, 412, 0])
                self.assertEqual(commands[0].attrs["@parameters"], [12, b"BlueUnovaOpeningStory.checked_in?"])
                self.assertEqual(transfer.attrs["@indent"], 1)
            else:
                self.assertEqual(len(commands), 2)
        for action, actor in report["fieldwork"].items():
            world = loads(files[f"Data/Map{actor['map']:03d}.rxdata"])
            event = world.attrs["@events"][actor["event"]]
            page, = event.attrs["@pages"]
            self.assertEqual(page.attrs["@trigger"], 0)
            self.assertEqual(page.attrs["@list"][0].attrs["@parameters"],
                             [f"BlueUnovaOpeningStory.{action}".encode("ascii")])
        self.assertEqual(files[opening.ENCOUNTERS_PBS],
                         b"[280]\nLand,21\n60,PATRAT,2,3\n40,LILLIPUP,2,3\n")
        self.assertEqual({path.name: path.read_bytes() for path in self.data.iterdir()}, original)

    def test_android_and_orphan_windows_collisions_block(self):
        claimed = opening.MAP_IDS[opening.opening.LAB]
        self.android_maps(1, claimed)
        with self.assertRaisesRegex(ValueError, "ocupados"):
            opening.compile_overlay(self.game, self.manifest)
        self.android_maps(1)
        (self.data / f"Map{claimed:03d}.rxdata").write_bytes(b"orphan")
        with self.assertRaisesRegex(ValueError, "ocupados"):
            opening.compile_overlay(self.game, self.manifest)

    def test_common_event_reference_blocks_a_vacant_map(self):
        claimed = opening.MAP_IDS[opening.opening.LAB]
        event = ruby("RPG::CommonEvent", list=[command(201, 0, claimed, 0, 0, 2, 0)])
        (self.data / "CommonEvents.rxdata").write_bytes(
            serialize([None, event], {"RPG::CommonEvent", "RPG::EventCommand"}))
        with self.assertRaisesRegex(ValueError, "referenciados"):
            opening.compile_overlay(self.game, self.manifest)

    def test_output_cannot_replace_a_previous_export(self):
        first = opening.write_overlay(self.root, self.game, self.manifest)
        receipt = self.root / opening.OUTPUT / "manifest.json"
        self.assertEqual(json.loads(receipt.read_bytes())["map_ids"], first["map_ids"])
        with self.assertRaisesRegex(ValueError, "Já existe"):
            opening.write_overlay(self.root, self.game, self.manifest)
