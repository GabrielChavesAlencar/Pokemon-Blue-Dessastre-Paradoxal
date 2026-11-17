"""G03.2 offline leader scaling, dynamic fixture evolution and weakness coverage tests."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g03_leader_scaling as bal
import audit_unova_g01_chapter_machine as g01

class UnovaG032Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p,cls.gyms,cls.shared,cls.evo=bal.load_project()
        cls.registry=g01._safe_source(ROOT/cls.p["sources"]["region_registry"])
        cls.species=g01._safe_source(ROOT/cls.p["sources"]["species_index"])
        cls.family={
            "FIXTURE_BASE":[{"to":"FIXTURE_STAGE2","method":"LEVEL",
                             "requirement":16,"condition":"NONE"}],
            "FIXTURE_STAGE2":[{"to":"FIXTURE_FINAL","method":"LEVEL",
                               "requirement":36,"condition":"NONE"}]}
        cls.threat_party=[
            {"species":"FIXTURE_EXISTING","types":["GRASS"],
             "multipliers":{"FIRE":2,"GROUND":2}}]
        cls.candidates=[
            {"species":"FIXTURE_RESIST","types":["WATER"],"bst":480,
             "multipliers":{"FIRE":0.5,"GROUND":0.5},
             "special_flags":[],"synthetic_only":True},
            {"species":"FIXTURE_WEAK","types":["ICE"],"bst":480,
             "multipliers":{"FIRE":2,"GROUND":2},
             "special_flags":[],"synthetic_only":True}]

    def plan(self,**override):
        kwargs={"leader_id":"UNOVA_G032_LEADER_01",
            "party":[{"level":40,"egg":False}],
            "engine_max_level":100,"story_stage":0,
            "earned_badges":[],"authored_team_size":3,
            "starter_choice":"SNIVY"}
        kwargs.update(override)
        return bal.plan_battle(self.p,**kwargs)

    def broken_plan(self,**kwargs):
        with self.assertRaises(ValueError):
            self.plan(**kwargs)

    def evolve(self,base="FIXTURE_BASE",level=20,edges=None,**kwargs):
        return bal.evolve_fixture(self.p,base,level,
                copy.deepcopy(self.family if edges is None else edges),**kwargs)

    def broken_evo(self,*args,**kwargs):
        with self.assertRaises(ValueError):
            self.evolve(*args,**kwargs)

    def cover(self,**override):
        args={"attack_types":["FIRE","GROUND"],
              "party":copy.deepcopy(self.threat_party),
              "candidates":copy.deepcopy(self.candidates)}
        args.update(override)
        return bal.coverage_plan(self.p,**args)

    def broken_cover(self,**kwargs):
        with self.assertRaises(ValueError):
            self.cover(**kwargs)

    def broken_policy(self,mutator):
        p=copy.deepcopy(self.p)
        mutator(p)
        with self.assertRaises(ValueError):
            bal.validate_policy(p,self.gyms,self.shared,self.evo,self.registry,self.species)

    def test_01_policy_is_planned_unova_white(self):
        self.assertEqual(self.p["region"],"UNOVA")
        self.assertEqual(self.p["campaign"],"WHITE_BW")
        self.assertFalse(self.p["can_install"])
        self.assertFalse(self.p["native_team_catalog_verified"])
    def test_02_eight_leaders_correspond_to_g02(self):
        self.assertEqual(len(self.p["leaders"]),8)
        self.assertEqual([g["gym_contract_id"] for g in self.p["leaders"]],
                         [g["id"] for g in self.gyms["gyms"]])
    def test_03_leaders_have_no_real_pbs_or_fixed_levels(self):
        self.assertTrue(all(x["trainer_pbs_id"] is None and
            x["trainer_party"] is None and x["trainer_levels"] is None
            for x in self.p["leaders"]))
    def test_04_white_opelucid_iris(self):
        self.assertEqual(self.p["leaders"][-1]["leader_key"],"IRIS")
        self.assertNotIn("DRAYDEN",[g["leader_key"] for g in self.p["leaders"]])
    def test_05_striaton_by_starter_matches_g02(self):
        self.assertEqual(self.p["leaders"][0]["leader_by_starter"],
                          {"SNIVY":"CHILI","TEPIG":"CRESS","OSHAWOTT":"CILAN"})
    def test_06_level_cap_not_falsely_from_badges(self):
        self.assertIsNone(self.p["level_cap"]["regional_numeric_cap_in_save"])
        self.assertFalse(self.p["level_cap"]["numeric_badge_cap_implemented"])
        self.assertTrue(self.p["level_cap"]["bst_cap_not_numeric_level_cap"])
    def test_07_stage_bst_caps_match_shared_story(self):
        self.assertEqual(self.p["level_cap"]["boss_stage_bst_caps"],
            [350,450,540,None])
    def test_08_normal_scale_from_highest_non_egg(self):
        r=self.plan()
        self.assertEqual((r["percent"],r["scaled_target_level"]),(70,28))
        self.assertEqual(r["progress_signal_level"],40)
    def test_09_master_scale_from_highest_non_egg(self):
        r=self.plan(story_stage=3)
        self.assertEqual((r["percent"],r["scaled_target_level"]),(90,36))
        self.assertEqual(r["variant"],"MASTER")
    def test_10_normal_stage_one_still_70(self):
        self.assertEqual(self.plan(story_stage=1)["percent"],70)
    def test_11_normal_stage_two_still_70(self):
        self.assertEqual(self.plan(story_stage=2)["percent"],70)
    def test_12_master_only_when_stage_three(self):
        for stage,pct in [(0,70),(1,70),(2,70),(3,90)]:
            with self.subTest(stage=stage):
                self.assertEqual(self.plan(story_stage=stage)["percent"],pct)
    def test_13_ignores_egg_at_higher_level(self):
        r=self.plan(party=[{"level":12,"egg":False},
            {"level":80,"egg":True},{"level":35,"egg":False}])
        self.assertEqual(r["scaled_target_level"],24)
        self.assertEqual(r["progress_signal_level"],35)
    def test_14_all_eggs_fallback_is_one(self):
        r=self.plan(party=[{"level":99,"egg":True}])
        self.assertEqual(r["progress_signal_level"],1)
        self.assertTrue(r["no_non_egg_fallback"])
        self.assertEqual(r["scaled_target_level"],1)
    def test_15_empty_party_has_safe_one_fallback(self):
        r=self.plan(party=[])
        self.assertEqual(r["scaled_target_level"],1)
        self.assertTrue(r["no_non_egg_fallback"])
    def test_16_engine_max_is_an_input_not_hardcoded_100(self):
        r=self.plan(party=[{"level":50,"egg":False}],engine_max_level=60)
        self.assertEqual(r["scaled_target_level"],35)
        self.assertIsNone(r["regional_badge_numeric_level_cap"])
    def test_17_integer_floor_on_odd_levels(self):
        r=self.plan(party=[{"level":31,"egg":False}])
        self.assertEqual(r["scaled_target_level"],21)
        self.assertEqual(self.plan(party=[{"level":31,"egg":False}],
            story_stage=3)["scaled_target_level"],27)
    def test_18_minimum_level_is_one(self):
        self.assertEqual(self.plan(party=[{"level":1,"egg":False}])["scaled_target_level"],1)
    def test_19_story_stage_outside_three_blocked(self):
        self.broken_plan(story_stage=4)
    def test_20_story_stage_boolean_blocked(self):
        self.broken_plan(story_stage=True)
    def test_21_engine_max_missing_blocked(self):
        self.broken_plan(engine_max_level=None)
    def test_22_engine_max_boolean_blocked(self):
        self.broken_plan(engine_max_level=True)
    def test_23_zero_engine_max_blocked(self):
        self.broken_plan(engine_max_level=0)
    def test_24_party_level_over_engine_max_blocked(self):
        self.broken_plan(party=[{"level":101,"egg":False}])
    def test_25_party_negative_level_blocked(self):
        self.broken_plan(party=[{"level":-1,"egg":False}])
    def test_26_party_boolean_level_blocked(self):
        self.broken_plan(party=[{"level":True,"egg":False}])
    def test_27_party_egg_must_be_boolean(self):
        self.broken_plan(party=[{"level":20,"egg":"FALSE"}])
    def test_28_party_slots_must_not_exceed_six(self):
        self.broken_plan(party=[{"level":20,"egg":False}]*7)
    def test_29_party_no_native_species_field_allowed(self):
        self.broken_plan(party=[{"level":30,"egg":False,"species":"MEWTWO"}])
    def test_30_authored_team_size_min_one(self):
        self.broken_plan(authored_team_size=0)
    def test_31_authored_team_size_max_six(self):
        self.broken_plan(authored_team_size=7)
    def test_32_normal_preserves_authored_small_team(self):
        r=self.plan(authored_team_size=2)
        self.assertEqual(r["planned_team_size"],2)
        self.assertEqual(r["pending_synthetic_master_slots"],0)
    def test_33_master_expands_planned_three_to_four(self):
        r=self.plan(story_stage=3,authored_team_size=3)
        self.assertEqual(r["planned_team_size"],4)
        self.assertEqual(r["pending_synthetic_master_slots"],1)
        self.assertFalse(r["native_team_generated"])
    def test_34_master_expands_planned_one_to_four(self):
        r=self.plan(story_stage=3,authored_team_size=1)
        self.assertEqual(r["pending_synthetic_master_slots"],3)
    def test_35_master_preserves_four_original(self):
        r=self.plan(story_stage=3,authored_team_size=4)
        self.assertEqual(r["planned_team_size"],4)
        self.assertEqual(r["pending_synthetic_master_slots"],0)
    def test_36_master_preserves_five_and_six(self):
        for count in (5,6):
            with self.subTest(count=count):
                self.assertEqual(self.plan(story_stage=3,
                    authored_team_size=count)["planned_team_size"],count)
    def test_37_first_challenge_preserves_species_and_moves(self):
        r=self.plan(story_stage=3)
        self.assertTrue(r["first_challenge_preserves_authored_species"])
        self.assertTrue(r["first_challenge_preserves_authored_moves"])
        self.assertFalse(r["apply_bst_replacement_to_first_challenge"])
        self.assertFalse(r["apply_base_power_cap_to_first_challenge"])
    def test_38_first_challenge_no_real_badge_award(self):
        r=self.plan()
        self.assertFalse(r["badge_awarded"])
        self.assertFalse(r["original_pbs_mutated"])
        self.assertFalse(r["can_install"])
    def test_39_full_power_unverified_roster_blocked(self):
        self.broken_plan(challenge_kind="FULL_POWER_REMATCH")
    def test_40_unexpected_boss_rematch_blocked(self):
        self.broken_plan(challenge_kind="REMATCH")
    def test_41_unknown_leader_contract_blocked(self):
        self.broken_plan(leader_id="UNOVA_G032_LEADER_99")
    def test_42_unknown_first_challenge_badges_blocked(self):
        self.broken_plan(earned_badges=["TRIO"])
    def test_43_striaton_wrong_starter_rejected(self):
        self.broken_plan(starter_choice="PIKACHU")
    def test_44_striaton_starter_missing_rejected(self):
        self.broken_plan(starter_choice=None)
    def test_45_striaton_each_branch_valid(self):
        for starter,leader in (("SNIVY","CHILI"),("TEPIG","CRESS"),
                              ("OSHAWOTT","CILAN")):
            with self.subTest(starter=starter):
                self.assertEqual(self.plan(starter_choice=starter)["leader_key"],leader)
    def test_46_non_striaton_starter_override_blocked(self):
        self.broken_plan(leader_id="UNOVA_G032_LEADER_02",
                         earned_badges=["TRIO"],starter_choice="SNIVY")
    def test_47_lenora_requires_trio_badge(self):
        r=self.plan(leader_id="UNOVA_G032_LEADER_02",
                    earned_badges=["TRIO"],starter_choice=None)
        self.assertEqual(r["leader_key"],"LENORA")
        self.assertEqual(r["expected_badge"],"BASIC")
    def test_48_eighth_leader_requires_seven_badges(self):
        g=self.p["leaders"][7]
        r=self.plan(leader_id=g["id"],earned_badges=g["prerequisite_badges"],
                    starter_choice=None)
        self.assertEqual(r["leader_key"],"IRIS")
        self.assertEqual(r["expected_badge"],"LEGEND")
    def test_49_eighth_leader_missing_seventh_badge_blocked(self):
        g=self.p["leaders"][7]
        self.broken_plan(leader_id=g["id"],earned_badges=g["prerequisite_badges"][:-1],
                         starter_choice=None)
    def test_50_evolution_level_threshold_plus_five(self):
        self.assertEqual(self.evolve(level=20)["final"],"FIXTURE_BASE")
        self.assertEqual(self.evolve(level=21)["final"],"FIXTURE_STAGE2")
    def test_51_second_evolution_plus_five_threshold(self):
        self.assertEqual(self.evolve(level=40)["final"],"FIXTURE_STAGE2")
        self.assertEqual(self.evolve(level=41)["final"],"FIXTURE_FINAL")
    def test_52_evolution_method_thresholds_shared(self):
        self.assertEqual(self.p["evolution"]["method_thresholds"],
            {"LEVEL_PLUS_GRACE":5,"STONE":30,"TRADE":40,"FRIENDSHIP":45})
    def test_53_stone_evolution_30_not_29(self):
        graph={"FIXTURE_BASE":[{"to":"FIXTURE_STONE",
              "method":"STONE","requirement":None,"condition":"NONE"}]}
        self.assertEqual(self.evolve(level=29,edges=graph)["final"],"FIXTURE_BASE")
        self.assertEqual(self.evolve(level=30,edges=graph)["final"],"FIXTURE_STONE")
    def test_54_trade_evolution_40(self):
        graph={"FIXTURE_BASE":[{"to":"FIXTURE_TRADE",
              "method":"TRADE","requirement":None,"condition":"NONE"}]}
        self.assertEqual(self.evolve(level=39,edges=graph)["final"],"FIXTURE_BASE")
        self.assertEqual(self.evolve(level=40,edges=graph)["final"],"FIXTURE_TRADE")
    def test_55_friendship_evolution_45(self):
        graph={"FIXTURE_BASE":[{"to":"FIXTURE_FRIEND",
              "method":"FRIENDSHIP","requirement":None,"condition":"NONE"}]}
        self.assertEqual(self.evolve(level=44,edges=graph)["final"],"FIXTURE_BASE")
        self.assertEqual(self.evolve(level=45,edges=graph)["final"],"FIXTURE_FRIEND")
    def test_56_ambiguous_evolution_branch_blocked(self):
        graph={"FIXTURE_BASE":[
            {"to":"FIXTURE_FIRE","method":"STONE","requirement":None,"condition":"NONE"},
            {"to":"FIXTURE_WATER","method":"STONE","requirement":None,"condition":"NONE"}]}
        r=self.evolve(level=50,edges=graph)
        self.assertEqual(r["final"],"FIXTURE_BASE")
        self.assertEqual(r["status"],"AMBIGUOUS_BRANCH_BLOCKED")
    def test_57_special_base_species_not_evolved(self):
        r=self.evolve(level=99,special=["FIXTURE_BASE"])
        self.assertEqual(r["final"],"FIXTURE_BASE")
        self.assertEqual(r["status"],"SPECIAL_SPECIES_BLOCKED")
    def test_58_special_target_species_skipped(self):
        r=self.evolve(level=99,special=["FIXTURE_STAGE2"])
        self.assertEqual(r["final"],"FIXTURE_BASE")
    def test_59_gender_condition_not_guessed(self):
        graph={"FIXTURE_BASE":[{"to":"FIXTURE_MALE",
            "method":"LEVEL","requirement":16,"condition":"MALE"}]}
        self.assertEqual(self.evolve(level=21,edges=graph)["final"],"FIXTURE_BASE")
        self.assertEqual(self.evolve(level=21,edges=graph,
            context={"gender":"MALE"})["final"],"FIXTURE_MALE")
    def test_60_time_condition_not_guessed(self):
        graph={"FIXTURE_BASE":[{"to":"FIXTURE_DAY",
            "method":"LEVEL","requirement":16,"condition":"DAY"}]}
        self.assertEqual(self.evolve(level=21,edges=graph)["final"],"FIXTURE_BASE")
        self.assertEqual(self.evolve(level=21,edges=graph,
            context={"time":"DAY"})["final"],"FIXTURE_DAY")
    def test_61_unsupported_evolution_method_rejected(self):
        graph={"FIXTURE_BASE":[{"to":"FIXTURE_SPECIAL",
            "method":"MOVE","requirement":None,"condition":"NONE"}]}
        self.broken_evo(level=60,edges=graph)
    def test_62_evolution_native_species_unverified_rejected(self):
        self.broken_evo(base="BULBASAUR",level=80)
    def test_63_evolution_forged_real_target_rejected(self):
        graph={"FIXTURE_BASE":[{"to":"VENUSAUR",
            "method":"LEVEL","requirement":16,"condition":"NONE"}]}
        self.broken_evo(level=22,edges=graph)
    def test_64_evolution_invalid_level_boolean_rejected(self):
        self.broken_evo(level=True)
    def test_65_evolution_unsupported_context_rejected(self):
        self.broken_evo(level=80,context={"weather":"rain"})
    def test_66_evolution_invalid_gender_rejected(self):
        self.broken_evo(level=80,context={"gender":"UNKNOWN"})
    def test_67_evolution_requirement_invalid_rejected(self):
        graph={"FIXTURE_BASE":[{"to":"FIXTURE_STAGE2",
           "method":"LEVEL","requirement":"16","condition":"NONE"}]}
        self.broken_evo(level=30,edges=graph)
    def test_68_evolution_stone_forged_requirement_rejected(self):
        graph={"FIXTURE_BASE":[{"to":"FIXTURE_STONE",
           "method":"STONE","requirement":24,"condition":"NONE"}]}
        self.broken_evo(level=60,edges=graph)
    def test_69_evolution_cycle_blocked(self):
        graph={"FIXTURE_BASE":[{"to":"FIXTURE_STAGE2",
            "method":"LEVEL","requirement":10,"condition":"NONE"}],
            "FIXTURE_STAGE2":[{"to":"FIXTURE_BASE",
            "method":"LEVEL","requirement":10,"condition":"NONE"}]}
        r=self.evolve(level=60,edges=graph)
        self.assertEqual(r["final"],"FIXTURE_STAGE2")
        self.assertEqual(r["status"],"CYCLE_BLOCKED")
    def test_70_evolution_does_not_mutate_graph(self):
        original=copy.deepcopy(self.family)
        self.evolve(level=80)
        self.assertEqual(self.family,original)
    def test_71_coverage_rank_resistance_over_weakness(self):
        r=self.cover()
        self.assertEqual(r["ranked_candidates"][0]["species"],"FIXTURE_RESIST")
        self.assertGreater(r["ranked_candidates"][0]["score"],
                           r["ranked_candidates"][1]["score"])
    def test_72_coverage_threats_account_for_two_weaknesses(self):
        self.assertEqual(self.cover()["threats"],{"FIRE":2,"GROUND":2})
    def test_73_coverage_immune_partner_gets_highest_score(self):
        candidates=copy.deepcopy(self.candidates)
        candidates.append({"species":"FIXTURE_IMMUNE","types":["STEEL"],
            "bst":480,"multipliers":{"FIRE":0,"GROUND":0},
            "special_flags":[],"synthetic_only":True})
        r=self.cover(candidates=candidates)
        self.assertEqual(r["ranked_candidates"][0]["species"],"FIXTURE_IMMUNE")
    def test_74_coverage_no_threats_still_ranks_by_new_types(self):
        party=[{"species":"FIXTURE_EXISTING","types":["GRASS"],
                "multipliers":{"FIRE":0.5,"GROUND":0.5}}]
        r=self.cover(party=party)
        self.assertEqual(r["threats"],{})
    def test_75_coverage_candidate_scores_are_synthetic_only(self):
        r=self.cover()
        self.assertFalse(r["native_type_effectiveness_verified"])
        self.assertFalse(r["can_add_to_real_team"])
        self.assertTrue(all(x["native_species_verified"] is False
                            for x in r["ranked_candidates"]))
    def test_76_coverage_no_candidates_returns_empty(self):
        self.assertEqual(self.cover(candidates=[])["ranked_candidates"],[])
    def test_77_coverage_duplicate_candidate_rejected(self):
        self.broken_cover(candidates=[self.candidates[0],self.candidates[0]])
    def test_78_coverage_real_species_instead_of_fixture_rejected(self):
        c=copy.deepcopy(self.candidates)
        c[0]["species"]="RESHIRAM"
        self.broken_cover(candidates=c)
    def test_79_coverage_legendary_candidate_rejected(self):
        c=copy.deepcopy(self.candidates)
        c[0]["special_flags"]=["Legendary"]
        self.broken_cover(candidates=c)
    def test_80_coverage_paradox_candidate_rejected(self):
        c=copy.deepcopy(self.candidates)
        c[0]["special_flags"]=["PARADOX"]
        self.broken_cover(candidates=c)
    def test_81_coverage_candidate_bst_below_shared_pool_blocked(self):
        c=copy.deepcopy(self.candidates)
        c[0]["bst"]=439
        self.broken_cover(candidates=c)
    def test_82_coverage_candidate_bst_above_shared_pool_blocked(self):
        c=copy.deepcopy(self.candidates)
        c[0]["bst"]=571
        self.broken_cover(candidates=c)
    def test_83_coverage_invalid_multiplier_rejected(self):
        c=copy.deepcopy(self.candidates)
        c[0]["multipliers"]["FIRE"]=3
        self.broken_cover(candidates=c)
    def test_84_coverage_missing_multiplier_rejected(self):
        c=copy.deepcopy(self.candidates)
        c[0]["multipliers"].pop("GROUND")
        self.broken_cover(candidates=c)
    def test_85_coverage_forbid_unreal_typing(self):
        c=copy.deepcopy(self.candidates)
        c[0]["types"]=["???"]
        self.broken_cover(candidates=c)
    def test_86_coverage_forbid_unverified_candidate(self):
        c=copy.deepcopy(self.candidates)
        c[0]["synthetic_only"]=False
        self.broken_cover(candidates=c)
    def test_87_coverage_duplicate_attack_type_rejected(self):
        self.broken_cover(attack_types=["FIRE","FIRE"])
    def test_88_coverage_forbid_zero_party_in_audit(self):
        self.broken_cover(party=[])
    def test_89_coverage_candidate_already_in_party_rejected(self):
        c=copy.deepcopy(self.candidates)
        c[0]["species"]="FIXTURE_EXISTING"
        self.broken_cover(candidates=c)
    def test_90_contract_forged_fixed_native_teams_rejected(self):
        self.broken_policy(lambda p:p["leaders"][0].update(trainer_party=["LILLIPUP"]))
    def test_91_contract_forged_native_level_rejected(self):
        self.broken_policy(lambda p:p["leaders"][0].update(trainer_levels=[10,20]))
    def test_92_contract_forged_mapid_rejected(self):
        self.broken_policy(lambda p:p["leaders"][4].update(source_map_id=518))
    def test_93_contract_wrong_white_leader_rejected(self):
        self.broken_policy(lambda p:p["leaders"][7].update(leader_key="DRAYDEN"))
    def test_94_contract_disable_master_4_policy_rejected(self):
        self.broken_policy(lambda p:p["team_policy"].update(master_team_target=3))
    def test_95_contract_change_normal_percent_rejected(self):
        self.broken_policy(lambda p:p["level_cap"].update(normal_percent=80))
    def test_96_contract_change_master_percent_rejected(self):
        self.broken_policy(lambda p:p["level_cap"].update(master_percent=100))
    def test_97_contract_fake_numeric_badge_level_cap_rejected(self):
        self.broken_policy(lambda p:p["level_cap"].update(regional_numeric_cap_in_save=30))
    def test_98_contract_enable_bst_first_leader_rejected(self):
        self.broken_policy(lambda p:p["first_challenge"].update(skip_bst_replacement=False))
    def test_99_contract_enable_power_cap_first_leader_rejected(self):
        self.broken_policy(lambda p:p["first_challenge"].update(skip_move_base_power_cap=False))
    def test_100_contract_unverified_full_power_enabled_rejected(self):
        self.broken_policy(lambda p:p["first_challenge"].update(full_power_rematches_enabled=True))
    def test_101_contract_forged_native_approval_rejected(self):
        self.broken_policy(lambda p:p.update(game_exe_tested=True))
    def test_102_contract_forged_can_install_rejected(self):
        self.broken_policy(lambda p:p.update(can_install=True))
    def test_103_contract_enable_real_species_evolution_rejected(self):
        self.broken_policy(lambda p:p["evolution"].update(unverified_native_species_blocked=False))
    def test_104_contract_claim_native_type_coverage_rejected(self):
        self.broken_policy(lambda p:p["coverage"].update(never_assert_native_type_matrix=False))
    def test_105_contract_duplicate_gym_rejected(self):
        self.broken_policy(lambda p:p["leaders"].append(copy.deepcopy(p["leaders"][0])))
    def test_106_contract_unova_status_requires_planned(self):
        reg=copy.deepcopy(self.registry)
        reg["regions"]["UNOVA"]["status"]="playable"
        with self.assertRaises(ValueError):
            bal.validate_policy(self.p,self.gyms,self.shared,self.evo,reg,self.species)
    def test_107_contract_shared_90_percent_drift_rejected(self):
        shared=copy.deepcopy(self.shared)
        shared["rules"]["master_percent"]=100
        with self.assertRaises(ValueError):
            bal.validate_policy(self.p,self.gyms,shared,self.evo,self.registry,self.species)
    def test_108_contract_empty_species_source_rejected(self):
        with self.assertRaises(ValueError):
            bal.validate_policy(self.p,self.gyms,self.shared,self.evo,self.registry,{})
    def test_109_demo_offline_only(self):
        result=bal.demo(self.p)
        self.assertEqual(result["scaled_synthetic_target_level"],36)
        self.assertEqual(result["master_missing_slots"],1)
        self.assertEqual(result["best_synthetic_coverage"],"FIXTURE_RESIST")
        self.assertFalse(result["real_team_generated"])
    def test_110_cli_check_offline(self):
        run=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g03_leader_scaling.py"),
            "--check"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertEqual(json.loads(run.stdout)["leaders"],8)
    def test_111_cli_demo_offline(self):
        run=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g03_leader_scaling.py"),
            "--simulate-demo"],cwd=ROOT,text=True,capture_output=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        self.assertFalse(json.loads(run.stdout)["can_install"])
    def test_112_contract_snapshot_no_native_data(self):
        self.assertTrue(all(x["can_install"] is False and
            x["real_battle_verified"] is False and x["source_map_id"] is None
            for x in self.p["leaders"]))
    def test_113_coverage_inputs_are_not_mutated(self):
        before=(copy.deepcopy(self.threat_party),copy.deepcopy(self.candidates))
        self.cover()
        self.assertEqual(before[0],self.threat_party)
        self.assertEqual(before[1],self.candidates)
    def test_114_evolution_with_missing_edge_does_not_guess(self):
        self.assertEqual(self.evolve(base="FIXTURE_UNKNOWN",level=80)["final"],
                         "FIXTURE_UNKNOWN")
    def test_115_master_bst_stage_is_unlimited_but_not_numeric_cap(self):
        r=self.plan(story_stage=3)
        self.assertIsNone(r["bst_stage_cap"])
        self.assertIsNone(r["regional_badge_numeric_level_cap"])
    def test_116_all_leader_prerequisite_badges_match_gym_contract(self):
        for leader,gym in zip(self.p["leaders"],self.gyms["gyms"]):
            with self.subTest(gym=leader["id"]):
                self.assertEqual(leader["prerequisite_badges"],gym["previous_badges"])
    def test_117_difficulty_variants_distinct_no_arbitrary_80_percent(self):
        self.assertEqual(self.p["difficulty_variants"],
            [{"id":"NORMAL","requires_stage":0,"percent":70,"master":False},
             {"id":"MASTER","requires_stage":3,"percent":90,"master":True}])
    def test_118_first_challenge_protection_holds_in_master_stage(self):
        self.assertFalse(self.plan(story_stage=3)["apply_base_power_cap_to_first_challenge"])
        self.assertFalse(self.plan(story_stage=3)["apply_bst_replacement_to_first_challenge"])
    def test_119_coverage_defensive_threats_reduce_with_resistant_member(self):
        party=copy.deepcopy(self.threat_party)
        party.append({"species":"FIXTURE_WALL","types":["WATER"],
                      "multipliers":{"FIRE":0.5,"GROUND":0.5}})
        r=self.cover(party=party)
        self.assertEqual(r["threats"],{"FIRE":1,"GROUND":1})
    def test_120_no_direct_pokemon_essentials_calls_in_demo(self):
        report=bal.demo(self.p)
        self.assertFalse(report["game_exe_tested"])
        self.assertEqual(report["regional_numeric_cap_in_save"],None)

if __name__=="__main__":
    unittest.main()
