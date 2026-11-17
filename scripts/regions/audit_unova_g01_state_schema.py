#!/usr/bin/env python3
"""Unova G01.1 offline-only state contract, never a native save adapter.

Only validate exact structural shape and source-catalog consistency.
Do not load Ruby, import game code, transition story chapters or write saves.
G01.2 implements progression; G01.4 implements explicit synthetic migration.
"""
from __future__ import annotations
import argparse
import copy
import json
from pathlib import Path
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"data/regions/unova-g01-state-contract.json"
SCHEMA=ROOT/"data/regions/unova-g01-state.schema.json"
AREAS=ROOT/"data/regions/unova-u03-areas.json"
EVENTS=ROOT/"data/regions/unova-u07-nuvema-events.json"
REGIONS=ROOT/"site/public/data/regions.json"

def deny(message:str)->None:
    raise ValueError("UNOVA_G01_1_BLOCKED: "+message)

def load_json(path:Path)->dict:
    # Files are repository-owned reference JSON only, never a user game save.
    with path.open("r",encoding="utf-8") as stream:
        value=json.load(stream)
    if not isinstance(value,dict):
        deny("expected object: "+path.name)
    return value

def _exact_keys(obj:Any,expected:set[str],label:str)->None:
    if not isinstance(obj,dict) or set(obj)!=expected:
        deny(label+" unexpected or missing fields")

def _enum_string(obj:Any,pool:set[str],label:str)->None:
    if not isinstance(obj,str) or obj not in pool:
        deny(label+" must be a known identifier")

