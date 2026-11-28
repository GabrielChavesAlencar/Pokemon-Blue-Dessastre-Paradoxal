#!/usr/bin/env python3
"""A12 Unova: inert installer-source ownership review + isolated QA preflight plan.

Source code is parsed, not imported or executed. This auditor never installs maps,
makes copies of the native game, alters user saves, or authorizes MapID ownership.
"""
from __future__ import annotations
import ast
import hashlib
import json
from collections import Counter
from pathlib import Path

import audit_unova_a04_mapids as a04
import audit_unova_a10_dynamic_matrix as a10

REPORT_DIR=Path(".blue-work/unova/audit")
SOURCE_FILES=(
 "scripts/install_game.py",
 "scripts/regions/install_kanto.py",
 "scripts/regions/pilot.py",
 "scripts/regions/johto_main_preview.py",
 "scripts/regions/auto_integrate_johto.py",
 "scripts/regions/pilot_hoenn.py",
 "scripts/regions/install_hoenn.py",
 "scripts/regions/install_sinnoh_qa_copy.py",
 "scripts/regions/sinnoh_shared.py",
)
MAX_SOURCE_BYTES=250_000
MAX_TOTAL_BYTES=850_000
STATUSES=a10.BLOCK
EXPECTED_STATUS="A11_DIAGNOSTIC_DONE_PLAN_ONLY_NOT_INSTALLABLE"

def deny(message):
    raise ValueError("UNOVA_A12_BLOQUEADO: "+str(message))

def funcs_of(tree):
    return {node.name for node in ast.walk(tree)
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))}

def has_range(tree,lo,hi):
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call) or not isinstance(node.func,ast.Name):
            continue
        if node.func.id!="range" or len(node.args)!=2:
            continue
        if (all(isinstance(x,ast.Constant) and type(x.value) is int for x in node.args)
            and (node.args[0].value,node.args[1].value)==(lo,hi)):
            return True
    return False

def has_maps_lookup(tree):
    for node in ast.walk(tree):
        if isinstance(node,ast.Subscript):
            key=node.slice
            if isinstance(key,ast.Constant) and key.value=="maps":
                return True
    return False

def named_map_range(tree, name):
    """Read a unique top-level literal range without importing the installer."""
    if tree is None:
        return None
    assignments = [
        node.value for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == name for target in node.targets)
    ]
    if len(assignments) != 1:
        return None
    call = assignments[0]
    if (not isinstance(call, ast.Call) or not isinstance(call.func, ast.Name)
            or call.func.id != "range" or len(call.args) != 2 or call.keywords
            or not all(isinstance(arg, ast.Constant) and type(arg.value) is int for arg in call.args)):
        return None
    start, stop = (arg.value for arg in call.args)
    return [start, stop - 1] if 0 < start < stop else None


