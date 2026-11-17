#!/usr/bin/env python3
"""Unova G01.2: pure offline chapter state machine based on G01.1.

No game save adapter; progression signals and completion markers are synthetic.
G01.3 remains responsible for reward idempotency/reentry; G01.4 for migrations.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
from typing import Any

import audit_unova_g01_state_schema as g01

ROOT=Path(__file__).resolve().parents[2]
RULES=ROOT/"data/regions/unova-g01-chapter-transitions.json"
STATES=("not_started","active","completed","blocked")
SIMULATION_GATE="SIMULATED_ONLY_NO_NATIVE_APPROVAL"
STARTERS=("SNIVY","TEPIG","OSHAWOTT")
ALLOWED_ACTIONS=("begin","record_u07","complete","advance")

def deny(reason:str)->None:
    raise ValueError("UNOVA_G01_2_BLOCKED: "+reason)

def _keys(row:Any,expected:set[str],label:str)->None:
    if not isinstance(row,dict) or set(row)!=expected:
        deny(label+" invalid fields")

def _safe_source(path:Path)->dict:
    path=Path(path)
    if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<300_000:
        deny("invalid reference source: "+str(path))
    try:
        return g01.load_json(path)
    except (OSError,ValueError,UnicodeError) as exc:
        deny("invalid JSON source: "+str(exc))

def load_project(root:Path=ROOT)->tuple[dict,dict]:
    """Read only repository metadata. Never consult the user's game directory."""
    root=Path(root)
    contract=_safe_source(root/"data/regions/unova-g01-state-contract.json")
    schema=_safe_source(root/"data/regions/unova-g01-state.schema.json")
    areas=_safe_source(root/"data/regions/unova-u03-areas.json")
    events=_safe_source(root/"data/regions/unova-u07-nuvema-events.json")
    regions=_safe_source(root/"site/public/data/regions.json")
    rules=_safe_source(root/"data/regions/unova-g01-chapter-transitions.json")
    g01.validate_contract(contract,schema,areas,events,regions)
    validate_rules(rules,contract,events)
    return contract,rules

def validate_rules(rules:dict,contract:dict,events:dict)->dict:
    _keys(rules,{"schema","region","campaign","phase","status","g01_contract",
        "g01_state_schema_version","engine_scope","simulation_gate",
        "native_save_adapter","auto_install","game_exe_tested",
        "source_u07_events","u07_order","transitions","completion","notes"},"rules")
    expected={"schema":1,"region":"UNOVA","campaign":"WHITE_BW","phase":"G01.2",
              "status":"OFFLINE_SYNTHETIC_TRANSITIONS_ONLY",
              "g01_contract":"data/regions/unova-g01-state-contract.json",
              "g01_state_schema_version":1,"engine_scope":"GITHUB_TESTS_ONLY",
              "simulation_gate":SIMULATION_GATE,"native_save_adapter":False,
              "auto_install":False,"game_exe_tested":False,
              "source_u07_events":"data/regions/unova-u07-nuvema-events.json"}
    for name,val in expected.items():
        if type(rules.get(name)) is not type(val) or rules[name]!=val:
            deny("rules identity/native approval changed: "+name)
    if (contract.get("contract_version")!=1 or
        contract.get("compatibility",{}).get("current_state_schema_version")!=1 or
        contract.get("compatibility",{}).get("native_save_adapter")!="NOT_IMPLEMENTED"):
        deny("G01.1 version or native adapter changed")
    expected_events=[{key:r[key] for key in ("key","requires","battle_policy","kind")}
                     for r in events["events"]]
    if rules["u07_order"]!=expected_events or len(expected_events)!=13:
        deny("U07 event order, prerequisites or battle policy conflict")
    chapters=contract["chapters"]
    missions=contract["missions"]
    expected_gates=[{
        "id":"UNOVA_G01_BEGIN_CH01","action":"begin","from":chapters[0]["key"],
        "to":chapters[1]["key"],"required_mission_key":None,
        "required_completion_flag":None,"required_u07_flags":[]
    }]
    for index in range(2,len(chapters)):
        expected_gates.append({
            "id":"UNOVA_G01_ADVANCE_CH"+str(index).zfill(2),
            "action":"advance","from":chapters[index-1]["key"],
            "to":chapters[index]["key"],
            "required_mission_key":missions[index-2]["key"],
            "required_completion_flag":"UNOVA_FLAG_CH"+str(index-1).zfill(2)+"_COMPLETED",
            "required_u07_flags":[x["key"] for x in expected_events] if index==2 else [],
        })
    if rules["transitions"]!=expected_gates or len(expected_gates)!=12:
        deny("chapter transitions must be consecutive and source-grounded")
    if rules["completion"]!={"chapter_01_requires_all_u07_events":True,
        "chapter_02_to_12_require_explicit_simulated_gate":True,
        "completion_markers_are_test_only":True,
        "real_gym_or_story_evidence_verified":False,
        "rewards_issued":False}:
        deny("completion policy must remain offline")
    if not isinstance(rules["notes"],list) or len(rules["notes"])<2:
        deny("rules documentation missing")
    return {"chapters":len(chapters),"transitions":len(expected_gates),
            "u07_events":len(expected_events),"game_exe_tested":False,
            "can_install":False,"native_save_compatible":False}

