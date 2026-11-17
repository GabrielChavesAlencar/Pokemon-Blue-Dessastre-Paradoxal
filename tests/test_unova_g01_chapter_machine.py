"""G01.2 isolated chapter machine positive/negative tests; no Game.exe or native saves."""
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
import audit_unova_g01_chapter_machine as machine

class G012ChapterMachineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract,cls.rules=machine.load_project()
        cls.events=machine._safe_source(ROOT/cls.rules["source_u07_events"])

    def fresh(self):return g01.empty_state(self.contract)
    def op(self,state,action,**kwargs):
        return machine.step(state,self.contract,self.rules,action,**kwargs)["state"]
    def begin(self):return self.op(self.fresh(),"begin")
    def u07(self,state,n=13):
        current=state
        for ev in self.rules["u07_order"][:n]:
            kwargs={"event_key":ev["key"]}
            if ev["kind"]=="choice":kwargs["starter_choice"]="SNIVY"
            if ev["battle_policy"] in ("ADVANCE_ON_LOSS","WIN_REQUIRED"):
                kwargs["outcome"]="WIN"
            current=self.op(current,"record_u07",**kwargs)
        return current
    def complete(self,state):
        return self.op(state,"complete",simulation_gate=machine.SIMULATION_GATE)
    def chapter(self,number):
        state=self.begin()
        state=self.u07(state)
        for n in range(1,number):
            state=self.complete(state)
            state=self.op(state,"advance")
        return state
    def rejects(self,state,action,**kwargs):
        before=copy.deepcopy(state)
        with self.assertRaises(ValueError):
            self.op(state,action,**kwargs)
        self.assertEqual(state,before)
    def invalid_rules(self,change):
        obj=copy.deepcopy(self.rules)
        change(obj)
        with self.assertRaises(ValueError):
            machine.validate_rules(obj,self.contract,self.events)

    def test_01_load_source_grounded_rules(self):
        c,r=machine.load_project()
        self.assertEqual(c["contract_version"],1)
        self.assertEqual((len(r["transitions"]),len(r["u07_order"])),(12,13))
        self.assertEqual(machine.validate_rules(r,c,self.events)["can_install"],False)
    def test_02_state_starts_at_chapter_zero(self):
        state=self.fresh()
        self.assertEqual(machine.validate_progression(state,self.contract,self.rules)["chapter_index"],0)
        self.assertEqual(machine.available(state,self.contract,self.rules)[0]["action"],"begin")
    def test_03_begin_creates_active_chapter_one_mission(self):
        s=self.begin()
        self.assertEqual(s["current_chapter"],"UNOVA_CH01_NUVEMA")
        self.assertEqual(s["missions"]["UNOVA_MISSION_CH01_BEGIN_JOURNEY"],"active")
        self.assertEqual(s["checkpoint"]["last_story_area_key"],"UNOVA_NUVEMA_TOWN")
        self.assertEqual(s["flags"],{})
    def test_04_begin_is_pure_without_mutating_caller(self):
        initial=self.fresh()
        s=self.op(initial,"begin")
        self.assertNotEqual(s,initial)
        self.assertEqual(initial,self.fresh())
    def test_05_begin_twice_is_blocked(self):
        self.rejects(self.begin(),"begin")
    def test_06_advance_before_begin_blocked(self):
        self.rejects(self.fresh(),"advance")
    def test_07_complete_before_begin_blocked(self):
        self.rejects(self.fresh(),"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_08_unregistered_action_blocked(self):
        self.rejects(self.fresh(),"install_native_map")
    def test_09_first_u07_event_requires_starter_choice(self):
        self.rejects(self.begin(),"record_u07",event_key=self.rules["u07_order"][0]["key"])
    def test_10_starter_choice_rejects_unregistered_pokemon(self):
        self.rejects(self.begin(),"record_u07",event_key=self.rules["u07_order"][0]["key"],starter_choice="MEW")
    def test_11_initial_starter_options_are_valid(self):
        for starter in ("SNIVY","TEPIG","OSHAWOTT"):
            state=self.op(self.begin(),"record_u07",event_key="UNOVA_U07_STARTER_GIFT",starter_choice=starter)
            self.assertTrue(state["flags"]["UNOVA_U07_STARTER_GIFT"])
    def test_12_starter_choice_no_battle_result(self):
        self.rejects(self.begin(),"record_u07",event_key="UNOVA_U07_STARTER_GIFT",starter_choice="SNIVY",outcome="WIN")
    def test_13_first_event_flags_are_synthetic(self):
        s=self.u07(self.begin(),1)
        self.assertEqual(s["flags"],{"UNOVA_U07_STARTER_GIFT":True})
        self.assertEqual(machine.available(s,self.contract,self.rules)[0]["event"],"UNOVA_U07_BIANCA_FIRST_BATTLE")
    def test_14_second_event_before_first_blocked(self):
        self.rejects(self.begin(),"record_u07",event_key="UNOVA_U07_BIANCA_FIRST_BATTLE",outcome="WIN")
    def test_15_battle_outcome_missing_blocked(self):
        self.rejects(self.u07(self.begin(),1),"record_u07",event_key="UNOVA_U07_BIANCA_FIRST_BATTLE")
    def test_16_bianca_loss_allowed_in_synthetic_mode(self):
        s=self.u07(self.begin(),1)
        s=self.op(s,"record_u07",event_key="UNOVA_U07_BIANCA_FIRST_BATTLE",outcome="LOSS")
        self.assertTrue(s["flags"]["UNOVA_U07_BIANCA_FIRST_BATTLE"])
    def test_17_cheren_loss_allowed_in_synthetic_mode(self):
        s=self.u07(self.begin(),2)
        s=self.op(s,"record_u07",event_key="UNOVA_U07_CHEREN_FIRST_BATTLE",outcome="LOSS")
        self.assertTrue(s["flags"]["UNOVA_U07_CHEREN_FIRST_BATTLE"])
    def test_18_n_battle_requires_win_in_synthetic_mode(self):
        s=self.u07(self.begin(),11)
        self.rejects(s,"record_u07",event_key="UNOVA_U07_N_FIRST_BATTLE",outcome="LOSS")
        good=self.op(s,"record_u07",event_key="UNOVA_U07_N_FIRST_BATTLE",outcome="WIN")
        self.assertTrue(good["flags"]["UNOVA_U07_N_FIRST_BATTLE"])
    def test_19_event_cannot_duplicate(self):
        self.rejects(self.u07(self.begin(),1),"record_u07",event_key="UNOVA_U07_STARTER_GIFT",starter_choice="SNIVY")
    def test_20_event_unknown_rejected(self):
        self.rejects(self.begin(),"record_u07",event_key="UNOVA_U07_UNKNOWN")
    def test_21_nonbattle_outcome_rejected(self):
        s=self.u07(self.begin(),3)
        self.rejects(s,"record_u07",event_key="UNOVA_U07_MOM_XTRANSCEIVER",outcome="WIN")
    def test_22_unexpected_starter_on_dialogue_rejected(self):
        s=self.u07(self.begin(),4)
        self.rejects(s,"record_u07",event_key="UNOVA_U07_VISIT_BIANCA_HOME",starter_choice="SNIVY")
    def test_23_partial_u07_events_cannot_complete_ch01(self):
        self.rejects(self.u07(self.begin(),12),"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_24_completion_requires_explicit_offline_marker(self):
        self.rejects(self.u07(self.begin()),"complete")
    def test_25_real_game_claim_cannot_act_as_gate(self):
        self.rejects(self.u07(self.begin()),"complete",simulation_gate="GAME_EXE_APPROVED")
    def test_26_full_u07_allows_complete_chapter_one(self):
        s=self.complete(self.u07(self.begin()))
        self.assertEqual(s["missions"]["UNOVA_MISSION_CH01_BEGIN_JOURNEY"],"completed")
        self.assertTrue(s["flags"]["UNOVA_FLAG_CH01_COMPLETED"])
        self.assertEqual(machine.available(s,self.contract,self.rules)[0]["target"],"UNOVA_CH02_STRIATON")
    def test_27_cannot_advance_before_chapter_completion(self):
        self.rejects(self.u07(self.begin()),"advance")
    def test_28_completed_ch01_can_advance_to_ch02(self):
        s=self.op(self.complete(self.u07(self.begin())),"advance")
        self.assertEqual(s["current_chapter"],"UNOVA_CH02_STRIATON")
        self.assertEqual(s["missions"]["UNOVA_MISSION_CH02_FIRST_GYM"],"active")
        self.assertEqual(s["checkpoint"]["last_story_area_key"],"UNOVA_STRIATON_CITY")
    def test_29_cannot_complete_chapter_twice(self):
        s=self.complete(self.u07(self.begin()))
        self.rejects(s,"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_30_no_double_advance_without_finishing_next_mission(self):
        s=self.chapter(2)
        self.rejects(s,"advance")
    def test_31_future_mission_injected_is_rejected(self):
        s=self.begin();s["missions"]["UNOVA_MISSION_CH02_FIRST_GYM"]="active"
        self.rejects(s,"advance")
    def test_32_future_chapter_flag_injected_is_rejected(self):
        s=self.begin();s["flags"]["UNOVA_FLAG_CH07_COMPLETED"]=True
        self.rejects(s,"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_33_prior_chapter_flag_cannot_be_deleted(self):
        s=self.chapter(3);s["flags"].pop("UNOVA_FLAG_CH01_COMPLETED")
        self.rejects(s,"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_34_prior_mission_cannot_be_downgraded(self):
        s=self.chapter(3);s["missions"]["UNOVA_MISSION_CH01_BEGIN_JOURNEY"]="active"
        self.rejects(s,"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_35_current_mission_must_be_active_or_completed(self):
        s=self.chapter(3);s["missions"]["UNOVA_MISSION_CH03_SECOND_GYM"]="blocked"
        self.rejects(s,"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_36_current_completion_and_flag_must_match(self):
        s=self.chapter(3);s["flags"]["UNOVA_FLAG_CH03_COMPLETED"]=True
        self.rejects(s,"advance")
    def test_37_false_flag_placeholder_rejected_in_reachable_machine_state(self):
        s=self.begin();s["flags"]["UNOVA_FLAG_CH01_COMPLETED"]=False
        self.rejects(s,"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_38_event_prefix_cannot_have_gap(self):
        s=self.begin();s["flags"]["UNOVA_U07_CHEREN_FIRST_BATTLE"]=True
        self.rejects(s,"record_u07",event_key="UNOVA_U07_STARTER_GIFT",starter_choice="SNIVY")
    def test_39_ch02_without_u07_flags_rejected(self):
        s=self.chapter(2);s["flags"].pop("UNOVA_U07_ROUTE2_PASSAGE")
        self.rejects(s,"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_40_checkpoint_cannot_jump_to_another_story_area(self):
        s=self.chapter(2);s["checkpoint"]["last_story_area_key"]="UNOVA_POKEMON_LEAGUE"
        self.rejects(s,"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_41_fake_numeric_mapid_rejected_by_g011(self):
        s=self.begin();s["checkpoint"]["map_id"]=518
        self.rejects(s,"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_42_different_region_state_rejected(self):
        s=self.begin();s["region"]="KANTO"
        self.rejects(s,"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_43_future_schema_rejected(self):
        s=self.begin();s["schema_version"]=2
        self.rejects(s,"complete",simulation_gate=machine.SIMULATION_GATE)
    def test_44_chapter2_explicit_simulated_completion(self):
        s=self.chapter(2)
        self.rejects(s,"complete",simulation_gate="NATIVE_GYM_WON")
        completed=self.complete(s)
        self.assertTrue(completed["flags"]["UNOVA_FLAG_CH02_COMPLETED"])
        self.assertEqual(completed["missions"]["UNOVA_MISSION_CH02_FIRST_GYM"],"completed")
    def test_45_advance_chain_reaches_chapter12_in_order(self):
        s=self.chapter(12)
        self.assertEqual(s["current_chapter"],"UNOVA_CH12_POSTGAME")
        self.assertEqual(s["missions"]["UNOVA_MISSION_CH12_POSTGAME"],"active")
        self.assertEqual(machine.validate_progression(s,self.contract,self.rules)["chapter_index"],12)
    def test_46_final_chapter_has_no_next_transition(self):
        s=self.complete(self.chapter(12))
        self.assertEqual(machine.available(s,self.contract,self.rules),[])
        self.rejects(s,"advance")
    def test_47_step_never_claims_rewards_or_native_save(self):
        res=machine.step(self.fresh(),self.contract,self.rules,"begin")
        self.assertFalse(res["reward_granted"])
        self.assertFalse(res["native_save_modified"])
        self.assertFalse(res["game_exe_tested"])
        self.assertFalse(res["can_install"])
    def test_48_rules_skip_chapter_rejected(self):
        self.invalid_rules(lambda r:r["transitions"][1].update(to="UNOVA_CH10_LEAGUE"))
    def test_49_rules_remove_required_previous_mission_rejected(self):
        self.invalid_rules(lambda r:r["transitions"][1].update(required_mission_key=None))
    def test_50_rules_remove_completion_flag_rejected(self):
        self.invalid_rules(lambda r:r["transitions"][2].update(required_completion_flag=None))
    def test_51_rules_remove_u07_precondition_rejected(self):
        self.invalid_rules(lambda r:r["transitions"][1].update(required_u07_flags=[]))
    def test_52_rules_change_n_battle_policy_rejected(self):
        self.invalid_rules(lambda r:r["u07_order"][11].update(battle_policy="ADVANCE_ON_LOSS"))
    def test_53_rules_fake_native_approval_rejected(self):
        self.invalid_rules(lambda r:r.update(game_exe_tested=True))
    def test_54_rules_fake_native_save_adapter_rejected(self):
        self.invalid_rules(lambda r:r.update(native_save_adapter=True))
    def test_55_rules_change_simulation_gate_rejected(self):
        self.invalid_rules(lambda r:r.update(simulation_gate="GAME_EXE"))
    def test_56_rules_reorder_events_rejected(self):
        self.invalid_rules(lambda r:r["u07_order"].reverse())
    def test_57_rules_duplicate_transition_rejected(self):
        self.invalid_rules(lambda r:r["transitions"].append(copy.deepcopy(r["transitions"][-1])))
    def test_58_full_demo_is_offline_not_gameplay(self):
        report=machine.demo(self.contract,self.rules)
        self.assertEqual(report["status"],"OFFLINE_DEMO_ONLY")
        self.assertEqual(report["final_chapter"],"UNOVA_CH12_POSTGAME")
        self.assertEqual(report["chapters_visited"],13)
        self.assertEqual(report["events_recorded"],13)
        self.assertFalse(report["rewards_granted"])
        self.assertFalse(report["native_save_modified"])
        self.assertFalse(report["can_install"])
    def test_59_cli_check_reports_no_install(self):
        r=subprocess.run([sys.executable,str(machine.ROOT/"scripts/regions/audit_unova_g01_chapter_machine.py"),"--check"],
            cwd=machine.ROOT,text=True,capture_output=True,timeout=25)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        obj=json.loads(r.stdout.strip())
        self.assertEqual(obj["transitions"],12)
        self.assertFalse(obj["can_install"])
    def test_60_cli_demo_reports_offline_only(self):
        r=subprocess.run([sys.executable,str(machine.ROOT/"scripts/regions/audit_unova_g01_chapter_machine.py"),"--simulate-demo"],
            cwd=machine.ROOT,text=True,capture_output=True,timeout=25)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        obj=json.loads(r.stdout.strip())
        self.assertEqual(obj["final_chapter"],"UNOVA_CH12_POSTGAME")
        self.assertFalse(obj["native_save_modified"])
        self.assertNotIn("final_state",obj)
    def test_61_reject_unexpected_event_argument_on_begin(self):
        self.rejects(self.fresh(),"begin",event_key="UNOVA_U07_STARTER_GIFT")
    def test_62_reject_unexpected_gate_on_advance(self):
        self.rejects(self.complete(self.u07(self.begin())),"advance",simulation_gate=machine.SIMULATION_GATE)
    def test_63_reject_unexpected_outcome_on_complete(self):
        self.rejects(self.u07(self.begin()),"complete",simulation_gate=machine.SIMULATION_GATE,outcome="WIN")
    def test_64_injected_starter_outside_event_blocked(self):
        self.rejects(self.fresh(),"begin",starter_choice="SNIVY")

if __name__=="__main__":
    unittest.main()
