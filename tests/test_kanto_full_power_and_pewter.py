"""Offline fixture tests for the Kanto boss-rematch catalogue and Pewter edge."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from kanto_full_power import full_power_draft
from pbs import TRAINERS
from pilot import pewter_route3_east_rows
from kanto_overworld import source_obstacle, source_sign_dialogue, adapt_source_field_event
from server.ruby_marshal import RubyObject
from pilot import command, new_event, if_scene


def fixture_event(name=b"Signpost", codes=None, sprite=b"", tile=44):
    condition = RubyObject("RPG::Event::Page::Condition", {
        "@self_switch_valid": False, "@self_switch_ch": b"A"})
    graphic = RubyObject("RPG::Event::Page::Graphic", {
        "@character_name": sprite, "@tile_id": tile})
    page = RubyObject("RPG::Event::Page", {
        "@condition": condition, "@graphic": graphic,
        "@trigger": 0, "@through": False,
        "@list": codes or [command(101, b"Welcome to Pewter!"), command(0)]})
    return RubyObject("RPG::Event", {
        "@id": 8, "@name": name, "@x": 3, "@y": 4, "@pages": [page]})


class RegionalCorrectionsContracts(unittest.TestCase):
    def test_all_15_full_power_profiles_have_strong_six_and_unique_versions(self):
        path = ROOT / "data/kanto-full-power.json"
        manifest = json.loads(path.read_text("utf8"))
        profiles = manifest["teams"]
        self.assertEqual(len(profiles), 15)
        species = set(p for row in profiles for p in row["species"])
        compiled = full_power_draft(path, species, TRAINERS)
        self.assertEqual(compiled.count("Pokemon = "), 90)
        self.assertEqual(sum(line.startswith("[BLUE_KANTO_")
                             for line in compiled.splitlines()), 15)
        self.assertTrue(all(len(row["species"]) == len(set(row["species"])) == 6
                            for row in profiles))
        self.assertIn("[BLUE_KANTO_LEADER,Brock,100]", compiled)
        self.assertIn("[BLUE_KANTO_CHAMPION_BLUE,Blue,103]", compiled)

    def test_full_power_refuses_unavailable_species_and_does_not_forge_source(self):
        path = ROOT / "data/kanto-full-power.json"
        manifest = json.loads(path.read_text("utf8"))
        species = set(p for row in manifest["teams"] for p in row["species"])
        with self.assertRaisesRegex(ValueError, "unavailable"):
            full_power_draft(path, species - {"GOLEM"}, TRAINERS)
        self.assertEqual(len(TRAINERS), len(set(TRAINERS)))

    def test_pewter_route3_gate_uses_original_25_to_32_connection(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "PBS"
            p.mkdir()
            (p / "map_connections.txt").write_text(
                "25,East,2,32,West,1\n", encoding="utf8")
            self.assertEqual(pewter_route3_east_rows(Path(tmp), 12, 8), (1, 9))
            (p / "map_connections.txt").write_text(
                "32,West,1,25,East,2\n", encoding="utf8")
            self.assertEqual(pewter_route3_east_rows(Path(tmp), 12, 8), (1, 9))
            (p / "map_connections.txt").write_text(
                "25,South,2,32,North,1\n", encoding="utf8")
            with self.assertRaisesRegex(ValueError, "east-west"):
                pewter_route3_east_rows(Path(tmp), 12, 8)

    def test_sign_is_safe_action_text_and_keeps_source_tile(self):
        sign = fixture_event()
        cmds = source_sign_dialogue(sign)
        self.assertIsNotNone(cmds)
        self.assertEqual([op.attrs["@code"] for op in cmds], [101])
        result = adapt_source_field_event(
            sign, 25, 8, {"POTION"}, lambda e: b"",
            new_event, command, if_scene)
        converted, meta = result
        self.assertEqual(meta["kind"], "sign_dialogue")
        self.assertEqual(converted.attrs["@pages"][0].attrs["@trigger"], 0)
        self.assertEqual(converted.attrs["@pages"][0].attrs["@graphic"].attrs["@tile_id"], 44)
        sign.attrs["@pages"][0].attrs["@list"] = [
            command(355, b"giveUnapprovedItem"), command(0)]
        self.assertIsNone(source_sign_dialogue(sign))
        self.assertIsNone(adapt_source_field_event(
            sign, 25, 8, {"POTION"}, lambda e: b"",
            new_event, command, if_scene))

    def test_cut_tree_aliases_require_real_source_event(self):
        for label in (b"CutTree", b"Cut Tree", b"Cut_Tree"):
            event = fixture_event(name=label)
            self.assertEqual(source_obstacle(event), "cut")
        self.assertIsNone(source_obstacle(fixture_event(name=b"Decorative Tree")))


if __name__ == "__main__":
    unittest.main()
