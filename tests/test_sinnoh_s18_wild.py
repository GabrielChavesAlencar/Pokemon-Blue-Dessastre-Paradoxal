"""S18 offline negative tests for Sinnoh wild evolution and planned area data."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_s18_wild import (
    CONTRACT, ENCOUNTERS, CH12, EVOLUTION, RUBY, audit,
)


class S18WildContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text("utf-8"))
        cls.encounters = json.loads(ENCOUNTERS.read_text("utf-8"))
        cls.ch12 = json.loads(CH12.read_text("utf-8"))
        cls.evolution = EVOLUTION.read_text("utf-8")
        cls.fixture = RUBY.read_text("utf-8")

    def check(self, *, contract=None, encounters=None, ch12=None,
              evolution=None, fixture=None):
        return audit(copy.deepcopy(self.contract if contract is None else contract),
                     copy.deepcopy(self.encounters if encounters is None else encounters),
                     copy.deepcopy(self.ch12 if ch12 is None else ch12),
                     self.evolution if evolution is None else evolution,
                     self.fixture if fixture is None else fixture)

    def test_01_policy_is_offline_with_21_reference_areas_not_installed(self):
        result = self.check()
        self.assertEqual(result["reference_areas"], 21)
        self.assertEqual(result["status"],
                         "SHARED_WILD_POLICY_VERIFIED_OFFLINE_NATIVE_PENDING")
        self.assertEqual(result["chance_tiers"], [15, 30, 45, 60])
        self.assertEqual(result["special_static_events_not_installed"], 2)
        self.assertTrue(result["preserves_original_encounter_slots"])
        self.assertFalse(result["native_map_ids_verified"])
        self.assertFalse(result["native_pbs_edited"])
        self.assertFalse(result["game_exe_or_joiplay_tested"])
        self.assertFalse(result["gameplay_approved"])

    def test_02_false_game_exe_or_pbs_approval_fails_closed(self):
        for k in self.contract["gameplay"]:
            doc = copy.deepcopy(self.contract)
            doc["gameplay"][k] = True
            with self.subTest(k=k), self.assertRaisesRegex(ValueError, "contrato S18"):
                self.check(contract=doc)

    def test_03_forged_cap_by_badges_and_wrong_chance_fails(self):
        for key, val in (
            ("regional_numeric_level_cap", 30),
            ("reference", "BADGE_COUNT"),
            ("level_evolution_grace", 0),
            ("stone_level", 20),
            ("original_species_slot_retained", False),
            ("preserve_native_encounter_metadata", False),
            ("preserve_original_pbs_weights", False),
            ("invalid_level_or_cap_keeps_original_slot", False),
        ):
            doc = copy.deepcopy(self.contract)
            doc["progress"][key] = val
            with self.subTest(k=key), self.assertRaisesRegex(ValueError, "contrato S18"):
                self.check(contract=doc)
        doc = copy.deepcopy(self.contract)
        doc["progress"]["wild_chances_by_gap"][2]["chance_percent"] = 95
        with self.assertRaisesRegex(ValueError, "contrato S18"):
            self.check(contract=doc)

    def test_04_21_reference_areas_cannot_be_replaced_by_fake_natives(self):
        for k, val in (
            ("map_id", 900),
            ("source_map_ids", [99]),
            ("destination_map_ids", [799]),
            ("encounter_slots", [{"species": "SHINX", "weight": 70}]),
            ("weight_percentages", [70, 30]),
            ("level_ranges", [5, 40]),
            ("native_pbs_verified", True),
            ("installed", True),
            ("species_method_assignments", [{"method": "Land", "species": "SHINX"}]),
            ("time_assignment_verified", True),
            ("status", "playable"),
        ):
            doc = copy.deepcopy(self.encounters)
            doc["areas"][0][k] = val
            with self.subTest(k=k), self.assertRaisesRegex(ValueError, "area CH13"):
                self.check(encounters=doc)

    def test_05_old_ch13_pbs_weights_and_status_remain_pending(self):
        for key, wrong in (
            ("encounter_weights_verified", True),
            ("may_write_pbs", True),
            ("may_install", True),
            ("can_allocate_map_ids", True),
            ("gameplay_verified", True),
            ("status", "INSTALLED"),
        ):
            doc = copy.deepcopy(self.encounters)
            doc[key] = wrong
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check(encounters=doc)
        doc = copy.deepcopy(self.encounters)
        doc["global_progress"]["regional_numeric_level_cap"] = 50
        with self.assertRaisesRegex(ValueError, "CH13 contradiz"):
            self.check(encounters=doc)

    def test_06_special_events_not_random_wild_encounters(self):
        for area_name in ("Valley Windworks", "Old Chateau"):
            doc = copy.deepcopy(self.encounters)
            area = next(a for a in doc["areas"] if a["reference_area"] == area_name)
            area["special_events"][0]["event_installed"] = True
            with self.subTest(area=area_name), self.assertRaisesRegex(
                ValueError, "evento estatico"
            ):
                self.check(encounters=doc)

    def test_07_duplicate_or_missing_area_is_blocked(self):
        doc = copy.deepcopy(self.encounters)
        doc["areas"].pop()
        with self.assertRaisesRegex(ValueError, "21 areas"):
            self.check(encounters=doc)
        doc = copy.deepcopy(self.encounters)
        doc["areas"][1]["reference_area"] = doc["areas"][0]["reference_area"]
        with self.assertRaisesRegex(ValueError, "repetida"):
            self.check(encounters=doc)

    def test_08_ambiguous_method_assignments_remain_unverified(self):
        doc = copy.deepcopy(self.encounters)
        doc["areas"][0]["candidate_pbs_methods"] = []
        with self.assertRaisesRegex(ValueError, "metodo candidato"):
            self.check(encounters=doc)
        doc = copy.deepcopy(self.encounters)
        doc["areas"][0]["reference_species"] = []
        with self.assertRaisesRegex(ValueError, "referencia"):
            self.check(encounters=doc)

    def test_09_old_ch12_cannot_claim_native_evolution_or_fixed_cap(self):
        doc = copy.deepcopy(self.ch12)
        doc["gameplay_verified"] = True
        with self.assertRaisesRegex(ValueError, "CH12"):
            self.check(ch12=doc)
        doc = copy.deepcopy(self.ch12)
        doc["level_cap"]["regional_numeric_cap_in_save"] = 30
        with self.assertRaisesRegex(ValueError, "CH12"):
            self.check(ch12=doc)

    def test_10_actual_runtime_guard_cannot_be_deleted(self):
        for missing in (
            "base_level <= cap",
            "base_level.between?(1, maximum) && cap.between?(1, maximum)",
            "return [species, base_level] unless active?",
            "source.get_evolutions(true)",
            "result.dup.tap { |row| row[0], row[1] = changed }",
        ):
            with self.subTest(token=missing), self.assertRaisesRegex(
                ValueError, "runtime compartilhado"
            ):
                self.check(evolution=self.evolution.replace(missing, ""))

    def test_11_fixture_wild_hook_cannot_be_faked_or_removed(self):
        for missing in (
            "S18SyntheticNativeEncounters.prepend(BlueEvolutionScaling::WildEncounters)",
            "BlueEvolutionScaling.wild_option(",
            "SINNOH_S18_NATIVE_WILD_ADAPTER_THRESHOLDS_SLOTS_NO_PBS_MUTATION_OFFLINE_OK",
        ):
            with self.subTest(token=missing), self.assertRaisesRegex(
                ValueError, "fixture Ruby"
            ):
                self.check(fixture=self.fixture.replace(missing, ""))

    def test_12_no_cross_region_native_map_or_player_save_is_created(self):
        before = self.check()
        self.assertFalse(before["native_map_ids_verified"])
        self.assertFalse(before["native_pbs_edited"])
        self.assertEqual(self.encounters["global_progress"]["regional_numeric_level_cap"],
                         None)
        self.assertTrue(all(area["encounter_slots"] == [] and
                            area["map_id"] is None and
                            area["weight_percentages"] is None and
                            area["level_ranges"] is None
                            for area in self.encounters["areas"]))


if __name__ == "__main__":
    unittest.main()
