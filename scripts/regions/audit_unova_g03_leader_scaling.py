#!/usr/bin/env python3
"""Unova G03.2: offline gym leader scaling/evolution/coverage contracts.

All dynamic species/effectiveness inputs are expressly SYNTHETIC test fixtures.
The real Pokémon Essentials engine remains the only native type/evolution source.
Never reads or changes Game.exe, maps, PBS, saves, Pokémon or team data.
"""
from __future__ import annotations
import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

import audit_unova_g01_chapter_machine as g01
import audit_unova_g02_gym_story as g02

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"data/regions/unova-g03-leader-scaling-contracts.json"
TYPES=frozenset({"NORMAL","FIRE","WATER","ELECTRIC","GRASS","ICE",
    "FIGHTING","POISON","GROUND","FLYING","PSYCHIC","BUG","ROCK",
    "GHOST","DRAGON","DARK","STEEL","FAIRY"})
SPECIAL=frozenset({"LEGENDARY","MYTHICAL","ULTRABEAST","PARADOX",
    "PENDING","DESSASTREPARADOXAL","REGIONAL","REGIONALFORM",
    "CONVERGENT","MEGA","GIGANTAMAX"})
PROFILE_TYPES=(("FIRE","WATER","GRASS"),("NORMAL",),("BUG",),
 ("ELECTRIC",),("GROUND",),("FLYING",),("ICE",),("DRAGON",))
METHODS={"LEVEL":"LEVEL_PLUS_GRACE","STONE":"STONE",
         "TRADE":"TRADE","FRIENDSHIP":"FRIENDSHIP"}
CONDITIONS=frozenset({"NONE","MALE","FEMALE","DAY","NIGHT"})
IDENT=re.compile(r"FIXTURE_[A-Z0-9_]+\Z")
MODES=("NORMAL","MASTER")

def deny(why:str)->None:
    raise ValueError("UNOVA_G03_2_BLOCKED: "+why)

def exact(obj:Any,keys:set[str],name:str)->None:
    if not isinstance(obj,dict) or set(obj)!=keys:
        deny(name+" must have exactly required fields")

def load_project(root:Path=ROOT)->tuple[dict,dict,dict,dict]:
    root=Path(root)
    policy=g01._safe_source(root/"data/regions/unova-g03-leader-scaling-contracts.json")
    gyms=g01._safe_source(root/policy["sources"]["gyms"])
    shared=g01._safe_source(root/policy["sources"]["shared_balance"])
    evo=g01._safe_source(root/policy["sources"]["shared_evolution"])
    region=g01._safe_source(root/policy["sources"]["region_registry"])
    species=g01._safe_source(root/policy["sources"]["species_index"])
    validate_policy(policy,gyms,shared,evo,region,species)
    return policy,gyms,shared,evo

