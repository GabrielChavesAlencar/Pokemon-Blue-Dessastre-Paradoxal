#!/usr/bin/env python3
"""Unova G02.2: 8 gym story contracts + simulated badge claims. No Game.exe.

Wraps G01.1–G01.3 and verifies a G01.4 serialization round trip of the G01
projection. Does not mutate G01.1 schema, save files, game scripts, badges,
items, HMs, map IDs, or executable. G02.3 handles the Elite Four and finale.
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

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"data/regions/unova-g02-gym-story-contracts.json"
SCOPE=ledger.SCOPE
STAGES=("ARRIVAL","STORY_GATE","LEADER_BATTLE","BADGE","AFTER_STORY")
KINDS=("narrative","narrative","battle","badge","narrative")
LEADERS=("TRIO_BY_STARTER","LENORA","BURGH","ELESA","CLAY","SKYLA","BRYCEN","IRIS")
PHASES=("U08","U10","U12","U15","U16","U19","U22","U24")
STRIATON={"SNIVY":"CHILI","TEPIG":"CRESS","OSHAWOTT":"CILAN"}
RESULTS=("APPLIED_SIMULATION","ALREADY_RECORDED_NO_OP","REENTERED_READ_ONLY")
RECEIPT_SCOPE="OFFLINE_G02_2_NOT_A_NATIVE_EVENT"
STATE_KEYS={"schema","region","campaign","scope","g01_envelope","story_receipts","badge_claims"}

def deny(why:str)->None:
    raise ValueError("UNOVA_G02_2_BLOCKED: "+str(why))

def exact(obj:Any,keys:set[str],label:str)->None:
    if not isinstance(obj,dict) or set(obj)!=keys:
        deny(label+" has unexpected or missing fields")

def load_project(root:Path=ROOT)->tuple:
    ctx=codec.load_project(root)
    catalog=machine._safe_source(Path(root)/"data/regions/unova-g02-gym-story-contracts.json")
    region=machine._safe_source(Path(root)/"site/public/data/regions.json")
    areas=machine._safe_source(Path(root)/"data/regions/unova-u03-areas.json")
    validate_catalog(catalog,ctx,region,areas)
    return ctx,catalog

def validate_catalog(catalog:dict,ctx:tuple,regions:dict,areas:dict)->dict:
    c,r,p,ev,serialization=ctx
    exact(catalog,{"schema","phase","region","campaign","status","g01_contract",
        "g01_transitions","g01_reentry","g01_serialization","area_catalog",
        "badge_registry","chapter_range","simulation_gate",
        "native_game_modified","game_exe_tested","can_install",
        "badge_items_granted","actual_story_events_executed","gyms","notes"},"G02.2 catalog")
    expected={"schema":1,"phase":"G02.2","region":"UNOVA","campaign":"WHITE_BW",
        "status":"GITHUB_ONLY_SYMBOLIC_CAMPAIGN_EVENTS",
        "g01_contract":"data/regions/unova-g01-state-contract.json",
        "g01_transitions":"data/regions/unova-g01-chapter-transitions.json",
        "g01_reentry":"data/regions/unova-g01-reentry-policy.json",
        "g01_serialization":"data/regions/unova-g01-serialization-contract.json",
        "area_catalog":"data/regions/unova-u03-areas.json",
        "badge_registry":"site/public/data/regions.json",
        "chapter_range":[2,9],"simulation_gate":machine.SIMULATION_GATE,
        "native_game_modified":False,"game_exe_tested":False,"can_install":False,
        "badge_items_granted":False,"actual_story_events_executed":False}
    for key,val in expected.items():
        if type(catalog.get(key)) is not type(val) or catalog[key]!=val:
            deny("unsafe or unsupported catalog setting: "+key)
    if not isinstance(catalog["notes"],list) or len(catalog["notes"])<3:
        deny("missing limits")
    badge_list=regions.get("regions",{}).get("UNOVA",{}).get("milestones")
    if (regions["regions"]["UNOVA"].get("status")!="planned" or
        badge_list!=["TRIO","BASIC","INSECT","BOLT","QUAKE","JET","FREEZE","LEGEND"]):
        deny("Unova region badge registry drift")
    area_keys={area["key"] for area in areas.get("areas",[])}
    if len(area_keys)!=74 or len(catalog["gyms"])!=8:
        deny("area/gym catalog has unexpected count")
    all_events=set()
    for i,gym in enumerate(catalog["gyms"]):
        idx=i+1;chapter=c["chapters"][idx+1];mission=c["missions"][idx]
        prefix="UNOVA_G02_GYM_"+str(idx).zfill(2)
        city=chapter["reference_area_key"]
        gym_area=city.replace("_CITY","_GYM")
        exact(gym,{"id","index","chapter_key","mission_key","city_area_key",
             "gym_area_key","badge","leader_key","leader_by_starter","campaign",
             "planned_phase","previous_badges","native_badge_item_id",
             "native_badge_switch_id","trainer_party","trainer_levels",
             "challenge_status","events"},"gym")
        wanted={"id":prefix,"index":idx,"chapter_key":chapter["key"],
            "mission_key":mission["key"],"city_area_key":city,"gym_area_key":gym_area,
            "badge":badge_list[i],"leader_key":LEADERS[i],
            "leader_by_starter":STRIATON if idx==1 else None,
            "campaign":"WHITE_BW","planned_phase":PHASES[i],
            "previous_badges":badge_list[:i],"native_badge_item_id":None,
            "native_badge_switch_id":None,"trainer_party":None,"trainer_levels":None,
            "challenge_status":"PLANNED_NOT_PLAYABLE"}
        for key,val in wanted.items():
            if type(gym.get(key)) is not type(val) or gym[key]!=val:
                deny("gym order, badge, leader variant or native claim drift: "+key)
        if city not in area_keys or gym_area not in area_keys:
            deny("gym maps must be reference-only U03 symbols")
        if not isinstance(gym["events"],list) or len(gym["events"])!=5:
            deny("exactly five events per gym required")
        for n,event in enumerate(gym["events"]):
            exact(event,{"id","kind","stage","title_ptbr","requires",
                "outcome_required","simulation_only","native_event_id",
                "source_map_id","trainer_id"},"gym event")
            event_id=prefix+"_"+STAGES[n]
            if event["id"] in all_events:
                deny("duplicate story event")
            all_events.add(event["id"])
            if (event["id"]!=event_id or type(event["stage"]) is not int or
                event["stage"]!=n or event["kind"]!=KINDS[n] or
                event["requires"]!=([prefix+"_"+STAGES[n-1]] if n else []) or
                event["outcome_required"]!=("WIN" if n==2 else None) or
                not isinstance(event["title_ptbr"],str) or not event["title_ptbr"].strip() or
                event["simulation_only"] is not True or
                event["native_event_id"] is not None or
                event["source_map_id"] is not None or event["trainer_id"] is not None):
                deny("source-grounded event stage or native identifier mismatch")
    return {"phase":"G02.2","gyms":8,"badges":8,"symbolic_events":40,
        "campaign":"WHITE_BW","status":"OFFLINE_CONTRACTS_VALIDATED",
        "game_exe_tested":False,"can_install":False}

def initial(ctx:tuple)->dict:
    return {"schema":1,"region":"UNOVA","campaign":"WHITE_BW","scope":SCOPE,
        "g01_envelope":ledger.initial(ctx[0]),"story_receipts":[],"badge_claims":[]}

def _leader(gym:dict,g01envelope:dict)->str:
    if gym["leader_by_starter"] is None:
        return gym["leader_key"]
    receipts=g01envelope["event_receipts"]
    if not receipts or receipts[0]["event_key"]!="UNOVA_U07_STARTER_GIFT":
        deny("Striaton starter choice not recorded in G01.3")
    starter=receipts[0]["starter_choice"]
    leader=gym["leader_by_starter"].get(starter)
    if not leader:deny("unknown starter for Striaton leader")
    return leader

def _expected_receipt(event:dict,gym:dict,env:dict,*,outcome:str|None,
                      leader_key:str|None)->dict:
    if event["kind"]=="battle":
        if outcome!="WIN" or leader_key!=_leader(gym,env["g01_envelope"]):
            deny("gym requires WIN and correct White campaign leader")
    elif outcome is not None or leader_key is not None:
        deny("nonbattle event must have no battle result or leader")
    return {"event_key":event["id"],"outcome":outcome,"leader_key":leader_key,
            "receipt_scope":RECEIPT_SCOPE}

def validate_envelope(env:dict,ctx:tuple,catalog:dict)->dict:
    exact(env,STATE_KEYS,"G02.2 envelope")
    if (type(env["schema"]) is not int or env["schema"]!=1 or
        env["region"]!="UNOVA" or env["campaign"]!="WHITE_BW" or
        env["scope"]!=SCOPE):
        deny("version, scope or region mismatch")
    c,r,p,events,_=ctx
    ledger.validate_envelope(env["g01_envelope"],c,r,p,events)
    state=env["g01_envelope"]["state"]
    index=machine._chapter_index(state,c)
    receipts=env["story_receipts"]
    if not isinstance(receipts,list) or len(receipts)>40:
        deny("story receipt list invalid")
    all_gyms=catalog["gyms"]
    expected_order=[(g,e) for g in all_gyms for e in g["events"]]
    badges=[]
    for n,receipt in enumerate(receipts):
        gym,event=expected_order[n]
        exact(receipt,{"event_key","outcome","leader_key","receipt_scope"},"story receipt")
        if receipt["event_key"]!=event["id"] or receipt["receipt_scope"]!=RECEIPT_SCOPE:
            deny("story receipt out of order or forged")
        expected=_expected_receipt(event,gym,env,
                                   outcome=receipt["outcome"],leader_key=receipt["leader_key"])
        if receipt!=expected:deny("story receipt altered")
        if gym["index"]+1>index:
            deny("story event exists in future chapter")
        if event["kind"]=="badge":
            badges.append(gym["badge"])
    if not isinstance(env["badge_claims"],list) or env["badge_claims"]!=badges or (
         len(set(badges))!=len(badges)):
        deny("badge claims must match once-only badge story receipts")
    if index<=1 and receipts:
        deny("no gym event may occur before opening chapter")
    for gym in all_gyms:
        ch_idx=gym["index"]+1
        actual=sum(1 for receipt in receipts if receipt["event_key"].startswith(gym["id"]+"_"))
        mission_status=state["missions"].get(gym["mission_key"])
        if ch_idx<index:
            if actual!=5 or mission_status!="completed" or gym["badge"] not in badges:
                deny("past gym requires five events, badge and completed mission")
        elif ch_idx==index:
            if mission_status=="completed" and (actual!=5 or gym["badge"] not in badges):
                deny("cannot complete a gym chapter without its badge")
        elif actual:
            deny("future gym receipts forbidden")
    if index>=10 and len(badges)!=8:
        deny("league access requires all eight simulated badges")
    return {"chapter_index":index,"event_count":len(receipts),
        "badge_count":len(badges),"native_badges_granted":False,
        "game_exe_tested":False,"can_install":False}

def _result(env:dict,status:str)->dict:
    return {"status":status,"envelope":copy.deepcopy(env),
        "native_badges_granted":False,"native_events_executed":False,
        "native_save_modified":False,"game_exe_tested":False,"can_install":False}

def apply(env:dict,ctx:tuple,catalog:dict,action:str, *,
          event_key:str|None=None,outcome:str|None=None,
          leader_key:str|None=None,chapter_key:str|None=None,
          starter_choice:str|None=None,simulation_gate:str|None=None)->dict:
    """All operations are fail-closed and do not mutate caller objects."""
    validate_envelope(env,ctx,catalog)
    if action not in {"begin","record_u07","record_story","complete","advance","reenter"}:
        deny("unknown G02.2 action")
    if action!="record_story" and leader_key is not None:
        deny("leader_key only accepted for story battles")
    if action=="record_story":
        if chapter_key is not None or starter_choice is not None or simulation_gate is not None:
            deny("unexpected story operation arguments")
        if not isinstance(event_key,str):deny("event key required")
        index=machine._chapter_index(env["g01_envelope"]["state"],ctx[0])
        all_events=[(g,e) for g in catalog["gyms"] for e in g["events"]]
        candidate=next(((g,e,n) for n,(g,e) in enumerate(all_events)
                        if e["id"]==event_key),None)
        if candidate is None:deny("unknown story event")
        gym,event,position=candidate
        expected=_expected_receipt(event,gym,env,outcome=outcome,leader_key=leader_key)
        if position<len(env["story_receipts"]):
            if env["story_receipts"][position]!=expected:
                deny("conflicting story replay")
            return _result(env,"ALREADY_RECORDED_NO_OP")
        if position!=len(env["story_receipts"]) or gym["index"]+1!=index:
            deny("out-of-order gym event or wrong chapter")
        state=env["g01_envelope"]["state"]
        if state["missions"].get(gym["mission_key"])!="active":
            deny("gym mission must be active")
        if any(badge not in env["badge_claims"] for badge in gym["previous_badges"]):
            deny("missing previous regional badge")
        if any(not any(r["event_key"]==key for r in env["story_receipts"])
               for key in event["requires"]):
            deny("missing story event prerequisite")
        next_env=copy.deepcopy(env)
        next_env["story_receipts"].append(expected)
        if event["kind"]=="badge":
            if gym["badge"] in next_env["badge_claims"]:deny("badge awarded twice")
            next_env["badge_claims"].append(gym["badge"])
        validate_envelope(next_env,ctx,catalog)
        return _result(next_env,"APPLIED_SIMULATION")
    if event_key is not None and action!="record_u07":
        deny("event_key not accepted for this operation")
    if outcome is not None and action!="record_u07":
        deny("outcome not accepted for this operation")
    if starter_choice is not None and action!="record_u07":
        deny("starter_choice only accepted during U07")
    if simulation_gate is not None and action!="complete":
        deny("simulation gate only permitted when completing a chapter")
    index=machine._chapter_index(env["g01_envelope"]["state"],ctx[0])
    if action=="complete" and index>=10:
        deny("League and finale are reserved for G02.3")
    if action=="advance" and index>=10:
        deny("League and finale are reserved for G02.3")
    if action=="complete" and 2<=index<=9:
        gym=catalog["gyms"][index-2]
        seen={r["event_key"] for r in env["story_receipts"]}
        if any(ev["id"] not in seen for ev in gym["events"]) or gym["badge"] not in env["badge_claims"]:
            deny("gym chapter cannot complete before all story events and badge")
    if action=="record_u07" and index!=1:
        # G01.3 still permits exact idempotent replays outside CH01.
        pass
    forwarded=ledger.apply(env["g01_envelope"],*ctx[:4],action,
                           event_key=event_key,starter_choice=starter_choice,
                           outcome=outcome,chapter_key=chapter_key,
                           simulation_gate=simulation_gate)
    changed=copy.deepcopy(env)
    changed["g01_envelope"]=forwarded["envelope"]
    validate_envelope(changed,ctx,catalog)
    if forwarded["status"]==ledger.STATUS_ALREADY:
        status="ALREADY_RECORDED_NO_OP"
    elif forwarded["status"]==ledger.STATUS_REENTER:
        status="REENTERED_READ_ONLY"
    elif forwarded["status"]==ledger.STATUS_RETRY:
        status="BATTLE_LOST_RETRY_REQUIRED"
    else:status="APPLIED_SIMULATION"
    return _result(changed,status)

def demo(ctx:tuple,catalog:dict)->dict:
    c,r,p,events,_=ctx
    env=initial(ctx)
    def action(name,**kwargs):
        nonlocal env
        result=apply(env,ctx,catalog,name,**kwargs)
        env=result["envelope"]
        return result
    action("begin")
    for event in events:
        kw={"event_key":event["key"]}
        if event["kind"]=="choice":kw["starter_choice"]="SNIVY"
        if event["battle_policy"] in ("ADVANCE_ON_LOSS","WIN_REQUIRED"):
            kw["outcome"]="WIN"
        action("record_u07",**kw)
    action("complete",chapter_key=c["chapters"][1]["key"],
           simulation_gate=machine.SIMULATION_GATE)
    action("advance",chapter_key=c["chapters"][1]["key"])
    for gym in catalog["gyms"]:
        for event in gym["events"]:
            kw={"event_key":event["id"]}
            if event["kind"]=="battle":
                kw.update(outcome="WIN",leader_key=_leader(gym,env["g01_envelope"]))
            action("record_story",**kw)
        action("complete",chapter_key=gym["chapter_key"],
               simulation_gate=machine.SIMULATION_GATE)
        action("advance",chapter_key=gym["chapter_key"])
    result=validate_envelope(env,ctx,catalog)
    encoded=codec.encode_current(env["g01_envelope"],ctx)
    if codec.decode_current(encoded,ctx)!=env["g01_envelope"]:
        deny("G01.4 projected state round-trip failed")
    if result["chapter_index"]!=10 or len(env["badge_claims"])!=8:
        deny("offline gym campaign did not reach league checkpoint")
    return {"phase":"G02.2","status":"OFFLINE_GYM_CAMPAIGN_SIMULATION_ONLY",
        "gyms":8,"events_recorded":40,"badge_claims":len(env["badge_claims"]),
        "chapter_after_gyms":env["g01_envelope"]["state"]["current_chapter"],
        "g01_4_projection_roundtrip":True,"native_badges_granted":False,
        "game_exe_tested":False,"native_save_modified":False,"can_install":False}

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check",action="store_true")
    group.add_argument("--simulate-demo",action="store_true")
    args=parser.parse_args(argv)
    try:
        ctx,catalog=load_project()
        region=machine._safe_source(ROOT/catalog["badge_registry"])
        areas=machine._safe_source(ROOT/catalog["area_catalog"])
        report=(validate_catalog(catalog,ctx,region,areas)
                if args.check else demo(ctx,catalog))
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,TypeError,KeyError,OSError,RecursionError) as exc:
        print("UNOVA_G02_2_BLOCKED: "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
