#!/usr/bin/env python3
"""Unova A11: read-only intro-route preflight and non-operative reservation plan.

Uses A04..A10 from one installed baseline. Does NOT evaluate event switches,
execute Ruby, assign MapIDs, create native backups, or edit any game files.
"""
from __future__ import annotations

import hashlib
import json
import re
import zlib
from collections import Counter
from pathlib import Path

import audit_unova_a04_mapids as a04
import audit_unova_a07_reference_provenance as a07
import audit_unova_a09_intro_and_claims as a09
import audit_unova_a10_dynamic_matrix as a10
from server.ruby_marshal import RubyObject, loads

OUT=Path(".blue-work/unova/audit")
MAX_FINDINGS=600
MAX_ENTRIES=3000
KNOWN_STATUSES=(
    "OBSERVED_VACANT_NOT_RESERVED","OCCUPIED_IN_CURRENT_SNAPSHOT",
    "INSTALLER_MANIFEST_CLAIM_REVIEW","STATIC_REFERENCE_REVIEW"
)

def deny(reason):
    raise ValueError("UNOVA_A11_BLOCKED: "+str(reason))

def props(value):
    return value.attrs if isinstance(value,RubyObject) else {}

def is_int(v):
    return type(v) is int

def classify_arg(value):
    """Heuristic shape only; returns neither raw Ruby text nor resolved values."""
    v=value.strip()
    if not v:return "EMPTY_OR_UNCERTAIN"
    if re.fullmatch(r"[0-9]{1,6}",v):return "NUMERIC_LITERAL"
    if re.fullmatch(r"[$@]{0,2}[A-Za-z_]\w*",v):return "VARIABLE_OR_SYMBOL"
    if re.match(r"[$@]?[A-Za-z_]\w*\s*\[",v):return "INDEXED_VARIABLE"
    if re.search(r"\w+\s*\(",v):return "CALL_OR_EXPRESSION"
    if re.search(r"[-+*/%?:]|\bif\b|\bcase\b",v):return "COMPUTED_EXPRESSION"
    return "UNCLASSIFIED_EXPRESSION"

def extract_shape_records(value,source,output,stats):
    if not isinstance(value,(bytes,str)):
        stats["unsupported_sections"]+=1;return
    blob=value.decode("utf-8","replace") if isinstance(value,bytes) else value
    if len(blob)>a07.SCRIPT_ENTRY_LIMIT:
        stats["unsupported_sections"]+=1;return
    stats["scanned_sections"]+=1
    for pattern in (a09.TRANSFER_CALL,a09.ASSIGN_CALL):
        for match in pattern.finditer(blob):
            argument=match.group(2).strip()
            prefix=blob[max(0,match.start()-30):match.start()]
            # Do not count Ruby 'def pbWarp(...)' signatures as actual call sites.
            if re.search(r"\bdef\s*$",prefix,re.I):continue
            if re.fullmatch(r"\d+",argument):continue
            stats["computed_hits"]+=1
            if len(output)>=MAX_FINDINGS:
                stats["truncated_hits"]+=1;continue
            output.append({**source,"line_number":blob.count("\n",0,match.start())+1,
                "api":match.group(1),"argument_kind":classify_arg(argument),
                "argument_fingerprint":hashlib.sha256(argument.encode("utf-8")).hexdigest()[:12],
                "value_resolved":False,"ruby_executed":False})

