#!/usr/bin/env python3
"""L01: OPTIONAL, OFFLINE projection of pre-existing public QA summaries.

This never starts B09/B10/B11, Sandbox, Game.exe or JoiPlay; never reads game,
saves, PNGs, private B11 baseline or arbitrary user paths. The only possible
input files are the seven explicitly staged JSON reports in a fixed workspace
directory. --preview is read-only. --write is a separate, explicit local action
writing exactly the L00 input JSON. No network, upload or clipboard action.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import re
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_g01_b09_receipt as g01
import audit_sinnoh_l00_readiness as l00

INPUT_DIR=".blue-work/sinnoh-l01-source"
INPUT_FILES={
    "b09_receipt":"b09-receipt.json",
    "b09_dry_run":"b09-dry-run.json",
    "b10":"b10-session.json",
    "b11_before":"b11-before.json",
    "b11_after":"b11-after.json",
    "r07":"r07-diagnostic.json",
    "r08":"r08-review-count.json",
}
DEST=l00.PRIVATE_REPORT
ID=re.compile(r"[0-9a-f]{32}\Z")
MAX_BYTES=65536

# These are the ONLY allowed keys in each SOURCE SUMMARY, not in the output.
# In particular no private-baseline.json, HMAC, save names/paths/hashes, files
# from game/Data, arbitrary source PDFs, or donor image lists are accepted.
B10_BASE={
    "schema","region","stage","status","source_clone_sha256",
    "source_stage_sha256","native_map_ids","sinnoh_terrain_map_ids",
    "expected_total_maps","all_cloned_files_sha_verified",
    "sandbox_feature_enabled_on_host","sandbox_session_started",
    "game_exe_started","save_write_isolation_runtime_verified",
    "host_save_directories_mapped","mapped_folders_read_only",
    "internet_networking_enabled","clipboard_enabled",
    "guest_game_copy_completed","rights_verified","r07_complete",
    "r08_complete","r09_complete","phase_b_approved","phase_c_approved",
    "phase_d_approved","note",
}
B10_OPTIONAL={"config_relative_path","guest_instructions","can_start_game_on_host"}
B11_BEFORE_SOURCE={
    "stage","status","watch_id","clone_sha256","monitored_directories_count",
    "scope_selection_mode","default_scopes_not_monitored",
    "monitored_files_before","bytes_hashed_before","config_relative_path",
    "paths_names_and_saves_in_report","windows_sandbox_started",
    "Game_exe_started","host_saves_runtime_isolation_confirmed",
    "coverage_is_partial","r07_complete","phase_b_approved",
}
B11_AFTER_SOURCE={
    "stage","status","watch_id","monitored_directories_count",
    "scope_selection_mode","default_scopes_not_monitored","coverage_is_partial",
    "monitored_files_before","monitored_files_after","bytes_hashed_after",
    "files_added","files_removed","files_changed","watch_unchanged",
    "guest_observation_self_reported",
    "guest_vm_execution_independently_verified",
    "complete_host_save_coverage_verified",
    "true_runtime_save_path_in_source_verified",
    "host_saves_globally_isolated_proven","assets_rights_verified",
    "R07_R08_R09_approved","gameplay_approved",
    "phase_b_approved","phase_c_approved","phase_d_approved",
    "paths_names_and_saves_in_report","next_action",
}
R07_SOURCE={
    "schema","region","task","substep","mode","status",
    "native_snapshot_present","native_occupied_count","native_mapinfos_sha256",
    "future_regional_reservations","future_regions_with_evidence",
    "future_regions_required","sinnoh_candidate_destination_ids",
    "collisions","blockers","candidate_safety_reviewable",
    "r07_complete","r08_real_maps_imported","r09_game_exe_joiplay_tested",
    "rights_verified","may_apply_to_main_game","game_or_saves_modified",
    "native_gameplay_verified","note",
}
R08_SOURCE={
    "schema","region","stage","kind","status","source_expected_png_count",
    "per_asset_licenses_reviewed_count","source_asset_rights_verified",
    "r08_complete",
}

def blocked(reason):
    # Caller NEVER prints raw input values, paths, or OS exception text.
    raise ValueError("SINNOH_L01_BLOCKED: "+reason)

def safe_file(root,rel):
    path=Path(root)/rel
    # No symlink in any component, including dangling final symlinks.
    if any(x.is_symlink() for x in (path,*path.parents)):
        blocked("symlink in named source or output")
    return path

def read_named(root,key):
    path=safe_file(root,INPUT_DIR+"/"+INPUT_FILES[key])
    if not path.is_file():
        return None
    if not 0<path.stat().st_size<=MAX_BYTES:
        blocked("staged JSON absent or over size limit")
    try:
        obj=json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError,ValueError,UnicodeError):
        blocked("staged JSON is not valid")
    if type(obj) is not dict:
        blocked("staged input must be object")
    return obj

def exact(obj,fields):
    if type(obj) is not dict or set(obj)!=set(fields):
        blocked("missing or unexpected source fields")

def negative(obj,fields):
    if any(obj.get(field) is not False for field in fields):
        blocked("source summary claims an unsafe native state")

def project_b09(receipt,dry,contract):
    # Reuse G01's strict existing dry-run/receipt validator. It checks exact
    # source fields, consistent count arithmetic and the plan-SHA folder bind.
    try:
        audit=g01.audit_receipt(receipt,contract,dry)
    except (TypeError,ValueError,KeyError,IndexError):
        blocked("B09 receipt and dry-run provenance mismatch")
    if audit["linked_to_supplied_dry_run"] is not True:
        blocked("B09 plan linkage missing")
    return {
        "stage":"B09","status":g01.STATUS,
        "plan_sha256":dry["plan_sha256"],
        "native_inventory_sha256":contract["native_inventory_sha256"],
        "map_ids_clone_total":receipt["map_ids_clone_total"],
        "b08_maps_validated":receipt["b08_maps_validated"],
        "b08_pngs_validated":receipt["b08_pngs_validated"],
        "saves_copied":False,"game_exe_executed":False,
        "safe_to_launch":False,"can_install_live_game":False,
        "r07_complete":False,"phase_b_approved":0,
    }

def project_b10(raw):
    if set(raw) not in (B10_BASE,B10_BASE|B10_OPTIONAL):
        blocked("B10 source fields not exactly the emitted summary")
    if raw["schema"]!=1 or raw["region"]!="SINNOH" or raw["stage"]!="B10":
        blocked("B10 source identity not valid")
    if raw["status"]!="WSB_CONFIG_PREPARED_NOT_LAUNCHED":
        blocked("B10 not prepared safely")
    for field in ("all_cloned_files_sha_verified","sandbox_feature_enabled_on_host",
                  "mapped_folders_read_only"):
        if raw[field] is not True:blocked("B10 safe WSB policy absent")
    negative(raw,("sandbox_session_started","game_exe_started",
                  "save_write_isolation_runtime_verified",
                  "host_save_directories_mapped","internet_networking_enabled",
                  "clipboard_enabled","guest_game_copy_completed",
                  "rights_verified","r07_complete","r08_complete","r09_complete"))
    if any(type(raw["phase_"+x+"_approved"]) is not int or raw["phase_"+x+"_approved"]!=0
           for x in ("b","c","d")):
        blocked("B10 native gate claimed")
    if B10_OPTIONAL.issubset(raw) and raw["can_start_game_on_host"] is not False:
        blocked("B10 source claims executable can run on host")
    return {field:raw[field] for field in l00.EXPECTED_FIELDS["B10"]}

def project_b11(before,after,plan_sha=None):
    exact(before,B11_BEFORE_SOURCE)
    exact(after,B11_AFTER_SOURCE)
    if (before["stage"]!="B11" or after["stage"]!="B11"
            or type(before["watch_id"]) is not str or not ID.fullmatch(before["watch_id"])
            or before["watch_id"]!=after["watch_id"]
            or not l00.is_sha(before["clone_sha256"])
            or (plan_sha is not None and before["clone_sha256"]!=plan_sha)):
        blocked("B11 before and after are not the same protected session")
    if (type(before["bytes_hashed_before"]) is not int or before["bytes_hashed_before"]<0
            or type(after["bytes_hashed_after"]) is not int or after["bytes_hashed_after"]<0):
        blocked("B11 private source total bytes invalid")
    # B11 can be exported in a standalone session, but it NEVER adds a SHA or
    # a secret session ID to the shareable projection.
    return {
        "stage":"B11",
        "before":{k:before[k] for k in l00.B11_BEFORE},
        "after":{k:after[k] for k in l00.B11_AFTER},
    }

def project_r07(raw):
    exact(raw,R07_SOURCE)
    if (raw["schema"]!=1 or raw["region"]!="SINNOH"
            or raw["task"]!="S07" or raw["substep"]!="R07"
            or raw["mode"]!="LOCAL_RESERVATIONS_DIAGNOSTIC_ONLY"):
        blocked("R07 diagnostic does not come from the expected format")
    negative(raw,("r07_complete","r08_real_maps_imported","r09_game_exe_joiplay_tested",
                  "rights_verified","may_apply_to_main_game","game_or_saves_modified",
                  "native_gameplay_verified"))
    if (type(raw["collisions"]) is not list or len(raw["collisions"])>5000
            or any(type(x) is not dict or set(x)!={"id","reason"}
                   or type(x["id"]) is not int
                   or type(x["reason"]) is not str
                   for x in raw["collisions"])):
        blocked("R07 collision counts cannot be derived")
    if type(raw["future_regional_reservations"]) is not dict or len(raw["future_regional_reservations"])>3:
        blocked("R07 regional reservation aggregate invalid")
    # Ownership comments, future IDs and any recorded paths are never exported.
    return {
        "stage":"R07","status":raw["status"],
        "native_snapshot_present":raw["native_snapshot_present"],
        "native_occupied_count":raw["native_occupied_count"],
        "native_mapinfos_sha256":raw["native_mapinfos_sha256"],
        "future_regions_with_evidence":raw["future_regions_with_evidence"],
        "future_regions_required":raw["future_regions_required"],
        "collisions_count":len(raw["collisions"]),
        "candidate_safety_reviewable":raw["candidate_safety_reviewable"],
        "r07_complete":False,"may_apply_to_main_game":False,
        "rights_verified":False,
    }

def project_r08(raw):
    exact(raw,R08_SOURCE)
    if (raw["schema"]!=1 or raw["region"]!="SINNOH"
            or raw["stage"]!="R08" or raw["kind"]!="MANUAL_AGGREGATE_REVIEW_COUNT_ONLY"
            or raw["status"]!="RIGHTS_REVIEW_PENDING"):
        blocked("R08 input only accepts an aggregate human count")
    negative(raw,("source_asset_rights_verified","r08_complete"))
    return {
        "stage":"R08","status":"RIGHTS_REVIEW_PENDING",
        "source_expected_png_count":raw["source_expected_png_count"],
        "per_asset_licenses_reviewed_count":raw["per_asset_licenses_reviewed_count"],
        "source_asset_rights_verified":False,
        "physical_maps_approved":False,
        "twinleaf_map_bindings_verified":False,"twinleaf_warps_verified":False,
        "barry_pbs_compiled":False,"r08_complete":False,
        "can_install":False,
    }

def collect(root=ROOT,repo_root=ROOT):
    # Entirely synthetic/public source operation; no recursive file discovery.
    docs={stage:l00.read_json(repo_root,rel) for stage,rel in l00.CONTRACTS.items()}
    raw={key:read_named(root,key) for key in INPUT_FILES}
    if (raw["b09_receipt"] is None)!=(raw["b09_dry_run"] is None):
        blocked("B09 receipt must be paired with its dry-run")
    if (raw["b11_before"] is None)!=(raw["b11_after"] is None):
        blocked("B11 before and after must be paired")
    if raw["b10"] is not None and raw["b09_receipt"] is None:
        blocked("B10 requires B09 linked dry-run and receipt")
    bundle=l00.read_json(repo_root,l00.TEMPLATE)
    bundle=copy.deepcopy(bundle)
    output=bundle["reports"]
    if raw["b09_receipt"] is not None:
        output["B09"]=project_b09(raw["b09_receipt"],raw["b09_dry_run"],docs["B09"])
    if raw["b10"] is not None:
        output["B10"]=project_b10(raw["b10"])
    if raw["b11_before"] is not None:
        sha=output["B09"]["plan_sha256"] if output["B09"] else None
        output["B11"]=project_b11(raw["b11_before"],raw["b11_after"],sha)
    if raw["r07"] is not None:
        output["R07"]=project_r07(raw["r07"])
    if raw["r08"] is not None:
        output["R08"]=project_r08(raw["r08"])
    # The real L00 contracts & final G12 provenance are the final guard.
    final=l00.g12.run(repo_root)
    handoff=l00.read_json(repo_root,l00.g12.HANDOFF)
    try:
        l00.audit(bundle,docs,handoff,final)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError):
        blocked("source summary was rejected by the L00 final auditor")
    return bundle

def write_explicit(root,bundle):
    """Atomic write only after separate --write invocation, with no upload."""
    output=safe_file(root,DEST)
    folder=output.parent
    # Refuse an already symlinked workspace or output, including dangling link.
    if output.is_symlink() or folder.is_symlink() or folder.parent.is_symlink():
        blocked("unsafe workspace output symlink")
    folder.mkdir(mode=0o700,parents=True,exist_ok=True)
    if not folder.is_dir() or output.is_symlink() or output.is_dir():
        blocked("unsafe output destination")
    data=json.dumps(bundle,indent=2,ensure_ascii=True,sort_keys=True)+"\n"
    fd,tmp=tempfile.mkstemp(prefix=".l01-",suffix=".json",dir=folder)
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as h:
            os.chmod(tmp,0o600)
            h.write(data)
            h.flush()
            os.fsync(h.fileno())
        if output.is_symlink():blocked("output symlink appeared")
        os.replace(tmp,output)
    finally:
        if os.path.lexists(tmp):os.unlink(tmp)
    return output

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    # Do not allow argparse to echo unknown raw private CLI arguments.
    if argv not in ([],["--preview"],["--write"],["--help"],["-h"]):
        print("SINNOH_L01_BLOCKED: unknown or unsafe option",file=sys.stderr)
        return 2
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument("--preview",action="store_true",help="print only sanitized JSON, do not write")
    mode.add_argument("--write",action="store_true",help="explicitly write one fixed local sanitized JSON for human review")
    args=parser.parse_args(argv)
    try:
        bundle=collect()
        if args.write:
            write_explicit(ROOT,bundle)
            print(json.dumps({
                "stage":"L01","status":"SANITIZED_JSON_WRITTEN_LOCALLY_REVIEW_BEFORE_SHARING",
                "received_reports":sum(v is not None for v in bundle["reports"].values()),
                "auto_uploaded":False,"native_approved":False,
            },sort_keys=True))
        else:
            print(json.dumps(bundle,sort_keys=True,indent=2,ensure_ascii=True))
        return 0
    except (OSError,ValueError,TypeError,KeyError,IndexError,UnicodeError,AttributeError):
        print("SINNOH_L01_BLOCKED: source summaries invalid or unsafe; no private data printed",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
