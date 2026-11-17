"""G02.3 White Elite Four/N/Ghetsis/credits regression; no Game.exe or saves."""
from __future__ import annotations
import copy
import itertools
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g02_elite_finale as final
import audit_unova_g01_chapter_machine as machine
import audit_unova_g01_serialization as codec

class G023Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx,cls.gyms,cls.cat=final.load_project()
        cls.c=cls.ctx[0]
        cls.members=[x["key"] for x in cls.cat["elite_members"]]
        cls.events=cls.cat["castle_events"]
        cls.snap={}
        env=final.build_league_fixture(cls.ctx,cls.gyms)
        cls.snap["league"]=copy.deepcopy(env)
        def perform(action,**kwargs):
            nonlocal env
            res=final.apply(env,cls.ctx,cls.gyms,cls.cat,action,**kwargs)
            env=res["envelope"]
            return res
        for i,key in enumerate(cls.members,1):
            perform("elite_battle",member_key=key,outcome="WIN")
            cls.snap["elite"+str(i)]=copy.deepcopy(env)
        perform("complete_elite",simulation_gate=machine.SIMULATION_GATE)
        cls.snap["elite_completed"]=copy.deepcopy(env)
        perform("advance_castle")
        cls.snap["castle"]=copy.deepcopy(env)
        for i,event in enumerate(cls.events):
            kw={"event_key":event["id"]}
            if event["kind"]=="battle":
                kw.update(outcome="WIN",opponent_key=event["id"].split("_")[-2])
            perform("castle_event",**kw)
            cls.snap["castle_event"+str(i+1)]=copy.deepcopy(env)
        perform("complete_castle",simulation_gate=machine.SIMULATION_GATE)
        cls.snap["castle_completed"]=copy.deepcopy(env)
        perform("unlock_postgame")
        cls.snap["postgame"]=copy.deepcopy(env)

    def fresh(self,name="league"):return copy.deepcopy(self.snap[name])
    def act(self,env,action,**kwargs):
        return final.apply(env,self.ctx,self.gyms,self.cat,action,**kwargs)
    def deny(self,env,action,**kwargs):
        original=copy.deepcopy(env)
        with self.assertRaises(ValueError):self.act(env,action,**kwargs)
        self.assertEqual(env,original)
    def invalid_env(self,mutator,name="league"):
        env=self.fresh(name);mutator(env)
        with self.assertRaises(ValueError):
            final.validate_envelope(env,self.ctx,self.gyms,self.cat)
    def invalid_cat(self,mutator):
        cat=copy.deepcopy(self.cat);mutator(cat)
        with self.assertRaises(ValueError):
            final.validate_catalog(cat,self.ctx,self.gyms,
                machine._safe_source(ROOT/cat["source_region_registry"]),
                machine._safe_source(ROOT/cat["source_area_catalog"]))
    def castle_kw(self,i,outcome="WIN"):
        event=self.events[i]
        kw={"event_key":event["id"]}
        if event["kind"]=="battle":
            kw.update(outcome=outcome,opponent_key="N" if i==2 else "GHETSIS")
        return kw

    def test_01_catalog_white_story_only(self):
        self.assertEqual(self.cat["phase"],"G02.3")
        self.assertEqual(self.cat["campaign"],"WHITE_BW")
        self.assertFalse(self.cat["can_install"])
        self.assertFalse(self.cat["game_exe_tested"])
    def test_02_four_elite_members_as_original_battle_contracts(self):
        self.assertEqual([m["member_name"] for m in self.cat["elite_members"]],
            ["SHAUNTAL","GRIMSLEY","CAITLIN","MARSHAL"])
    def test_03_four_elite_members_have_no_made_up_teams(self):
        self.assertTrue(all(m["team"] is None and m["levels"] is None
            and m["native_trainer_id"] is None for m in self.cat["elite_members"]))
    def test_04_castle_events_are_n_z_ghetsis_credits(self):
        self.assertEqual([e["id"] for e in self.events],[
            "UNOVA_G023_CASTLE_ENTRY","UNOVA_G023_ZEKROM_STORY_GATE",
            "UNOVA_G023_N_BATTLE","UNOVA_G023_GHETSIS_BATTLE",
            "UNOVA_G023_CREDITS"])
    def test_05_g02_eight_badge_requirement(self):
        self.assertEqual(self.fresh()["g02_envelope"]["badge_claims"],
            ["TRIO","BASIC","INSECT","BOLT","QUAKE","JET","FREEZE","LEGEND"])
    def test_06_league_active_mission_from_g011(self):
        state=self.fresh()["g02_envelope"]["g01_envelope"]["state"]
        self.assertEqual(state["current_chapter"],"UNOVA_CH10_LEAGUE")
        self.assertEqual(state["missions"]["UNOVA_MISSION_CH10_ELITE_FOUR"],"active")
    def test_07_league_starts_no_elite_or_castle_receipts(self):
        env=self.fresh()
        self.assertEqual((env["elite_wins"],env["castle_receipts"],env["unique_story_tokens"]),([],[],[]))
    def test_08_all_twenty_four_elite_orders_are_accepted(self):
        for order in itertools.permutations(self.members):
            with self.subTest(order=order):
                env=self.fresh()
                for key in order:
                    env=self.act(env,"elite_battle",member_key=key,outcome="WIN")["envelope"]
                self.assertEqual(len(env["elite_wins"]),4)
                self.assertEqual({x["member_key"] for x in env["elite_wins"]},set(self.members))
                self.assertEqual(final.validate_envelope(env,self.ctx,self.gyms,self.cat)["elite_wins"],4)
    def test_09_each_member_can_be_fought_first(self):
        for key in self.members:
            with self.subTest(key=key):
                self.assertEqual(self.act(self.fresh(),"elite_battle",
                    member_key=key,outcome="WIN")["status"],final.RESULT_SUCCESS)
    def test_10_elite_loss_is_noop(self):
        env=self.fresh()
        res=self.act(env,"elite_battle",member_key=self.members[0],outcome="LOSS")
        self.assertEqual(res["status"],final.RESULT_LOSS)
        self.assertEqual(res["envelope"],env)
        self.assertEqual(res["suggested_safe_return_area_key"],"UNOVA_POKEMON_LEAGUE")
        self.assertFalse(res["native_teleport_executed"])
    def test_11_elite_repeated_losses_allow_future_win(self):
        env=self.fresh()
        for _ in range(3):
            r=self.act(env,"elite_battle",member_key=self.members[2],outcome="LOSS")
            self.assertEqual(r["envelope"],env)
        win=self.act(env,"elite_battle",member_key=self.members[2],outcome="WIN")
        self.assertEqual(win["status"],final.RESULT_SUCCESS)
    def test_12_elite_duplicates_do_not_count_twice(self):
        env=self.fresh("elite1")
        r=self.act(env,"elite_battle",member_key=self.members[0],outcome="WIN")
        self.assertEqual(r["status"],final.RESULT_REPLAY)
        self.assertEqual(r["envelope"],env)
    def test_13_elite_cannot_rewrite_win_as_loss(self):
        self.deny(self.fresh("elite1"),"elite_battle",
            member_key=self.members[0],outcome="LOSS")
    def test_14_elite_unknown_member_blocked(self):
        self.deny(self.fresh(),"elite_battle",member_key="UNOVA_G023_ELITE_ALDER",outcome="WIN")
    def test_15_elite_no_outcome_blocked(self):
        self.deny(self.fresh(),"elite_battle",member_key=self.members[0])
    def test_16_elite_battle_no_draw_blocked(self):
        self.deny(self.fresh(),"elite_battle",member_key=self.members[0],outcome="DRAW")
    def test_17_cannot_complete_elite_after_three_wins(self):
        self.deny(self.fresh("elite3"),"complete_elite",
            simulation_gate=machine.SIMULATION_GATE)
    def test_18_cannot_complete_elite_without_simulation_gate(self):
        self.deny(self.fresh("elite4"),"complete_elite")
    def test_19_cannot_complete_elite_with_real_claim(self):
        self.deny(self.fresh("elite4"),"complete_elite",simulation_gate="GAME_EXE_APPROVED")
    def test_20_four_elite_wins_allow_completion(self):
        env=self.fresh("elite_completed")
        self.assertEqual(env["g02_envelope"]["g01_envelope"]["state"]["missions"][
            "UNOVA_MISSION_CH10_ELITE_FOUR"],"completed")
    def test_21_elite_completion_replay_noop(self):
        r=self.act(self.fresh("elite_completed"),"complete_elite",
            simulation_gate=machine.SIMULATION_GATE)
        self.assertEqual(r["status"],final.RESULT_REPLAY)
    def test_22_castle_locked_before_elite_completion(self):
        self.deny(self.fresh("elite3"),"advance_castle")
    def test_23_castle_available_after_four_elite_wins(self):
        r=self.act(self.fresh("elite_completed"),"advance_castle")
        self.assertEqual(r["status"],final.RESULT_SUCCESS)
        self.assertEqual(r["envelope"]["g02_envelope"]["g01_envelope"]["state"][
            "current_chapter"],"UNOVA_CH11_NS_CASTLE")
    def test_24_advance_castle_repeat_noop(self):
        r=self.act(self.fresh("castle"),"advance_castle")
        self.assertEqual(r["status"],final.RESULT_REPLAY)
    def test_25_castle_narrative_arrival_first(self):
        r=self.act(self.fresh("castle"),"castle_event",**self.castle_kw(0))
        self.assertEqual(r["status"],final.RESULT_SUCCESS)
        self.assertEqual(r["envelope"]["castle_receipts"][0]["event_key"],self.events[0]["id"])
    def test_26_zekrom_gate_cannot_precede_castle_entry(self):
        self.deny(self.fresh("castle"),"castle_event",**self.castle_kw(1))
    def test_27_white_zekrom_story_gate_is_unique(self):
        env=self.fresh("castle_event2")
        self.assertEqual(env["unique_story_tokens"],
            ["UNOVA_G023_ZEKROM_GATE_READY_NOT_CAPTURED"])
        self.assertEqual(self.act(env,"castle_event",**self.castle_kw(1))["status"],
                         final.RESULT_REPLAY)
    def test_28_z_gate_never_captures_legendary(self):
        r=self.act(self.fresh("castle_event1"),"castle_event",**self.castle_kw(1))
        self.assertFalse(r["legendary_captured"])
        self.assertFalse(r["actual_rewards_granted"])
    def test_29_n_battle_must_follow_zekrom_gate(self):
        self.deny(self.fresh("castle_event1"),"castle_event",**self.castle_kw(2))
    def test_30_n_loss_retries_at_castle_without_progress(self):
        env=self.fresh("castle_event2")
        r=self.act(env,"castle_event",**self.castle_kw(2,outcome="LOSS"))
        self.assertEqual(r["status"],final.RESULT_LOSS)
        self.assertEqual(r["envelope"],env)
        self.assertEqual(r["suggested_safe_return_area_key"],"UNOVA_NS_CASTLE")
    def test_31_n_loss_repeat_safe(self):
        env=self.fresh("castle_event2")
        for _ in range(3):
            r=self.act(env,"castle_event",**self.castle_kw(2,outcome="LOSS"))
            self.assertEqual(r["envelope"],env)
    def test_32_n_win_after_loss_allowed(self):
        env=self.fresh("castle_event2")
        loss=self.act(env,"castle_event",**self.castle_kw(2,outcome="LOSS"))
        win=self.act(loss["envelope"],"castle_event",**self.castle_kw(2))
        self.assertEqual(win["status"],final.RESULT_SUCCESS)
        self.assertEqual(len(win["envelope"]["castle_receipts"]),3)
    def test_33_n_win_replay_noop(self):
        env=self.fresh("castle_event3")
        self.assertEqual(self.act(env,"castle_event",**self.castle_kw(2))["status"],
                         final.RESULT_REPLAY)
    def test_34_n_win_cannot_be_rewritten_as_loss(self):
        self.deny(self.fresh("castle_event3"),"castle_event",
                  **self.castle_kw(2,outcome="LOSS"))
    def test_35_n_battle_wrong_opponent_blocked(self):
        self.deny(self.fresh("castle_event2"),"castle_event",
            event_key=self.events[2]["id"],outcome="WIN",opponent_key="GHETSIS")
    def test_36_n_battle_requires_result(self):
        self.deny(self.fresh("castle_event2"),"castle_event",
            event_key=self.events[2]["id"],opponent_key="N")
    def test_37_ghetsis_battle_requires_n_win(self):
        self.deny(self.fresh("castle_event2"),"castle_event",**self.castle_kw(3))
    def test_38_ghetsis_loss_no_progress(self):
        env=self.fresh("castle_event3")
        r=self.act(env,"castle_event",**self.castle_kw(3,outcome="LOSS"))
        self.assertEqual(r["status"],final.RESULT_LOSS)
        self.assertEqual(r["envelope"],env)
    def test_39_ghetsis_loss_then_win(self):
        env=self.fresh("castle_event3")
        loss=self.act(env,"castle_event",**self.castle_kw(3,outcome="LOSS"))
        win=self.act(loss["envelope"],"castle_event",**self.castle_kw(3))
        self.assertEqual(win["status"],final.RESULT_SUCCESS)
    def test_40_ghetsis_win_replay_noop(self):
        env=self.fresh("castle_event4")
        self.assertEqual(self.act(env,"castle_event",**self.castle_kw(3))["status"],
                         final.RESULT_REPLAY)
    def test_41_ghetsis_win_cannot_change_to_loss(self):
        self.deny(self.fresh("castle_event4"),"castle_event",
                  **self.castle_kw(3,outcome="LOSS"))
    def test_42_ghetsis_wrong_opponent_blocked(self):
        self.deny(self.fresh("castle_event3"),"castle_event",
                  event_key=self.events[3]["id"],outcome="WIN",opponent_key="N")
    def test_43_credits_before_ghetsis_blocked(self):
        self.deny(self.fresh("castle_event3"),"castle_event",**self.castle_kw(4))
    def test_44_credits_after_ghetsis_once(self):
        env=self.fresh("castle_event5")
        self.assertEqual(env["unique_story_tokens"][:2],
                         ["UNOVA_G023_ZEKROM_GATE_READY_NOT_CAPTURED",
                          "UNOVA_G023_CREDITS_SIMULATED"])
    def test_45_credits_duplicate_noop(self):
        env=self.fresh("castle_event5")
        result=self.act(env,"castle_event",**self.castle_kw(4))
        self.assertEqual(result["status"],final.RESULT_REPLAY)
        self.assertEqual(result["envelope"],env)
    def test_46_credits_not_actually_played(self):
        r=self.act(self.fresh("castle_event4"),"castle_event",**self.castle_kw(4))
        self.assertFalse(r["real_credits_shown"])
        self.assertFalse(r["game_exe_tested"])
    def test_47_castle_completion_before_credits_blocked(self):
        self.deny(self.fresh("castle_event4"),"complete_castle",
            simulation_gate=machine.SIMULATION_GATE)
    def test_48_castle_completion_requires_explicit_gate(self):
        self.deny(self.fresh("castle_event5"),"complete_castle")
    def test_49_castle_completion_with_simulation_gate(self):
        env=self.fresh("castle_completed")
        self.assertEqual(env["g02_envelope"]["g01_envelope"]["state"]["missions"][
            "UNOVA_MISSION_CH11_N_CASTLE"],"completed")
    def test_50_castle_completion_replay_noop(self):
        env=self.fresh("castle_completed")
        r=self.act(env,"complete_castle",simulation_gate=machine.SIMULATION_GATE)
        self.assertEqual(r["status"],final.RESULT_REPLAY)
    def test_51_postgame_before_credits_blocked(self):
        self.deny(self.fresh("castle_event4"),"unlock_postgame")
    def test_52_postgame_before_chapter_completion_blocked(self):
        self.deny(self.fresh("castle_event5"),"unlock_postgame")
    def test_53_postgame_requires_completed_castle_and_credits(self):
        env=self.fresh("postgame")
        self.assertEqual(env["g02_envelope"]["g01_envelope"]["state"][
            "current_chapter"],"UNOVA_CH12_POSTGAME")
        self.assertEqual(len(env["unique_story_tokens"]),3)
    def test_54_postgame_unlocked_once(self):
        env=self.fresh("postgame")
        r=self.act(env,"unlock_postgame")
        self.assertEqual(r["status"],final.RESULT_REPLAY)
        self.assertEqual(r["envelope"],env)
    def test_55_postgame_does_not_mean_postgame_implemented(self):
        env=self.fresh("postgame")
        s=env["g02_envelope"]["g01_envelope"]["state"]
        self.assertEqual(s["missions"]["UNOVA_MISSION_CH12_POSTGAME"],"active")
    def test_56_return_to_league_read_only(self):
        env=self.fresh("castle_event4")
        r=self.act(env,"reenter",chapter_key=self.c["chapters"][10]["key"])
        self.assertEqual(r["status"],final.RESULT_REENTER)
        self.assertEqual(r["envelope"],env)
    def test_57_return_to_castle_read_only(self):
        env=self.fresh("postgame")
        r=self.act(env,"reenter",chapter_key=self.c["chapters"][11]["key"])
        self.assertEqual(r["status"],final.RESULT_REENTER)
        self.assertEqual(r["envelope"],env)
    def test_58_no_reenter_future_chapter(self):
        self.deny(self.fresh(),"reenter",chapter_key=self.c["chapters"][12]["key"])
    def test_59_no_reenter_unknown_chapter(self):
        self.deny(self.fresh("castle"),"reenter",chapter_key="UNOVA_CH99_FUTURE")
    def test_60_no_auto_teleport_on_loss(self):
        r=self.act(self.fresh("elite1"),"elite_battle",
            member_key=self.members[2],outcome="LOSS")
        self.assertFalse(r["native_teleport_executed"])
    def test_61_missing_fourth_elite_win_cannot_complete(self):
        self.deny(self.fresh("elite3"),"complete_elite",
            simulation_gate=machine.SIMULATION_GATE)
    def test_62_duplicate_elite_receipt_rejected(self):
        self.invalid_env(lambda e:e["elite_wins"].append(copy.deepcopy(e["elite_wins"][0])),
                         "elite1")
    def test_63_fake_extra_elite_receipt_rejected(self):
        self.invalid_env(lambda e:e["elite_wins"].append({
            "member_key":"ALDER","outcome":"WIN","receipt_scope":final.RECEIPT_SCOPE}),"league")
    def test_64_forged_elite_loss_receipt_rejected(self):
        self.invalid_env(lambda e:e["elite_wins"][0].update(outcome="LOSS"),"elite1")
    def test_65_elite_receipt_missing_field_rejected(self):
        self.invalid_env(lambda e:e["elite_wins"][0].pop("receipt_scope"),"elite1")
    def test_66_castle_receipt_wrong_sequence_rejected(self):
        self.invalid_env(lambda e:e["castle_receipts"].reverse(),"castle_event3")
    def test_67_castle_receipt_duplicate_rejected(self):
        self.invalid_env(lambda e:e["castle_receipts"].append(
            copy.deepcopy(e["castle_receipts"][-1])),"castle_event3")
    def test_68_castle_receipt_loss_forged_rejected(self):
        self.invalid_env(lambda e:e["castle_receipts"][2].update(outcome="LOSS"),
                         "castle_event3")
    def test_69_credits_token_forged_before_ghetsis_rejected(self):
        self.invalid_env(lambda e:e["unique_story_tokens"].append(
            "UNOVA_G023_CREDITS_SIMULATED"),"castle_event2")
    def test_70_postgame_token_forged_early_rejected(self):
        self.invalid_env(lambda e:e["unique_story_tokens"].append(
            "UNOVA_G023_POSTGAME_ACCESS_SIMULATED"),"castle_event5")
    def test_71_legendary_token_removed_rejected(self):
        self.invalid_env(lambda e:e["unique_story_tokens"].clear(),"castle_event2")
    def test_72_future_chapter_forged_rejected(self):
        self.invalid_env(lambda e:e["g02_envelope"]["g01_envelope"]["state"].update(
            current_chapter="UNOVA_CH12_POSTGAME"),"elite4")
    def test_73_badge_removed_rejected(self):
        self.invalid_env(lambda e:e["g02_envelope"]["badge_claims"].pop(),"league")
    def test_74_early_castle_receipt_rejected(self):
        self.invalid_env(lambda e:e["castle_receipts"].append(
            copy.deepcopy(self.snap["castle_event1"]["castle_receipts"][0])),"league")
    def test_75_missing_elite_win_in_castle_rejected(self):
        self.invalid_env(lambda e:e["elite_wins"].pop(),"castle")
    def test_76_missing_castle_credits_in_postgame_rejected(self):
        self.invalid_env(lambda e:e["castle_receipts"].pop(),"postgame")
    def test_77_scope_forged_rejected(self):
        self.invalid_env(lambda e:e.update(scope="NATIVE_GAME_SAVE"))
    def test_78_region_forged_rejected(self):
        self.invalid_env(lambda e:e.update(region="KANTO"))
    def test_79_schema_future_rejected(self):
        self.invalid_env(lambda e:e.update(schema=2))
    def test_80_extra_native_reward_rejected(self):
        self.invalid_env(lambda e:e.update(real_zekrom={"species":"ZEKROM"}))
    def test_81_wrong_elite_member_order_in_catalog_rejected(self):
        self.invalid_cat(lambda x:x["elite_members"].reverse())
    def test_82_catalog_wrong_specialty_rejected(self):
        self.invalid_cat(lambda x:x["elite_members"][0].update(specialty="WATER"))
    def test_83_catalog_forged_native_party_rejected(self):
        self.invalid_cat(lambda x:x["elite_members"][0].update(team=[{"species":"LITWICK"}]))
    def test_84_catalog_forged_native_mapid_rejected(self):
        self.invalid_cat(lambda x:x["castle_events"][0].update(native_map_id=999))
    def test_85_catalog_wrong_n_battle_outcome_rejected(self):
        self.invalid_cat(lambda x:x["castle_events"][2].update(outcome_required="LOSS"))
    def test_86_catalog_misordered_castle_gate_rejected(self):
        self.invalid_cat(lambda x:x["castle_events"][1].update(requires=[]))
    def test_87_catalog_remove_elite_member_rejected(self):
        self.invalid_cat(lambda x:x["elite_members"].pop())
    def test_88_catalog_wrong_white_dragon_rejected(self):
        self.invalid_cat(lambda x:x["unique_story_tokens"].update(
            legendary_gate="UNOVA_G023_RESHIRAM_GATE_READY"))
    def test_89_catalog_false_native_credits_rejected(self):
        self.invalid_cat(lambda x:x.update(real_credits_shown=True))
    def test_90_catalog_false_native_legendary_claim_rejected(self):
        self.invalid_cat(lambda x:x.update(legendary_captured=True))
    def test_91_catalog_false_save_modification_rejected(self):
        self.invalid_cat(lambda x:x.update(native_saves_modified=True))
    def test_92_catalog_false_can_install_rejected(self):
        self.invalid_cat(lambda x:x.update(can_install=True))
    def test_93_catalog_badge_gate_removed_rejected(self):
        self.invalid_cat(lambda x:x["required_badges"].pop())
    def test_94_catalog_fake_levels_rejected(self):
        self.invalid_cat(lambda x:x["elite_members"][1].update(levels=[50]))
    def test_95_g01_4_roundtrip_projection_unchanged(self):
        env=self.fresh("postgame")
        projection=env["g02_envelope"]["g01_envelope"]
        raw=codec.encode_current(projection,self.ctx)
        self.assertEqual(codec.decode_current(raw,self.ctx),projection)
        self.assertNotIn("unique_story_tokens",json.loads(raw)["payload"])
    def test_96_cannot_serialize_g023_directly_via_g01_codec(self):
        with self.assertRaises(ValueError):
            codec.encode_current(self.fresh("postgame"),self.ctx)
    def test_97_cannot_use_native_approval_completion(self):
        self.deny(self.fresh("elite4"),"complete_elite",
                  simulation_gate="GAME_EXE_APPROVED")
    def test_98_unexpected_outcome_on_complete_rejected(self):
        self.deny(self.fresh("elite4"),"complete_elite",
                  outcome="WIN",simulation_gate=machine.SIMULATION_GATE)
    def test_99_unexpected_event_key_on_elite_battle_rejected(self):
        self.deny(self.fresh(),"elite_battle",member_key=self.members[0],
                  event_key=self.events[0]["id"],outcome="WIN")
    def test_100_unexpected_member_on_castle_event_rejected(self):
        self.deny(self.fresh("castle"),"castle_event",
                  event_key=self.events[0]["id"],member_key=self.members[0])
    def test_101_unexpected_simulation_gate_on_story_rejected(self):
        self.deny(self.fresh("castle"),"castle_event",
                  event_key=self.events[0]["id"],simulation_gate=machine.SIMULATION_GATE)
    def test_102_unexpected_reenter_gate_rejected(self):
        self.deny(self.fresh("castle"),"reenter",
                  chapter_key=self.c["chapters"][10]["key"],
                  simulation_gate=machine.SIMULATION_GATE)
    def test_103_unknown_operation_blocked(self):
        self.deny(self.fresh("postgame"),"capture_zekrom")
    def test_104_demo_full_campaign_and_credits(self):
        r=final.demo(self.ctx,self.gyms,self.cat)
        self.assertEqual(r["elite_wins"],4)
        self.assertEqual(r["castle_events"],5)
        self.assertEqual(r["final_chapter"],"UNOVA_CH12_POSTGAME")
        self.assertTrue(r["g01_4_projection_roundtrip"])
        self.assertFalse(r["legendary_captured"])
        self.assertFalse(r["real_credits_shown"])
    def test_105_cli_check_passes(self):
        r=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g02_elite_finale.py"),
            "--check"],cwd=ROOT,capture_output=True,text=True,timeout=35)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(json.loads(r.stdout)["elite_members"],4)
    def test_106_cli_demo_passes(self):
        r=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g02_elite_finale.py"),
            "--simulate-demo"],cwd=ROOT,capture_output=True,text=True,timeout=35)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        obj=json.loads(r.stdout)
        self.assertEqual(obj["castle_events"],5)
        self.assertFalse(obj["game_exe_tested"])

if __name__=="__main__":
    unittest.main()
