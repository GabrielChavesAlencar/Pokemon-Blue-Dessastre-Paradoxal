#!/usr/bin/env python3
"""Unova G03.4 — source-linked Elite Four/Alder difficulty contracts, offline only.

G02.3 owns campaign Elite wins; G02.4 owns rematch sessions and Alder's win.
G03.3 supplies the optional story-backed envelope. G03.2 supplies 70/90%
scaling and fixture-only defensive coverage. No real party, PBS, Game.exe,
map or save is ever loaded or modified. The Full Power variant is disabled.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import audit_unova_g01_chapter_machine as machine
import audit_unova_g01_serialization as codec
import audit_unova_g02_postgame as postgame
import audit_unova_g03_leader_scaling as balance
import audit_unova_g03_rivals_plasma as rivals

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"data/regions/unova-g03-elite-alder-rematch-contracts.json"
NAMES=("SHAUNTAL","GRIMSLEY","CAITLIN","MARSHAL","ALDER")
FIELD_NAMES={"schema","phase","region","campaign","status","sources",
    "campaign_entry_chapter","postgame_entry_chapter","campaign_order",
    "rematch_order","authoritative_story_ledger","authoritative_rematch_ledger",
    "reward_policy","level_policy","coverage_policy","full_power_policy",
    "postgame_session_limit","actors","native_game_modified",
    "native_saves_modified","real_battles_executed","real_pbs_compiled",
    "game_exe_tested","android_tested","can_install","notes"}
SOURCES={
    "g01":"data/regions/unova-g01-state-contract.json",
    "g02_finale":"data/regions/unova-g02-elite-finale-contracts.json",
    "g02_postgame":"data/regions/unova-g02-postgame-contracts.json",
    "g03_leaders":"data/regions/unova-g03-leader-scaling-contracts.json",
    "g03_rivals":"data/regions/unova-g03-rivals-plasma-story-contracts.json",
    "npc":"data/regions/unova-sp04-npcs.json",
    "trainer":"data/regions/unova-e06-e07-preparation.json"}
SCOPED_TYPES={"CAMPAIGN","REMATCH_NORMAL","REMATCH_MASTER","FULL_POWER_LOCKED"}
SUCCESS="APPLIED_SIMULATION"
ALREADY="ALREADY_RECORDED_NO_OP"
LOSS="BATTLE_LOST_RETRY_REQUIRED"
REENTER="REENTERED_READ_ONLY"

def deny(message:str)->None:
    raise ValueError("UNOVA_G03_4_BLOCKED: "+message)

def exact(value:Any,keys:set[str],label:str)->None:
    if not isinstance(value,dict) or set(value)!=keys:
        deny(label+" fields differ from versioned contract")

def load_project(root:Path=ROOT)->tuple:
    root=Path(root)
    ctx,gyms,finale,post,scaling,rival_catalog=rivals.load_project(root)
    data=machine._safe_source(root/"data/regions/unova-g03-elite-alder-rematch-contracts.json")
    npc_catalog=machine._safe_source(root/data["sources"]["npc"])
    trainers=machine._safe_source(root/data["sources"]["trainer"])
    validate_catalog(data,ctx,finale,post,scaling,rival_catalog,npc_catalog,trainers)
    return ctx,gyms,finale,post,scaling,rival_catalog,data

def validate_catalog(data:dict,ctx:tuple,finale:dict,post:dict,
                     scaling:dict,rival_catalog:dict,npcs:dict,trainers:dict)->dict:
    exact(data,FIELD_NAMES,"G03.4 catalog")
    top={"schema":1,"phase":"G03.4","region":"UNOVA","campaign":"WHITE_BW",
        "status":"OFFLINE_ELITE_ALDER_BATTLE_VARIANT_CONTRACTS",
        "sources":SOURCES,"campaign_entry_chapter":ctx[0]["chapters"][10]["key"],
        "postgame_entry_chapter":ctx[0]["chapters"][12]["key"],
        "campaign_order":"ANY_ORDER_FOUR_ELITE_NO_ALDER",
        "rematch_order":"ANY_ORDER_FOUR_ELITE_THEN_ALDER",
        "authoritative_story_ledger":"G02.3_ELITE_FOUR",
        "authoritative_rematch_ledger":"G02.4_REMATCH_SESSIONS",
        "reward_policy":"NO_NATIVE_REWARDS_OR_SECOND_BADGES",
        "postgame_session_limit":25,
        "native_game_modified":False,"native_saves_modified":False,
        "real_battles_executed":False,"real_pbs_compiled":False,
        "game_exe_tested":False,"android_tested":False,"can_install":False}
    for key,want in top.items():
        if type(data.get(key)) is not type(want) or data[key]!=want:
            deny("canonical source or false native approval: "+key)
    level={"normal_percent":70,"master_percent":90,
        "master_story_stage":3,"engine_cap_input_required":True,
        "highest_non_egg_party_level":True,
        "regional_numeric_level_cap":None,"synthetic_master_team_target":4,
        "max_team_size":6,"unknown_canonical_team_size":None,
        "first_challenge_preserves_original_party_and_moves":True}
    coverage={"source":"G03.2_EXPLICIT_SYNTHETIC_EFFECTIVENESS",
        "native_type_chart_verified":False,"native_species_verified":False,
        "fixture_only":True,"auto_add_pokemon":False}
    full={"enabled":False,"requires_world_champion_profile":True,
        "requires_ten_league_titles":True,
        "requires_native_verified_roster":True,
        "requires_native_verified_opponent":True,
        "world_champion_proof_source":None,"verified_team_source":None,
        "allow_synthetic_bypass":False}
    if data.get("level_policy")!=level or data.get("coverage_policy")!=coverage or (
        data.get("full_power_policy")!=full):
        deny("G03.2 rules or Full Power guards modified")
    if (scaling.get("phase")!="G03.2" or rival_catalog.get("phase")!="G03.3" or
        finale.get("phase")!="G02.3" or post.get("phase")!="G02.4" or
        scaling["level_cap"]["normal_percent"]!=70 or
        scaling["level_cap"]["master_percent"]!=90 or
        scaling["level_cap"]["regional_numeric_cap_in_save"] is not None or
        scaling["first_challenge"]["full_power_rematches_enabled"] is not False or
        post["league_rematch"]["champion_key"]!="ALDER" or
        post["league_rematch"]["max_sessions"]!=25 or
        len(finale["elite_members"])!=4):
        deny("G01/G02/G03 base or Full Power policy inconsistent")
    if not isinstance(data["notes"],list) or len(data["notes"])<5:
        deny("planned-only warnings absent")
    npc_map={x["key"]:x for x in npcs["characters"]}
    tr_map={x["key"]:x for x in trainers["trainer_references"]}
    actors=data.get("actors")
    if not isinstance(actors,list) or len(actors)!=5:
        deny("exactly four Elite + Alder required")
    variants_total=0
    for i,(actor,name) in enumerate(zip(actors,NAMES)):
        exact(actor,{"key","name","kind","npc_key","trainer_reference_key",
            "primary_area_key","source_campaign_key","source_rematch_key",
            "order_policy","variants","real_team","real_levels","real_moves",
            "real_abilities","native_trainer_id","native_event_id","source_map_id"},
            "Elite/Alder actor")
        npc_id="UNOVA_NPC_"+name;trainer_id="UNOVA_TRAINER_"+name
        trainer=tr_map.get(trainer_id);npc=npc_map.get(npc_id)
        if trainer is None or npc is None or (
            npc["trainer_reference_key"]!=trainer_id or
            npc["primary_area_key"]!=trainer["area_key"] or
            trainer["verified"] is not False or trainer["installed"] is not False or
            trainer["pbs_trainer_id"] is not None or trainer["team"]!=[] or
            trainer["level_reference"] is not None):
            deny("SP04/E07 actor missing or native team no longer unverified")
        source=finale["elite_members"][i]["key"] if i<4 else None
        expected={"key":"UNOVA_G034_ACTOR_"+name,"name":name,
            "kind":"ELITE_FOUR" if i<4 else "CHAMPION_POSTGAME",
            "npc_key":npc_id,"trainer_reference_key":trainer_id,
            "primary_area_key":trainer["area_key"],"source_campaign_key":source,
            "source_rematch_key":(post["league_rematch"]["elite_members"][i]
                if i<4 else post["league_rematch"]["champion_key"]),
            "order_policy":"ANY_ORDER_ONCE_PER_SESSION" if i<4 else
                "AFTER_FOUR_UNIQUE_ELITE_WINS",
            "real_team":None,"real_levels":None,"real_moves":None,
            "real_abilities":None,"native_trainer_id":None,
            "native_event_id":None,"source_map_id":None}
        for key,want in expected.items():
            if key not in actor or actor[key]!=want or type(actor[key]) is not type(want):
                deny("Elite or Alder references differ from authoritative G02 sources")
        modes=(("CAMPAIGN",) if i<4 else ())+(
            "REMATCH_NORMAL","REMATCH_MASTER","FULL_POWER_LOCKED")
        if not isinstance(actor["variants"],list) or len(actor["variants"])!=len(modes):
            deny("variants missing or invented")
        for variant,mode in zip(actor["variants"],modes):
            exact(variant,{"key","mode","access","eligible","story_stage",
                "real_team","real_levels","real_moves","native_pbs_id",
                "source_verified","native_battle_executable"},"team variant")
            target={"key":"UNOVA_G034_"+name+"_"+mode,
                "mode":mode,"access":"CH10_LEAGUE" if mode=="CAMPAIGN"
                    else "CH12_POSTGAME","eligible":mode!="FULL_POWER_LOCKED",
                "story_stage":3 if mode=="REMATCH_MASTER" else None,
                "real_team":None,"real_levels":None,"real_moves":None,
                "native_pbs_id":None,"source_verified":False,
                "native_battle_executable":False}
            if variant!=target:
                deny("invented team, fake native status or unexpected variant")
            variants_total+=1
    return {"phase":"G03.4","elite_members":4,"champion":"ALDER",
        "source_linked_actors":5,"stable_variants":variants_total,
        "normal_percent":70,"master_percent":90,
        "full_power_enabled":False,"real_pbs_compiled":False,
        "game_exe_tested":False,"can_install":False}

def actor_by_name(data:dict,name:str)->dict:
    if not isinstance(name,str):
        deny("actor name required")
    for actor in data["actors"]:
        if actor["name"]==name:return actor
    deny("unknown Elite or Champion actor")

def _chapter(env:dict,ctx:tuple)->int:
    return rivals._state_index(env,ctx)

def _post(env:dict)->dict:
    return env["g024_envelope"]

def validate_envelope(env:dict,ctx:tuple,gyms:dict,finale:dict,
                      post:dict,rival_catalog:dict)->dict:
    return rivals.validate_envelope(env,ctx,gyms,finale,post,rival_catalog)

def _battle_source_status(env:dict,ctx:tuple,actor:dict)->str:
    if actor["source_campaign_key"] is None:
        deny("Alder is postgame only in Pokémon White")
    chapter=_chapter(env,ctx)
    if chapter<10:
        deny("first Elite battle requires original CH10 after eight badges")
    wins={r["member_key"] for r in _post(env)["g023_envelope"]["elite_wins"]}
    return "WIN_RECORDED_IN_G02_3" if actor["source_campaign_key"] in wins else (
        "AVAILABLE_UNPROVEN_NATIVE" if chapter==10 else
        "NOT_WON_IN_G02_3")

def inspect_campaign(env:dict,ctx:tuple,gyms:dict,finale:dict,
                     post:dict,rival_catalog:dict,data:dict, *,actor_name:str)->dict:
    validate_envelope(env,ctx,gyms,finale,post,rival_catalog)
    actor=actor_by_name(data,actor_name)
    return {"status":_battle_source_status(env,ctx,actor),
        "source_member_key":actor["source_campaign_key"],
        "native_battle_verified":False,"game_exe_tested":False,
        "can_install":False}

def plan_team(env:dict,ctx:tuple,gyms:dict,finale:dict,post:dict,
              rival_catalog:dict,scaling:dict,data:dict, *,actor_name:str,
              mode:str,party:list[dict],engine_max_level:int,
              story_stage:int,synthetic_authored_team_size:int|None=None,
              fixture_coverage:dict|None=None)->dict:
    """Read-only plan: cannot create actual teams or bypass locked Full Power."""
    validate_envelope(env,ctx,gyms,finale,post,rival_catalog)
    actor=actor_by_name(data,actor_name)
    selected=next((x for x in actor["variants"] if x["mode"]==mode),None)
    if selected is None or not selected["eligible"] or mode=="FULL_POWER_LOCKED":
        deny("no verified native roster / ten-title proof for Full Power")
    balance._int(story_stage,"story_stage",0,3)
    chapter=_chapter(env,ctx)
    if mode=="CAMPAIGN":
        if chapter!=10 or actor["kind"]!="ELITE_FOUR":
            deny("White campaign first Elite requires CH10 and cannot include Alder")
        if _battle_source_status(env,ctx,actor)!="AVAILABLE_UNPROVEN_NATIVE":
            deny("original Elite battle already recorded or outside CH10")
    else:
        if chapter!=12:deny("postgame rematch requires G02.3 credits and CH12")
        session=_post(env)["active_rematch"]
        if not isinstance(session,dict):deny("G02.4 rematch session must be active")
        if mode=="REMATCH_MASTER" and story_stage!=3:
            deny("Master rematch requires stage 3")
        if mode=="REMATCH_NORMAL" and story_stage==3:
            deny("stage 3 must use Master")
        if actor["kind"]=="ELITE_FOUR":
            if actor["source_rematch_key"] in session["elite_wins"]:
                deny("already recorded this member in active session")
            if session["alder_won"]:
                deny("Elite is closed after Alder")
        else:
            if session["alder_won"] or len(session["elite_wins"])!=4:
                deny("Alder only after all four unique Elite wins in same session")
    progress,fallback=balance._party_progress(party,engine_max_level)
    percent=scaling["level_cap"]["master_percent" if story_stage==3 else
                                "normal_percent"]
    if synthetic_authored_team_size is not None:
        balance._int(synthetic_authored_team_size,
                     "synthetic_authored_team_size",1,6)
    desired=max(synthetic_authored_team_size,4) if (
        synthetic_authored_team_size is not None and story_stage==3
        ) else synthetic_authored_team_size
    if fixture_coverage is None:
        summary=None
    else:
        balance.exact(fixture_coverage,{"attack_types","party","candidates"},
                      "coverage fixture")
        summary=balance.coverage_plan(scaling,**fixture_coverage)
    return {"phase":"G03.4","status":"OFFLINE_TEAM_VARIANT_PREVIEW",
        "actor_id":actor["key"],"variant_key":selected["key"],
        "source_campaign_key":actor["source_campaign_key"],
        "source_rematch_key":actor["source_rematch_key"],
        "mode":mode,"difficulty":"MASTER" if story_stage==3 else "NORMAL",
        "progress_signal_level":progress,"no_non_egg_fallback":fallback,
        "scale_percent":percent,
        "synthetic_target_level":max(1,min(engine_max_level,progress*percent//100)),
        "regional_numeric_level_cap":None,
        "synthetic_authored_team_size":synthetic_authored_team_size,
        "synthetic_target_team_size":desired,
        "synthetic_missing_slots":desired-synthetic_authored_team_size if
            desired is not None else None,
        "fixture_coverage":summary,
        "canonical_species":None,"canonical_moves":None,"canonical_levels":None,
        "native_type_coverage_verified":False,"native_evolution_applied":False,
        "native_team_generated":False,"native_pbs_mutated":False,
        "real_rewards_granted":False,"game_exe_tested":False,"can_install":False}

def step_rematch(env:dict,ctx:tuple,gyms:dict,finale:dict,post:dict,
                 rival_catalog:dict,data:dict,action:str, *,
                 session_id:int,actor_name:str|None=None,
                 outcome:str|None=None)->dict:
    """Delegate every mutation to G02.4, never fork rematch receipts."""
    validate_envelope(env,ctx,gyms,finale,post,rival_catalog)
    if _chapter(env,ctx)!=12:
        deny("rematch progression requires completed credits and postgame")
    if type(session_id) is not int or not 1<=session_id<=data["postgame_session_limit"]:
        deny("session ID must be bounded integer")
    if action in {"start","finish"}:
        if actor_name is not None or outcome is not None:
            deny("start/finish must not carry a battle or trainer claim")
        op="start_rematch" if action=="start" else "finish_rematch"
        kw={"session_id":session_id}
    elif action=="battle":
        actor=actor_by_name(data,actor_name)
        if outcome not in {"WIN","LOSS"}:
            deny("rematch battle needs explicit WIN/LOSS")
        op=("rematch_alder" if actor["name"]=="ALDER"
            else "rematch_elite")
        kw={"session_id":session_id,"outcome":outcome}
        if op=="rematch_elite":
            kw["member_key"]=actor["source_rematch_key"]
    else:
        deny("unrecognized G03.4 battle operation")
    response=postgame.apply(_post(env),ctx,gyms,finale,post,op,**kw)
    next_env=copy.deepcopy(env)
    next_env["g024_envelope"]=response["envelope"]
    validate_envelope(next_env,ctx,gyms,finale,post,rival_catalog)
    return {"status":response["status"],"envelope":next_env,
        "suggested_safe_return_area_key":response["suggested_safe_return_area_key"],
        "source_authority":"G02.4_REMATCH_SESSIONS",
        "native_teleport_executed":False,"native_battles_executed":False,
        "native_saves_modified":False,"real_rewards_granted":False,
        "real_badges_granted":False,"game_exe_tested":False,"can_install":False}

def demo(ctx:tuple,gyms:dict,finale:dict,post:dict,scaling:dict,
         rival_catalog:dict,data:dict)->dict:
    env,checkpoints=rivals.build_demo(ctx,gyms,finale,post,scaling,rival_catalog)
    league=checkpoints["CH10_LEAGUE"]
    names=[x["name"] for x in data["actors"][:4]]
    first=plan_team(league,ctx,gyms,finale,post,rival_catalog,scaling,data,
        actor_name=names[0],mode="CAMPAIGN",
        party=[{"level":40,"egg":False},{"level":90,"egg":True}],
        engine_max_level=100,story_stage=0)
    if first["synthetic_target_level"]!=28:
        deny("G03.2 first Elite scaling regression")
    def perform(action,**kwargs):
        nonlocal env
        reply=step_rematch(env,ctx,gyms,finale,post,rival_catalog,data,
                          action,session_id=1,**kwargs)
        env=reply["envelope"]
        return reply
    perform("start")
    master=plan_team(env,ctx,gyms,finale,post,rival_catalog,scaling,data,
        actor_name=names[0],mode="REMATCH_MASTER",
        party=[{"level":40,"egg":False}],engine_max_level=100,
        story_stage=3,synthetic_authored_team_size=3)
    if master["synthetic_target_level"]!=36 or master["synthetic_missing_slots"]!=1:
        deny("G03.2 Master scaling regression")
    for name in reversed(names):
        if perform("battle",actor_name=name,outcome="LOSS")["status"]!=LOSS:
            deny("Elite rematch loss must preserve session")
        perform("battle",actor_name=name,outcome="WIN")
    if perform("battle",actor_name="ALDER",outcome="LOSS")["status"]!=LOSS:
        deny("Alder loss must preserve session")
    perform("battle",actor_name="ALDER",outcome="WIN")
    perform("finish")
    proof=validate_envelope(env,ctx,gyms,finale,post,rival_catalog)
    ledger=_post(env)
    if len(ledger["rematches_completed"])!=1 or proof["rival_rematches"]!=0:
        deny("G02.4 rematch authority changed")
    original=rivals._g01(env)
    if codec.decode_current(codec.encode_current(original,ctx),ctx)!=original:
        deny("G01.4 projection round-trip failed")
    if env["battle_receipts"]!=checkpoints["CH12_POSTGAME"]["battle_receipts"]:
        deny("G03.3 actor story receipts must remain unchanged")
    return {"phase":"G03.4","status":"OFFLINE_ELITE_ALDER_REMATCH_NOT_NATIVE",
        "source_linked_actors":5,"stable_variants":19,
        "first_elite_scaled_level":first["synthetic_target_level"],
        "master_rematch_scaled_level":master["synthetic_target_level"],
        "completed_g02_4_rematch_sessions":len(ledger["rematches_completed"]),
        "g01_4_projection_roundtrip":True,
        "full_power_enabled":False,"real_rewards_granted":False,
        "real_teams_created":False,"game_exe_tested":False,"can_install":False}

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check",action="store_true")
    modes.add_argument("--simulate-demo",action="store_true")
    args=parser.parse_args(argv)
    try:
        ctx,gyms,finale,post,scaling,rivals_data,data=load_project()
        if args.check:
            npcs=machine._safe_source(ROOT/data["sources"]["npc"])
            trainers=machine._safe_source(ROOT/data["sources"]["trainer"])
            result=validate_catalog(data,ctx,finale,post,scaling,rivals_data,
                                    npcs,trainers)
        else:
            result=demo(ctx,gyms,finale,post,scaling,rivals_data,data)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,TypeError,KeyError,IndexError,OSError,RecursionError) as exc:
        print("UNOVA_G03_4_BLOCKED: "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
