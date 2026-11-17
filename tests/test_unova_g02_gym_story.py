"""G02.2: source-based White eight-gym event, badge, story gate regressions."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g02_gym_story as g02
import audit_unova_g01_chapter_machine as machine
import audit_unova_g01_serialization as codec

class G022GymTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx,cls.catalog=g02.load_project()
        cls.c,cls.rules,cls.policy,cls.events,_=cls.ctx
        cls.snapshots={}
        env=g02.initial(cls.ctx)
        def act(name,**kwargs):
            nonlocal env
            ret=g02.apply(env,cls.ctx,cls.catalog,name,**kwargs)
            env=ret["envelope"]
            return ret
        cls.snapshots["prestart"]=copy.deepcopy(env)
        act("begin")
        cls.snapshots["ch01"]=copy.deepcopy(env)
        for event in cls.events:
            kw={"event_key":event["key"]}
            if event["kind"]=="choice":kw["starter_choice"]="SNIVY"
            if event["battle_policy"] in {"ADVANCE_ON_LOSS","WIN_REQUIRED"}:
                kw["outcome"]="WIN"
            act("record_u07",**kw)
        act("complete",chapter_key=cls.c["chapters"][1]["key"],
            simulation_gate=machine.SIMULATION_GATE)
        act("advance",chapter_key=cls.c["chapters"][1]["key"])
        for gym in cls.catalog["gyms"]:
            idx=gym["index"]
            cls.snapshots[f"ch{idx+1}_active"]=copy.deepcopy(env)
            for event in gym["events"]:
                kw={"event_key":event["id"]}
                if event["kind"]=="battle":
                    kw.update(outcome="WIN",leader_key=g02._leader(gym,env["g01_envelope"]))
                act("record_story",**kw)
                cls.snapshots[f"gym{idx}_event{event['stage']}"]=copy.deepcopy(env)
            act("complete",chapter_key=gym["chapter_key"],
                simulation_gate=machine.SIMULATION_GATE)
            cls.snapshots[f"ch{idx+1}_complete"]=copy.deepcopy(env)
            act("advance",chapter_key=gym["chapter_key"])
        cls.snapshots["league"]=copy.deepcopy(env)

    def start(self,n):
        return copy.deepcopy(self.snapshots[f"ch{n+1}_active"])
    def end(self,n):
        return copy.deepcopy(self.snapshots[f"ch{n+1}_complete"])
    def event(self,n,step):
        return copy.deepcopy(self.snapshots[f"gym{n}_event{step}"])
    def apply(self,env,action,**kw):
        return g02.apply(env,self.ctx,self.catalog,action,**kw)
    def deny(self,env,action,**kw):
        before=copy.deepcopy(env)
        with self.assertRaises(ValueError):
            self.apply(env,action,**kw)
        self.assertEqual(before,env)
    def invalid(self,change):
        obj=copy.deepcopy(self.catalog)
        change(obj)
        region=machine._safe_source(ROOT/obj["badge_registry"])
        areas=machine._safe_source(ROOT/obj["area_catalog"])
        with self.assertRaises(ValueError):
            g02.validate_catalog(obj,self.ctx,region,areas)
    @staticmethod
    def story_kw(gym,event,env):
        args={"event_key":event["id"]}
        if event["kind"]=="battle":
            args.update(outcome="WIN",leader_key=g02._leader(gym,env["g01_envelope"]))
        return args

    def test_01_sources_approved_offline_only(self):
        r=g02.load_project()
        self.assertEqual(r[1]["phase"],"G02.2")
        self.assertFalse(r[1]["can_install"])
        self.assertFalse(r[1]["badge_items_granted"])
    def test_02_exact_eight_gym_battle_contracts(self):
        self.assertEqual(len(self.catalog["gyms"]),8)
        self.assertEqual([g["badge"] for g in self.catalog["gyms"]],
            ["TRIO","BASIC","INSECT","BOLT","QUAKE","JET","FREEZE","LEGEND"])
    def test_03_forty_events_all_symbolic(self):
        entries=[e for gym in self.catalog["gyms"] for e in gym["events"]]
        self.assertEqual(len(entries),40)
        self.assertEqual(len({e["id"] for e in entries}),40)
        self.assertTrue(all(e["source_map_id"] is None and
            e["native_event_id"] is None and e["trainer_id"] is None for e in entries))
    def test_04_all_gym_area_keys_from_u03(self):
        areas={r["key"] for r in machine._safe_source(ROOT/self.catalog["area_catalog"])["areas"]}
        self.assertTrue(all(g["city_area_key"] in areas and
            g["gym_area_key"] in areas for g in self.catalog["gyms"]))
    def test_05_white_iriss_not_drayden(self):
        self.assertEqual(self.catalog["gyms"][7]["leader_key"],"IRIS")
        self.assertNotIn("DRAYDEN",[g["leader_key"] for g in self.catalog["gyms"]])
    def test_06_starter_snivy_selects_chili(self):
        self.assertEqual(g02._leader(self.catalog["gyms"][0],self.start(1)["g01_envelope"]),"CHILI")
    def test_07_starter_variants_cover_all_three_choices(self):
        self.assertEqual(self.catalog["gyms"][0]["leader_by_starter"],
                         {"SNIVY":"CHILI","TEPIG":"CRESS","OSHAWOTT":"CILAN"})
    def test_08_no_real_teams_levels_or_badge_switches(self):
        self.assertTrue(all(g["trainer_party"] is None and
            g["trainer_levels"] is None and
            g["native_badge_switch_id"] is None for g in self.catalog["gyms"]))
    def test_09_prestart_has_zero_badges(self):
        env=self.snapshots["prestart"]
        self.assertEqual(g02.validate_envelope(env,self.ctx,self.catalog)["badge_count"],0)
    def test_10_ch01_has_zero_gyms(self):
        env=self.snapshots["ch01"]
        self.assertEqual(g02.validate_envelope(env,self.ctx,self.catalog)["event_count"],0)
    def test_11_new_gym_2_opens_after_U07(self):
        env=self.start(1)
        self.assertEqual(env["g01_envelope"]["state"]["current_chapter"],"UNOVA_CH02_STRIATON")
        self.assertEqual(env["story_receipts"],[])
    def test_12_first_story_event_applies(self):
        gym=self.catalog["gyms"][0]
        before=self.start(1)
        result=self.apply(before,"record_story",event_key=gym["events"][0]["id"])
        self.assertEqual(result["status"],"APPLIED_SIMULATION")
        self.assertEqual(len(result["envelope"]["story_receipts"]),1)
        self.assertEqual(before,self.start(1))
    def test_13_first_story_replay_is_noop(self):
        env=self.event(1,0)
        r=self.apply(env,"record_story",event_key=self.catalog["gyms"][0]["events"][0]["id"])
        self.assertEqual(r["status"],"ALREADY_RECORDED_NO_OP")
        self.assertEqual(r["envelope"],env)
    def test_14_first_badge_requires_battle(self):
        gym=self.catalog["gyms"][0]
        self.deny(self.event(1,1),"record_story",event_key=gym["events"][3]["id"])
    def test_15_all_gyms_have_no_early_badge(self):
        for n in range(1,9):
            with self.subTest(gym=n):
                self.assertEqual(len(self.start(n)["badge_claims"]),n-1)
    def test_16_all_gym_battles_require_win(self):
        for n,gym in enumerate(self.catalog["gyms"],1):
            with self.subTest(gym=n):
                env=self.event(n,1)
                leader=g02._leader(gym,env["g01_envelope"])
                self.deny(env,"record_story",event_key=gym["events"][2]["id"],
                          outcome="LOSS",leader_key=leader)
    def test_17_missing_explicit_battle_result_rejected(self):
        gym=self.catalog["gyms"][1]
        env=self.event(2,1)
        self.deny(env,"record_story",event_key=gym["events"][2]["id"],
                  leader_key="LENORA")
    def test_18_wrong_leader_rejected(self):
        gym=self.catalog["gyms"][0]
        env=self.event(1,1)
        self.deny(env,"record_story",event_key=gym["events"][2]["id"],
                  outcome="WIN",leader_key="CRESS")
    def test_19_wrong_white_opelucid_leader_rejected(self):
        gym=self.catalog["gyms"][7]
        env=self.event(8,1)
        self.deny(env,"record_story",event_key=gym["events"][2]["id"],
                  outcome="WIN",leader_key="DRAYDEN")
    def test_20_battle_win_records_only_symbolic_receipt(self):
        env=self.event(2,2)
        self.assertEqual(env["story_receipts"][-1]["receipt_scope"],g02.RECEIPT_SCOPE)
        self.assertEqual(env["story_receipts"][-1]["outcome"],"WIN")
        self.assertEqual(env["badge_claims"],["TRIO"])
    def test_21_each_badge_claimed_once_at_stage_3(self):
        for n in range(1,9):
            with self.subTest(gym=n):
                env=self.event(n,3)
                self.assertEqual(env["badge_claims"][-1],self.catalog["gyms"][n-1]["badge"])
                self.assertEqual(len(env["badge_claims"]),n)
    def test_22_badge_replay_noop(self):
        gym=self.catalog["gyms"][0]
        env=self.event(1,3)
        r=self.apply(env,"record_story",event_key=gym["events"][3]["id"])
        self.assertEqual(r["status"],"ALREADY_RECORDED_NO_OP")
        self.assertEqual(r["envelope"],env)
    def test_23_cannot_complete_gym_before_badge(self):
        env=self.event(1,2)
        self.deny(env,"complete",chapter_key=self.catalog["gyms"][0]["chapter_key"],
                  simulation_gate=machine.SIMULATION_GATE)
    def test_24_cannot_complete_gym_before_exit_story(self):
        env=self.event(1,3)
        self.deny(env,"complete",chapter_key=self.catalog["gyms"][0]["chapter_key"],
                  simulation_gate=machine.SIMULATION_GATE)
    def test_25_all_gym_completion_after_five_events(self):
        for gym in self.catalog["gyms"]:
            with self.subTest(gym=gym["index"]):
                env=self.end(gym["index"])
                self.assertEqual(env["g01_envelope"]["state"]["missions"][gym["mission_key"]],"completed")
                self.assertEqual(len(env["badge_claims"]),gym["index"])
    def test_26_all_gym_advances_require_previous_badge(self):
        for gym in self.catalog["gyms"][:-1]:
            with self.subTest(gym=gym["index"]):
                env=self.start(gym["index"])
                self.deny(env,"advance",chapter_key=gym["chapter_key"])
    def test_27_all_eight_badges_to_league(self):
        env=self.snapshots["league"]
        self.assertEqual(env["badge_claims"],["TRIO","BASIC","INSECT","BOLT",
            "QUAKE","JET","FREEZE","LEGEND"])
        self.assertEqual(env["g01_envelope"]["state"]["current_chapter"],"UNOVA_CH10_LEAGUE")
        self.assertEqual(g02.validate_envelope(env,self.ctx,self.catalog)["badge_count"],8)
    def test_28_league_continuation_reserved_for_g023(self):
        env=self.snapshots["league"]
        self.deny(env,"complete",chapter_key=self.c["chapters"][10]["key"],
                  simulation_gate=machine.SIMULATION_GATE)
    def test_29_no_direct_postgame_advance(self):
        env=self.snapshots["league"]
        self.deny(env,"advance",chapter_key=self.c["chapters"][10]["key"])
    def test_30_story_event_future_chapter_rejected(self):
        gym=self.catalog["gyms"][4]
        self.deny(self.start(1),"record_story",event_key=gym["events"][0]["id"])
    def test_31_story_event_skipped_stage_rejected(self):
        gym=self.catalog["gyms"][0]
        self.deny(self.start(1),"record_story",event_key=gym["events"][1]["id"])
    def test_32_duplicate_badge_receipt_rejected(self):
        env=self.event(1,3);env["story_receipts"].append(copy.deepcopy(env["story_receipts"][-1]))
        with self.assertRaises(ValueError):g02.validate_envelope(env,self.ctx,self.catalog)
    def test_33_forged_badge_claim_rejected(self):
        env=self.start(1);env["badge_claims"].append("TRIO")
        with self.assertRaises(ValueError):g02.validate_envelope(env,self.ctx,self.catalog)
    def test_34_wrong_badge_order_rejected(self):
        env=self.start(3);env["badge_claims"].reverse()
        with self.assertRaises(ValueError):g02.validate_envelope(env,self.ctx,self.catalog)
    def test_35_badge_removed_from_past_chapter_rejected(self):
        env=self.start(3);env["badge_claims"].pop()
        with self.assertRaises(ValueError):g02.validate_envelope(env,self.ctx,self.catalog)
    def test_36_reentry_previous_chapter_is_readonly(self):
        env=self.start(5)
        before=copy.deepcopy(env)
        r=self.apply(env,"reenter",chapter_key=self.c["chapters"][2]["key"])
        self.assertEqual(r["status"],"REENTERED_READ_ONLY")
        self.assertEqual(r["envelope"],before)
        self.assertEqual(env,before)
    def test_37_reentry_future_chapter_rejected(self):
        self.deny(self.start(3),"reenter",chapter_key=self.c["chapters"][9]["key"])
    def test_38_repeat_past_badge_stays_single(self):
        gym=self.catalog["gyms"][0];env=self.start(5)
        r=self.apply(env,"record_story",event_key=gym["events"][3]["id"])
        self.assertEqual(r["status"],"ALREADY_RECORDED_NO_OP")
        self.assertEqual(r["envelope"]["badge_claims"],env["badge_claims"])
    def test_39_repeat_battle_different_outcome_rejected(self):
        env=self.start(2);gym=self.catalog["gyms"][0]
        self.deny(env,"record_story",event_key=gym["events"][2]["id"],
                  outcome="LOSS",leader_key="CHILI")
    def test_40_chapter_01_U07_source_still_available(self):
        env=copy.deepcopy(self.snapshots["ch01"])
        self.assertEqual(env["g01_envelope"]["state"]["current_chapter"],"UNOVA_CH01_NUVEMA")
        self.assertEqual(env["badge_claims"],[])
    def test_41_g01_4_round_trip_projection(self):
        env=self.snapshots["league"]
        blob=codec.encode_current(env["g01_envelope"],self.ctx)
        self.assertEqual(codec.decode_current(blob,self.ctx),env["g01_envelope"])
    def test_42_g01_4_does_not_serialize_g02_badges_as_native(self):
        env=self.snapshots["league"]
        blob=codec.encode_current(env["g01_envelope"],self.ctx)
        d=json.loads(blob)
        self.assertNotIn("badge_claims",d["payload"])
    def test_43_cross_region_envelope_rejected(self):
        env=self.start(1);env["region"]="SINNOH"
        with self.assertRaises(ValueError):g02.validate_envelope(env,self.ctx,self.catalog)
    def test_44_wrong_version_rejected(self):
        env=self.start(1);env["schema"]=2
        with self.assertRaises(ValueError):g02.validate_envelope(env,self.ctx,self.catalog)
    def test_45_extra_native_field_rejected(self):
        env=self.start(1);env["native_badges"]=8
        with self.assertRaises(ValueError):g02.validate_envelope(env,self.ctx,self.catalog)
    def test_46_g01_future_chapter_forged_rejected(self):
        env=self.start(1);env["g01_envelope"]["state"]["current_chapter"]="UNOVA_CH10_LEAGUE"
        with self.assertRaises(ValueError):g02.validate_envelope(env,self.ctx,self.catalog)
    def test_47_missing_story_receipt_rejected(self):
        env=self.start(2);env["story_receipts"].pop()
        with self.assertRaises(ValueError):g02.validate_envelope(env,self.ctx,self.catalog)
    def test_48_forged_battle_win_rejected(self):
        env=self.event(1,2);env["story_receipts"][-1]["outcome"]="LOSS"
        with self.assertRaises(ValueError):g02.validate_envelope(env,self.ctx,self.catalog)
    def test_49_nonbattle_result_rejected(self):
        gym=self.catalog["gyms"][0]
        self.deny(self.start(1),"record_story",event_key=gym["events"][0]["id"],outcome="WIN")
    def test_50_unknown_story_event_rejected(self):
        self.deny(self.start(1),"record_story",event_key="UNOVA_G02_FAKE")
    def test_51_unknown_operation_rejected(self):
        self.deny(self.start(1),"give_legend_badge")
    def test_52_unauthorized_native_gate_rejected(self):
        gym=self.catalog["gyms"][0]
        self.deny(self.event(1,4),"complete",chapter_key=gym["chapter_key"],
                  simulation_gate="REAL_GAME_APPROVED")
    def test_53_completed_chapter_replay_does_not_add_badges(self):
        env=self.end(3);gym=self.catalog["gyms"][2]
        r=self.apply(env,"complete",chapter_key=gym["chapter_key"],
            simulation_gate=machine.SIMULATION_GATE)
        self.assertEqual(r["status"],"ALREADY_RECORDED_NO_OP")
        self.assertEqual(r["envelope"],env)
    def test_54_advance_replay_does_not_skip_next(self):
        env=self.start(4);gym=self.catalog["gyms"][2]
        r=self.apply(env,"advance",chapter_key=gym["chapter_key"])
        self.assertEqual(r["status"],"ALREADY_RECORDED_NO_OP")
        self.assertEqual(r["envelope"],env)
    def test_55_catalog_fake_map_id_rejected(self):
        self.invalid(lambda x:x["gyms"][0].update(native_badge_switch_id=12))
    def test_56_catalog_fake_badge_item_rejected(self):
        self.invalid(lambda x:x["gyms"][1].update(native_badge_item_id=400))
    def test_57_catalog_fake_pokemon_team_rejected(self):
        self.invalid(lambda x:x["gyms"][2].update(trainer_party=[{"species":"LILLIPUP"}]))
    def test_58_catalog_fake_levels_rejected(self):
        self.invalid(lambda x:x["gyms"][0].update(trainer_levels=[18]))
    def test_59_catalog_fake_playable_rejected(self):
        self.invalid(lambda x:x.update(can_install=True))
    def test_60_catalog_drayden_white_rejected(self):
        self.invalid(lambda x:x["gyms"][7].update(leader_key="DRAYDEN"))
    def test_61_catalog_wrong_striaton_branch_rejected(self):
        self.invalid(lambda x:x["gyms"][0]["leader_by_starter"].update(SNIVY="CILAN"))
    def test_62_catalog_wrong_badge_order_rejected(self):
        self.invalid(lambda x:x["gyms"][3].update(badge="TRIO"))
    def test_63_catalog_invented_area_rejected(self):
        self.invalid(lambda x:x["gyms"][4].update(gym_area_key="UNOVA_FAKE"))
    def test_64_catalog_missing_event_gate_rejected(self):
        self.invalid(lambda x:x["gyms"][5]["events"][3].update(requires=[]))
    def test_65_catalog_loss_allowed_in_gym_rejected(self):
        self.invalid(lambda x:x["gyms"][6]["events"][2].update(outcome_required="LOSS"))
    def test_66_catalog_wrong_campaign_rejected(self):
        self.invalid(lambda x:x.update(campaign="BLACK_BW"))
    def test_67_catalog_native_events_claim_rejected(self):
        self.invalid(lambda x:x.update(actual_story_events_executed=True))
    def test_68_catalog_unexpected_extra_event_rejected(self):
        self.invalid(lambda x:x["gyms"][0]["events"].append(copy.deepcopy(x["gyms"][0]["events"][0])))
    def test_69_registry_bogus_badge_rejected(self):
        regions=machine._safe_source(ROOT/self.catalog["badge_registry"])
        areas=machine._safe_source(ROOT/self.catalog["area_catalog"])
        regions["regions"]["UNOVA"]["milestones"][0]="FAKE"
        with self.assertRaises(ValueError):
            g02.validate_catalog(self.catalog,self.ctx,regions,areas)
    def test_70_all_returns_never_grant_native_items(self):
        gym=self.catalog["gyms"][0]
        r=self.apply(self.start(1),"record_story",event_key=gym["events"][0]["id"])
        self.assertFalse(r["native_badges_granted"])
        self.assertFalse(r["native_events_executed"])
        self.assertFalse(r["native_save_modified"])
        self.assertFalse(r["game_exe_tested"])
        self.assertFalse(r["can_install"])
    def test_71_demo_full_eight_gym_simulation(self):
        result=g02.demo(self.ctx,self.catalog)
        self.assertEqual(result["events_recorded"],40)
        self.assertEqual(result["badge_claims"],8)
        self.assertEqual(result["chapter_after_gyms"],"UNOVA_CH10_LEAGUE")
        self.assertTrue(result["g01_4_projection_roundtrip"])
        self.assertFalse(result["native_badges_granted"])
    def test_72_cli_check_success(self):
        run=subprocess.run([sys.executable,str(g02.ROOT/"scripts/regions/audit_unova_g02_gym_story.py"),
            "--check"],cwd=g02.ROOT,text=True,capture_output=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(json.loads(run.stdout)["symbolic_events"],40)
    def test_73_cli_demo_success(self):
        run=subprocess.run([sys.executable,str(g02.ROOT/"scripts/regions/audit_unova_g02_gym_story.py"),
            "--simulate-demo"],cwd=g02.ROOT,text=True,capture_output=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(json.loads(run.stdout)["badge_claims"],8)
    def test_74_no_game_exe_or_saves_in_catalog(self):
        gym=self.catalog["gyms"][0]
        self.assertEqual(gym["challenge_status"],"PLANNED_NOT_PLAYABLE")
        self.assertTrue(all(e["simulation_only"] for e in gym["events"]))
    def test_75_all_contract_prerequisites_in_source_order(self):
        for gym in self.catalog["gyms"]:
            for j,event in enumerate(gym["events"]):
                self.assertEqual(event["requires"],[gym["events"][j-1]["id"]] if j else [])
    def test_76_g01_chapter_completion_requires_full_story_all_gyms(self):
        for gym in self.catalog["gyms"]:
            with self.subTest(gym=gym["index"]):
                env=self.event(gym["index"],3)
                self.deny(env,"complete",chapter_key=gym["chapter_key"],
                    simulation_gate=machine.SIMULATION_GATE)

if __name__=="__main__":
    unittest.main()
