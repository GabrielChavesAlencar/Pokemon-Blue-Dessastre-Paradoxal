"""Stage 09: native Blue rival PBS learns moves legally and stays offline."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from build_johto_rival_pbs_v2 import (
    build, publish, level_up_moves, read_blocks_from_bytes, validate_stage08
)

MOVES = {
    "CHIKORITA": "1,GROWL,1,TACKLE,6,RAZORLEAF",
    "CYNDAQUIL": "1,LEER,1,TACKLE,6,SMOKESCREEN",
    "TOTODILE": "1,LEER,1,SCRATCH,6,WATERGUN",
}


def fixture(root: Path) -> Path:
    game = root / "game"
    pbs = game / "PBS"
    pbs.mkdir(parents=True)
    (pbs / "trainer_types.txt").write_text(
        "[RIVAL1]\nName = Rival\nGender = Male\nBaseMoney = 16\n", encoding="utf-8")
    lines = []
    for species, moves in MOVES.items():
        lines.extend([
            f"[{species}]", f"Name = {species}", "Types = GRASS",
            "BaseStats = 45,49,65,45,49,65", "Abilities = OVERGROW",
            f"Moves = {moves}"
        ])
    (pbs / "pokemon.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (pbs / "moves.txt").write_text(
        "\n".join(f"[{name}]\nName = {name}" for name in
                  ("GROWL", "TACKLE", "RAZORLEAF", "LEER",
                   "SMOKESCREEN", "SCRATCH", "WATERGUN")) + "\n", encoding="utf-8")
    (pbs / "trainers.txt").write_text(
        "[YOUNGSTER,Test]\nPokemon = RATTATA,5\n", encoding="utf-8")
    return game


class JohtoRivalPBSV2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="johto-pbs09-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game = fixture(self.root)

    def test_exactly_three_teams_using_legal_level_five_moves(self):
        report, files = build(self.game)
        self.assertEqual([v["rival_species"] for v in report["versions"]],
                         ["CYNDAQUIL", "TOTODILE", "CHIKORITA"])
        self.assertEqual([v["moves"] for v in report["versions"]],
                         [["LEER", "TACKLE"], ["LEER", "SCRATCH"],
                          ["GROWL", "TACKLE"]])
        self.assertEqual([v["level"] for v in report["versions"]], [5, 5, 5])
        blocks = read_blocks_from_bytes(files["PBS/trainers_johto.txt"])
        self.assertEqual(set(blocks),
                         {f"BLUE_JOHTO_RIVAL,Rival,{v}" for v in range(3)})
        self.assertTrue(all(len(lines) == 2 for lines in blocks.values()))
        self.assertEqual(len(files), 2)
        self.assertEqual(report["native_trainer_type_source"], "RIVAL1")
        self.assertFalse(report["pbs_compiled"])
        self.assertFalse(report["battle_proven"])
        self.assertFalse(report["can_install"])
        self.assertFalse(report["ready_marker_created"])

    def test_only_moves_from_native_learnset_at_or_below_five(self):
        self.assertEqual(level_up_moves("CHIKORITA", {
            "Moves": "0,GROWL,1,TACKLE,6,RAZORLEAF,9,POISONPOWDER"
        }, {"GROWL", "TACKLE", "RAZORLEAF", "POISONPOWDER"}),
            ["GROWL", "TACKLE"])
        self.assertEqual(level_up_moves("CYNDAQUIL", {
            "Moves": "1,LEER,1,TACKLE,1,LEER,6,SMOKESCREEN"
        }, {"LEER", "TACKLE", "SMOKESCREEN"}), ["TACKLE", "LEER"])

    def test_rejects_undefined_or_malformed_moves(self):
        for moves in ("1,FAKEMOVE", "1,GROWL,5", "foo,GROWL", "8,GROWL"):
            with self.subTest(moves=moves):
                with self.assertRaisesRegex(ValueError,
                                            "golpe|Golpe|Learnset|Nível|Nenhum"):
                    level_up_moves("CHIKORITA", {"Moves": moves}, {"GROWL"})

    def test_missing_species_fails_closed(self):
        path = self.game / "PBS/pokemon.txt"
        path.write_text(path.read_text("utf-8").replace(
            "[CHIKORITA]", "[CHIKORITO]"), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ausentes"):
            build(self.game)

    def test_missing_move_and_move_catalogue_fails_closed(self):
        path = self.game / "PBS/moves.txt"
        path.write_text("[LEER]\nName = Leer\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "não definido"):
            build(self.game)
        path.unlink()
        with self.assertRaisesRegex(ValueError, "obrigatórios"):
            build(self.game)

    def test_type_collision_or_missing_native_rival1_blocked(self):
        path = self.game / "PBS/trainer_types.txt"
        path.write_text(
            "[RIVAL1]\nName = Rival\nGender = Male\nBaseMoney = 16\n"
            "[BLUE_JOHTO_RIVAL]\nName = Fake\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicado"):
            build(self.game)
        path.write_text("[YOUNGSTER]\nName = Kid\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "RIVAL1"):
            build(self.game)

    def test_trainer_collision_in_other_pbs_blocked(self):
        (self.game / "PBS/trainers_extra.txt").write_text(
            "[BLUE_JOHTO_RIVAL,Rival,0]\nPokemon = CYNDAQUIL,5\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "duplicado"):
            build(self.game)

    def test_publish_only_in_new_work_folder_preserves_native_and_no_marker(self):
        before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in (self.game / "PBS").iterdir()}
        output = self.root / ".blue-work/out09"
        report = publish(self.game, output, root=self.root)
        self.assertEqual(report["versions"][0]["version"], 0)
        after = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in (self.game / "PBS").iterdir()}
        self.assertEqual(before, after)
        self.assertFalse((self.game / "Data/blue-johto-rival-ready.txt").exists())
        self.assertEqual(len(list((output / "PBS").iterdir())), 2)
        self.assertFalse(json.loads((output / "johto-pbs09-report.json")
                                    .read_text("utf-8"))["story_stage08"]["linked"])
        with self.assertRaisesRegex(ValueError, "NOVA"):
            publish(self.game, output, root=self.root)
        with self.assertRaisesRegex(ValueError, "NOVA"):
            publish(self.game, self.game / "PBS/evil", root=self.root)

    def test_rejects_stage08_outside_private_work_folder(self):
        with self.assertRaisesRegex(ValueError, "Stage08"):
            validate_stage08(self.root / "game")

    def test_report_has_pinned_hashes_and_does_not_certify_graphics_or_engine(self):
        report, files = build(self.game)
        self.assertEqual(len(report["source_pbs_sha256"]), 3)
        self.assertTrue(report["levels"].startswith("LEVEL_5_FIRST_ENCOUNTER_ONLY"))
        self.assertIn("PENDING", report["trainer_graphic"])
        for name, data in files.items():
            self.assertEqual(hashlib.sha256(data).hexdigest(),
                             report["files_sha256"][name])
        self.assertEqual(report["story_stage08"],
                         {"linked": False, "story_events_compiled_in_game": False})


if __name__ == "__main__":
    unittest.main()
