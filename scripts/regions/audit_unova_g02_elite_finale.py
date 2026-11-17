#!/usr/bin/env python3
"""G02.3 Unova White Elite Four/N/Ghetsis/credits, pure offline simulator.

Keeps all G01.1-G01.4/G02.2 data isolated from any native game or save.
Elite Four wins are a unique set, regardless of the order chosen. Castle events
are a strict prefix. Losses are no-ops with a symbolic suggested return area.
No native items, maps, parties, Zekrom capture, credits or travel are executed.
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

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"data/regions/unova-g02-elite-finale-contracts.json"
SCOPE=ledger.SCOPE
RECEIPT_SCOPE="OFFLINE_G023_NOT_A_NATIVE_BATTLE_OR_CREDITS"
MEMBERS=(("SHAUNTAL","GHOST"),("GRIMSLEY","DARK"),
         ("CAITLIN","PSYCHIC"),("MARSHAL","FIGHTING"))
CASTLE=("CASTLE_ENTRY","ZEKROM_STORY_GATE","N_BATTLE",
        "GHETSIS_BATTLE","CREDITS")
KINDS=("narrative","legendary_story_gate","battle","battle","credits")
ACTIONS=frozenset({"elite_battle","complete_elite","advance_castle",
                   "castle_event","complete_castle","unlock_postgame","reenter"})
FIELDS={"schema","region","campaign","scope","g02_envelope","elite_wins",
        "castle_receipts","unique_story_tokens"}
RESULT_SUCCESS="APPLIED_SIMULATION"
RESULT_REPLAY="ALREADY_RECORDED_NO_OP"
RESULT_LOSS="BATTLE_LOST_RETRY_REQUIRED"
RESULT_REENTER="REENTERED_READ_ONLY"

def deny(message:str)->None:
    raise ValueError("UNOVA_G02_3_BLOCKED: "+message)

def exact(obj:Any,keys:set[str],label:str)->None:
    if not isinstance(obj,dict) or set(obj)!=keys:
        deny(label+" has unexpected or missing fields")

def load_project(root:Path=ROOT)->tuple[tuple,dict,dict]:
    root=Path(root)
    ctx,gym_catalog=gyms.load_project(root)
    catalog=machine._safe_source(root/"data/regions/unova-g02-elite-finale-contracts.json")
    regions=machine._safe_source(root/catalog["source_region_registry"])
    areas=machine._safe_source(root/catalog["source_area_catalog"])
    validate_catalog(catalog,ctx,gym_catalog,regions,areas)
    return ctx,gym_catalog,catalog

def validate_catalog(catalog:dict,ctx:tuple,gym_catalog:dict,
                     regions:dict,areas:dict)->dict:
    exact(catalog,{"schema","phase","region","campaign","status",
       "source_g01_contract","source_g01_transitions","source_g01_reentry",
       "source_g01_serialization","source_g02_gym_contracts",
       "source_area_catalog","source_region_registry","required_badges",
       "elite_chapter_key","castle_chapter_key","postgame_chapter_key",
       "elite_area_key","castle_area_key","chapter_order","simulation_gate",
       "elite_order","elite_members","castle_events","castle_order",
       "safe_loss_return_areas","unique_story_tokens","native_game_modified",
       "native_saves_modified","game_exe_tested","can_install",
       "legendary_captured","real_credits_shown","rewards_granted","notes"},"G02.3 catalog")
    c,r,p,events,_=ctx
    expected={
       "schema":1,"phase":"G02.3","region":"UNOVA","campaign":"WHITE_BW",
       "status":"OFFLINE_ELITE_FINALE_CONTRACTS_ONLY",
       "source_g01_contract":"data/regions/unova-g01-state-contract.json",
       "source_g01_transitions":"data/regions/unova-g01-chapter-transitions.json",
       "source_g01_reentry":"data/regions/unova-g01-reentry-policy.json",
       "source_g01_serialization":"data/regions/unova-g01-serialization-contract.json",
       "source_g02_gym_contracts":"data/regions/unova-g02-gym-story-contracts.json",
       "source_area_catalog":"data/regions/unova-u03-areas.json",
       "source_region_registry":"site/public/data/regions.json",
       "required_badges":["TRIO","BASIC","INSECT","BOLT",
                           "QUAKE","JET","FREEZE","LEGEND"],
       "elite_chapter_key":c["chapters"][10]["key"],
       "castle_chapter_key":c["chapters"][11]["key"],
       "postgame_chapter_key":c["chapters"][12]["key"],
       "elite_area_key":"UNOVA_ELITE_FOUR",
       "castle_area_key":"UNOVA_NS_CASTLE",
       "chapter_order":[c["chapters"][i]["key"] for i in (10,11,12)],
       "simulation_gate":machine.SIMULATION_GATE,
       "elite_order":"ANY_ORDER_ONCE_EACH","castle_order":"STRICT_PREFIX",
       "safe_loss_return_areas":{"elite":"UNOVA_POKEMON_LEAGUE",
                                 "castle":"UNOVA_NS_CASTLE"},
       "unique_story_tokens":{
           "legendary_gate":"UNOVA_G023_ZEKROM_GATE_READY_NOT_CAPTURED",
           "credits":"UNOVA_G023_CREDITS_SIMULATED",
           "postgame":"UNOVA_G023_POSTGAME_ACCESS_SIMULATED"},
       "native_game_modified":False,"native_saves_modified":False,
       "game_exe_tested":False,"can_install":False,
       "legendary_captured":False,"real_credits_shown":False,
       "rewards_granted":False
    }
    for key,val in expected.items():
        if type(catalog.get(key)) is not type(val) or catalog[key]!=val:
            deny("unsafe, invalid or invented source contract field: "+key)
    if (not isinstance(catalog["notes"],list) or len(catalog["notes"])<4 or
        gym_catalog.get("phase")!="G02.2" or
        regions.get("regions",{}).get("UNOVA",{}).get("status")!="planned" or
        regions["regions"]["UNOVA"].get("milestones")!=expected["required_badges"]):
        deny("catalog or region registry no longer reference-only")
    area_keys={x["key"] for x in areas.get("areas",[])}
    if len(area_keys)!=74 or any(key not in area_keys for key in
        ("UNOVA_POKEMON_LEAGUE","UNOVA_ELITE_FOUR","UNOVA_NS_CASTLE")):
        deny("finale areas not in U03 reference inventory")
    if not isinstance(catalog["elite_members"],list) or len(catalog["elite_members"])!=4:
        deny("expected four elite members")
    for member,(name,specialty) in zip(catalog["elite_members"],MEMBERS):
        exact(member,{"key","member_name","specialty","chapter_key","area_key",
              "battle_outcome_required","native_trainer_id","team","levels",
              "simulation_only"},"elite member")
        wanted={"key":"UNOVA_G023_ELITE_"+name,"member_name":name,
            "specialty":specialty,"chapter_key":c["chapters"][10]["key"],
            "area_key":"UNOVA_ELITE_FOUR","battle_outcome_required":"WIN",
            "native_trainer_id":None,"team":None,"levels":None,"simulation_only":True}
        if member!=wanted:deny("elite source or native team metadata mismatch")
    if not isinstance(catalog["castle_events"],list) or len(catalog["castle_events"])!=5:
        deny("exactly five castle story events required")
    for i,event in enumerate(catalog["castle_events"]):
        exact(event,{"id","kind","stage","chapter_key","area_key",
              "description_ptbr","requires","outcome_required","single_execution",
              "native_event_id","native_map_id","team","levels"},"castle event")
        eid="UNOVA_G023_"+CASTLE[i]
        wanted={"id":eid,"kind":KINDS[i],"stage":i,
                "chapter_key":c["chapters"][11]["key"],
                "area_key":"UNOVA_NS_CASTLE",
                "requires":["UNOVA_G023_"+CASTLE[i-1]] if i else [],
                "outcome_required":"WIN" if i in (2,3) else None,
                "single_execution":True,"native_event_id":None,
                "native_map_id":None,"team":None,"levels":None}
        if any(event[k]!=v or type(event[k]) is not type(v) for k,v in wanted.items()):
            deny("castle event order, battle outcome, or native metadata mismatch")
        if not isinstance(event["description_ptbr"],str) or not event["description_ptbr"].strip():
            deny("castle stage needs Portuguese narrative description")
    return {"phase":"G02.3","elite_members":4,"castle_events":5,
            "any_order_elite":True,"status":"OFFLINE_FINALE_CONTRACTS_VALIDATED",
            "can_install":False,"game_exe_tested":False}

def initial(ctx:tuple)->dict:
    return {"schema":1,"region":"UNOVA","campaign":"WHITE_BW",
        "scope":SCOPE,"g02_envelope":gyms.initial(ctx),
        "elite_wins":[],"castle_receipts":[],"unique_story_tokens":[]}

def _index(env:dict,ctx:tuple)->int:
    return machine._chapter_index(env["g02_envelope"]["g01_envelope"]["state"],ctx[0])

def _expected_tokens(env:dict,catalog:dict,index:int)->list[str]:
    tokens=catalog["unique_story_tokens"]
    n=len(env["castle_receipts"])
    value=[]
    if n>=2:value.append(tokens["legendary_gate"])
    if n>=5:value.append(tokens["credits"])
    if index>=12:value.append(tokens["postgame"])
    return value

def validate_envelope(env:dict,ctx:tuple,gym_catalog:dict,catalog:dict)->dict:
    exact(env,FIELDS,"G02.3 envelope")
    if (type(env["schema"]) is not int or env["schema"]!=1 or
        env["region"]!="UNOVA" or env["campaign"]!="WHITE_BW" or
        env["scope"]!=SCOPE):
        deny("G02.3 version/region/scope mismatch")
    gym_proof=gyms.validate_envelope(env["g02_envelope"],ctx,gym_catalog)
    idx=gym_proof["chapter_index"]
    wins=env["elite_wins"]
    members={m["key"] for m in catalog["elite_members"]}
    if not isinstance(wins,list) or len(wins)>4:
        deny("elite wins require a bounded array")
    seen=set()
    for rec in wins:
        exact(rec,{"member_key","outcome","receipt_scope"},"elite receipt")
        key=rec["member_key"]
        if not isinstance(key,str) or key not in members or key in seen or (
            rec["outcome"]!="WIN" or rec["receipt_scope"]!=RECEIPT_SCOPE):
            deny("elite win receipt forged, duplicate or unknown")
        seen.add(key)
    if idx<10 and wins:deny("elite wins before eight badges/League")
    if idx>=11 and len(seen)!=4:deny("Castle requires four unique Elite wins")
    g01state=env["g02_envelope"]["g01_envelope"]["state"]
    elite_status=g01state["missions"].get(ctx[0]["missions"][9]["key"])
    if idx==10 and elite_status=="completed" and len(seen)!=4:
        deny("League mission completed without four elite wins")
    castle=env["castle_receipts"]
    if not isinstance(castle,list) or len(castle)>5:
        deny("castle receipts malformed or too numerous")
    if idx<11 and castle:deny("castle events recorded before Castle chapter")
    for i,receipt in enumerate(castle):
        event=catalog["castle_events"][i]
        exact(receipt,{"event_key","outcome","opponent_key","receipt_scope"},"castle receipt")
        opponent=CASTLE[i].replace("_BATTLE","") if i in (2,3) else None
        expected={"event_key":event["id"],"outcome":"WIN" if i in (2,3) else None,
                  "opponent_key":opponent,"receipt_scope":RECEIPT_SCOPE}
        if receipt!=expected:deny("castle event order or battle result invalid")
    status=g01state["missions"].get(ctx[0]["missions"][10]["key"])
    if idx==11 and status=="completed" and len(castle)!=5:
        deny("Castle mission completed before credits")
    if idx>=12 and len(castle)!=5:
        deny("postgame entered without all finale events and credits")
    tokens=env["unique_story_tokens"]
    if not isinstance(tokens,list) or tokens!=_expected_tokens(env,catalog,idx):
        deny("once-only Zekrom/credits/postgame tokens inconsistent with events")
    return {"phase":"G02.3","chapter_index":idx,"elite_wins":len(wins),
            "castle_events":len(castle),"credits_simulated":len(castle)==5,
            "postgame_simulated":idx>=12,"native_save_modified":False,
            "real_credits_shown":False,"game_exe_tested":False,"can_install":False}

def result(env:dict,status:str,*,return_area:str|None=None)->dict:
    return {"status":status,"envelope":copy.deepcopy(env),
        "suggested_safe_return_area_key":return_area,
        "native_teleport_executed":False,"actual_rewards_granted":False,
        "legendary_captured":False,"native_save_modified":False,
        "real_credits_shown":False,"game_exe_tested":False,"can_install":False}

def apply(env:dict,ctx:tuple,gym_catalog:dict,catalog:dict,
          action:str,*,member_key:str|None=None,event_key:str|None=None,
          outcome:str|None=None,opponent_key:str|None=None,
          chapter_key:str|None=None,simulation_gate:str|None=None)->dict:
    """Pure, fail-closed; no real save, badge, battle, or credits are touched."""
    validate_envelope(env,ctx,gym_catalog,catalog)
    if action not in ACTIONS:deny("unknown finale operation")
    idx=_index(env,ctx)
    state=env["g02_envelope"]["g01_envelope"]["state"]
    if action!="elite_battle" and member_key is not None:
        deny("member key only permitted for Elite battle")
    if action!="castle_event" and (event_key is not None or opponent_key is not None):
        deny("castle event arguments used outside castle_event")
    if action not in {"elite_battle","castle_event"} and outcome is not None:
        deny("outcome only permitted on a battle event")
    if action!="reenter" and chapter_key is not None:
        deny("chapter_key only permitted on reentry")
    if action not in {"complete_elite","complete_castle"} and simulation_gate is not None:
        deny("simulation gate only permitted on chapter completion")
    if action=="elite_battle":
        members={m["key"] for m in catalog["elite_members"]}
        if member_key not in members or outcome not in {"WIN","LOSS"}:
            deny("unknown Elite member or missing explicit battle outcome")
        if idx<10 or idx>11:
            # Completed wins remain inspectable after the story, but new wins cannot occur there.
            if idx==12 and outcome=="WIN" and any(x["member_key"]==member_key for x in env["elite_wins"]):
                return result(env,RESULT_REPLAY)
            deny("Elite battle is outside League/Castle")
        previous=next((x for x in env["elite_wins"] if x["member_key"]==member_key),None)
        if previous is not None:
            if outcome=="WIN":return result(env,RESULT_REPLAY)
            deny("cannot rewrite a recorded Elite win as loss")
        if idx!=10 or state["missions"].get(ctx[0]["missions"][9]["key"])!="active":
            deny("Elite win cannot begin after leaving the active League")
        if outcome=="LOSS":
            return result(env,RESULT_LOSS,
                return_area=catalog["safe_loss_return_areas"]["elite"])
        changed=copy.deepcopy(env)
        changed["elite_wins"].append({"member_key":member_key,"outcome":"WIN",
                                      "receipt_scope":RECEIPT_SCOPE})
        validate_envelope(changed,ctx,gym_catalog,catalog)
        return result(changed,RESULT_SUCCESS)
    if action=="castle_event":
        events={e["id"]:i for i,e in enumerate(catalog["castle_events"])}
        if not isinstance(event_key,str) or event_key not in events:
            deny("unknown castle event")
        i=events[event_key]
        expected_opponent=CASTLE[i].replace("_BATTLE","") if i in (2,3) else None
        if i in (2,3):
            if opponent_key!=expected_opponent or outcome not in {"WIN","LOSS"}:
                deny("N/Ghetsis require named opponent and explicit WIN/LOSS")
        elif opponent_key is not None or outcome is not None:
            deny("nonbattle castle event cannot claim battle results")
        receipts=env["castle_receipts"]
        if i<len(receipts):
            if outcome!="LOSS" and receipts[i]=={
                "event_key":event_key,"outcome":"WIN" if i in (2,3) else None,
                "opponent_key":expected_opponent,"receipt_scope":RECEIPT_SCOPE}:
                return result(env,RESULT_REPLAY)
            deny("conflicting replay of a once-only castle event")
        if idx!=11 or state["missions"].get(ctx[0]["missions"][10]["key"])!="active":
            deny("new Castle event outside active CH11")
        if i!=len(receipts):deny("castle event out of story order")
        if len(env["elite_wins"])!=4:deny("Castle entry requires four Elite wins")
        if outcome=="LOSS":
            return result(env,RESULT_LOSS,
                return_area=catalog["safe_loss_return_areas"]["castle"])
        changed=copy.deepcopy(env)
        changed["castle_receipts"].append({
            "event_key":event_key,"outcome":"WIN" if i in (2,3) else None,
            "opponent_key":expected_opponent,"receipt_scope":RECEIPT_SCOPE})
        changed["unique_story_tokens"]=_expected_tokens(changed,catalog,idx)
        validate_envelope(changed,ctx,gym_catalog,catalog)
        return result(changed,RESULT_SUCCESS)
    if action=="reenter":
        if simulation_gate is not None:deny("reenter cannot accept simulation gate")
        if chapter_key not in [ctx[0]["chapters"][i]["key"] for i in range(1,idx+1)]:
            deny("reenter forbidden for unknown/future chapter")
        forwarded=gyms.apply(env["g02_envelope"],ctx,gym_catalog,"reenter",
                             chapter_key=chapter_key)
        if forwarded["status"]!="REENTERED_READ_ONLY":
            deny("unexpected G02.2 reentry")
        return result(env,RESULT_REENTER)
    if simulation_gate is not None and simulation_gate!=machine.SIMULATION_GATE:
        deny("completion requires explicit synthetic-only gate")
    if action in {"complete_elite","advance_castle"} and idx!=10:
        if idx>10 and (len(env["elite_wins"])==4 and
                       state["missions"].get(ctx[0]["missions"][9]["key"])=="completed"):
            return result(env,RESULT_REPLAY)
        deny("Elite progression only in CH10")
    if action in {"complete_castle","unlock_postgame"} and idx!=11:
        if idx==12 and len(env["castle_receipts"])==5 and (
            state["missions"].get(ctx[0]["missions"][10]["key"])=="completed"):
            return result(env,RESULT_REPLAY)
        deny("Castle progression only in CH11")
    if action=="complete_elite":
        if simulation_gate!=machine.SIMULATION_GATE:deny("explicit synthetic gate required")
        if len(env["elite_wins"])!=4:deny("must defeat all four Elite members")
        if state["missions"][ctx[0]["missions"][9]["key"]]=="completed":
            return result(env,RESULT_REPLAY)
        forwarded_action="complete";chapter=ctx[0]["chapters"][10]["key"]
    elif action=="advance_castle":
        if len(env["elite_wins"])!=4 or state["missions"][ctx[0]["missions"][9]["key"]]!="completed":
            deny("Castle is locked until all Elite wins and chapter completion")
        forwarded_action="advance";chapter=ctx[0]["chapters"][10]["key"]
    elif action=="complete_castle":
        if simulation_gate!=machine.SIMULATION_GATE:deny("explicit synthetic gate required")
        if len(env["castle_receipts"])!=5:deny("N, Ghetsis and credits required")
        if state["missions"][ctx[0]["missions"][10]["key"]]=="completed":
            return result(env,RESULT_REPLAY)
        forwarded_action="complete";chapter=ctx[0]["chapters"][11]["key"]
    elif action=="unlock_postgame":
        if len(env["castle_receipts"])!=5 or (
            state["missions"][ctx[0]["missions"][10]["key"]]!="completed"):
            deny("postgame requires completed credits and Castle chapter")
        forwarded_action="advance";chapter=ctx[0]["chapters"][11]["key"]
    else:
        deny("operation not supported")
    forwarded=ledger.apply(env["g02_envelope"]["g01_envelope"],*ctx[:4],
                           forwarded_action,chapter_key=chapter,
                           simulation_gate=simulation_gate if forwarded_action=="complete" else None)
    changed=copy.deepcopy(env)
    changed["g02_envelope"]["g01_envelope"]=forwarded["envelope"]
    changed["unique_story_tokens"]=_expected_tokens(changed,catalog,_index(changed,ctx))
    validate_envelope(changed,ctx,gym_catalog,catalog)
    return result(changed,RESULT_SUCCESS if forwarded["status"]==ledger.STATUS_APPLIED
                  else RESULT_REPLAY)

def build_league_fixture(ctx:tuple,gym_catalog:dict)->dict:
    """Replays all G01/G02 prereqs, no hardcoded or bypassed eight badges."""
    c,r,p,events,_=ctx
    env=gyms.initial(ctx)
    def act(name,**kwargs):
        nonlocal env
        env=gyms.apply(env,ctx,gym_catalog,name,**kwargs)["envelope"]
    act("begin")
    for e in events:
        kw={"event_key":e["key"]}
        if e["kind"]=="choice":kw["starter_choice"]="SNIVY"
        if e["battle_policy"] in {"ADVANCE_ON_LOSS","WIN_REQUIRED"}:
            kw["outcome"]="WIN"
        act("record_u07",**kw)
    act("complete",chapter_key=c["chapters"][1]["key"],
        simulation_gate=machine.SIMULATION_GATE)
    act("advance",chapter_key=c["chapters"][1]["key"])
    for g in gym_catalog["gyms"]:
        for e in g["events"]:
            kw={"event_key":e["id"]}
            if e["kind"]=="battle":
                kw["outcome"]="WIN"
                kw["leader_key"]=gyms._leader(g,env["g01_envelope"])
            act("record_story",**kw)
        act("complete",chapter_key=g["chapter_key"],
            simulation_gate=machine.SIMULATION_GATE)
        act("advance",chapter_key=g["chapter_key"])
    if env["badge_claims"]!=[g["badge"] for g in gym_catalog["gyms"]]:
        deny("League fixture missing eight unique badges")
    return {"schema":1,"region":"UNOVA","campaign":"WHITE_BW","scope":SCOPE,
            "g02_envelope":env,"elite_wins":[],"castle_receipts":[],
            "unique_story_tokens":[]}

def demo(ctx:tuple,gym_catalog:dict,catalog:dict)->dict:
    env=build_league_fixture(ctx,gym_catalog)
    def perform(action,**kwargs):
        nonlocal env
        r=apply(env,ctx,gym_catalog,catalog,action,**kwargs)
        env=r["envelope"]
        return r
    order=list(reversed([x["key"] for x in catalog["elite_members"]]))
    loss=perform("elite_battle",member_key=order[0],outcome="LOSS")
    if loss["status"]!=RESULT_LOSS:deny("Elite defeat must preserve progress")
    for key in order:
        perform("elite_battle",member_key=key,outcome="WIN")
    perform("complete_elite",simulation_gate=machine.SIMULATION_GATE)
    perform("advance_castle")
    for e in catalog["castle_events"]:
        kw={"event_key":e["id"]}
        if e["kind"]=="battle":
            kw.update(outcome="WIN",opponent_key=CASTLE[e["stage"]].replace("_BATTLE",""))
            if perform("castle_event",**{**kw,"outcome":"LOSS"})["status"]!=RESULT_LOSS:
                deny("Castle loss must be retriable")
        perform("castle_event",**kw)
    perform("complete_castle",simulation_gate=machine.SIMULATION_GATE)
    perform("unlock_postgame")
    validated=validate_envelope(env,ctx,gym_catalog,catalog)
    projection=codec.encode_current(env["g02_envelope"]["g01_envelope"],ctx)
    if codec.decode_current(projection,ctx)!=env["g02_envelope"]["g01_envelope"]:
        deny("G01.4 projection failed to round-trip")
    if validated["chapter_index"]!=12 or len(env["unique_story_tokens"])!=3:
        deny("postgame not symbolically unlocked")
    return {"phase":"G02.3","status":"OFFLINE_FINALE_SIMULATION_NOT_GAMEPLAY",
            "elite_wins":len(env["elite_wins"]),"elite_order":order,
            "castle_events":len(env["castle_receipts"]),
            "unique_story_tokens":env["unique_story_tokens"],
            "final_chapter":ctx[0]["chapters"][12]["key"],
            "g01_4_projection_roundtrip":True,
            "legendary_captured":False,"real_credits_shown":False,
            "native_save_modified":False,"game_exe_tested":False,
            "can_install":False}

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--simulate-demo",action="store_true")
    args=parser.parse_args(argv)
    try:
        ctx,gyms_data,catalog=load_project()
        regions=machine._safe_source(ROOT/catalog["source_region_registry"])
        areas=machine._safe_source(ROOT/catalog["source_area_catalog"])
        report=(validate_catalog(catalog,ctx,gyms_data,regions,areas) if args.check
                else demo(ctx,gyms_data,catalog))
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,TypeError,KeyError,IndexError,OSError,RecursionError) as exc:
        print("UNOVA_G02_3_BLOCKED: "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
