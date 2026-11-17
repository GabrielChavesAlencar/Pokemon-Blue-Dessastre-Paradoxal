"""Unova G03.3: sourced rival/Plasma/boss contracts; synthetic receipts only."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g03_rivals_plasma as g
import audit_unova_g01_chapter_machine as machine
import audit_unova_g01_serialization as codec

class UnovaG033Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx,cls.gyms,cls.finale,cls.post,cls.balance,cls.catalog=g.load_project()
        cls.finished,cls.snap=g.build_demo(
            cls.ctx,cls.gyms,cls.finale,cls.post,cls.balance,cls.catalog)
        cls.entries={e["id"]:e for e in cls.catalog["encounters"]}
        cls.planned=[e for e in cls.catalog["encounters"]
                     if e["source_mode"]=="PLANNED"]
        cls.linked=[e for e in cls.catalog["encounters"]
                    if e["source_mode"]!="PLANNED"]
        cls.npcs=machine._safe_source(ROOT/cls.catalog["sources"]["npc_catalog"])
        cls.trainers=machine._safe_source(ROOT/cls.catalog["sources"]["trainer_references"])
        cls.areas=machine._safe_source(ROOT/cls.catalog["sources"]["areas"])
        cls.u07=machine._safe_source(ROOT/cls.catalog["sources"]["g01_u07"])

    def env(self,label="CH12_POSTGAME"):
        return copy.deepcopy(self.snap[label])
    def act(self,env,action,**kwargs):
        return g.apply(env,self.ctx,self.gyms,self.finale,self.post,self.catalog,
                       action,**kwargs)
    def deny(self,env,action,**kwargs):
        old=copy.deepcopy(env)
        with self.assertRaises(ValueError):
            self.act(env,action,**kwargs)
        self.assertEqual(old,env)
    def event(self,chapter,actor):
        return self.entries[f"UNOVA_G033_CH{chapter:02d}_{actor}"]
    def source(self,e,env):
        return self.act(env,"inspect_linked",encounter_key=e["id"])
    def bad_state(self,change,label="CH12_POSTGAME"):
        env=self.env(label);change(env)
        with self.assertRaises(ValueError):
            g.validate_envelope(env,self.ctx,self.gyms,self.finale,self.post,self.catalog)
    def bad_catalog(self,change):
        catalog=copy.deepcopy(self.catalog);change(catalog)
        with self.assertRaises(ValueError):
            g.validate_catalog(catalog,self.ctx,self.gyms,self.finale,self.post,
                               self.balance,self.npcs,self.trainers,self.areas,self.u07)
    def team(self,env=None,**override):
        x={"encounter_key":self.event(2,"CHEREN")["id"],
           "party":[{"level":40,"egg":False}],
           "engine_max_level":100,"story_stage":0,
           "synthetic_authored_team_size":3}
        x.update(override)
        return g.plan_team(env or self.env("CH02_START"),self.ctx,self.gyms,
                           self.finale,self.post,self.balance,self.catalog,**x)

    def test_001_catalog_refers_to_existing_e07_and_sp04(self):
        self.assertEqual(self.catalog["sources"]["trainer_references"],
                         "data/regions/unova-e06-e07-preparation.json")
        self.assertFalse(self.catalog["real_team_data_verified"])
    def test_002_exact_fifteen_stable_story_records(self):
        self.assertEqual(len(self.catalog["encounters"]),15)
        self.assertEqual(len(set(self.entries)),15)
    def test_003_six_authoritative_read_only_links(self):
        self.assertEqual(len(self.linked),6)
        self.assertEqual(len([e for e in self.linked
                     if e["source_mode"]=="LINKED_G013"]),4)
        self.assertEqual(len([e for e in self.linked
                     if e["source_mode"]=="LINKED_G023"]),2)
    def test_004_exact_nine_planned_battle_slots(self):
        self.assertEqual(len(self.planned),9)
        self.assertTrue(all(e["source_event_key"] is None for e in self.planned))
    def test_005_actor_keys_are_whitelisted(self):
        self.assertEqual({e["actor_key"] for e in self.catalog["encounters"]},
            {"CHEREN","BIANCA","N","GHETSIS","PLASMA_GRUNT"})
    def test_006_plasma_archetype_has_no_pbs_trainer(self):
        self.assertTrue(all(e["trainer_reference_key"] is None for e in
            self.catalog["encounters"] if e["actor_key"]=="PLASMA_GRUNT"))
    def test_007_every_battle_team_and_level_are_null(self):
        self.assertTrue(all(e["canonical_team"] is None and
            e["canonical_levels"] is None and e["canonical_moves"] is None and
            e["trainer_pbs_id"] is None for e in self.catalog["encounters"]))
    def test_008_every_event_map_id_is_null(self):
        self.assertTrue(all(e["native_map_id"] is None and e["native_event_id"] is None
            for e in self.catalog["encounters"]))
    def test_009_ch01_bianca_cheren_g013_loss_allowed(self):
        self.assertEqual(self.event(1,"BIANCA")["battle_policy"],"ADVANCE_ON_LOSS")
        self.assertEqual(self.event(1,"CHEREN")["battle_policy"],"ADVANCE_ON_LOSS")
    def test_010_ch01_n_requires_win_g013(self):
        self.assertEqual(self.event(1,"N")["battle_policy"],"WIN_REQUIRED")
    def test_011_ch01_gh_starts_as_speech_not_battle(self):
        self.assertEqual(self.event(1,"GHETSIS")["battle_policy"],"NO_BATTLE")
    def test_012_ch11_n_gh_are_g023_links(self):
        self.assertEqual(self.event(11,"N")["source_event_key"],"UNOVA_G023_N_BATTLE")
        self.assertEqual(self.event(11,"GHETSIS")["source_event_key"],
                         "UNOVA_G023_GHETSIS_BATTLE")
    def test_013_only_ch02_ch09_slots_are_planned(self):
        self.assertEqual({e["chapter_index"] for e in self.planned},
                         set(range(2,10)))
    def test_014_actors_have_stable_distinct_team_variant_keys(self):
        variants=[e["team_variant_key"] for e in self.catalog["encounters"]]
        self.assertEqual(len(variants),len(set(variants)))
    def test_015_fabricated_reward_intent_only_for_planned_wins(self):
        self.assertTrue(all(e["reward_intent_token"] is not None for e in self.planned))
        self.assertTrue(all(e["reward_intent_token"] is None for e in self.linked))
    def test_016_never_installed_no_boss_pbs(self):
        self.assertFalse(self.catalog["trainer_pbs_compiled"])
        self.assertFalse(self.catalog["can_install"])
    def test_017_g032_difficulty_shared_not_arbitrary(self):
        self.assertEqual(self.catalog["team_scaling"]["normal_percent"],70)
        self.assertEqual(self.catalog["team_scaling"]["master_percent"],90)
    def test_018_initial_state_has_empty_receipts(self):
        env=g.initial(self.ctx)
        self.assertEqual(env["battle_receipts"],[])
        self.assertEqual(env["reward_intents"],[])
        self.assertEqual(env["rematch_receipts"],[])
    def test_019_ch00_fresh_validates_full_g02_stack(self):
        env=self.env("CH00")
        self.assertEqual(g.validate_envelope(env,self.ctx,self.gyms,self.finale,
                         self.post,self.catalog)["chapter_index"],0)
    def test_020_ch01_requires_source_record_before_inspect_passes(self):
        env=self.env("CH01_START")
        self.assertFalse(self.source(self.event(1,"N"),env)["authoritative_source_recorded"])
    def test_021_ch01_source_links_become_readable_after_u07(self):
        env=self.env("CH01_COMPLETE_EVENTS")
        self.assertTrue(all(self.source(e,env)["authoritative_source_recorded"]
                            for e in self.linked if e["chapter_index"]==1))
    def test_022_ch11_source_links_readable_after_finals(self):
        env=self.env("CH11_CASTLE_DONE")
        self.assertTrue(self.source(self.event(11,"N"),env)["authoritative_source_recorded"])
        self.assertTrue(self.source(self.event(11,"GHETSIS"),env)["authoritative_source_recorded"])
    def test_023_source_inspection_is_read_only(self):
        env=self.env("CH01_COMPLETE_EVENTS")
        response=self.source(self.event(1,"BIANCA"),env)
        self.assertEqual(response["envelope"],env)
        self.assertEqual(response["status"],"SOURCE_RECORDED_OFFLINE")
    def test_024_g013_bianca_cannot_be_rerecorded(self):
        self.deny(self.env("CH01_COMPLETE_EVENTS"),"record_battle",
                  encounter_key=self.event(1,"BIANCA")["id"],outcome="WIN")
    def test_025_g013_n_cannot_be_rerecorded(self):
        self.deny(self.env("CH01_COMPLETE_EVENTS"),"record_battle",
                  encounter_key=self.event(1,"N")["id"],outcome="WIN")
    def test_026_g023_n_cannot_be_rerecorded(self):
        self.deny(self.env("CH11_CASTLE_DONE"),"record_battle",
                  encounter_key=self.event(11,"N")["id"],outcome="WIN")
    def test_027_g023_ghetsis_cannot_be_rerecorded(self):
        self.deny(self.env("CH11_CASTLE_DONE"),"record_battle",
                  encounter_key=self.event(11,"GHETSIS")["id"],outcome="WIN")
    def test_028_cannot_inspect_planned_as_authoritative_source(self):
        self.deny(self.env("CH02_START"),"inspect_linked",
                  encounter_key=self.event(2,"CHEREN")["id"])
    def test_029_ch02_first_planned_win(self):
        env=self.env("CH02_START")
        out=self.act(env,"record_battle",
                     encounter_key=self.event(2,"CHEREN")["id"],outcome="WIN")
        self.assertEqual(out["status"],g.APPLIED)
        self.assertEqual(len(out["envelope"]["battle_receipts"]),1)
    def test_030_ch02_loss_does_not_advance(self):
        env=self.env("CH02_START")
        out=self.act(env,"record_battle",
            encounter_key=self.event(2,"CHEREN")["id"],outcome="LOSS")
        self.assertEqual(out["status"],g.LOSS)
        self.assertEqual(out["envelope"],env)
    def test_031_ch02_repeated_loss_retriable(self):
        env=self.env("CH02_START")
        for _ in range(3):
            env2=self.act(env,"record_battle",encounter_key=self.event(2,"CHEREN")["id"],
                          outcome="LOSS")["envelope"]
            self.assertEqual(env2,env)
    def test_032_ch02_loss_followed_by_win(self):
        env=self.env("CH02_START")
        loss=self.act(env,"record_battle",
            encounter_key=self.event(2,"CHEREN")["id"],outcome="LOSS")
        win=self.act(loss["envelope"],"record_battle",
            encounter_key=self.event(2,"CHEREN")["id"],outcome="WIN")
        self.assertEqual(win["status"],g.APPLIED)
    def test_033_ch02_identical_replay_noop(self):
        env=self.env("CH02_STORY_DONE")
        r=self.act(env,"record_battle",
            encounter_key=self.event(2,"CHEREN")["id"],outcome="WIN")
        self.assertEqual(r["status"],g.REPLAY)
        self.assertEqual(r["envelope"],env)
    def test_034_win_cannot_be_changed_to_loss(self):
        self.deny(self.env("CH02_STORY_DONE"),"record_battle",
            encounter_key=self.event(2,"CHEREN")["id"],outcome="LOSS")
    def test_035_skip_to_future_chapter_event_denied(self):
        self.deny(self.env("CH02_START"),"record_battle",
            encounter_key=self.event(7,"N")["id"],outcome="WIN")
    def test_036_outcome_draw_denied(self):
        self.deny(self.env("CH02_START"),"record_battle",
            encounter_key=self.event(2,"CHEREN")["id"],outcome="DRAW")
    def test_037_missing_outcome_denied(self):
        self.deny(self.env("CH02_START"),"record_battle",
                  encounter_key=self.event(2,"CHEREN")["id"])
    def test_038_unknown_event_denied(self):
        self.deny(self.env("CH02_START"),"record_battle",
                  encounter_key="UNOVA_G033_FANTASY",outcome="WIN")
    def test_039_reward_intent_exactly_once(self):
        env=self.env("CH02_STORY_DONE")
        self.assertEqual(len(env["reward_intents"]),1)
        self.assertEqual(env["reward_intents"][0]["category"],g.REWARD_SCOPE)
        self.assertEqual(env["reward_intents"][0]["amount"],1)
    def test_040_intents_are_not_inventory_grants(self):
        out=self.act(self.env("CH02_START"),"record_battle",
                     encounter_key=self.event(2,"CHEREN")["id"],outcome="WIN")
        self.assertFalse(out["native_rewards_granted"])
        self.assertFalse(out["native_saves_modified"])
    def test_041_cannot_complete_ch02_without_cheren(self):
        self.deny(self.env("CH02_START"),"complete_gym",
                  simulation_gate=machine.SIMULATION_GATE)
    def test_042_cannot_complete_without_gym_battle(self):
        self.deny(self.env("CH02_STORY_DONE"),"complete_gym",
                  simulation_gate=machine.SIMULATION_GATE)
    def test_043_ch02_can_complete_with_battle_and_gym(self):
        result=self.act(self.env("CH02_READY_TO_COMPLETE"),"complete_gym",
            simulation_gate=machine.SIMULATION_GATE)
        self.assertEqual(result["status"],g.APPLIED)
    def test_044_gym_completion_requires_explicit_synthetic_gate(self):
        self.deny(self.env("CH02_READY_TO_COMPLETE"),"complete_gym")
    def test_045_real_game_approval_token_blocked(self):
        self.deny(self.env("CH02_READY_TO_COMPLETE"),"complete_gym",
                  simulation_gate="GAME_EXE_APPROVED")
    def test_046_advance_requires_gym_completion(self):
        self.deny(self.env("CH02_READY_TO_COMPLETE"),"advance_gym")
    def test_047_advance_after_ch02_completed(self):
        out=self.act(self.env("CH02_CHAPTER_COMPLETED"),"advance_gym")
        self.assertEqual(out["status"],g.APPLIED)
        self.assertEqual(g._state_index(out["envelope"],self.ctx),3)
    def test_048_all_eight_chapter_gates_complete(self):
        for ch in range(2,10):
            with self.subTest(chapter=ch):
                r=self.act(self.env(f"CH{ch:02d}_READY_TO_COMPLETE"),
                           "complete_gym",simulation_gate=machine.SIMULATION_GATE)
                self.assertEqual(r["status"],g.APPLIED)
    def test_049_all_eight_chapter_gates_advance(self):
        for ch in range(2,10):
            with self.subTest(chapter=ch):
                r=self.act(self.env(f"CH{ch:02d}_CHAPTER_COMPLETED"),"advance_gym")
                self.assertEqual(g._state_index(r["envelope"],self.ctx),ch+1)
    def test_050_chapter_gates_cannot_be_called_at_ch01(self):
        self.deny(self.env("CH01_COMPLETE_EVENTS"),"advance_gym")
    def test_051_chapter_gates_cannot_be_called_in_league(self):
        self.deny(self.env("CH10_LEAGUE"),"advance_gym")
    def test_052_chapter_gates_cannot_be_called_in_castle(self):
        self.deny(self.env("CH11_CASTLE_DONE"),"complete_gym",
                  simulation_gate=machine.SIMULATION_GATE)
    def test_053_chapter_gates_cannot_be_called_in_postgame(self):
        self.deny(self.env(),"advance_gym")
    def test_054_ch05_bianca_precedes_cheren_in_catalog(self):
        self.assertEqual([x["actor_key"] for x in self.planned
              if x["chapter_index"]==5],["BIANCA","CHEREN"])
    def test_055_ch02_ch09_all_nine_receipts_proven(self):
        env=self.env("CH10_LEAGUE")
        self.assertEqual(len(env["battle_receipts"]),9)
        self.assertEqual(len(env["reward_intents"]),9)
    def test_056_full_campaign_g03_does_not_mutate_g02_receipts(self):
        full=self.env()
        self.assertEqual(len(full["g024_envelope"]["g023_envelope"]["g02_envelope"][
                         "story_receipts"]),40)
    def test_057_full_campaign_g03_preserves_g013_u07_receipts(self):
        self.assertEqual(len(g._g01(self.env())["event_receipts"]),13)
    def test_058_g033_ledger_keeps_boss_n_and_ghetsis_linked_only(self):
        env=self.env()
        self.assertNotIn(self.event(11,"N")["id"],
                         [r["event_key"] for r in env["battle_receipts"]])
        self.assertNotIn(self.event(11,"GHETSIS")["id"],
                         [r["event_key"] for r in env["battle_receipts"]])
    def test_059_g023_credits_prove_postgame_entry(self):
        env=self.env()
        proof=g.validate_envelope(env,self.ctx,self.gyms,self.finale,self.post,self.catalog)
        self.assertEqual(proof["chapter_index"],12)
        self.assertEqual(proof["planned_battle_wins"],9)
    def test_060_source_replay_after_chapter_advance_is_readonly(self):
        env=self.env("CH10_LEAGUE")
        e=self.event(2,"CHEREN")
        self.assertEqual(self.act(env,"record_battle",
            encounter_key=e["id"],outcome="WIN")["status"],g.REPLAY)
    def test_061_postgame_rematch_bianca_first_session(self):
        env=self.env()
        out=self.act(env,"rematch",actor_key="BIANCA",session_id=1,outcome="WIN")
        self.assertEqual(out["status"],g.APPLIED)
        self.assertEqual(out["envelope"]["rematch_receipts"][0]["actor_key"],"BIANCA")
    def test_062_postgame_rematch_cheren_first_session(self):
        env=self.env()
        out=self.act(env,"rematch",actor_key="CHEREN",session_id=1,outcome="WIN")
        self.assertEqual(out["status"],g.APPLIED)
    def test_063_postgame_loss_is_safe_noop(self):
        env=self.env()
        out=self.act(env,"rematch",actor_key="CHEREN",session_id=1,outcome="LOSS")
        self.assertEqual(out["status"],g.LOSS)
        self.assertEqual(out["envelope"],env)
    def test_064_postgame_loss_then_win(self):
        env=self.env()
        loss=self.act(env,"rematch",actor_key="CHEREN",session_id=1,outcome="LOSS")
        win=self.act(loss["envelope"],"rematch",
                     actor_key="CHEREN",session_id=1,outcome="WIN")
        self.assertEqual(win["status"],g.APPLIED)
    def test_065_postgame_rematch_replay_once(self):
        env=self.act(self.env(),"rematch",actor_key="CHEREN",
                     session_id=1,outcome="WIN")["envelope"]
        win=self.act(env,"rematch",actor_key="CHEREN",session_id=1,outcome="WIN")
        self.assertEqual(win["status"],g.REPLAY)
        self.assertEqual(win["envelope"],env)
    def test_066_postgame_replay_cannot_reverse_win_to_loss(self):
        env=self.act(self.env(),"rematch",actor_key="CHEREN",
                     session_id=1,outcome="WIN")["envelope"]
        self.deny(env,"rematch",actor_key="CHEREN",session_id=1,outcome="LOSS")
    def test_067_postgame_rematch_sequential_sessions(self):
        env=self.env()
        for sid in range(1,9):
            env=self.act(env,"rematch",actor_key="BIANCA",
                         session_id=sid,outcome="WIN")["envelope"]
        self.assertEqual(len(env["rematch_receipts"]),8)
    def test_068_postgame_rematch_more_than_eight_blocked(self):
        env=self.env()
        for sid in range(1,9):
            env=self.act(env,"rematch",actor_key="BIANCA",
                         session_id=sid,outcome="WIN")["envelope"]
        self.deny(env,"rematch",actor_key="BIANCA",session_id=9,outcome="WIN")
    def test_069_postgame_rematch_skip_session_blocked(self):
        self.deny(self.env(),"rematch",actor_key="BIANCA",
                  session_id=2,outcome="WIN")
    def test_070_postgame_rematch_no_n(self):
        self.deny(self.env(),"rematch",actor_key="N",session_id=1,outcome="WIN")
    def test_071_postgame_rematch_no_ghetsis(self):
        self.deny(self.env(),"rematch",actor_key="GHETSIS",session_id=1,outcome="WIN")
    def test_072_postgame_rematch_no_grunt(self):
        self.deny(self.env(),"rematch",actor_key="PLASMA_GRUNT",
                  session_id=1,outcome="WIN")
    def test_073_no_rematch_in_ch10_league(self):
        self.deny(self.env("CH10_LEAGUE"),"rematch",
                  actor_key="CHEREN",session_id=1,outcome="WIN")
    def test_074_no_rematch_in_ch11_castle(self):
        self.deny(self.env("CH11_CASTLE_DONE"),"rematch",
                  actor_key="CHEREN",session_id=1,outcome="WIN")
    def test_075_no_rematch_before_first_planned_victory(self):
        env=self.env()
        env["battle_receipts"]=[r for r in env["battle_receipts"]
                                  if not r["event_key"].endswith("_BIANCA")]
        env["reward_intents"]=[r for r in env["reward_intents"]
             if not r["source_event"].endswith("_BIANCA")]
        self.deny(env,"rematch",actor_key="BIANCA",session_id=1,outcome="WIN")
    def test_076_rematch_id_boolean_rejected(self):
        self.deny(self.env(),"rematch",actor_key="CHEREN",
                  session_id=True,outcome="WIN")
    def test_077_rematch_id_negative_rejected(self):
        self.deny(self.env(),"rematch",actor_key="CHEREN",
                  session_id=-1,outcome="WIN")
    def test_078_rematch_unknown_result_rejected(self):
        self.deny(self.env(),"rematch",actor_key="CHEREN",
                  session_id=1,outcome="DRAW")
    def test_079_rematch_requires_three_documented_args(self):
        self.deny(self.env(),"rematch",actor_key="CHEREN",session_id=1)
    def test_080_rematch_second_rival_independent_counter(self):
        env=self.act(self.env(),"rematch",actor_key="CHEREN",
                     session_id=1,outcome="WIN")["envelope"]
        env=self.act(env,"rematch",actor_key="BIANCA",
                     session_id=1,outcome="WIN")["envelope"]
        self.assertEqual([r["session_id"] for r in env["rematch_receipts"]],[1,1])
    def test_081_reenter_previous_chapter_read_only(self):
        env=self.env("CH10_LEAGUE")
        r=self.act(env,"reenter",chapter_key=self.ctx[0]["chapters"][5]["key"])
        self.assertEqual(r["status"],g.REENTER)
        self.assertEqual(r["envelope"],env)
    def test_082_postgame_reenter_chapter_one_safe(self):
        env=self.env()
        r=self.act(env,"reenter",chapter_key=self.ctx[0]["chapters"][1]["key"])
        self.assertEqual(r["status"],g.REENTER)
        self.assertEqual(r["envelope"],env)
    def test_083_reenter_future_chapter_rejected(self):
        self.deny(self.env("CH02_START"),"reenter",
                  chapter_key=self.ctx[0]["chapters"][9]["key"])
    def test_084_reenter_unknown_chapter_rejected(self):
        self.deny(self.env(),"reenter",chapter_key="UNOVA_CH999")
    def test_085_plan_normal_level_70_percent(self):
        r=self.team()
        self.assertEqual((r["percent"],r["target_synthetic_level"]),(70,28))
        self.assertFalse(r["native_team_verified"])
    def test_086_plan_master_level_90_percent(self):
        r=self.team(story_stage=3)
        self.assertEqual((r["percent"],r["target_synthetic_level"]),(90,36))
        self.assertEqual(r["synthetic_target_team_size"],4)
    def test_087_plan_ignores_eggs(self):
        r=self.team(party=[{"level":30,"egg":False},{"level":99,"egg":True}])
        self.assertEqual(r["target_synthetic_level"],21)
    def test_088_plan_missing_authored_size_remains_null(self):
        r=self.team(synthetic_authored_team_size=None,story_stage=3)
        self.assertIsNone(r["synthetic_target_team_size"])
        self.assertIsNone(r["missing_master_slots"])
    def test_089_plan_master_preserves_team_five(self):
        r=self.team(story_stage=3,synthetic_authored_team_size=5)
        self.assertEqual(r["synthetic_target_team_size"],5)
    def test_090_plan_native_levels_never_proven(self):
        r=self.team(story_stage=3)
        self.assertFalse(r["native_evolutions_applied"])
        self.assertFalse(r["native_weakness_coverage_verified"])
        self.assertIsNone(r["canonical_team"])
    def test_091_plan_wrong_chapter_rejected(self):
        with self.assertRaises(ValueError):
            self.team(encounter_key=self.event(7,"N")["id"])
    def test_092_plan_gh_speech_cannot_be_team(self):
        with self.assertRaises(ValueError):
            self.team(self.env("CH01_COMPLETE_EVENTS"),
                      encounter_key=self.event(1,"GHETSIS")["id"])
    def test_093_plan_bad_story_stage_rejected(self):
        with self.assertRaises(ValueError):
            self.team(story_stage=4)
    def test_094_plan_invalid_synthetic_team_size_rejected(self):
        with self.assertRaises(ValueError):
            self.team(synthetic_authored_team_size=7)
    def test_095_plan_native_pokemon_party_shape_rejected(self):
        with self.assertRaises(ValueError):
            self.team(party=[{"species":"TURTWIG","level":30,"egg":False}])
    def test_096_plan_engine_max_not_hardcoded(self):
        r=self.team(engine_max_level=50,party=[{"level":50,"egg":False}])
        self.assertEqual(r["target_synthetic_level"],35)
    def test_097_g013_layer_roundtrip_g014_projection(self):
        env=self.env()
        old=g._g01(env)
        encoded=codec.encode_current(old,self.ctx)
        self.assertEqual(codec.decode_current(encoded,self.ctx),old)
    def test_098_cannot_serialize_g033_directly_in_g014(self):
        with self.assertRaises(ValueError):
            codec.encode_current(self.env(),self.ctx)
    def test_099_forged_battle_outcome_rejected(self):
        self.bad_state(lambda x:x["battle_receipts"][0].update(outcome="LOSS"))
    def test_100_duplicate_battle_receipt_rejected(self):
        self.bad_state(lambda x:x["battle_receipts"].append(
            copy.deepcopy(x["battle_receipts"][0])))
    def test_101_forged_reward_intent_token_rejected(self):
        self.bad_state(lambda x:x["reward_intents"][0].update(token="REAL_RARE_CANDY"))
    def test_102_removed_reward_intent_rejected(self):
        self.bad_state(lambda x:x["reward_intents"].pop())
    def test_103_forged_native_reward_rejected(self):
        self.bad_state(lambda x:x.update(inventory={"POTION":1}))
    def test_104_future_battle_receipt_in_past_chapter_rejected(self):
        env=self.env("CH02_START")
        env["battle_receipts"].append(copy.deepcopy(self.env()["battle_receipts"][-1]))
        with self.assertRaises(ValueError):
            g.validate_envelope(env,self.ctx,self.gyms,self.finale,self.post,self.catalog)
    def test_105_misordered_battle_receipts_rejected(self):
        self.bad_state(lambda x:x["battle_receipts"].reverse())
    def test_106_forged_team_variant_rejected(self):
        self.bad_state(lambda x:x["battle_receipts"][0].update(team_variant_key="FAKE"))
    def test_107_future_schema_rejected(self):
        self.bad_state(lambda x:x.update(schema=2))
    def test_108_cross_region_state_rejected(self):
        self.bad_state(lambda x:x.update(region="SINNOH"))
    def test_109_wrong_scope_native_save_rejected(self):
        self.bad_state(lambda x:x.update(scope="NATIVE_SAVE"))
    def test_110_forged_duplicate_rematch_rejected(self):
        env=self.act(self.env(),"rematch",actor_key="CHEREN",
                     session_id=1,outcome="WIN")["envelope"]
        env["rematch_receipts"].append(copy.deepcopy(env["rematch_receipts"][0]))
        with self.assertRaises(ValueError):
            g.validate_envelope(env,self.ctx,self.gyms,self.finale,self.post,self.catalog)
    def test_111_forged_rematch_no_original_win_rejected(self):
        env=self.act(self.env(),"rematch",actor_key="CHEREN",
                     session_id=1,outcome="WIN")["envelope"]
        env["rematch_receipts"][0]["outcome"]="LOSS"
        with self.assertRaises(ValueError):
            g.validate_envelope(env,self.ctx,self.gyms,self.finale,self.post,self.catalog)
    def test_112_forged_native_team_contract_rejected(self):
        self.bad_catalog(lambda c:c["encounters"][4].update(canonical_team=["PATRAT"]))
    def test_113_forged_map_id_contract_rejected(self):
        self.bad_catalog(lambda c:c["encounters"][5].update(native_map_id=518))
    def test_114_forged_native_trainer_pbs_rejected(self):
        self.bad_catalog(lambda c:c["encounters"][6].update(trainer_pbs_id="PLASMA"))
    def test_115_duplicate_chapter_encounter_contract_rejected(self):
        self.bad_catalog(lambda c:c["encounters"].append(copy.deepcopy(c["encounters"][4])))
    def test_116_noncanonical_bianca_battle_policy_rejected(self):
        self.bad_catalog(lambda c:c["encounters"][0].update(battle_policy="WIN_REQUIRED"))
    def test_117_wrong_finale_authoritative_link_rejected(self):
        self.bad_catalog(lambda c:c["encounters"][-1].update(
            source_event_key="UNOVA_G023_N_BATTLE"))
    def test_118_forged_predecessor_link_rejected(self):
        self.bad_catalog(lambda c:c["encounters"][7].update(required_prior_events=[]))
    def test_119_fake_reward_native_claim_rejected(self):
        self.bad_catalog(lambda c:c.update(can_install=True))
    def test_120_fake_pbs_compiled_claim_rejected(self):
        self.bad_catalog(lambda c:c.update(trainer_pbs_compiled=True))
    def test_121_enable_unaudited_rival_rematches_rejected(self):
        self.bad_catalog(lambda c:c["rematch"].update(
            actors=["BIANCA","CHEREN","N"]))
    def test_122_100_percent_master_not_supported(self):
        self.bad_catalog(lambda c:c["team_scaling"].update(master_percent=100))
    def test_123_invent_bst_level_cap_rejected(self):
        self.bad_catalog(lambda c:c["team_scaling"].update(no_numeric_regional_cap=False))
    def test_124_catalog_wrong_source_path_rejected(self):
        self.bad_catalog(lambda c:c["sources"].update(g01_state="unknown.json"))
    def test_125_catalog_stable_actor_variant_not_reordered(self):
        self.bad_catalog(lambda c:c["encounters"][8].update(
            team_variant_key="UNOVA_G033_TEAM_CHEREN_02"))
    def test_126_catalog_fake_grunt_native_trainer_ref_rejected(self):
        self.bad_catalog(lambda c:c["encounters"][5].update(
            trainer_reference_key="UNOVA_TRAINER_GHETSIS"))
    def test_127_reentry_or_native_claim_not_accepted_as_battle(self):
        self.deny(self.env("CH02_START"),"award_real_pokemon",
                  encounter_key=self.event(2,"CHEREN")["id"])
    def test_128_extra_starter_arg_cannot_modify_event(self):
        self.deny(self.env("CH02_START"),"record_battle",
                  encounter_key=self.event(2,"CHEREN")["id"],
                  outcome="WIN",actor_key="N")
    def test_129_all_results_are_offline(self):
        out=self.act(self.env("CH02_START"),"record_battle",
                     encounter_key=self.event(2,"CHEREN")["id"],outcome="WIN")
        self.assertFalse(out["native_battles_executed"])
        self.assertFalse(out["native_rewards_granted"])
        self.assertFalse(out["game_exe_tested"])
        self.assertFalse(out["can_install"])
    def test_130_cli_check_returns_stable_count(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g03_rivals_plasma.py"),
            "--check"],cwd=ROOT,text=True,capture_output=True,timeout=50)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        self.assertEqual(json.loads(p.stdout)["chapter_encounters"],15)
    def test_131_cli_full_demo_reaches_postgame_without_native(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g03_rivals_plasma.py"),
            "--simulate-demo"],cwd=ROOT,text=True,capture_output=True,timeout=60)
        self.assertEqual(p.returncode,0,p.stderr+p.stdout)
        data=json.loads(p.stdout)
        self.assertEqual(data["planned_battles_recorded"],9)
        self.assertEqual(data["synthetic_rival_rematches"],2)
        self.assertFalse(data["native_rewards_granted"])
    def test_132_replay_of_complete_story_demo(self):
        proof=g.demo(self.ctx,self.gyms,self.finale,self.post,self.balance,self.catalog)
        self.assertEqual(proof["chapter"],"UNOVA_CH12_POSTGAME")
        self.assertEqual(proof["read_only_linked_events"],6)

if __name__=="__main__":
    unittest.main()
