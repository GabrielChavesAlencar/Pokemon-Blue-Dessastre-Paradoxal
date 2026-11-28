import json
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))

from audit_hoenn_h00 import inspect_delivery, no_overlap_borders, routes_by_number, scope_for, tiles_present
from server.ruby_marshal import RubyData, RubyObject, integer


class HoennH00Tests(unittest.TestCase):
    def test_routes_use_exact_names_and_destination_is_not_inferred(self):
        rows = [
            {
                "source_id": 107 if number == 105 else 900 + number,
                "name": f"Route {number}", "has_terrain": True,
            }
            for number in range(101, 135)
        ]
        rows.append({"source_id": 256, "name": "Route 105_U", "has_terrain": True})
        self.assertEqual(routes_by_number(rows)[105], 107)
        rows.append({"source_id": 257, "name": "Route 105", "has_terrain": True})
        with self.assertRaisesRegex(ValueError, "identidade física única"):
            routes_by_number(rows)

    def test_empty_and_named_variants_do_not_count_as_emerald_scope(self):
        self.assertEqual(scope_for("Hoenn", [], False, 0), "hierarchy_or_empty")
        self.assertEqual(scope_for("Room", ["Battle Frontier"], True, 1), "postgame_candidate")
        self.assertEqual(scope_for("Port", ["Birth Island"], True, 1), "external_event")
        self.assertEqual(scope_for("Sootopolis City (STORMING)", [], True, 0), "donor_variant_or_filler")
        self.assertEqual(scope_for("Unverified house", [], True, 1), "scope_review_required")

    def test_scope_distinguishes_story_interiors_optional_and_donor_scenes(self):
        cases = (
            ("Granite Cave B1F", ["Granite Cave", "Dungeons"], "emerald_story_dungeon_reference"),
            ("Petalburg Gym", ["Petalburg City", "Cities"], "emerald_story_location_reference"),
            ("Room", ["Petalburg City", "Cities"], "city_or_route_interior_reference"),
            ("Captain's Office", ["Abandoned Ship", "Dungeons"], "emerald_optional_reference"),
            ("Route 124_U", ["Underwater Maps", "Special"], "emerald_underwater_reference"),
            ("Boat transition", ["Cutscene Maps", "Special"], "donor_scene_or_integration_reference"),
            ("Routes", ["Hoenn"], "donor_scene_or_integration_reference"),
            ("Delta Episode Cutscene 1", ["Cutscene Maps"], "donor_variant_or_filler"),
        )
        for name, parents, scope in cases:
            with self.subTest(name=name):
                self.assertEqual(scope_for(name, parents, True, 1), scope)

    def test_terrain_must_fit_the_native_table(self):
        packed = struct.pack("<5I3H", 3, 1, 1, 3, 3, 1, 0, 0)
        world = RubyObject("RPG::Map", {
            "@width": 1, "@height": 1, "@data": RubyData("Table", packed),
        })
        self.assertTrue(tiles_present(world))
        world.attrs["@width"] = 2
        with self.assertRaisesRegex(ValueError, "dimensões"):
            tiles_present(world)

    def test_edges_that_only_touch_at_the_end_have_no_shared_tile(self):
        mapping = {147: 857, 76: 810}
        maps = {
            147: RubyObject("RPG::Map", {"@width": 80}),
            76: RubyObject("RPG::Map", {"@width": 360}),
        }
        rows = "857,North,80,810,South,0\n857,North,79,810,South,0"
        self.assertEqual(no_overlap_borders(rows, mapping, maps), [{
            "record": "857,North,80,810,South,0",
            "source_ids": [147, 76], "edge_lengths": [80, 360], "shared_tiles": 0,
        }])

    def test_shared_johto_and_sinnoh_claims_are_checked(self):
        payload = {
            "Data/MapInfos.rxdata": bytes((4, 8)) + b"{" + integer(1) + b"i" + integer(700) + b"i" + integer(1),
            "Data/blue-johto-main-preview.json": json.dumps({"map_ids": [700]}).encode(),
            "Data/blue-sinnoh-shared.json": json.dumps({"map_ids": [700]}).encode(),
        }
        with self.assertRaisesRegex(ValueError, "duas regiões"):
            inspect_delivery(payload.__getitem__, set(payload) | {"Data/Map700.rxdata"})

    def test_ownership_collision_fails_before_reading_any_map(self):
        payload = {
            "Data/MapInfos.rxdata": b"\x04\x08{" + integer(1) + b"i" + integer(700) + b"i" + integer(1),
            "Data/blue-kanto-install.json": json.dumps({"maps": {"39": 700}}).encode(),
            "Data/blue-hoenn-install.json": json.dumps({"maps": {"7": 700}}).encode(),
        }
        with self.assertRaisesRegex(ValueError, "duas regiões"):
            inspect_delivery(payload.__getitem__, set(payload) | {"Data/Map700.rxdata"})


if __name__ == "__main__":
    unittest.main()
