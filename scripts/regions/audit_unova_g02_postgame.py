#!/usr/bin/env python3
"""G02.4 Unova White optional postgame — pure source-grounded simulation.

Six sages (Ghetsis already addressed), Looker, legendary encounter intentions,
optional areas and repeatable Elite Four/Alder sessions. All operations are
in-memory: no Game.exe, RXDATA, save, HM or party is read, written or edited.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
from typing import Any

import audit_unova_g01_chapter_machine as g01
import audit_unova_g01_reentry_ledger as ledger
import audit_unova_g01_serialization as codec
import audit_unova_g02_gym_story as gyms
import audit_unova_g02_elite_finale as finale

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"data/regions/unova-g02-postgame-contracts.json"
SCOPE=ledger.SCOPE
RECEIPT_SCOPE="OFFLINE_G024_NOT_NATIVE"
GATE=g01.SIMULATION_GATE
SUCCESS="APPLIED_SIMULATION"
ALREADY="ALREADY_RECORDED_NO_OP"
LOSS="BATTLE_LOST_RETRY_REQUIRED"
REENTER="REENTERED_READ_ONLY"
SAGE_DEFS=(("GORM","UNOVA_DREAMYARD","TM75_SWORDS_DANCE",()),
 ("RYOKU","UNOVA_RELIC_CASTLE","TM04_CALM_MIND",()),
 ("ZINZOLIN","UNOVA_COLD_STORAGE","TM01_HONE_CLAWS",()),
 ("BRONIUS","UNOVA_CHARGESTONE_CAVE","TM69_ROCK_POLISH",()),
 ("ROOD","UNOVA_ROUTE_18","TM32_DOUBLE_TEAM",("SURF",)),
 ("GIALLO","UNOVA_ROUTE_14","TM08_BULK_UP",("SURF","WATERFALL")))
LEGEND_DEFS=(("COBALION","UNOVA_MISTRALTON_CAVE",("SURF",),(),False),
 ("TERRAKION","UNOVA_VICTORY_ROAD",(),("COBALION",),False),
 ("VIRIZION","UNOVA_PINWHEEL_FOREST",(),("COBALION",),False),
 ("KYUREM","UNOVA_GIANT_CHASM",(),(),False),
 ("THUNDURUS","UNOVA_ROUTE_07",(),(),False),
 ("LANDORUS","UNOVA_ABUNDANT_SHRINE",("SURF",),("THUNDURUS",),True))
ACTIVITY_DEFS=(("EASTERN_UNOVA","UNOVA_ROUTE_11",()),
 ("WHITE_FOREST","UNOVA_WHITE_FOREST",()),
 ("UNDELLA_VISIT","UNOVA_UNDELLA_TOWN",()),
 ("ABYSSAL_RUINS","UNOVA_UNDELLA_BAY",("DIVE",)),
 ("BATTLE_SUBWAY","UNOVA_BATTLE_SUBWAY",()),
 ("ROYAL_UNOVA","UNOVA_ROYAL_UNOVA",()),
 ("VOLCARONA","UNOVA_RELIC_CASTLE",()))
FIELDS={"schema","region","campaign","scope","g023_envelope",
        "navigation_planned","looker_briefed","sages_found","looker_completed",
        "legendary_encounters","party_pair_planned","optional_activities",
        "rematches_completed","active_rematch"}
ACTIONS={
 "register_navigation":{"capability","simulation_gate"},
 "looker_briefing":set(),
 "find_sage":{"sage_key"},
 "looker_completion":set(),
 "legendary_encounter":{"legend_key","outcome"},
 "plan_genie_pair":{"simulation_gate"},
 "optional_activity":{"activity_key"},
 "start_rematch":{"session_id"},
 "rematch_elite":{"session_id","member_key","outcome"},
 "rematch_alder":{"session_id","outcome"},
 "finish_rematch":{"session_id"},
 "reenter":{"chapter_key"},
}

def deny(msg:str)->None:
    raise ValueError("UNOVA_G02_4_BLOCKED: "+msg)

def exact(value:Any,keys:set[str],name:str)->None:
    if not isinstance(value,dict) or set(value)!=keys:
        deny(name+" fields must exactly match contract")

def load_project(root:Path=ROOT)->tuple:
    root=Path(root)
    ctx,gym_catalog,finale_catalog=finale.load_project(root)
    data=g01._safe_source(root/"data/regions/unova-g02-postgame-contracts.json")
    areas=g01._safe_source(root/data["area_catalog"])
    validate_catalog(data,ctx,gym_catalog,finale_catalog,areas)
    return ctx,gym_catalog,finale_catalog,data

def validate_catalog(data:dict,ctx:tuple,gyms_catalog:dict,
                     finale_catalog:dict,areas:dict)->dict:
    exact(data,{"schema","phase","region","campaign","status","g01_source",
        "g02_2_source","g02_3_source","area_catalog","required_chapter",
        "required_credits_token","required_postgame_token","simulation_gate",
        "sages_collection","looker_briefing","sages","looker_completion",
        "navigation_capabilities","party_pair_gate","legendary_encounters",
        "event_only_blocked","optional_activities","league_rematch",
        "native_game_modified","native_saves_modified","game_exe_tested",
        "can_install","real_badges_granted","real_pokemon_captured",
        "real_hms_verified","real_items_granted","notes"},"postgame catalog")
    expected={
        "schema":1,"phase":"G02.4","region":"UNOVA","campaign":"WHITE_BW",
        "status":"GITHUB_ONLY_PLANNED_POSTGAME_CONTRACTS",
        "g01_source":"data/regions/unova-g01-state-contract.json",
        "g02_2_source":"data/regions/unova-g02-gym-story-contracts.json",
        "g02_3_source":"data/regions/unova-g02-elite-finale-contracts.json",
        "area_catalog":"data/regions/unova-u03-areas.json",
        "required_chapter":ctx[0]["chapters"][12]["key"],
        "required_credits_token":finale_catalog["unique_story_tokens"]["credits"],
        "required_postgame_token":finale_catalog["unique_story_tokens"]["postgame"],
        "simulation_gate":GATE,
        "sages_collection":"SIX_POSTGAME_SAGES_NOT_GHETSIS",
        "navigation_capabilities":["DIVE","SURF","WATERFALL"],
        "event_only_blocked":["VICTINI","KELDEO","MELOETTA","GENESECT"],
        "native_game_modified":False,"native_saves_modified":False,
        "game_exe_tested":False,"can_install":False,
        "real_badges_granted":False,"real_pokemon_captured":False,
        "real_hms_verified":False,"real_items_granted":False}
    for key,val in expected.items():
        if type(data.get(key)) is not type(val) or data[key]!=val:
            deny("catalog source/version/native status changed: "+key)
    if gyms_catalog.get("phase")!="G02.2" or finale_catalog.get("phase")!="G02.3":
        deny("G02.2/G02.3 foundation missing")
    valid_areas={area["key"] for area in areas.get("areas",[])}
    if len(valid_areas)!=74 or not isinstance(data["notes"],list) or len(data["notes"])<4:
        deny("planned U03 areas or safety explanations missing")
    briefing=data["looker_briefing"]
    if briefing!={"key":"UNOVA_G024_LOOKER_BRIEFING",
        "area_key":"UNOVA_NUVEMA_TOWN",
        "planned_key_item_intent":"SUPER_ROD_NOT_GRANTED",
        "requires_chapter":ctx[0]["chapters"][12]["key"],
        "native_npc_id":None,"map_id":None}:
        deny("Looker beginning is missing or falsely native")
    completion=data["looker_completion"]
    if completion!={"key":"UNOVA_G024_LOOKER_SIX_SAGES_COMPLETE",
         "required_sages":6,"any_order":True,"native_event_id":None}:
        deny("Looker conclusion must require all six sages")
    sage_rows=data["sages"]
    if not isinstance(sage_rows,list) or len(sage_rows)!=6:
        deny("exactly six postgame sages required")
    for row,(name,area,tm,abilities) in zip(sage_rows,SAGE_DEFS):
        required={"key":"UNOVA_G024_SAGE_"+name,"name":name,"area_key":area,
            "tm_intent":tm,"required_capabilities":list(abilities),
            "planned_phase":"U28","reward_granted":False,
            "native_event_id":None,"map_id":None}
        if row!=required or area not in valid_areas:deny("sage identity/location or reward drift")
    pair=data["party_pair_gate"]
    if pair!={"key":"UNOVA_G024_PLANNED_TORNADUS_THUNDURUS_PAIR",
             "required_species":["THUNDURUS","TORNADUS"],
             "version":"WHITE_BW","party_verified_in_game":False}:
        deny("Landorus simulated party gate must not claim native ownership")
    legends=data["legendary_encounters"]
    if not isinstance(legends,list) or len(legends)!=6:
        deny("six planned legendary encounter contracts required")
    for row,(name,area,abilities,prereqs,pair_required) in zip(legends,LEGEND_DEFS):
        required={"key":"UNOVA_G024_LEGEND_"+name,"species":name,
            "area_key":area,"required_capabilities":list(abilities),
            "required_encounters":["UNOVA_G024_LEGEND_"+key for key in prereqs],
            "requires_both_genies_party_simulated":pair_required,
            "version":"WHITE_BW","planned_phase":"U30",
            "native_encounter_id":None,"map_id":None,
            "ownership_verified":False,"capture_executed":False}
        if row!=required or area not in valid_areas:deny("legendary prerequisites/White version drift")
    activities=data["optional_activities"]
    if not isinstance(activities,list) or len(activities)!=7:
        deny("seven optional postgame activities required")
    for row,(name,area,abilities) in zip(activities,ACTIVITY_DEFS):
        required={"key":"UNOVA_G024_ACTIVITY_"+name,"area_key":area,
            "required_capabilities":list(abilities),
            "kind":"SPECIAL_ENCOUNTER_NOT_LEGENDARY" if name=="VOLCARONA" else "OPTIONAL_ACTIVITY",
            "planned_phase":"U29" if name in {"WHITE_FOREST","EASTERN_UNOVA","UNDELLA_VISIT"} else "U30",
            "native_event_id":None,"map_id":None,"items_granted":False}
        if row!=required or area not in valid_areas:deny("optional visit/White Forest drift")
    rematch=data["league_rematch"]
    expected_rematch={"key":"UNOVA_G024_LEAGUE_REMATCH",
        "elite_members":[member["key"] for member in finale_catalog["elite_members"]],
        "champion_key":"ALDER","elite_order":"ANY_ORDER",
        "loss_behavior":"NO_PROGRESS_AND_SYMBOLIC_RETURN_ONLY",
        "reward_policy":"NO_NATIVE_REWARDS","max_sessions":25,
        "native_trainer_id":None,"trainer_party":None,"trainer_levels":None}
    if rematch!=expected_rematch:
        deny("League rematch must require four original Elite members and Alder")
    return {"phase":"G02.4","six_sages":6,"legendary_encounters":6,
        "optional_activities":7,"rematch_max_sessions":25,
        "status":"OFFLINE_POSTGAME_CATALOG_VALIDATED","can_install":False,
        "game_exe_tested":False}

def initial(ctx:tuple)->dict:
    return {"schema":1,"region":"UNOVA","campaign":"WHITE_BW",
        "scope":SCOPE,"g023_envelope":finale.initial(ctx),
        "navigation_planned":[],"looker_briefed":False,"sages_found":[],
        "looker_completed":False,"legendary_encounters":[],
        "party_pair_planned":False,"optional_activities":[],
        "rematches_completed":[],"active_rematch":None}

def postgame_fixture(ctx:tuple,gym_catalog:dict,finale_catalog:dict)->dict:
    """Actually replay G01/G02.2/G02.3 prerequisites; never forge credits."""
    env=finale.build_league_fixture(ctx,gym_catalog)
    def use(action:str,**kwargs):
        nonlocal env
        env=finale.apply(env,ctx,gym_catalog,finale_catalog,action,**kwargs)["envelope"]
    for member in finale_catalog["elite_members"]:
        use("elite_battle",member_key=member["key"],outcome="WIN")
    use("complete_elite",simulation_gate=GATE)
    use("advance_castle")
    for event in finale_catalog["castle_events"]:
        kwargs={"event_key":event["id"]}
        if event["kind"]=="battle":
            kwargs["outcome"]="WIN"
            kwargs["opponent_key"]="N" if event["stage"]==2 else "GHETSIS"
        use("castle_event",**kwargs)
    use("complete_castle",simulation_gate=GATE)
    use("unlock_postgame")
    return {"schema":1,"region":"UNOVA","campaign":"WHITE_BW",
        "scope":SCOPE,"g023_envelope":env,"navigation_planned":[],
        "looker_briefed":False,"sages_found":[],"looker_completed":False,
        "legendary_encounters":[],"party_pair_planned":False,
        "optional_activities":[],"rematches_completed":[],"active_rematch":None}

def _index(env:dict,ctx:tuple)->int:
    return g01._chapter_index(
        env["g023_envelope"]["g02_envelope"]["g01_envelope"]["state"],ctx[0])

def _validate_rematch_record(session:dict,expected_id:int,
                             member_keys:set[str],max_sessions:int,
                             *,finished:bool)->None:
    keys={"session_id","elite_wins","alder_won"}
    if finished:keys.add("receipt_scope")
    exact(session,keys,"rematch session")
    if (type(session["session_id"]) is not int or
        session["session_id"]!=expected_id or
        not 1<=session["session_id"]<=max_sessions or
        type(session["alder_won"]) is not bool):
        deny("rematch session ID/status invalid")
    wins=session["elite_wins"]
    if (not isinstance(wins,list) or len(wins)>4 or
        any(not isinstance(k,str) or k not in member_keys for k in wins) or
        len(set(wins))!=len(wins)):
        deny("rematch Elite wins must be a unique subset")
    if session["alder_won"] and len(wins)!=4:
        deny("Alder cannot win before all four Elite members")
    if finished and (not session["alder_won"] or
                     session["receipt_scope"]!=RECEIPT_SCOPE):
        deny("completed rematch requires Alder WIN and offline receipt")

def validate_envelope(env:dict,ctx:tuple,gym_catalog:dict,
                      finale_catalog:dict,catalog:dict)->dict:
    exact(env,FIELDS,"G02.4 envelope")
    if (type(env["schema"]) is not int or env["schema"]!=1 or
        env["region"]!="UNOVA" or env["campaign"]!="WHITE_BW" or
        env["scope"]!=SCOPE):
        deny("postgame envelope region/scope/version invalid")
    finale_state=finale.validate_envelope(
        env["g023_envelope"],ctx,gym_catalog,finale_catalog)
    index=finale_state["chapter_index"]
    nav=env["navigation_planned"]
    caps=set(catalog["navigation_capabilities"])
    if (not isinstance(nav,list) or any(not isinstance(x,str) or x not in caps for x in nav)
        or nav!=sorted(set(nav))):
        deny("synthetic navigation must be sorted, unique and allowlisted")
    if type(env["looker_briefed"]) is not bool or type(env["looker_completed"]) is not bool or (
        type(env["party_pair_planned"]) is not bool):
        deny("postgame boolean status invalid")
    sages=env["sages_found"]
    if not isinstance(sages,list) or len(sages)>6:
        deny("sages receipts malformed")
    known_sages={s["key"]:s for s in catalog["sages"]}
    sage_seen=set()
    for r in sages:
        exact(r,{"sage_key","area_key","tm_intent","receipt_scope"},"sage receipt")
        key=r["sage_key"]
        if not isinstance(key,str) or key not in known_sages or key in sage_seen:
            deny("unknown or repeated sage")
        sage_seen.add(key)
        source=known_sages[key]
        if r!={"sage_key":key,"area_key":source["area_key"],
                "tm_intent":source["tm_intent"],"receipt_scope":RECEIPT_SCOPE}:
            deny("sage receipt or TM intent differs from catalog")
        if not set(source["required_capabilities"]).issubset(nav):
            deny("sage navigation prerequisites missing")
    if sages and not env["looker_briefed"]:
        deny("Looker must initiate quest before sages")
    if env["looker_completed"] and (
        not env["looker_briefed"] or len(sages)!=6):
        deny("Looker cannot finish before six unique sages")
    legends=env["legendary_encounters"]
    if not isinstance(legends,list) or len(legends)>6:
        deny("legendary encounter receipts malformed")
    known_legends={l["key"]:l for l in catalog["legendary_encounters"]}
    seen=set()
    for r in legends:
        exact(r,{"legend_key","area_key","receipt_scope"},"legendary receipt")
        key=r["legend_key"]
        if not isinstance(key,str) or key not in known_legends or key in seen:
            deny("unknown, event-only or repeated legendary")
        source=known_legends[key]
        if r!={"legend_key":key,"area_key":source["area_key"],"receipt_scope":RECEIPT_SCOPE}:
            deny("legendary receipt mismatch")
        if (not set(source["required_capabilities"]).issubset(nav) or
            not set(source["required_encounters"]).issubset(seen) or
            (source["requires_both_genies_party_simulated"] and
             not env["party_pair_planned"])):
            deny("legendary prerequisite or encounter order missing")
        seen.add(key)
    if env["party_pair_planned"] and "UNOVA_G024_LEGEND_THUNDURUS" not in seen:
        deny("simulated pair requires White's Thundurus storyline")
    activities=env["optional_activities"]
    if not isinstance(activities,list) or len(activities)>7:
        deny("optional activity receipts malformed")
    available={a["key"]:a for a in catalog["optional_activities"]}
    act_seen=set()
    for r in activities:
        exact(r,{"activity_key","area_key","receipt_scope"},"activity receipt")
        key=r["activity_key"]
        if not isinstance(key,str) or key not in available or key in act_seen:
            deny("unknown or repeated activity")
        item=available[key]
        if r!={"activity_key":key,"area_key":item["area_key"],"receipt_scope":RECEIPT_SCOPE} or (
            not set(item["required_capabilities"]).issubset(nav)):
            deny("activity location or navigation requirement missing")
        act_seen.add(key)
    sessions=env["rematches_completed"]
    if not isinstance(sessions,list) or len(sessions)>catalog["league_rematch"]["max_sessions"]:
        deny("bounded rematch history required")
    members=set(catalog["league_rematch"]["elite_members"])
    for n,rec in enumerate(sessions,1):
        _validate_rematch_record(rec,n,members,
                                 catalog["league_rematch"]["max_sessions"],finished=True)
    active=env["active_rematch"]
    if active is not None:
        _validate_rematch_record(active,len(sessions)+1,members,
                                 catalog["league_rematch"]["max_sessions"],finished=False)
    if index!=12 and (nav or env["looker_briefed"] or sages or env["looker_completed"] or
            legends or env["party_pair_planned"] or activities or sessions or active is not None):
        deny("postgame actions require credits and current CH12")
    if index==12:
        tokens=env["g023_envelope"]["unique_story_tokens"]
        if catalog["required_credits_token"] not in tokens or (
            catalog["required_postgame_token"] not in tokens):
            deny("postgame requires original CH11 credits from G02.3")
    return {"phase":"G02.4","chapter_index":index,"sages_found":len(sages),
        "looker_completed":env["looker_completed"],
        "legendary_encounter_intents":len(legends),
        "optional_activities":len(activities),
        "rematch_sessions_completed":len(sessions),
        "native_items_granted":False,"legendary_captured":False,
        "game_exe_tested":False,"can_install":False}

def result(env:dict,status:str,*,safe_area:str|None=None)->dict:
    return {"status":status,"envelope":copy.deepcopy(env),
        "suggested_safe_return_area_key":safe_area,
        "native_teleport_executed":False,"native_saves_modified":False,
        "real_hms_verified":False,"real_pokemon_captured":False,
        "real_items_granted":False,"real_battles_executed":False,
        "game_exe_tested":False,"can_install":False}

def apply(env:dict,ctx:tuple,gym_catalog:dict,finale_catalog:dict,
          catalog:dict,action:str, *,
          capability:str|None=None,sage_key:str|None=None,
          legend_key:str|None=None,activity_key:str|None=None,
          session_id:int|None=None,member_key:str|None=None,
          outcome:str|None=None,chapter_key:str|None=None,
          simulation_gate:str|None=None)->dict:
    """Pure copy-on-write. Validation before and after every transition."""
    validate_envelope(env,ctx,gym_catalog,finale_catalog,catalog)
    if action not in ACTIONS:deny("unknown postgame operation or blocked event-only distribution")
    supplied={key for key,value in {
        "capability":capability,"sage_key":sage_key,"legend_key":legend_key,
        "activity_key":activity_key,"session_id":session_id,
        "member_key":member_key,"outcome":outcome,
        "chapter_key":chapter_key,"simulation_gate":simulation_gate}.items()
        if value is not None}
    if supplied!=ACTIONS[action]:
        deny("action requires exactly its documented arguments")
    index=_index(env,ctx)
    if action=="reenter":
        if chapter_key not in [ctx[0]["chapters"][i]["key"] for i in range(1,index+1)]:
            deny("cannot reenter future or unknown chapter")
        returned=finale.apply(env["g023_envelope"],ctx,gym_catalog,
                              finale_catalog,"reenter",chapter_key=chapter_key)
        if returned["status"]!=finale.RESULT_REENTER:
            deny("unsafe fallback for G02.3 reentry")
        return result(env,REENTER)
    if index!=12:
        deny("must finish G02.3 White credits before postgame")
    changed=copy.deepcopy(env)
    capset=set(env["navigation_planned"])
    if action=="register_navigation":
        if simulation_gate!=GATE or capability not in catalog["navigation_capabilities"]:
            deny("navigation is a planned capability, never a native HM proof")
        if capability in capset:return result(env,ALREADY)
        changed["navigation_planned"]=sorted(capset|{capability})
    elif action=="looker_briefing":
        if env["looker_briefed"]:return result(env,ALREADY)
        changed["looker_briefed"]=True
    elif action=="find_sage":
        src=next((s for s in catalog["sages"] if s["key"]==sage_key),None)
        if src is None:deny("unknown sage or Ghetsis is not one of six postgame sages")
        if not env["looker_briefed"]:deny("Looker quest not started")
        if any(r["sage_key"]==sage_key for r in env["sages_found"]):
            return result(env,ALREADY)
        if not set(src["required_capabilities"]).issubset(capset):
            deny("missing synthetic navigation prerequisites for sage")
        changed["sages_found"].append({
            "sage_key":sage_key,"area_key":src["area_key"],
            "tm_intent":src["tm_intent"],"receipt_scope":RECEIPT_SCOPE})
    elif action=="looker_completion":
        if env["looker_completed"]:return result(env,ALREADY)
        if not env["looker_briefed"] or len(env["sages_found"])!=6:
            deny("all six distinct sages must be recorded")
        changed["looker_completed"]=True
    elif action=="legendary_encounter":
        src=next((x for x in catalog["legendary_encounters"] if x["key"]==legend_key),None)
        if src is None or outcome!="ENCOUNTERED":
            deny("no capture, win, loss or mythical external event is authorized")
        if any(r["legend_key"]==legend_key for r in env["legendary_encounters"]):
            return result(env,ALREADY)
        if (not set(src["required_capabilities"]).issubset(capset) or
            not set(src["required_encounters"]).issubset({
                r["legend_key"] for r in env["legendary_encounters"]}) or
            (src["requires_both_genies_party_simulated"] and not env["party_pair_planned"])):
            deny("planned encounter prerequisites not met")
        changed["legendary_encounters"].append({
            "legend_key":legend_key,"area_key":src["area_key"],
            "receipt_scope":RECEIPT_SCOPE})
    elif action=="plan_genie_pair":
        if simulation_gate!=GATE:deny("never infer real party ownership")
        if env["party_pair_planned"]:return result(env,ALREADY)
        if not any(r["legend_key"]=="UNOVA_G024_LEGEND_THUNDURUS"
                   for r in env["legendary_encounters"]):
            deny("White's Thundurus storyline must be registered first")
        changed["party_pair_planned"]=True
    elif action=="optional_activity":
        src=next((x for x in catalog["optional_activities"] if x["key"]==activity_key),None)
        if src is None:deny("unknown optional activity")
        if any(r["activity_key"]==activity_key for r in env["optional_activities"]):
            return result(env,ALREADY)
        if not set(src["required_capabilities"]).issubset(capset):
            deny("missing planned navigation for optional area")
        changed["optional_activities"].append({
            "activity_key":activity_key,"area_key":src["area_key"],
            "receipt_scope":RECEIPT_SCOPE})
    else:
        if type(session_id) is not int or not 1<=session_id<=catalog["league_rematch"]["max_sessions"]:
            deny("rematch session needs a bounded positive integer")
        finished=len(env["rematches_completed"])
        active=env["active_rematch"]
        if action=="start_rematch":
            if session_id<=finished:return result(env,ALREADY)
            if active is not None:
                if active["session_id"]==session_id:return result(env,ALREADY)
                deny("cannot start a second concurrent league session")
            if session_id!=finished+1:deny("cannot skip session IDs")
            changed["active_rematch"]={"session_id":session_id,"elite_wins":[],"alder_won":False}
        else:
            if session_id<=finished:
                if (action in {"finish_rematch","rematch_elite","rematch_alder"} and
                    (action=="finish_rematch" or outcome=="WIN")):
                    return result(env,ALREADY)
                deny("cannot change a completed rematch result")
            if active is None or active["session_id"]!=session_id:
                deny("rematch session not active")
            if action=="rematch_elite":
                if member_key not in catalog["league_rematch"]["elite_members"] or outcome not in {"WIN","LOSS"}:
                    deny("unknown Elite member or battle outcome")
                if member_key in active["elite_wins"]:
                    if outcome=="WIN":return result(env,ALREADY)
                    deny("completed Elite win cannot be reversed")
                if active["alder_won"]:deny("Elite rematch cannot occur after Alder")
                if outcome=="LOSS":
                    return result(env,LOSS,safe_area="UNOVA_POKEMON_LEAGUE")
                changed["active_rematch"]["elite_wins"].append(member_key)
            elif action=="rematch_alder":
                if outcome not in {"WIN","LOSS"}:deny("Alder battle needs WIN/LOSS")
                if active["alder_won"]:
                    if outcome=="WIN":return result(env,ALREADY)
                    deny("Alder WIN cannot be reversed")
                if len(active["elite_wins"])!=4:deny("Alder requires four Elite wins")
                if outcome=="LOSS":
                    return result(env,LOSS,safe_area="UNOVA_POKEMON_LEAGUE")
                changed["active_rematch"]["alder_won"]=True
            elif action=="finish_rematch":
                if not active["alder_won"] or len(active["elite_wins"])!=4:
                    deny("only complete Elite and Alder sessions may be archived")
                changed["rematches_completed"].append({
                    "session_id":session_id,"elite_wins":copy.deepcopy(active["elite_wins"]),
                    "alder_won":True,"receipt_scope":RECEIPT_SCOPE})
                changed["active_rematch"]=None
            else:
                deny("unsupported rematch operation")
    validate_envelope(changed,ctx,gym_catalog,finale_catalog,catalog)
    return result(changed,SUCCESS)

def demo(ctx:tuple,gym_catalog:dict,finale_catalog:dict,catalog:dict)->dict:
    env=postgame_fixture(ctx,gym_catalog,finale_catalog)
    def call(name:str,**kwargs):
        nonlocal env
        response=apply(env,ctx,gym_catalog,finale_catalog,catalog,name,**kwargs)
        env=response["envelope"]
        return response
    call("register_navigation",capability="SURF",simulation_gate=GATE)
    call("register_navigation",capability="WATERFALL",simulation_gate=GATE)
    call("register_navigation",capability="DIVE",simulation_gate=GATE)
    call("looker_briefing")
    for sage in reversed(catalog["sages"]):
        call("find_sage",sage_key=sage["key"])
    call("looker_completion")
    for item in catalog["legendary_encounters"]:
        if item["species"]=="LANDORUS":
            call("plan_genie_pair",simulation_gate=GATE)
        call("legendary_encounter",legend_key=item["key"],outcome="ENCOUNTERED")
    for item in catalog["optional_activities"]:
        call("optional_activity",activity_key=item["key"])
    call("start_rematch",session_id=1)
    for member in reversed(catalog["league_rematch"]["elite_members"]):
        call("rematch_elite",session_id=1,member_key=member,outcome="WIN")
    if call("rematch_alder",session_id=1,outcome="LOSS")["status"]!=LOSS:
        deny("losing to Alder must not advance")
    call("rematch_alder",session_id=1,outcome="WIN")
    call("finish_rematch",session_id=1)
    integrity=validate_envelope(env,ctx,gym_catalog,finale_catalog,catalog)
    projection=env["g023_envelope"]["g02_envelope"]["g01_envelope"]
    if codec.decode_current(codec.encode_current(projection,ctx),ctx)!=projection:
        deny("G01.4 projection failed")
    return {"phase":"G02.4","status":"OFFLINE_POSTGAME_DEMO_NOT_NATIVE",
        "sages_found":integrity["sages_found"],"looker_complete":integrity["looker_completed"],
        "legendary_encounter_intents":integrity["legendary_encounter_intents"],
        "optional_activities":integrity["optional_activities"],
        "league_rematches_completed":integrity["rematch_sessions_completed"],
        "g01_4_projection_roundtrip":True,"native_saves_modified":False,
        "real_pokemon_captured":False,"real_items_granted":False,
        "game_exe_tested":False,"can_install":False}

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    choice=parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--check",action="store_true")
    choice.add_argument("--simulate-demo",action="store_true")
    args=parser.parse_args(argv)
    try:
        ctx,gym_catalog,finale_catalog,catalog=load_project()
        report=(validate_catalog(catalog,ctx,gym_catalog,finale_catalog,
                g01._safe_source(ROOT/catalog["area_catalog"])) if args.check else
                demo(ctx,gym_catalog,finale_catalog,catalog))
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,TypeError,KeyError,IndexError,OSError,RecursionError) as exc:
        print("UNOVA_G02_4_BLOCKED: "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
