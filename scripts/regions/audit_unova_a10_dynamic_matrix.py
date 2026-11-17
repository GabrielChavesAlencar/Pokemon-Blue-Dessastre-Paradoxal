#!/usr/bin/env python3
"""A10: read-only dynamic transfer triage and candidate MapID availability matrix.

This does not execute Ruby, confirm live event gates, reserve IDs or edit game
content. A clean static scan is not a proof of future installer ownership.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import audit_unova_a04_mapids as a04
import audit_unova_a07_reference_provenance as a07
import audit_unova_a08_readiness as a08
from server.ruby_marshal import RubyObject, loads

REPORT = Path(".blue-work/unova/audit")
BLOCK = range(518,600)
MAX_EVENTS = 12000
MAX_NEAR = 12
MAX_CALLS = 400
MAX_MANIFEST_BYTES = 1024*1024
MANIFESTS = a08.REGION_PROOFS
GUARD_CODES = {111:"CONDITIONAL_BRANCH",112:"LOOP",113:"BREAK_LOOP",
               115:"EXIT_EVENT",118:"LABEL",119:"JUMP_LABEL",
               121:"SWITCH_CONTROL",122:"VARIABLE_CONTROL",
               123:"SELF_SWITCH_CONTROL",411:"ELSE_BRANCH",412:"END_BRANCH"}

def deny(reason):
    raise ValueError("UNOVA_A10_BLOCKED: "+str(reason))

def attrs(value):
    return value.attrs if isinstance(value,RubyObject) else {}

def get_int(value):
    return value if type(value) is int else None

def candidate_destinations(document):
    """Extract *observed* map mapping values, never synthesize future claims."""
    found=set()
    uncertain=[]
    def valid(v):
        if type(v) is int:return v
        if isinstance(v,str) and v.isdecimal() and len(v)<=5:return int(v)
        return None
    def explore(value,depth=0):
        if depth>10:
            uncertain.append("DEPTH_LIMIT");return
        if isinstance(value,dict):
            if len(value)>50000:
                uncertain.append("MAPPING_TOO_LARGE");return
            for k,v in value.items():
                if k in ("maps","mapping","map_ids","remap","destination_map_ids","assigned_map_ids"):
                    if isinstance(v,dict):
                        for dest in v.values():
                            n=valid(dest)
                            if n is not None:found.add(n)
                            elif isinstance(dest,(dict,list)):explore(dest,depth+1)
                            else:uncertain.append("UNRECOGNIZED_MAPPING_DESTINATION")
                    elif isinstance(v,list):
                        for dest in v:
                            n=valid(dest)
                            if n is not None:found.add(n)
                            elif isinstance(dest,(dict,list)):explore(dest,depth+1)
                    else:uncertain.append("UNRECOGNIZED_MAPPING_SHAPE")
                elif k in ("new_map_id","destination_map_id","target_map_id","native_map_id"):
                    n=valid(v)
                    if n is not None:found.add(n)
                    else:uncertain.append("UNRECOGNIZED_DESTINATION_FIELD")
                elif isinstance(v,(dict,list)):
                    explore(v,depth+1)
        elif isinstance(value,list):
            if len(value)>50000:uncertain.append("ARRAY_TOO_LARGE");return
            for item in value:
                if isinstance(item,(dict,list)):explore(item,depth+1)
    explore(document)
    return found,sorted(set(uncertain))

def read_manifests(data):
    rows=[];all_ids=set()
    for name in MANIFESTS:
        path=data/name
        if not path.exists() and not path.is_symlink():
            rows.append({"name":name,"status":"NOT_FOUND","candidate_ids":[]})
            continue
        if path.is_symlink() or not path.is_file():
            rows.append({"name":name,"status":"UNSAFE_FILE","candidate_ids":[]})
            continue
        try:
            if not 0<path.stat().st_size<=MAX_MANIFEST_BYTES:
                deny("manifest size limit")
            raw=path.read_bytes()
            obj=json.loads(raw.decode("utf-8-sig"))
            if not isinstance(obj,dict):deny("manifest is not a JSON object")
            ids,uncertain=candidate_destinations(obj)
            candidates=sorted(i for i in ids if i in BLOCK)
            all_ids.update(candidates)
            rows.append({"name":name,"status":"PARSED_SCHEMA_PARTIAL",
                         "sha256":hashlib.sha256(raw).hexdigest(),
                         "candidate_ids":candidates,
                         "numeric_destination_values":len(ids),
                         "schema_warnings":uncertain[:30]})
        except (OSError,ValueError,UnicodeError,RecursionError,TypeError) as exc:
            rows.append({"name":name,"status":"READ_ERROR","candidate_ids":[],
                         "reason":str(exc)[:120]})
    return {"files":rows,"candidate_ids":sorted(all_ids),
            "all_installer_manifests_known":False,
            "future_blue_story_claims_verified":False,
            "schema_and_future_coverage_complete":False}

def context_of_transfer(command,index,commands):
    params=attrs(command).get("@parameters",[])
    static=(isinstance(params,list) and len(params)>1 and type(params[0]) is int
            and params[0]==0 and type(params[1]) is int and params[1]>0)
    before=commands[max(0,index-MAX_NEAR):index]
    guards=[]
    for off,entry in enumerate(before):
        data=attrs(entry);code=data.get("@code")
        if code not in GUARD_CODES:continue
        guard_params=data.get("@parameters",[])
        # Preserve only control discriminator/ids; never run or reveal script.
        safe_numbers=[]
        if isinstance(guard_params,list):
            safe_numbers=[v for v in guard_params[:5] if type(v) is int]
        guards.append({"command_index":max(0,index-MAX_NEAR)+off,
                       "kind":GUARD_CODES[code],
                       "indent":get_int(data.get("@indent")),
                       "numeric_params":safe_numbers})
    return {"command_index":index,"kind":"STATIC" if static else "COMPUTED_OR_UNSUPPORTED",
            "map_id":params[1] if static else None,
            "x":get_int(params[2]) if static and len(params)>2 else None,
            "y":get_int(params[3]) if static and len(params)>3 else None,
            "command_indent":get_int(attrs(command).get("@indent")),
            "preceding_control_commands":guards,
            "control_flow_runtime_verified":False}

def inspect_intro(game,base,a09):
    maps=base.get("maps",[])
    record=next((item for item in maps if item.get("id")==1),None)
    if not record:deny("Map001 missing from A04")
    path=a04.directory_root(game)/record["source_filename"]
    raw=a07.limited_read(path,a07.MAP_LIMIT)
    if hashlib.sha256(raw).hexdigest()!=record["sha256"]:
        deny("Map001 changed since A04")
    root=loads(raw)
    if not isinstance(root,RubyObject) or root.name!="RPG::Map":deny("invalid RPG::Map")
    events=attrs(root).get("@events",{})
    if not isinstance(events,dict) or len(events)>MAX_EVENTS:deny("invalid event structure")
    rows=[];target3=[]
    for eid in (1,2):
        event=events.get(eid)
        if not isinstance(event,RubyObject):
            rows.append({"event_id":eid,"status":"MISSING","pages":[]})
            continue
        pages=attrs(event).get("@pages",[])
        if not isinstance(pages,list) or len(pages)>a07.MAX_PAGES:deny("invalid page list")
        p_reports=[]
        for pn,page in enumerate(pages,1):
            p=attrs(page);commands=p.get("@list",[])
            if not isinstance(commands,list) or len(commands)>a07.MAX_COMMANDS:
                deny("invalid command list")
            cond=attrs(p.get("@condition"))
            active={k:bool(cond.get("@"+k)) for k in ("switch1_valid","switch2_valid",
                                                     "variable_valid","self_switch_valid")}
            guards={key:get_int(cond.get("@"+key)) for key in ("switch1_id","switch2_id",
                "variable_id","variable_value") if active.get(("variable" if key.startswith("variable_")
                else key.split("_id")[0])+"_valid",False)}
            if active.get("self_switch_valid"):
                guards["self_switch_ch"]=a08.plain(cond.get("@self_switch_ch",b""),10)
            transfers=[]
            for idx,cmd in enumerate(commands):
                obj=attrs(cmd)
                if type(obj.get("@code")) is not int:deny("invalid command code")
                if obj["@code"]!=201:continue
                item=context_of_transfer(cmd,idx,commands)
                transfers.append(item)
                if item["map_id"]==3:target3.append((eid,pn,idx))
            p_reports.append({"page_index":pn,
                "trigger_code":get_int(p.get("@trigger")),
                "condition_flags":active,
                "active_condition_inputs":guards,
                "page_is_active_at_runtime":"UNKNOWN",
                "page_priority_checked_at_runtime":False,
                "transfer_commands":transfers[:300],
                "transfer_commands_truncated":len(transfers)>300,
                "script_event_commands":sum(1 for c in commands if attrs(c).get("@code") in (355,655))})
        rows.append({"event_id":eid,"status":"EXAMINED_INERT","page_count":len(pages),"pages":p_reports})
    intro=a09.get("intro_event_evidence",{})
    expected=intro.get("static_transfer_to_mapid3_count")
    matches=expected==len(target3) and intro.get("mapid3_origin_matches_a07") is True
    return {"events":rows,"mapid3_transfer_positions":[{"event_id":e,"page":p,"command_index":i}
                  for e,p,i in target3],
            "matches_a09_count":matches,
            "runtime_conditions_verified":False,
            "original_destination_3_intent_verified":False}

def dynamic_calls(a09):
    triage=a09.get("script_transfer_triage",{})
    calls=triage.get("api_findings",[])
    if not isinstance(calls,list):deny("invalid A09 script evidence")
    grouped=Counter(x.get("classification","UNKNOWN") for x in calls if isinstance(x,dict))
    unresolved=[]
    for item in calls[:MAX_CALLS]:
        if not isinstance(item,dict):continue
        if item.get("classification") not in ("SYMBOLIC_OR_COMPUTED","INCOMPLETE_OR_UNCERTAIN"):
            continue
        unresolved.append({"source_type":item.get("source_type"),
            "event_id":item.get("event_id"),"page_index":item.get("page_index"),
            "command_index":item.get("command_index"),"script_entry":item.get("script_entry"),
            "line_number":item.get("line_number"),"api":item.get("api"),
            "classification":item.get("classification"),"resolved_at_runtime":False})
    return {"classification_counts":dict(grouped),
            "reported_computed_count":int(triage.get("classification_counts",{}).get("SYMBOLIC_OR_COMPUTED",0)),
            "unresolved_provenance":unresolved,
            "unresolved_provenance_truncated":len(calls)>MAX_CALLS,
            "script_scan_errors":triage.get("scan_error_count"),
            "scan_scope":triage.get("scope"),
            "dynamic_targets_verified":False,
            "script_call_sites_executed":False}

def audit(game:Path,project:Path,a04_report:dict,a06_report:dict,
          a07_report:dict,a08_report:dict,a09_report:dict)->dict:
    game=a04.safe_path(game);project=a04.safe_path(project)
    base=a04_report.get("sources",{}).get("DECADES",{})
    digest=base.get("mapinfos_sha256")
    chain=(a04_report.get("phase")=="A04" and a06_report.get("phase")=="A06"
           and a07_report.get("phase")=="A07" and a08_report.get("phase")=="A08"
           and a09_report.get("phase")=="A09"
           and digest and all(x.get("mapinfos_sha256")==digest for x in
                    (a06_report,a07_report,a08_report,a09_report))
           and a07_report.get("review_errors_count")==0
           and not a06_report.get("map_read_failures")
           and a09_report.get("status")=="REVIEW_REQUIRED_NO_RESERVATION")
    if not chain:deny("A04-A09 audit chain incomplete/inconsistent")
    data=a04.directory_root(game)
    occupied=set(a04_report.get("observed_or_declared_occupied_map_ids",[]))
    intro=inspect_intro(game,base,a09_report)
    scripts=dynamic_calls(a09_report)
    manifest=read_manifests(data)
    references=set(a06_report.get("static_destination_mapids",[]))
    reference_candidates=references.intersection(BLOCK)
    rows=[]
    counts=Counter()
    claims=set(manifest["candidate_ids"])
    for mid in BLOCK:
        in_current=mid in occupied
        in_manifest=mid in claims
        in_static=mid in reference_candidates
        if in_current: status="OCCUPIED_IN_CURRENT_SNAPSHOT"
        elif in_manifest:status="INSTALLER_MANIFEST_CLAIM_REVIEW"
        elif in_static:status="STATIC_REFERENCE_REVIEW"
        else:status="OBSERVED_VACANT_NOT_RESERVED"
        counts[status]+=1
        rows.append({"map_id":mid,"status":status,
            "physically_or_declared_occupied":in_current,
            "manifest_claim_observed":in_manifest,
            "static_transfer_reference_observed":in_static,
            "future_claims_verified":False,"approved_for_reservation":False})
    problems=[]
    if not intro["matches_a09_count"]:problems.append("A09_INTRO_TRANSFER_MISMATCH")
    if intro["mapid3_transfer_positions"] and 3 not in occupied:
        problems.append("MAPID3_MISSING_INTRO_DESTINATION")
    if scripts["reported_computed_count"]:problems.append("COMPUTED_CALL_TARGETS_NOT_RESOLVED")
    if scripts["script_scan_errors"]:problems.append("PARTIAL_SCRIPT_SCAN")
    if claims.intersection(BLOCK):problems.append("LOCAL_MANIFEST_CANDIDATE_CLAIMS")
    if occupied.intersection(BLOCK):problems.append("CANDIDATE_BLOCK_OCCUPIED")
    if reference_candidates:problems.append("STATIC_CANDIDATE_REFERENCES")
    problems.append("FUTURE_BLUE_STORY_CLAIMS_NOT_VERIFIED")
    problems.append("INTRO_RUNTIME_BEHAVIOR_NOT_VERIFIED")
    return {"schema":1,"phase":"A10","region":"UNOVA",
        "mode":"READ_ONLY_DYNAMIC_DESTINATION_AND_MAPID_MATRIX",
        "status":"DIAGNOSTIC_COMPLETE_RESERVATION_BLOCKED",
        "mapinfos_sha256":digest,
        "intro_transfer_analysis":intro,
        "dynamic_script_references":scripts,
        "installer_manifest_analysis":manifest,
        "mapid_matrix":rows,"matrix_status_counts":dict(counts),
        "mapids_reviewed":len(rows),
        "candidate_range":[518,599],
        "observed_snapshot_no_candidate_occupancy":not bool(occupied.intersection(BLOCK)),
        "unresolved_review_flags":sorted(set(problems)),
        "source_maps_from_unova_verified":False,
        "game_exe_intro_verified":False,"future_installer_ownership_verified":False,
        "mapid3_destination_repaired":False,"reserve_plan_only":True,
        "can_reserve_mapids":False,"can_install":False,"mapids_allocated":False,
        "game_exe_tested":False,"android_tested":False,
        "game_or_saves_modified":False,"bar_a_completed":0,"bar_a_total":8}

def save(project:Path,report:dict)->Path:
    project=a04.safe_path(project)
    for p in (project/".blue-work",project/".blue-work/unova",project/REPORT):
        if p.is_symlink() or (p.exists() and not p.is_dir()):
            deny("unsafe report directory")
        p.mkdir(exist_ok=True)
    content=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
    path=project/REPORT/("a10-dynamic-matrix-"+hashlib.sha256(content).hexdigest()[:16]+".json")
    if path.is_symlink():deny("symlink report")
    if path.exists():
        if path.read_bytes()!=content:deny("report hash conflict")
    else:
        with path.open("xb") as output:output.write(content)
    return path
