"""G01.1 strict versioned state model: offline structural contract, no native game files."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g01_state_schema as g01

class G011StateSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract=g01.load_json(g01.CONTRACT)
        cls.schema=g01.load_json(g01.SCHEMA)
        cls.areas=g01.load_json(g01.AREAS)
        cls.events=g01.load_json(g01.EVENTS)
        cls.regions=g01.load_json(g01.REGIONS)

    def c(self):
        return copy.deepcopy(self.contract)
    def state(self):
        return g01.empty_state(self.contract)
    def check_contract(self,contract=None,schema=None,areas=None,events=None,regions=None):
        return g01.validate_contract(
            self.contract if contract is None else contract,
            self.schema if schema is None else schema,
            self.areas if areas is None else areas,
            self.events if events is None else events,
            self.regions if regions is None else regions)
    def check_state(self,state):
        return g01.validate_state(state,self.contract,self.areas)
    def deny_state(self,change):
        state=self.state();change(state)
        with self.assertRaises(ValueError):
            self.check_state(state)
    def deny_contract(self,change):
        c=self.c();change(c)
        with self.assertRaises(ValueError):
            self.check_contract(contract=c)

    def test_01_original_contract_validated(self):
        report=self.check_contract()
        self.assertEqual(report["status"],"VERSIONED_SCHEMA_VALIDATED_OFFLINE_ONLY")
        self.assertFalse(report["can_install"])
        self.assertFalse(report["game_exe_tested"])
        self.assertFalse(report["android_tested"])
    def test_02_counts_and_u03_u07_anchors(self):
        report=self.check_contract()
        self.assertEqual((report["chapters"],report["missions"],report["flags"]),(13,12,25))
        self.assertEqual((report["source_areas"],report["source_u07_events"]),(74,13))
        self.assertEqual(self.contract["flag_catalog"][0]["key"],
                         self.events["events"][0]["key"])
    def test_03_default_state_empty_and_pure(self):
        state=self.state()
        self.assertEqual(state["current_chapter"],"UNOVA_CH00_NOT_STARTED")
        self.assertEqual(state["flags"],{})
        self.assertEqual(state["missions"],{})
        self.assertEqual(state["checkpoint"]["map_id"],None)
        self.assertTrue(self.check_state(state)["structurally_valid"])
        self.assertFalse(self.check_state(state)["native_save_compatible"])
    def test_04_state_cloned_not_mutated(self):
        first=self.state();first["flags"]["UNOVA_U07_STARTER_GIFT"]=True
        second=self.state()
        self.assertEqual(second["flags"],{})
        self.assertNotEqual(first,second)
    def test_05_sparse_flag_and_mission_values_pass_structural_only(self):
        state=self.state()
        state["flags"]["UNOVA_U07_STARTER_GIFT"]=True
        state["missions"]["UNOVA_MISSION_CH01_BEGIN_JOURNEY"]="active"
        self.assertTrue(self.check_state(state)["structurally_valid"])
        self.assertFalse(self.check_state(state)["transitions_verified"])
    def test_06_symbolic_area_checkpoint_accepted(self):
        state=self.state()
        state["checkpoint"]["last_story_area_key"]="UNOVA_NUVEMA_TOWN"
        state["checkpoint"]["last_heal_center_area_key"]="UNOVA_ACCUMULA_TOWN"
        state["checkpoint"]["last_safe_area_key"]="UNOVA_ROUTE_01"
        self.assertTrue(self.check_state(state)["structurally_valid"])
        self.assertFalse(state["checkpoint"]["verified_in_game"])
    def test_07_each_chapter_is_reference_only(self):
        for ch in self.contract["chapters"]:
            self.assertIsNone(ch["map_id"])
            self.assertFalse(ch["game_exe_verified"])
    def test_08_future_version_is_not_silently_migrated(self):
        self.deny_state(lambda x:x.update(schema_version=2))
    def test_09_old_version_is_not_silently_migrated(self):
        self.deny_state(lambda x:x.update(schema_version=0))
    def test_10_boolean_version_does_not_equal_int(self):
        self.deny_state(lambda x:x.update(schema_version=True))
    def test_11_cross_region_save_rejected(self):
        self.deny_state(lambda x:x.update(region="SINNOH"))
    def test_12_other_campaign_version_rejected(self):
        self.deny_state(lambda x:x.update(campaign="BLACK_BW"))
    def test_13_native_save_claim_rejected(self):
        self.deny_state(lambda x:x.update(state_status="NATIVE_SAVE"))
    def test_14_extra_native_game_field_rejected(self):
        self.deny_state(lambda x:x.update(GameSave={"player":True}))
    def test_15_missing_required_field_rejected(self):
        self.deny_state(lambda x:x.pop("missions"))
    def test_16_unknown_chapter_rejected(self):
        self.deny_state(lambda x:x.update(current_chapter="UNOVA_CH99_INSTALLED"))
    def test_17_unova_flag_namespace_must_be_registered(self):
        self.deny_state(lambda x:x["flags"].update({"UNOVA_FAKE_GYM":True}))
    def test_18_known_flag_only_accepts_real_boolean(self):
        self.deny_state(lambda x:x["flags"].update({"UNOVA_U07_STARTER_GIFT":1}))
    def test_19_known_flag_cannot_accept_string_boolean(self):
        self.deny_state(lambda x:x["flags"].update({"UNOVA_U07_STARTER_GIFT":"true"}))
    def test_20_unknown_mission_rejected(self):
        self.deny_state(lambda x:x["missions"].update({"UNOVA_MISSION_HACK":"completed"}))
    def test_21_invalid_mission_status_rejected(self):
        self.deny_state(lambda x:x["missions"].update({"UNOVA_MISSION_CH01_BEGIN_JOURNEY":"playable"}))
    def test_22_mission_value_requires_string(self):
        self.deny_state(lambda x:x["missions"].update({"UNOVA_MISSION_CH01_BEGIN_JOURNEY":True}))
    def test_23_unknown_checkpoint_area_rejected(self):
        self.deny_state(lambda x:x["checkpoint"].update(last_story_area_key="UNOVA_UNKNOWN"))
    def test_24_cross_region_checkpoint_rejected(self):
        self.deny_state(lambda x:x["checkpoint"].update(last_safe_area_key="KANTO_PALLET"))
    def test_25_numeric_mapid_rejected(self):
        self.deny_state(lambda x:x["checkpoint"].update(map_id=518))
    def test_26_coordinate_x_rejected(self):
        self.deny_state(lambda x:x["checkpoint"].update(x=4))
    def test_27_coordinate_y_rejected(self):
        self.deny_state(lambda x:x["checkpoint"].update(y=2))
    def test_28_false_claim_native_checkpoint_rejected(self):
        self.deny_state(lambda x:x["checkpoint"].update(verified_in_game=True))
    def test_29_unknown_checkpoint_attr_rejected(self):
        self.deny_state(lambda x:x["checkpoint"].update(save_file="File1.rxdata"))
    def test_30_bad_checkpoint_type_rejected(self):
        self.deny_state(lambda x:x.update(checkpoint=None))
    def test_31_catalog_duplicate_chapter_rejected(self):
        self.deny_contract(lambda c:c["chapters"][1].update(key=c["chapters"][0]["key"]))
    def test_32_catalog_duplicate_flag_rejected(self):
        self.deny_contract(lambda c:c["flag_catalog"][2].update(key=c["flag_catalog"][1]["key"]))
    def test_33_catalog_forged_native_switch_rejected(self):
        self.deny_contract(lambda c:c["flag_catalog"][0].update(native_switch_id=5))
    def test_34_catalog_forged_mapid_rejected(self):
        self.deny_contract(lambda c:c["chapters"][1].update(map_id=518))
    def test_35_catalog_forged_real_event_rejected(self):
        self.deny_contract(lambda c:c["missions"][0].update(real_event_id=14))
    def test_36_catalog_mission_to_wrong_chapter_rejected(self):
        self.deny_contract(lambda c:c["missions"][0].update(chapter_key="UNOVA_CH10_LEAGUE"))
    def test_37_catalog_flag_not_in_u07_rejected(self):
        self.deny_contract(lambda c:c["flag_catalog"][0].update(source_event_key="UNOVA_U07_NEW"))
    def test_38_areas_catalog_forged_installed_rejected(self):
        areas=copy.deepcopy(self.areas);areas["may_install"]=True
        with self.assertRaises(ValueError):self.check_contract(areas=areas)
    def test_39_event_contract_forged_install_rejected(self):
        events=copy.deepcopy(self.events);events["can_install"]=True
        with self.assertRaises(ValueError):self.check_contract(events=events)
    def test_40_region_registry_playable_rejected(self):
        regions=copy.deepcopy(self.regions);regions["regions"]["UNOVA"]["status"]="playable"
        with self.assertRaises(ValueError):self.check_contract(regions=regions)
    def test_41_json_schema_additional_flag_rejected(self):
        schema=copy.deepcopy(self.schema)
        schema["properties"]["flags"]["properties"]["UNOVA_FORGED"]={"type":"boolean"}
        with self.assertRaises(ValueError):self.check_contract(schema=schema)
    def test_42_json_schema_unknown_native_checkpoint_rejected(self):
        schema=copy.deepcopy(self.schema)
        schema["properties"]["checkpoint"]["properties"]["map_id"]={"type":"integer"}
        with self.assertRaises(ValueError):self.check_contract(schema=schema)
    def test_43_json_schema_mission_values_mismatch(self):
        schema=copy.deepcopy(self.schema)
        schema["properties"]["missions"]["properties"]["UNOVA_MISSION_CH01_BEGIN_JOURNEY"]["enum"]=["playable"]
        with self.assertRaises(ValueError):self.check_contract(schema=schema)
    def test_44_json_schema_flag_directory_not_open(self):
        schema=copy.deepcopy(self.schema)
        schema["properties"]["flags"]["additionalProperties"]=True
        with self.assertRaises(ValueError):self.check_contract(schema=schema)
    def test_45_policy_does_not_auto_migrate(self):
        self.deny_contract(lambda c:c["compatibility"].update(implicit_migration=True))
    def test_46_policy_does_not_accept_future(self):
        self.deny_contract(lambda c:c["compatibility"].update(accepted_versions=[1,2]))
    def test_47_contract_cannot_claim_native_game_test(self):
        self.deny_contract(lambda c:c.update(game_exe_tested=True))
    def test_48_contract_cannot_claim_assets_imported(self):
        self.deny_contract(lambda c:c.update(source_assets_imported=True))
    def test_49_contract_must_keep_both_catalog_refs(self):
        self.deny_contract(lambda c:c.update(source_area_catalog="other.json"))
    def test_51_default_state_cannot_forge_completed_event(self):
        self.deny_contract(lambda c:c["default_state"]["flags"].update(
            {"UNOVA_U07_STARTER_GIFT":True}))

    def test_52_default_state_cannot_start_in_elite_four(self):
        self.deny_contract(lambda c:c["default_state"].update(
            current_chapter="UNOVA_CH10_LEAGUE"))

    def test_50_cli_reports_offline_mode_and_no_game(self):
        result=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g01_state_schema.py"),"--check"],
            cwd=ROOT,text=True,capture_output=True,timeout=20,check=False)
        self.assertEqual(result.returncode,0,result.stderr+"\n"+result.stdout)
        summary=json.loads(result.stdout.strip())
        self.assertEqual(summary["chapters"],13)
        self.assertFalse(summary["can_install"])
        self.assertFalse((ROOT/"game"/"Game.exe").exists())

if __name__=="__main__":
    unittest.main()