def inspect_computed(game,a04_report,a09_report):
    """Re-scan same two A09 sources without executing scripts or leaking text."""
    data=a04.directory_root(game)
    base=a04_report["sources"]["DECADES"]
    maprow=next((x for x in base["maps"] if x["id"]==1),None)
    if not maprow:deny("Map001 missing in A04")
    raw=a07.limited_read(data/maprow["source_filename"],a07.MAP_LIMIT)
    if hashlib.sha256(raw).hexdigest()!=maprow["sha256"]:
        deny("Map001 changed after A04")
    root=loads(raw)
    if not isinstance(root,RubyObject) or root.name!="RPG::Map":
        deny("Map001 invalid")
    events=props(root).get("@events",{})
    if not isinstance(events,dict):deny("Map001 events invalid")
    hits=[];errors=[];stats=Counter()
    for eid in (1,2):
        event=events.get(eid)
        for pn,page in enumerate(props(event).get("@pages",[]),1):
            commands=props(page).get("@list",[])
            if not isinstance(commands,list) or len(commands)>a07.MAX_COMMANDS:
                deny("Map001 commands invalid")
            for ci,cmd in enumerate(commands):
                entry=props(cmd)
                if entry.get("@code") in (355,655):
                    params=entry.get("@parameters",[])
                    if isinstance(params,list) and params:
                        extract_shape_records(params[0],{"source_type":"MAP001",
                            "event_id":eid,"page_index":pn,"command_index":ci},hits,stats)
                    else:stats["unsupported_sections"]+=1
    scripts=data/"Scripts.rxdata"
    decoded=0
    if scripts.exists() or scripts.is_symlink():
        try:
            bundle=loads(a07.limited_read(scripts,a07.MAP_LIMIT))
            if not isinstance(bundle,list) or len(bundle)>MAX_ENTRIES:
                deny("Scripts.rxdata structure invalid")
            total=0
            for idx,entry in enumerate(bundle):
                if not isinstance(entry,list) or len(entry)<3 or not isinstance(entry[2],bytes):
                    errors.append({"script_entry":idx,"issue":"UNSUPPORTED_ENTRY"});continue
                try:
                    decomp=zlib.decompressobj()
                    content=decomp.decompress(entry[2],a07.SCRIPT_ENTRY_LIMIT+1)
                    if (len(content)>a07.SCRIPT_ENTRY_LIMIT or
                        decomp.unconsumed_tail or decomp.unused_data or not decomp.eof):
                        raise ValueError("INCOMPLETE_OR_OVERSIZED_SCRIPT")
                    total+=len(content)
                    if total>a07.SCRIPT_TOTAL_LIMIT:
                        raise ValueError("SCRIPTS_TOTAL_LIMIT")
                    decoded+=1
                    extract_shape_records(content,{"source_type":"SCRIPTS_RXDATA",
                        "script_entry":idx},hits,stats)
                except (ValueError,zlib.error,TypeError) as exc:
                    errors.append({"script_entry":idx,"issue":str(exc)[:70]})
        except (OSError,ValueError,IndexError,TypeError,RecursionError) as exc:
            errors.append({"issue":"SCRIPTS_BUNDLE_UNREADABLE","reason":str(exc)[:100]})
    else:
        errors.append({"issue":"SCRIPTS_RXDATA_NOT_FOUND"})
    expected=a09_report.get("script_transfer_triage",{}).get(
        "classification_counts",{}).get("SYMBOLIC_OR_COMPUTED")
    return {"scope":"MAP001_EVENTS_1_2_AND_SCRIPTS_RXDATA",
        "computed_shape_observed":stats["computed_hits"],
        "a09_computed_count":expected,
        "counts_match_a09":expected==stats["computed_hits"],
        "shape_histogram":dict(Counter(x["argument_kind"] for x in hits)),
        "unresolved_calls":hits,
        "unresolved_calls_truncated":stats["truncated_hits"]>0,
        "script_entries_decompressed":decoded,
        "unsupported_sections":stats["unsupported_sections"],
        "errors":errors[:100],"errors_count":len(errors),
        "all_dynamic_targets_resolved":False,
        "all_possible_transfer_apis_scanned":False,
        "ruby_executed":False}

