"""CH13: negative and positive audit of reference-only Sinnoh habitats."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_symbolic_encounters import (
    CATALOG, REVIEW, COVERAGE, PBS, HABITAT, EVOLUTION, audit, read_json, read_text,
)


class SinnohCH13SymbolicEncounterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = read_json(CATALOG)
        cls.review = read_json(REVIEW)
        cls.coverage = read_json(COVERAGE)
        cls.pbs = read_text(PBS)
        cls.habitat = read_text(HABITAT)
        cls.evolution = read_text(EVOLUTION)

    def check(self, catalog=None, review=None, coverage=None, pbs=None,
              habitat=None, evolution=None):
        return audit(copy.deepcopy(self.catalog if catalog is None else catalog),
                     copy.deepcopy(self.review if review is None else review),
                     copy.deepcopy(self.coverage if coverage is None else coverage),
                     self.pbs if pbs is None else pbs,
                     self.habitat if habitat is None else habitat,
                     self.evolution if evolution is None else evolution)

    def reject(self, pattern, **overrides):
        with self.assertRaisesRegex(ValueError, pattern):
            self.check(**overrides)

    def test_authored_21_areas_remain_uninstalled(self):
        report = self.check()
        self.assertEqual(report["areas"], 21)
        self.assertEqual(report["unresolved_area_symbols"],
                         ["Mt. Coronet", "Route 212", "Old Chateau"])
        self.assertEqual(report["real_slots_verified"], 0)
        self.assertEqual(report["native_map_ids_assigned"], 0)
        self.assertFalse(report["can_install"])
        self.assertFalse(report["gameplay_verified"])

    def test_cli_read_only_and_no_native_files_written(self):
        cp = subprocess.run(
            [sys.executable,
             str(ROOT / "scripts/regions/audit_sinnoh_symbolic_encounters.py")],
            capture_output=True, text=True, check=False)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(json.loads(cp.stdout)["areas"], 21)

    def test_missing_and_extra_top_level_fields_fail(self):
        for field in ("status", "global_progress", "areas"):
            with self.subTest(field=field):
                cat = copy.deepcopy(self.catalog)
                cat.pop(field)
                self.reject("Campos", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["native_map_id"] = 100
        self.reject("Campos", catalog=cat)

    def test_fake_playable_or_installed_approval_rejected(self):
        for key in ("may_write_pbs", "may_install", "gameplay_verified",
                    "can_allocate_map_ids", "encounter_weights_verified"):
            with self.subTest(key=key):
                cat = copy.deepcopy(self.catalog)
                cat[key] = True
                self.reject("Status", catalog=cat)

    def test_missing_duplicate_or_out_of_order_areas_fail(self):
        cat = copy.deepcopy(self.catalog)
        cat["areas"].pop()
        self.reject("incompletas", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["areas"][1]["reference_area"] = cat["areas"][0]["reference_area"]
        self.reject("duplicada|fora de ordem", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["areas"][0], cat["areas"][1] = cat["areas"][1], cat["areas"][0]
        self.reject("duplicada|fora de ordem", catalog=cat)

    def test_fabricated_map_id_or_source_or_destination_blocked(self):
        for field, value in (("map_id", 501),
                             ("source_map_ids", [7]),
                             ("destination_map_ids", [500]),
                             ("installed", True),
                             ("native_pbs_verified", True)):
            with self.subTest(field=field):
                cat = copy.deepcopy(self.catalog)
                cat["areas"][0][field] = value
                self.reject("MapID|instalação", catalog=cat)

    def test_unknown_or_ambiguous_map_symbol_fails(self):
        cat = copy.deepcopy(self.catalog)
        cat["areas"][0]["area_symbol"] = "ROUTE_999"
        self.reject("Símbolo", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["areas"][8]["area_symbol"] = "MT_CORONET_WEST_APPROACH"
        self.reject("Símbolo", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["areas"][13]["area_symbol"] = "ROUTE_212"
        self.reject("Símbolo", catalog=cat)

    def test_invented_species_or_duplicate_species_fail(self):
        cat = copy.deepcopy(self.catalog)
        cat["areas"][0]["reference_species"].append("PIKACHU")
        self.reject("Espécies", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["areas"][0]["reference_species"].append("STARLY")
        self.reject("Espécies", catalog=cat)

    def test_method_must_match_review_terrain_not_guessed_slot(self):
        cat = copy.deepcopy(self.catalog)
        cat["areas"][3]["candidate_pbs_methods"] = ["Land"]
        self.reject("Terreno", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["areas"][3]["terrain"] = "GRASS"
        self.reject("Terreno", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["areas"][0]["candidate_pbs_methods"].append("HoneyTree")
        self.reject("Terreno", catalog=cat)

    def test_method_missing_from_real_blue_habitat_blocks(self):
        code = self.habitat.replace("LandMorning:", "LandMorning_DISABLED:")
        self.reject("Habitat Dex", habitat=code)
        code = self.pbs.replace('"LandMorning"', '"LandMorning_MISSING"')
        self.reject("PBS desconhecido", pbs=code)

    def test_cannot_invent_time_windows_or_species_time_assignment(self):
        cat = copy.deepcopy(self.catalog)
        cat["areas"][0]["time_windows_to_audit"] = ["day"]
        self.reject("Horário", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["areas"][5]["time_assignment_verified"] = True
        self.reject("Horário", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["areas"][5]["species_method_assignments"] = [
            {"species": "GASTLY", "method": "CaveNight"}]
        self.reject("Horário", catalog=cat)

    def test_cannot_add_rates_levels_slots_or_accidental_pbs_data(self):
        for field, value in (("encounter_slots", [{"species": "STARLY", "weight": 100}]),
                             ("weight_percentages", [50, 50]),
                             ("level_ranges", [[2, 5]])):
            with self.subTest(field=field):
                cat = copy.deepcopy(self.catalog)
                cat["areas"][0][field] = value
                self.reject("Slots", catalog=cat)

    def test_weekly_drifloon_and_rotom_are_not_grass_slots(self):
        for index, special in ((4, "DRIFLOON"), (20, "ROTOM")):
            with self.subTest(index=index):
                cat = copy.deepcopy(self.catalog)
                cat["areas"][index]["reference_species"].append(special)
                self.reject("Espécies|especial", catalog=cat)
                cat = copy.deepcopy(self.catalog)
                cat["areas"][index]["special_events"][0]["event_installed"] = True
                self.reject("Encontro especial", catalog=cat)
                cat = copy.deepcopy(self.catalog)
                cat["areas"][index]["special_events"] = []
                self.reject("Eventos estáticos", catalog=cat)

    def test_source_review_drift_is_not_silently_accepted(self):
        src = copy.deepcopy(self.review)
        src["regions"]["SINNOH"]["areas"][0]["reference_species"] = ["RATTATA"]
        self.reject("Espécies", review=src)
        src = copy.deepcopy(self.review)
        src["status"] = "PLAYABLE"
        self.reject("Fonte de revisão", review=src)

    def test_coverage_map_ids_cannot_be_marked_native_verified(self):
        coverage = copy.deepcopy(self.coverage)
        for phase in coverage["phases"]:
            for area in phase["areas"]:
                if area["symbol"] == "ROUTE_201":
                    area["verified"] = True
        self.reject("planejamento|físico", coverage=coverage)

    def test_unknown_regional_numeric_cap_rejected(self):
        cat = copy.deepcopy(self.catalog)
        cat["global_progress"]["regional_numeric_level_cap"] = 35
        self.reject("Progressão", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["global_progress"]["reference_party"] = "badge_level"
        self.reject("Progressão", catalog=cat)

    def test_shared_dynamic_evolution_gates_and_chances_cannot_drift(self):
        for key, fake in (("stone_level", 40),
                          ("trade_level", 30),
                          ("friendship_level", 30),
                          ("level_evolution_grace", 0)):
            with self.subTest(key=key):
                cat = copy.deepcopy(self.catalog)
                cat["global_progress"][key] = fake
                self.reject("Progressão", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["global_progress"]["wild_chances_by_gap"][0]["chance_percent"] = 100
        self.reject("Progressão", catalog=cat)

    def test_unsupported_shared_evolution_runtime_blocks(self):
        code = self.evolution.replace("STONE_LEVEL = 30", "STONE_LEVEL = 45")
        self.reject("BlueEvolutionScaling", evolution=code)
        code = self.evolution.replace("return 15 if gap < 5", "return 90 if gap < 5")
        self.reject("BlueEvolutionScaling", evolution=code)

    def test_false_flags_in_area_must_fail_closed(self):
        cat = copy.deepcopy(self.catalog)
        cat["areas"][0]["status"] = "installed"
        self.reject("instalação", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["areas"][0]["time_assignment_verified"] = "false"
        self.reject("Horário", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        cat["areas"][0]["source_map_ids"] = [0]
        self.reject("MapID", catalog=cat)

    def test_schema_cannot_hide_data_inside_unrecognized_area_fields(self):
        cat = copy.deepcopy(self.catalog)
        cat["areas"][0]["probability"] = 100
        self.reject("Campos obrigatórios", catalog=cat)
        cat = copy.deepcopy(self.catalog)
        del cat["areas"][0]["reference_species"]
        self.reject("Campos obrigatórios", catalog=cat)


if __name__ == "__main__":
    unittest.main()
