"""CH08: exhaustive Barry PBS version/seed and false-approval regressions."""
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
    MATCHUPS, PBS_TRAINERS, PBS_TYPE, READY_MARKER, build, publish
)
from verify_sinnoh_barry_pbs import inspect
from test_sinnoh_barry_pbs import fixture


class SinnohBarryCh08Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = fixture(self.root)
        self.draft = self.root / ".blue-work/sinnoh-barry-ch08"
        publish(self.game, self.draft, root=self.root)

    def manifest(self):
        return json.loads((self.draft / "sinnoh-barry-pbs-report.json").read_text("utf-8"))

    def write(self, record):
        (self.draft / "sinnoh-barry-pbs-report.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def expect_block(self, reason):
        with self.assertRaisesRegex(ValueError, reason):
            inspect(self.draft, self.game, root=self.root)

    def test_three_versions_counter_species_and_native_moves(self):
        report = self.manifest()
        self.assertEqual(len(report["versions"]), 3)
        self.assertEqual([(r["player_starter"], r["rival_species"])
                          for r in report["versions"]], list(MATCHUPS))
        self.assertEqual([r["version"] for r in report["versions"]], [0, 1, 2])
        self.assertEqual([r["seed_level_only"] for r in report["versions"]], [5, 5, 5])
        self.assertTrue(report["pbs_seed_is_not_final_battle_level"])
        self.assertEqual(report["balance"]["normal_percent"], 70)
        self.assertEqual(report["balance"]["master_percent"], 90)
        self.assertFalse(report["dynamic_scaling_verified_in_game"])
        result = inspect(self.draft, self.game, root=self.root)
        self.assertEqual(result["teams_verified"], 3)
        self.assertFalse(result["native_scaling_executed"])
        self.assertFalse(result["may_install_into_game"])

    def test_absent_team_or_type_pbs_fail_closed(self):
        for rel in (PBS_TRAINERS, PBS_TYPE):
            with self.subTest(rel=rel):
                path = self.draft / rel
                raw = path.read_bytes()
                path.unlink()
                self.expect_block("ausente|SHA-256")
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)

    def test_native_source_missing_blocks_generation(self):
        for rel in ("PBS/pokemon.txt", "PBS/moves.txt",
                    "PBS/trainer_types.txt", "PBS/trainers.txt"):
            with self.subTest(rel=rel):
                path = self.game / rel
                raw = path.read_bytes()
                path.unlink()
                if rel == "PBS/trainers.txt":
                    # Baseline trainers.txt not an input in the current builder,
                    # but no compiled Barry proof or in-game authorization follows.
                    report, files = build(self.game, root=self.root)
                    self.assertFalse(report["can_install"])
                    self.assertFalse(report["ready_marker_created"])
                else:
                    with self.assertRaises(ValueError):
                        build(self.game, root=self.root)
                path.write_bytes(raw)

    def test_wrong_counter_version_and_seed_manifest_are_rejected(self):
        for index in range(3):
            for field, wrong in (
                ("version", (index + 1) % 3),
                ("player_starter", "PIKACHU"),
                ("rival_species", "RATTATA"),
                ("seed_level_only", 7),
                ("effective_level", "5"),
                ("handler", "TrainerBattle.start(:FAKE_RIVAL, 'Barry', 0)"),
            ):
                with self.subTest(index=index, field=field):
                    report = self.manifest()
                    report["versions"][index][field] = wrong
                    self.write(report)
                    self.expect_block("Versão PBS|handler|nivel dinamico")
                    self.write_base()
        self.assertFalse((self.game / READY_MARKER).exists())

    def write_base(self):
        # Rebuild in memory without rewriting game or touching ready marker.
        report, _ = build(self.game, root=self.root)
        self.write(report)

    def test_falsely_published_levels_and_approval_flags_are_rejected(self):
        changes = [
            ("pbs_seed_level", 7),
            ("pbs_seed_is_not_final_battle_level", False),
            ("ready_marker_filename", "Data/ready.txt"),
            ("trainer_type", "RIVAL1"),
            ("trainer_name", "Other"),
            ("can_install", True),
            ("pbs_compiled", True),
            ("ready_marker_allowed", True),
            ("ready_marker_created", True),
            ("battle_proven", True),
            ("dynamic_scaling_verified_in_game", True),
            ("graphic_verified", True),
            ("save_load_verified", True),
        ]
        for field, bad in changes:
            with self.subTest(field=field):
                report = self.manifest()
                report[field] = bad
                self.write(report)
                self.expect_block("adulterados|incorreto|falsa aprovação")
                self.write_base()

    def test_zero_or_extra_rival_version_cannot_be_hidden_by_hash(self):
        for replacement in (
            ("[BLUE_SINNOH_RIVAL,Barry,2]", "[BLUE_SINNOH_RIVAL,Barry,9]"),
            ("Pokemon = CHIMCHAR,5", "Pokemon = CHIMCHAR,7"),
            ("Pokemon = PIPLUP,5", "Pokemon = TURTWIG,5"),
        ):
            with self.subTest(replacement=replacement):
                teamfile = self.draft / PBS_TRAINERS
                original = teamfile.read_bytes()
                modified = original.decode("utf-8").replace(*replacement, 1).encode("utf-8")
                self.assertNotEqual(modified, original)
                teamfile.write_bytes(modified)
                report = self.manifest()
                report["files_sha256"][PBS_TRAINERS] = hashlib.sha256(modified).hexdigest()
                self.write(report)
                self.expect_block("três treinadores|adulterado|Versão")
                teamfile.write_bytes(original)
                self.write_base()

    def test_extra_native_starter_or_missing_starter_is_rejected(self):
        for keys in (["TURTWIG", "CHIMCHAR"], ["TURTWIG", "CHIMCHAR", "PIPLUP", "PIKACHU"]):
            with self.subTest(keys=keys):
                report = self.manifest()
                report["native_starters"] = {s: report["native_starters"].get(
                    s, report["native_starters"]["PIPLUP"]) for s in keys}
                self.write(report)
                self.expect_block("três equipes")
                self.write_base()

    def test_fake_70_90_or_changed_campaign_runtime_is_rejected(self):
        report = self.manifest()
        report["balance"]["master_percent"] = 70
        self.write(report)
        self.expect_block("Runtime de balanceamento")
        self.write_base()
        path = self.root / "scripts/battle_polish/Campaign.rb"
        content = path.read_text("utf-8")
        path.write_text(content + "\n# verified source changed\n", encoding="utf-8")
        self.expect_block("Runtime de balanceamento")
        path.write_text(content, encoding="utf-8")
        self.assertEqual(inspect(self.draft, self.game, root=self.root)["teams_verified"], 3)

    def test_no_game_or_save_modified_or_ready_marker_created(self):
        before = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.game.rglob("*") if p.is_file()}
        inspect(self.draft, self.game, root=self.root)
        after = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.game.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((self.draft / READY_MARKER).exists())
        self.assertFalse((self.game / READY_MARKER).exists())


if __name__ == "__main__":
    unittest.main()