def completion_flag(index:int)->str:
    return "UNOVA_FLAG_CH"+str(index).zfill(2)+"_COMPLETED"

def _chapter_index(state:dict,contract:dict)->int:
    keys=[r["key"] for r in contract["chapters"]]
    try:
        return keys.index(state["current_chapter"])
    except (ValueError,KeyError) as exc:
        deny("unknown current chapter: "+str(exc))

def validate_progression(state:dict,contract:dict,rules:dict)->dict:
    """Validate reachable snapshot invariants, not just its JSON data shape."""
    areas={"areas":[{"key":r["reference_area_key"]} for r in contract["chapters"]
                    if r["reference_area_key"] is not None]}
    # Validate full G01.1 semantics with source catalog: G01.1 constraints
    # require 74 area keys; read them from the repository source fixture.
    areas=_safe_source(ROOT/"data/regions/unova-u03-areas.json")
    g01.validate_state(state,contract,areas)
    idx=_chapter_index(state,contract)
    missions=contract["missions"]
    flags=state["flags"]
    history=set(x["key"] for x in rules["u07_order"])
    all_chflags={completion_flag(i) for i in range(1,13)}
    if any(value is not True for value in flags.values()):
        deny("machine state cannot store false placeholder flags")
    if idx==0:
        if flags or state["missions"] or state["checkpoint"]["last_story_area_key"] is not None:
            deny("unstarted state must have no progress")
        return {"chapter_index":0,"finished":False,"offline":True}
    for past in range(1,idx):
        if state["missions"].get(missions[past-1]["key"])!="completed" or (
            flags.get(completion_flag(past)) is not True):
            deny("earlier chapter must be completed before current chapter")
    current=missions[idx-1]["key"]
    current_status=state["missions"].get(current)
    if current_status not in {"active","completed"}:
        deny("current mission must be active or completed")
    for later in range(idx+1,13):
        if missions[later-1]["key"] in state["missions"] or (
            completion_flag(later) in flags):
            deny("future chapter/mission was pre-unlocked")
    if (flags.get(completion_flag(idx)) is True)!=(current_status=="completed"):
        deny("current completion flag and mission must agree")
    if state["checkpoint"]["last_story_area_key"]!=contract["chapters"][idx]["reference_area_key"]:
        deny("chapter checkpoint cannot skip to another story area")
    recorded=[x["key"] for x in rules["u07_order"] if flags.get(x["key"]) is True]
    all_u07=[x["key"] for x in rules["u07_order"]]
    if recorded!=all_u07[:len(recorded)] or any(
            f in history and f not in recorded for f in flags):
        deny("U07 progress must be a monotonic prefix")
    if idx>1 and recorded!=all_u07:
        deny("U07 opening must be complete to leave chapter 01")
    if idx==1 and current_status=="completed" and recorded!=all_u07:
        deny("cannot complete chapter 01 without all 13 opening events")
    for chapter in range(idx+1,13):
        if completion_flag(chapter) in flags:
            deny("future completion flag not permitted")
    if any(flag in all_chflags and flag not in {
            completion_flag(k) for k in range(1,idx+1)} for flag in flags):
        deny("out-of-order completion flag")
    return {"chapter_index":idx,"finished":idx==12 and current_status=="completed",
            "offline":True,"current_mission":current,"current_mission_status":current_status}

def available(state:dict,contract:dict,rules:dict)->list[dict]:
    info=validate_progression(state,contract,rules)
    index=info["chapter_index"]
    if index==0:
        return [{"action":"begin","target":contract["chapters"][1]["key"]}]
    status=info["current_mission_status"]
    if status=="completed":
        return ([{"action":"advance","target":contract["chapters"][index+1]["key"]}]
                if index<12 else [])
    if index==1:
        nxt=next((e for e in rules["u07_order"]
                  if state["flags"].get(e["key"]) is not True),None)
        if nxt:
            return [{"action":"record_u07","event":nxt["key"],
                     "requires":list(nxt["requires"])}]
    return [{"action":"complete","chapter":contract["chapters"][index]["key"],
             "synthetic_gate":SIMULATION_GATE}]

