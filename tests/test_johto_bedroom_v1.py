"""No Game.exe here: synthetic tests of a real RPG Maker XP tile table."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/regions"))
from build_johto_bedroom_v1 import (
    WIDTH, HEIGHT, START, STAIRS_APPROACH, blueprint, table_values, tile
)


class JohtoBedroomOfflineTests(unittest.TestCase):
    def setUp(self):
        self.flags = [0] * 5328

    def test_rmxp_table_and_no_event_import(self):
        raw, proof = blueprint(tuple(self.flags))
        shape, grid = table_values(raw, dimensions=3)
        self.assertEqual(shape, (14, 11, 3))
        self.assertEqual(len(grid), WIDTH * HEIGHT * 3)
        self.assertEqual(proof["events_installed"], 0)
        self.assertFalse(proof["gameplay_playable"])
        self.assertFalse(proof["tested_in_game"])

    def test_bedroom_is_new_14_by_11_not_cloned_cabin(self):
        raw, proof = blueprint(tuple(self.flags))
        self.assertNotEqual(proof["size"], [40, 40])
        self.assertEqual(proof["size"], [14, 11])
        self.assertEqual(len(proof["furniture"]), 5)
        _, grid = table_values(raw)
        self.assertEqual(grid[2 + 14 * (3 + 11 * 2)], tile(275, 0))
        self.assertEqual(grid[6 + 14 * (3 + 11 * 2)], tile(280, 0))
        self.assertEqual(grid[10 + 14 * (7 + 11 * 2)], tile(238, 1))

    def test_spawn_to_stairs_is_static_only(self):
        _, proof = blueprint(tuple(self.flags))
        self.assertGreaterEqual(proof["static_reachable_tiles"], 15)
        self.assertEqual((proof["spawn_proposal"]["x"], proof["spawn_proposal"]["y"]), START)
        self.assertEqual((proof["stairs_approach_proposal"]["x"],
                          proof["stairs_approach_proposal"]["y"]), STAIRS_APPROACH)
        self.assertFalse(proof["spawn_proposal"]["verified_in_game"])

    def test_blocked_floor_is_rejected(self):
        self.flags[tile(88, 0)] = 15
        self.flags[tile(88, 1)] = 15
        with self.assertRaisesRegex(ValueError, "blocked"):
            blueprint(tuple(self.flags))

    def test_outside_tile_or_bad_marshal_table_is_rejected(self):
        with self.assertRaises(ValueError):
            tile(619, 0)
        with self.assertRaises(ValueError):
            table_values(b"invalid", dimensions=3)
        with self.assertRaises(ValueError):
            table_values(struct.pack("<5I", 3, 14, 11, 3, 400), dimensions=3)


if __name__ == "__main__":
    unittest.main()
