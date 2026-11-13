"""Testes do compilador de eventos autorais do primeiro piloto de Johto."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from build_johto_events import compile_events, publish, read_json
    from audit_johto import checksum, read_map_data
    from stage import serialize
    from server.ruby_marshal import RubyObject
finally:
    sys.path.pop(0)

MAP_KEYS = (
    "JOHTO_NEW_BARK_PLAYER_HOME_2F",
    "JOHTO_NEW_BARK_PLAYER_HOME_1F",
    "JOHTO_NEW_BARK_TOWN",
    "JOHTO_NEW_BARK_ELM_LAB",
    "JOHTO_ROUTE_29",
)


def make_fixture(root):
    preview = root / ".blue-work/geometry"
    data = preview / "Data"
    data.mkdir(parents=True)
    base = read_json(ROOT / "data/regions/johto-new-bark-events.json")
    archive = hashlib.sha256(b"synthetic-data-not-an-approved-game").hexdigest()
    stage_maps = []
    for index, row in enumerate(base["maps"], start=601):
        assert row["symbol"] in MAP_KEYS
        map_file = data / f"Map{index:03d}.rxdata"
        world = RubyObject("RPG::Map", {
            "@width": 24, "@height": 22, "@tileset_id": 3,
            "@events": {}, "@autoplay_bgm": False, "@autoplay_bgs": False,
        })
        map_file.write_bytes(serialize(world))
        row["map_id"] = index
        row["map_sha256"] = checksum(map_file)
        for n, event in enumerate(row["events"], start=1):
            event["x"], event["y"] = 2 + n, 5
            event["verified_position"] = True
            if event["kind"] == "handler":
                event["sprite"] = "Test_Character"
            if event["kind"] == "warp":
                event["arrival_x"], event["arrival_y"] = 8, 9
        stage_maps.append({
            "symbol": row["symbol"], "destination_id": index,
            "events_imported": 0,
        })
    (preview / "johto-stage.json").write_text(json.dumps({
        "schema": 1, "region": "JOHTO",
        "status": "GEOMETRY_PREVIEW_ONLY", "not_playable": True,
        "can_install": False, "source_archive_sha256": archive,
        "maps": stage_maps,
    }), encoding="utf-8")
    return preview, base


class JohtoEventBuildTests(unittest.TestCase):
    def test_template_never_fakes_mapids_or_coordinates(self):
        spec = read_json(ROOT / "data/regions/johto-new-bark-events.json")
        self.assertEqual(spec["status"], "EVENT_COORDINATES_REQUIRE_REAL_AUDIT")
        self.assertEqual(len(spec["maps"]), 5)
        self.assertTrue(all(m["map_id"] is None and m["map_sha256"] is None
                            for m in spec["maps"]))
        self.assertTrue(all(not e["verified_position"] for m in spec["maps"]
                            for e in m["events"]))
        self.assertEqual({e["handler"] for m in spec["maps"] for e in m["events"]
                          if e["kind"] == "handler"},
                         {"mother", "elm", "starter", "rival"})

    def test_compiles_events_as_data_without_changing_geometry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            preview, spec = make_fixture(root)
            before = {p.name: checksum(p) for p in (preview / "Data").glob("Map*.rxdata")}
            result, files = compile_events(preview, spec, work_root=root)
            self.assertFalse(result["can_install"])
            self.assertTrue(result["not_playable"])
            self.assertEqual(len(files), 5)
            self.assertEqual(sum(result["events_per_map"].values()), 12)
            for key, payload in files.items():
                self.assertTrue(key.startswith("Data/Map"))
                self.assertEqual(result["files"][key],
                                 hashlib.sha256(payload).hexdigest())
                world = read_map_data(preview / key)
                from server.ruby_marshal import loads
                upgraded = loads(payload)
                self.assertEqual(upgraded.attrs["@width"], world.attrs["@width"])
                self.assertEqual(upgraded.attrs["@height"], world.attrs["@height"])
                self.assertTrue(upgraded.attrs["@events"])
                for ev in upgraded.attrs["@events"].values():
                    self.assertEqual(ev.name, "RPG::Event")
                    self.assertEqual(ev.attrs["@pages"][0].name, "RPG::Event::Page")
                    cmds = ev.attrs["@pages"][0].attrs["@list"]
                    self.assertEqual(cmds[-1].attrs["@code"], 0)
                    for cmd in cmds:
                        if cmd.attrs["@code"] == 355:
                            self.assertIn(cmd.attrs["@parameters"][0], (
                                b"BlueJohtoPilot.mother",
                                b"BlueJohtoPilot.elm",
                                b"BlueJohtoPilot.choose_starter",
                                b"BlueJohtoPilot.rival",
                            ))
            self.assertEqual(before, {p.name: checksum(p)
                                       for p in (preview / "Data").glob("Map*.rxdata")})
            self.assertFalse((root / "game").exists())

    def test_template_without_real_maps_is_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            preview, _ = make_fixture(root)
            original = read_json(ROOT / "data/regions/johto-new-bark-events.json")
            with self.assertRaisesRegex(ValueError, "MapID/hash"):
                compile_events(preview, original, work_root=root)

    def test_missing_positions_and_bad_destination_are_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            preview, spec = make_fixture(root)
            bad = copy.deepcopy(spec)
            bad["maps"][0]["events"][0]["verified_position"] = False
            with self.assertRaisesRegex(ValueError, "não verificada"):
                compile_events(preview, bad, work_root=root)
            bad = copy.deepcopy(spec)
            bad["maps"][0]["events"][0]["arrival_x"] = 999
            with self.assertRaisesRegex(ValueError, "fora do mapa"):
                compile_events(preview, bad, work_root=root)
            bad = copy.deepcopy(spec)
            bad["maps"][0]["events"][0]["destination"] = "KANTO_PALLET"
            with self.assertRaisesRegex(ValueError, "desconhecido"):
                compile_events(preview, bad, work_root=root)

    def test_rejects_arbitrary_ruby_script_and_duplicate_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            preview, spec = make_fixture(root)
            bad = copy.deepcopy(spec)
            bad["maps"][1]["events"][0]["handler"] = "Kernel.system"
            with self.assertRaisesRegex(ValueError, "não confiável"):
                compile_events(preview, bad, work_root=root)
            bad = copy.deepcopy(spec)
            bad["maps"][1]["events"][1]["key"] = bad["maps"][1]["events"][0]["key"]
            with self.assertRaisesRegex(ValueError, "Evento/posição"):
                compile_events(preview, bad, work_root=root)

    def test_rejects_tampered_preview_or_already_installed_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            preview, spec = make_fixture(root)
            first = preview / "Data/Map601.rxdata"
            first.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "alterado"):
                compile_events(preview, spec, work_root=root)

    def test_publish_only_new_isolated_folder_and_no_release_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            preview, spec = make_fixture(root)
            game = root / "game/Data"
            game.mkdir(parents=True)
            sentinel = game / "Map001.rxdata"
            sentinel.write_bytes(b"decades-unaltered")
            output = root / ".blue-work/new-events"
            result = publish(preview, output, spec, work_root=root)
            self.assertFalse(result["can_install"])
            self.assertEqual(sentinel.read_bytes(), b"decades-unaltered")
            self.assertTrue((output / "Data/Map601.rxdata").is_file())
            self.assertFalse((output / "Data/blue-johto-install.json").exists())
            with self.assertRaisesRegex(ValueError, "NOVO"):
                publish(preview, output, spec, work_root=root)
            with self.assertRaisesRegex(ValueError, "NOVO"):
                publish(preview, game, spec, work_root=root)


if __name__ == "__main__":
    unittest.main()
