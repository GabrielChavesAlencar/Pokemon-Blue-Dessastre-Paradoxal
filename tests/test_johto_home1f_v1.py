"""Regression checks for authored New Bark first floor, without Game.exe."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/regions"))
from build_johto_home1f_v1 import (
    WIDTH, HEIGHT, STAIRS_APPROACH, ARRIVAL_FROM_2F,
    DOOR_APPROACH, ARRIVAL_FROM_TOWN, MOTHER_PROPOSAL,
    blueprint, table_values, tile,
)


class JohtoHome1FOfflineTests(unittest.TestCase):
    def setUp(self):
        self.flags = [0] * 5328

    def test_rmxp_dimensions_and_no_foreign_events(self):
        raw, report = blueprint(tuple(self.flags))
        (w, h, z), values = table_values(raw, dimensions=3)
        self.assertEqual((w, h, z), (16, 13, 3))
        self.assertEqual(len(values), WIDTH * HEIGHT * 3)
        self.assertEqual(report["events_installed"], 0)
        self.assertFalse(report["engine_warps_installed"])
        self.assertFalse(report["gameplay_playable"])
        self.assertFalse(report["tested_in_game"])

    def test_actual_furniture_and_non_cloned_dimensions(self):
        raw, report = blueprint(tuple(self.flags))
        names = {i["name"] for i in report["furniture"]}
        self.assertEqual(names, {
            "kitchen_counter", "dining_table_with_chairs", "tv_cabinet",
            "sofa", "potted_plant", "stairs_visual", "front_door_visual"
        })
        _, cells = table_values(raw, dimensions=3)
        self.assertEqual(cells[2 + WIDTH * (3 + HEIGHT * 2)], tile(257, 0))
        self.assertEqual(cells[12 + WIDTH * (8 + HEIGHT * 2)], tile(238, 1))
        self.assertEqual(cells[7 + WIDTH * (10 + HEIGHT * 2)], tile(200, 4))
        self.assertNotEqual(report["size"], [24, 26])

    def test_mother_stairs_and_town_door_proposals_are_reachable(self):
        _, report = blueprint(tuple(self.flags))
        points = {
            "stairs_approach": STAIRS_APPROACH,
            "arrival_from_2f": ARRIVAL_FROM_2F,
            "door_approach": DOOR_APPROACH,
            "arrival_from_town": ARRIVAL_FROM_TOWN,
            "mother_position": MOTHER_PROPOSAL,
        }
        for name, (x, y) in points.items():
            row = report["proposed_positions"][name]
            self.assertEqual((row["x"], row["y"]), (x, y))
            self.assertTrue(row["static_passability_checked"])
            self.assertFalse(row["verified_in_game"])
        self.assertGreaterEqual(report["static_reachable_tiles"], 25)

    def test_blocks_invalid_floor(self):
        self.flags[tile(88, 0)] = 15
        self.flags[tile(88, 1)] = 15
        with self.assertRaisesRegex(ValueError, "bloqueada"):
            blueprint(tuple(self.flags))

    def test_blocks_malformed_rmxp_table_or_bad_tile(self):
        with self.assertRaises(ValueError):
            tile(619, 1)
        with self.assertRaises(ValueError):
            table_values(b"invalid", dimensions=3)
        with self.assertRaises(ValueError):
            table_values(struct.pack("<5I", 3, 16, 13, 3, 100), dimensions=3)

    def test_blocks_missing_native_passage_flags(self):
        with self.assertRaisesRegex(ValueError, "tabela completa"):
            blueprint(tuple([0] * 128))


if __name__ == "__main__":
    unittest.main()
