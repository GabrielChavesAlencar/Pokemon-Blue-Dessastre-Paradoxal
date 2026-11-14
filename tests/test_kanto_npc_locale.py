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
    from pilot import command
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
                dumps_simple(sorted(baseline.items())))
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
            with patch.object(kanto_npc_locale, "load", return_value=fake_map):
                report = install_npc_locale(root, source, target)
            self.assertEqual(report["localized_unique_lines"], 0)
            self.assertEqual(report["remaining_unique_lines"], 1)
            self.assertTrue(report["invalid_local_translations"])


if __name__ == "__main__":
    unittest.main()