def validate_contract(contract:dict,schema:dict,areas:dict,events:dict,regions:dict)->dict:
    _exact_keys(contract,{
        "contract_version","region","campaign","phase","status",
        "source_area_catalog","source_event_catalog","source_regions_registry",
        "state_schema_file","compatibility","default_state","allowed_mission_statuses",
        "absent_flag_means","absent_mission_means","chapters","missions",
        "flag_catalog","native_game_files_modified","source_assets_imported",
        "game_exe_tested","android_tested","can_install","notes"
    },"G01.1 contract")
    if (type(contract["contract_version"]) is not int or contract["contract_version"]!=1
        or contract["region"]!="UNOVA" or contract["campaign"]!="WHITE_BW"
        or contract["phase"]!="G01.1" or
        contract["status"]!="VERSIONED_SCHEMA_ONLY_NOT_NATIVE_SAVE"):
        deny("contract identity/version mismatch")
    for key,path in (("source_area_catalog","data/regions/unova-u03-areas.json"),
                     ("source_event_catalog","data/regions/unova-u07-nuvema-events.json"),
                     ("source_regions_registry","site/public/data/regions.json"),
                     ("state_schema_file","data/regions/unova-g01-state.schema.json")):
        if contract[key]!=path:deny("unexpected source path "+key)
    for name in ("native_game_files_modified","source_assets_imported",
                 "game_exe_tested","android_tested","can_install"):
        if contract[name] is not False:deny("native status falsely promoted: "+name)
    policy=contract["compatibility"]
    _exact_keys(policy,{
        "current_state_schema_version","accepted_versions","future_versions","older_versions",
        "unknown_fields","implicit_migration","native_save_adapter",
        "state_transitions","persistence_format"
    },"compatibility")
    if (type(policy["current_state_schema_version"]) is not int or
        policy["current_state_schema_version"]!=1 or
        policy["accepted_versions"]!=[1] or
        policy["future_versions"]!="REJECT_FAIL_CLOSED" or
        policy["older_versions"]!="REJECT_UNTIL_G01_4_EXPLICIT_MIGRATOR" or
        policy["unknown_fields"]!="REJECT" or
        policy["implicit_migration"] is not False or
        policy["native_save_adapter"]!="NOT_IMPLEMENTED" or
        policy["state_transitions"]!="NOT_IMPLEMENTED_G01_2" or
        policy["persistence_format"]!="SIMULATED_ONLY_NOT_GAME_SAVE"):
        deny("unsupported/unsafe state compatibility policy")
    if (areas.get("region")!="UNOVA" or areas.get("state")!="PLANNED_REFERENCE_ONLY"
        or areas.get("may_install") is not False or
        not isinstance(areas.get("areas"),list) or len(areas["areas"])!=74):
        deny("U03 areas no longer reference-only")
    area_keys=[row.get("key") for row in areas["areas"] if isinstance(row,dict)]
    if len(area_keys)!=74 or len(set(area_keys))!=74:
        deny("U03 area IDs are not unique")
    if (events.get("region")!="UNOVA" or
        events.get("phase")!="U07_CONTRACTS" or
        events.get("can_install") is not False or
        not isinstance(events.get("events"),list) or len(events["events"])!=13):
        deny("U07 event source not coherent")
    event_keys=[row.get("key") for row in events["events"] if isinstance(row,dict)]
    if len(event_keys)!=13 or len(set(event_keys))!=13:
        deny("U07 event IDs not unique")
    if (regions.get("regions",{}).get("UNOVA",{}).get("status")!="planned" or
        regions["regions"]["UNOVA"].get("milestones")!=[
            "TRIO","BASIC","INSECT","BOLT","QUAKE","JET","FREEZE","LEGEND"]):
        deny("Unova region registry is not planned")
    chapters=contract["chapters"]
    if not isinstance(chapters,list) or len(chapters)!=13:
        deny("expected 13 planned chapter references")
    chapter_keys=[]
    for idx,row in enumerate(chapters):
        _exact_keys(row,{"key","index","title","reference_area_key",
                          "planned_phase","arc","map_id","game_exe_verified"},"chapter")
        key=row["key"]
        if (not isinstance(key,str) or not key.startswith(
                "UNOVA_CH"+str(idx).zfill(2)+"_") or
            type(row["index"]) is not int or row["index"]!=idx or
            not isinstance(row["title"],str) or not row["title"].strip() or
            not isinstance(row["planned_phase"],str) or
            not row["planned_phase"].startswith("U") or
            row["arc"] not in {"prestart","campaign","postgame"} or
            row["map_id"] is not None or row["game_exe_verified"] is not False or
            (idx==0 and (row["reference_area_key"] is not None or
                         row["arc"]!="prestart")) or
            (idx>0 and row["reference_area_key"] not in area_keys) or
            (idx==12 and row["arc"]!="postgame") or
            (0<idx<12 and row["arc"]!="campaign")):
            deny("invalid planned chapter identity or source "+str(idx))
        chapter_keys.append(key)
    if len(set(chapter_keys))!=len(chapter_keys):
        deny("duplicate chapter key")
    missions=contract["missions"]
    if not isinstance(missions,list) or len(missions)!=12:
        deny("expected 12 planned main/postgame missions")
    mission_keys=[]
    for idx,row in enumerate(missions,1):
        _exact_keys(row,{"key","chapter_key","reference_area_key",
                          "kind","planned_only","real_event_id"},"mission")
        if (not isinstance(row["key"],str) or not row["key"].startswith(
                "UNOVA_MISSION_CH"+str(idx).zfill(2)+"_") or
            row["chapter_key"]!=chapter_keys[idx] or
            row["reference_area_key"]!=chapters[idx]["reference_area_key"] or
            row["kind"]!=("postgame" if idx==12 else "main") or
            row["planned_only"] is not True or row["real_event_id"] is not None):
            deny("planned mission invalid "+str(idx))
        mission_keys.append(row["key"])
    if len(set(mission_keys))!=12:deny("duplicate mission key")
    flags=contract["flag_catalog"]
    if not isinstance(flags,list) or len(flags)!=25:deny("expected 25 symbolic flags")
    flag_keys=[]
    for idx,row in enumerate(flags):
        if idx<13:
            _exact_keys(row,{"key","kind","source_event_key","native_switch_id"},"event flag")
            if row["key"]!=event_keys[idx] or row["source_event_key"]!=event_keys[idx] or row["kind"]!="EVENT_COMPLETED":
                deny("event flag not linked to U07")
        else:
            _exact_keys(row,{"key","kind","chapter_key","native_switch_id"},"chapter flag")
            ch=chapters[idx-12]
            if (row["key"]!="UNOVA_FLAG_CH"+str(ch["index"]).zfill(2)+"_COMPLETED"
                or row["chapter_key"]!=ch["key"] or
                row["kind"]!="CHAPTER_COMPLETED"):
                deny("chapter flag incompatible")
        if row["native_switch_id"] is not None:deny("native switch falsely bound")
        flag_keys.append(row["key"])
    if len(set(flag_keys))!=25:deny("duplicate flag keys")
    if (contract["allowed_mission_statuses"]!=[
          "not_started","active","completed","blocked"] or
        contract["absent_flag_means"] is not False or
        contract["absent_mission_means"]!="not_started"):
        deny("missing-key policy mismatch")
    if (schema.get("$schema")!="https://json-schema.org/draft/2020-12/schema"
        or schema.get("type")!="object" or
        schema.get("additionalProperties") is not False):
        deny("JSON Schema draft/strictness mismatch")
    props=schema.get("properties",{})
    state_keys={"schema_version","region","campaign","state_status",
                "current_chapter","flags","missions","checkpoint"}
    if set(props)!=state_keys or set(schema.get("required",[]))!=state_keys:
        deny("JSON Schema required fields drifted")
    for field,expected in (("schema_version",1),("region","UNOVA"),
                           ("campaign","WHITE_BW"),
                           ("state_status","SIMULATED_ONLY_NOT_GAME_SAVE")):
        if props[field].get("const")!=expected:deny("state schema const mismatch")
    if props["current_chapter"].get("enum")!=chapter_keys:
        deny("JSON Schema chapter enum inconsistent")
    for name,keys in (("flags",flag_keys),("missions",mission_keys)):
        section=props[name]
        if section.get("additionalProperties") is not False or (
            set(section.get("properties",{}))!=set(keys)):
            deny("JSON Schema "+name+" is not closed")
        for val in section["properties"].values():
            if (name=="flags" and val.get("type")!="boolean") or (
                name=="missions" and val.get("enum")!=contract["allowed_mission_statuses"]):
                deny("JSON Schema "+name+" value types drifted")
    chk=props["checkpoint"]
    cp_keys={"last_story_area_key","last_heal_center_area_key",
             "last_safe_area_key","map_id","x","y","verified_in_game"}
    if (set(chk.get("required",[]))!=cp_keys or
        set(chk.get("properties",{}))!=cp_keys or
        chk.get("additionalProperties") is not False):
        deny("JSON Schema checkpoint not closed")
    for field in ("last_story_area_key","last_heal_center_area_key","last_safe_area_key"):
        variants=chk["properties"][field].get("anyOf")
        if not isinstance(variants,list) or variants!=[
            {"type":"null"},{"type":"string","enum":area_keys}]:
            deny("JSON Schema checkpoint area mismatch")
    for field in ("map_id","x","y"):
        if chk["properties"][field]!={"type":"null"}:
            deny("JSON Schema invents native coordinate")
    if chk["properties"]["verified_in_game"].get("const") is not False:
        deny("JSON Schema falsely approves native checkpoint")
    initial=contract["default_state"]
    if (not isinstance(initial,dict) or
        initial.get("current_chapter")!=chapter_keys[0] or
        initial.get("flags")!={} or initial.get("missions")!={} or
        initial.get("checkpoint")!={
            "last_story_area_key":None,"last_heal_center_area_key":None,
            "last_safe_area_key":None,"map_id":None,"x":None,"y":None,
            "verified_in_game":False}):
        deny("default state must begin empty, without native map data")
    validate_state(initial,contract,areas)
    return {"phase":"G01.1","state_schema_version":1,"chapters":len(chapter_keys),
            "missions":len(mission_keys),"flags":len(flag_keys),
            "source_areas":len(area_keys),"source_u07_events":len(event_keys),
            "status":"VERSIONED_SCHEMA_VALIDATED_OFFLINE_ONLY",
            "can_install":False,"game_exe_tested":False,"android_tested":False}