def audit_installer_sources(project):
    """Bounded AST review of bundled repo snapshot, NOT trusted live installer state."""
    records=[];total=0;parsed={}
    for name in SOURCE_FILES:
        path=project/name
        row={"path":name,"status":"NOT_FOUND","sha256":None,
             "loaded_from":"AUDIT_BUNDLE_OR_REPO_SNAPSHOT","executed":False}
        if not path.exists() and not path.is_symlink():
            records.append(row);continue
        if path.is_symlink() or not path.is_file():
            row["status"]="UNSAFE_SOURCE_PATH";records.append(row);continue
        try:
            size=path.stat().st_size
            if not 0<size<=MAX_SOURCE_BYTES or total+size>MAX_TOTAL_BYTES:
                row["status"]="SOURCE_SIZE_LIMIT";records.append(row);continue
            data=path.read_bytes()
            total+=len(data)
            row["sha256"]=hashlib.sha256(data).hexdigest()
            tree=ast.parse(data.decode("utf-8-sig"),filename=name)
            row["status"]="AST_PARSED_INERT"
            row["size_bytes"]=len(data)
            parsed[name]=tree
        except (OSError,UnicodeError,SyntaxError,ValueError,RecursionError) as exc:
            row["status"]="SOURCE_PARSE_ERROR"
            row["reason"]=str(exc)[:130]
        records.append(row)
    def ready(name):return name in parsed
    def function(name,which):return ready(name) and which in funcs_of(parsed[name])
    # These are specifically checked syntax anchors, not claims of runtime reachability.
    k="scripts/regions/install_kanto.py"
    j="scripts/regions/johto_main_preview.py"
    aj="scripts/regions/auto_integrate_johto.py"
    h="scripts/regions/pilot_hoenn.py"
    ih="scripts/regions/install_hoenn.py"
    s="scripts/regions/install_sinnoh_qa_copy.py"
    shared="scripts/regions/sinnoh_shared.py"
    root="scripts/install_game.py"
    facts=[
      {"region":"KANTO","claim":"MAPPING_FROM_GENERATED_PILOT_MANIFEST",
       "code_paths":[k],"anchor_found":function(k,"apply_install") and
                        has_maps_lookup(parsed[k]) if ready(k) else False,
       "known_destination_interval":None,"destination_ids_complete":False},
      {"region":"JOHTO","claim":"STAGED_MAPS_600_681",
       "code_paths":[j,aj],"anchor_found":ready(j) and ready(aj) and
                      has_range(parsed[j],600,682) and has_range(parsed[aj],600,682),
       "known_destination_interval":[600,681],"destination_ids_complete":False},
      {"region":"JOHTO","claim":"PREVIEW_GUARD_600_699",
       "code_paths":[j],"anchor_found":ready(j) and has_range(parsed[j],600,700)
                      and function(j,"build_overlay"),
       "known_destination_interval":[600,699],"destination_ids_complete":False},
      {"region":"HOENN","claim":"DYNAMIC_FREE_POOL_700_999",
       "code_paths":[h,ih],"anchor_found":ready(h) and ready(ih) and
                      has_range(parsed[h],700,1000) and function(h,"build_overlay")
                      and function(ih,"apply"),
       "known_destination_interval":[700,999],"destination_ids_complete":False},
      {"region":"SINNOH","claim":"ISOLATED_QA_COPY_PREPARATION",
       "code_paths":[s],"anchor_found":function(s,"prepare") and function(s,"install"),
       "known_destination_interval":None,"destination_ids_complete":False},
      {"region":"BLUE_STORY","claim":"REGIONAL_AUTOINTEGRATION_ENTRYPOINT",
       "code_paths":[root],"anchor_found":function(root,"install"),
       "known_destination_interval":None,"destination_ids_complete":False},
    ]
    for name, claim in (("SHARED_IDS", "SHARED_LOCAL_MAP_IDS"),
                        ("ID_RANGE", "SHARED_OVERLAY_VALIDATION_BAND")):
        span = named_map_range(parsed.get(shared), name)
        facts.append({"region": "SINNOH", "claim": claim, "code_paths": [shared],
                      "anchor_found": span is not None and function(shared, "validate_manifest"),
                      "known_destination_interval": span, "destination_ids_complete": False})
    # Only *verified anchors* support a syntactic comparison for *these bands*.
    ranges=[]
    for fact in facts:
        span=fact["known_destination_interval"]
        if fact["anchor_found"] and span:
            ranges.append({"region":fact["region"],"claim":fact["claim"],
               "range":span,"intersects_518_599":span[0]<=599 and span[1]>=518,
               "proof":"AST_LITERAL_RANGE_ONLY_NOT_COMPLETE_INSTALLER_OWNERSHIP"})
    return {"files":records,"sources_expected":len(SOURCE_FILES),
        "sources_parsed":len(parsed),
        "all_source_snapshots_read":len(parsed)==len(SOURCE_FILES),
        "code_anchors":facts,
        "observed_literal_bands":ranges,
        "bounded_source_bytes_read":total,
        "sources_executed":False,
        "repo_snapshot_matches_future_blue_story_code":False,
        "all_installer_allocation_paths_covered":False,
        "future_claims_proven_absent":False}

def resolve_shape_groups(a11):
    evidence=a11.get("computed_reference_review",{})
    hist=evidence.get("shape_histogram",{})
    if not isinstance(hist,dict):deny("A11 shape histogram absent")
    if any(type(v) is not int or v<0 for v in hist.values()):
        deny("A11 histogram invalid")
    count=evidence.get("computed_shape_observed")
    if type(count) is not int or count!=sum(hist.values()):
        deny("A11 shapes inconsistent")
    calls=evidence.get("unresolved_calls",[])
    if not isinstance(calls,list):deny("A11 unresolved references invalid")
    # Only shapes and hashes, never actual script text or argument execution.
    priorities={"INDEXED_VARIABLE":"HIGH","UNCLASSIFIED_EXPRESSION":"HIGH",
                "EMPTY_OR_UNCERTAIN":"HIGH","VARIABLE_OR_SYMBOL":"MEDIUM",
                "CALL_OR_EXPRESSION":"HIGH","COMPUTED_EXPRESSION":"HIGH"}
    return {"total_observed":count,"same_as_a09":evidence.get("counts_match_a09") is True,
        "by_shape":[{"shape":shape,"count":qty,
            "manual_review_priority":priorities.get(shape,"HIGH")}
            for shape,qty in sorted(hist.items())],
        "unresolved_source_fingerprints":[{"source_type":item.get("source_type"),
             "script_entry":item.get("script_entry"),"line_number":item.get("line_number"),
             "argument_kind":item.get("argument_kind"),
             "argument_fingerprint":item.get("argument_fingerprint")}
             for item in calls[:80] if isinstance(item,dict)],
        "all_destinations_known":False,"dynamic_calls_executed":False}

