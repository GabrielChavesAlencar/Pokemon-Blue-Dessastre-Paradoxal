"""Offline regression: original Kanto items, NPCs and HM obstacles stay safe."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from pilot import command, new_event, if_scene, KANTO_MOONSTONE_CALLBACK
    from verify_pilot import KANTO_MOONSTONE_CALLBACK as REQUIRED_MOONSTONE_CALLBACK
    from kanto_overworld import (
        source_item_ball, source_obstacle, source_npc_dialogue,
        adapt_source_field_event, safely_adapt_source_field_event, MissingActorGraphic,
    )
    from server.ruby_marshal import RubyObject
finally:
    sys.path.remove(str(ROOT / "scripts/regions"))


def fake_event(event_id=9, name=b"Item:POTION", scripts=None,
               graphic=b"items", trigger=0, conditional=False):
    cond = RubyObject("RPG::Event::Page::Condition", {
        "@self_switch_valid": conditional, "@self_switch_ch": b"A",
    })
    pic = RubyObject("RPG::Event::Page::Graphic", {
        "@character_name": graphic, "@tile_id": 0,
    })
    page = RubyObject("RPG::Event::Page", {
        "@condition": cond, "@graphic": pic,
        "@trigger": trigger, "@through": False,
        "@list": scripts if scripts is not None else [
            command(111, 12, b"pbItemBall(:POTION)"),
            command(123, b"A", 0),
            command(0),
        ],
    })
    return RubyObject("RPG::Event", {
        "@id": event_id, "@name": name, "@x": 11, "@y": 7,
        "@pages": [page],
    })


def adapt(event, items=("POTION", "RARECANDY")):
    return adapt_source_field_event(
        event, 24, event.attrs["@id"], set(items),
        lambda ev: b"FRLG_Pilot_items",
        new_event, command, if_scene,
    )


class KantoOverworldContracts(unittest.TestCase):
    def test_item_ball_preserves_coords_and_persists_via_self_switch(self):
        original = fake_event()
        self.assertEqual(source_item_ball(original), ("POTION", 1))
        converted, meta = adapt(original)
        self.assertEqual(meta, {"kind": "item", "item": "POTION", "quantity": 1})
        self.assertEqual((converted.attrs["@id"], converted.attrs["@x"],
                          converted.attrs["@y"]), (9, 11, 7))
        self.assertEqual(len(converted.attrs["@pages"]), 2)
        a, b = [p.attrs for p in converted.attrs["@pages"]]
        self.assertEqual(a["@graphic"].attrs["@character_name"], b"FRLG_Pilot_items")
        self.assertTrue(b["@condition"].attrs["@self_switch_valid"])
        self.assertEqual(b["@condition"].attrs["@self_switch_ch"], b"A")
        self.assertTrue(b["@through"])
        commands = [op.attrs["@parameters"][0] for op in a["@list"]
                    if op.attrs["@code"] == 355]
        self.assertEqual(commands, [
            b'BlueKantoPilot.pickup(:POTION, "KANTO_024_009", 9, 1)',
        ])
        self.assertFalse(original.attrs["@pages"][0].attrs["@condition"].attrs[
            "@self_switch_valid"])

    def test_item_ball_quantity_and_missing_items_are_not_fabricated(self):
        mult = fake_event(name=b"Item:RARECANDY x2",
                          scripts=[command(111, 12, b"pbItemBall(:RARECANDY, 2)")])
        self.assertEqual(source_item_ball(mult), ("RARECANDY", 2))
        self.assertEqual(adapt(mult)[1]["quantity"], 2)
        self.assertIsNone(adapt(mult, items=("POTION",)))
        inconsistent = fake_event(name=b"Item:POTION",
                                  scripts=[command(111, 12, b"pbItemBall(:MASTERBALL)")])
        self.assertIsNone(source_item_ball(inconsistent))
        quest = fake_event(name=b"Item:POTION", scripts=[
            command(111, 12, b"pbItemBall(:POTION)"),
            command(201, 0, 200, 4, 5, 2, 0),
        ])
        self.assertIsNone(source_item_ball(quest))
        scripted = fake_event(name=b"Item:POTION", scripts=[
            command(355, b"giveUnapprovedQuestReward"),
        ])
        self.assertIsNone(source_item_ball(scripted))

    def test_rock_smash_uses_native_engine_and_keeps_original_name(self):
        event = fake_event(name=b"SmashRock", scripts=[command(0)])
        self.assertEqual(source_obstacle(event), "rock_smash")
        result, metadata = adapt(event)
        self.assertEqual(metadata["kind"], "rock_smash")
        first = result.attrs["@pages"][0].attrs
        self.assertEqual(first["@trigger"], 0)
        self.assertFalse(first["@through"])
        self.assertEqual(result.attrs["@name"], b"SmashRock")
        self.assertEqual([c.attrs["@code"] for c in first["@list"]],
                         [111, 355, 355, 0, 412, 0])
        self.assertEqual(first["@list"][1].attrs["@parameters"][0], b"pbSmashThisEvent")

    def test_cut_trees_import_with_native_cut_and_do_not_block_builder(self):
        event = fake_event(name=b"CutTree", scripts=[command(0)],
                           graphic=b"Tree")
        self.assertEqual(source_obstacle(event), "cut")
        result, meta = adapt(event)
        self.assertEqual(meta["kind"], "cut")
        first = result.attrs["@pages"][0].attrs
        self.assertEqual(result.attrs["@name"], b"CutTree")
        self.assertEqual((result.attrs["@x"], result.attrs["@y"]), (11, 7))
        self.assertEqual(first["@trigger"], 0)
        self.assertFalse(first["@through"])
        self.assertEqual(first["@graphic"].attrs["@character_name"],
                         b"FRLG_Pilot_items")
        self.assertEqual(len(result.attrs["@pages"]), 1)
        rows = first["@list"]
        self.assertEqual([r.attrs["@code"] for r in rows],
                         [111, 355, 0, 412, 0])
        self.assertEqual(rows[0].attrs["@parameters"][1], b"pbCut")
        self.assertEqual(rows[1].attrs["@parameters"][0], b"pbSmashThisEvent")
        # Engine requires the original CutTree marker for field moves.
        self.assertIsNone(source_npc_dialogue(event))

    def test_strength_boulder_uses_native_push_and_stays_solid(self):
        event = fake_event(name=b"StrengthBoulder", scripts=[command(0)])
        result, metadata = adapt(event)
        self.assertEqual(metadata["kind"], "strength")
        first = result.attrs["@pages"][0].attrs
        self.assertEqual(first["@trigger"], 1)
        self.assertFalse(first["@through"])
        self.assertEqual(first["@list"][0].attrs["@parameters"][0],
                         b"pbPushThisBoulder")

    def test_npc_literal_dialogues_only(self):
        npc = fake_event(name=b"Resident", scripts=[
            command(101, b"Bem-vindo a Viridian!"),
            command(401, b"Cuidado com a floresta."),
        ], graphic=b"boy")
        self.assertEqual(len(source_npc_dialogue(npc)), 2)
        result, meta = adapt(npc)
        self.assertEqual(meta["kind"], "npc_dialogue")
        self.assertEqual(result.attrs["@x"], 11)
        unsafe = fake_event(name=b"Resident",
                            scripts=[command(355, b"pbReceiveItem(:MASTERBALL)")],
                            graphic=b"boy")
        self.assertIsNone(source_npc_dialogue(unsafe))
        self.assertIsNone(adapt(unsafe))
        conditioned = fake_event(name=b"Resident", graphic=b"boy",
                                 scripts=[command(101, b"Oi")], conditional=True)
        self.assertIsNone(source_npc_dialogue(conditioned))

    def test_missing_optional_npc_sprite_never_crashes_kanto_build(self):
        # Reproduces the Windows error from FRLG: NPC_Hiker.png is absent.
        npc = fake_event(name=b"Friendly Hiker", scripts=[
            command(101, b"Ola!"),
        ], graphic=b"NPC_Hiker")
        def missing_actor(event):
            raise MissingActorGraphic("Missing actor graphic: NPC_Hiker")

        field, problem = safely_adapt_source_field_event(
            npc, 24, 9, {"POTION"}, missing_actor,
            new_event, command, if_scene)
        self.assertIsNone(field)
        self.assertEqual(problem, "Missing actor graphic: NPC_Hiker")
        # Other safe NPCs with real sprites are still recovered.
        result, problem = safely_adapt_source_field_event(
            npc, 24, 9, {"POTION"}, lambda e: b"FRLG_Pilot_NPC_Hiker",
            new_event, command, if_scene)
        self.assertIsNone(problem)
        self.assertEqual(result[1]["kind"], "npc_dialogue")

    def test_missing_optional_item_and_rock_art_is_recoverable(self):
        def missing_actor(event):
            raise MissingActorGraphic("Missing actor graphic: MissingSheet")
        for event in (
            fake_event(name=b"Item:POTION", graphic=b"MissingSheet"),
            fake_event(name=b"SmashRock", scripts=[command(0)],
                       graphic=b"MissingSheet"),
        ):
            result, problem = safely_adapt_source_field_event(
                event, 24, 9, {"POTION"}, missing_actor,
                new_event, command, if_scene)
            self.assertIsNone(result)
            self.assertIn("MissingSheet", problem)

    def test_only_missing_graphic_is_nonfatal(self):
        npc = fake_event(name=b"Friendly Hiker", scripts=[
            command(101, b"Oi!"),
        ], graphic=b"NPC_Hiker")
        def unexpected_failure(event):
            raise ValueError("Other source audit error")
        with self.assertRaisesRegex(ValueError, "Other source audit error"):
            safely_adapt_source_field_event(
                npc, 24, 9, {"POTION"}, unexpected_failure,
                new_event, command, if_scene)

    def test_moonstone_required_event_and_verifier_use_same_script(self):
        # Regression for Windows startup failure:
        # Required Kanto event scripts are missing: [(36, 18)]
        # The pickup gained an event-id argument but verifier kept old text.
        expected = REQUIRED_MOONSTONE_CALLBACK
        self.assertEqual(
            expected,
            'BlueKantoPilot.pickup(:MOONSTONE, "KANTO_036_018", 18)')
        self.assertEqual(KANTO_MOONSTONE_CALLBACK, expected)
        pilot = (ROOT / "scripts/regions/pilot.py").read_text("utf8")
        verifier = (ROOT / "scripts/regions/verify_pilot.py").read_text("utf8")
        self.assertIn("36: {18: KANTO_MOONSTONE_CALLBACK}", pilot)
        self.assertIn("(36, 18): KANTO_MOONSTONE_CALLBACK", verifier)
        # A compiled native event command must match the verifier string.
        native = new_event(
            fake_event(event_id=18, name=b"Moon Stone", graphic=b""),
            [command(355, KANTO_MOONSTONE_CALLBACK.encode("utf8"))],
            0, b"")
        scripts = [
            op.attrs["@parameters"][0].decode("utf8")
            for op in native.attrs["@pages"][0].attrs["@list"]
            if op.attrs["@code"] in (355, 655) and op.attrs["@parameters"]
        ]
        self.assertIn(expected, scripts)

    def test_source_coverage_is_scoped_to_active_kanto_maps(self):
        script = (ROOT / "scripts/regions/pilot.py").read_text("utf8")
        self.assertIn('if original in preview_only:', script)
        self.assertIn('adapt_source_field_event(', script)
        self.assertIn('blue-kanto-field-events.json', script)
        self.assertIn('missing_graphics', script)
        self.assertIn('safely_adapt_source_field_event(', script)
        self.assertIn('scripts/regions/kanto_overworld.py', script)
        self.assertIn('if source_obstacle(event) == "cut":', script)
        self.assertIn('scripts/regions/kanto_dex.py', script)
        runtime = (ROOT / "scripts/regions/KantoPilot.rb").read_text("utf8")
        self.assertIn('def self.pickup(item, key, event_id = nil, quantity = 1)', runtime)
        self.assertIn('collected << key', runtime)
        self.assertIn('GameData::Item.exists?(item)', runtime)


if __name__ == "__main__":
    unittest.main()
