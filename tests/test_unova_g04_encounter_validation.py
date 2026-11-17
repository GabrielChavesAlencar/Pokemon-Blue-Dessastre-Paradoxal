"""Unova G04.4: fixture-only encounter probability integrity + native gaps."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g04_encounter_validation as mod

class UnovaG044Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data, cls.g04, cls.g43, cls.report = mod.load_project()
        cls.regions = mod.g042.load_json(ROOT/cls.data["sources"]["registry"])
        cls.tracker = mod.g042.load_json(ROOT/cls.data["sources"]["tracker"])

    def slot(self,species="FIXTURE_A",weight=100,low=2,high=4,source="SYNTHETIC_FIXTURE"):
        return {"species":species,"weight_percent":weight,
                "level_min":low,"level_max":high,"source":source}

    def group(self,**overrides):
        row={"area_key":"UNOVA_ROUTE_01","method":"Land",
             "time_bucket":"ANY","season_bucket":"ANY","campaign":"WHITE_BW",
             "encounter_rate":15,"source":"SYNTHETIC_FIXTURE",
             "slots":[self.slot()]}
        row.update(overrides)
        return row

    def audit(self,rows=None,**kw):
        return mod.evaluate_fixtures(self.data,self.g04,
                 [self.group()] if rows is None else rows,**kw)

    def reject(self,rows=None,**kw):
        with self.assertRaises(ValueError):self.audit(rows,**kw)

    def bad_catalog(self,mutation):
        copydata=copy.deepcopy(self.data)
        mutation(copydata)
        with self.assertRaises(ValueError):
            mod.validate_catalog(copydata,self.g04,self.g43,self.regions,self.tracker)

    def test_001_74_symbolic_area_rows(self):
        self.assertEqual(self.report["symbolic_areas"],74)
        self.assertEqual(len(self.data["areas"]),74)
    def test_002_area_order_matches_g04_2_and_g04_3(self):
        self.assertEqual([a["area_key"] for a in self.data["areas"]],
                         [a["area_key"] for a in self.g04["areas"]])
        self.assertEqual([a["area_key"] for a in self.data["areas"]],
                         [a["area_key"] for a in self.g43["areas"]])
    def test_003_34_candidate_areas(self):
        self.assertEqual(self.report["areas_with_candidate_method_questions"],34)
    def test_004_40_areas_no_generic_candidates(self):
        self.assertEqual(self.report["areas_without_candidate_methods"],40)
    def test_005_twenty_supported_pbs_methods(self):
        self.assertEqual(self.report["source_supported_pbs_methods"],20)
    def test_006_no_native_weight_evidence(self):
        self.assertTrue(all(a["native_weights"] is None for a in self.data["areas"]))
    def test_007_no_native_species_evidence(self):
        self.assertTrue(all(a["native_species"] is None for a in self.data["areas"]))
    def test_008_no_native_level_evidence(self):
        self.assertTrue(all(a["native_levels"] is None for a in self.data["areas"]))
    def test_009_no_native_encounter_rates(self):
        self.assertTrue(all(a["native_encounter_rate"] is None for a in self.data["areas"]))
    def test_010_no_native_slots(self):
        self.assertTrue(all(a["native_slots"] == [] for a in self.data["areas"]))
    def test_011_no_native_map_ids(self):
        self.assertTrue(all(a["native_map_id"] is None for a in self.data["areas"]))
    def test_012_no_falsely_installed_methods(self):
        self.assertTrue(all(a["native_method_verified"] is False
                            and a["native_pbs_verified"] is False
                            and a["installable"] is False for a in self.data["areas"]))
    def test_013_no_native_source_sha_or_rights(self):
        self.assertTrue(all(x is None for x in self.data["native_evidence"].values()))
    def test_014_no_game_exe_or_android_approval(self):
        self.assertFalse(self.data["game_exe_tested"])
        self.assertFalse(self.data["android_tested"])
    def test_015_no_pbs_write_or_install(self):
        self.assertFalse(self.data["can_write_pbs"])
        self.assertFalse(self.data["can_install"])
        self.assertFalse(self.data["can_allocate_map_ids"])
    def test_016_registry_still_planned(self):
        self.assertEqual(self.regions["regions"]["UNOVA"]["status"],"planned")
    def test_017_no_technical_or_playable_bar(self):
        self.assertEqual(self.tracker["native_technical_bar"]["completed"],0)
        self.assertEqual(self.tracker["native_playable_bar"]["completed"],0)
    def test_018_sum_is_group_specific(self):
        self.assertEqual(self.data["policy"]["partition_dimensions"],
            ["area_key","method","time_bucket","season_bucket","campaign"])
    def test_019_incomplete_sum_not_zero(self):
        self.assertIsNone(self.data["policy"]["incomplete_table_sum"])
    def test_020_100_complete_fixture_valid(self):
        result=self.audit()
        self.assertEqual(result["complete_synthetic_partitions"],1)
        self.assertEqual(result["partitions"][0]["weight_sum_percent"],100)
    def test_021_80_20_sum_valid(self):
        result=self.audit([self.group(slots=[
            self.slot(weight=80),self.slot("FIXTURE_B",20)])])
        self.assertEqual(result["partitions"][0]["weight_sum_percent"],100)
    def test_022_50_50_sum_valid(self):
        self.assertEqual(self.audit([self.group(slots=[self.slot(weight=50),
             self.slot("FIXTURE_B",50)])])["complete_synthetic_partitions"],1)
    def test_023_three_slots_sum_valid(self):
        self.assertEqual(self.audit([self.group(slots=[self.slot(weight=25),
             self.slot("FIXTURE_B",25),self.slot("FIXTURE_C",50)])]
            )["partitions"][0]["weight_sum_percent"],100)
    def test_024_90_sum_rejected(self):
        self.reject([self.group(slots=[self.slot(weight=90)])])
    def test_025_101_sum_rejected(self):
        self.reject([self.group(slots=[self.slot(weight=100),
                 self.slot("FIXTURE_B",1)])])
    def test_026_0_weight_rejected_not_absence_of_encounters(self):
        self.reject([self.group(slots=[self.slot(weight=0)])])
    def test_027_negative_weight_rejected(self):
        self.reject([self.group(slots=[self.slot(weight=-1)])])
    def test_028_float_weight_rejected(self):
        self.reject([self.group(slots=[self.slot(weight=50.0)])])
    def test_029_boolean_weight_rejected(self):
        self.reject([self.group(slots=[self.slot(weight=True)])])
    def test_030_missing_weight_preserves_null(self):
        result=self.audit([self.group(slots=[self.slot(weight=None)])])
        self.assertIsNone(result["partitions"][0]["weight_sum_percent"])
        self.assertIn("weight_percent",result["partitions"][0]["unknown_fields"])
    def test_031_partial_50_plus_unknown_preserves_null(self):
        result=self.audit([self.group(slots=[self.slot(weight=50),
                   self.slot("FIXTURE_B",None)])])
        self.assertIsNone(result["partitions"][0]["weight_sum_percent"])
    def test_032_100_plus_unknown_does_not_claim_complete(self):
        result=self.audit([self.group(slots=[self.slot(weight=100),
                   self.slot("FIXTURE_B",None)])])
        self.assertIsNone(result["partitions"][0]["weight_sum_percent"])
    def test_033_zero_slots_not_no_encounters(self):
        result=self.audit([self.group(slots=[])])
        self.assertEqual(result["partitions"][0]["status"],
                         "INCOMPLETE_SYNTHETIC_FIXTURE_UNKNOWNS_PRESERVED")
        self.assertIn("slots",result["partitions"][0]["unknown_fields"])
    def test_034_missing_rate_does_not_claim_completeness(self):
        result=self.audit([self.group(encounter_rate=None)])
        self.assertIsNone(result["partitions"][0]["weight_sum_percent"])
        self.assertIn("encounter_rate",result["partitions"][0]["unknown_fields"])
    def test_035_missing_species_preserves_null(self):
        result=self.audit([self.group(slots=[self.slot(species=None)])])
        self.assertIsNone(result["partitions"][0]["weight_sum_percent"])
        self.assertIn("species",result["partitions"][0]["unknown_fields"])
    def test_036_missing_level_min_preserves_null(self):
        result=self.audit([self.group(slots=[self.slot(low=None)])])
        self.assertIsNone(result["partitions"][0]["weight_sum_percent"])
    def test_037_missing_level_max_preserves_null(self):
        result=self.audit([self.group(slots=[self.slot(high=None)])])
        self.assertIsNone(result["partitions"][0]["weight_sum_percent"])
    def test_038_level_min_greater_max_rejected(self):
        self.reject([self.group(slots=[self.slot(low=10,high=8)])])
    def test_039_below_level_one_rejected(self):
        self.reject([self.group(slots=[self.slot(low=0)])])
    def test_040_above_engine_limit_rejected(self):
        self.reject([self.group(slots=[self.slot(high=101)])])
    def test_041_level_equal_engine_limit_valid(self):
        self.assertEqual(self.audit([self.group(slots=[self.slot(high=100)])]
              )["complete_synthetic_partitions"],1)
    def test_042_duplicate_full_partition_rejected(self):
        self.reject([self.group(),self.group()])
    def test_043_duplicate_identical_slot_rejected(self):
        self.reject([self.group(slots=[self.slot(weight=50),
               self.slot(weight=50)])])
    def test_044_same_species_different_levels_allowed(self):
        result=self.audit([self.group(slots=[self.slot(weight=50,low=2,high=4),
                                    self.slot(weight=50,low=5,high=6)])])
        self.assertEqual(result["partitions"][0]["weight_sum_percent"],100)
    def test_045_time_partitions_are_independent(self):
        result=self.audit([self.group(time_bucket="MORNING"),
                 self.group(time_bucket="NIGHT")])
        self.assertEqual(result["complete_synthetic_partitions"],2)
    def test_046_season_partitions_are_independent(self):
        result=self.audit([self.group(season_bucket="SPRING"),
                 self.group(season_bucket="WINTER")])
        self.assertEqual(result["complete_synthetic_partitions"],2)
    def test_047_method_partitions_independent(self):
        result=self.audit([self.group(method="Land"),self.group(method="Water")])
        self.assertEqual(result["complete_synthetic_partitions"],2)
    def test_048_area_partitions_independent(self):
        result=self.audit([self.group(area_key="UNOVA_ROUTE_01"),
                 self.group(area_key="UNOVA_ROUTE_02")])
        self.assertEqual(result["complete_synthetic_partitions"],2)
    def test_049_no_other_variant_without_provenance(self):
        self.reject([self.group(campaign="BLACK_BW")])
    def test_050_night_method_wrong_time_rejected(self):
        self.reject([self.group(method="LandNight",time_bucket="DAY")])
    def test_051_night_method_correct_time_allowed(self):
        self.assertEqual(self.audit([self.group(method="LandNight",
                    time_bucket="NIGHT")])["complete_synthetic_partitions"],1)
    def test_052_invalid_time_bucket_rejected(self):
        self.reject([self.group(time_bucket="DAWN")])
    def test_053_invalid_season_bucket_rejected(self):
        self.reject([self.group(season_bucket="MONSOON")])
    def test_054_invalid_pbs_method_rejected(self):
        self.reject([self.group(method="Fishing")])
    def test_055_headbutt_not_pbs_method(self):
        self.reject([self.group(method="HeadbuttHigh")])
    def test_056_event_area_must_not_get_random_tables(self):
        self.reject([self.group(area_key="UNOVA_LIBERTY_GARDEN")])
    def test_057_gym_must_not_get_random_tables(self):
        self.reject([self.group(area_key="UNOVA_STRIATON_GYM")])
    def test_058_unknown_area_rejected(self):
        self.reject([self.group(area_key="UNOVA_ROUTE_99")])
    def test_059_native_group_source_rejected(self):
        self.reject([self.group(source="NATIVE_PBS")])
    def test_060_native_slot_source_rejected(self):
        self.reject([self.group(slots=[self.slot(source="NATIVE_PBS")])])
    def test_061_real_species_id_rejected(self):
        self.reject([self.group(slots=[self.slot(species="PATRAT")])])
    def test_062_native_input_source_rejected(self):
        self.reject(input_source="NATIVE_PBS")
    def test_063_negative_encounter_rate_rejected(self):
        self.reject([self.group(encounter_rate=-1)])
    def test_064_string_encounter_rate_rejected(self):
        self.reject([self.group(encounter_rate="15")])
    def test_065_zero_rate_fixture_valid_not_native_proof(self):
        result=self.audit([self.group(encounter_rate=0)])
        self.assertEqual(result["partitions"][0]["encounter_rate"],0)
        self.assertFalse(result["partitions"][0]["native_source_verified"])
    def test_066_no_native_pbs_mutations_claimed(self):
        result=self.audit()
        self.assertFalse(result["native_game_modified"])
        self.assertFalse(result["can_install"])
        self.assertEqual(result["native_tables_checked"],0)
    def test_067_extraneous_slot_field_rejected(self):
        s=self.slot()
        s["assigned_by_unova"]=True
        self.reject([self.group(slots=[s])])
    def test_068_extraneous_partition_field_rejected(self):
        row=self.group()
        row["native_verified"]=True
        self.reject([row])
    def test_069_invalid_engine_max_rejected(self):
        self.reject(engine_max_level=0)
    def test_070_boolean_engine_max_rejected(self):
        self.reject(engine_max_level=True)
    def test_071_catalog_weight_forgery_refused(self):
        self.bad_catalog(lambda d:d["areas"][0].update(native_weights=[100]))
    def test_072_catalog_zero_rate_forgery_refused(self):
        self.bad_catalog(lambda d:d["areas"][0].update(native_encounter_rate=0))
    def test_073_catalog_species_forgery_refused(self):
        self.bad_catalog(lambda d:d["areas"][0].update(native_species="PATRAT"))
    def test_074_catalog_method_verified_forgery_refused(self):
        self.bad_catalog(lambda d:d["areas"][0].update(native_method_verified=True))
    def test_075_catalog_slot_forgery_refused(self):
        self.bad_catalog(lambda d:d["areas"][0].update(native_slots=[{}]))
    def test_076_catalog_mapid_forgery_refused(self):
        self.bad_catalog(lambda d:d["areas"][0].update(native_map_id=518))
    def test_077_catalog_source_sha_forgery_refused(self):
        self.bad_catalog(lambda d:d["native_evidence"].update(encounters_pbs_sha256="fake"))
    def test_078_catalog_license_forgery_refused(self):
        self.bad_catalog(lambda d:d["native_evidence"].update(source_license_approval=True))
    def test_079_catalog_flag_forgery_refused(self):
        self.bad_catalog(lambda d:d.update(can_install=True))
    def test_080_catalog_missing_area_refused(self):
        self.bad_catalog(lambda d:d["areas"].pop())
    def test_081_catalog_order_swap_refused(self):
        self.bad_catalog(lambda d:d["areas"].reverse())
    def test_082_catalog_wrong_policy_refused(self):
        self.bad_catalog(lambda d:d["policy"].update(complete_fixture_weight_sum=99))
    def test_083_catalog_extra_field_refused(self):
        self.bad_catalog(lambda d:d.update(real_tables_verified=True))
    def test_084_demo_has_two_complete_and_one_incomplete(self):
        result=mod.demo(self.data,self.g04)
        self.assertEqual(result["partitions_checked"],3)
        self.assertEqual(result["complete_synthetic_partitions"],2)
        self.assertIsNone(result["partitions"][1]["weight_sum_percent"])
    def test_085_demo_preserves_season_and_time(self):
        result=mod.demo(self.data,self.g04)
        self.assertEqual(result["partitions"][1]["partition"]["season_bucket"],"WINTER")
        self.assertEqual(result["partitions"][1]["partition"]["time_bucket"],"NIGHT")
    def test_086_fixture_does_not_mutate_contract(self):
        before=copy.deepcopy(self.data)
        self.audit()
        self.assertEqual(self.data,before)
    def test_087_cli_check(self):
        proc=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g04_encounter_validation.py"),
            "--check"],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["symbolic_areas"],74)
    def test_088_cli_demo(self):
        proc=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g04_encounter_validation.py"),
            "--simulate-demo"],capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stdout+proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["complete_synthetic_partitions"],2)

if __name__=="__main__":
    unittest.main()
