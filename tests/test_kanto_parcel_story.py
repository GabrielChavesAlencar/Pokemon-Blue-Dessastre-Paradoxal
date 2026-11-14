"""Offline contracts for the canonical Viridian Mart + Route 2 story gate."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from pilot import (
        command, route2_north_columns, viridian_route2_block_line,
        make_viridian_parcel_intro,
    )
    from server.ruby_marshal import RubyObject
finally:
    sys.path.remove(str(ROOT / "scripts/regions"))


def example_clerk():
    condition = RubyObject("RPG::Event::Page::Condition", {
        "@self_switch_valid": False, "@self_switch_ch": b"A",
    })
    graphic = RubyObject("RPG::Event::Page::Graphic", {
        "@character_name": b"person_002", "@tile_id": 0,
    })
    page = RubyObject("RPG::Event::Page", {
        "@condition": condition, "@graphic": graphic,
        "@trigger": 0, "@through": False,
        "@list": [command(355, b"pbPokemonMart([:POKEBALL])")],
    })
    return RubyObject("RPG::Event", {
        "@id": 2, "@name": b"Shopkeeper", "@x": 4, "@y": 2,
        "@pages": [page],
    })


class KantoParcelStoryTests(unittest.TestCase):
    def test_mart_autorun_routes_player_to_the_real_clerk(self):
        clerk = example_clerk()
        intro = make_viridian_parcel_intro({2: clerk})
        self.assertEqual(intro.attrs["@id"], 3)
        self.assertEqual(len(intro.attrs["@pages"]), 2)
        first, second = [p.attrs for p in intro.attrs["@pages"]]
        self.assertEqual(first["@trigger"], 3)
        self.assertTrue(first["@through"])
        self.assertEqual(first["@graphic"].attrs["@character_name"], b"")
        scripts = [op.attrs["@parameters"][0] for op in first["@list"]
                   if op.attrs["@code"] == 355]
        self.assertEqual(scripts, [
            b"BlueKantoPilot.viridian_parcel_call",
            b"BlueKantoPilot.walk_to_viridian_clerk(2)",
            b"BlueKantoPilot.receive_oak_parcel",
        ])
        self.assertTrue(any(op.attrs["@code"] == 210 for op in first["@list"]))
        self.assertEqual(first["@list"][-2].attrs["@code"], 123)
        self.assertEqual(second["@condition"].attrs["@self_switch_ch"], b"A")
        self.assertTrue(second["@condition"].attrs["@self_switch_valid"])
        self.assertEqual(second["@trigger"], 0)
        self.assertEqual(clerk.attrs["@pages"][0].attrs["@trigger"], 0)

    def test_source_connection_sets_precise_north_border_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "PBS").mkdir()
            source = root / "PBS/map_connections.txt"
            source.write_text("10,North,4,18,South,1\n", encoding="utf8")
            self.assertEqual(route2_north_columns(root, 10, 4), tuple(range(3, 7)))
            source.write_text("18,South,1,10,North,4\n", encoding="utf8")
            self.assertEqual(route2_north_columns(root, 10, 4), tuple(range(3, 7)))
            source.write_text("10,East,4,18,West,1\n", encoding="utf8")
            with self.assertRaisesRegex(ValueError, "not a northern"):
                route2_north_columns(root, 10, 4)
            source.write_text("10,North,4,18,South,1\n10,North,4,18,South,1\n")
            with self.assertRaisesRegex(ValueError, "exactly one"):
                route2_north_columns(root, 10, 4)

    def test_gate_follows_red_line_beside_northern_house_not_map_edge(self):
        # The reference screenshot draws the horizontal restriction near the
        # sleeping old man, west of the northern house, not at map y=0.
        door = example_clerk()
        door.attrs["@x"], door.attrs["@y"] = 9, 6
        city = RubyObject("RPG::Map", {"@width": 15, "@height": 12})
        row, first, last = viridian_route2_block_line({2: door}, city)
        self.assertEqual((row, first, last), (5, 3, 8))
        self.assertNotEqual(row, 0)
        self.assertEqual(last - first, 5)

    def test_gate_rejects_missing_house_or_out_of_bounds_corridor(self):
        city = RubyObject("RPG::Map", {"@width": 15, "@height": 12})
        with self.assertRaisesRegex(ValueError, "northern Viridian house"):
            viridian_route2_block_line({}, city)
        door = example_clerk()
        door.attrs["@x"] = 3
        door.attrs["@y"] = 6
        with self.assertRaisesRegex(ValueError, "outside the source map"):
            viridian_route2_block_line({2: door}, city)
        door.attrs["@x"] = 9
        door.attrs["@y"] = 1
        with self.assertRaisesRegex(ValueError, "outside the source map"):
            viridian_route2_block_line({2: door}, city)

    def test_mart_entry_resets_stale_autorun_and_tunnels_are_unmodified(self):
        script = (ROOT / "scripts/regions/pilot.py").read_text("utf8")
        self.assertIn("prepare_viridian_mart_visit", script)
        self.assertIn("viridian_route2_block_line(events, map_data)", script)
        self.assertIn("blue-kanto-viridian-route2-line.txt", script)
        self.assertNotIn("selected.update(gates)", script)
        self.assertNotIn("guarded_forest_transfer", script)
        self.assertNotIn("mart_counter_approach", script)
        runtime = (ROOT / "scripts/regions/KantoPilot.rb").read_text("utf8")
        self.assertIn("def self.walk_to_viridian_clerk", runtime)
        self.assertIn("$game_player.passable?", runtime)
        self.assertIn("def self.route2_gate_warning", runtime)
        self.assertIn("def self.route2_exit_blocked?", runtime)
        self.assertIn("Game_Player.prepend(BlueKantoPilot::Route2ExitGuard)", runtime)
        self.assertIn('event.name == "Kanto Viridian Route 2 Parcel Gate"', runtime)
        self.assertIn("clear_legacy_viridian_route2_gates", runtime)
        self.assertIn("player.y == row + 1", runtime)
        self.assertNotIn("player.y == 0 && $game_map", runtime)
        self.assertIn('BlueMusic.kanto_me_play("healed")', runtime)
        self.assertIn('progress["pilot_oak_parcel_delivered"] = true', runtime)


if __name__ == "__main__":
    unittest.main()
