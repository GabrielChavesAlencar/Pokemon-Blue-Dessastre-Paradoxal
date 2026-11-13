"""Pure Python offline checks: border geometry, not actual playability."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts/regions'))
from johto_route29_cherrygrove import (PATH_SIGNATURE, RoomGrid, derive_connection,
                                      inspect_corridor, parse_rgss_table)


def room(width=6, height=32, side='West', at=11, *, blocked=False, duplicate=False):
    layers = [400] * (width * height) + [0] * (2 * width * height)
    for y in range(height):
        for x in range(width):
            layers[x + width * y] = 396
    for d, val in enumerate(PATH_SIGNATURE):
        for x in (range(4) if side == 'West' else range(width - 4, width)):
            layers[x + width * (at + d)] = val
    if duplicate:
        for d, val in enumerate(PATH_SIGNATURE):
            for x in (range(4) if side == 'West' else range(width - 4, width)):
                layers[x + width * (at + 5 + d)] = val
    passage = [0] * 500
    if blocked:
        passage[96] = 15
    return RoomGrid(width, height, tuple(layers), tuple(passage))


class Route29CityOfflineTests(unittest.TestCase):
    def test_unique_three_tile_real_pattern_produces_exact_offsets(self):
        route = room()
        city = room(side='East', at=23)
        self.assertEqual(inspect_corridor(route, 'West'), [11])
        self.assertEqual(inspect_corridor(city, 'East'), [23])
        report = derive_connection(route, city, route_id=625, city_id=601)
        self.assertEqual(report['pbs_line'], '601,East,12,625,West,0')
        self.assertFalse(report['gameplay_playable'])
        self.assertFalse(report['tested_in_game'])

    def test_blocked_road_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Passagens'):
            derive_connection(room(blocked=True), room(side='East', at=23),
                              route_id=625, city_id=601)

    def test_ambiguous_road_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Passagens'):
            derive_connection(room(duplicate=True), room(side='East', at=23),
                              route_id=625, city_id=601)

    def test_existing_route_connection_cannot_duplicate(self):
        with self.assertRaisesRegex(ValueError, 'ja possui conexao'):
            derive_connection(room(), room(side='East', at=23),
                              route_id=625, city_id=601,
                              existing='625,West,0,601,East,12\n')

    def test_fails_outside_johto_namespace(self):
        with self.assertRaisesRegex(ValueError, 'namespace'):
            derive_connection(room(), room(side='East', at=23),
                              route_id=84, city_id=601)

    def test_table_parser_fails_corrupted_dimensions(self):
        import struct
        wrong = struct.pack('<5I', 3, 2, 2, 3, 100)
        with self.assertRaisesRegex(ValueError, 'inconsistente'):
            parse_rgss_table(wrong)


if __name__ == '__main__':
    unittest.main()