def step(state:dict,contract:dict,rules:dict,action:str, *,
         event_key:str|None=None,outcome:str|None=None,
         starter_choice:str|None=None,simulation_gate:str|None=None)->dict:
    """Pure and transactional: never mutates caller state on error."""
    validate_progression(state,contract,rules)
    if action not in ALLOWED_ACTIONS:deny("unsupported operation")
    new=copy.deepcopy(state)
    idx=_chapter_index(new,contract)
    chapters=contract["chapters"]
    missions=contract["missions"]
    if action!="record_u07" and (event_key is not None or outcome is not None
                                  or starter_choice is not None):
        deny("unexpected event arguments")
    if action!="complete" and simulation_gate is not None:
        deny("unexpected simulation gate")
    if action=="begin":
        if idx!=0:deny("journey already started")
        new["current_chapter"]=chapters[1]["key"]
        new["missions"][missions[0]["key"]]="active"
        new["checkpoint"]["last_story_area_key"]=chapters[1]["reference_area_key"]
    elif action=="record_u07":
        if idx!=1 or new["missions"].get(missions[0]["key"])!="active":
            deny("U07 events only in active opening chapter")
        next_event=next((x for x in rules["u07_order"]
                         if new["flags"].get(x["key"]) is not True),None)
        if next_event is None or event_key!=next_event["key"]:
            deny("out-of-order or duplicate opening event")
        if any(new["flags"].get(pre) is not True for pre in next_event["requires"]):
            deny("missing U07 event prerequisite")
        kind=next_event["kind"]
        policy=next_event["battle_policy"]
        if kind=="choice":
            if starter_choice not in STARTERS or outcome is not None:
                deny("starter choice must be one of the three Unova starters")
        elif policy in ("ADVANCE_ON_LOSS","WIN_REQUIRED"):
            if starter_choice is not None or outcome not in ("WIN","LOSS"):
                deny("explicit simulated battle outcome required")
            if policy=="WIN_REQUIRED" and outcome!="WIN":
                deny("the N battle requires a synthetic win")
        elif outcome is not None or starter_choice is not None:
            deny("nonbattle event cannot have starter/outcome")
        new["flags"][event_key]=True
    elif action=="complete":
        if idx==0:deny("no active chapter")
        if new["missions"][missions[idx-1]["key"]]!="active":
            deny("mission cannot be completed twice")
        if simulation_gate!=SIMULATION_GATE:
            deny("explicit synthetic-only completion required")
        if idx==1 and any(new["flags"].get(event["key"]) is not True
                          for event in rules["u07_order"]):
            deny("all 13 U07 events required for first chapter")
        new["missions"][missions[idx-1]["key"]]="completed"
        new["flags"][completion_flag(idx)]=True
    elif action=="advance":
        if idx==0 or idx>=12:deny("no next chapter")
        gate=rules["transitions"][idx]
        if (gate["from"]!=chapters[idx]["key"] or
            gate["to"]!=chapters[idx+1]["key"] or
            new["missions"].get(gate["required_mission_key"])!="completed" or
            new["flags"].get(gate["required_completion_flag"]) is not True or
            any(new["flags"].get(flag) is not True
                for flag in gate["required_u07_flags"])):
            deny("chapter transition missing prerequisites")
        new["current_chapter"]=gate["to"]
        new["missions"][missions[idx]["key"]]="active"
        new["checkpoint"]["last_story_area_key"]=chapters[idx+1]["reference_area_key"]
    validate_progression(new,contract,rules)
    return {"state":new,"chapter":new["current_chapter"],"available":available(new,contract,rules),
            "status":"OFFLINE_SYNTHETIC_ONLY","reward_granted":False,
            "native_save_modified":False,"game_exe_tested":False,"can_install":False}

def demo(contract:dict,rules:dict)->dict:
    state=g01.empty_state(contract)
    steps=[]
    def call(action,**kw):
        nonlocal state
        result=step(state,contract,rules,action,**kw)
        state=result["state"]
        steps.append({"action":action,"chapter":result["chapter"],
                      "synthetic":True,"reward_granted":False})
    call("begin")
    for event in rules["u07_order"]:
        kwargs={"event_key":event["key"]}
        if event["kind"]=="choice":kwargs["starter_choice"]="SNIVY"
        if event["battle_policy"] in ("ADVANCE_ON_LOSS","WIN_REQUIRED"):
            kwargs["outcome"]="WIN"
        call("record_u07",**kwargs)
    for index in range(1,13):
        call("complete",simulation_gate=SIMULATION_GATE)
        if index<12:call("advance")
    return {"phase":"G01.2","status":"OFFLINE_DEMO_ONLY",
            "chapters_visited":13,"events_recorded":13,
            "steps":len(steps),"final_chapter":state["current_chapter"],
            "final_state":state,"game_exe_tested":False,
            "native_save_modified":False,"rewards_granted":False,
            "can_install":False}

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    actions=parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check",action="store_true")
    actions.add_argument("--simulate-demo",action="store_true")
    args=parser.parse_args(argv)
    try:
        contract,rules=load_project()
        if args.check:
            report=validate_rules(rules,contract,_safe_source(ROOT/rules["source_u07_events"]))
            report.update({"phase":"G01.2","status":"OFFLINE_RULES_VALIDATED_NOT_INSTALLED"})
        else:
            report=demo(contract,rules)
            report.pop("final_state")  # No snapshots or saves are written.
        print(json.dumps(report,sort_keys=True,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,RecursionError) as exc:
        print("UNOVA_G01_2_BLOCKED: "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