def rehearsal(a04_report,a10_report,a11_report,source_review):
    # This is a pure-memory gate model: no directory or game clone is created.
    matrix=a11_report.get("reservation_preflight",{}).get("candidate_matrix",[])
    if not isinstance(matrix,list) or len(matrix)!=82:
        deny("A11 reserve preflight matrix missing")
    occupied=set(a04_report.get("observed_or_declared_occupied_map_ids",[]))
    manifest=set(a10_report.get("installer_manifest_analysis",{}).get("candidate_ids",[]))
    if not all(type(x) is int for x in manifest|occupied):
        deny("Noninteger native IDs")
    staged=[]
    installer_bands = [row["range"] for row in source_review["observed_literal_bands"]
                       if row["intersects_518_599"]]
    for offset,r in enumerate(matrix):
        if not isinstance(r,dict) or r.get("map_id")!=518+offset:
            deny("A11 candidate matrix order mismatch")
        mid=r["map_id"];occ=mid in occupied;claimed=mid in manifest
        if (r.get("reserved") is not False or r.get("safe_to_write") is not False
            or r.get("observed_status") not in a11_report["reservation_preflight"]["status_counts"]):
            deny("A11 unsafe or unknown row")
        if (r.get("observed_status")=="OCCUPIED_IN_CURRENT_SNAPSHOT")!=occ:
            deny("A11 occupancy vs A04 mismatch")
        staged.append({"map_id":mid,"planned_relative_map_path":f"Data/Map{mid:03}.rxdata",
            "observed_native_collision":occ,
            "installer_manifest_claim_observed":claimed,
            "installer_literal_band_overlap":any(lo <= mid <= hi for lo, hi in installer_bands),
            "source_map_confirmed":False,"reservation_approved":False,
            "write_allowed":False})
    snapshot_conflicts=sum(x["observed_native_collision"] or x["installer_manifest_claim_observed"]
                          for x in staged)
    return {"mode":"IN_MEMORY_NEGATIVE_GATE_REHEARSAL_ONLY",
        "candidate_count":len(staged),"target_rows":staged,
        "observed_snapshot_conflicts":snapshot_conflicts,
        "installer_literal_band_overlap_count":sum(x["installer_literal_band_overlap"] for x in staged),
        "clean_snapshot_case":{"native_conflicts":snapshot_conflicts,
            "approved":False,"reason":"FUTURE_CLAIMS_AND_UNOVA_SOURCE_NOT_VERIFIED"},
        "synthetic_cases":[
            {"case":"INJECT_MANIFEST_CLAIM_MAPID_518","synthetic":True,
             "would_block":True,"native_files_created":False},
            {"case":"INJECT_STALE_MAPINFOS_SHA256","synthetic":True,
             "would_block":True,"native_files_created":False},
            {"case":"INJECT_UNVERIFIED_SOURCE_ARCHIVE","synthetic":True,
             "would_block":True,"native_files_created":False},
        ],
        "isolated_game_copy_created":False,"backup_created":False,
        "game_exe_started":False,"native_game_changed":False,
        "ready_to_install":False,"mapids_reserved":False,
        "future_copy_requirements":[
            "verified donor source with permission and per-map checksums",
            "consistent current MapInfos SHA256 immediately before any write",
            "future regional manifest claims reconciled with current native files",
            "isolated clone with separate save directory and no shared player profile",
            "transactional backup, collision rejection and rollback on isolated clone",
            "Game.exe entry, migration and warps tested on clone",
        ],
        "all_bundled_source_anchors_found":all(x["anchor_found"] for x in
                                            source_review["code_anchors"])}

