"""Geração segura de inventário nativo e vínculo MapID de New Bark.

Somente fixtures sintéticas RMXP; nunca declara gameplay validado.
"""
import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from audit_johto_native_rooms import report as native_report, write_report
    from bind_johto_new_bark import bind, publish, REQUIRED
    from build_johto_interiors import build as build_interiors
    from audit_johto import checksum
    from test_johto_interior_authoring import make_data
finally:
    sys.path.pop(0)


def fixture(root: Path):
    game, preview, templates = make_data(root)
    output = root / ".blue-work/johto-with-interiors"
    build_interiors(preview, game, output, templates, root=root)
    spec = json.loads((ROOT / "data/regions/johto-new-bark-events.json")
                      .read_text(encoding="utf-8"))
    return game, preview, output, spec


class JohtoNewBarkBindingTests(unittest.TestCase):
    def test_native_room_inventory_does_not_verify_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game, initial, preview, spec = fixture(root)
            originals = {str(p.relative_to(game)): checksum(p)
                         for p in game.rglob("*") if p.is_file()}
            output = root / ".blue-work/native-rooms.json"
            result = native_report(game, initial, root=root)
            self.assertEqual(result["status"], "READ_ONLY_ROOM_CANDIDATES")
            self.assertFalse(result["can_install"])
            self.assertFalse(result["room_reviewed"])
            self.assertGreaterEqual(result["count"], 3)
            ids = {x["native_map_id"] for x in result["rooms"]}
            self.assertTrue({1, 2, 3}.issubset(ids))
            self.assertTrue(all(not x["template_reviewed"] for x in result["rooms"]))
            for symbol in REQUIRED - {"JOHTO_NEW_BARK_TOWN", "JOHTO_ROUTE_29"}:
                self.assertIn(symbol, result["suggestions_not_approved"])
            write_report(output, result, root=root)
            self.assertTrue(output.exists())
            self.assertEqual(json.loads(output.read_text("utf-8"))["count"],
                             result["count"])
            self.assertEqual(originals, {str(p.relative_to(game)): checksum(p)
                                         for p in game.rglob("*") if p.is_file()})
            with self.assertRaisesRegex(ValueError, "NOVO"):
                write_report(output, result, root=root)

    def test_binds_five_maps_and_preserves_every_coordinate_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game, initial, preview, spec = fixture(root)
            original_spec = copy.deepcopy(spec)
            original_native = checksum(game / "Data/MapInfos.rxdata")
            bound = bind(preview, game, spec, root=root)
            self.assertEqual(bound["binding_status"], "MAP_IDS_BOUND_EVENT_POSITIONS_PENDING")
            self.assertFalse(bound["can_install"])
            self.assertTrue(bound["not_playable"])
            self.assertEqual({row["symbol"] for row in bound["maps"]}, REQUIRED)
            ids = {row["symbol"]: row["map_id"] for row in bound["maps"]}
            self.assertEqual(ids["JOHTO_NEW_BARK_TOWN"], 603)
            self.assertEqual(ids["JOHTO_ROUTE_29"], 605)
            self.assertEqual(ids["JOHTO_NEW_BARK_PLAYER_HOME_2F"], 606)
            self.assertEqual(ids["JOHTO_NEW_BARK_PLAYER_HOME_1F"], 607)
            self.assertEqual(ids["JOHTO_NEW_BARK_ELM_LAB"], 608)
            self.assertEqual(len(bound["todo_review"]), 13)
            for row in bound["maps"]:
                self.assertEqual(row["map_sha256"],
                                 checksum(preview / "Data" /
                                          f"Map{row['map_id']:03d}.rxdata"))
                for ev in row["events"]:
                    self.assertIsNone(ev["x"])
                    self.assertIsNone(ev["y"])
                    self.assertFalse(ev["verified_position"])
                    if ev["kind"] == "warp":
                        self.assertIsNone(ev["arrival_x"])
                        self.assertIsNone(ev["arrival_y"])
                    else:
                        self.assertIsNone(ev["sprite"])
            self.assertIsNone(bound["start"]["x"])
            self.assertFalse(bound["start"]["passability_verified"])
            self.assertEqual(original_spec, spec)
            path = root / ".blue-work/new-bark-bound.json"
            publish(path, bound, root=root)
            self.assertEqual(json.loads(path.read_text("utf-8"))["binding_status"],
                             bound["binding_status"])
            self.assertEqual(checksum(game / "Data/MapInfos.rxdata"), original_native)
            with self.assertRaisesRegex(ValueError, "NOVA"):
                publish(path, bound, root=root)

    def test_fails_without_all_five_maps_or_with_stale_native_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game, initial, preview, spec = fixture(root)
            with self.assertRaisesRegex(ValueError, "Faltam interiores"):
                bind(initial, game, spec, root=root)
            (game / "Data/Tilesets.rxdata").write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                bind(preview, game, spec, root=root)

    def test_refuses_approved_coordinates_or_uncontrolled_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game, initial, preview, spec = fixture(root)
            partial = copy.deepcopy(spec)
            partial["maps"][0]["events"][0]["x"] = 1
            with self.assertRaisesRegex(ValueError, "não auditados"):
                bind(preview, game, partial, root=root)
            partial = copy.deepcopy(spec)
            partial["start"]["verified_position"] = True
            with self.assertRaisesRegex(ValueError, "Spawn"):
                bind(preview, game, partial, root=root)
            full = bind(preview, game, spec, root=root)
            with self.assertRaisesRegex(ValueError, "NOVA"):
                publish(game / "Data/overwrite.json", full, root=root)
            self.assertFalse((game / "Data/overwrite.json").exists())


if __name__ == "__main__":
    unittest.main()
