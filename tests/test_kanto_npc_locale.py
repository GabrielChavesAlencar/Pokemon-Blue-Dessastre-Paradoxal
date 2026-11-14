"""Kanto NPC Portuguese: source-faithful, local-only, isolated regression tests."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    import kanto_npc_locale
    from kanto_npc_locale import npc_literals, imported_npc_lines, install_npc_locale
    from translate_kanto_npcs import safe_translate, current_pilot
    from pilot import command, npc_dialogue_calls
    from server.ruby_marshal import RubyObject, dumps_simple, loads, text
finally:
    sys.path.remove(str(ROOT / "scripts/regions"))


def event_dialogue():
    page = RubyObject("RPG::Event::Page", {
        "@trigger": 0,
        "@graphic": RubyObject("RPG::Event::Page::Graphic", {
            "@character_name": b"NPC_Test",
        }),
        "@condition": RubyObject("RPG::Event::Page::Condition", {
            "@self_switch_valid": False
        }),
        "@list": [command(101, b"Hello there!"),
                  command(401, b"How are you?"),
                  command(0)],
    })
    return RubyObject("RPG::Event", {
        "@name": b"Friendly Neighbor", "@id": 7, "@x": 4, "@y": 5,
        "@pages": [page],
    })


class FakeTranslator:
    def translate(self, source):
        return {
            "Hello there! How are you?": "Olá! Como você está?",
        }.get(source, source)


class TestKantoNpcLocale(unittest.TestCase):
    def test_npc_dialogue_extracts_only_real_source_text(self):
        event = event_dialogue()
        from kanto_overworld import source_npc_dialogue
        cmds = source_npc_dialogue(event)
        self.assertEqual(npc_literals(cmds), ["Hello there! How are you?"])
        self.assertEqual(npc_literals([
            command(355, b'pbMessage(_INTL("Nice weather!"))'),
            command(355, b'dangerous_code(:MASTERBALL)'),
        ]), ["Nice weather!"])

    def test_runtime_npc_bridge_preserves_original_source_and_language_choice(self):
        guard = event_dialogue()
        guard.attrs["@pages"][0].attrs["@list"] = [
            command(101, b"I absolutely forbid you from"),
            command(401, b"going through here!"),
            command(0),
        ]
        from kanto_overworld import source_npc_dialogue
        literals = npc_literals(source_npc_dialogue(guard))
        self.assertEqual(literals, ["I absolutely forbid you from going through here!"])
        commands = npc_dialogue_calls(10, 7, literals)
        self.assertEqual([c.attrs["@code"] for c in commands], [355, 0])
        self.assertEqual(commands[0].attrs["@parameters"][0],
                         b"BlueKantoPilot.npc_dialogue(10, 7, 0)")
        # The generated Ruby code contains only numeric identifiers, never
        # external strings that could interpolate or execute arbitrary Ruby.
        self.assertNotIn(b"forbid", commands[0].attrs["@parameters"][0])
        decoded = loads(dumps_simple([[10, 7, literals]]))
        self.assertEqual(text(decoded[0][2][0]), literals[0])
        self.assertEqual(guard.attrs["@pages"][0].attrs["@list"][0]
                         .attrs["@parameters"][0],
                         b"I absolutely forbid you from")
        runtime = (ROOT / "scripts/regions/KantoPilot.rb").read_text("utf8")
        self.assertIn("def self.npc_dialogue(source_map, source_event, index)", runtime)
        self.assertIn("BlueLocale.translate(message)", runtime)
        pilot = (ROOT / "scripts/regions/pilot.py").read_text("utf8")
        self.assertIn('Data/blue-kanto-npc-dialogues.dat', pilot)
        self.assertIn("npc_dialogue_calls(", pilot)

    def test_unsafe_source_dialogue_is_not_bridged(self):
        from kanto_overworld import source_npc_dialogue
        malicious = event_dialogue()
        malicious.attrs["@pages"][0].attrs["@list"] = [
            command(355, b"pbReceiveItem(:MASTERBALL)"), command(0)
        ]
        self.assertIsNone(source_npc_dialogue(malicious))

    def test_local_machine_translation_preserves_game_controls(self):
        translator = FakeTranslator()
        self.assertEqual(safe_translate("Hello there! How are you?", translator),
                         ("Olá! Como você está?", None))
        pt, reason = safe_translate(r"\PN found a Potion!", translator)
        self.assertIsNone(pt)
        self.assertIn("control", reason)
        pt, reason = safe_translate("Hello there! {PLAYER}", translator)
        self.assertIsNone(pt)
        self.assertIn("interpolation", reason)

    def test_only_imported_npc_is_translated_and_decades_is_untouched(self):
        npc = event_dialogue()
        fake_map = RubyObject("RPG::Map", {
            "@events": {7: npc, 8: event_dialogue()},
        })
        inventory = {"schema": 1, "imported": [{
            "kind": "npc_dialogue", "source_map": 24, "map": 602,
            "event": 7, "x": 4, "y": 5
        }]}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "frlg"
            (source / "Data").mkdir(parents=True)
            game = root / "pilot"
            (game / "Data").mkdir(parents=True)
            (game / "Data/blue-kanto-field-events.json").write_text(
                json.dumps(inventory), encoding="utf8")
            baseline = {"Existing Blue line": "Linha existente do Blue"}
            (game / "Data/blue-pt-br.dat").write_bytes(
                dumps_simple([[k, v] for k, v in sorted(baseline.items())]))
            locale = root / ".blue-work/kanto-npc-ptbr.json"
            locale.parent.mkdir()
            locale.write_text(json.dumps({
                "version": 1, "language": "pt-BR",
                "translations": {
                    "Hello there! How are you?": "Olá! Como você está?",
                    "Not a Kanto NPC": "Não é um NPC de Kanto",
                }
            }), encoding="utf8")
            with patch.object(kanto_npc_locale, "load", return_value=fake_map):
                report = install_npc_locale(root, source, game)
            merged = {
                text(k): text(v)
                for k, v in loads((game / "Data/blue-pt-br.dat").read_bytes())
            }
            self.assertEqual(merged["Existing Blue line"],
                             "Linha existente do Blue")
            self.assertEqual(merged["Hello there! How are you?"],
                             "Olá! Como você está?")
            self.assertNotIn("Not a Kanto NPC", merged)
            self.assertEqual(report["total_npc_events"], 1)
            self.assertEqual(report["remaining_unique_lines"], 0)
            # Compiled source data and original FRLG event are not mutated.
            self.assertEqual(npc.attrs["@pages"][0].attrs["@list"][0]
                             .attrs["@parameters"][0], b"Hello there!")

    def test_screenshot_guard_translation_is_built_in_without_external_model(self):
        # Screenshot: the player selected Portuguese, but this FRLG guard
        # still said "I absolutely forbid you from going through here!".
        guard = event_dialogue()
        guard.attrs["@pages"][0].attrs["@list"] = [
            command(101, b"I absolutely forbid you from"),
            command(401, b"going through here!"),
            command(0),
        ]
        inventory = {"schema": 1, "imported": [{
            "kind": "npc_dialogue", "source_map": 10, "map": 610,
            "event": 7, "x": 4, "y": 5
        }]}
        self.assertEqual(npc_literals(guard.attrs["@pages"][0].attrs["@list"]),
                         ["I absolutely forbid you from going through here!"])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data").mkdir()
            (root / "data/kanto-npc-ptbr.json").write_bytes(
                (ROOT / "data/kanto-npc-ptbr.json").read_bytes())
            source = root / "frlg"
            (source / "Data").mkdir(parents=True)
            target = root / "pilot"
            (target / "Data").mkdir(parents=True)
            (target / "Data/blue-kanto-field-events.json").write_text(
                json.dumps(inventory), encoding="utf8")
            m = RubyObject("RPG::Map", {"@events": {7: guard}})
            with patch.object(kanto_npc_locale, "load", return_value=m):
                report = install_npc_locale(root, source, target)
            result = {text(pair[0]): text(pair[1]) for pair in loads(
                (target / "Data/blue-pt-br.dat").read_bytes())}
            self.assertEqual(
                result["I absolutely forbid you from going through here!"],
                "Está terminantemente proibido passar por aqui!")
            self.assertEqual(report["remaining_unique_lines"], 0)
            self.assertEqual(report["reviewed_project_translations"], 1)
            # No private Argos package, translator invocation or cache needed.
            self.assertFalse((root / ".blue-work/kanto-npc-ptbr.json").exists())

    def test_screenshot_clefairy_phrase_is_translated_without_argos(self):
        # Actual screenshot: pt-BR is selected but the Pewter NPC says
        # "Clefairy came from the moon. That's what the rumor is."
        npc = event_dialogue()
        npc.attrs["@pages"][0].attrs["@list"] = [
            command(101, b"Clefairy came from the moon."),
            command(401, b"That's what the rumor is."),
            command(0),
        ]
        inventory = {"schema": 1, "imported": [{
            "kind": "npc_dialogue", "source_map": 25, "map": 625,
            "event": 7, "x": 4, "y": 5
        }]}
        english = "Clefairy came from the moon. That's what the rumor is."
        self.assertEqual(npc_literals(npc.attrs["@pages"][0].attrs["@list"]),
                         [english])
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data").mkdir()
            (root / "data/kanto-npc-ptbr.json").write_bytes(
                (ROOT / "data/kanto-npc-ptbr.json").read_bytes())
            source = root / "frlg"
            (source / "Data").mkdir(parents=True)
            target = root / "pilot"
            (target / "Data").mkdir(parents=True)
            (target / "Data/blue-kanto-field-events.json").write_text(
                json.dumps(inventory), encoding="utf8")
            with patch.object(kanto_npc_locale, "load", return_value=RubyObject(
                    "RPG::Map", {"@events": {7: npc}})):
                report = install_npc_locale(root, source, target)
            values = {text(a): text(b) for a, b in loads(
                (target / "Data/blue-pt-br.dat").read_bytes())}
            self.assertEqual(values[english],
                             "Clefairy veio da Lua. É isso que dizem por aí.")
            self.assertEqual(report["remaining_unique_lines"], 0)
            self.assertEqual(report["reviewed_project_translations"], 1)

    def test_old_automatic_cache_cannot_override_reviewed_guard(self):
        guard = event_dialogue()
        guard.attrs["@pages"][0].attrs["@list"] = [
            command(101, b"I absolutely forbid you from going through here!"),
            command(0),
        ]
        inventory = {"schema": 1, "imported": [{
            "kind": "npc_dialogue", "source_map": 10, "map": 610,
            "event": 7, "x": 4, "y": 5
        }]}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "data").mkdir()
            (root / "data/kanto-npc-ptbr.json").write_bytes(
                (ROOT / "data/kanto-npc-ptbr.json").read_bytes())
            source = root / "frlg"
            (source / "Data").mkdir(parents=True)
            game = root / "pilot"
            (game / "Data").mkdir(parents=True)
            (game / "Data/blue-kanto-field-events.json").write_text(
                json.dumps(inventory), encoding="utf8")
            cache = root / ".blue-work/kanto-npc-ptbr.json"
            cache.parent.mkdir(parents=True)
            cache.write_text(json.dumps({
                "version": 1, "language": "pt-BR",
                "translation_method": "Argos Translate en-pt, automatic/unreviewed",
                "translations": {
                    "I absolutely forbid you from going through here!":
                        "Eu proíbo você absolutamente de passar aqui!"
                }
            }), encoding="utf8")
            fake_map = RubyObject("RPG::Map", {"@events": {7: guard}})
            with patch.object(kanto_npc_locale, "load", return_value=fake_map):
                install_npc_locale(root, source, game)
            translations = {text(pair[0]): text(pair[1]) for pair in loads(
                (game / "Data/blue-pt-br.dat").read_bytes())}
            self.assertEqual(
                translations["I absolutely forbid you from going through here!"],
                "Está terminantemente proibido passar por aqui!")

    def test_optional_offline_translator_recovers_missing_source_npc_lines(self):
        npc = event_dialogue()
        inventory = {"schema": 1, "imported": [{
            "kind": "npc_dialogue", "source_map": 24, "map": 602,
            "event": 7, "x": 4, "y": 5
        }]}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source"
            (source / "Data").mkdir(parents=True)
            target = root / "pilot"
            (target / "Data").mkdir(parents=True)
            (target / "Data/blue-kanto-field-events.json").write_text(
                json.dumps(inventory), encoding="utf8")
            m = RubyObject("RPG::Map", {"@events": {7: npc}})
            with (patch.object(kanto_npc_locale, "load", return_value=m),
                  patch("translate_kanto_npcs.get_argos_translator",
                        return_value=FakeTranslator())):
                report = install_npc_locale(root, source, target)
            result = {text(pair[0]): text(pair[1]) for pair in loads(
                (target / "Data/blue-pt-br.dat").read_bytes())}
            self.assertEqual(result["Hello there! How are you?"],
                             "Olá! Como você está?")
            self.assertEqual(report["remaining_unique_lines"], 0)
            self.assertEqual(len(report["automatic_unreviewed_translations"]), 1)

    def test_pilot_rebuild_refreshes_bundled_locale_and_curated_catalogue(self):
        pilot = (ROOT / "scripts/regions/pilot.py").read_text("utf8")
        locale = (ROOT / "scripts/battle_polish/Locale.rb").read_text("utf8")
        self.assertIn('"data/kanto-npc-ptbr.json"', pilot)
        self.assertIn('"scripts/battle_polish/Locale.rb"', pilot)
        self.assertIn('"Locale.rb", "KantoDex.rb"', pilot)
        self.assertIn("I absolutely forbid you from going through here!", locale)

    def test_invalid_local_translation_stays_out_of_game(self):
        fake_map = RubyObject("RPG::Map", {
            "@events": {7: event_dialogue()},
        })
        inventory = {"schema": 1, "imported": [{
            "kind": "npc_dialogue", "source_map": 24, "map": 602,
            "event": 7, "x": 4, "y": 5
        }]}
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source"
            (source / "Data").mkdir(parents=True)
            target = root / "pilot"
            (target / "Data").mkdir(parents=True)
            (target / "Data/blue-kanto-field-events.json").write_text(
                json.dumps(inventory), encoding="utf8")
            local = root / ".blue-work/kanto-npc-ptbr.json"
            local.parent.mkdir()
            local.write_text(json.dumps({
                "version": 1, "language": "pt-BR",
                "translations": {
                    "Hello there! How are you?": r"Olá \PN!",
                },
            }), encoding="utf8")
            with (patch.object(kanto_npc_locale, "load", return_value=fake_map),
                  patch("translate_kanto_npcs.get_argos_translator", return_value=None)):
                report = install_npc_locale(root, source, target)
            self.assertEqual(report["localized_unique_lines"], 0)
            self.assertEqual(report["remaining_unique_lines"], 1)
            self.assertTrue(report["invalid_local_translations"])


if __name__ == "__main__":
    unittest.main()
