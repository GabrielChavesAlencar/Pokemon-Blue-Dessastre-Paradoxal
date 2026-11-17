"""Regression: safe Mt. Moon fossil anchors, exclusive choice and Cinnabar revival."""
from __future__ import annotations
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from pilot import source_mt_moon_fossil, command, TRAINERS
finally:
    sys.path.remove(str(ROOT / "scripts/regions"))


def native_event(name=b"fossil", script=None, event_id=20):
    commands = [command(355, script.encode())] if script else [command(0)]
    page = SimpleNamespace(attrs={"@list": commands})
    return SimpleNamespace(attrs={
        "@id": event_id, "@name": name, "@pages": [page],
    })


class KantoFossilRegression(unittest.TestCase):
    def test_01_original_fossil_names_are_exact(self):
        for name, item in [
            (b"Item:HELIXFOSSIL", "HELIXFOSSIL"),
            (b"Dome Fossil", "DOMEFOSSIL"),
            (b"HELIXFOSSIL", "HELIXFOSSIL"),
        ]:
            with self.subTest(name=name):
                self.assertEqual(source_mt_moon_fossil(native_event(name)), item)

    def test_02_source_scripting_recovers_item_and_not_dialogue(self):
        self.assertEqual(source_mt_moon_fossil(
            native_event(b"Fossil Left", "pbReceiveItem(:HELIXFOSSIL)"
        )), "HELIXFOSSIL")
        self.assertEqual(source_mt_moon_fossil(
            native_event(b"Fossil Right", "pbItemBall(:DOMEFOSSIL)"
        )), "DOMEFOSSIL")
        for name, script in [
            (b"Professor fossil", None),
            (b"Talk: HELIXFOSSIL", "pbMessage('Take this fossil!')"),
            (b"Item:HELIXFOSSIL", "pbItemBall(:DOMEFOSSIL)"),
        ]:
            with self.subTest(name=name):
                self.assertIsNone(source_mt_moon_fossil(native_event(name, script)))

    def test_03_source_scientist_identity_is_stable(self):
        self.assertEqual(TRAINERS[38][19], ("SUPERNERD", "Miguel"))
        src = (ROOT / "scripts/regions/pilot.py").read_text(encoding="utf-8")
        self.assertIn('BlueKantoPilot.choose_moon_fossil(:{item})', src)
        self.assertIn('"@self_switch_valid": True', src)
        self.assertIn('if original == 38 and event_id in fossil_anchors:', src)

    def test_04_existing_saves_get_a_callback_without_map_rewrite(self):
        ruby = (ROOT / "scripts/regions/KantoPilot.rb").read_text(encoding="utf-8")
        self.assertIn('key == "KANTO_038_019"', ruby)
        self.assertIn('progress["pilot_mt_moon_fossil"]', ruby)
        self.assertIn('choose_moon_fossil unless moon_fossil_props?', ruby)
        self.assertIn('BlueKantoPilot.in_cinnabar_lab?', ruby)
        self.assertIn('def self.revive_cinnabar_fossil', ruby)
        self.assertIn('return false unless $bag.remove(item, 1)', ruby)
        self.assertIn('unless pbAddPokemonSilent(species, 5)', ruby)
        self.assertIn('$bag.add(item, 1)', ruby)

    def test_05_regional_choice_and_rewards_are_explicit(self):
        ruby = (ROOT / "scripts/regions/KantoPilot.rb").read_text(encoding="utf-8")
        self.assertIn('HELIXFOSSIL: :OMANYTE, DOMEFOSSIL: :KABUTO', ruby)
        self.assertIn('OLDAMBER: :AERODACTYL', ruby)
        self.assertIn('progress["pilot_mt_moon_fossil"] = choice.to_s', ruby)
        self.assertIn('progress.fetch("pilot_wins", [])', ruby)
        self.assertIn('in_cinnabar_lab?', ruby)

    def test_06_android_hotfix_compiles_kanto_script(self):
        script = (ROOT / "scripts/android/repack_multiregion_hotfix.py").read_text(encoding="utf-8")
        self.assertIn('replace_compiled_kanto(', script)
        self.assertIn('KANTO_MANIFEST', script)
        self.assertIn('"KantoPilot.rb"', script)
        self.assertIn('proof.get("installed_sha256")', script)


if __name__ == "__main__":
    unittest.main()
