#!/usr/bin/env python3
"""Unova G03.3: rival/Plasma/chapter boss story contracts, OFFLINE ONLY.

G01.3 U07 and G02.3 N/Ghetsis receipts stay authoritative: read-only links,
no duplicate wins. The nine later rival/Plasma battles are explicit design
fixtures, not evidence of native sprites, teams, PBS or events. G03.3 wraps
existing G02 transitions for optional fail-closed story-gate checks.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import audit_unova_g01_chapter_machine as machine
import audit_unova_g01_reentry_ledger as ledger
import audit_unova_g01_serialization as codec
import audit_unova_g02_gym_story as gyms
import audit_unova_g02_elite_finale as finale
import audit_unova_g02_postgame as postgame
import audit_unova_g03_leader_scaling as balance

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"data/regions/unova-g03-rivals-plasma-story-contracts.json"
SCOPE=ledger.SCOPE
RECEIPT_SCOPE="OFFLINE_G033_DESIGN_BATTLE_NOT_A_NATIVE_EVENT"
REWARD_SCOPE="STORY_MILESTONE_INTENT_NOT_INVENTORY"
LOSS="BATTLE_LOST_RETRY_REQUIRED"
APPLIED="APPLIED_SIMULATION"
REPLAY="ALREADY_RECORDED_NO_OP"
REENTER="REENTERED_READ_ONLY"
SOURCES={
 "g01_state":"data/regions/unova-g01-state-contract.json",
 "g01_u07":"data/regions/unova-u07-nuvema-events.json",
 "g01_reentry":"data/regions/unova-g01-reentry-policy.json",
 "g01_serialization":"data/regions/unova-g01-serialization-contract.json",
 "g02_gyms":"data/regions/unova-g02-gym-story-contracts.json",
 "g02_finale":"data/regions/unova-g02-elite-finale-contracts.json",
 "g02_postgame":"data/regions/unova-g02-postgame-contracts.json",
 "g03_scaling":"data/regions/unova-g03-leader-scaling-contracts.json",
 "npc_catalog":"data/regions/unova-sp04-npcs.json",
 "trainer_references":"data/regions/unova-e06-e07-preparation.json",
 "areas":"data/regions/unova-u03-areas.json"}
ACTOR_REFS={
 "BIANCA":("UNOVA_NPC_BIANCA","UNOVA_TRAINER_BIANCA"),
 "CHEREN":("UNOVA_NPC_CHEREN","UNOVA_TRAINER_CHEREN"),
 "N":("UNOVA_NPC_N","UNOVA_TRAINER_N"),
 "GHETSIS":("UNOVA_NPC_GHETSIS","UNOVA_TRAINER_GHETSIS"),
 "PLASMA_GRUNT":("UNOVA_NPC_PLASMA_GRUNT_MALE",None)}
# Indexed entries derive *only* from earlier reference catalogs and design
# slots. Planned story slots are not claims of native Pokémon White battle data.
# actor, chapter, area, source kind, linked key, prerequisite encounter IDs, battle policy.
EVENT_DEFS=(
 ("BIANCA",1,"NUVEMA_TOWN","LINKED_G013","UNOVA_U07_BIANCA_FIRST_BATTLE",(),"ADVANCE_ON_LOSS"),
 ("CHEREN",1,"NUVEMA_TOWN","LINKED_G013","UNOVA_U07_CHEREN_FIRST_BATTLE",(),"ADVANCE_ON_LOSS"),
 ("GHETSIS",1,"ACCUMULA_TOWN","LINKED_G013","UNOVA_U07_PLASMA_SPEECH",(),"NO_BATTLE"),
 ("N",1,"ACCUMULA_TOWN","LINKED_G013","UNOVA_U07_N_FIRST_BATTLE",(),"WIN_REQUIRED"),
 ("CHEREN",2,"ROUTE_03","PLANNED",None,("UNOVA_G033_CH01_CHEREN",),"WIN_REQUIRED"),
 ("PLASMA_GRUNT",3,"PINWHEEL_FOREST","PLANNED",None,(),"WIN_REQUIRED"),
 ("PLASMA_GRUNT",4,"CASTELIA_CITY","PLANNED",None,("UNOVA_G033_CH03_PLASMA_GRUNT",),"WIN_REQUIRED"),
 ("BIANCA",5,"NIMBASA_CITY","PLANNED",None,("UNOVA_G033_CH01_BIANCA",),"WIN_REQUIRED"),
 ("CHEREN",5,"ROUTE_05","PLANNED",None,("UNOVA_G033_CH02_CHEREN",),"WIN_REQUIRED"),
 ("PLASMA_GRUNT",6,"COLD_STORAGE","PLANNED",None,("UNOVA_G033_CH04_PLASMA_GRUNT",),"WIN_REQUIRED"),
 ("N",7,"CHARGESTONE_CAVE","PLANNED",None,("UNOVA_G033_CH01_N",),"WIN_REQUIRED"),
 ("PLASMA_GRUNT",8,"DRAGONSPIRAL_TOWER","PLANNED",None,("UNOVA_G033_CH06_PLASMA_GRUNT",),"WIN_REQUIRED"),
 ("CHEREN",9,"ROUTE_10","PLANNED",None,("UNOVA_G033_CH05_CHEREN",),"WIN_REQUIRED"),
 ("N",11,"NS_CASTLE","LINKED_G023","UNOVA_G023_N_BATTLE",("UNOVA_G033_CH07_N",),"WIN_REQUIRED"),
 ("GHETSIS",11,"NS_CASTLE","LINKED_G023","UNOVA_G023_GHETSIS_BATTLE",("UNOVA_G033_CH11_N",),"WIN_REQUIRED"))
ENVELOPE_KEYS={"schema","region","campaign","scope","g024_envelope",
               "battle_receipts","reward_intents","rematch_receipts"}
CHAPTER_GATE_ACTIONS={"complete_gym","advance_gym"}

def deny(why:str)->None:
    raise ValueError("UNOVA_G03_3_BLOCKED: "+why)

def exact(value:Any,keys:set[str],label:str)->None:
    if not isinstance(value,dict) or set(value)!=keys:
        deny(label+" unexpected or missing fields")

def load_project(root:Path=ROOT)->tuple:
    root=Path(root)
    ctx,gym_catalog,finale_catalog,postgame_catalog=postgame.load_project(root)
    balance_policy,_,_,_=balance.load_project(root)
    data=machine._safe_source(root/"data/regions/unova-g03-rivals-plasma-story-contracts.json")
    npcs=machine._safe_source(root/data["sources"]["npc_catalog"])
    trainer_sources=machine._safe_source(root/data["sources"]["trainer_references"])
    areas=machine._safe_source(root/data["sources"]["areas"])
    u07=machine._safe_source(root/data["sources"]["g01_u07"])
    validate_catalog(data,ctx,gym_catalog,finale_catalog,postgame_catalog,
                     balance_policy,npcs,trainer_sources,areas,u07)
    return ctx,gym_catalog,finale_catalog,postgame_catalog,balance_policy,data

def validate_catalog(data:dict,ctx:tuple,gym_catalog:dict,finale_catalog:dict,
                     postgame_catalog:dict,balance_policy:dict,npcs:dict,
                     trainer_sources:dict,areas:dict,u07:dict)->dict:
    exact(data,{"schema","phase","region","campaign","status","sources",
                "simulation_scope","canonical_linked_receipts",
                "planned_battle_outcome_required","planned_on_loss",
                "chapter_completion_guard","reward_category","reward_amount",
                "max_rematch_sessions_per_rival","rematch","team_scaling",
                "encounters","native_game_modified","native_saves_modified",
                "trainer_pbs_compiled","real_team_data_verified","game_exe_tested",
                "android_tested","can_install","notes"},"G03.3 contract")
    expected={"schema":1,"phase":"G03.3","region":"UNOVA","campaign":"WHITE_BW",
      "status":"OFFLINE_RIVALS_PLASMA_CHAPTER_EVENTS_ONLY","sources":SOURCES,
      "simulation_scope":SCOPE,
      "canonical_linked_receipts":"READ_ONLY_G01_G02_NO_DUPLICATION",
      "planned_battle_outcome_required":"WIN",
      "planned_on_loss":"NO_PROGRESS_RETRY_NO_REWARD",
      "chapter_completion_guard":"OFFLINE_G033_CH02_CH09_ONLY",
      "reward_category":REWARD_SCOPE,"reward_amount":1,
      "max_rematch_sessions_per_rival":8,
      "native_game_modified":False,"native_saves_modified":False,
      "trainer_pbs_compiled":False,"real_team_data_verified":False,
      "game_exe_tested":False,"android_tested":False,"can_install":False,
      "rematch":{"actors":["BIANCA","CHEREN"],
        "chapter_key":ctx[0]["chapters"][12]["key"],
        "requires_original_planned_victory":True,
        "source_roster_verified":False,"real_revanche_installed":False,
        "never_award_second_reward":True},
      "team_scaling":{"percent_reference":"G03.2",
        "max_engine_level_parameter_required":True,
        "normal_percent":70,"master_percent":90,"master_stage":3,
        "master_team_target":4,"unknown_native_team_size_remains_null":True,
        "no_actual_team_created":True,"no_numeric_regional_cap":True,
        "evolution_by_native_species_only_when_verified":True}}
    for key,expected_value in expected.items():
        if type(data.get(key)) is not type(expected_value) or data[key]!=expected_value:
            deny("source policy drift or fabricated native status: "+key)
    if (gym_catalog.get("phase")!="G02.2" or finale_catalog.get("phase")!="G02.3" or
        postgame_catalog.get("phase")!="G02.4" or
        balance_policy.get("phase")!="G03.2" or
        balance_policy["level_cap"]["normal_percent"]!=70 or
        balance_policy["level_cap"]["master_percent"]!=90 or
        balance_policy["first_challenge"]["full_power_rematches_enabled"] is not False):
        deny("G01–G03 dependencies drift")
    if not isinstance(data["notes"],list) or len(data["notes"])<5:
        deny("catalog boundaries not explained")
    entries=data["encounters"]
    if not isinstance(entries,list) or len(entries)!=len(EVENT_DEFS):
        deny("story encounters must match stable sourced 15-slot design")
    all_areas={x["key"] for x in areas.get("areas",[])}
    all_npcs={x["key"]:x for x in npcs.get("characters",[])}
    all_trainers={x["key"]:x for x in trainer_sources.get("trainer_references",[])}
    u07_events={x["key"]:x for x in u07.get("events",[])}
    castle_events={x["id"]:x for x in finale_catalog["castle_events"]}
    seen=set();versions={}
    for item,(actor,index,area,sourcemode,sourceid,required,battle_policy) in zip(entries,EVENT_DEFS):
        exact(item,{"id","chapter_key","chapter_index","mission_key","actor_key",
             "npc_reference_key","trainer_reference_key","reference_area_key",
             "source_mode","source_event_key","battle_policy",
             "required_prior_events","team_variant_key","team_reference_status",
             "canonical_team","canonical_levels","canonical_moves",
             "trainer_pbs_id","native_event_id","native_map_id","planned_only",
             "reward_intent_token"},"chapter encounter")
        variants=versions.get(actor,0)+1;versions[actor]=variants
        eid=f"UNOVA_G033_CH{index:02d}_{actor}"
        npc,trainer=ACTOR_REFS[actor]
        wanted={"id":eid,"chapter_key":ctx[0]["chapters"][index]["key"],
          "chapter_index":index,"mission_key":ctx[0]["missions"][index-1]["key"],
          "actor_key":actor,"npc_reference_key":npc,
          "trainer_reference_key":trainer,"reference_area_key":"UNOVA_"+area,
          "source_mode":sourcemode,"source_event_key":sourceid,
          "battle_policy":battle_policy,"required_prior_events":list(required),
          "team_variant_key":f"UNOVA_G033_TEAM_{actor}_{variants:02d}",
          "team_reference_status":"SYMBOLIC_NO_PBS_SOURCE",
          "canonical_team":None,"canonical_levels":None,"canonical_moves":None,
          "trainer_pbs_id":None,"native_event_id":None,"native_map_id":None,
          "planned_only":sourcemode=="PLANNED",
          "reward_intent_token":f"UNOVA_G033_STORY_INTENT_{eid[11:]}" if sourcemode=="PLANNED" else None}
        if item!=wanted:
            deny("chapter variant, reward or native reference does not match sources")
        if eid in seen or any(x not in seen for x in required):
            deny("duplicate story event or forward prerequisite")
        seen.add(eid)
        if wanted["reference_area_key"] not in all_areas or npc not in all_npcs:
            deny("missing area or NPC reference")
        if trainer is not None:
            ref=all_trainers.get(trainer)
            if (ref is None or ref["verified"] is not False or ref["installed"] is not False or
                ref["team"]!=[] or ref["pbs_trainer_id"] is not None):
                deny("trainer source missing or erroneously installed")
        if all_npcs[npc]["trainer_reference_key"]!=trainer:
            deny("NPC reference identity drift")
        if sourcemode=="LINKED_G013":
            linked=u07_events.get(sourceid)
            if linked is None or (
                linked["battle_policy"]!=None if battle_policy=="NO_BATTLE" else
                linked["battle_policy"]!=battle_policy):
                deny("G01.3 linked U07 policy mismatch")
        if sourcemode=="LINKED_G023" and (
            sourceid not in castle_events or
            castle_events[sourceid]["outcome_required"]!="WIN"):
            deny("G02.3 linked finale battle mismatch")
    return {"phase":"G03.3","actors":len(ACTOR_REFS),"chapter_encounters":15,
        "authoritative_readonly_links":6,"planned_battles":9,
        "game_exe_tested":False,"can_install":False}

def initial(ctx:tuple)->dict:
    return {"schema":1,"region":"UNOVA","campaign":"WHITE_BW","scope":SCOPE,
        "g024_envelope":postgame.initial(ctx),"battle_receipts":[],
        "reward_intents":[],"rematch_receipts":[]}

def _g01(env:dict)->dict:
    return env["g024_envelope"]["g023_envelope"]["g02_envelope"]["g01_envelope"]

def _state_index(env:dict,ctx:tuple)->int:
    return machine._chapter_index(_g01(env)["state"],ctx[0])

def _linked(record:dict,env:dict)->bool:
    if record["source_mode"]=="LINKED_G013":
        return record["source_event_key"] in {
            r["event_key"] for r in _g01(env)["event_receipts"]}
    if record["source_mode"]=="LINKED_G023":
        return record["source_event_key"] in {
            r["event_key"] for r in env["g024_envelope"]["g023_envelope"]["castle_receipts"]}
    return False

def _known(data:dict,key:str)->dict:
    if not isinstance(key,str):deny("encounter key must be a string")
    for record in data["encounters"]:
        if record["id"]==key:return record
    deny("unknown story encounter ID")

def _expected_receipt(entry:dict)->dict:
    return {"event_key":entry["id"],"outcome":"WIN",
            "team_variant_key":entry["team_variant_key"],
            "reward_intent_token":entry["reward_intent_token"],
            "receipt_scope":RECEIPT_SCOPE}

def validate_envelope(env:dict,ctx:tuple,gyms_data:dict,finale_data:dict,
                      postgame_data:dict,data:dict)->dict:
    exact(env,ENVELOPE_KEYS,"G03.3 envelope")
    if (type(env["schema"]) is not int or env["schema"]!=1 or
        env["region"]!="UNOVA" or env["campaign"]!="WHITE_BW" or
        env["scope"]!=SCOPE):
        deny("unknown state version or region")
    postgame.validate_envelope(env["g024_envelope"],ctx,gyms_data,finale_data,postgame_data)
    chapter=_state_index(env,ctx)
    receipts=env["battle_receipts"]
    if not isinstance(receipts,list) or len(receipts)>9:
        deny("planned story receipts malformed")
    entries=[x for x in data["encounters"] if x["source_mode"]=="PLANNED"]
    order={x["id"]:i for i,x in enumerate(entries)}
    checked=set();prior=-1
    for rec in receipts:
        exact(rec,{"event_key","outcome","team_variant_key",
                   "reward_intent_token","receipt_scope"},"planned battle receipt")
        key=rec["event_key"]
        if not isinstance(key,str) or key not in order or key in checked:
            deny("unknown or duplicate planned battle receipt")
        entry=entries[order[key]]
        if rec!=_expected_receipt(entry):
            deny("forged battle outcome, team variant or reward token")
        if order[key]<=prior or entry["chapter_index"]>chapter:
            deny("planned battle receipts must follow chapter sequence")
        for dep in entry["required_prior_events"]:
            parent=_known(data,dep)
            if dep not in checked and not _linked(parent,env):
                deny("missing actor history prerequisite")
        checked.add(key);prior=order[key]
    intents=env["reward_intents"]
    if not isinstance(intents,list) or intents!=[{
            "category":REWARD_SCOPE,"token":rec["reward_intent_token"],"amount":1,
            "source_event":rec["event_key"]} for rec in receipts]:
        deny("reward intents must derive exactly once from story wins")
    rematches=env["rematch_receipts"]
    if not isinstance(rematches,list) or len(rematches)>16:
        deny("bounded rematch records required")
    counts={actor:0 for actor in data["rematch"]["actors"]}
    first_win={r["event_key"] for r in receipts}
    for rec in rematches:
        exact(rec,{"actor_key","session_id","outcome","receipt_scope"},"rival rematch receipt")
        actor=rec["actor_key"]
        if not isinstance(actor,str) or actor not in counts or (
            type(rec["session_id"]) is not int or
            rec["session_id"]!=counts[actor]+1 or
            rec["session_id"]>data["max_rematch_sessions_per_rival"] or
            rec["outcome"]!="WIN" or rec["receipt_scope"]!=RECEIPT_SCOPE):
            deny("rematch id, actor or WIN receipt forged")
        counts[actor]+=1
        if not any(row["actor_key"]==actor and row["id"] in first_win
                   for row in entries):
            deny("cannot have rematch before original planned victory")
    if chapter!=12 and rematches:
        deny("rival rematches only available after G02.3 credits")
    return {"phase":"G03.3","chapter_index":chapter,
        "planned_battle_wins":len(receipts),
        "unique_story_reward_intents":len(intents),
        "rival_rematches":len(rematches),
        "native_battles_executed":False,"native_rewards_granted":False,
        "game_exe_tested":False,"can_install":False}

def result(env:dict,status:str,*,source_verified:bool|None=None)->dict:
    return {"status":status,"envelope":copy.deepcopy(env),
        "authoritative_source_recorded":source_verified,
        "native_battles_executed":False,"native_rewards_granted":False,
        "native_saves_modified":False,"real_trainer_pbs_verified":False,
        "game_exe_tested":False,"can_install":False}

def apply(env:dict,ctx:tuple,gyms_data:dict,finale_data:dict,
          postgame_data:dict,data:dict,action:str, *,
          encounter_key:str|None=None,outcome:str|None=None,
          actor_key:str|None=None,session_id:int|None=None,
          chapter_key:str|None=None,simulation_gate:str|None=None)->dict:
    """Copy-on-write bridge. No native files and no duplicate U07/finale receipts."""
    validate_envelope(env,ctx,gyms_data,finale_data,postgame_data,data)
    allowed={"record_battle":{"encounter_key","outcome"},
             "inspect_linked":{"encounter_key"},
             "complete_gym":{"simulation_gate"},
             "advance_gym":set(),
             "rematch":{"actor_key","session_id","outcome"},
             "reenter":{"chapter_key"}}
    if action not in allowed:deny("unknown or native-only story operation")
    supplied={k for k,v in {"encounter_key":encounter_key,"outcome":outcome,
        "actor_key":actor_key,"session_id":session_id,"chapter_key":chapter_key,
        "simulation_gate":simulation_gate}.items() if v is not None}
    if supplied!=allowed[action]:
        deny("action requires exactly documented arguments")
    current=_state_index(env,ctx)
    if action=="inspect_linked":
        e=_known(data,encounter_key)
        if e["source_mode"]=="PLANNED":
            deny("planned battle cannot claim a canonical U07 or G02.3 receipt")
        return result(env,"SOURCE_RECORDED_OFFLINE" if _linked(e,env)
                      else "SOURCE_NOT_YET_RECORDED",source_verified=_linked(e,env))
    if action=="reenter":
        response=postgame.apply(env["g024_envelope"],ctx,gyms_data,
            finale_data,postgame_data,"reenter",chapter_key=chapter_key)
        if response["status"]!=postgame.REENTER:deny("G02 reentry not read-only")
        return result(env,REENTER)
    if action=="record_battle":
        entry=_known(data,encounter_key)
        if entry["source_mode"]!="PLANNED":
            deny("linked G01.3/G02.3 battles must never be re-recorded")
        if outcome not in {"WIN","LOSS"}:deny("planned battle needs explicit WIN or LOSS")
        old=next((r for r in env["battle_receipts"] if r["event_key"]==encounter_key),None)
        if old:
            if outcome=="WIN":return result(env,REPLAY)
            deny("cannot overwrite a recorded story win with a loss")
        if current!=entry["chapter_index"]:
            deny("planned battle must occur in its active chapter")
        if _g01(env)["state"]["missions"][entry["mission_key"]]!="active":
            deny("planned battle requires active G01 chapter mission")
        checked={r["event_key"] for r in env["battle_receipts"]}
        for dep in entry["required_prior_events"]:
            parent=_known(data,dep)
            if dep not in checked and not _linked(parent,env):
                deny("actor storyline prerequisite is missing")
        if outcome=="LOSS":
            return result(env,LOSS)
        changed=copy.deepcopy(env)
        changed["battle_receipts"].append(_expected_receipt(entry))
        changed["reward_intents"].append({
            "category":REWARD_SCOPE,"token":entry["reward_intent_token"],
            "amount":1,"source_event":entry["id"]})
        validate_envelope(changed,ctx,gyms_data,finale_data,postgame_data,data)
        return result(changed,APPLIED)
    if action in CHAPTER_GATE_ACTIONS:
        if not 2<=current<=9:deny("G03.3 chapter guards only apply to CH02..CH09")
        if action=="complete_gym":
            if simulation_gate!=machine.SIMULATION_GATE:
                deny("offline chapter completion requires synthetic-only gate")
            required={e["id"] for e in data["encounters"]
                      if e["source_mode"]=="PLANNED" and e["chapter_index"]==current}
            if not required.issubset({r["event_key"] for r in env["battle_receipts"]}):
                deny("cannot finish chapter before its planned rival/Plasma encounters")
        forwarded=gyms.apply(env["g024_envelope"]["g023_envelope"]["g02_envelope"],
            ctx,gyms_data,"complete" if action=="complete_gym" else "advance",
            chapter_key=ctx[0]["chapters"][current]["key"],
            simulation_gate=simulation_gate if action=="complete_gym" else None)
        changed=copy.deepcopy(env)
        changed["g024_envelope"]["g023_envelope"]["g02_envelope"]=forwarded["envelope"]
        validate_envelope(changed,ctx,gyms_data,finale_data,postgame_data,data)
        return result(changed,APPLIED if forwarded["status"]!= "ALREADY_RECORDED_NO_OP" else REPLAY)
    if action=="rematch":
        if actor_key not in data["rematch"]["actors"] or (
            type(session_id) is not int or not 1<=session_id<=data["max_rematch_sessions_per_rival"]):
            deny("unapproved rival rematch actor or invalid bounded session")
        if outcome not in {"WIN","LOSS"}:deny("rematch requires explicit WIN/LOSS")
        if current!=12:
            deny("rematches require G02.3 completed credits and CH12")
        if not any(x["actor_key"]==actor_key and
            any(r["event_key"]==x["id"] for r in env["battle_receipts"])
            for x in data["encounters"] if x["source_mode"]=="PLANNED"):
            deny("first planned rival victory not yet recorded")
        older=[x for x in env["rematch_receipts"] if x["actor_key"]==actor_key]
        if session_id<=len(older):
            if outcome=="WIN":return result(env,REPLAY)
            deny("cannot rewrite a completed rival rematch WIN as LOSS")
        if session_id!=len(older)+1:deny("rematch sessions must be sequential")
        if outcome=="LOSS":return result(env,LOSS)
        changed=copy.deepcopy(env)
        changed["rematch_receipts"].append({
            "actor_key":actor_key,"session_id":session_id,
            "outcome":"WIN","receipt_scope":RECEIPT_SCOPE})
        validate_envelope(changed,ctx,gyms_data,finale_data,postgame_data,data)
        return result(changed,APPLIED)
    deny("unsupported operation")

def plan_team(env:dict,ctx:tuple,gyms_data:dict,finale_data:dict,
              postgame_data:dict,policy:dict,data:dict, *,encounter_key:str,
              party:list[dict],engine_max_level:int,story_stage:int,
              synthetic_authored_team_size:int|None=None)->dict:
    """Read-only scaling projection, never a real Pokémon party."""
    validate_envelope(env,ctx,gyms_data,finale_data,postgame_data,data)
    entry=_known(data,encounter_key)
    if entry["battle_policy"]=="NO_BATTLE":
        deny("dialogue is not a trainer battle")
    if _state_index(env,ctx)!=entry["chapter_index"]:
        deny("team previews only for an active symbolic chapter")
    if entry["source_mode"]!="PLANNED" and not _linked(entry,env):
        deny("linked battle has no recorded G01.3 or G02.3 proof yet")
    balance._int(story_stage,"story_stage",0,3)
    if synthetic_authored_team_size is not None:
        balance._int(synthetic_authored_team_size,"synthetic_authored_team_size",1,6)
    progress,empty=balance._party_progress(party,engine_max_level)
    master=story_stage==3
    pct=policy["level_cap"]["master_percent" if master else "normal_percent"]
    scale=max(1,min(engine_max_level,progress*pct//100))
    size=(max(4,synthetic_authored_team_size) if master else
          synthetic_authored_team_size) if synthetic_authored_team_size is not None else None
    return {"phase":"G03.3","status":"UNVERIFIED_SCALING_PLAN_ONLY",
        "encounter_key":entry["id"],"trainer_reference_key":entry["trainer_reference_key"],
        "team_variant_key":entry["team_variant_key"],
        "chapter_key":entry["chapter_key"],
        "difficulty":"MASTER" if master else "NORMAL",
        "percent":pct,"progress_signal_level":progress,
        "empty_or_all_eggs_fallback":empty,"target_synthetic_level":scale,
        "regional_numeric_level_cap":None,
        "synthetic_authored_team_size":synthetic_authored_team_size,
        "synthetic_target_team_size":size,
        "missing_master_slots":size-synthetic_authored_team_size if size is not None else None,
        "canonical_team":None,"native_team_verified":False,
        "native_evolutions_applied":False,"native_weakness_coverage_verified":False,
        "native_pbs_mutated":False,"game_exe_tested":False,"can_install":False}

def build_demo(ctx:tuple,gyms_data:dict,finale_data:dict,postgame_data:dict,
               policy:dict,data:dict)->tuple[dict,dict]:
    """Replay full G01/G02.2/G02.3 path with G03.3 gates, no shortcuts."""
    env=initial(ctx);snapshots={"CH00":copy.deepcopy(env)}
    def g02(action:str,**kwargs):
        nonlocal env
        r=gyms.apply(env["g024_envelope"]["g023_envelope"]["g02_envelope"],
                     ctx,gyms_data,action,**kwargs)
        env=copy.deepcopy(env)
        env["g024_envelope"]["g023_envelope"]["g02_envelope"]=r["envelope"]
        validate_envelope(env,ctx,gyms_data,finale_data,postgame_data,data)
    def g03(action:str,**kwargs):
        nonlocal env
        r=apply(env,ctx,gyms_data,finale_data,postgame_data,data,action,**kwargs)
        env=r["envelope"]
        return r
    def g023(action:str,**kwargs):
        nonlocal env
        r=finale.apply(env["g024_envelope"]["g023_envelope"],
                       ctx,gyms_data,finale_data,action,**kwargs)
        env=copy.deepcopy(env)
        env["g024_envelope"]["g023_envelope"]=r["envelope"]
        validate_envelope(env,ctx,gyms_data,finale_data,postgame_data,data)
    g02("begin");snapshots["CH01_START"]=copy.deepcopy(env)
    for event in ctx[3]:
        kw={"event_key":event["key"]}
        if event["kind"]=="choice":kw["starter_choice"]="SNIVY"
        if event["battle_policy"] in ("ADVANCE_ON_LOSS","WIN_REQUIRED"):
            kw["outcome"]="WIN"
        g02("record_u07",**kw)
    snapshots["CH01_COMPLETE_EVENTS"]=copy.deepcopy(env)
    g02("complete",chapter_key=ctx[0]["chapters"][1]["key"],
        simulation_gate=machine.SIMULATION_GATE)
    g02("advance",chapter_key=ctx[0]["chapters"][1]["key"])
    for gym in gyms_data["gyms"]:
        index=gym["index"]
        snapshots[f"CH{index+1:02d}_START"]=copy.deepcopy(env)
        for event in [e for e in data["encounters"] if e["source_mode"]=="PLANNED"
                      and e["chapter_index"]==index+1]:
            g03("record_battle",encounter_key=event["id"],outcome="WIN")
        snapshots[f"CH{index+1:02d}_STORY_DONE"]=copy.deepcopy(env)
        for event in gym["events"]:
            kw={"event_key":event["id"]}
            if event["kind"]=="battle":
                kw.update(outcome="WIN",leader_key=gyms._leader(gym,_g01(env)))
            g02("record_story",**kw)
        snapshots[f"CH{index+1:02d}_READY_TO_COMPLETE"]=copy.deepcopy(env)
        g03("complete_gym",simulation_gate=machine.SIMULATION_GATE)
        snapshots[f"CH{index+1:02d}_CHAPTER_COMPLETED"]=copy.deepcopy(env)
        g03("advance_gym")
    snapshots["CH10_LEAGUE"]=copy.deepcopy(env)
    for member in finale_data["elite_members"]:
        g023("elite_battle",member_key=member["key"],outcome="WIN")
    g023("complete_elite",simulation_gate=machine.SIMULATION_GATE)
    g023("advance_castle")
    for event in finale_data["castle_events"]:
        kw={"event_key":event["id"]}
        if event["kind"]=="battle":
            kw.update(outcome="WIN",opponent_key="N" if event["stage"]==2 else "GHETSIS")
        g023("castle_event",**kw)
    snapshots["CH11_CASTLE_DONE"]=copy.deepcopy(env)
    g023("complete_castle",simulation_gate=machine.SIMULATION_GATE)
    g023("unlock_postgame")
    snapshots["CH12_POSTGAME"]=copy.deepcopy(env)
    return env,snapshots

def demo(ctx:tuple,gyms_data:dict,finale_data:dict,postgame_data:dict,
         policy:dict,data:dict)->dict:
    env,checkpoints=build_demo(ctx,gyms_data,finale_data,postgame_data,policy,data)
    preview=plan_team(checkpoints["CH02_START"],ctx,gyms_data,
        finale_data,postgame_data,policy,data,
        encounter_key="UNOVA_G033_CH02_CHEREN",
        party=[{"level":40,"egg":False},{"level":70,"egg":True}],
        engine_max_level=100,story_stage=3,synthetic_authored_team_size=3)
    if preview["target_synthetic_level"]!=36 or preview["missing_master_slots"]!=1:
        deny("G03.2 Master projection differs from policy")
    re=apply(env,ctx,gyms_data,finale_data,postgame_data,data,
        "rematch",actor_key="CHEREN",session_id=1,outcome="WIN")
    env=re["envelope"]
    re=apply(env,ctx,gyms_data,finale_data,postgame_data,data,
        "rematch",actor_key="BIANCA",session_id=1,outcome="WIN")
    env=re["envelope"]
    proof=validate_envelope(env,ctx,gyms_data,finale_data,postgame_data,data)
    original=_g01(env)
    if codec.decode_current(codec.encode_current(original,ctx),ctx)!=original:
        deny("G01.4 authoritative state projection failed")
    if proof["planned_battle_wins"]!=9 or proof["rival_rematches"]!=2:
        deny("G03.3 source-based chapter campaign did not reach expected proof")
    return {"phase":"G03.3","status":"OFFLINE_RIVALS_PLASMA_SIMULATED_NOT_NATIVE",
       "chapter":ctx[0]["chapters"][12]["key"],
       "planned_battles_recorded":proof["planned_battle_wins"],
       "read_only_linked_events":6,
       "unique_reward_intents":proof["unique_story_reward_intents"],
       "synthetic_rival_rematches":proof["rival_rematches"],
       "scaled_synthetic_master_level":preview["target_synthetic_level"],
       "g01_4_projection_roundtrip":True,
       "game_exe_tested":False,"native_saves_modified":False,
       "native_rewards_granted":False,"can_install":False}

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check",action="store_true")
    group.add_argument("--simulate-demo",action="store_true")
    args=parser.parse_args(argv)
    try:
        ctx,gyms_data,finale_data,postgame_data,policy,data=load_project()
        if args.check:
            npcs=machine._safe_source(ROOT/data["sources"]["npc_catalog"])
            refs=machine._safe_source(ROOT/data["sources"]["trainer_references"])
            areas=machine._safe_source(ROOT/data["sources"]["areas"])
            u07=machine._safe_source(ROOT/data["sources"]["g01_u07"])
            report=validate_catalog(data,ctx,gyms_data,finale_data,postgame_data,
                                    policy,npcs,refs,areas,u07)
        else:
            report=demo(ctx,gyms_data,finale_data,postgame_data,policy,data)
        print(json.dumps(report,sort_keys=True,ensure_ascii=False))
        return 0
    except (ValueError,TypeError,KeyError,IndexError,OSError,RecursionError) as exc:
        print("UNOVA_G03_3_BLOCKED: "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