def validate_policy(policy:dict,gyms:dict,shared:dict,evo:dict,
                    region:dict,species:dict)->dict:
    exact(policy,{"schema","phase","region","campaign","status","sources",
        "level_cap","team_policy","evolution","coverage","first_challenge",
        "difficulty_variants","leaders","native_pbs_compiled",
        "native_team_catalog_verified","native_maps_installed",
        "game_exe_tested","android_tested","gameplay_verified","can_install",
        "notes"},"G03.2 policy")
    source_paths={"gyms":"data/regions/unova-g02-gym-story-contracts.json",
        "progress":"data/regions/unova-g01-state-contract.json",
        "battle":"scripts/battle_polish/Campaign.rb",
        "evolution":"scripts/battle_polish/EvolutionScaling.rb",
        "story":"scripts/battle_polish/Story.rb",
        "shared_balance":"data/regions/sinnoh-trainer-balance-s17.json",
        "shared_evolution":"data/regions/sinnoh-trainer-evolution-contract.json",
        "species_index":"data/national-species.json",
        "region_registry":"site/public/data/regions.json"}
    expected_top={"schema":1,"phase":"G03.2","region":"UNOVA",
        "campaign":"WHITE_BW",
        "status":"OFFLINE_GYM_SCALING_CONTRACT_NOT_NATIVE_TEAMS",
        "sources":source_paths,
        "native_pbs_compiled":False,
        "native_team_catalog_verified":False,
        "native_maps_installed":False,"game_exe_tested":False,
        "android_tested":False,"gameplay_verified":False,"can_install":False}
    for key,val in expected_top.items():
        if type(policy.get(key)) is not type(val) or policy[key]!=val:
            deny("catalog or native status drift: "+key)
    if (shared.get("rules",{}).get("normal_percent")!=70 or
        shared["rules"]["master_percent"]!=90 or
        shared["rules"]["master_requires_stage"]!=3 or
        shared["rules"]["master_team_target"]!=4 or
        shared["rules"]["max_opponents_per_side"]!=6 or
        evo["level_cap"]["regional_numeric_cap_in_save"] is not None or
        evo["level_cap"]["bst_cap_is_not_a_level_cap"] is not True or
        evo["balance"]["evolution_after_scaling"] is not True):
        deny("shared 70/90 Master and no-native-numeric-level-cap invariants drift")
    lc={"regional_numeric_cap_in_save":None,
        "numeric_badge_cap_implemented":False,
        "source_signal":"HIGHEST_NON_EGG_PARTY_LEVEL",
        "game_engine_upper_bound":"GameData::GrowthRate.max_level",
        "minimum":1,"normal_percent":70,"master_percent":90,
        "rounding":"INTEGER_FLOOR","normal_stage":0,"master_stage":3,
        "boss_stage_bst_caps":[350,450,540,None],
        "bst_cap_not_numeric_level_cap":True}
    team={"master_team_target":4,"max_opponents_per_side":6,
        "normal_preserves_authored_size":True,
        "master_preserves_native_teams_size_gte_4":True,
        "master_expands_only_synthetic_slots_in_qa":True,
        "original_pbs_unchanged":True,"no_native_team_generation":True}
    evolution={"method_thresholds":{"LEVEL_PLUS_GRACE":5,"STONE":30,
        "TRADE":40,"FRIENDSHIP":45},"max_steps":3,
        "strict_methods":["LEVEL","STONE","TRADE","FRIENDSHIP"],
        "conditional_gender_time_requires_explicit_context":True,
        "ambiguous_branch_blocked":True,"special_species_blocked":True,
        "unverified_native_species_blocked":True,
        "source":"GameData::Species#get_evolutions(true)"}
    coverage={"method":"EFFECTIVENESS_MULTIPLIER_INPUT_SYNTHETIC",
        "native_effectiveness_source":"Effectiveness.calculate",
        "candidate_source":"GameData::Species pool only at runtime",
        "valid_multipliers":[0,0.25,0.5,1,2,4],
        "threat_policy":"WEAKNESS_AGGREGATE_MINUS_RESISTANCE",
        "score_immunity":6,"score_resistance":4,"score_weakness_penalty":-4,
        "new_types_bonus":9,"never_assert_native_type_matrix":True,
        "synthetic_candidates_only":True,
        "coverage_guarantee_requires_native_party":True}
    first={"leader_preserves_authored_species":True,
        "leader_preserves_authored_moves":True,
        "skip_bst_replacement":True,"skip_move_base_power_cap":True,
        "full_power_rematch_requires_world_champion_profile":True,
        "full_power_rematch_requires_verified_team":True,
        "full_power_rematches_enabled":False,
        "never_award_second_badge":True}
    variants=[{"id":"NORMAL","requires_stage":0,"percent":70,"master":False},
        {"id":"MASTER","requires_stage":3,"percent":90,"master":True}]
    for key,val in {"level_cap":lc,"team_policy":team,"evolution":evolution,
                    "coverage":coverage,"first_challenge":first,
                    "difficulty_variants":variants}.items():
        if policy.get(key)!=val or type(policy[key]) is not type(val):
            deny("rule differs from existing shared Blue code: "+key)
    gym_list=gyms.get("gyms",[])
    if (gyms.get("phase")!="G02.2" or len(gym_list)!=8 or
        not isinstance(species,dict) or len(species)<1000 or
        region.get("regions",{}).get("UNOVA",{}).get("status")!="planned" or
        not isinstance(policy["leaders"],list) or len(policy["leaders"])!=8):
        deny("gyms, species reference or region readiness invalid")
    for idx,(leader,gym) in enumerate(zip(policy["leaders"],gym_list),1):
        keys={"id","gym_contract_id","chapter_key","leader_key",
             "leader_by_starter","first_challenge_badge","prerequisite_badges",
             "planned_specialty_types","specialty_status","trainer_type",
             "trainer_pbs_id","trainer_version","trainer_party",
             "trainer_levels","moves","ability_data","source_map_id",
             "real_battle_verified","can_install"}
        exact(leader,keys,"leader contract")
        wanted={"id":f"UNOVA_G032_LEADER_{idx:02d}",
            "gym_contract_id":gym["id"],"chapter_key":gym["chapter_key"],
            "leader_key":gym["leader_key"],
            "leader_by_starter":gym["leader_by_starter"],
            "first_challenge_badge":gym["badge"],
            "prerequisite_badges":gym["previous_badges"],
            "planned_specialty_types":list(PROFILE_TYPES[idx-1]),
            "specialty_status":"DESIGN_REFERENCE_NOT_NATIVE_SPECIES_TYPING",
            "trainer_type":"LEADER","trainer_pbs_id":None,
            "trainer_version":None,"trainer_party":None,
            "trainer_levels":None,"moves":None,"ability_data":None,
            "source_map_id":None,"real_battle_verified":False,
            "can_install":False}
        if leader!=wanted:deny("leader order, White variant or native team metadata invented")
    if not isinstance(policy["notes"],list) or len(policy["notes"])<4:
        deny("safety notes missing")
    return {"phase":"G03.2","leaders":8,"team_catalog_native_verified":False,
            "normal_percent":70,"master_percent":90,
            "regional_numeric_cap_in_save":None,
            "status":"OFFLINE_LEADER_SCALING_POLICY_VALIDATED",
            "game_exe_tested":False,"can_install":False}

