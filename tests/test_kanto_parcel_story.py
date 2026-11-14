"""Offline contracts for the canonical Viridian Mart + Route 2 story gate."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from pilot import (
        command, route2_north_columns, make_viridian_route2_gates,
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

    def test_solid_gates_are_in_viridian_not_the_forest_building(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "PBS").mkdir()
            (root / "PBS/map_connections.txt").write_text(
                "10,North,4,18,South,1\n", encoding="utf8")
            city = RubyObject("RPG::Map", {"@width": 10, "@height": 12})
            route = RubyObject("RPG::Map", {"@width": 4, "@height": 9})
            gate_events = make_viridian_route2_gates(
                {2: example_clerk()}, root, city, route,
            )
            self.assertEqual(len(gate_events), 4)
            self.assertEqual([g.attrs["@x"] for g in gate_events.values()], [3, 4, 5, 6])
            self.assertTrue(all(g.attrs["@y"] == 0 for g in gate_events.values()))
            for ev in gate_events.values():
                active, unlocked = [pg.attrs for pg in ev.attrs["@pages"]]
                self.assertEqual(active["@trigger"], 1)
                self.assertFalse(active["@through"])
                self.assertEqual(unlocked["@trigger"], 0)
                self.assertTrue(unlocked["@through"])
                self.assertTrue(unlocked["@condition"].attrs["@self_switch_valid"])
                scripts = [op.attrs["@parameters"][0] for op in active["@list"]
                           if op.attrs["@code"] == 355]
                self.assertEqual(scripts, [b"BlueKantoPilot.route2_gate_warning"])
                self.assertTrue(any(op.attrs["@code"] == 123 for op in active["@list"]))
            # Original event remains unchanged (no frozen region-wide switch).
            self.assertEqual(example_clerk().attrs["@pages"][0].attrs["@trigger"], 0)

    def test_mart_entry_resets_stale_autorun_and_tunnels_are_unmodified(self):
        script = (ROOT / "scripts/regions/pilot.py").read_text("utf8")
        self.assertIn("prepare_viridian_mart_visit", script)
        self.assertIn("make_viridian_route2_gates(events, source, map_data, route2_map)", script)
        self.assertNotIn("guarded_forest_transfer", script)
        self.assertNotIn("mart_counter_approach", script)
        runtime = (ROOT / "scripts/regions/KantoPilot.rb").read_text("utf8")
        self.assertIn("def self.walk_to_viridian_clerk", runtime)
        self.assertIn("$game_player.passable?", runtime)
        self.assertIn("def self.route2_gate_warning", runtime)
        self.assertIn("def self.route2_exit_blocked?", runtime)
        self.assertIn("Game_Player.prepend(BlueKantoPilot::Route2ExitGuard)", runtime)
        self.assertIn('event.name == "Kanto Viridian Route 2 Parcel Gate"', runtime)
        self.assertIn('BlueMusic.kanto_me_play("healed")', runtime)
        self.assertIn('progress["pilot_oak_parcel_delivered"] = true', runtime)


if __name__ == "__main__":
    unittest.main()
