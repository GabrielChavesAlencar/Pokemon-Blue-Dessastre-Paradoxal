"""G01.3 receipt ledger safety regression: offline rewards, no save files or Game.exe."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g01_chapter_machine as machine
import audit_unova_g01_reentry_ledger as ledger

class UnovaG013Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c,cls.rules,cls.policy,cls.events=ledger.load_project()

    def fresh(self):
        return ledger.initial(self.c)

    def apply(self,env,action,**kwargs):
        return ledger.apply(env,self.c,self.rules,self.policy,self.events,action,**kwargs)

    def begin(self):
        return self.apply(self.fresh(),"begin")["envelope"]

    @staticmethod
    def params(event):
        out={"event_key":event["key"]}
        if event["kind"]=="choice":
            out["starter_choice"]="SNIVY"
        if event["battle_policy"] in {"WIN_REQUIRED","ADVANCE_ON_LOSS"}:
            out["outcome"]="WIN"
        return out

    def prefix(self,num):
        env=self.begin()
        for event in self.events[:num]:
            env=self.apply(env,"record_u07",**self.params(event))["envelope"]
        return env

    def finish_first(self):
        env=self.prefix(13)
        return self.apply(env,"complete",chapter_key=self.c["chapters"][1]["key"],
                          simulation_gate=machine.SIMULATION_GATE)["envelope"]

    def chapter(self,num):
        env=self.finish_first()
        for idx in range(1,num):
            env=self.apply(env,"advance",chapter_key=self.c["chapters"][idx]["key"])["envelope"]
            if idx+1<num:
                env=self.apply(env,"complete",chapter_key=self.c["chapters"][idx+1]["key"],
                               simulation_gate=machine.SIMULATION_GATE)["envelope"]
        return env

    def deny(self,env,action,**kwargs):
        before=copy.deepcopy(env)
        with self.assertRaises(ValueError):
            self.apply(env,action,**kwargs)
        self.assertEqual(env,before)

    def reject_env(self,env):
        with self.assertRaises(ValueError):
            ledger.validate_envelope(env,self.c,self.rules,self.policy,self.events)

    def reject_policy(self,edit):
        changed=copy.deepcopy(self.policy)
        edit(changed)
        with self.assertRaises(ValueError):
            ledger.validate_policy(changed,self.c,self.rules,self.events)

    def test_01_contract_is_strict_offline(self):
        p=ledger.validate_policy(self.policy,self.c,self.rules,self.events)
        self.assertEqual(p["u07_events"],13)
        self.assertEqual(p["unique_reward_intent_tokens"],5)
        self.assertFalse(p["native_items_granted"])
        self.assertFalse(p["can_install"])

    def test_02_initial_no_progress(self):
        env=self.fresh()
        self.assertEqual(env["event_receipts"],[])
        self.assertEqual(env["reward_intents"],{})
        self.assertEqual(ledger.validate_envelope(env,self.c,self.rules,self.policy,self.events)["events_recorded"],0)

    def test_03_begin_is_pure_and_offline(self):
        env=self.fresh()
        ret=self.apply(env,"begin")
        self.assertEqual(ret["status"],ledger.STATUS_APPLIED)
        self.assertEqual(env,self.fresh())
        self.assertEqual(ret["new_reward_intents"],[])
        self.assertFalse(ret["native_save_modified"])

    def test_04_begin_duplicate_noop(self):
        env=self.begin()
        ret=self.apply(env,"begin")
        self.assertEqual(ret["status"],ledger.STATUS_ALREADY)
        self.assertEqual(ret["envelope"],env)

    def test_05_first_u07_starter_has_no_inventory_reward(self):
        r=self.apply(self.begin(),"record_u07",event_key=self.events[0]["key"],
                     starter_choice="SNIVY")
        self.assertEqual(r["new_reward_intents"],[])
        self.assertEqual(r["envelope"]["reward_intents"],{})
        self.assertFalse(r["actual_items_granted"])

    def test_06_every_u07_flag_has_exactly_one_receipt(self):
        env=self.prefix(13)
        self.assertEqual(len(env["event_receipts"]),13)
        self.assertEqual([r["event_key"] for r in env["event_receipts"]],
                         [x["key"] for x in self.events])
        self.assertEqual(ledger.validate_envelope(env,self.c,self.rules,self.policy,self.events)["events_recorded"],13)

    def test_07_poke_ball_amount_is_five_not_one(self):
        env=self.prefix(13)
        self.assertEqual(env["reward_intents"]["ITEM:POKE_BALL"],5)

    def test_08_real_source_key_items_exact(self):
        env=self.prefix(13)
        self.assertEqual(env["reward_intents"],{
            "KEY_ITEM:XTRANSCEIVER":1,"KEY_ITEM:POKEDEX":1,
            "KEY_ITEM:TOWN_MAP":1,"ITEM:POKE_BALL":5,
            "STORY_TOKEN:ROUTE_2_PASSAGE_READY":1
        })

    def test_09_reward_receipt_has_not_granted_status(self):
        env=self.prefix(13)
        self.assertTrue(all(x["receipt_status"]==ledger.RECEIPT_STATUS for x in env["event_receipts"]))

    def test_10_first_reward_intent_matches_U07_provenance(self):
        env=self.prefix(3)
        out=self.apply(env,"record_u07",event_key="UNOVA_U07_MOM_XTRANSCEIVER")
        self.assertEqual(out["new_reward_intents"],[{
            "kind":"REWARD_INTENT_NOT_GRANTED_IN_GAME",
            "category":"KEY_ITEM","token":"XTRANSCEIVER","amount":1,
            "source_event":"UNOVA_U07_MOM_XTRANSCEIVER"}])

    def test_11_duplicate_event_same_input_is_noop(self):
        env=self.prefix(5)
        out=self.apply(env,"record_u07",event_key=self.events[4]["key"])
        self.assertEqual(out["status"],ledger.STATUS_ALREADY)
        self.assertEqual(out["envelope"],env)
        self.assertEqual(out["new_reward_intents"],[])

    def test_12_duplicate_grant_has_no_reward_effect(self):
        env=self.prefix(4)
        out=self.apply(env,"record_u07",event_key=self.events[3]["key"])
        self.assertEqual(out["status"],ledger.STATUS_ALREADY)
        self.assertEqual(out["new_reward_intents"],[])
        self.assertEqual(out["envelope"]["reward_intents"]["KEY_ITEM:XTRANSCEIVER"],1)

    def test_13_duplicate_poke_ball_grant_not_ten(self):
        env=self.prefix(9)
        out=self.apply(env,"record_u07",event_key=self.events[8]["key"])
        self.assertEqual(out["new_reward_intents"],[])
        self.assertEqual(out["envelope"]["reward_intents"]["ITEM:POKE_BALL"],5)

    def test_14_duplicate_starter_same_choice_noop(self):
        env=self.prefix(1)
        out=self.apply(env,"record_u07",event_key=self.events[0]["key"],
                       starter_choice="SNIVY")
        self.assertEqual(out["status"],ledger.STATUS_ALREADY)

    def test_15_duplicate_starter_changed_choice_rejected(self):
        self.deny(self.prefix(1),"record_u07",event_key=self.events[0]["key"],
                  starter_choice="TEPIG")

    def test_16_duplicate_starter_missing_choice_rejected(self):
        self.deny(self.prefix(1),"record_u07",event_key=self.events[0]["key"])

    def test_17_first_bianca_battle_loss_records_receipt(self):
        env=self.prefix(1)
        out=self.apply(env,"record_u07",event_key=self.events[1]["key"],outcome="LOSS")
        self.assertEqual(out["status"],ledger.STATUS_APPLIED)
        self.assertEqual(out["envelope"]["event_receipts"][-1]["outcome"],"LOSS")

    def test_18_duplicate_bianca_loss_noop(self):
        env=self.prefix(1)
        env=self.apply(env,"record_u07",event_key=self.events[1]["key"],outcome="LOSS")["envelope"]
        out=self.apply(env,"record_u07",event_key=self.events[1]["key"],outcome="LOSS")
        self.assertEqual(out["status"],ledger.STATUS_ALREADY)

    def test_19_bianca_loss_cannot_be_rewritten_as_win(self):
        env=self.prefix(1)
        env=self.apply(env,"record_u07",event_key=self.events[1]["key"],outcome="LOSS")["envelope"]
        self.deny(env,"record_u07",event_key=self.events[1]["key"],outcome="WIN")

    def test_20_cheren_loss_progresses(self):
        env=self.prefix(2)
        out=self.apply(env,"record_u07",event_key=self.events[2]["key"],outcome="LOSS")
        self.assertEqual(out["status"],ledger.STATUS_APPLIED)
        self.assertTrue(out["envelope"]["state"]["flags"][self.events[2]["key"]])

    def test_21_early_rival_loss_replay_conflicting_result(self):
        env=self.prefix(2)
        env=self.apply(env,"record_u07",event_key=self.events[2]["key"],outcome="LOSS")["envelope"]
        self.deny(env,"record_u07",event_key=self.events[2]["key"],outcome="WIN")

    def test_22_N_loss_causes_no_progress_or_receipt(self):
        env=self.prefix(11)
        result=self.apply(env,"record_u07",event_key=self.events[11]["key"],outcome="LOSS")
        self.assertEqual(result["status"],ledger.STATUS_RETRY)
        self.assertEqual(result["envelope"],env)
        self.assertEqual(result["new_reward_intents"],[])

    def test_23_N_can_lose_more_than_once_without_side_effects(self):
        env=self.prefix(11)
        for _ in range(3):
            result=self.apply(env,"record_u07",event_key=self.events[11]["key"],outcome="LOSS")
            self.assertEqual(result["envelope"],env)
            self.assertEqual(result["status"],ledger.STATUS_RETRY)

    def test_24_N_win_after_loss_is_unique(self):
        env=self.prefix(11)
        loss=self.apply(env,"record_u07",event_key=self.events[11]["key"],outcome="LOSS")
        win=self.apply(loss["envelope"],"record_u07",event_key=self.events[11]["key"],outcome="WIN")
        self.assertEqual(win["status"],ledger.STATUS_APPLIED)
        self.assertEqual(len(win["envelope"]["event_receipts"]),12)
        self.assertEqual(win["envelope"]["event_receipts"][-1]["outcome"],"WIN")

    def test_25_N_loss_after_win_denied(self):
        env=self.prefix(12)
        self.deny(env,"record_u07",event_key=self.events[11]["key"],outcome="LOSS")

    def test_26_N_win_replay_noop(self):
        env=self.prefix(12)
        self.assertEqual(self.apply(env,"record_u07",event_key=self.events[11]["key"],
                                    outcome="WIN")["status"],ledger.STATUS_ALREADY)

    def test_27_skip_event_denied(self):
        self.deny(self.begin(),"record_u07",event_key=self.events[3]["key"])

    def test_28_unknown_event_denied(self):
        self.deny(self.begin(),"record_u07",event_key="UNOVA_U07_FAKE")

    def test_29_missing_starter_denied(self):
        self.deny(self.begin(),"record_u07",event_key=self.events[0]["key"])

    def test_30_starter_cannot_be_legendary(self):
        self.deny(self.begin(),"record_u07",event_key=self.events[0]["key"],
                  starter_choice="MEWTWO")

    def test_31_nonbattle_outcome_denied(self):
        self.deny(self.prefix(3),"record_u07",event_key=self.events[3]["key"],
                  outcome="WIN")

    def test_32_event_not_allowed_before_begin(self):
        self.deny(self.fresh(),"record_u07",event_key=self.events[0]["key"],
                  starter_choice="SNIVY")

    def test_33_event_new_after_leaving_ch01_denied(self):
        env=self.chapter(2)
        self.deny(env,"record_u07",event_key=self.events[0]["key"],
                  starter_choice="TEPIG")

    def test_34_matching_event_replay_after_leaving_ch01_noop(self):
        env=self.chapter(2)
        out=self.apply(env,"record_u07",event_key=self.events[3]["key"])
        self.assertEqual(out["status"],ledger.STATUS_ALREADY)
        self.assertEqual(out["envelope"],env)

    def test_35_complete_ch01_require_offline_gate(self):
        env=self.prefix(13)
        self.deny(env,"complete",chapter_key=self.c["chapters"][1]["key"])

    def test_36_complete_ch01_premature_blocked(self):
        env=self.prefix(12)
        self.deny(env,"complete",chapter_key=self.c["chapters"][1]["key"],
                  simulation_gate=machine.SIMULATION_GATE)

    def test_37_complete_ch01_no_item_grants(self):
        env=self.prefix(13)
        result=self.apply(env,"complete",chapter_key=self.c["chapters"][1]["key"],
                          simulation_gate=machine.SIMULATION_GATE)
        self.assertEqual(result["new_reward_intents"],[])
        self.assertEqual(result["envelope"]["reward_intents"],env["reward_intents"])

    def test_38_complete_ch01_replay_noop(self):
        env=self.finish_first()
        out=self.apply(env,"complete",chapter_key=self.c["chapters"][1]["key"],
                       simulation_gate=machine.SIMULATION_GATE)
        self.assertEqual(out["status"],ledger.STATUS_ALREADY)
        self.assertEqual(out["envelope"],env)

    def test_39_complete_past_chapter_noop(self):
        env=self.chapter(3)
        out=self.apply(env,"complete",chapter_key=self.c["chapters"][1]["key"],
                       simulation_gate=machine.SIMULATION_GATE)
        self.assertEqual(out["status"],ledger.STATUS_ALREADY)

    def test_40_complete_past_chapter_wrong_gate_rejected(self):
        env=self.chapter(3)
        self.deny(env,"complete",chapter_key=self.c["chapters"][1]["key"],
                  simulation_gate="REAL_GYM_APPROVED")

    def test_41_advance_ch01_exactly_once(self):
        env=self.finish_first()
        result=self.apply(env,"advance",chapter_key=self.c["chapters"][1]["key"])
        self.assertEqual(result["status"],ledger.STATUS_APPLIED)
        self.assertEqual(result["envelope"]["state"]["current_chapter"],"UNOVA_CH02_STRIATON")

    def test_42_replay_advance_ch01_noop(self):
        env=self.chapter(2)
        result=self.apply(env,"advance",chapter_key=self.c["chapters"][1]["key"])
        self.assertEqual(result["status"],ledger.STATUS_ALREADY)
        self.assertEqual(result["envelope"],env)

    def test_43_replay_advance_ch01_from_ch03_noop(self):
        env=self.chapter(3)
        result=self.apply(env,"advance",chapter_key=self.c["chapters"][1]["key"])
        self.assertEqual(result["status"],ledger.STATUS_ALREADY)
        self.assertEqual(result["envelope"],env)

    def test_44_advance_before_completion_rejected(self):
        self.deny(self.prefix(13),"advance",chapter_key=self.c["chapters"][1]["key"])

    def test_45_skip_chapter_with_advance_rejected(self):
        env=self.chapter(2)
        self.deny(env,"advance",chapter_key=self.c["chapters"][3]["key"])

    def test_46_future_complete_rejected(self):
        env=self.chapter(2)
        self.deny(env,"complete",chapter_key=self.c["chapters"][8]["key"],
                  simulation_gate=machine.SIMULATION_GATE)

    def test_47_reenter_ch01_from_ch02_readonly(self):
        env=self.chapter(2)
        result=self.apply(env,"reenter",chapter_key=self.c["chapters"][1]["key"])
        self.assertEqual(result["status"],ledger.STATUS_REENTER)
        self.assertEqual(result["envelope"],env)
        self.assertEqual(result["envelope"]["state"]["current_chapter"],"UNOVA_CH02_STRIATON")

    def test_48_reenter_current_chapter_readonly(self):
        env=self.chapter(2)
        self.assertEqual(self.apply(env,"reenter",
            chapter_key=self.c["chapters"][2]["key"])["status"],ledger.STATUS_REENTER)

    def test_49_reenter_ch01_from_ch12_preserves_checkpoint(self):
        env=self.chapter(12)
        before=copy.deepcopy(env["state"]["checkpoint"])
        result=self.apply(env,"reenter",chapter_key=self.c["chapters"][1]["key"])
        self.assertEqual(result["envelope"]["state"]["checkpoint"],before)
        self.assertEqual(result["envelope"]["reward_intents"],env["reward_intents"])

    def test_50_cannot_reenter_future_chapter(self):
        self.deny(self.chapter(2),"reenter",chapter_key=self.c["chapters"][10]["key"])

    def test_51_cannot_reenter_prestart_after_begin(self):
        self.deny(self.begin(),"reenter",chapter_key=self.c["chapters"][0]["key"])

    def test_52_can_reenter_prestart_before_begin(self):
        env=self.fresh()
        self.assertEqual(self.apply(env,"reenter",
            chapter_key=self.c["chapters"][0]["key"])["status"],ledger.STATUS_REENTER)

    def test_53_receipt_missing_rejected(self):
        env=self.prefix(4)
        env["event_receipts"].pop()
        self.reject_env(env)

    def test_54_duplicate_receipt_rejected(self):
        env=self.prefix(4)
        env["event_receipts"].append(copy.deepcopy(env["event_receipts"][-1]))
        self.reject_env(env)

    def test_55_wrong_receipt_order_rejected(self):
        env=self.prefix(5)
        env["event_receipts"][0],env["event_receipts"][1]=env["event_receipts"][1],env["event_receipts"][0]
        self.reject_env(env)

    def test_56_receipt_reward_quantity_forged_rejected(self):
        env=self.prefix(4)
        env["event_receipts"][-1]["reward_intents"][0]["amount"]=200
        self.reject_env(env)

    def test_57_receipt_reward_category_forged_rejected(self):
        env=self.prefix(4)
        env["event_receipts"][-1]["reward_intents"][0]["category"]="POKEMON"
        self.reject_env(env)

    def test_58_receipt_starter_forged_rejected(self):
        env=self.prefix(1)
        env["event_receipts"][0]["starter_choice"]="MEW"
        self.reject_env(env)

    def test_59_receipt_battle_outcome_forged_rejected(self):
        env=self.prefix(12)
        env["event_receipts"][11]["outcome"]="LOSS"
        self.reject_env(env)

    def test_60_receipt_status_must_not_claim_grant(self):
        env=self.prefix(4)
        env["event_receipts"][-1]["receipt_status"]="ITEM_GRANTED_IN_GAME"
        self.reject_env(env)

    def test_61_reward_ledger_extra_token_rejected(self):
        env=self.prefix(4);env["reward_intents"]["KEY_ITEM:RARE_CANDY"]=999
        self.reject_env(env)

    def test_62_reward_ledger_wrong_amount_rejected(self):
        env=self.prefix(9);env["reward_intents"]["ITEM:POKE_BALL"]=10
        self.reject_env(env)

    def test_63_reward_ledger_missing_token_rejected(self):
        env=self.prefix(4);env["reward_intents"].pop("KEY_ITEM:XTRANSCEIVER")
        self.reject_env(env)

    def test_64_reward_ledger_boolean_amount_rejected(self):
        env=self.prefix(4);env["reward_intents"]["KEY_ITEM:XTRANSCEIVER"]=True
        self.reject_env(env)

    def test_65_orphan_flag_without_receipt_rejected(self):
        env=self.prefix(4);env["state"]["flags"]["UNOVA_U07_VISIT_BIANCA_HOME"]=True
        self.reject_env(env)

    def test_66_orphan_receipt_without_flag_rejected(self):
        env=self.prefix(4);env["state"]["flags"].pop("UNOVA_U07_MOM_XTRANSCEIVER")
        self.reject_env(env)

    def test_67_envelope_other_region_rejected(self):
        env=self.fresh();env["region"]="KANTO"
        self.reject_env(env)

    def test_68_envelope_future_version_rejected(self):
        env=self.fresh();env["schema"]=2
        self.reject_env(env)

    def test_69_envelope_boolean_version_rejected(self):
        env=self.fresh();env["schema"]=True
        self.reject_env(env)

    def test_70_envelope_fake_native_save_field_rejected(self):
        env=self.fresh();env["GameSave"]={"id":42}
        self.reject_env(env)

    def test_71_envelope_replay_scope_forged_rejected(self):
        env=self.fresh();env["scope"]="NATIVE_GAME_SAVE"
        self.reject_env(env)

    def test_72_g011_future_state_schema_rejected(self):
        env=self.begin();env["state"]["schema_version"]=3
        self.reject_env(env)

    def test_73_g012_future_chapter_flag_rejected(self):
        env=self.begin();env["state"]["flags"]["UNOVA_FLAG_CH10_COMPLETED"]=True
        self.reject_env(env)

    def test_74_malformed_receipts_list_rejected(self):
        env=self.fresh();env["event_receipts"]={"receipt":"fake"}
        self.reject_env(env)

    def test_75_malformed_intent_map_rejected(self):
        env=self.fresh();env["reward_intents"]=None
        self.reject_env(env)

    def test_76_source_policy_fake_amount_rejected(self):
        self.reject_policy(lambda p:p["events"][8]["grants_once"][0].update(amount=500))

    def test_77_source_policy_fake_new_reward_rejected(self):
        self.reject_policy(lambda p:p["reward_keys"].append("KEY_ITEM:MASTER_BALL"))

    def test_78_source_policy_reordered_events_rejected(self):
        self.reject_policy(lambda p:p["events"].reverse())

    def test_79_policy_claim_actual_items_granted_rejected(self):
        self.reject_policy(lambda p:p.update(actual_items_granted=True))

    def test_80_policy_claim_can_install_rejected(self):
        self.reject_policy(lambda p:p.update(can_install=True))

    def test_81_policy_disable_conflicting_replay_rejected(self):
        self.reject_policy(lambda p:p.update(conflicting_replay="ALLOW"))

    def test_82_policy_change_version_rejected(self):
        self.reject_policy(lambda p:p.update(ledger_schema_version=2))

    def test_83_policy_enable_native_save_adapter_rejected(self):
        self.reject_policy(lambda p:p.update(release_native_claims=True))

    def test_84_invalid_action_rejected(self):
        self.deny(self.fresh(),"grant_master_ball")

    def test_85_unexpected_chapter_arg_for_event_rejected(self):
        self.deny(self.begin(),"record_u07",event_key=self.events[0]["key"],
                  starter_choice="SNIVY",chapter_key=self.c["chapters"][1]["key"])

    def test_86_missing_chapter_arg_for_complete_rejected(self):
        self.deny(self.prefix(13),"complete",simulation_gate=machine.SIMULATION_GATE)

    def test_87_wrong_chapter_arg_for_advance_rejected(self):
        self.deny(self.finish_first(),"advance",chapter_key=self.c["chapters"][2]["key"])

    def test_88_unexpected_outcome_for_reenter_rejected(self):
        self.deny(self.begin(),"reenter",chapter_key=self.c["chapters"][1]["key"],outcome="WIN")

    def test_89_unexpected_gate_for_reenter_rejected(self):
        self.deny(self.begin(),"reenter",chapter_key=self.c["chapters"][1]["key"],
                  simulation_gate=machine.SIMULATION_GATE)

    def test_90_demo_shows_no_real_grants(self):
        result=ledger.demo(self.c,self.rules,self.policy,self.events)
        self.assertEqual(result["events_recorded"],13)
        self.assertEqual(result["unique_reward_intent_tokens"],5)
        self.assertEqual(result["duplicate_event_noops"],13)
        self.assertEqual(result["failed_n_attempts_without_progress"],1)
        self.assertEqual(result["chapter_after_reentry"],"UNOVA_CH02_STRIATON")
        self.assertEqual(result["reward_intents"]["ITEM:POKE_BALL"],5)
        self.assertFalse(result["native_items_granted"])
        self.assertFalse(result["can_install"])

    def test_91_cli_check_passes_with_offline_label(self):
        proc=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g01_reentry_ledger.py"),"--check"],
            cwd=ROOT,capture_output=True,text=True,check=False,timeout=25)
        self.assertEqual(proc.returncode,0,proc.stdout+"\n"+proc.stderr)
        result=json.loads(proc.stdout.strip())
        self.assertEqual(result["status"],"OFFLINE_LEDGER_POLICY_VALIDATED")
        self.assertFalse(result["native_items_granted"])

    def test_92_cli_demo_runs_without_save_access(self):
        proc=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g01_reentry_ledger.py"),"--simulate-demo"],
            cwd=ROOT,capture_output=True,text=True,check=False,timeout=25)
        self.assertEqual(proc.returncode,0,proc.stdout+"\n"+proc.stderr)
        result=json.loads(proc.stdout.strip())
        self.assertEqual(result["status"],"OFFLINE_LEDGER_DEMO_NOT_NATIVE_GAME")
        self.assertFalse(result["native_save_modified"])

    def test_93_terminal_postgame_reentry_stays_readonly(self):
        env=self.chapter(12)
        env=self.apply(env,"complete",chapter_key=self.c["chapters"][12]["key"],
                       simulation_gate=machine.SIMULATION_GATE)["envelope"]
        read=self.apply(env,"reenter",chapter_key=self.c["chapters"][3]["key"])
        self.assertEqual(read["status"],ledger.STATUS_REENTER)
        self.assertEqual(read["envelope"],env)

    def test_94_terminal_postgame_double_complete_noop(self):
        env=self.chapter(12)
        env=self.apply(env,"complete",chapter_key=self.c["chapters"][12]["key"],
                       simulation_gate=machine.SIMULATION_GATE)["envelope"]
        retry=self.apply(env,"complete",chapter_key=self.c["chapters"][12]["key"],
                         simulation_gate=machine.SIMULATION_GATE)
        self.assertEqual(retry["status"],ledger.STATUS_ALREADY)
        self.assertEqual(retry["new_reward_intents"],[])

    def test_95_terminal_postgame_cannot_advance(self):
        env=self.chapter(12)
        self.deny(env,"advance",chapter_key=self.c["chapters"][12]["key"])

if __name__=="__main__":
    unittest.main()
