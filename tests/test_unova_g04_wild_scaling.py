"""G04.3 Unova read-only wild evolution/level audits; no native encounters."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_unova_g04_wild_scaling as mod

class UnovaG043Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.g04, cls.report = mod.load_project()
        cls.g03 = mod.g042.load_json(ROOT / cls.data["sources"]["g03_scaling"])
        cls.shared = mod.g042.load_json(ROOT / cls.data["sources"]["shared_evolution"])
        cls.native = mod.g042.read_text(ROOT / cls.data["sources"]["native_evolution"])
        cls.registry = mod.g042.load_json(ROOT / cls.data["sources"]["registry"])
        cls.tracker = mod.g042.load_json(ROOT / cls.data["sources"]["tracker"])
    def graph(self, method="Level", threshold=20):
        return {
            "FIXTURE_BASE": {"special_flags": [], "form": 0, "evolutions": [
                {"target": "FIXTURE_EVOLVED", "method": method,
                 "parameter": threshold if method in mod.LEVEL else None}]},
            "FIXTURE_EVOLVED": {"special_flags": [], "form": 0, "evolutions": []},
        }
    def slot(self, **changes):
        slot = {"species": "FIXTURE_BASE", "level": 10,
                "weight_percent": 20, "encounter_rate": 15,
                "source": "SYNTHETIC_FIXTURE"}
        slot.update(changes)
        return slot
    def sim(self, **changes):
        kwargs = {
            "area_key": "UNOVA_ROUTE_01", "method": "Land",
            "party": [{"level": 30, "egg": False}],
            "engine_max_level": 100, "slot": self.slot(),
            "graph": self.graph(), "rolls": [0],
        }
        kwargs.update(changes)
        return mod.simulate_fixture(self.data, self.g04, **kwargs)
    def reject_sim(self, **changes):
        with self.assertRaises(ValueError):
            self.sim(**changes)
    def reject_catalog(self, mutate):
        d = copy.deepcopy(self.data)
        mutate(d)
        with self.assertRaises(ValueError):
            mod.validate_catalog(d, self.g04, self.g03, self.shared,
                                 self.native, self.registry, self.tracker)

    def test_001_exactly_74_symbolic_areas(self):
        self.assertEqual(len(self.data["areas"]), 74)
        self.assertEqual(self.report["areas"], 74)
    def test_002_ordered_areas_same_as_g04_2(self):
        self.assertEqual([a["area_key"] for a in self.data["areas"]],
                         [a["area_key"] for a in self.g04["areas"]])
    def test_003_no_native_levels_or_species(self):
        self.assertTrue(all(a["native_level_min"] is None
                            and a["native_level_max"] is None
                            and a["native_species"] is None for a in self.data["areas"]))
    def test_004_no_native_weights_or_rates(self):
        self.assertTrue(all(a["native_slot_weights"] is None and
                            a["native_encounter_rate"] is None
                            for a in self.data["areas"]))
    def test_005_no_real_map_ids(self):
        self.assertTrue(all(a["native_map_id"] is None for a in self.data["areas"]))
    def test_006_no_installation_or_playability(self):
        self.assertFalse(self.data["can_install"])
        self.assertFalse(self.data["game_exe_tested"])
        self.assertFalse(self.data["android_tested"])
        self.assertFalse(self.data["native_encounters_verified"])
    def test_007_registry_stays_planned(self):
        self.assertEqual(self.registry["regions"]["UNOVA"]["status"], "planned")
    def test_008_technical_and_playable_bars_zero(self):
        self.assertEqual(self.tracker["native_technical_bar"]["completed"], 0)
        self.assertEqual(self.tracker["native_playable_bar"]["completed"], 0)
    def test_009_no_badge_derived_numeric_cap(self):
        self.assertIsNone(self.data["progress"]["regional_badge_numeric_level_cap"])
    def test_010_progress_uses_highest_non_egg(self):
        self.assertEqual(mod.progress_level([
            {"level": 20, "egg": False}, {"level": 100, "egg": True},
            {"level": 45, "egg": False}], 100), 45)
    def test_011_all_eggs_fallback_to_level_one(self):
        self.assertEqual(mod.progress_level([{"level": 50, "egg": True}], 100), 1)
    def test_012_empty_party_fallback_to_level_one(self):
        self.assertEqual(mod.progress_level([], 100), 1)
    def test_013_maximum_level_enforced(self):
        self.assertEqual(mod.progress_level([{"level": 100, "egg": False}], 100), 100)
    def test_014_invalid_egg_type_rejected(self):
        with self.assertRaises(ValueError):
            mod.progress_level([{"level": 10, "egg": 1}], 100)
    def test_015_invalid_party_level_rejected(self):
        with self.assertRaises(ValueError):
            mod.progress_level([{"level": 101, "egg": False}], 100)
    def test_016_boolean_level_rejected(self):
        with self.assertRaises(ValueError):
            mod.progress_level([{"level": True, "egg": False}], 100)
    def test_017_level_method_plus_five(self):
        self.assertEqual(mod.method_threshold({"method": "Level", "parameter": 20}), 25)
    def test_018_stone_threshold_thirty(self):
        self.assertEqual(mod.method_threshold({"method": "Item", "parameter": None}), 30)
    def test_019_trade_threshold_forty(self):
        self.assertEqual(mod.method_threshold({"method": "Trade", "parameter": None}), 40)
    def test_020_happiness_threshold_forty_five(self):
        self.assertEqual(mod.method_threshold({"method": "Happiness", "parameter": None}), 45)
    def test_021_wild_chance_below_threshold_zero(self):
        self.assertEqual(mod.wild_chance(24, 25), 0)
    def test_022_wild_chance_first_band_fifteen(self):
        self.assertEqual([mod.wild_chance(x,25) for x in [25,29]], [15,15])
    def test_023_wild_chance_second_band_thirty(self):
        self.assertEqual([mod.wild_chance(x,25) for x in [30,39]], [30,30])
    def test_024_wild_chance_third_band_forty_five(self):
        self.assertEqual([mod.wild_chance(x,25) for x in [40,49]], [45,45])
    def test_025_wild_chance_fourth_band_sixty(self):
        self.assertEqual(mod.wild_chance(50,25), 60)
    def test_026_native_level_is_not_scaled_to_party_level(self):
        outcome = self.sim(party=[{"level": 24, "egg": False}], rolls=[])
        self.assertEqual(outcome["resolved_level"], 10)
        self.assertEqual(outcome["resolved_species"], "FIXTURE_BASE")
    def test_027_cap_below_native_level_skips_evolution(self):
        outcome = self.sim(party=[{"level": 7, "egg": False}], rolls=[])
        self.assertEqual(outcome["resolved_level"], 10)
    def test_028_evolves_when_chance_passes_and_cap_allows(self):
        outcome = self.sim()
        self.assertEqual(outcome["resolved_species"], "FIXTURE_EVOLVED")
        self.assertEqual(outcome["resolved_level"], 25)
        self.assertEqual(outcome["trace"][0]["chance_percent"], 30)
    def test_029_preserves_original_weights_and_rates(self):
        outcome = self.sim()
        self.assertEqual(outcome["preserved_weight_percent"], 20)
        self.assertEqual(outcome["preserved_encounter_rate"], 15)
        self.assertIsNone(outcome["native_encounter_rate"])
        self.assertIsNone(outcome["native_slot_weights"])
    def test_030_high_roll_rejects_evolution(self):
        outcome = self.sim(rolls=[99])
        self.assertEqual(outcome["resolved_species"], "FIXTURE_BASE")
        self.assertEqual(outcome["resolved_level"], 10)
    def test_031_boundary_roll_30_rejects_second_band(self):
        self.assertEqual(self.sim(rolls=[30])["resolved_species"], "FIXTURE_BASE")
    def test_032_boundary_roll_29_passes_second_band(self):
        self.assertEqual(self.sim(rolls=[29])["resolved_species"], "FIXTURE_EVOLVED")
    def test_033_egg_only_party_does_not_evolve(self):
        self.assertEqual(self.sim(party=[{"level": 100, "egg": True}], rolls=[])["progress_level"], 1)
    def test_034_ambiguous_branch_preserves_original(self):
        graph = self.graph()
        graph["FIXTURE_OTHER"] = {"special_flags": [], "form": 0, "evolutions": []}
        graph["FIXTURE_BASE"]["evolutions"].append(
            {"target": "FIXTURE_OTHER", "method": "Level", "parameter": 20})
        self.assertEqual(self.sim(graph=graph,rolls=[])["resolved_species"], "FIXTURE_BASE")
    def test_035_two_methods_one_target_are_not_ambiguous(self):
        graph = self.graph()
        graph["FIXTURE_BASE"]["evolutions"].append(
            {"target": "FIXTURE_EVOLVED", "method": "Item", "parameter": None})
        self.assertEqual(self.sim(graph=graph)["resolved_species"], "FIXTURE_EVOLVED")
    def test_036_special_target_blocked(self):
        graph = self.graph()
        graph["FIXTURE_EVOLVED"]["special_flags"] = ["Paradox"]
        self.assertEqual(self.sim(graph=graph,rolls=[])["resolved_species"], "FIXTURE_BASE")
    def test_037_special_source_blocked(self):
        graph = self.graph()
        graph["FIXTURE_BASE"]["special_flags"] = ["Legendary"]
        self.assertEqual(self.sim(graph=graph,rolls=[])["resolved_species"], "FIXTURE_BASE")
    def test_038_nonzero_form_target_blocked(self):
        graph = self.graph()
        graph["FIXTURE_EVOLVED"]["form"] = 1
        self.assertEqual(self.sim(graph=graph,rolls=[])["resolved_species"], "FIXTURE_BASE")
    def test_039_gender_unverified_does_not_evolve(self):
        self.assertEqual(self.sim(graph=self.graph("LevelMale"),rolls=[])["resolved_species"],"FIXTURE_BASE")
    def test_040_male_condition_verified_evolves(self):
        self.assertEqual(self.sim(graph=self.graph("LevelMale"),gender="MALE")["resolved_species"],"FIXTURE_EVOLVED")
    def test_041_wrong_gender_does_not_evolve(self):
        self.assertEqual(self.sim(graph=self.graph("LevelFemale"),gender="MALE",rolls=[])["resolved_species"],"FIXTURE_BASE")
    def test_042_day_unverified_does_not_evolve(self):
        self.assertEqual(self.sim(graph=self.graph("LevelDay"),rolls=[])["resolved_species"],"FIXTURE_BASE")
    def test_043_day_only_when_day(self):
        self.assertEqual(self.sim(graph=self.graph("LevelDay"),time_bucket="DAY")["resolved_species"],"FIXTURE_EVOLVED")
    def test_044_night_unverified_does_not_evolve(self):
        self.assertEqual(self.sim(graph=self.graph("LevelNight"),rolls=[])["resolved_species"],"FIXTURE_BASE")
    def test_045_night_verified_evolves(self):
        self.assertEqual(self.sim(graph=self.graph("LevelNight"),time_bucket="NIGHT")["resolved_species"],"FIXTURE_EVOLVED")
    def test_046_stone_before_30_blocked(self):
        self.assertEqual(self.sim(graph=self.graph("Item"),party=[{"level":29,"egg":False}],rolls=[])["resolved_species"],"FIXTURE_BASE")
    def test_047_stone_at_30_allowed(self):
        self.assertEqual(self.sim(graph=self.graph("Item"))["resolved_species"],"FIXTURE_EVOLVED")
    def test_048_trade_before_40_blocked(self):
        self.assertEqual(self.sim(graph=self.graph("Trade"),rolls=[])["resolved_species"],"FIXTURE_BASE")
    def test_049_trade_at_40_allowed(self):
        self.assertEqual(self.sim(graph=self.graph("Trade"),party=[{"level":40,"egg":False}])["resolved_species"],"FIXTURE_EVOLVED")
    def test_050_friendship_at_45_allowed(self):
        self.assertEqual(self.sim(graph=self.graph("Happiness"),party=[{"level":45,"egg":False}])["resolved_species"],"FIXTURE_EVOLVED")
    def test_051_no_genuine_pokemon_identifier(self):
        graph = self.graph()
        graph["RATTATA"] = graph.pop("FIXTURE_BASE")
        self.reject_sim(graph=graph)
    def test_052_native_slot_source_rejected(self):
        self.reject_sim(slot=self.slot(source="NATIVE_PBS"))
    def test_053_native_input_source_rejected(self):
        self.reject_sim(input_source="NATIVE_PBS")
    def test_054_no_fabricated_area_assignment(self):
        self.reject_sim(area_key="UNOVA_STRIATON_GYM")
    def test_055_unsupported_method_cannot_be_assigned(self):
        self.reject_sim(method="HeadbuttHigh")
    def test_056_wrong_method_evolution_rejected(self):
        graph = self.graph()
        graph["FIXTURE_BASE"]["evolutions"][0]["method"] = "TradeSpecial"
        self.reject_sim(graph=graph)
    def test_057_implicit_random_roll_forbidden(self):
        self.reject_sim(rolls=[])
    def test_058_invalid_roll_rejected(self):
        self.reject_sim(rolls=[100])
    def test_059_three_steps_at_most(self):
        graph = self.graph()
        graph["FIXTURE_EVOLVED"]["evolutions"] = [
            {"target":"FIXTURE_THIRD","method":"Level","parameter":20}]
        graph["FIXTURE_THIRD"] = {"special_flags":[],"form":0,"evolutions":[
            {"target":"FIXTURE_FOURTH","method":"Level","parameter":20}]}
        graph["FIXTURE_FOURTH"] = {"special_flags":[],"form":0,"evolutions":[
            {"target":"FIXTURE_FIFTH","method":"Level","parameter":20}]}
        graph["FIXTURE_FIFTH"] = {"special_flags":[],"form":0,"evolutions":[]}
        outcome = self.sim(graph=graph, rolls=[0,0,0])
        self.assertEqual(outcome["resolved_species"],"FIXTURE_FOURTH")
        self.assertEqual(len(outcome["trace"]),3)
    def test_060_data_catalog_immutable_after_simulate(self):
        original = copy.deepcopy(self.data)
        self.sim()
        self.assertEqual(self.data,original)
    def test_061_area_level_forgery_refused(self):
        self.reject_catalog(lambda d: d["areas"][0].update(native_level_min=5))
    def test_062_area_species_forgery_refused(self):
        self.reject_catalog(lambda d: d["areas"][0].update(native_species=["PATRAT"]))
    def test_063_area_rate_zero_is_forgery(self):
        self.reject_catalog(lambda d: d["areas"][0].update(native_encounter_rate=0))
    def test_064_area_weight_forgery_refused(self):
        self.reject_catalog(lambda d: d["areas"][0].update(native_slot_weights=[100]))
    def test_065_area_mapid_forgery_refused(self):
        self.reject_catalog(lambda d: d["areas"][0].update(native_map_id=518))
    def test_066_area_installation_forgery_refused(self):
        self.reject_catalog(lambda d: d["areas"][0].update(scaling_installed=True))
    def test_067_missing_area_refused(self):
        self.reject_catalog(lambda d: d["areas"].pop())
    def test_068_extra_area_refused(self):
        self.reject_catalog(lambda d: d["areas"].append(copy.deepcopy(d["areas"][0])))
    def test_069_wrong_area_order_refused(self):
        self.reject_catalog(lambda d: d["areas"].reverse())
    def test_070_wrong_progress_signal_refused(self):
        self.reject_catalog(lambda d: d["progress"].update(signal="BADGE_LEVEL_CAP"))
    def test_071_numeric_badge_cap_refused(self):
        self.reject_catalog(lambda d: d["progress"].update(regional_badge_numeric_level_cap=30))
    def test_072_evolution_band_change_refused(self):
        self.reject_catalog(lambda d: d["chance_bands"][0].update(chance_percent=90))
    def test_073_unsafe_branch_selection_refused(self):
        self.reject_catalog(lambda d: d["safety"].update(branching_requires_single_unique_eligible_target=False))
    def test_074_false_pbs_approval_refused(self):
        self.reject_catalog(lambda d: d.update(native_encounters_verified=True))
    def test_075_false_game_exe_approval_refused(self):
        self.reject_catalog(lambda d: d.update(game_exe_tested=True))
    def test_076_extra_unknown_field_refused(self):
        self.reject_catalog(lambda d: d.update(unapproved=True))
    def test_077_runtime_drift_refused(self):
        with self.assertRaises(ValueError):
            mod.check_runtime(self.native.replace("STONE_LEVEL = 30", "STONE_LEVEL = 25"))
    def test_078_g04_2_source_must_remain_non_native(self):
        changed = copy.deepcopy(self.g04)
        changed["native_encounters_verified"] = True
        with self.assertRaises(ValueError):
            mod.validate_catalog(self.data,changed,self.g03,self.shared,
                                 self.native,self.registry,self.tracker)
    def test_079_registry_promotion_refused(self):
        changed = copy.deepcopy(self.registry)
        changed["regions"]["UNOVA"]["status"] = "playable"
        with self.assertRaises(ValueError):
            mod.validate_catalog(self.data,self.g04,self.g03,self.shared,
                                 self.native,changed,self.tracker)
    def test_080_demo_is_fixture_only(self):
        demo = mod.demo(self.data,self.g04)
        self.assertEqual(demo["synthetic_early"]["resolved_species"],"FIXTURE_RATTATA")
        self.assertEqual(demo["synthetic_late"]["resolved_species"],"FIXTURE_RATICATE")
        self.assertFalse(demo["can_install"])
    def test_081_cli_check(self):
        r = subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g04_wild_scaling.py"),
                            "--check"],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(json.loads(r.stdout)["areas"],74)
    def test_082_cli_demo(self):
        r = subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g04_wild_scaling.py"),
                            "--simulate-demo"],capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertTrue(json.loads(r.stdout)["synthetic_late"]["fixture_only"])

if __name__=="__main__":
    unittest.main()
