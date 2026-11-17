"""G02.4 offline postgame tests. Never accesses player saves, Game.exe, RXDATA."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g01_chapter_machine as g01
import audit_unova_g01_serialization as codec
import audit_unova_g02_postgame as post

class UnovaG024Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx,cls.gyms,cls.final,cls.cat=post.load_project()
        cls.snap={}
        cls.snap["early"]=post.initial(cls.ctx)
        env=post.postgame_fixture(cls.ctx,cls.gyms,cls.final)
        cls.snap["postgame"]=copy.deepcopy(env)
        def call(action,**kwargs):
            nonlocal env
            r=post.apply(env,cls.ctx,cls.gyms,cls.final,cls.cat,action,**kwargs)
            env=r["envelope"]
            return r
        for cap in ("DIVE","SURF","WATERFALL"):
            call("register_navigation",capability=cap,simulation_gate=g01.SIMULATION_GATE)
        cls.snap["navigation"]=copy.deepcopy(env)
        call("looker_briefing")
        cls.snap["briefed"]=copy.deepcopy(env)
        for n,sage in enumerate(cls.cat["sages"],1):
            call("find_sage",sage_key=sage["key"])
            cls.snap["sages"+str(n)]=copy.deepcopy(env)
        call("looker_completion")
        cls.snap["looker_done"]=copy.deepcopy(env)
        for leg in cls.cat["legendary_encounters"]:
            if leg["species"]=="LANDORUS":
                call("plan_genie_pair",simulation_gate=g01.SIMULATION_GATE)
                cls.snap["genie_pair"]=copy.deepcopy(env)
            call("legendary_encounter",legend_key=leg["key"],outcome="ENCOUNTERED")
            cls.snap["legend_"+leg["species"]]=copy.deepcopy(env)
        for item in cls.cat["optional_activities"]:
            call("optional_activity",activity_key=item["key"])
        cls.snap["activities"]=copy.deepcopy(env)
        call("start_rematch",session_id=1)
        cls.snap["rematch1_active"]=copy.deepcopy(env)
        for i,member in enumerate(cls.cat["league_rematch"]["elite_members"],1):
            call("rematch_elite",session_id=1,member_key=member,outcome="WIN")
            cls.snap["rematch1_elite"+str(i)]=copy.deepcopy(env)
        call("rematch_alder",session_id=1,outcome="WIN")
        cls.snap["rematch1_alder"]=copy.deepcopy(env)
        call("finish_rematch",session_id=1)
        cls.snap["rematch1_done"]=copy.deepcopy(env)
        call("start_rematch",session_id=2)
        cls.snap["rematch2_active"]=copy.deepcopy(env)

    def env(self,name="postgame"):return copy.deepcopy(self.snap[name])
    def act(self,env,action,**kwargs):
        return post.apply(env,self.ctx,self.gyms,self.final,self.cat,action,**kwargs)
    def deny(self,env,action,**kwargs):
        before=copy.deepcopy(env)
        with self.assertRaises(ValueError):
            self.act(env,action,**kwargs)
        self.assertEqual(env,before)
    def invalid_env(self,mutator,name="postgame"):
        env=self.env(name);mutator(env)
        with self.assertRaises(ValueError):
            post.validate_envelope(env,self.ctx,self.gyms,self.final,self.cat)
    def invalid_catalog(self,mutator):
        catalog=copy.deepcopy(self.cat)
        mutator(catalog)
        area=g01._safe_source(ROOT/catalog["area_catalog"])
        with self.assertRaises(ValueError):
            post.validate_catalog(catalog,self.ctx,self.gyms,self.final,area)
    def cap(self,env,ability):
        return self.act(env,"register_navigation",
                        capability=ability,simulation_gate=g01.SIMULATION_GATE)["envelope"]
    def sage(self,name):
        return "UNOVA_G024_SAGE_"+name
    def legend(self,name):
        return "UNOVA_G024_LEGEND_"+name
    def activity(self,name):
        return "UNOVA_G024_ACTIVITY_"+name

    def test_01_catalog_explicitly_offline(self):
        self.assertEqual(self.cat["phase"],"G02.4")
        self.assertFalse(self.cat["can_install"])
        self.assertFalse(self.cat["real_pokemon_captured"])
        self.assertFalse(self.cat["real_hms_verified"])
    def test_02_lookers_six_not_ghetsis(self):
        self.assertEqual([s["name"] for s in self.cat["sages"]],
            ["GORM","RYOKU","ZINZOLIN","BRONIUS","ROOD","GIALLO"])
        self.assertNotIn("GHETSIS",[s["name"] for s in self.cat["sages"]])
    def test_03_six_distinct_source_areas(self):
        self.assertEqual(len({s["area_key"] for s in self.cat["sages"]}),6)
    def test_04_sages_tm_intents_match_planned_white(self):
        self.assertEqual([s["tm_intent"] for s in self.cat["sages"]],
            ["TM75_SWORDS_DANCE","TM04_CALM_MIND","TM01_HONE_CLAWS",
             "TM69_ROCK_POLISH","TM32_DOUBLE_TEAM","TM08_BULK_UP"])
    def test_05_external_event_legendaries_blocked(self):
        self.assertEqual(self.cat["event_only_blocked"],
            ["VICTINI","KELDEO","MELOETTA","GENESECT"])
    def test_06_white_only_thundurus_not_tornadus_roamer(self):
        self.assertIn(self.legend("THUNDURUS"),
            [l["key"] for l in self.cat["legendary_encounters"]])
        self.assertNotIn(self.legend("TORNADUS"),
            [l["key"] for l in self.cat["legendary_encounters"]])
    def test_07_volcarona_is_special_not_legendary(self):
        a=next(x for x in self.cat["optional_activities"] if "VOLCARONA" in x["key"])
        self.assertEqual(a["kind"],"SPECIAL_ENCOUNTER_NOT_LEGENDARY")
    def test_08_every_area_from_reference_u03(self):
        keys={x["key"] for x in g01._safe_source(ROOT/self.cat["area_catalog"])["areas"]}
        uses=[x["area_key"] for x in self.cat["sages"]+self.cat["legendary_encounters"]+
              self.cat["optional_activities"]]
        uses.append(self.cat["looker_briefing"]["area_key"])
        self.assertTrue(all(x in keys for x in uses))
    def test_09_initial_prestart_has_no_flags(self):
        proof=post.validate_envelope(self.env("early"),self.ctx,self.gyms,self.final,self.cat)
        self.assertEqual(proof["chapter_index"],0)
        self.assertEqual(proof["sages_found"],0)
    def test_10_postgame_fixture_proves_eight_badges(self):
        env=self.env()
        self.assertEqual(len(env["g023_envelope"]["g02_envelope"]["badge_claims"]),8)
    def test_11_postgame_fixture_proves_castle_credits(self):
        env=self.env()
        self.assertIn("UNOVA_G023_CREDITS_SIMULATED",
                      env["g023_envelope"]["unique_story_tokens"])
        self.assertEqual(post.validate_envelope(env,self.ctx,self.gyms,self.final,self.cat)["chapter_index"],12)
    def test_12_cannot_brief_looker_before_credits(self):
        self.deny(self.env("early"),"looker_briefing")
    def test_13_cannot_register_navigation_before_credits(self):
        self.deny(self.env("early"),"register_navigation",
                  capability="SURF",simulation_gate=g01.SIMULATION_GATE)
    def test_14_cannot_find_sage_before_credits(self):
        self.deny(self.env("early"),"find_sage",sage_key=self.sage("GORM"))
    def test_15_cannot_start_rematch_before_credits(self):
        self.deny(self.env("early"),"start_rematch",session_id=1)
    def test_16_looker_briefing_once(self):
        r=self.act(self.env(),"looker_briefing")
        self.assertEqual(r["status"],post.SUCCESS)
        self.assertTrue(r["envelope"]["looker_briefed"])
        self.assertFalse(r["real_items_granted"])
    def test_17_duplicate_briefing_is_noop(self):
        env=self.env("briefed")
        r=self.act(env,"looker_briefing")
        self.assertEqual(r["status"],post.ALREADY)
        self.assertEqual(r["envelope"],env)
    def test_18_cannot_find_sage_before_looker(self):
        self.deny(self.env("navigation"),"find_sage",sage_key=self.sage("GORM"))
    def test_19_each_sage_can_be_first_after_lookers_briefing(self):
        for sage in self.cat["sages"]:
            with self.subTest(sage=sage["name"]):
                r=self.act(self.env("briefed"),"find_sage",sage_key=sage["key"])
                self.assertEqual(r["status"],post.SUCCESS)
                self.assertEqual(len(r["envelope"]["sages_found"]),1)
    def test_20_sages_can_be_found_in_reverse_order(self):
        env=self.env("briefed")
        for sage in reversed(self.cat["sages"]):
            env=self.act(env,"find_sage",sage_key=sage["key"])["envelope"]
        self.assertEqual({r["sage_key"] for r in env["sages_found"]},
                         {x["key"] for x in self.cat["sages"]})
    def test_21_sage_does_not_grant_tm_in_game(self):
        r=self.act(self.env("briefed"),"find_sage",sage_key=self.sage("GORM"))
        self.assertFalse(r["real_items_granted"])
        self.assertEqual(r["envelope"]["sages_found"][0]["tm_intent"],"TM75_SWORDS_DANCE")
    def test_22_sage_replay_noop(self):
        env=self.env("sages1")
        r=self.act(env,"find_sage",sage_key=self.sage("GORM"))
        self.assertEqual(r["status"],post.ALREADY)
        self.assertEqual(r["envelope"],env)
    def test_23_sage_unknown_rejected(self):
        self.deny(self.env("briefed"),"find_sage",sage_key=self.sage("GHETSIS"))
    def test_24_sage_unregistered_rejected(self):
        self.deny(self.env("briefed"),"find_sage",sage_key="UNOVA_G024_SAGE_FAKE")
    def test_25_sage_rood_needs_surf_plan(self):
        e=self.act(self.env(),"looker_briefing")["envelope"]
        self.deny(e,"find_sage",sage_key=self.sage("ROOD"))
    def test_26_sage_giallo_needs_waterfall_plan(self):
        e=self.cap(self.env("postgame"),"SURF")
        e=self.act(e,"looker_briefing")["envelope"]
        self.deny(e,"find_sage",sage_key=self.sage("GIALLO"))
    def test_27_sage_giallo_allowed_with_surf_and_waterfall_plans(self):
        e=self.cap(self.cap(self.env(),"SURF"),"WATERFALL")
        e=self.act(e,"looker_briefing")["envelope"]
        self.assertEqual(self.act(e,"find_sage",sage_key=self.sage("GIALLO"))["status"],
                         post.SUCCESS)
    def test_28_cannot_finish_looker_after_five_sages(self):
        self.deny(self.env("sages5"),"looker_completion")
    def test_29_finish_looker_requires_six(self):
        self.assertEqual(self.act(self.env("sages6"),"looker_completion")["status"],
                         post.SUCCESS)
    def test_30_looker_completion_replay_noop(self):
        env=self.env("looker_done")
        r=self.act(env,"looker_completion")
        self.assertEqual(r["status"],post.ALREADY)
        self.assertEqual(r["envelope"],env)
    def test_31_sages_do_not_change_g01_progression(self):
        self.assertEqual(self.env("looker_done")["g023_envelope"],
                         self.env("briefed")["g023_envelope"])
    def test_32_navigation_capability_requires_explicit_synthetic_gate(self):
        self.deny(self.env(),"register_navigation",capability="SURF",
                  simulation_gate="NATIVE_HM_APPROVED")
    def test_33_navigation_gate_missing_rejected(self):
        self.deny(self.env(),"register_navigation",capability="SURF")
    def test_34_unregistered_navigation_blocked(self):
        self.deny(self.env(),"register_navigation",capability="FLY",
                  simulation_gate=g01.SIMULATION_GATE)
    def test_35_navigation_replay_noop(self):
        env=self.env("navigation")
        r=self.act(env,"register_navigation",capability="SURF",
                   simulation_gate=g01.SIMULATION_GATE)
        self.assertEqual(r["status"],post.ALREADY)
    def test_36_navigation_is_sorted_and_unique(self):
        self.assertEqual(self.env("navigation")["navigation_planned"],
                         ["DIVE","SURF","WATERFALL"])
    def test_37_navigation_does_not_verify_hm_in_game(self):
        r=self.act(self.env(),"register_navigation",
                   capability="SURF",simulation_gate=g01.SIMULATION_GATE)
        self.assertFalse(r["real_hms_verified"])
        self.assertFalse(r["native_saves_modified"])
    def test_38_thundurus_encounter_is_planned_not_capture(self):
        env=self.env("briefed")
        r=self.act(env,"legendary_encounter",
                   legend_key=self.legend("THUNDURUS"),outcome="ENCOUNTERED")
        self.assertEqual(r["status"],post.SUCCESS)
        self.assertFalse(r["real_pokemon_captured"])
    def test_39_kyurem_encounter_not_capture(self):
        r=self.act(self.env(),"legendary_encounter",
                   legend_key=self.legend("KYUREM"),outcome="ENCOUNTERED")
        self.assertEqual(r["status"],post.SUCCESS)
        self.assertFalse(r["real_pokemon_captured"])
    def test_40_cobalion_requires_surf_plan(self):
        self.deny(self.env(),"legendary_encounter",
                  legend_key=self.legend("COBALION"),outcome="ENCOUNTERED")
    def test_41_cobalion_allowed_with_surf_plan(self):
        env=self.cap(self.env(),"SURF")
        self.assertEqual(self.act(env,"legendary_encounter",
            legend_key=self.legend("COBALION"),outcome="ENCOUNTERED")["status"],post.SUCCESS)
    def test_42_terrakion_requires_cobalion(self):
        self.deny(self.env(),"legendary_encounter",
                  legend_key=self.legend("TERRAKION"),outcome="ENCOUNTERED")
    def test_43_virizion_requires_cobalion(self):
        self.deny(self.env(),"legendary_encounter",
                  legend_key=self.legend("VIRIZION"),outcome="ENCOUNTERED")
    def test_44_cobalion_unlocks_two_optional_encounter_intents(self):
        env=self.env("legend_COBALION")
        for name in ("TERRAKION","VIRIZION"):
            with self.subTest(name=name):
                self.assertEqual(self.act(env,"legendary_encounter",
                    legend_key=self.legend(name),outcome="ENCOUNTERED")["status"],
                    post.SUCCESS)
    def test_45_cobalion_before_terrakion_and_virizion_in_receipts(self):
        env=self.env("legend_VIRIZION")
        self.assertEqual([r["legend_key"] for r in env["legendary_encounters"]][:3],
            [self.legend("COBALION"),self.legend("TERRAKION"),self.legend("VIRIZION")])
    def test_46_legend_capture_outcome_is_not_supported(self):
        self.deny(self.env(),"legendary_encounter",
                  legend_key=self.legend("KYUREM"),outcome="CAPTURED")
    def test_47_legend_win_outcome_is_not_supported(self):
        self.deny(self.env(),"legendary_encounter",
                  legend_key=self.legend("KYUREM"),outcome="WIN")
    def test_48_legend_missing_explicit_encounter_rejected(self):
        self.deny(self.env(),"legendary_encounter",legend_key=self.legend("KYUREM"))
    def test_49_legend_replay_is_noop(self):
        env=self.env("legend_KYUREM")
        r=self.act(env,"legendary_encounter",
                   legend_key=self.legend("KYUREM"),outcome="ENCOUNTERED")
        self.assertEqual(r["status"],post.ALREADY)
        self.assertEqual(r["envelope"],env)
    def test_50_landorus_requires_simulated_pair(self):
        self.deny(self.env("legend_THUNDURUS"),"legendary_encounter",
                  legend_key=self.legend("LANDORUS"),outcome="ENCOUNTERED")
    def test_51_pair_requires_thundurus_story_first(self):
        self.deny(self.env(),"plan_genie_pair",simulation_gate=g01.SIMULATION_GATE)
    def test_52_pair_requires_explicit_simulation_gate(self):
        self.deny(self.env("legend_THUNDURUS"),"plan_genie_pair",
                  simulation_gate="REAL_PARTY_VERIFIED")
    def test_53_pair_does_not_prove_actual_party(self):
        r=self.act(self.env("legend_THUNDURUS"),"plan_genie_pair",
                   simulation_gate=g01.SIMULATION_GATE)
        self.assertTrue(r["envelope"]["party_pair_planned"])
        self.assertFalse(r["real_pokemon_captured"])
    def test_54_pair_replay_is_noop(self):
        env=self.env("genie_pair")
        self.assertEqual(self.act(env,"plan_genie_pair",
            simulation_gate=g01.SIMULATION_GATE)["status"],post.ALREADY)
    def test_55_landorus_requires_surf_even_with_pair(self):
        env=self.env("genie_pair")
        env["navigation_planned"]=["DIVE","SURF","WATERFALL"]
        self.assertEqual(self.act(env,"legendary_encounter",
            legend_key=self.legend("LANDORUS"),outcome="ENCOUNTERED")["status"],post.SUCCESS)
    def test_56_landorus_after_pair_single_encounter(self):
        env=self.env("legend_LANDORUS")
        self.assertEqual(len(env["legendary_encounters"]),6)
        self.assertTrue(env["party_pair_planned"])
    def test_57_external_victini_event_not_automatically_unlocked(self):
        self.deny(self.env(),"legendary_encounter",
                  legend_key=self.legend("VICTINI"),outcome="ENCOUNTERED")
    def test_58_event_only_keldeo_never_automatically_unlocked(self):
        self.deny(self.env(),"legendary_encounter",
                  legend_key=self.legend("KELDEO"),outcome="ENCOUNTERED")
    def test_59_event_only_meloetta_never_automatically_unlocked(self):
        self.deny(self.env(),"legendary_encounter",
                  legend_key=self.legend("MELOETTA"),outcome="ENCOUNTERED")
    def test_60_event_only_genesect_never_automatically_unlocked(self):
        self.deny(self.env(),"legendary_encounter",
                  legend_key=self.legend("GENESECT"),outcome="ENCOUNTERED")
    def test_61_white_forest_available_only_after_credits(self):
        self.deny(self.env("early"),"optional_activity",
                  activity_key=self.activity("WHITE_FOREST"))
        r=self.act(self.env(),"optional_activity",
                   activity_key=self.activity("WHITE_FOREST"))
        self.assertEqual(r["status"],post.SUCCESS)
    def test_62_white_forest_replay_noop(self):
        env=self.env("activities")
        r=self.act(env,"optional_activity",
                   activity_key=self.activity("WHITE_FOREST"))
        self.assertEqual(r["status"],post.ALREADY)
    def test_63_abyssal_ruins_requires_dive_plan(self):
        self.deny(self.env(),"optional_activity",
                  activity_key=self.activity("ABYSSAL_RUINS"))
    def test_64_abyssal_ruins_with_dive_plan(self):
        env=self.cap(self.env(),"DIVE")
        self.assertEqual(self.act(env,"optional_activity",
            activity_key=self.activity("ABYSSAL_RUINS"))["status"],post.SUCCESS)
    def test_65_all_seven_activities_are_planned_only(self):
        env=self.env("activities")
        self.assertEqual(len(env["optional_activities"]),7)
        self.assertTrue(all(r["receipt_scope"]==post.RECEIPT_SCOPE
                            for r in env["optional_activities"]))
    def test_66_activity_unknown_rejected(self):
        self.deny(self.env(),"optional_activity",activity_key=self.activity("BLACK_CITY"))
    def test_67_activity_has_no_real_rewards(self):
        r=self.act(self.env(),"optional_activity",
                   activity_key=self.activity("VOLCARONA"))
        self.assertFalse(r["real_pokemon_captured"])
        self.assertFalse(r["real_items_granted"])
    def test_68_rematch_start_session_one(self):
        env=self.env("activities")
        r=self.act(env,"start_rematch",session_id=1)
        self.assertEqual(r["status"],post.SUCCESS)
        self.assertEqual(r["envelope"]["active_rematch"]["session_id"],1)
    def test_69_rematch_can_start_without_lookers_sages(self):
        self.assertEqual(self.act(self.env(),"start_rematch",session_id=1)["status"],
                         post.SUCCESS)
    def test_70_rematch_session_skip_blocked(self):
        self.deny(self.env(),"start_rematch",session_id=2)
    def test_71_rematch_bool_session_id_rejected(self):
        self.deny(self.env(),"start_rematch",session_id=True)
    def test_72_rematch_negative_session_id_rejected(self):
        self.deny(self.env(),"start_rematch",session_id=-1)
    def test_73_rematch_second_start_same_id_noop(self):
        env=self.env("rematch1_active")
        self.assertEqual(self.act(env,"start_rematch",session_id=1)["status"],post.ALREADY)
    def test_74_rematch_second_concurrent_session_blocked(self):
        self.deny(self.env("rematch1_active"),"start_rematch",session_id=2)
    def test_75_rematch_elite_any_first_member(self):
        env=self.env("rematch1_active")
        for name in self.cat["league_rematch"]["elite_members"]:
            with self.subTest(member=name):
                self.assertEqual(self.act(env,"rematch_elite",session_id=1,
                     member_key=name,outcome="WIN")["status"],post.SUCCESS)
    def test_76_rematch_elite_loss_retry_does_not_change_state(self):
        env=self.env("rematch1_active")
        member=self.cat["league_rematch"]["elite_members"][0]
        r=self.act(env,"rematch_elite",session_id=1,member_key=member,outcome="LOSS")
        self.assertEqual(r["status"],post.LOSS)
        self.assertEqual(r["envelope"],env)
        self.assertEqual(r["suggested_safe_return_area_key"],"UNOVA_POKEMON_LEAGUE")
        self.assertFalse(r["native_teleport_executed"])
    def test_77_rematch_elite_win_once(self):
        env=self.env("rematch1_elite1")
        member=self.cat["league_rematch"]["elite_members"][0]
        self.assertEqual(self.act(env,"rematch_elite",session_id=1,
            member_key=member,outcome="WIN")["status"],post.ALREADY)
    def test_78_rematch_elite_cannot_reverse_win_to_loss(self):
        env=self.env("rematch1_elite1")
        member=self.cat["league_rematch"]["elite_members"][0]
        self.deny(env,"rematch_elite",session_id=1,
                  member_key=member,outcome="LOSS")
    def test_79_rematch_unknown_elite_member_rejected(self):
        self.deny(self.env("rematch1_active"),"rematch_elite",
                  session_id=1,member_key="ALDER",outcome="WIN")
    def test_80_alder_rematch_requires_four_elite_wins(self):
        self.deny(self.env("rematch1_elite3"),"rematch_alder",session_id=1,outcome="WIN")
    def test_81_alder_rematch_loss_no_progress(self):
        env=self.env("rematch1_elite4")
        r=self.act(env,"rematch_alder",session_id=1,outcome="LOSS")
        self.assertEqual(r["status"],post.LOSS)
        self.assertEqual(r["envelope"],env)
    def test_82_alder_rematch_win_after_loss(self):
        env=self.env("rematch1_elite4")
        loss=self.act(env,"rematch_alder",session_id=1,outcome="LOSS")
        win=self.act(loss["envelope"],"rematch_alder",session_id=1,outcome="WIN")
        self.assertTrue(win["envelope"]["active_rematch"]["alder_won"])
    def test_83_alder_rematch_win_replay_noop(self):
        env=self.env("rematch1_alder")
        r=self.act(env,"rematch_alder",session_id=1,outcome="WIN")
        self.assertEqual(r["status"],post.ALREADY)
    def test_84_alder_rematch_win_cannot_reverse(self):
        self.deny(self.env("rematch1_alder"),"rematch_alder",
                  session_id=1,outcome="LOSS")
    def test_85_rematch_finish_requires_alder_win(self):
        self.deny(self.env("rematch1_elite4"),"finish_rematch",session_id=1)
    def test_86_rematch_completed_after_alder(self):
        env=self.env("rematch1_done")
        self.assertEqual(len(env["rematches_completed"]),1)
        self.assertIsNone(env["active_rematch"])
        self.assertEqual(env["rematches_completed"][0]["session_id"],1)
    def test_87_rematch_finish_duplicate_noop(self):
        env=self.env("rematch1_done")
        self.assertEqual(self.act(env,"finish_rematch",session_id=1)["status"],post.ALREADY)
    def test_88_rematch_second_session_allowed(self):
        env=self.env("rematch2_active")
        self.assertEqual(env["active_rematch"]["session_id"],2)
    def test_89_rematch_second_session_completion_is_separate(self):
        env=self.env("rematch2_active")
        for member in reversed(self.cat["league_rematch"]["elite_members"]):
            env=self.act(env,"rematch_elite",session_id=2,
                         member_key=member,outcome="WIN")["envelope"]
        env=self.act(env,"rematch_alder",session_id=2,outcome="WIN")["envelope"]
        env=self.act(env,"finish_rematch",session_id=2)["envelope"]
        self.assertEqual([s["session_id"] for s in env["rematches_completed"]],[1,2])
    def test_90_rematch_wrong_session_id_rejected(self):
        self.deny(self.env("rematch2_active"),"rematch_elite",session_id=3,
                  member_key=self.cat["league_rematch"]["elite_members"][0],outcome="WIN")
    def test_91_rematches_cannot_modify_original_elite_four_proof(self):
        self.assertEqual(self.env("rematch1_done")["g023_envelope"],
                         self.env("activities")["g023_envelope"])
    def test_92_return_to_pre_game_chapter_is_readonly(self):
        env=self.env("rematch1_done")
        r=self.act(env,"reenter",chapter_key=self.ctx[0]["chapters"][10]["key"])
        self.assertEqual(r["status"],post.REENTER)
        self.assertEqual(r["envelope"],env)
    def test_93_reentry_future_chapter_denied(self):
        self.deny(self.env(),"reenter",chapter_key="UNOVA_CH99_FUTURE")
    def test_94_fake_save_claim_rejected(self):
        self.invalid_env(lambda e:e.update(native_save_slot=1))
    def test_95_duplicate_sage_receipt_rejected(self):
        self.invalid_env(lambda e:e["sages_found"].append(
            copy.deepcopy(e["sages_found"][0])),"sages1")
    def test_96_forged_sage_tm_receipt_rejected(self):
        self.invalid_env(lambda e:e["sages_found"][0].update(tm_intent="MASTER_BALL"),
                         "sages1")
    def test_97_forged_looker_completion_rejected(self):
        self.invalid_env(lambda e:e.update(looker_completed=True),"briefed")
    def test_98_unregistered_legendary_receipt_rejected(self):
        self.invalid_env(lambda e:e["legendary_encounters"].append({
            "legend_key":"UNOVA_G024_LEGEND_RESHIRAM","area_key":"UNOVA_NS_CASTLE",
            "receipt_scope":post.RECEIPT_SCOPE}))
    def test_99_forged_legendary_capture_flag_rejected(self):
        self.invalid_env(lambda e:e["legendary_encounters"][0].update(captured=True),
                         "legend_COBALION")
    def test_100_terrakion_before_cobalion_receipt_rejected(self):
        self.invalid_env(lambda e:e["legendary_encounters"].reverse(),"legend_TERRAKION")
    def test_101_false_party_pair_without_thundurus_rejected(self):
        self.invalid_env(lambda e:e.update(party_pair_planned=True))
    def test_102_forged_navigation_noncanonical_rejected(self):
        self.invalid_env(lambda e:e.update(navigation_planned=["SURF","DIVE"]),"navigation")
    def test_103_extra_badge_native_token_rejected(self):
        self.invalid_env(lambda e:e["g023_envelope"]["g02_envelope"][
            "badge_claims"].append("FAKE"))
    def test_104_rematch_forged_alder_before_elite_rejected(self):
        self.invalid_env(lambda e:e["active_rematch"].update(alder_won=True),
                         "rematch1_active")
    def test_105_rematch_duplicate_member_rejected(self):
        self.invalid_env(lambda e:e["active_rematch"]["elite_wins"].append(
            e["active_rematch"]["elite_wins"][0]),"rematch1_elite1")
    def test_106_completed_session_no_alder_win_rejected(self):
        self.invalid_env(lambda e:e["rematches_completed"][0].update(alder_won=False),
                         "rematch1_done")
    def test_107_completed_session_nonsequential_id_rejected(self):
        self.invalid_env(lambda e:e["rematches_completed"][0].update(session_id=2),
                         "rematch1_done")
    def test_108_wrong_white_forest_catalog_rejected(self):
        self.invalid_catalog(lambda c:c["optional_activities"][1].update(
            area_key="UNOVA_BLACK_CITY"))
    def test_109_catalog_forged_native_sage_id_rejected(self):
        self.invalid_catalog(lambda c:c["sages"][0].update(native_event_id=123))
    def test_110_catalog_ghetsis_added_as_seventh_sage_rejected(self):
        self.invalid_catalog(lambda c:c["sages"].append(copy.deepcopy(c["sages"][0])))
    def test_111_catalog_thundurus_swapped_to_tornadus_rejected(self):
        self.invalid_catalog(lambda c:c["legendary_encounters"][4].update(
            species="TORNADUS"))
    def test_112_catalog_relax_landorus_pair_rejected(self):
        self.invalid_catalog(lambda c:c["legendary_encounters"][5].update(
            requires_both_genies_party_simulated=False))
    def test_113_catalog_fake_capture_executed_rejected(self):
        self.invalid_catalog(lambda c:c["legendary_encounters"][0].update(
            capture_executed=True))
    def test_114_catalog_fake_items_granted_rejected(self):
        self.invalid_catalog(lambda c:c.update(real_items_granted=True))
    def test_115_catalog_fake_playable_status_rejected(self):
        self.invalid_catalog(lambda c:c.update(can_install=True))
    def test_116_catalog_remove_sage_navigation_requirement_rejected(self):
        self.invalid_catalog(lambda c:c["sages"][5].update(required_capabilities=[]))
    def test_117_catalog_fake_elite_team_rejected(self):
        self.invalid_catalog(lambda c:c["league_rematch"].update(
            trainer_party=[{"species":"VOLCARONA"}]))
    def test_118_g01_4_roundtrip_projection_unchanged(self):
        env=self.env("rematch1_done")
        state=env["g023_envelope"]["g02_envelope"]["g01_envelope"]
        encoded=codec.encode_current(state,self.ctx)
        self.assertEqual(codec.decode_current(encoded,self.ctx),state)
    def test_119_g01_codec_does_not_silently_persist_optional_states(self):
        with self.assertRaises(ValueError):
            codec.encode_current(self.env("rematch1_done"),self.ctx)
    def test_120_full_demo_synthetic_only(self):
        result=post.demo(self.ctx,self.gyms,self.final,self.cat)
        self.assertEqual(result["sages_found"],6)
        self.assertTrue(result["looker_complete"])
        self.assertEqual(result["legendary_encounter_intents"],6)
        self.assertEqual(result["optional_activities"],7)
        self.assertEqual(result["league_rematches_completed"],1)
        self.assertFalse(result["can_install"])
        self.assertFalse(result["real_pokemon_captured"])
    def test_121_cli_check(self):
        r=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g02_postgame.py"),
            "--check"],cwd=ROOT,text=True,capture_output=True,timeout=40)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(json.loads(r.stdout)["six_sages"],6)
    def test_122_cli_demo(self):
        r=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g02_postgame.py"),
            "--simulate-demo"],cwd=ROOT,text=True,capture_output=True,timeout=40)
        self.assertEqual(r.returncode,0,r.stdout+r.stderr)
        self.assertEqual(json.loads(r.stdout)["league_rematches_completed"],1)
    def test_123_cross_region_state_blocked(self):
        self.invalid_env(lambda e:e.update(region="KANTO"))
    def test_124_unsupported_future_version_blocked(self):
        self.invalid_env(lambda e:e.update(schema=2))
    def test_125_unknown_operation_rejected(self):
        self.deny(self.env(),"grant_real_super_rod")
    def test_126_missing_required_action_arg_rejected(self):
        self.deny(self.env(),"legendary_encounter",legend_key=self.legend("KYUREM"))
    def test_127_extra_native_action_arg_rejected(self):
        self.deny(self.env(),"looker_briefing",simulation_gate=g01.SIMULATION_GATE)
    def test_128_all_result_flags_denote_offline(self):
        r=self.act(self.env(),"looker_briefing")
        self.assertFalse(r["native_saves_modified"])
        self.assertFalse(r["real_battles_executed"])
        self.assertFalse(r["game_exe_tested"])
        self.assertFalse(r["real_items_granted"])
        self.assertFalse(r["can_install"])

if __name__=="__main__":
    unittest.main()
