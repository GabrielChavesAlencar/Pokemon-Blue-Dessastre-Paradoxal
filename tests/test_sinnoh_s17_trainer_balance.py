"""S17: negative audit tests for dynamic trainer levels, roster provenance."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_s17_balance import CONTRACT, CH12, CH15, RUBY, audit


class S17TrainerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text("utf-8"))
        cls.evolution = json.loads(CH12.read_text("utf-8"))
        cls.teams = json.loads(CH15.read_text("utf-8"))
        cls.ruby = RUBY.read_text("utf-8")

    def check(self, contract=None, evolution=None, teams=None, source=None):
        return audit(
            copy.deepcopy(self.contract if contract is None else contract),
            copy.deepcopy(self.evolution if evolution is None else evolution),
            copy.deepcopy(self.teams if teams is None else teams),
            ruby_source=self.ruby if source is None else source,
        )

    def test_01_source_contract_and_13_historical_teams_remain_uninstalled(self):
        result = self.check()
        self.assertEqual(result["status"], "STATIC_CONTRACT_VALIDATED_NATIVE_TRAINERS_PENDING")
        self.assertEqual(result["reference_teams_only"], 13)
        self.assertEqual(result["normal_percent"], 70)
        self.assertEqual(result["master_percent"], 90)
        self.assertEqual(result["max_opponents_per_side"], 6)
        self.assertFalse(result["native_trainers_installed"])
        self.assertFalse(result["gameplay_certified"])
        self.assertIsNone(result["fixed_runtime_levels"])

    def test_02_false_native_trainer_maps_or_execution_is_rejected(self):
        for field in (
            "native_trainer_pbs_verified", "native_trainer_events_verified",
            "native_maps_installed", "game_exe_executed", "joiplay_executed",
            "gameplay_verified", "can_install",
        ):
            with self.subTest(field=field):
                doc = copy.deepcopy(self.contract)
                doc[field] = True
                with self.assertRaisesRegex(ValueError, "certificacao"):
                    self.check(contract=doc)

    def test_03_forged_fixed_levels_or_native_pokemon_are_rejected(self):
        for key, fake in (
            ("real_trainer_levels", [23, 45]),
            ("real_trainer_teams", [{"trainer": "Cynthia", "party": ["GARCHOMP"]}]),
            ("physical_map_ids", [800]),
        ):
            with self.subTest(field=key):
                doc = copy.deepcopy(self.contract)
                doc[key] = fake
                with self.assertRaisesRegex(ValueError, "inventados"):
                    self.check(contract=doc)

    def test_04_normal_master_rules_cloning_and_cap_are_strict(self):
        for key, wrong in (
            ("normal_percent", 50), ("master_percent", 100),
            ("rounding", "ceil"), ("master_requires_stage", 2),
            ("master_team_target", 3), ("max_opponents_per_side", 7),
            ("source_level", "last_pokemon_level"),
            ("apply_after_cloning_original_trainer", False),
            ("natural_evolution_after_scaling", False),
            ("preserve_native_pbs_input", False),
        ):
            with self.subTest(field=key):
                doc = copy.deepcopy(self.contract)
                doc["rules"][key] = wrong
                with self.assertRaisesRegex(ValueError, "regra dinamica"):
                    self.check(contract=doc)

    def test_05_missing_duplicate_and_fake_fixture_scenarios_are_rejected(self):
        for replacement in (
            self.contract["verified_in_offline_fixtures"][:-1],
            self.contract["verified_in_offline_fixtures"] +
            [self.contract["verified_in_offline_fixtures"][0]],
            self.contract["verified_in_offline_fixtures"] +
            ["native_game_exe_approved"],
        ):
            doc = copy.deepcopy(self.contract)
            doc["verified_in_offline_fixtures"] = replacement
            with self.assertRaisesRegex(ValueError, "cobertura"):
                self.check(contract=doc)

    def test_06_ch12_existing_runtime_must_not_drift_or_invent_badge_cap(self):
        for key, wrong in (
            ("normal_percent", 60), ("master_percent", 95),
            ("master_team_target", 5), ("max_opponent_pokemon", 9),
            ("evolution_after_scaling", False),
            ("authored_boss_species_preserved", False),
            ("trainer_pbs_never_mutated", False),
        ):
            doc = copy.deepcopy(self.evolution)
            doc["balance"][key] = wrong
            with self.subTest(field=key), self.assertRaises(ValueError):
                self.check(evolution=doc)
        doc = copy.deepcopy(self.evolution)
        doc["level_cap"]["regional_numeric_cap_in_save"] = 40
        with self.assertRaisesRegex(ValueError, "nivel fixo"):
            self.check(evolution=doc)

    def test_07_ch15_history_cannot_be_falsely_marked_as_native(self):
        for key, value in (
            ("native_source_available_in_repository", True),
            ("native_pbs_compilation_verified", True),
            ("native_event_battle_bindings_verified", True),
            ("gameplay_verified", True), ("can_install", True),
            ("may_write_pbs", True),
        ):
            doc = copy.deepcopy(self.teams)
            doc[key] = value
            with self.subTest(field=key), self.assertRaisesRegex(ValueError, "historico"):
                self.check(teams=doc)
        doc = copy.deepcopy(self.teams)
        doc["trainers"][0]["native_pbs"]["compiled"] = True
        with self.assertRaisesRegex(ValueError, "13 equipes"):
            self.check(teams=doc)

    def test_08_fixture_cannot_be_removed_or_replaced_by_dummy(self):
        for source in (
            "", "puts 'everything works'",
            self.ruby.replace("Battle.new(nil, nil, [], nil, trainers)",
                              "Battle.new()"),
            self.ruby.replace("Marshal.dump(trainers)", "nil"),
        ):
            with self.subTest(size=len(source)), self.assertRaisesRegex(ValueError, "fixture"):
                self.check(source=source)

    def test_09_boss_species_and_player_party_do_not_become_install_claims(self):
        doc = copy.deepcopy(self.contract)
        doc["rules"]["preserve_authored_boss_species"] = False
        with self.assertRaisesRegex(ValueError, "regra dinamica"):
            self.check(contract=doc)
        result = self.check()
        self.assertFalse(result["original_pbs_or_saves_modified"])
        self.assertFalse(result["trainer_event_bindings_verified"])

    def test_10_cross_region_and_trainer_provenance_references_are_fixed(self):
        doc = copy.deepcopy(self.contract)
        doc["references"]["campaign"] = "scripts/regions/NotReal.rb"
        with self.assertRaisesRegex(ValueError, "fonte real"):
            self.check(contract=doc)
        doc = copy.deepcopy(self.teams)
        doc["dynamic_balance"]["boss_species_preserved"] = False
        with self.assertRaisesRegex(ValueError, "CH15 contradiz"):
            self.check(teams=doc)


if __name__ == "__main__":
    unittest.main()