def validate_state(state:dict,contract:dict,areas:dict)->dict:
    """Version-1 strict structural validation; NO event transition authorization."""
    expected={"schema_version","region","campaign","state_status",
              "current_chapter","flags","missions","checkpoint"}
    _exact_keys(state,expected,"state")
    if type(state["schema_version"]) is not int or (
        state["schema_version"]!=contract["compatibility"]["current_state_schema_version"]):
        deny("unknown or future/older schema version; migration is G01.4")
    if (state["region"]!="UNOVA" or state["campaign"]!="WHITE_BW" or
        state["state_status"]!="SIMULATED_ONLY_NOT_GAME_SAVE"):
        deny("cross-region or native save identity rejected")
    chapter_keys={row["key"] for row in contract["chapters"]}
    _enum_string(state["current_chapter"],chapter_keys,"chapter")
    if not isinstance(state["flags"],dict):
        deny("flags must be object")
    flag_keys={row["key"] for row in contract["flag_catalog"]}
    for key,value in state["flags"].items():
        _enum_string(key,flag_keys,"flag")
        if type(value) is not bool:deny("flag must be strict boolean")
    if not isinstance(state["missions"],dict):
        deny("missions must be object")
    mission_keys={row["key"] for row in contract["missions"]}
    mission_statuses=set(contract["allowed_mission_statuses"])
    for key,value in state["missions"].items():
        _enum_string(key,mission_keys,"mission")
        _enum_string(value,mission_statuses,"mission status")
    cp=state["checkpoint"]
    _exact_keys(cp,{"last_story_area_key","last_heal_center_area_key",
                    "last_safe_area_key","map_id","x","y",
                    "verified_in_game"},"checkpoint")
    valid_areas={row["key"] for row in areas["areas"]}
    for key in ("last_story_area_key","last_heal_center_area_key","last_safe_area_key"):
        if cp[key] is not None:
            _enum_string(cp[key],valid_areas,key)
    if any(cp[k] is not None for k in ("map_id","x","y")) or (
        cp["verified_in_game"] is not False):
        deny("G01.1 checkpoint cannot include MapID/position/native proof")
    return {"state_schema_version":1,"structurally_valid":True,
            "transitions_verified":False,"native_save_compatible":False,
            "flags_set":len(state["flags"]),"missions_recorded":len(state["missions"])}

def empty_state(contract:dict)->dict:
    return copy.deepcopy(contract["default_state"])

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true",help="validate repository contract only")
    args=parser.parse_args(argv)
    if not args.check:parser.error("use --check (no files are written)")
    try:
        contract=load_json(CONTRACT)
        report=validate_contract(contract,load_json(SCHEMA),load_json(AREAS),
                                 load_json(EVENTS),load_json(REGIONS))
        print(json.dumps(report,sort_keys=True,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,RecursionError) as exc:
        print("UNOVA_G01_1_BLOCKED: "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