def intro_gate_review(a10_report):
    intro=a10_report["intro_transfer_analysis"]
    examined=[];missing=[];fingerprints=[]
    for event in intro.get("events",[]):
        eid=event.get("event_id")
        if eid not in (1,2):continue
        if event.get("status")!="EXAMINED_INERT":
            missing.append(eid);continue
        pages=event.get("pages",[])
        if not isinstance(pages,list):deny("A10 pages invalid")
        for page in pages:
            no=page.get("page_index")
            transfers=page.get("transfer_commands",[])
            if not isinstance(transfers,list):deny("A10 transfer list invalid")
            for transfer in transfers:
                if transfer.get("map_id")!=3:continue
                fingerprints.append((eid,no,transfer.get("command_index")))
                examined.append({"source_map_id":1,"event_id":eid,
                    "page_index":no,"trigger_code":page.get("trigger_code"),
                    "page_condition_flags":page.get("condition_flags",{}),
                    "enabled_condition_inputs":page.get("active_condition_inputs",{}),
                    "transfer_command_index":transfer.get("command_index"),
                    "preceding_control_commands":transfer.get("preceding_control_commands",[]),
                    "pages_in_same_event":len(pages),
                    "higher_indexed_page_exists":any(is_int(p.get("page_index"))
                       and p["page_index"]>no for p in pages),
                    "page_is_active_at_runtime":"UNKNOWN",
                    "branch_taken_at_runtime":"UNKNOWN",
                    "actual_destination_intent":"UNKNOWN",
                    "automatic_replacement_allowed":False})
    old=intro.get("mapid3_transfer_positions",[])
    expected=sorted((x.get("event_id"),x.get("page"),x.get("command_index")) for x in old)
    return {"sensitive_transfers":examined,
        "transfer_count":len(examined),
        "matches_a10_positions":sorted(fingerprints)==expected,
        "missing_events":missing,
        "page_selection_verified":False,
        "runtime_input_and_switches_verified":False,
        "safe_replacement_map_id":None,
        "needs_manual_game_exe_test":True}

def reserve_preflight(a10_report,a04_report):
    rows=a10_report.get("mapid_matrix")
    if not isinstance(rows,list) or len(rows)!=82:
        deny("A10 candidate matrix absent or incomplete")
    ids=[x.get("map_id") for x in rows if isinstance(x,dict)]
    if ids!=list(range(518,600)):deny("A10 IDs not exactly 518..599")
    if any(r.get("approved_for_reservation") is not False for r in rows):
        deny("A10 falsely approved a candidate")
    occ=set(a04_report.get("observed_or_declared_occupied_map_ids",[]))
    counts={s:0 for s in KNOWN_STATUSES}
    result=[]
    for r in rows:
        mid=r["map_id"];s=r.get("status")
        if s not in counts:deny("unrecognized A10 state")
        if (r.get("physically_or_declared_occupied") is not (mid in occ) or
            (s=="OCCUPIED_IN_CURRENT_SNAPSHOT")!=(mid in occ)):
            deny("A10 vacancy vs A04 contradictory")
        counts[s]+=1
        result.append({"map_id":mid,"observed_status":s,
            "eligible_for_provisional_design":s=="OBSERVED_VACANT_NOT_RESERVED",
            "reserved":False,"native_assignment":None,
            "future_ownership_verified":False,"safe_to_write":False})
    return {"range":[518,599],"count":len(result),"status_counts":counts,
        "candidate_matrix":result,"reservation_approved":False,
        "rollback_protocol":{
            "status":"DRAFT_ONLY_NOT_EXECUTED",
            "requires_prewrite_inventory_and_sha256":True,
            "requires_separate_backups":[
                "game/Data/MapInfos.rxdata",
                "game/Data/MapNNN.rxdata for every changed native ID",
                "game/Data/Tilesets.rxdata and referenced graphics",
                "game/Data/blue-*-install.json and regional mapping markers",
                "game/Data/Scripts.rxdata and affected common events",
                "game/Game.exe and other affected resources",
                "user save files stored outside game directory"
            ],
            "prewrite_requirements":[
                "source map ownership and distribution rights confirmed",
                "full Kanto Johto Hoenn Sinnoh installer ID claim review",
                "new install has compare-and-swap SHA256 baseline gate",
                "Game.exe and JoiPlay tests in isolated clone",
                "rollback tested in isolated clone",
            ],
            "installer_or_backup_created":False,
            "restore_performed":False,
            "may_touch_user_game":False}}

