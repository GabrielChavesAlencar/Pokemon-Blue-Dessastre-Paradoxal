"""Offline-only tests for Professor Elm's native-tile geometry and graphics."""
import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/regions"))
from build_johto_elm_lab_v1 import (
    WIDTH, HEIGHT, STARTERS, BALLS, APPROACH, ELM, DOOR,
    blueprint, extend_table, table_values, decode_png, encode_png, tile
)


class JohtoElmLabOfflineTests(unittest.TestCase):
    def setUp(self):
        self.flags = [0] * 5336
        self.flags[5328:5331] = [15, 15, 15]

    def test_three_visible_ball_tiles_are_really_embedded_in_map(self):
        grid, proof = blueprint(tuple(self.flags))
        dims, values = table_values(grid, dimension=3)
        self.assertEqual(dims, (20, 16, 3))
        self.assertEqual(len(values), 960)
        for i, (name, (x, y)) in enumerate(zip(STARTERS, BALLS)):
            self.assertEqual(values[x + WIDTH*(y + HEIGHT*2)], 5328+i)
            self.assertEqual(proof["starter_balls"][i]["starter"], name)
            self.assertFalse(proof["starter_balls"][i]["event_installed"])
            self.assertTrue(proof["starter_balls"][i]["remove_static_tile_when_event_added"])
        self.assertFalse(proof["gameplay_playable"])
        self.assertFalse(proof["tested_in_game"])

    def test_elm_door_and_all_starter_approaches_have_connected_path(self):
        _, proof = blueprint(tuple(self.flags))
        self.assertGreaterEqual(proof["static_reachable_tiles"], 55)
        wanted = {"elm": ELM, "entry_door_approach": DOOR}
        wanted.update({"approach_"+name.lower(): xy for name, xy in zip(STARTERS, APPROACH)})
        for key, (x, y) in wanted.items():
            self.assertEqual(proof["proposed_positions"][key]["x"], x)
            self.assertEqual(proof["proposed_positions"][key]["y"], y)
            self.assertFalse(proof["proposed_positions"][key]["verified_in_game"])

    def test_original_lab_layout_and_static_furniture(self):
        _, report = blueprint(tuple(self.flags))
        names = {x["name"] for x in report["furniture"]}
        self.assertEqual(report["size"], [20, 16])
        self.assertTrue({
            "research_bookshelf", "diagnostics_computer",
            "lab_scanner", "entry_door"
        }.issubset(names))
        self.assertEqual(sum("starter_pedestal_" in x["name"]
                             for x in report["furniture"]), 3)
        self.assertEqual(report["events_installed"], 0)
        self.assertFalse(report["engine_warps_installed"])

    def test_rejects_invalid_native_passage_table(self):
        with self.assertRaises(ValueError):
            extend_table(b"broken")
        with self.assertRaises(ValueError):
            tile(618, 0)
        raw = struct.pack("<5I", 1, 5328, 1, 1, 5328)+b"\0"*(5328*2)
        shape, data = table_values(extend_table(raw, ball_flag=15), dimension=1)
        self.assertEqual(shape, (5336, 1, 1))
        self.assertEqual(data[-8:], (15, 15, 15, 0, 0, 0, 0, 0))

    def test_blocked_lab_aisle_causes_fail_closed(self):
        self.flags[tile(85, 2)] = 15
        with self.assertRaisesRegex(ValueError, "Blocked|unreachable"):
            blueprint(tuple(self.flags))

    def test_png_codec_roundtrip_and_filter(self):
        row = b"\x11\x22\x33\xff"*8
        binary = encode_png(8, [row, row[::-1]])
        w, h, rows = decode_png(binary, expected_width=8)
        self.assertEqual((w, h), (8, 2))
        self.assertEqual(rows, [row, row[::-1]])

    def test_png_corruption_rejected(self):
        binary = bytearray(encode_png(4, [b"\x12\x23\x34\xff"*4]))
        binary[21] ^= 7
        with self.assertRaises(ValueError):
            decode_png(bytes(binary))


if __name__ == "__main__":
    unittest.main()