def _int(value:Any,name:str,lo:int=0,hi:int=999999)->int:
    if type(value) is not int or not lo<=value<=hi:
        deny(name+" must be a bounded integer")
    return value

def _party_progress(party:list[dict],engine_max_level:int)->tuple[int,bool]:
    _int(engine_max_level,"engine_max_level",1,1000)
    if not isinstance(party,list) or len(party)>6:
        deny("synthetic party must be an array with at most 6 slots")
    eligible=[]
    for slot in party:
        exact(slot,{"level","egg"},"synthetic party member")
        _int(slot["level"],"party level",1,engine_max_level)
        if type(slot["egg"]) is not bool:
            deny("egg flag must be boolean")
        if not slot["egg"]:eligible.append(slot["level"])
    return min(max(eligible,default=1),engine_max_level),not bool(eligible)

def _leader(policy:dict,leader_id:str)->dict:
    for entry in policy["leaders"]:
        if entry["id"]==leader_id:return entry
    deny("unknown Unova gym leader reference")

def plan_battle(policy:dict,leader_id:str,*,party:list[dict],
                engine_max_level:int,story_stage:int,
                earned_badges:list[str],authored_team_size:int,
                starter_choice:str|None=None,
                challenge_kind:str="FIRST_CHALLENGE")->dict:
    """Contract plan only: no real team, slots, PBS or badge gets written."""
    gym=_leader(policy,leader_id)
    _int(story_stage,"story_stage",0,3)
    _int(authored_team_size,"authored_team_size",1,6)
    if challenge_kind!="FIRST_CHALLENGE":
        deny("Full Power or other rematch requires an audited native roster and world-champion profile")
    if not isinstance(earned_badges,list) or earned_badges!=gym["prerequisite_badges"]:
        deny("leader first challenge requires the exact previous regional badges")
    if gym["leader_by_starter"] is not None:
        if starter_choice not in {"SNIVY","TEPIG","OSHAWOTT"}:
            deny("Striaton requires a recorded original starter choice")
        leader=gym["leader_by_starter"][starter_choice]
    else:
        if starter_choice is not None:
            deny("non-Striaton gym must not receive synthetic starter override")
        leader=gym["leader_key"]
    progress,fallback=_party_progress(party,engine_max_level)
    master=story_stage==3
    pct=policy["level_cap"]["master_percent" if master else "normal_percent"]
    target=max(1,min(engine_max_level,progress*pct//100))
    planned_size=max(authored_team_size,4) if master else authored_team_size
    return {"phase":"G03.2","status":"SYNTHETIC_SCALING_PLAN_ONLY",
        "leader_contract_id":leader_id,"leader_key":leader,
        "chapter_key":gym["chapter_key"],"expected_badge":gym["first_challenge_badge"],
        "variant":"MASTER" if master else "NORMAL",
        "story_stage":story_stage,"bst_stage_cap":policy["level_cap"]["boss_stage_bst_caps"][story_stage],
        "progress_signal_level":progress,
        "no_non_egg_fallback":fallback,
        "regional_badge_numeric_level_cap":None,
        "percent":pct,"scaled_target_level":target,
        "authored_team_size":authored_team_size,"planned_team_size":planned_size,
        "pending_synthetic_master_slots":planned_size-authored_team_size,
        "native_team_generated":False,"original_pbs_mutated":False,
        "first_challenge_preserves_authored_species":True,
        "first_challenge_preserves_authored_moves":True,
        "apply_bst_replacement_to_first_challenge":False,
        "apply_base_power_cap_to_first_challenge":False,
        "badge_awarded":False,"game_exe_tested":False,"can_install":False}

def evolve_fixture(policy:dict,base:str,level:int,edges:dict,
                   *,context:dict|None=None,special:list[str]|None=None)->dict:
    """Synthetic evolution graph, never a hardcoded species Pokédex table."""
    _int(level,"level",1,1000)
    if not isinstance(base,str) or not IDENT.fullmatch(base):
        deny("evolution inputs must be labelled FIXTURE_*, not asserted native species")
    if not isinstance(edges,dict) or len(edges)>100 or any(
            not isinstance(k,str) or not IDENT.fullmatch(k) or
            not isinstance(v,list) or len(v)>12 for k,v in edges.items()):
        deny("synthetic evolution graph malformed")
    context={} if context is None else context
    exact(context,set(context),"evolution condition context")
    if set(context)-{"gender","time"}:
        deny("unsupported evolution context")
    if "gender" in context and context["gender"] not in {"MALE","FEMALE"}:
        deny("gender must be explicit")
    if "time" in context and context["time"] not in {"DAY","NIGHT"}:
        deny("time must be explicit")
    special=[] if special is None else special
    if not isinstance(special,list) or any(
        not isinstance(s,str) or not IDENT.fullmatch(s) for s in special):
        deny("invalid synthetic special species list")
    if base in special:
        return {"base":base,"final":base,"chain":[base],
                "status":"SPECIAL_SPECIES_BLOCKED","native_data_verified":False}
    current=base;chain=[current];status="NO_SAFE_EVOLUTION"
    for _ in range(policy["evolution"]["max_steps"]):
        options=edges.get(current,[])
        matches=[]
        for item in options:
            exact(item,{"to","method","requirement","condition"},"evolution edge")
            nxt=item["to"];method=item["method"];condition=item["condition"]
            if not isinstance(nxt,str) or not IDENT.fullmatch(nxt) or nxt==current:
                deny("invalid evolution fixture target")
            if not isinstance(method,str) or method not in METHODS:
                deny("unsupported evolution method; no invented branch")
            if condition not in CONDITIONS:
                deny("unsupported conditions; no guess")
            if method=="LEVEL":
                threshold=_int(item["requirement"],"level evolution threshold",1,1000)+5
            else:
                if item["requirement"] is not None:
                    deny("stone/trade/friendship threshold has no native parameter in this fixture")
                threshold=policy["evolution"]["method_thresholds"][METHODS[method]]
            if condition in {"MALE","FEMALE"} and context.get("gender")!=condition:
                continue
            if condition in {"DAY","NIGHT"} and context.get("time")!=condition:
                continue
            if level>=threshold and nxt not in special:
                matches.append((nxt,threshold))
        targets={m[0] for m in matches}
        if len(targets)>1:
            status="AMBIGUOUS_BRANCH_BLOCKED";break
        if not targets:break
        nxt=next(iter(targets))
        if nxt in chain:
            status="CYCLE_BLOCKED";break
        current=nxt;chain.append(current);status="SYNTHETIC_EVOLUTION_ONLY"
    return {"base":base,"final":current,"chain":chain,
            "status":status,"native_data_verified":False}

def _multipliers(m:dict,types:list[str],label:str)->None:
    if not isinstance(m,dict) or set(m)!=set(types) or any(
        type(x) not in (int,float) or x not in {0,0.25,0.5,1,2,4}
        for x in m.values()):
        deny(label+" must provide valid explicit synthetic Effectiveness multipliers")

def coverage_plan(policy:dict,*,attack_types:list[str],party:list[dict],
                  candidates:list[dict])->dict:
    """Score synthetic Master partners; never claim a verified native matchup."""
    if not isinstance(attack_types,list) or not attack_types or len(attack_types)>18 or (
        len(set(attack_types))!=len(attack_types)) or any(
        not isinstance(t,str) or t not in TYPES for t in attack_types):
        deny("unique known attack-type labels required")
    if not isinstance(party,list) or not 1<=len(party)<=6 or not isinstance(candidates,list) or len(candidates)>80:
        deny("bounded synthetic party and candidate lists required")
    used_types=set();used_species=set();threats={}
    for row in party:
        exact(row,{"species","types","multipliers"},"synthetic party member")
        key=row["species"]
        if not isinstance(key,str) or not IDENT.fullmatch(key) or key in used_species:
            deny("unique labelled synthetic party species required")
        used_species.add(key)
        t=row["types"]
        if not isinstance(t,list) or not 1<=len(t)<=2 or len(set(t))!=len(t) or any(x not in TYPES for x in t):
            deny("synthetic party types invalid")
        used_types.update(t)
        _multipliers(row["multipliers"],attack_types,"party")
    for attack in attack_types:
        multipliers=[p["multipliers"][attack] for p in party]
        weakness=sum(4 if v>=4 else 2 if v>1 else 0 for v in multipliers)
        resist=sum(v<1 for v in multipliers)
        if weakness>resist:threats[attack]=weakness-resist
    ranked=[];seen=set()
    for row in candidates:
        exact(row,{"species","types","bst","multipliers","synthetic_only","special_flags"},"candidate")
        key=row["species"]
        if not isinstance(key,str) or not IDENT.fullmatch(key) or key in used_species or key in seen:
            deny("candidate must be unique FIXTURE_* not an existing trainer species")
        seen.add(key)
        t=row["types"]
        if not isinstance(t,list) or not 1<=len(t)<=2 or len(set(t))!=len(t) or any(x not in TYPES for x in t):
            deny("candidate types invalid")
        if row["synthetic_only"] is not True or not isinstance(row["special_flags"],list) or any(
            not isinstance(x,str) for x in row["special_flags"]) or (
            set(row["special_flags"]) & SPECIAL):
            deny("candidate not an eligible ordinary synthetic species")
        bst=_int(row["bst"],"candidate BST",440,570)
        _multipliers(row["multipliers"],attack_types,"candidate")
        coverage=0
        for attack,risk in threats.items():
            mult=row["multipliers"][attack]
            coverage+=risk*(6 if mult==0 else 4 if mult<1 else -4 if mult>1 else 0)
        new_types=len(set(t)-used_types)
        score=coverage*3+new_types*9+(bst-440)//12
        ranked.append({"species":key,"score":score,
                       "threat_coverage":coverage,"new_types":new_types,
                       "native_species_verified":False})
    ranked.sort(key=lambda x:(-x["score"],x["species"]))
    return {"status":"SYNTHETIC_COVERAGE_ONLY",
        "threats":threats,"ranked_candidates":ranked,
        "native_type_effectiveness_verified":False,
        "can_add_to_real_team":False}

def demo(policy:dict)->dict:
    sample=plan_battle(policy,"UNOVA_G032_LEADER_01",
        party=[{"level":40,"egg":False},{"level":60,"egg":True}],
        engine_max_level=100,story_stage=3,earned_badges=[],
        authored_team_size=3,starter_choice="SNIVY")
    evo=evolve_fixture(policy,"FIXTURE_BASE",27,{
        "FIXTURE_BASE":[{"to":"FIXTURE_STAGE2","method":"LEVEL",
                         "requirement":16,"condition":"NONE"}],
        "FIXTURE_STAGE2":[{"to":"FIXTURE_STAGE3","method":"LEVEL",
                          "requirement":36,"condition":"NONE"}]})
    coverage=coverage_plan(policy,attack_types=["FIRE","GROUND"],
        party=[{"species":"FIXTURE_EXISTING","types":["GRASS"],
            "multipliers":{"FIRE":2,"GROUND":2}}],
        candidates=[
            {"species":"FIXTURE_RESIST","types":["WATER"],"bst":480,
             "multipliers":{"FIRE":0.5,"GROUND":0.5},
             "special_flags":[],"synthetic_only":True},
            {"species":"FIXTURE_WEAK","types":["ICE"],"bst":480,
             "multipliers":{"FIRE":2,"GROUND":2},
             "special_flags":[],"synthetic_only":True}])
    if sample["scaled_target_level"]!=36 or sample["pending_synthetic_master_slots"]!=1 or (
        evo["final"]!="FIXTURE_STAGE2" or
        coverage["ranked_candidates"][0]["species"]!="FIXTURE_RESIST"):
        deny("synthetic G03.2 regression demo invariant")
    return {"phase":"G03.2","status":"OFFLINE_BALANCE_DEMO_NOT_NATIVE",
        "master_scale_percent":sample["percent"],
        "scaled_synthetic_target_level":sample["scaled_target_level"],
        "master_missing_slots":sample["pending_synthetic_master_slots"],
        "evolution_result":evo["final"],
        "best_synthetic_coverage":coverage["ranked_candidates"][0]["species"],
        "regional_numeric_cap_in_save":None,"real_team_generated":False,
        "game_exe_tested":False,"can_install":False}

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--simulate-demo",action="store_true")
    args=parser.parse_args(argv)
    try:
        policy,gyms,shared,evo=load_project()
        region=g01._safe_source(ROOT/policy["sources"]["region_registry"])
        species=g01._safe_source(ROOT/policy["sources"]["species_index"])
        report=(validate_policy(policy,gyms,shared,evo,region,species)
                if args.check else demo(policy))
        print(json.dumps(report,sort_keys=True,ensure_ascii=False))
        return 0
    except (ValueError,TypeError,KeyError,IndexError,OSError,RecursionError) as exc:
        print("UNOVA_G03_2_BLOCKED: "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
