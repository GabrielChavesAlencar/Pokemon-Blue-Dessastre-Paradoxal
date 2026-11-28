"""K04 candidate normalizes one pinned source typo and uses native event IDs."""
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/regions"))
from k04_gameplay import TRAINERS, center_anchor, clean_trainer_source, trainer_event, trainer_profiles
from pbs import trainer_draft
from pilot import command
from server.ruby_marshal import RubyObject


def actor(label, script, trigger=2):
    return RubyObject("RPG::Event", {"@name": label, "@pages": [RubyObject("RPG::Event::Page", {
        "@trigger": trigger,
        "@condition": RubyObject("RPG::Event::Page::Condition", {"@switch1_valid": False}),
        "@graphic": RubyObject("RPG::Event::Page::Graphic", {"@character_name": b"actor"}),
        "@list": [command(355, script)],
    })]})


class GameplayTests(unittest.TestCase):
    def test_allen_has_one_native_profile_and_two_distinct_event_victory_keys(self):
        teams = {f"{sid}/{eid}": {key: []} for sid, rows in TRAINERS.items() for eid, key in rows.items()}
        self.assertEqual(len(teams), 30)
        self.assertEqual(len(trainer_profiles({"trainers": teams})), 29)
        for eid in (1, 25):
            original = actor(b"Trainer(3)", b"foreign logic")
            result = trainer_event(original, 91, eid, "HIKER,Allen", b"native-sprite")
            first, after = (page.attrs for page in result.attrs["@pages"])
            self.assertEqual(first["@trigger"], 2)
            self.assertEqual(after["@trigger"], 0)
            self.assertTrue(after["@condition"].attrs["@self_switch_valid"])
            scripts = [op.attrs["@parameters"][0] for op in first["@list"] if op.attrs["@code"] == 355]
            self.assertIn(f'BlueKantoPilot.battle(:BLUE_KANTO_HIKER, "Allen", "KANTO_091_{eid:03d}")'.encode(), scripts)
            self.assertNotIn(b"foreign logic", scripts)
        with self.assertRaisesRegex(ValueError, "profile changed"):
            trainer_profiles({"trainers": {k: v for k, v in teams.items() if k != "91/25"}})

    def test_normalization_is_exact_and_donor_pbs_is_immutable(self):
        with TemporaryDirectory() as tmp:
            original = Path(tmp)/"raw.txt"
            clean = Path(tmp)/"clean.txt"
            fixture = "[PICNICKER,Alicia]\nLoseText = example\nx\nPokemon = ODDISH,18\n"
            original.write_text(fixture, encoding="utf-8")
            specs = {"PICNICKER,Alicia": ("PICNICKER", "Alicia", 0)}
            clean_trainer_source(original, clean, specs)
            self.assertEqual(original.read_text(encoding="utf-8"), fixture)
            self.assertIn("Pokemon = ODDISH,18", trainer_draft(clean, {"ODDISH"}, set(), set(), specs))
            original.write_text(fixture + "bad field\n", encoding="utf-8")
            clean_trainer_source(original, clean, specs)
            with self.assertRaisesRegex(ValueError, "requires manual review"):
                trainer_draft(clean, {"ODDISH"}, set(), set(), specs)

    def test_center_requires_a_unique_original_visible_healing_event(self):
        donor = RubyObject("RPG::Map", {"@events": {
            2: actor(b"Nurse", b"pbSetPokemonCenter", 0),
            3: actor(b"Bystander", b'pbMessage("Center")', 0),
        }})
        self.assertEqual(center_anchor(donor), 2)
        donor.attrs["@events"][4] = actor(b"Duplicate", b"pbHealAll", 0)
        with self.assertRaisesRegex(ValueError, "one original visible nurse"):
            center_anchor(donor)


if __name__ == "__main__":
    unittest.main()
