"""Rival de Johto: PBS de três equipes é rascunho validado, nunca liberado."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from draft_johto_rival_pbs import build, publish
finally:
    sys.path.pop(0)


def fixture(root):
    game = root / "game"
    pbs = game / "PBS"
    pbs.mkdir(parents=True)
    (pbs / "trainer_types.txt").write_text(
        "[RIVAL1]\nName = Rival\nGender = Male\nBaseMoney = 100\nSkillLevel = 50\n",
        encoding="utf-8")
    (pbs / "pokemon.txt").write_text(
        "[CHIKORITA]\nName = Chikorita\n[CYNDAQUIL]\nName = Cyndaquil\n"
        "[TOTODILE]\nName = Totodile\n", encoding="utf-8")
    (pbs / "trainers.txt").write_text(
        "[YOUNGSTER,Test]\nPokemon = RATTATA,5\n", encoding="utf-8")
    return game


class JohtoRivalPBSTests(unittest.TestCase):
    def test_generates_native_essentials_format_for_three_starters(self):
        with tempfile.TemporaryDirectory() as t:
            game = fixture(Path(t))
            report, files = build(game)
            self.assertFalse(report["pbs_compiled"])
            self.assertFalse(report["can_install"])
            self.assertFalse(report["battle_proven"])
            trainer = files["PBS/trainers_johto.txt"].decode("utf-8")
            self.assertIn("[BLUE_JOHTO_RIVAL,Rival,0]", trainer)
            self.assertIn("[BLUE_JOHTO_RIVAL,Rival,1]", trainer)
            self.assertIn("[BLUE_JOHTO_RIVAL,Rival,2]", trainer)
            self.assertEqual(trainer.count("Pokemon = "), 3)
            self.assertEqual(trainer.count(",5"), 3)
            self.assertEqual([x["rival_species"] for x in report["versions"]],
                             ["CYNDAQUIL", "TOTODILE", "CHIKORITA"])
            self.assertIn("[BLUE_JOHTO_RIVAL]",
                          files["PBS/trainer_types_johto.txt"].decode("utf-8"))

    def test_rejects_missing_species_or_type_or_type_collision(self):
        with tempfile.TemporaryDirectory() as t:
            game = fixture(Path(t))
            (game / "PBS/pokemon.txt").write_text("[CHIKORITA]\n", "utf-8")
            with self.assertRaisesRegex(ValueError, "ausentes"):
                build(game)
            (game / "PBS/pokemon.txt").write_text(
                "[CHIKORITA]\n[CYNDAQUIL]\n[TOTODILE]\n", "utf-8")
            (game / "PBS/trainer_types.txt").write_text("[YOUNGSTER]\nName = Kid\n", "utf-8")
            with self.assertRaisesRegex(ValueError, "RIVAL1"):
                build(game)
            (game / "PBS/trainer_types.txt").write_text(
                "[RIVAL1]\nName = Rival\n[BLUE_JOHTO_RIVAL]\nName = Fake\n", "utf-8")
            with self.assertRaisesRegex(ValueError, "existe BLUE_JOHTO_RIVAL"):
                build(game)

    def test_no_writes_to_game_or_ready_marker(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            game = fixture(root)
            original = (game / "PBS/trainers.txt").read_bytes()
            result = publish(game, root / ".blue-work/rival", root=root)
            self.assertFalse(result["battle_proven"])
            self.assertEqual(original, (game / "PBS/trainers.txt").read_bytes())
            self.assertFalse((game / "Data/blue-johto-rival-ready.txt").exists())
            self.assertTrue((root / ".blue-work/rival/PBS/trainers_johto.txt").is_file())
            with self.assertRaisesRegex(ValueError, "NOVO"):
                publish(game, root / ".blue-work/rival", root=root)
            with self.assertRaisesRegex(ValueError, "NOVO"):
                publish(game, game / "johto-overwrite", root=root)


if __name__ == "__main__":
    unittest.main()
