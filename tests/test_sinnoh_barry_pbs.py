"""Barry's three PBS drafts use owned synthetic files, not donor assets."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from build_sinnoh_barry_pbs import (
    MATCHUPS, PBS_TRAINERS, PBS_TYPE, READY_MARKER, SEED_LEVEL,
    balance_contract, build, legal_moves, publish
)
from build_johto_rival_pbs_v2 import read_blocks_from_bytes


LEARNSETS = {
    "TURTWIG": "1,TACKLE,5,WITHDRAW,6,RAZORLEAF",
    "CHIMCHAR": "1,SCRATCH,1,LEER,7,EMBER",
    "PIPLUP": "1,POUND,4,GROWL,8,BUBBLE",
}


def fixture(root: Path) -> Path:
    game = root / "game"
    pbs = game / "PBS"
    pbs.mkdir(parents=True, exist_ok=True)
    (pbs / "trainer_types.txt").write_text(
        "[RIVAL1]\nName = Rival\nGender = Male\nBaseMoney = 16\n",
        encoding="utf-8",
    )
    lines = []
    for species, learnset in LEARNSETS.items():
        lines.extend((
            f"[{species}]",
            f"Name = {species}",
            "Types = GRASS" if species == "TURTWIG" else
            ("Types = FIRE" if species == "CHIMCHAR" else "Types = WATER"),
            "BaseStats = 55,68,64,45,45,55",
            "Abilities = OVERGROW" if species == "TURTWIG" else "Abilities = BLAZE" if species == "CHIMCHAR" else "Abilities = TORRENT",
            f"Moves = {learnset}",
        ))
    (pbs / "pokemon.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    moves = ["TACKLE", "WITHDRAW", "RAZORLEAF", "SCRATCH", "LEER",
             "EMBER", "POUND", "GROWL", "BUBBLE"]
    (pbs / "moves.txt").write_text(
        "\n".join(f"[{move}]\nName = {move}" for move in moves) + "\n",
        encoding="utf-8",
    )
    (pbs / "trainers.txt").write_text(
        "[YOUNGSTER,Test]\nPokemon = RATTATA,5\n", encoding="utf-8",
    )
    # Builder resolves the Blue's native scaling source inside this fake root.
    src = root / "scripts/battle_polish/Campaign.rb"
    src.parent.mkdir(parents=True)
    src.write_text((
        "module BlueCampaign\n"
        "def self.scaled_level(party,percent); end\n"
        "master? ? 90 : 70\n"
        "def self.trainer_level(trainer,party=$player.party); end\n"
        "level=BlueCampaign.trainer_level(args[4])\n"
        "pkmn.level=level\n"
        "BlueCampaign.active?\n"
        "end\n"
    ), encoding="utf-8")
    return game


class SinnohBarryPBSTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.game = fixture(self.root)

    def test_exactly_three_starter_counter_versions_and_legal_moves(self):
        manifest, files = build(self.game, root=self.root)
        self.assertEqual([x["player_starter"] for x in manifest["versions"]],
                         ["TURTWIG", "CHIMCHAR", "PIPLUP"])
        self.assertEqual([x["rival_species"] for x in manifest["versions"]],
                         ["CHIMCHAR", "PIPLUP", "TURTWIG"])
        self.assertEqual([x["moves_at_seed_level"] for x in manifest["versions"]],
                         [["SCRATCH", "LEER"], ["POUND", "GROWL"],
                          ["TACKLE", "WITHDRAW"]])
        self.assertEqual(set(files), {PBS_TYPE, PBS_TRAINERS})
        blocks = read_blocks_from_bytes(files[PBS_TRAINERS])
        self.assertEqual(set(blocks), {
            "BLUE_SINNOH_RIVAL,Barry,0",
            "BLUE_SINNOH_RIVAL,Barry,1",
            "BLUE_SINNOH_RIVAL,Barry,2",
        })
        self.assertEqual([x["seed_level_only"] for x in manifest["versions"]], [5, 5, 5])
        self.assertTrue(manifest["pbs_seed_is_not_final_battle_level"])
        self.assertEqual(manifest["balance"]["normal_percent"], 70)
        self.assertEqual(manifest["balance"]["master_percent"], 90)
        self.assertTrue(manifest["balance"]["static_source_contract_checked"])
        self.assertFalse(manifest["balance"]["active_in_actual_game_verified"])

    def test_report_never_installs_pbs_or_creates_ready_marker(self):
        result, files = build(self.game, root=self.root)
        for name, contents in files.items():
            self.assertEqual(hashlib.sha256(contents).hexdigest(),
                             result["files_sha256"][name])
        self.assertEqual(result["ready_marker_filename"], READY_MARKER)
        for name in ("can_install", "pbs_compiled", "battle_proven",
                     "dynamic_scaling_verified_in_game", "graphic_verified",
                     "ready_marker_created", "ready_marker_allowed", "save_load_verified"):
            self.assertIs(result[name], False, name)
        self.assertFalse((self.game / READY_MARKER).exists())

    def test_only_native_moves_at_or_below_level_five(self):
        self.assertEqual(legal_moves("TURTWIG", {
            "Moves": "1,TACKLE,1,WITHDRAW,1,TACKLE,6,RAZORLEAF",
        }, {"TACKLE", "WITHDRAW", "RAZORLEAF"}), ["WITHDRAW", "TACKLE"])
        for learnset in ("9,TACKLE", "foo,TACKLE", "1,TACKLE,4", "1,FAKE"):
            with self.subTest(learnset=learnset):
                with self.assertRaises(ValueError):
                    legal_moves("TURTWIG", {"Moves": learnset}, {"TACKLE"})

    def test_native_species_and_missing_moves_are_rejected(self):
        file = self.game / "PBS/pokemon.txt"
        file.write_text(file.read_text("utf-8").replace("[TURTWIG]", "[MISSING_TURTWIG]"),
                        encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "ausentes"):
            build(self.game, root=self.root)
        fixture(self.root)
        move_file = self.game / "PBS/moves.txt"
        move_file.write_text("[TACKLE]\nName = Tackle\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "não definido"):
            build(self.game, root=self.root)

    def test_rejects_type_and_trainer_collisions_in_any_pbs_extension(self):
        (self.game / "PBS/trainer_types_alt.txt").write_text(
            "[BLUE_SINNOH_RIVAL]\nName = Fake\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "já existe"):
            build(self.game, root=self.root)
        (self.game / "PBS/trainer_types_alt.txt").unlink()
        (self.game / "PBS/trainers_alt.txt").write_text(
            "[BLUE_SINNOH_RIVAL,Barry,99]\nPokemon = PIPLUP,5\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "já existe"):
            build(self.game, root=self.root)

    def test_rejects_wrong_native_rival_type_and_malformed_fields(self):
        typ = self.game / "PBS/trainer_types.txt"
        typ.write_text("[YOUNGSTER]\nName = Youngster\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "RIVAL1"):
            build(self.game, root=self.root)
        typ.write_text("[RIVAL1]\nName = Rival\nGender = Male\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "BaseMoney"):
            build(self.game, root=self.root)

    def test_does_not_claim_dynamic_scaling_if_runtime_code_changed(self):
        scale = self.root / "scripts/battle_polish/Campaign.rb"
        scale.write_text("module BlueCampaign; def self.trainer_level(t); 5; end; end",
                         encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Escala nativa"):
            build(self.game, root=self.root)

    def test_rejects_corrupt_base_stats_missing_moves_and_incomplete_pbs(self):
        pok = self.game / "PBS/pokemon.txt"
        pok.write_text(pok.read_text("utf-8").replace(
            "BaseStats = 55,68,64,45,45,55", "BaseStats = 1,2,3", 1),
            encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "BaseStats"):
            build(self.game, root=self.root)
        pok.unlink()
        with self.assertRaisesRegex(ValueError, "pokemon.txt"):
            build(self.game, root=self.root)

    def test_publish_creates_only_new_ignored_workspace_and_preserves_game(self):
        originals = {
            p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (self.root / "game").rglob("*") if p.is_file()
        }
        target = self.root / ".blue-work/sinnoh-barry-pbs"
        report = publish(self.game, target, root=self.root)
        self.assertTrue((target / PBS_TRAINERS).is_file())
        self.assertTrue((target / PBS_TYPE).is_file())
        self.assertTrue((target / "sinnoh-barry-pbs-report.json").is_file())
        self.assertFalse((target / READY_MARKER).exists())
        self.assertFalse((self.game / READY_MARKER).exists())
        self.assertFalse(report["can_install"])
        after = {
            p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (self.root / "game").rglob("*") if p.is_file()
        }
        self.assertEqual(originals, after)
        with self.assertRaisesRegex(ValueError, "NOVA"):
            publish(self.game, target, root=self.root)
        with self.assertRaisesRegex(ValueError, "NOVA"):
            publish(self.game, self.game / "PBS/evil", root=self.root)

    def test_output_does_not_contain_unverified_levels_as_gameplay_claim(self):
        report, _ = build(self.game, root=self.root)
        self.assertEqual(report["pbs_seed_level"], SEED_LEVEL)
        self.assertEqual(report["versions"][0]["effective_level"],
                         "BlueCampaign.trainer_level(player_party) at runtime")
        self.assertEqual(report["stage"], "BARRY_FIRST_RIVAL_3_VERSION_PBS_DRAFT")
        self.assertNotIn("READY", report["status"])
        self.assertEqual(report["versions"][0]["version"], 0)
        self.assertEqual(report["versions"][1]["version"], 1)
        self.assertEqual(report["versions"][2]["version"], 2)


if __name__ == "__main__":
    unittest.main()
