"""G05.1 Unova regional HM/key item isolation; no native saves or pickup events."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g05_regional_items as mod


class UnovaG051Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data,cls.registry,cls.report=mod.load_project()
        cls.state_doc=mod.load_json(ROOT,cls.data["sources"]["state"])
        cls.sinnoh=mod.load_json(ROOT,cls.data["sources"]["sinnoh_reference"])
        cls.tracker=mod.load_json(ROOT,cls.data["sources"]["tracker"])
        cls.travel_rb=mod.read_source(ROOT,cls.data["sources"]["travel_runtime"])
        cls.field_rb=mod.read_source(ROOT,cls.data["sources"]["field_runtime"])
        cls.regions_rb=mod.read_source(ROOT,cls.data["sources"]["regions_runtime"])

    def item(self,name="ALPHA",kind="HM",qty=1):
        return {"id":"FIXTURE_"+name,"kind":kind,"qty":qty}

    def state(self):
        return {
            "scope":mod.SCOPE,"current":"KANTO",
            "bag":[self.item("KANTO_HM"),self.item("KEY_KANTO","KEY_ITEM"),
                   self.item("TM","TM"),self.item("REPEL","CONSUMABLE"),
                   self.item("STONE","MEGA_STONE")],
            "pc":[self.item("KANTO_PC_KEY","KEY_ITEM"),
                  self.item("PC_TM","TM")],
            "registered":["FIXTURE_KANTO_HM","FIXTURE_TM"],
            "vault":{"UNOVA":{
                "items":[self.item("UNOVA_HM")],
                "pc_items":[self.item("UNOVA_PC_KEY","KEY_ITEM")],
                "registered":["FIXTURE_UNOVA_HM"],
            }},
            "bag_capacity":12,"pc_capacity":12,"badges":[]
        }

    def travel(self,state=None,destination="UNOVA",**kwargs):
        return mod.plan_travel(self.data,self.registry,self.state() if state is None else state,
                               destination,**kwargs)

    def bad_travel(self,state=None,destination="UNOVA",**kwargs):
        with self.assertRaises(ValueError):self.travel(state,destination,**kwargs)

    def altered_catalog(self,func):
        changed=copy.deepcopy(self.data)
        func(changed)
        with self.assertRaises(ValueError):
            mod.validate_catalog(changed,self.registry,self.state_doc,self.sinnoh,
                                 self.tracker,self.travel_rb,self.field_rb,self.regions_rb)

    def field(self,state=None,action="SURF",local_event=False,hm_item_id="FIXTURE_UNOVA_HM"):
        if state is None:state=self.travel()["fixture"]
        return mod.plan_field_access(self.data,self.registry,state,action=action,
                      local_event=local_event,hm_item_id=hm_item_id)

    def test_001_policy_name(self):
        self.assertEqual(self.data["phase"],"G05.1")
        self.assertEqual(self.data["campaign"],"WHITE_BW")
    def test_002_unova_planned(self):
        self.assertEqual(self.registry["regions"]["UNOVA"]["status"],"planned")
    def test_003_no_native_item_ids(self):
        self.assertTrue(all(v is None for v in self.data["native_evidence"].values()))
    def test_004_unova_six_field_actions(self):
        self.assertEqual(self.report["unova_field_actions"],6)
    def test_005_six_action_order(self):
        self.assertEqual([v["action"] for v in self.data["unova_field_rules"]],list(mod.ACTIONS))
    def test_006_all_events_match_registry(self):
        for row in self.data["unova_field_rules"]:
            self.assertEqual(self.registry["regions"]["UNOVA"]["field"][row["action"]],
                             {"event":row["event"],"tool":True})
    def test_007_no_native_pickup_events(self):
        self.assertTrue(all(not row["pickup_source_proven"] for row in self.data["unova_field_rules"]))
    def test_008_no_native_item_ids_or_events(self):
        self.assertTrue(all(row["native_hm_id"] is None and row["native_event_id"] is None
                            for row in self.data["unova_field_rules"]))
    def test_009_no_installable_rules(self):
        self.assertTrue(all(not row["implemented"] for row in self.data["unova_field_rules"]))
        self.assertFalse(self.data["can_install"])
    def test_010_no_native_qa(self):
        self.assertFalse(self.data["game_exe_tested"])
        self.assertFalse(self.data["android_tested"])
    def test_011_no_real_save_mutation(self):
        self.assertFalse(self.data["native_saves_modified"])
    def test_012_no_native_pbs_modified(self):
        self.assertFalse(self.data["native_pbs_verified"])
    def test_013_no_false_native_pickups(self):
        self.assertFalse(self.data["native_pickups_verified"])
    def test_014_technical_bar_still_zero(self):
        self.assertEqual(self.tracker["native_technical_bar"]["completed"],0)
    def test_015_playable_bar_still_zero(self):
        self.assertEqual(self.tracker["native_playable_bar"]["completed"],0)
    def test_016_source_g01_no_native_save(self):
        self.assertEqual(self.state_doc["status"],"VERSIONED_SCHEMA_ONLY_NOT_NATIVE_SAVE")
    def test_017_sinnoh_reference_not_approved(self):
        self.assertFalse(self.sinnoh["approved_for_install"])
    def test_018_two_local_item_classes(self):
        self.assertEqual(self.data["classification"]["regional"],["HM","KEY_ITEM"])
    def test_019_three_global_item_classes(self):
        self.assertEqual(self.data["classification"]["global"],["TM","CONSUMABLE","MEGA_STONE"])
    def test_020_runtime_uses_game_data_metadata(self):
        self.assertIn("data.is_key_item? || data.is_HM?",self.travel_rb)
    def test_021_runtime_pc_separate_from_pokemon_boxes(self):
        self.assertIn("def self.local_pc_contents(storage)",self.travel_rb)
    def test_022_runtime_legacy_native_decades_preserved(self):
        self.assertIn('current["current"] == "DECADES"',self.field_rb)
    def test_023_integration_not_a_native_redistribution(self):
        self.assertTrue(self.data["legacy_policy"]["unova_destination_not_installed"])
    def test_024_fixture_state_schema_valid(self):
        self.assertEqual(mod.validate_state(self.state(),self.registry)["current"],"KANTO")
    def test_025_arrival_unova_current(self):
        self.assertEqual(self.travel()["fixture"]["current"],"UNOVA")
    def test_026_arrival_removes_kanto_hm(self):
        self.assertNotIn("FIXTURE_KANTO_HM",[v["id"] for v in self.travel()["fixture"]["bag"]])
    def test_027_arrival_removes_kanto_key_item(self):
        self.assertNotIn("FIXTURE_KEY_KANTO",[v["id"] for v in self.travel()["fixture"]["bag"]])
    def test_028_arrival_restores_unova_hm(self):
        self.assertIn("FIXTURE_UNOVA_HM",[v["id"] for v in self.travel()["fixture"]["bag"]])
    def test_029_arrival_pc_removes_foreign_key_item(self):
        self.assertNotIn("FIXTURE_KANTO_PC_KEY",[v["id"] for v in self.travel()["fixture"]["pc"]])
    def test_030_arrival_pc_restores_unova_key_item(self):
        self.assertIn("FIXTURE_UNOVA_PC_KEY",[v["id"] for v in self.travel()["fixture"]["pc"]])
    def test_031_arrival_preserves_global_tm(self):
        self.assertIn("FIXTURE_TM",[v["id"] for v in self.travel()["fixture"]["bag"]])
    def test_032_arrival_preserves_consumable(self):
        self.assertIn("FIXTURE_REPEL",[v["id"] for v in self.travel()["fixture"]["bag"]])
    def test_033_arrival_preserves_mega_stone(self):
        self.assertIn("FIXTURE_STONE",[v["id"] for v in self.travel()["fixture"]["bag"]])
    def test_034_arrival_preserves_global_pc_tm(self):
        self.assertIn("FIXTURE_PC_TM",[v["id"] for v in self.travel()["fixture"]["pc"]])
    def test_035_arrival_stores_kanto_bag_in_vault(self):
        self.assertEqual({v["id"] for v in self.travel()["fixture"]["vault"]["KANTO"]["items"]},
                         {"FIXTURE_KANTO_HM","FIXTURE_KEY_KANTO"})
    def test_036_arrival_stores_kanto_pc_in_vault(self):
        self.assertEqual(self.travel()["fixture"]["vault"]["KANTO"]["pc_items"][0]["id"],
                         "FIXTURE_KANTO_PC_KEY")
    def test_037_arrival_retains_global_shortcut(self):
        self.assertIn("FIXTURE_TM",self.travel()["fixture"]["registered"])
    def test_038_arrival_removes_foreign_hm_shortcut(self):
        self.assertNotIn("FIXTURE_KANTO_HM",self.travel()["fixture"]["registered"])
    def test_039_arrival_restores_unova_shortcut(self):
        self.assertIn("FIXTURE_UNOVA_HM",self.travel()["fixture"]["registered"])
    def test_040_return_to_kanto_restores_local_hm(self):
        returned=self.travel(self.travel()["fixture"],"KANTO")
        self.assertIn("FIXTURE_KANTO_HM",[v["id"] for v in returned["fixture"]["bag"]])
    def test_041_return_to_kanto_restores_key_item(self):
        returned=self.travel(self.travel()["fixture"],"KANTO")
        self.assertIn("FIXTURE_KEY_KANTO",[v["id"] for v in returned["fixture"]["bag"]])
    def test_042_return_removes_unova_hm(self):
        returned=self.travel(self.travel()["fixture"],"KANTO")
        self.assertNotIn("FIXTURE_UNOVA_HM",[v["id"] for v in returned["fixture"]["bag"]])
    def test_043_return_stores_unova_hm(self):
        returned=self.travel(self.travel()["fixture"],"KANTO")
        self.assertIn("FIXTURE_UNOVA_HM",[v["id"] for v in returned["fixture"]["vault"]["UNOVA"]["items"]])
    def test_044_return_restores_kanto_item_pc(self):
        returned=self.travel(self.travel()["fixture"],"KANTO")
        self.assertIn("FIXTURE_KANTO_PC_KEY",[v["id"] for v in returned["fixture"]["pc"]])
    def test_045_return_pc_stores_unova_item(self):
        returned=self.travel(self.travel()["fixture"],"KANTO")
        self.assertIn("FIXTURE_UNOVA_PC_KEY",[v["id"] for v in returned["fixture"]["vault"]["UNOVA"]["pc_items"]])
    def test_046_travel_does_not_mutate_input(self):
        state=self.state()
        before=copy.deepcopy(state)
        self.travel(state)
        self.assertEqual(state,before)
    def test_047_travel_does_not_modify_native_save(self):
        self.assertFalse(self.travel()["native_save_modified"])
    def test_048_travel_does_not_unlock_field_use(self):
        self.assertFalse(self.travel()["field_use_unlocked"])
    def test_049_stale_hm_shortcut_not_persisted(self):
        state=self.state()
        state["registered"].append("FIXTURE_MISSING_HM")
        out=self.travel(state)["fixture"]
        self.assertNotIn("FIXTURE_MISSING_HM",out["vault"]["KANTO"]["registered"])
    def test_050_current_local_registration_persisted(self):
        self.assertEqual(self.travel()["fixture"]["vault"]["KANTO"]["registered"],["FIXTURE_KANTO_HM"])
    def test_051_no_prior_destination_vault_is_empty(self):
        state=self.state()
        state["vault"]={}
        out=self.travel(state)["fixture"]
        self.assertEqual([v for v in out["bag"] if v["kind"]=="HM"],[])
    def test_052_no_previous_destination_vault_does_not_grant_hm(self):
        state=self.state()
        state["vault"]={}
        out=self.travel(state)["fixture"]
        self.assertEqual(out["current"],"UNOVA")
    def test_053_missing_local_field_event_blocked(self):
        self.assertEqual(self.field()["status"],"MISSING_LOCAL_EVENT")
    def test_054_local_event_without_hm_blocked(self):
        self.assertEqual(self.field(local_event=True,hm_item_id=None)["status"],"MISSING_LOCAL_HM")
    def test_055_foreign_hm_not_eligible_for_unova(self):
        self.assertEqual(self.field(local_event=True,hm_item_id="FIXTURE_KANTO_HM")["status"],"MISSING_LOCAL_HM")
    def test_056_synthetic_local_event_and_hm_not_native_approval(self):
        result=self.field(local_event=True)
        self.assertEqual(result["status"],"SIMULATED_GATES_PASS_NOT_NATIVE_AUTHORIZED")
        self.assertFalse(result["runtime_authorized"])
    def test_057_no_native_event_id_generated(self):
        self.assertIsNone(self.field(local_event=True)["native_event_id"])
    def test_058_not_in_unova_field_access_blocked(self):
        with self.assertRaises(ValueError):
            self.field(state=self.state(),local_event=True)
    def test_059_wrong_action_blocked(self):
        with self.assertRaises(ValueError):
            self.field(action="ROCK_SMASH",local_event=True)
    def test_060_non_bool_event_blocked(self):
        with self.assertRaises(ValueError):
            self.field(local_event=1)
    def test_061_native_hm_id_not_allowed(self):
        with self.assertRaises(ValueError):
            self.field(local_event=True,hm_item_id="HM03")
    def test_062_foreign_hm_pretending_local_not_allowed(self):
        state=self.travel()["fixture"]
        self.assertEqual(self.field(state=state,local_event=True,
             hm_item_id="FIXTURE_KEY_KANTO")["status"],"MISSING_LOCAL_HM")
    def test_063_not_hm_kind_ignored(self):
        state=self.travel()["fixture"]
        self.assertEqual(self.field(state=state,local_event=True,
             hm_item_id="FIXTURE_TM")["status"],"MISSING_LOCAL_HM")
    def test_064_same_region_travel_blocked(self):
        self.bad_travel(destination="KANTO")
    def test_065_unknown_destination_blocked(self):
        self.bad_travel(destination="UNKNOWN")
    def test_066_unova_is_not_native_installed(self):
        self.assertTrue(self.travel()["status"].startswith("PLANNED_FIXTURE"))
    def test_067_native_scope_blocked(self):
        state=self.state();state["scope"]="REAL_GAME_SAVE"
        self.bad_travel(state)
    def test_068_native_input_source_blocked(self):
        self.bad_travel(input_source="NATIVE_PBS")
    def test_069_real_item_id_blocked(self):
        state=self.state();state["bag"][0]["id"]="HM01"
        self.bad_travel(state)
    def test_070_unknown_item_kind_blocked(self):
        state=self.state();state["bag"][0]["kind"]="UNVERIFIED"
        self.bad_travel(state)
    def test_071_boolean_item_quantity_blocked(self):
        state=self.state();state["bag"][0]["qty"]=True
        self.bad_travel(state)
    def test_072_zero_item_quantity_blocked(self):
        state=self.state();state["bag"][0]["qty"]=0
        self.bad_travel(state)
    def test_073_negative_item_quantity_blocked(self):
        state=self.state();state["bag"][0]["qty"]=-1
        self.bad_travel(state)
    def test_074_duplicate_item_id_in_bag_blocked(self):
        state=self.state();state["bag"].append(copy.deepcopy(state["bag"][0]))
        self.bad_travel(state)
    def test_075_duplicate_item_id_in_pc_blocked(self):
        state=self.state();state["pc"].append(copy.deepcopy(state["pc"][0]))
        self.bad_travel(state)
    def test_076_unknown_vault_region_blocked(self):
        state=self.state();state["vault"]["MISSING"]=state["vault"]["UNOVA"]
        self.bad_travel(state)
    def test_077_illegal_global_item_in_vault_blocked(self):
        state=self.state();state["vault"]["UNOVA"]["items"].append(self.item("NEW_TM","TM"))
        self.bad_travel(state)
    def test_078_missing_item_for_vault_shortcut_blocked(self):
        state=self.state();state["vault"]["UNOVA"]["registered"].append("FIXTURE_MISSING")
        self.bad_travel(state)
    def test_079_duplicate_saved_shortcut_blocked(self):
        state=self.state();state["vault"]["UNOVA"]["registered"].append("FIXTURE_UNOVA_HM")
        self.bad_travel(state)
    def test_080_duplicate_active_shortcut_blocked(self):
        state=self.state();state["registered"].append("FIXTURE_KANTO_HM")
        self.bad_travel(state)
    def test_081_full_bag_prevents_travel_no_commit(self):
        state=self.state();before=copy.deepcopy(state)
        state["bag_capacity"]=5
        state["vault"]["UNOVA"]["items"].extend([
            self.item("UNOVA_OTHER_HM"),self.item("UNOVA_MAP","KEY_ITEM"),
            self.item("UNOVA_PASS","KEY_ITEM")])
        before=copy.deepcopy(state)
        self.bad_travel(state)
        self.assertEqual(state,before)
    def test_082_full_pc_prevents_travel_no_commit(self):
        state=self.state();state["pc_capacity"]=2
        state["vault"]["UNOVA"]["pc_items"].extend([
            self.item("UNOVA_PC_KEY_B","KEY_ITEM"),
            self.item("UNOVA_PC_KEY_C","KEY_ITEM")])
        before=copy.deepcopy(state)
        self.bad_travel(state)
        self.assertEqual(state,before)
    def test_083_invalid_bag_capacity_refused(self):
        state=self.state();state["bag_capacity"]=-1
        self.bad_travel(state)
    def test_084_badge_native_identifier_refused(self):
        state=self.state();state["badges"]=["KANTO:BOULDER"]
        self.bad_travel(state)
    def test_085_untrusted_vault_duplicate_item_blocked(self):
        state=self.state();state["vault"]["UNOVA"]["items"].append(self.item("UNOVA_HM"))
        self.bad_travel(state)
    def test_086_untrusted_vault_quantity_zero_blocked(self):
        state=self.state();state["vault"]["UNOVA"]["pc_items"][0]["qty"]=0
        self.bad_travel(state)
    def test_087_forged_native_hm_id_in_contract_blocked(self):
        self.altered_catalog(lambda d:d["unova_field_rules"][0].update(native_hm_id="HM01"))
    def test_088_forged_native_pickup_event_blocked(self):
        self.altered_catalog(lambda d:d["native_evidence"].update(unova_hm_pickup_events=[42]))
    def test_089_injected_can_install_blocked(self):
        self.altered_catalog(lambda d:d.update(can_install=True))
    def test_090_contract_global_tm_rule_drift_blocked(self):
        self.altered_catalog(lambda d:d["classification"].update(global_=["TM"]))
    def test_091_contract_bag_pc_policy_drift_blocked(self):
        self.altered_catalog(lambda d:d["regional_vault_policy"].update(no_foreign_hm_or_key_item=False))
    def test_092_contract_extra_field_blocked(self):
        self.altered_catalog(lambda d:d.update(native_items_granted=True))
    def test_093_registry_field_rule_drift_blocked(self):
        changed=copy.deepcopy(self.registry)
        changed["regions"]["UNOVA"]["field"]["CUT"]["event"]="FAKE"
        with self.assertRaises(ValueError):
            mod.validate_catalog(self.data,changed,self.state_doc,self.sinnoh,
                                 self.tracker,self.travel_rb,self.field_rb,self.regions_rb)
    def test_094_native_runtime_drift_blocked(self):
        with self.assertRaises(ValueError):
            mod.validate_runtime(self.travel_rb.replace("data.is_key_item? || data.is_HM?",
                "data.is_key_item?"),self.field_rb,self.regions_rb)
    def test_095_fixture_demo_round_trip(self):
        result=mod.demo(self.data,self.registry)
        self.assertTrue(result["returned_kanto_hm"])
        self.assertTrue(result["unova_hm_preserved_in_vault"])
    def test_096_fixture_demo_field_gate(self):
        result=mod.demo(self.data,self.registry)
        self.assertEqual(result["local_event_denied"],"MISSING_LOCAL_EVENT")
        self.assertEqual(result["simulated_gate"],"SIMULATED_GATES_PASS_NOT_NATIVE_AUTHORIZED")
    def test_097_cli_check(self):
        ret=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g05_regional_items.py"),
                       "--check"],capture_output=True,text=True)
        self.assertEqual(ret.returncode,0,ret.stdout+ret.stderr)
        self.assertEqual(json.loads(ret.stdout)["unova_field_actions"],6)
    def test_098_cli_demo(self):
        ret=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g05_regional_items.py"),
                       "--simulate-demo"],capture_output=True,text=True)
        self.assertEqual(ret.returncode,0,ret.stdout+ret.stderr)
        self.assertFalse(json.loads(ret.stdout)["native_saves_modified"])

if __name__ == "__main__":
    unittest.main()
