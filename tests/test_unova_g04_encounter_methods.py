"""G04.2 Unova time/method/season reference audit: native probabilities UNKNOWN."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g04_encounter_methods as wild

class UnovaG042Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data,cls.u03,cls.regions,cls.report=wild.load_project()
        cls.pbs=(ROOT/cls.data["sources"]["blue_pbs_methods"]).read_text(encoding="utf-8")
        cls.habitat=(ROOT/cls.data["sources"]["blue_habitat"]).read_text(encoding="utf-8")
        cls.evolution=(ROOT/cls.data["sources"]["native_wild_evolution"]).read_text(encoding="utf-8")
        cls.sinnoh=json.loads((ROOT/cls.data["sources"]["shared_sinnoh_reference"]).read_text(encoding="utf-8"))
        cls.route="UNOVA_ROUTE_01"
        cls.cave="UNOVA_WELLSPRING_CAVE"
        cls.water="UNOVA_UNDELLA_BAY"

    def bad_catalog(self,change):
        changed=copy.deepcopy(self.data)
        change(changed)
        with self.assertRaises(ValueError):
            wild.validate_catalog(changed,self.u03,self.regions,self.pbs,
                                  self.habitat,self.evolution,self.sinnoh)
    def bad_input(self,**override):
        kw={"area_key":self.route,"method":"Land","time_bucket":"ANY",
            "season_bucket":"ANY"}
        kw.update(override)
        with self.assertRaises(ValueError):wild.plan_audit(self.data,**kw)
    def query(self,**override):
        kw={"area_key":self.route,"method":"Land",
            "time_bucket":"ANY","season_bucket":"ANY"}
        kw.update(override)
        return wild.plan_audit(self.data,**kw)
    def sample(self,key):
        return next(x for x in self.data["areas"] if x["area_key"]==key)
    def fixture_slot(self,**extra):
        result={"species":"PATRAT","weight_percent":20,"level_min":2,"level_max":4}
        result.update(extra)
        return result

    def test_001_white_unova_not_playable(self):
        self.assertEqual(self.data["region"],"UNOVA")
        self.assertEqual(self.data["reference_version"],"WHITE_BW")
        self.assertFalse(self.data["can_install"])
        self.assertFalse(self.data["native_encounters_verified"])
    def test_002_u03_has_exactly_74_reference_areas(self):
        self.assertEqual(len(self.data["areas"]),74)
        self.assertEqual(self.report["u03_area_references"],74)
    def test_003_all_reference_keys_equal_u03_order(self):
        self.assertEqual([a["area_key"] for a in self.data["areas"]],
                         [a["key"] for a in self.u03["areas"]])
    def test_004_method_registry_has_twenty_blue_pbs_methods(self):
        self.assertEqual(len(self.data["method_registry"]),20)
        self.assertEqual(self.report["pbs_method_names"],20)
    def test_005_pbs_registry_is_sourced_from_static_ast(self):
        self.assertEqual(wild._extract_pbs_methods(self.pbs),
                         {r["pbs_method"] for r in self.data["method_registry"]})
    def test_006_methods_include_land_and_day_parts(self):
        self.assertTrue(set(wild.LAND)<={x["pbs_method"] for x in self.data["method_registry"]})
    def test_007_methods_include_cave_and_day_parts(self):
        self.assertTrue(set(wild.CAVE)<={x["pbs_method"] for x in self.data["method_registry"]})
    def test_008_methods_include_water_and_day_parts(self):
        self.assertTrue(set(wild.WATER)<={x["pbs_method"] for x in self.data["method_registry"]})
    def test_009_methods_include_three_rod_variants(self):
        self.assertTrue(set(wild.FISH)<={x["pbs_method"] for x in self.data["method_registry"]})
    def test_010_methods_include_rock_smash(self):
        self.assertIn("RockSmash",[x["pbs_method"] for x in self.data["method_registry"]])
    def test_011_no_headbutt_pbs_assumed(self):
        self.assertNotIn("HeadbuttHigh",[x["pbs_method"] for x in self.data["method_registry"]])
        self.assertNotIn("HeadbuttLow",[x["pbs_method"] for x in self.data["method_registry"]])
    def test_012_headbutt_can_exist_in_habitat_without_pbs(self):
        self.assertIn("HeadbuttHigh",self.habitat)
        self.assertIn("HeadbuttLow",self.habitat)
    def test_013_morning_specific_pbs_marked_morning(self):
        self.assertEqual(next(x["time_bucket"] for x in self.data["method_registry"]
                if x["pbs_method"]=="LandMorning"),"MORNING")
    def test_014_evening_specific_pbs_marked_evening(self):
        self.assertEqual(next(x["time_bucket"] for x in self.data["method_registry"]
                if x["pbs_method"]=="CaveEvening"),"EVENING")
    def test_015_day_neutral_land_method_any_time(self):
        self.assertEqual(next(x["time_bucket"] for x in self.data["method_registry"]
                if x["pbs_method"]=="Land"),"ANY")
    def test_016_rod_time_bucket_any(self):
        self.assertTrue(all(x["time_bucket"]=="ANY" for x in self.data["method_registry"]
                            if x["method_family"]=="FISHING"))
    def test_017_five_time_review_buckets_plus_any(self):
        self.assertEqual(self.data["time_buckets"],
                         ["ANY","MORNING","DAY","AFTERNOON","EVENING","NIGHT"])
    def test_018_four_season_review_buckets_plus_any(self):
        self.assertEqual(self.data["season_buckets"],
                         ["ANY","SPRING","SUMMER","AUTUMN","WINTER"])
    def test_019_all_versions_white_b_w(self):
        self.assertEqual(self.data["supported_campaign_variants"],["WHITE_BW"])
    def test_020_35_areas_have_method_questions_only(self):
        self.assertEqual(self.report["areas_with_candidate_review_methods"],35)
        self.assertEqual(self.report["areas_without_proven_wild_method"],39)
    def test_021_every_area_has_no_native_slot(self):
        self.assertTrue(all(a["encounter_slots"]==[] for a in self.data["areas"]))
    def test_022_every_area_has_unknown_not_zero_percentage(self):
        self.assertTrue(all(a["weight_percentages"] is None for a in self.data["areas"]))
    def test_023_every_area_has_unknown_not_zero_rates(self):
        self.assertTrue(all(a["encounter_rate"] is None for a in self.data["areas"]))
    def test_024_every_area_has_unknown_native_levels(self):
        self.assertTrue(all(a["level_ranges"] is None for a in self.data["areas"]))
    def test_025_all_areas_have_no_native_species(self):
        self.assertTrue(all(a["real_species"] is None for a in self.data["areas"]))
    def test_026_all_areas_have_no_mapids(self):
        self.assertTrue(all(a["source_map_id"] is None and
            a["destination_map_id"] is None for a in self.data["areas"]))
    def test_027_all_areas_have_no_native_pbs_verified(self):
        self.assertTrue(all(not a["native_pbs_verified"] for a in self.data["areas"]))
    def test_028_no_time_specific_species_assignment(self):
        self.assertTrue(all(a["method_time_assignments"]==[] for a in self.data["areas"]))
    def test_029_no_season_specific_species_assignment(self):
        self.assertTrue(all(a["method_season_assignments"]==[] for a in self.data["areas"]))
    def test_030_no_version_specific_species_assignment(self):
        self.assertTrue(all(a["method_version_assignments"]==[] for a in self.data["areas"]))
    def test_031_never_assume_zero_is_no_encounters(self):
        self.assertTrue(self.data["encounter_probability_policy"]["zero_is_not_proof_of_absence"])
    def test_032_no_season_rate_generation(self):
        self.assertFalse(self.data["encounter_probability_policy"]["allow_generated_percentages"])
        self.assertTrue(self.data["encounter_probability_policy"][
            "no_seasonal_or_time_derived_probabilities"])
    def test_033_evolution_chance_not_spawn_weight(self):
        self.assertTrue(self.data["encounter_probability_policy"][
            "evolution_chance_is_not_spawn_weight"])
    def test_034_g04_4_owns_later_weight_sums(self):
        self.assertEqual(self.data["encounter_probability_policy"][
            "percentage_total_check"],"DEFER_UNTIL_G04_4_SOURCE_VERIFIED")
    def test_035_route_has_land_reference_methods(self):
        self.assertIn("Land",self.sample(self.route)["candidate_methods"])
        self.assertIn("LandNight",self.sample(self.route)["candidate_methods"])
    def test_036_route_water_is_only_question_not_assignment(self):
        row=self.sample(self.route)
        self.assertIn("Water",row["candidate_methods"])
        self.assertFalse(row["actual_method_assignment_verified"])
    def test_037_route_rod_is_only_question_not_assignment(self):
        row=self.sample(self.route)
        self.assertIn("GoodRod",row["candidate_methods"])
        self.assertTrue(row["candidate_methods_are_questions_only"])
    def test_038_cave_has_cave_reference_methods(self):
        self.assertIn("CaveNight",self.sample(self.cave)["candidate_methods"])
    def test_039_cave_rocksmash_only_question(self):
        self.assertIn("RockSmash",self.sample(self.cave)["candidate_methods"])
        self.assertFalse(self.sample(self.cave)["actual_method_assignment_verified"])
    def test_040_water_has_old_good_super_rods(self):
        row=self.sample(self.water)
        self.assertEqual(row["candidate_methods"][-3:],
                         ["OldRod","GoodRod","SuperRod"])
    def test_041_settlement_not_marked_no_wild_pokemon(self):
        row=self.sample("UNOVA_NUVEMA_TOWN")
        self.assertEqual(row["candidate_methods"],[])
        self.assertIsNone(row["encounter_rate"])
    def test_042_gyms_do_not_get_synthetic_wild_tables(self):
        self.assertEqual(self.sample("UNOVA_STRIATON_GYM")["candidate_methods"],[])
    def test_043_liberty_garden_event_only_no_synthetic_spawns(self):
        row=self.sample("UNOVA_LIBERTY_GARDEN")
        self.assertEqual(row["candidate_methods"],wild.LAND and list(wild.LAND))
        self.assertEqual(row["encounter_slots"],[])
    def test_044_unity_tower_event_only_no_synthetic_spawns(self):
        self.assertEqual(self.sample("UNOVA_UNITY_TOWER")["candidate_methods"],[])
    def test_045_n_castle_no_wild_table(self):
        self.assertEqual(self.sample("UNOVA_NS_CASTLE")["candidate_methods"],[])
    def test_046_rocksmash_is_source_supported_not_natively_assigned(self):
        r=self.query(area_key=self.cave,method="RockSmash",time_bucket="ANY",
                     season_bucket="ANY")
        self.assertFalse(r["actual_method_assignment_verified"])
    def test_047_route_morning_audit_question(self):
        r=self.query(method="LandMorning",time_bucket="MORNING",
                     season_bucket="SPRING")
        self.assertEqual(r["method_question"],"LandMorning")
        self.assertEqual(r["season_question"],"SPRING")
    def test_048_route_afternoon_audit_question(self):
        r=self.query(method="LandAfternoon",time_bucket="AFTERNOON",
                     season_bucket="SUMMER")
        self.assertEqual(r["time_question"],"AFTERNOON")
    def test_049_route_evening_audit_question(self):
        r=self.query(method="LandEvening",time_bucket="EVENING",
                     season_bucket="AUTUMN")
        self.assertEqual(r["time_question"],"EVENING")
    def test_050_route_night_audit_question(self):
        r=self.query(method="LandNight",time_bucket="NIGHT",
                     season_bucket="WINTER")
        self.assertEqual(r["time_question"],"NIGHT")
    def test_051_water_surf_night_question(self):
        r=self.query(area_key=self.water,method="WaterNight",
                     time_bucket="NIGHT",season_bucket="AUTUMN")
        self.assertEqual(r["method_family"],"WATER")
    def test_052_fishing_good_rod_question_any(self):
        r=self.query(area_key=self.water,method="GoodRod",
                     time_bucket="ANY",season_bucket="SPRING")
        self.assertEqual(r["method_family"],"FISHING")
    def test_053_cave_day_question(self):
        r=self.query(area_key=self.cave,method="CaveDay",
                     time_bucket="DAY",season_bucket="SUMMER")
        self.assertEqual(r["method_family"],"CAVE")
    def test_054_cave_anytime_question(self):
        r=self.query(area_key=self.cave,method="Cave",
                     time_bucket="ANY",season_bucket="ANY")
        self.assertEqual(r["time_question"],"ANY")
    def test_055_fishing_neutral_time_morning_is_still_not_placement(self):
        r=self.query(area_key=self.water,method="OldRod",
                     time_bucket="MORNING",season_bucket="WINTER")
        self.assertEqual(r["status"],"AUDIT_QUESTION_NOT_AN_ENCOUNTER_ASSIGNMENT")
    def test_056_query_never_contains_species(self):
        r=self.query()
        self.assertEqual(r["species_method_assignments"],[])
        self.assertEqual(r["encounter_slots"],[])
    def test_057_query_never_outputs_percentage(self):
        r=self.query()
        self.assertIsNone(r["weight_percentages"])
        self.assertIsNone(r["encounter_rate"])
    def test_058_query_never_outputs_real_native_maps(self):
        r=self.query()
        self.assertIsNone(r["source_map_id"])
        self.assertIsNone(r["destination_map_id"])
        self.assertFalse(r["native_encounter_loaded"])
    def test_059_query_never_promotes_game_exe(self):
        r=self.query()
        self.assertFalse(r["can_install"])
        self.assertFalse(r["game_exe_tested"])
    def test_060_query_does_not_mutate_catalog(self):
        before=copy.deepcopy(self.data)
        self.query()
        self.assertEqual(before,self.data)
    def test_061_wrong_time_for_morning_method_refused(self):
        self.bad_input(method="LandMorning",time_bucket="NIGHT")
    def test_062_any_time_cannot_erase_night_method_suffix(self):
        self.bad_input(method="LandNight",time_bucket="ANY")
    def test_063_water_morning_mismatch_refused(self):
        self.bad_input(area_key=self.water,method="WaterMorning",
                       time_bucket="DAY")
    def test_064_cave_evening_mismatch_refused(self):
        self.bad_input(area_key=self.cave,method="CaveEvening",
                       time_bucket="AFTERNOON")
    def test_065_wrong_time_identifier_refused(self):
        self.bad_input(time_bucket="DUSK")
    def test_066_wrong_season_identifier_refused(self):
        self.bad_input(season_bucket="MONSOON")
    def test_067_non_white_version_refused(self):
        self.bad_input(version="BLACK2")
    def test_068_black_variant_not_verified_refused(self):
        self.bad_input(version="BLACK_BW")
    def test_069_unknown_area_refused(self):
        self.bad_input(area_key="UNOVA_ROUTE_99")
    def test_070_missing_area_refused(self):
        self.bad_input(area_key=None)
    def test_071_unknown_pbs_method_refused(self):
        self.bad_input(method="Fishing")
    def test_072_unsupported_headbutt_in_pbs_refused(self):
        self.bad_input(method="HeadbuttHigh")
    def test_073_gym_wild_method_is_not_falsely_assigned(self):
        self.bad_input(area_key="UNOVA_CASTELIA_GYM",method="Land")
    def test_074_undella_bay_not_falsely_assigned_cave_method(self):
        self.bad_input(area_key=self.water,method="Cave")
    def test_075_rocksmash_not_falsely_assigned_route(self):
        self.bad_input(method="RockSmash")
    def test_076_cannot_query_both_unnamed_method_and_season(self):
        self.bad_input(method=None)
    def test_077_unverified_proposed_slot_rejected_even_with_prob_100(self):
        with self.assertRaises(ValueError):wild.reject_unverified_slots(
            self.data,area_key=self.route,method="Land",
            proposed_slots=[self.fixture_slot(weight_percent=100)])
    def test_078_unverified_proposed_slot_rejected_even_if_zero_weight(self):
        with self.assertRaises(ValueError):wild.reject_unverified_slots(
            self.data,area_key=self.route,method="Land",
            proposed_slots=[self.fixture_slot(weight_percent=0)])
    def test_079_unverified_proposed_slot_rejected_even_if_rare_one_percent(self):
        with self.assertRaises(ValueError):wild.reject_unverified_slots(
            self.data,area_key=self.route,method="Land",
            proposed_slots=[self.fixture_slot(weight_percent=1)])
    def test_080_no_slot_import_without_proof_is_safe_empty(self):
        r=wild.reject_unverified_slots(self.data,area_key=self.route,
                                       method="Land",proposed_slots=[])
        self.assertEqual(r["slots"],[])
        self.assertIsNone(r["weight_percentages"])
    def test_081_unknown_method_rejected_even_empty(self):
        with self.assertRaises(ValueError):wild.reject_unverified_slots(
            self.data,area_key=self.route,method="Fishing",proposed_slots=[])
    def test_082_unknown_area_rejected_even_empty(self):
        with self.assertRaises(ValueError):wild.reject_unverified_slots(
            self.data,area_key="UNOVA_FAKE",method="Land",proposed_slots=[])
    def test_083_catalog_extra_area_refused(self):
        self.bad_catalog(lambda d:d["areas"].append(copy.deepcopy(d["areas"][0])))
    def test_084_catalog_missing_area_refused(self):
        self.bad_catalog(lambda d:d["areas"].pop())
    def test_085_catalog_reordered_area_refused(self):
        self.bad_catalog(lambda d:d["areas"].reverse())
    def test_086_catalog_mismatched_u03_kind_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(u03_kind="gym"))
    def test_087_catalog_mismatched_u03_chapter_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(chapter_scope="postgame"))
    def test_088_catalog_inserted_species_slot_refused(self):
        self.bad_catalog(lambda d:d["areas"][15]["encounter_slots"].append(
            self.fixture_slot()))
    def test_089_catalog_fake_weight_percentage_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(weight_percentages=[100]))
    def test_090_catalog_numeric_zero_rate_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(encounter_rate=0))
    def test_091_catalog_numeric_positive_rate_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(encounter_rate=15))
    def test_092_catalog_fixed_level_range_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(level_ranges=[3,5]))
    def test_093_catalog_forged_real_species_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(real_species=["PATRAT"]))
    def test_094_catalog_fake_source_mapid_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(source_map_id=518))
    def test_095_catalog_fake_destination_mapid_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(destination_map_id=518))
    def test_096_catalog_false_native_assignment_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(
            actual_method_assignment_verified=True))
    def test_097_catalog_false_seasonal_native_mapping_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(
            seasonal_species_assignment_verified=True))
    def test_098_catalog_forged_time_species_mapping_refused(self):
        self.bad_catalog(lambda d:d["areas"][15]["method_time_assignments"].append(
            {"time":"DAY","species":"PATRAT"}))
    def test_099_catalog_forged_white_only_species_mapping_refused(self):
        self.bad_catalog(lambda d:d["areas"][15]["method_version_assignments"].append(
            {"version":"WHITE_BW","species":"PATRAT"}))
    def test_100_catalog_forged_method_species_mapping_refused(self):
        self.bad_catalog(lambda d:d["areas"][15]["species_method_assignments"].append(
            {"method":"Land","species":"PATRAT"}))
    def test_101_catalog_forged_season_species_mapping_refused(self):
        self.bad_catalog(lambda d:d["areas"][15]["method_season_assignments"].append(
            {"season":"WINTER","species":"PATRAT"}))
    def test_102_catalog_false_native_pbs_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(native_pbs_verified=True))
    def test_103_catalog_false_native_gameplay_refused(self):
        self.bad_catalog(lambda d:d.update(game_exe_tested=True))
    def test_104_catalog_false_android_approval_refused(self):
        self.bad_catalog(lambda d:d.update(android_tested=True))
    def test_105_catalog_false_installable_refused(self):
        self.bad_catalog(lambda d:d.update(can_install=True))
    def test_106_catalog_false_mapid_allocation_refused(self):
        self.bad_catalog(lambda d:d.update(can_allocate_map_ids=True))
    def test_107_catalog_allow_pbs_writing_refused(self):
        self.bad_catalog(lambda d:d.update(can_write_pbs=True))
    def test_108_catalog_disable_probability_guard_refused(self):
        self.bad_catalog(lambda d:d["encounter_probability_policy"].update(
            allow_fixed_numeric_weights=True))
    def test_109_catalog_change_null_evidence_to_fake_url_refused(self):
        self.bad_catalog(lambda d:d["source_evidence"].update(
            weight_evidence="https://example.com/unknown"))
    def test_110_catalog_fake_original_file_sha_refused(self):
        self.bad_catalog(lambda d:d["source_evidence"].update(
            unova_encounters_pbs_sha256="abcd"))
    def test_111_catalog_fake_rights_approval_refused(self):
        self.bad_catalog(lambda d:d["source_evidence"].update(
            source_license_approval="approved"))
    def test_112_catalog_false_native_mapid_verification_refused(self):
        self.bad_catalog(lambda d:d["source_evidence"].update(
            source_area_map_ids_verified=True))
    def test_113_catalog_false_native_method_supported_refused(self):
        self.bad_catalog(lambda d:d["method_registry"][0].update(
            native_method_assignment_verified=True))
    def test_114_catalog_extra_method_refused(self):
        self.bad_catalog(lambda d:d["method_registry"].append(copy.deepcopy(
            d["method_registry"][0])))
    def test_115_catalog_remove_morning_method_refused(self):
        self.bad_catalog(lambda d:d["method_registry"].pop(1))
    def test_116_catalog_change_time_suffix_refused(self):
        self.bad_catalog(lambda d:d["method_registry"][1].update(time_bucket="NIGHT"))
    def test_117_catalog_add_fishing_to_gym_refused(self):
        self.bad_catalog(lambda d:d["areas"][34]["candidate_methods"].append("OldRod"))
    def test_118_catalog_forge_season_verified_in_land_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(
            seasonal_species_assignment_verified=True))
    def test_119_catalog_missing_winter_review_refused(self):
        self.bad_catalog(lambda d:d["areas"][15]["season_variants_to_audit"].remove("WINTER"))
    def test_120_catalog_disable_method_candidates_only_guard_refused(self):
        self.bad_catalog(lambda d:d["areas"][15].update(
            candidate_methods_are_questions_only=False))
    def test_121_catalog_wrong_regional_version_refused(self):
        self.bad_catalog(lambda d:d.update(reference_version="BLACK2"))
    def test_122_catalog_false_event_species_from_area_name_refused(self):
        self.bad_catalog(lambda d:d["special_encounter_policy"].update(
            can_infer_special_species_from_area_name=True))
    def test_123_catalog_remove_source_path_refused(self):
        self.bad_catalog(lambda d:d["sources"].update(areas="data/unknown.json"))
    def test_124_catalog_g04_4_weight_gate_mutated_refused(self):
        self.bad_catalog(lambda d:d["encounter_probability_policy"].update(
            percentage_total_check="ACCEPT_ANY"))
    def test_125_catalog_extra_mapped_season_refused(self):
        self.bad_catalog(lambda d:d["season_buckets"].append("MONSOON"))
    def test_126_catalog_extra_time_bucket_refused(self):
        self.bad_catalog(lambda d:d["time_buckets"].append("DAWN"))
    def test_127_catalog_extra_native_flag_refused(self):
        self.bad_catalog(lambda d:d.update(playable=True))
    def test_128_invalid_blue_pbs_method_change_refused(self):
        with self.assertRaises(ValueError):
            wild.validate_catalog(self.data,self.u03,self.regions,
                                  self.pbs.replace('"LandMorning"','"LandSunrise"'),
                                  self.habitat,self.evolution,self.sinnoh)
    def test_129_missing_blue_habitat_source_refused(self):
        with self.assertRaises(ValueError):
            wild.validate_catalog(self.data,self.u03,self.regions,
                                  self.pbs,"missing",self.evolution,self.sinnoh)
    def test_130_sinnoh_source_cannot_claim_native_verified(self):
        src=copy.deepcopy(self.sinnoh);src["encounter_weights_verified"]=True
        with self.assertRaises(ValueError):
            wild.validate_catalog(self.data,self.u03,self.regions,
                                  self.pbs,self.habitat,self.evolution,src)
    def test_131_u03_route_provenance_cannot_change_silently(self):
        source=copy.deepcopy(self.u03)
        source["areas"][15]["source_map_id"]=518
        with self.assertRaises(ValueError):
            wild.validate_catalog(self.data,source,self.regions,
                                  self.pbs,self.habitat,self.evolution,self.sinnoh)
    def test_132_unova_region_cannot_be_falsely_promoted(self):
        regions=copy.deepcopy(self.regions)
        regions["regions"]["UNOVA"]["status"]="playable"
        with self.assertRaises(ValueError):
            wild.validate_catalog(self.data,self.u03,regions,
                                  self.pbs,self.habitat,self.evolution,self.sinnoh)
    def test_133_demo_has_all_four_seasons_and_no_probabilities(self):
        r=wild.demo(self.data)
        self.assertEqual(r["seasons"],["SPRING","WINTER","SUMMER","AUTUMN"])
        self.assertEqual(r["verified_probabilities"],0)
        self.assertFalse(r["can_install"])
    def test_134_cli_check(self):
        r=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_unova_g04_encounter_methods.py"),
            "--check"],cwd=ROOT,capture_output=True,text=True,timeout=45)
        self.assertEqual(r.returncode,0,r.stderr+r.stdout)
        self.assertEqual(json.loads(r.stdout)["u03_area_references"],74)
    def test_135_cli_demo(self):
        r=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_unova_g04_encounter_methods.py"),
            "--simulate-demo"],cwd=ROOT,capture_output=True,text=True,timeout=45)
        self.assertEqual(r.returncode,0,r.stderr+r.stdout)
        self.assertEqual(json.loads(r.stdout)["native_encounters"],0)
    def test_136_source_registry_has_no_verified_probs(self):
        self.assertTrue(all(row["source_status"]=="PLANNED_U03_AREA_ONLY"
            for row in self.data["areas"]))
        self.assertTrue(all(row["actual_area_rates_verified"] is False
            for row in self.data["areas"]))

if __name__=="__main__":
    unittest.main()
