"""G03.4 Unova Elite Four/Alder offline variants, G02.4 delegation and guards."""
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
import audit_unova_g03_elite_alder as elite
import audit_unova_g03_rivals_plasma as rivals
import audit_unova_g01_chapter_machine as g01
import audit_unova_g01_serialization as codec

class UnovaG034Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx,cls.gyms,cls.finale,cls.post,cls.scale,cls.rival,cls.catalog=elite.load_project()
        cls.actors=[x["name"] for x in cls.catalog["actors"]]
        cls.finish,cls.story=rivals.build_demo(
            cls.ctx,cls.gyms,cls.finale,cls.post,cls.scale,cls.rival)
        cls.fixtures={}
        env=copy.deepcopy(cls.story["CH12_POSTGAME"])
        cls.fixtures["postgame"]=copy.deepcopy(env)
        def run(action,**kw):
            nonlocal env
            result=elite.step_rematch(env,cls.ctx,cls.gyms,cls.finale,
                                      cls.post,cls.rival,cls.catalog,action,
                                      session_id=1,**kw)
            env=result["envelope"]
            return result
        run("start");cls.fixtures["active"]=copy.deepcopy(env)
        for i,name in enumerate(cls.actors[:4],1):
            run("battle",actor_name=name,outcome="WIN")
            cls.fixtures["elite"+str(i)]=copy.deepcopy(env)
        run("battle",actor_name="ALDER",outcome="WIN")
        cls.fixtures["alder"]=copy.deepcopy(env)
        run("finish")
        cls.fixtures["done"]=copy.deepcopy(env)

    def fixture(self,label="postgame"):return copy.deepcopy(self.fixtures[label])
    def story_fixture(self,label="CH10_LEAGUE"):
        return copy.deepcopy(self.story[label])
    def act(self,env,action,session=1,**kw):
        return elite.step_rematch(env,self.ctx,self.gyms,self.finale,self.post,
                                  self.rival,self.catalog,action,session_id=session,**kw)
    def denied(self,env,action,session=1,**kw):
        original=copy.deepcopy(env)
        with self.assertRaises(ValueError):self.act(env,action,session,**kw)
        self.assertEqual(env,original)
    def plan(self,env=None,**kwargs):
        args={"actor_name":"SHAUNTAL","mode":"CAMPAIGN",
            "party":[{"level":40,"egg":False}],
            "engine_max_level":100,"story_stage":0,
            "synthetic_authored_team_size":None}
        args.update(kwargs)
        return elite.plan_team(env if env is not None else self.story_fixture(),
                               self.ctx,self.gyms,self.finale,self.post,
                               self.rival,self.scale,self.catalog,**args)
    def rejected_plan(self,env=None,**kwargs):
        with self.assertRaises(ValueError):self.plan(env,**kwargs)
    def broken_catalog(self,change):
        data=copy.deepcopy(self.catalog);change(data)
        npc=g01._safe_source(ROOT/data["sources"]["npc"])
        trainers=g01._safe_source(ROOT/data["sources"]["trainer"])
        with self.assertRaises(ValueError):
            elite.validate_catalog(data,self.ctx,self.finale,self.post,
                                   self.scale,self.rival,npc,trainers)
    def source_pokemons(self):
        return {"attack_types":["FIRE","GROUND"],
            "party":[{"species":"FIXTURE_WALL_TARGET","types":["GRASS"],
                      "multipliers":{"FIRE":2,"GROUND":2}}],
            "candidates":[
              {"species":"FIXTURE_WATER_WALL","types":["WATER"],"bst":480,
               "multipliers":{"FIRE":0.5,"GROUND":0.5},
               "synthetic_only":True,"special_flags":[]},
              {"species":"FIXTURE_ICE_TARGET","types":["ICE"],"bst":480,
               "multipliers":{"FIRE":2,"GROUND":2},
               "synthetic_only":True,"special_flags":[]}]}

    def test_001_region_white_only(self):
        self.assertEqual((self.catalog["region"],self.catalog["campaign"]),
                         ("UNOVA","WHITE_BW"))
    def test_002_exactly_four_elite_and_alder(self):
        self.assertEqual(self.actors,["SHAUNTAL","GRIMSLEY","CAITLIN","MARSHAL","ALDER"])
    def test_003_four_elite_any_order(self):
        self.assertEqual(self.catalog["campaign_order"],"ANY_ORDER_FOUR_ELITE_NO_ALDER")
        self.assertEqual(self.catalog["rematch_order"],"ANY_ORDER_FOUR_ELITE_THEN_ALDER")
    def test_004_nineteen_stable_variants(self):
        self.assertEqual(sum(len(a["variants"]) for a in self.catalog["actors"]),19)
    def test_005_variant_keys_unique(self):
        keys=[v["key"] for a in self.catalog["actors"] for v in a["variants"]]
        self.assertEqual(len(keys),len(set(keys)))
    def test_006_alder_not_initial_campaign_actor(self):
        self.assertIsNone(self.catalog["actors"][-1]["source_campaign_key"])
        self.assertNotIn("CAMPAIGN",[v["mode"] for v in self.catalog["actors"][-1]["variants"]])
    def test_007_canonical_e07_teams_remain_unverified(self):
        self.assertTrue(all(a["real_team"] is None and a["real_levels"] is None and
            a["real_moves"] is None and a["native_trainer_id"] is None
            for a in self.catalog["actors"]))
    def test_008_all_variants_have_no_native_pbs(self):
        self.assertTrue(all(v["native_pbs_id"] is None and v["real_team"] is None
                            and v["real_levels"] is None and not v["source_verified"]
                            for a in self.catalog["actors"] for v in a["variants"]))
    def test_009_original_source_g023_for_elite(self):
        self.assertEqual([a["source_campaign_key"] for a in self.catalog["actors"][:4]],
                         [x["key"] for x in self.finale["elite_members"]])
    def test_010_g024_source_for_rematches(self):
        self.assertEqual([a["source_rematch_key"] for a in self.catalog["actors"][:4]],
                         self.post["league_rematch"]["elite_members"])
        self.assertEqual(self.catalog["actors"][-1]["source_rematch_key"],"ALDER")
    def test_011_no_duplicated_reward_ledger(self):
        self.assertEqual(self.catalog["reward_policy"],
                         "NO_NATIVE_REWARDS_OR_SECOND_BADGES")
    def test_012_no_real_team_compilation(self):
        self.assertFalse(self.catalog["real_pbs_compiled"])
        self.assertFalse(self.catalog["can_install"])
    def test_013_full_power_policy_defaults_fail_closed(self):
        self.assertFalse(self.catalog["full_power_policy"]["enabled"])
        self.assertIsNone(self.catalog["full_power_policy"]["verified_team_source"])
        self.assertTrue(self.catalog["full_power_policy"]["requires_ten_league_titles"])
    def test_014_first_elite_ch10_70_percent(self):
        r=self.plan()
        self.assertEqual(r["synthetic_target_level"],28)
        self.assertEqual(r["scale_percent"],70)
    def test_015_first_elite_stage_three_master(self):
        r=self.plan(story_stage=3)
        self.assertEqual(r["synthetic_target_level"],36)
        self.assertEqual(r["difficulty"],"MASTER")
    def test_016_first_elite_unknown_team_size_preserved(self):
        r=self.plan(story_stage=3)
        self.assertIsNone(r["synthetic_target_team_size"])
        self.assertIsNone(r["synthetic_missing_slots"])
    def test_017_synthetic_master_size_three_four(self):
        r=self.plan(story_stage=3,synthetic_authored_team_size=3)
        self.assertEqual(r["synthetic_target_team_size"],4)
        self.assertEqual(r["synthetic_missing_slots"],1)
        self.assertFalse(r["native_team_generated"])
    def test_018_synthetic_master_preserves_team_five(self):
        r=self.plan(story_stage=3,synthetic_authored_team_size=5)
        self.assertEqual(r["synthetic_target_team_size"],5)
    def test_019_normal_size_two_unchanged(self):
        r=self.plan(synthetic_authored_team_size=2)
        self.assertEqual(r["synthetic_target_team_size"],2)
    def test_020_stage_one_two_are_normal_70_percent(self):
        for stage in (1,2):
            with self.subTest(stage=stage):
                self.assertEqual(self.plan(story_stage=stage)["scale_percent"],70)
    def test_021_first_elite_from_all_four_members(self):
        for name in self.actors[:4]:
            with self.subTest(name=name):
                r=self.plan(actor_name=name)
                self.assertEqual(r["actor_id"],"UNOVA_G034_ACTOR_"+name)
    def test_022_no_alder_campaign_at_ch10(self):
        self.rejected_plan(actor_name="ALDER",mode="CAMPAIGN")
    def test_023_no_canonical_team_in_preview(self):
        r=self.plan()
        self.assertIsNone(r["canonical_species"])
        self.assertIsNone(r["canonical_moves"])
        self.assertIsNone(r["canonical_levels"])
    def test_024_no_native_badge_reward(self):
        r=self.plan()
        self.assertFalse(r["real_rewards_granted"])
        self.assertFalse(r["native_pbs_mutated"])
        self.assertFalse(r["native_evolution_applied"])
    def test_025_initial_chapter_nine_cannot_fight_elite(self):
        self.rejected_plan(self.story_fixture("CH09_START"))
    def test_026_initial_chapter_one_cannot_fight_elite(self):
        self.rejected_plan(self.story_fixture("CH01_START"))
    def test_027_no_campaign_replay_after_win_recorded(self):
        env=self.story_fixture()
        out=self.finale["elite_members"][0]
        from audit_unova_g02_elite_finale import apply as finale_apply
        r=finale_apply(env["g024_envelope"]["g023_envelope"],
            self.ctx,self.gyms,self.finale,"elite_battle",
            member_key=out["key"],outcome="WIN")
        env["g024_envelope"]["g023_envelope"]=r["envelope"]
        self.rejected_plan(env,actor_name="SHAUNTAL")
    def test_028_postgame_cannot_issue_first_campaign_plan(self):
        self.rejected_plan(self.fixture(),actor_name="SHAUNTAL",mode="CAMPAIGN")
    def test_029_campaign_inspection_before_win(self):
        r=elite.inspect_campaign(self.story_fixture(),self.ctx,self.gyms,
            self.finale,self.post,self.rival,self.catalog,actor_name="SHAUNTAL")
        self.assertEqual(r["status"],"AVAILABLE_UNPROVEN_NATIVE")
    def test_030_campaign_inspection_after_complete(self):
        r=elite.inspect_campaign(self.fixture(),self.ctx,self.gyms,
            self.finale,self.post,self.rival,self.catalog,actor_name="SHAUNTAL")
        self.assertEqual(r["status"],"WIN_RECORDED_IN_G02_3")
    def test_031_campaign_inspection_alder_refused(self):
        with self.assertRaises(ValueError):
            elite.inspect_campaign(self.fixture(),self.ctx,self.gyms,self.finale,
                                   self.post,self.rival,self.catalog,actor_name="ALDER")
    def test_032_unknown_member_rejected(self):
        self.rejected_plan(actor_name="GHETSIS",mode="CAMPAIGN")
    def test_033_campaign_starts_with_no_team_size_guess(self):
        r=self.plan()
        self.assertIsNone(r["synthetic_authored_team_size"])
    def test_034_all_eggs_safe_fallback_one(self):
        r=self.plan(party=[{"level":100,"egg":True}])
        self.assertEqual(r["synthetic_target_level"],1)
        self.assertTrue(r["no_non_egg_fallback"])
    def test_035_egg_with_high_level_ignored(self):
        r=self.plan(party=[{"level":30,"egg":False},{"level":99,"egg":True}])
        self.assertEqual(r["synthetic_target_level"],21)
    def test_036_engine_max_explicit_and_not_hardcoded(self):
        r=self.plan(engine_max_level=60,party=[{"level":60,"egg":False}])
        self.assertEqual(r["synthetic_target_level"],42)
    def test_037_bad_engine_max_rejected(self):
        self.rejected_plan(engine_max_level=0)
    def test_038_level_over_engine_limit_rejected(self):
        self.rejected_plan(engine_max_level=30)
    def test_039_bad_story_stage_rejected(self):
        self.rejected_plan(story_stage=5)
    def test_040_synthetic_size_larger_six_rejected(self):
        self.rejected_plan(synthetic_authored_team_size=7)
    def test_041_pokemon_species_fake_native_party_rejected(self):
        self.rejected_plan(party=[{"level":30,"egg":False,"species":"RESHIRAM"}])
    def test_042_campaign_full_power_locked_even_with_master(self):
        self.rejected_plan(mode="FULL_POWER_LOCKED",story_stage=3)
    def test_043_no_rematch_before_postgame(self):
        self.rejected_plan(self.story_fixture(),mode="REMATCH_NORMAL")
    def test_044_no_rematch_plan_without_active_session(self):
        self.rejected_plan(self.fixture(),mode="REMATCH_NORMAL")
    def test_045_start_session_one_after_credits(self):
        r=self.act(self.fixture(),"start")
        self.assertEqual(r["status"],"APPLIED_SIMULATION")
        self.assertEqual(r["source_authority"],"G02.4_REMATCH_SESSIONS")
    def test_046_active_normal_rematch_plan(self):
        r=self.plan(self.fixture("active"),mode="REMATCH_NORMAL")
        self.assertEqual(r["scale_percent"],70)
        self.assertEqual(r["variant_key"],"UNOVA_G034_SHAUNTAL_REMATCH_NORMAL")
    def test_047_active_master_rematch_plan(self):
        r=self.plan(self.fixture("active"),mode="REMATCH_MASTER",story_stage=3)
        self.assertEqual(r["scale_percent"],90)
        self.assertEqual(r["variant_key"],"UNOVA_G034_SHAUNTAL_REMATCH_MASTER")
    def test_048_normal_rematch_stage_three_refused(self):
        self.rejected_plan(self.fixture("active"),mode="REMATCH_NORMAL",story_stage=3)
    def test_049_master_rematch_not_stage_three_refused(self):
        self.rejected_plan(self.fixture("active"),mode="REMATCH_MASTER",story_stage=2)
    def test_050_master_rematch_with_synthetic_four_slots(self):
        r=self.plan(self.fixture("active"),mode="REMATCH_MASTER",story_stage=3,
                    synthetic_authored_team_size=1)
        self.assertEqual(r["synthetic_missing_slots"],3)
    def test_051_rematch_unknown_canonical_size_remains_none(self):
        r=self.plan(self.fixture("active"),mode="REMATCH_MASTER",story_stage=3)
        self.assertIsNone(r["synthetic_missing_slots"])
    def test_052_alder_locked_until_four_unique_elite(self):
        self.rejected_plan(self.fixture("elite3"),actor_name="ALDER",mode="REMATCH_NORMAL")
    def test_053_alder_available_after_four_elite(self):
        r=self.plan(self.fixture("elite4"),actor_name="ALDER",mode="REMATCH_NORMAL")
        self.assertEqual(r["actor_id"],"UNOVA_G034_ACTOR_ALDER")
    def test_054_alder_master_stage_three_available(self):
        r=self.plan(self.fixture("elite4"),actor_name="ALDER",
                    mode="REMATCH_MASTER",story_stage=3)
        self.assertEqual(r["scale_percent"],90)
    def test_055_alder_after_win_no_duplicate_team_plan(self):
        self.rejected_plan(self.fixture("alder"),actor_name="ALDER",mode="REMATCH_NORMAL")
    def test_056_already_won_elite_cannot_plan_again(self):
        self.rejected_plan(self.fixture("elite1"),actor_name="SHAUNTAL",mode="REMATCH_NORMAL")
    def test_057_other_elite_remains_available(self):
        r=self.plan(self.fixture("elite1"),actor_name="GRIMSLEY",mode="REMATCH_NORMAL")
        self.assertEqual(r["actor_id"],"UNOVA_G034_ACTOR_GRIMSLEY")
    def test_058_no_full_power_after_credits(self):
        self.rejected_plan(self.fixture("active"),mode="FULL_POWER_LOCKED")
    def test_059_no_full_power_for_alder_after_four_wins(self):
        self.rejected_plan(self.fixture("elite4"),actor_name="ALDER",
                           mode="FULL_POWER_LOCKED")
    def test_060_no_full_power_after_completing_session(self):
        self.rejected_plan(self.fixture("done"),mode="FULL_POWER_LOCKED",story_stage=3)
    def test_061_full_power_cannot_be_enabled_by_extra_client_parameter(self):
        with self.assertRaises(TypeError):
            self.plan(self.fixture("active"),mode="FULL_POWER_LOCKED",
                      world_champion_titles=10)
    def test_062_start_repeated_session_id_noop(self):
        r=self.act(self.fixture("active"),"start")
        self.assertEqual(r["status"],"ALREADY_RECORDED_NO_OP")
    def test_063_second_concurrent_session_denied(self):
        self.denied(self.fixture("active"),"start",session=2)
    def test_064_skip_session_number_denied(self):
        self.denied(self.fixture(),"start",session=2)
    def test_065_boolean_session_id_denied(self):
        self.denied(self.fixture(),"start",session=True)
    def test_066_negative_session_id_denied(self):
        self.denied(self.fixture(),"start",session=-1)
    def test_067_alder_first_battle_denied(self):
        self.denied(self.fixture("active"),"battle",actor_name="ALDER",outcome="WIN")
    def test_068_four_elite_any_first_member(self):
        for name in self.actors[:4]:
            with self.subTest(name=name):
                r=self.act(self.fixture("active"),"battle",actor_name=name,outcome="WIN")
                self.assertEqual(r["status"],"APPLIED_SIMULATION")
    def test_069_all_twenty_four_elite_orders_accepted(self):
        for order in itertools.permutations(self.actors[:4]):
            with self.subTest(order=order):
                env=self.fixture("active")
                for name in order:
                    env=self.act(env,"battle",actor_name=name,outcome="WIN")["envelope"]
                self.assertEqual(len(env["g024_envelope"]["active_rematch"]["elite_wins"]),4)
    def test_070_loss_leaves_session_untouched(self):
        env=self.fixture("active")
        r=self.act(env,"battle",actor_name="SHAUNTAL",outcome="LOSS")
        self.assertEqual(r["status"],"BATTLE_LOST_RETRY_REQUIRED")
        self.assertEqual(r["envelope"],env)
        self.assertFalse(r["native_teleport_executed"])
    def test_071_loss_return_area_is_symbolic_league(self):
        r=self.act(self.fixture("active"),"battle",actor_name="SHAUNTAL",outcome="LOSS")
        self.assertEqual(r["suggested_safe_return_area_key"],"UNOVA_POKEMON_LEAGUE")
    def test_072_loss_then_win_allowed(self):
        env=self.fixture("active")
        env=self.act(env,"battle",actor_name="SHAUNTAL",outcome="LOSS")["envelope"]
        self.assertEqual(self.act(env,"battle",actor_name="SHAUNTAL",
                                  outcome="WIN")["status"],"APPLIED_SIMULATION")
    def test_073_elite_duplicate_win_noop(self):
        r=self.act(self.fixture("elite1"),"battle",actor_name="SHAUNTAL",outcome="WIN")
        self.assertEqual(r["status"],"ALREADY_RECORDED_NO_OP")
    def test_074_elite_win_cannot_become_loss(self):
        self.denied(self.fixture("elite1"),"battle",actor_name="SHAUNTAL",outcome="LOSS")
    def test_075_alder_loss_after_elite_is_noop(self):
        env=self.fixture("elite4")
        r=self.act(env,"battle",actor_name="ALDER",outcome="LOSS")
        self.assertEqual(r["status"],"BATTLE_LOST_RETRY_REQUIRED")
        self.assertEqual(r["envelope"],env)
    def test_076_alder_win_after_four_elite_allowed(self):
        r=self.act(self.fixture("elite4"),"battle",actor_name="ALDER",outcome="WIN")
        self.assertEqual(r["status"],"APPLIED_SIMULATION")
    def test_077_alder_double_win_noop(self):
        r=self.act(self.fixture("alder"),"battle",actor_name="ALDER",outcome="WIN")
        self.assertEqual(r["status"],"ALREADY_RECORDED_NO_OP")
    def test_078_alder_win_cannot_become_loss(self):
        self.denied(self.fixture("alder"),"battle",actor_name="ALDER",outcome="LOSS")
    def test_079_no_finished_session_without_alder(self):
        self.denied(self.fixture("elite4"),"finish")
    def test_080_finish_archives_single_G024_receipt(self):
        env=self.fixture("done")
        sessions=env["g024_envelope"]["rematches_completed"]
        self.assertEqual(len(sessions),1)
        self.assertEqual(sessions[0]["elite_wins"],
                         [x["source_rematch_key"] for x in self.catalog["actors"][:4]])
        self.assertIsNone(env["g024_envelope"]["active_rematch"])
    def test_081_finish_replay_noop(self):
        r=self.act(self.fixture("done"),"finish")
        self.assertEqual(r["status"],"ALREADY_RECORDED_NO_OP")
    def test_082_start_second_session_after_first_finished(self):
        r=self.act(self.fixture("done"),"start",session=2)
        self.assertEqual(r["envelope"]["g024_envelope"]["active_rematch"]["session_id"],2)
    def test_083_second_session_has_empty_elite_again(self):
        env=self.act(self.fixture("done"),"start",session=2)["envelope"]
        self.assertEqual(env["g024_envelope"]["active_rematch"]["elite_wins"],[])
    def test_084_rematch_Does_not_change_G01(self):
        a=rivals._g01(self.fixture("postgame"))
        b=rivals._g01(self.fixture("done"))
        self.assertEqual(a,b)
    def test_085_rematch_does_not_change_G03_3_story_receipts(self):
        self.assertEqual(self.fixture("postgame")["battle_receipts"],
                         self.fixture("done")["battle_receipts"])
    def test_086_rematch_does_not_add_G03_3_reward_intents(self):
        self.assertEqual(self.fixture("postgame")["reward_intents"],
                         self.fixture("done")["reward_intents"])
    def test_087_bad_battle_result_refused(self):
        self.denied(self.fixture("active"),"battle",
                    actor_name="SHAUNTAL",outcome="DRAW")
    def test_088_missing_battle_outcome_refused(self):
        self.denied(self.fixture("active"),"battle",actor_name="SHAUNTAL")
    def test_089_unknown_battle_actor_refused(self):
        self.denied(self.fixture("active"),"battle",actor_name="N",outcome="WIN")
    def test_090_no_start_with_unexpected_actor(self):
        self.denied(self.fixture(),"start",actor_name="ALDER")
    def test_091_no_finish_with_unexpected_outcome(self):
        self.denied(self.fixture("alder"),"finish",outcome="WIN")
    def test_092_rematch_before_credits_denied(self):
        self.denied(self.story_fixture(),"start")
    def test_093_g03_2_coverage_fixture_reused(self):
        r=self.plan(fixture_coverage=self.source_pokemons())
        self.assertEqual(r["fixture_coverage"]["ranked_candidates"][0]["species"],
                         "FIXTURE_WATER_WALL")
        self.assertFalse(r["native_type_coverage_verified"])
    def test_094_coverage_fixture_no_real_team_change(self):
        r=self.plan(fixture_coverage=self.source_pokemons())
        self.assertFalse(r["fixture_coverage"]["can_add_to_real_team"])
        self.assertFalse(r["native_team_generated"])
    def test_095_coverage_fixture_rejects_fake_native_species(self):
        fixture=self.source_pokemons();fixture["candidates"][0]["species"]="HYDREIGON"
        self.rejected_plan(fixture_coverage=fixture)
    def test_096_coverage_fixture_rejects_legendary(self):
        fixture=self.source_pokemons();fixture["candidates"][0]["special_flags"]=["LEGENDARY"]
        self.rejected_plan(fixture_coverage=fixture)
    def test_097_coverage_fixture_rejects_missing_type_multiplier(self):
        fixture=self.source_pokemons();fixture["candidates"][0]["multipliers"].pop("GROUND")
        self.rejected_plan(fixture_coverage=fixture)
    def test_098_coverage_fixture_requires_all_fields(self):
        fixture=self.source_pokemons();fixture.pop("attack_types")
        self.rejected_plan(fixture_coverage=fixture)
    def test_099_coverage_fixture_does_not_mutate_input(self):
        fixture=self.source_pokemons();orig=copy.deepcopy(fixture)
        self.plan(fixture_coverage=fixture)
        self.assertEqual(orig,fixture)
    def test_100_catalog_invented_native_team_refused(self):
        self.broken_catalog(lambda d:d["actors"][0].update(real_team=["CHANDELURE"]))
    def test_101_catalog_invented_native_level_refused(self):
        self.broken_catalog(lambda d:d["actors"][0]["variants"][0].update(real_levels=[49]))
    def test_102_catalog_invented_pbs_id_refused(self):
        self.broken_catalog(lambda d:d["actors"][-1].update(native_trainer_id=100))
    def test_103_catalog_swap_alder_into_initial_elite_refused(self):
        self.broken_catalog(lambda d:d["actors"][0].update(name="ALDER"))
    def test_104_catalog_forged_Alder_campaign_refused(self):
        self.broken_catalog(lambda d:d["actors"][-1].update(
            source_campaign_key="UNOVA_G023_ELITE_ALDER"))
    def test_105_catalog_full_power_enabled_refused(self):
        self.broken_catalog(lambda d:d["full_power_policy"].update(enabled=True))
    def test_106_catalog_full_power_source_falsified_refused(self):
        self.broken_catalog(lambda d:d["full_power_policy"].update(
            verified_team_source="fake_pbs"))
    def test_107_catalog_full_power_bypass_refused(self):
        self.broken_catalog(lambda d:d["full_power_policy"].update(
            allow_synthetic_bypass=True))
    def test_108_catalog_teams_variant_native_compiled_refused(self):
        self.broken_catalog(lambda d:d["actors"][0]["variants"][0].update(
            native_battle_executable=True))
    def test_109_catalog_fake_map_id_refused(self):
        self.broken_catalog(lambda d:d["actors"][0].update(source_map_id=518))
    def test_110_catalog_fake_reward_policy_refused(self):
        self.broken_catalog(lambda d:d.update(reward_policy="GRANT_RARE_CANDY"))
    def test_111_catalog_fake_native_playable_status_refused(self):
        self.broken_catalog(lambda d:d.update(can_install=True))
    def test_112_catalog_mutated_90_percent_refused(self):
        self.broken_catalog(lambda d:d["level_policy"].update(master_percent=99))
    def test_113_catalog_invented_numeric_level_cap_refused(self):
        self.broken_catalog(lambda d:d["level_policy"].update(
            regional_numeric_level_cap=45))
    def test_114_catalog_changed_authoritative_ledger_refused(self):
        self.broken_catalog(lambda d:d.update(
            authoritative_rematch_ledger="G03.4_SELF_ISSUED"))
    def test_115_catalog_missing_actor_refused(self):
        self.broken_catalog(lambda d:d["actors"].pop())
    def test_116_catalog_duplicate_variant_refused(self):
        self.broken_catalog(lambda d:d["actors"][0]["variants"].append(
            copy.deepcopy(d["actors"][0]["variants"][0])))
    def test_117_catalog_variant_false_source_verified_refused(self):
        self.broken_catalog(lambda d:d["actors"][0]["variants"][1].update(
            source_verified=True))
    def test_118_catalog_difficulty_master_wrong_stage_refused(self):
        self.broken_catalog(lambda d:d["actors"][1]["variants"][2].update(story_stage=2))
    def test_119_catalog_native_coverage_claim_refused(self):
        self.broken_catalog(lambda d:d["coverage_policy"].update(
            native_type_chart_verified=True))
    def test_120_catalog_false_n_saves_modified_refused(self):
        self.broken_catalog(lambda d:d.update(native_saves_modified=True))
    def test_121_G01_4_codec_roundtrip_projection_only(self):
        env=self.fixture("done");p=rivals._g01(env)
        self.assertEqual(codec.decode_current(codec.encode_current(p,self.ctx),self.ctx),p)
    def test_122_G01_4_codec_cannot_serialize_full_G03_4_env(self):
        with self.assertRaises(ValueError):
            codec.encode_current(self.fixture("done"),self.ctx)
    def test_123_full_demo_and_rematch_win(self):
        r=elite.demo(self.ctx,self.gyms,self.finale,self.post,self.scale,
                     self.rival,self.catalog)
        self.assertEqual(r["stable_variants"],19)
        self.assertEqual(r["completed_g02_4_rematch_sessions"],1)
        self.assertFalse(r["full_power_enabled"])
        self.assertFalse(r["real_teams_created"])
    def test_124_cli_check(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g03_elite_alder.py"),
            "--check"],cwd=ROOT,capture_output=True,text=True,timeout=45)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(json.loads(p.stdout)["stable_variants"],19)
    def test_125_cli_demo(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g03_elite_alder.py"),
            "--simulate-demo"],cwd=ROOT,capture_output=True,text=True,timeout=75)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(json.loads(p.stdout)["master_rematch_scaled_level"],36)
    def test_126_chapter_10_requires_original_eight_badges(self):
        self.assertEqual(len(self.story_fixture()["g024_envelope"]["g023_envelope"][
            "g02_envelope"]["badge_claims"]),8)
    def test_127_rematch_after_credits_all_castle_events(self):
        self.assertEqual(len(self.fixture()["g024_envelope"]["g023_envelope"][
            "castle_receipts"]),5)
    def test_128_final_result_never_grants_rewards_or_native_battles(self):
        r=self.act(self.fixture("elite4"),"battle",actor_name="ALDER",outcome="WIN")
        self.assertFalse(r["native_battles_executed"])
        self.assertFalse(r["real_rewards_granted"])
        self.assertFalse(r["real_badges_granted"])
        self.assertFalse(r["native_saves_modified"])
        self.assertFalse(r["can_install"])

if __name__=="__main__":
    unittest.main()