def audit(game:Path,project:Path,a04_report:dict,a06_report:dict,
          a07_report:dict,a08_report:dict,a09_report:dict,a10_report:dict,
          a11_report:dict)->dict:
    game=a04.safe_path(game);project=a04.safe_path(project)
    baseline=a04_report.get("sources",{}).get("DECADES",{})
    digest=baseline.get("mapinfos_sha256")
    chain=(digest and a04_report.get("phase")=="A04"
        and all(r.get("phase")==p and r.get("mapinfos_sha256")==digest
                for p,r in (("A06",a06_report),("A07",a07_report),
                    ("A08",a08_report),("A09",a09_report),
                    ("A10",a10_report),("A11",a11_report)))
        and a11_report.get("status")==EXPECTED_STATUS
        and a11_report.get("can_reserve_mapids") is False
        and a11_report.get("mapids_allocated") is False
        and a07_report.get("review_errors_count")==0
        and a10_report.get("mapids_reviewed")==82)
    if not chain:deny("A04..A11 audit chain incoherent")
    data=a04.directory_root(game)
    infos=data/"MapInfos.rxdata"
    if infos.is_symlink() or not infos.is_file() or hashlib.sha256(
            infos.read_bytes()).hexdigest()!=digest:
        deny("MapInfos changed since A04")
    map1=next((row for row in baseline.get("maps",[]) if row.get("id")==1),None)
    if not map1:deny("Map001 missing")
    p=data/map1["source_filename"]
    if p.is_symlink() or not p.is_file() or hashlib.sha256(
            p.read_bytes()).hexdigest()!=map1.get("sha256"):
        deny("Map001 changed since A04")
    review=audit_installer_sources(project)
    shapes=resolve_shape_groups(a11_report)
    plan=rehearsal(a04_report,a10_report,a11_report,review)
    manifest=a10_report.get("installer_manifest_analysis",{})
    intro=a11_report.get("intro_route_review",{})
    flags=["FUTURE_BLUE_STORY_OWNERSHIP_NOT_PROVEN",
           "UNOVA_SOURCE_RIGHTS_AND_MAP_FILES_MISSING",
           "ISOLATED_QA_GAME_NOT_CREATED",
           "MAPID3_INTRO_RUNTIME_DESTINATION_NOT_VERIFIED"]
    if not review["all_source_snapshots_read"] or not plan["all_bundled_source_anchors_found"]:
        flags.append("INSTALLER_SOURCE_SNAPSHOT_INCOMPLETE")
    if plan["observed_snapshot_conflicts"]:
        flags.append("LOCAL_CANDIDATE_COLLISION_OBSERVED")
    if not shapes["same_as_a09"]:
        flags.append("COMPUTED_SHAPE_COUNT_MISMATCH_A09")
    if shapes["total_observed"]:
        flags.append("DYNAMIC_TRANSFER_ARGUMENTS_UNRESOLVED")
    if any(row.get("status")!="PARSED_SCHEMA_PARTIAL"
           for row in manifest.get("files",[])):
        flags.append("LOCAL_MANIFEST_COVERAGE_INCOMPLETE")
    if intro.get("transfer_count") and not intro.get("page_selection_verified"):
        flags.append("INTRO_EVENT_PAGE_AND_BRANCH_RUNTIME_UNVERIFIED")
    if any(x["intersects_518_599"] for x in review["observed_literal_bands"]):
        flags.append("KNOWN_LITERAL_INSTALLER_BAND_OVERLAP")
    return {"schema":1,"region":"UNOVA","phase":"A12",
        "mode":"INERT_INSTALLER_SOURCE_OWNERSHIP_AND_IN_MEMORY_QA_PLAN",
        "status":"A12_SOURCE_REVIEW_DONE_ISOLATED_QA_NOT_CREATED",
        "mapinfos_sha256":digest,
        "installer_source_review":review,
        "regional_local_manifest_review":{
            "manifest_files":manifest.get("files",[]),
            "all_future_manifest_claims_checked":False,
            "all_local_manifest_schemas_interpreted":False},
        "dynamic_reference_prioritization":shapes,
        "intro_mapid3_runtime_status":{
            "transfers_observed":intro.get("transfer_count",0),
            "destination_map_id":3,"destination_exists":3 in
                a04_report.get("observed_or_declared_occupied_map_ids",[]),
            "actual_runtime_branch_verified":False,
            "replacement_destination_verified":False},
        "isolated_install_preparation":plan,
        "review_flags":sorted(set(flags)),
        "known_literal_bands_do_not_intersect_candidate_interval":
            all(not x["intersects_518_599"] for x in review["observed_literal_bands"]),
        "complete_future_code_and_manifest_ownership_proven":False,
        "full_source_remap_approved":False,
        "can_reserve_mapids":False,"can_install":False,
        "mapids_allocated":False,"rollback_performed":False,
        "game_exe_tested":False,"android_tested":False,
        "game_or_saves_modified":False,"bar_a_completed":0,"bar_a_total":8}

def save(project:Path,report:dict)->Path:
    project=a04.safe_path(project)
    for folder in (project/".blue-work",project/".blue-work/unova",project/REPORT_DIR):
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            deny("unsafe report directory")
        folder.mkdir(exist_ok=True)
    payload=(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n").encode("utf-8")
    target=project/REPORT_DIR/("a12-installer-ownership-"+hashlib.sha256(payload).hexdigest()[:16]+".json")
    if target.is_symlink():deny("report symlink")
    if target.exists():
        if target.read_bytes()!=payload:deny("immutable evidence conflict")
    else:
        with target.open("xb") as stream:stream.write(payload)
    return target
