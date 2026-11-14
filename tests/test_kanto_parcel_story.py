"""Offline contract tests for the Viridian parcel cutscene and forest gate."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from pilot import (command, guarded_forest_transfer, make_viridian_parcel_intro)
    from server.ruby_marshal import RubyObject
finally:
    sys.path.remove(str(ROOT / "scripts/regions"))


class KantoOakParcelTests(unittest.TestCase):
    def fake_shopkeeper(self):
        cond = RubyObject("RPG::Event::Page::Condition", {
            "@self_switch_valid": False, "@self_switch_ch": b"A",
        })
        graphic = RubyObject("RPG::Event::Page::Graphic", {
            "@character_name": b"person_002", "@tile_id": 0,
        })
        page = RubyObject("RPG::Event::Page", {
            "@condition": cond, "@graphic": graphic,
            "@trigger": 0, "@through": False,
            "@list": [command(355, b"pbPokemonMart([:POKEBALL])")],
        })
        return RubyObject("RPG::Event", {
            "@id": 2, "@name": b"Shopkeeper", "@x": 4, "@y": 2,
            "@pages": [page],
        })

    def test_parcel_intro_is_one_shot_autorun_with_player_approach(self):
        original = self.fake_shopkeeper()
        intro = make_viridian_parcel_intro({2: original})
        self.assertEqual(intro.attrs["@id"], 3)
        self.assertEqual((intro.attrs["@x"], intro.attrs["@y"]), (4, 2))
        self.assertEqual(len(intro.attrs["@pages"]), 2)
        first, closed = (p.attrs for p in intro.attrs["@pages"])
        self.assertEqual(first["@trigger"], 3)
        self.assertTrue(first["@through"])
        self.assertEqual(first["@graphic"].attrs["@character_name"], b"")
        ops = first["@list"]
        self.assertEqual(ops[0].attrs["@parameters"][2],
                         b"BlueKantoPilot.parcel_pickup_pending?")
        self.assertIn(b"BlueKantoPilot.viridian_parcel_call",
                      [op.attrs["@parameters"][0] for op in ops
                       if op.attrs["@code"] == 355])
        self.assertIn(b"BlueKantoPilot.receive_oak_parcel",
                      [op.attrs["@parameters"][0] for op in ops
                       if op.attrs["@code"] == 355])
        player_route = next(op for op in ops if op.attrs["@code"] == 209)
        self.assertEqual(player_route.attrs["@parameters"][0], -1)
        self.assertEqual(ops[-1].attrs["@code"], 123)
        self.assertTrue(closed["@condition"].attrs["@self_switch_valid"])
        self.assertEqual(closed["@condition"].attrs["@self_switch_ch"], b"A")
        self.assertEqual(closed["@trigger"], 0)
        self.assertEqual([op.attrs["@code"] for op in closed["@list"]], [0])
        self.assertEqual(original.attrs["@pages"][0].attrs["@trigger"], 0)

    def test_forest_warp_reuses_source_coordinates_and_denies_before_parcel(self):
        transfer = command(201, 0, 740, 11, 18, 2, 0)
        guarded = guarded_forest_transfer(transfer)
        self.assertEqual([row.attrs["@code"] for row in guarded],
                         [111, 201, 0, 411, 355, 0, 412])
        self.assertEqual(guarded[0].attrs["@parameters"][2],
                         b"BlueKantoPilot.forest_unlocked?")
        self.assertEqual(guarded[1].attrs["@parameters"],
                         [0, 740, 11, 18, 2, 0])
        self.assertEqual(guarded[1].attrs["@indent"], 1)
        self.assertEqual(guarded[4].attrs["@parameters"][0],
                         b"BlueKantoPilot.forest_gate_warning")

    def test_runtime_scope_does_not_mutate_other_regions(self):
        source = (ROOT / "scripts/regions/pilot.py").read_text("utf-8")
        self.assertIn('original != 24 and warp.attrs["@parameters"][1] == mapping[24]', source)
        self.assertIn("make_viridian_parcel_intro(events)", source)
        gameplay = (ROOT / "scripts/regions/KantoPilot.rb").read_text("utf-8")
        self.assertIn('BlueMusic.kanto_me_play("healed")', gameplay)
        self.assertIn('progress["pilot_oak_parcel_delivered"] = true', gameplay)


if __name__ == "__main__":
    unittest.main()
