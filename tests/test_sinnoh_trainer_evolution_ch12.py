"""CH12: reject guessed regional level caps, static teams and drift."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_trainer_evolution import (
    audit, CONTRACT, CAMPAIGN, STORY, EVOLUTION, REGISTRY, read,
)


class SinnohCH12ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(read(CONTRACT))
        cls.campaign = read(CAMPAIGN)
        cls.story = read(STORY)
        cls.evolution = read(EVOLUTION)
        cls.registry = json.loads(read(REGISTRY))

    def check(self, spec=None, campaign=None, story=None,
              evolution=None, registry=None):
        return audit(
            copy.deepcopy(self.contract if spec is None else spec),
            self.campaign if campaign is None else campaign,
            self.evolution if evolution is None else evolution,
            self.story if story is None else story,
            copy.deepcopy(self.registry if registry is None else registry),
        )

    def rejects(self, message, **changes):
        with self.assertRaisesRegex(ValueError, message):
            self.check(**changes)

    def test_authored_sinnoh_remains_planned(self):
        result = self.check()
        self.assertEqual((result["normal_percent"],
                          result["master_percent"]), (70, 90))
        self.assertFalse(result["regional_badge_level_cap_defined"])
        self.assertFalse(result["gameplay_verified"])
        self.assertFalse(result["can_install"])

    def test_guessed_level_cap_by_badge_is_rejected(self):
        for invented in (30, 50, 100):
            with self.subTest(invented=invented):
                spec = copy.deepcopy(self.contract)
                spec["level_cap"]["regional_numeric_cap_in_save"] = invented
                self.rejects("Level cap", spec=spec)
        spec = copy.deepcopy(self.contract)
        spec["level_cap"]["regional_badge_to_level_cap_implemented"] = True
        self.rejects("Level cap", spec=spec)

    def test_bst_tier_is_not_numeric_level_cap(self):
        spec = copy.deepcopy(self.contract)
        spec["level_cap"]["bst_stage_caps"] = [30, 50, 70, None]
        self.rejects("Level cap", spec=spec)
        spec = copy.deepcopy(self.contract)
        spec["level_cap"]["bst_cap_is_not_a_level_cap"] = False
        self.rejects("Level cap", spec=spec)

    def test_wrong_normal_master_values_or_rounding(self):
        for key, value in (("normal_percent", 90),
                           ("master_percent", 70),
                           ("rounding", "ceiling"),
                           ("master_trigger", "badge_count>=8")):
            with self.subTest(key=key):
                spec = copy.deepcopy(self.contract)
                spec["balance"][key] = value
                self.rejects("Normal/Master", spec=spec)

    def test_team_limits_and_pbs_immutability(self):
        for key, value in (("master_team_target", 6),
                           ("max_opponent_pokemon", 7),
                           ("trainer_pbs_never_mutated", False),
                           ("authored_boss_species_preserved", False),
                           ("evolution_after_scaling", False)):
            with self.subTest(key=key):
                spec = copy.deepcopy(self.contract)
                spec["balance"][key] = value
                self.rejects("Normal/Master", spec=spec)

    def test_level_plus_five_boundary(self):
        for value in (0, 4, 6):
            with self.subTest(grace=value):
                spec = copy.deepcopy(self.contract)
                spec["evolution"]["level_required_plus_grace"] = value
                self.rejects("evolução", spec=spec)

    def test_stone_trade_happiness_thresholds_rejected_if_changed(self):
        for key, wrong in (("stone_level", 40),
                           ("trade_level", 30),
                           ("friendship_level", 46)):
            with self.subTest(key=key):
                spec = copy.deepcopy(self.contract)
                spec["evolution"][key] = wrong
                self.rejects("evolução", spec=spec)

    def test_unknown_native_conditions_must_not_be_assumed(self):
        for key in ("unsupported_conditions_blocked", "ambiguous_branch_blocked",
                    "special_forms_blocked",
                    "conditions_by_gender_and_time_respected"):
            with self.subTest(key=key):
                spec = copy.deepcopy(self.contract)
                spec["evolution"][key] = False
                self.rejects("evolução", spec=spec)

    def test_all_six_synthetic_sinnoh_families_preserved(self):
        spec = copy.deepcopy(self.contract)
        spec["trainer_examples"].pop()
        self.rejects("incompletos", spec=spec)
        spec = copy.deepcopy(self.contract)
        spec["trainer_examples"][0]["thresholds"] = [18, 32]
        self.rejects("Família", spec=spec)
        spec = copy.deepcopy(self.contract)
        spec["trainer_examples"][3]["synthetic_fixture_only"] = False
        self.rejects("Família", spec=spec)

    def test_missing_or_extra_contract_fields_are_rejected(self):
        spec = copy.deepcopy(self.contract)
        spec.pop("balance")
        self.rejects("Campos", spec=spec)
        spec = copy.deepcopy(self.contract)
        spec["fixed_trainer_level"] = 30
        self.rejects("Campos", spec=spec)

    def test_false_gameplay_approval_is_rejected(self):
        for key in ("gameplay_verified", "native_trainers_installed", "can_install"):
            with self.subTest(key=key):
                spec = copy.deepcopy(self.contract)
                spec[key] = True
                self.rejects("falso", spec=spec)

    def test_mutated_real_campaign_runtime_blocks(self):
        code = self.campaign.replace(
            "master? ? 90 : 70", "master? ? 70 : 70")
        self.rejects("Campaign.rb", campaign=code)
        code = self.campaign.replace(
            "pkmn=Marshal.load(Marshal.dump(original));pkmn.level=level",
            "pkmn=original;pkmn.level=level")
        self.rejects("Campaign.rb", campaign=code)

    def test_mutated_real_story_runtime_blocks(self):
        code = self.story.replace(
            "def self.cap;[350,450,540,nil][stage];end",
            "def self.cap;[200,400,600,nil][stage];end")
        self.rejects("Story.rb", story=code)
        code = self.story.replace(
            "BlueEvolutionScaling.legitimate_trainer_form?(p)", "false")
        self.rejects("Story.rb", story=code)

    def test_mutated_native_evolution_source_blocks(self):
        code = self.evolution.replace(
            "STONE_LEVEL = 30", "STONE_LEVEL = 40")
        self.rejects("EvolutionScaling.rb", evolution=code)
        code = self.evolution.replace(
            "return [] unless targets.length == 1", "return matches")
        self.rejects("EvolutionScaling.rb", evolution=code)

    def test_registry_sinnoh_not_playable_or_missing(self):
        data = copy.deepcopy(self.registry)
        data["regions"]["SINNOH"]["status"] = "available"
        self.rejects("planned", registry=data)
        data = copy.deepcopy(self.registry)
        del data["regions"]["SINNOH"]
        self.rejects("planned", registry=data)


if __name__ == "__main__":
    unittest.main()