def audit(game:Path,project:Path,a04_report:dict,a06_report:dict,
          a07_report:dict,a08_report:dict,a09_report:dict,a10_report:dict)->dict:
    game=a04.safe_path(game)
    project=a04.safe_path(project)
    base=a04_report.get("sources",{}).get("DECADES",{})
    digest=base.get("mapinfos_sha256")
    chain=(digest and a04_report.get("phase")=="A04"
        and all(x.get("mapinfos_sha256")==digest for x in
            (a06_report,a07_report,a08_report,a09_report,a10_report))
        and all(x.get("phase")==phase for x,phase in (
            (a06_report,"A06"),(a07_report,"A07"),(a08_report,"A08"),
            (a09_report,"A09"),(a10_report,"A10")))
        and a07_report.get("review_errors_count")==0
        and a10_report.get("status")=="DIAGNOSTIC_COMPLETE_RESERVATION_BLOCKED"
        and a10_report.get("mapids_reviewed")==82)
    if not chain:deny("A04 through A10 incoherent or incomplete")
    intro=intro_gate_review(a10_report)
    dynamic=inspect_computed(game,a04_report,a09_report)
    reserve=reserve_preflight(a10_report,a04_report)
    manifest=a10_report["installer_manifest_analysis"]
    missing=[x["name"] for x in manifest.get("files",[])
             if x.get("status")!="PARSED_SCHEMA_PARTIAL"]
    flags=[]
    if intro["transfer_count"] and 3 not in a04_report.get("observed_or_declared_occupied_map_ids",[]):
        flags.append("MAPID3_MISSING_INTRO_TARGET")
    if not intro["matches_a10_positions"] or intro["missing_events"]:
        flags.append("INTRO_A10_COHERENCE_OR_EVENT_MISSING")
    if dynamic["computed_shape_observed"] or dynamic["a09_computed_count"]:
        flags.append("COMPUTED_MAPID_REFERENCES_NEED_RUNTIME_PROVENANCE")
    if not dynamic["counts_match_a09"] or dynamic["errors_count"] or dynamic["unsupported_sections"]:
        flags.append("SCRIPT_TRIAGE_INCOMPLETE_OR_DIFFERENT")
    if missing:flags.append("REGIONAL_MANIFESTS_INCOMPLETE")
    if any(x["status"]!="OBSERVED_VACANT_NOT_RESERVED" for x in reserve["candidate_matrix"]):
        flags.append("CANDIDATE_MAPID_CONFLICTS_OBSERVED")
    flags+=["FUTURE_BLUE_STORY_CLAIMS_UNCHECKED",
            "NO_NATIVE_GAME_EXE_OR_ANDROID_INTRO_VALIDATION",
            "UNOVA_SOURCE_RIGHTS_AND_REMAP_PENDING"]
    return {"schema":1,"region":"UNOVA","phase":"A11",
        "mode":"INERT_INTRO_GATES_COMPUTED_SHAPES_AND_RESERVE_PREFLIGHT",
        "status":"A11_DIAGNOSTIC_DONE_PLAN_ONLY_NOT_INSTALLABLE",
        "mapinfos_sha256":digest,
        "intro_route_review":intro,
        "computed_reference_review":dynamic,
        "regional_manifest_missing_or_partial":missing,
        "reservation_preflight":reserve,
        "review_flags":sorted(set(flags)),
        "all_script_destinations_resolved":False,
        "runtime_intro_verified":False,"mapid3_repaired":False,
        "source_rights_verified":False,"future_installer_claims_verified":False,
        "can_reserve_mapids":False,"mapids_allocated":False,
        "can_install":False,"native_qa_passed":False,
        "game_exe_tested":False,"android_tested":False,
        "game_or_saves_modified":False,
        "bar_a_completed":0,"bar_a_total":8}

def save(project:Path,report:dict)->Path:
    project=a04.safe_path(project)
    for folder in (project/".blue-work",project/".blue-work/unova",project/OUT):
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            deny("unsafe private report path")
        folder.mkdir(exist_ok=True)
    data=(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    target=project/OUT/("a11-intro-preflight-"+hashlib.sha256(data).hexdigest()[:16]+".json")
    if target.is_symlink():deny("symlink output")
    if target.exists():
        if target.read_bytes()!=data:deny("immutable report conflict")
    else:
        with target.open("xb") as file:file.write(data)
    return target
