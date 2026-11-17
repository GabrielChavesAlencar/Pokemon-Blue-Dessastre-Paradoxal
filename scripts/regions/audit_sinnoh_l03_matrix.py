#!/usr/bin/env python3
"""Sinnoh L03: immutable-format documentary reconciliation, NOT native acceptance.

GitHub-only by default. Can optionally read only the fixed L00/L01 sanitized
receipt using --workspace-reports, with the same privacy limitations as L02.
No user game, save, private baseline, WSB guest, network or upload is accessed.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import review_sinnoh_l02_evidence as l02

MATRIX="data/regions/sinnoh-l03-documentary-review.json"
STAGES=("B09","B10","B11","R07","R08")
STATUSES=(
    l02.STATUS_MISSING,l02.STATUS_UNVERIFIED,
    l02.STATUS_DEPENDENCY,l02.STATUS_BLOCKED,
)
ACTIONS={
    l02.STATUS_MISSING:"REQUEST_NEW_SANITIZED_REPORT",
    l02.STATUS_UNVERIFIED:"SCHEDULE_DOCUMENTARY_ANALYSIS",
    l02.STATUS_DEPENDENCY:"RECONCILE_PREREQUISITES",
    l02.STATUS_BLOCKED:"BLOCK_AND_REVIEW",
}
DISPOSITIONS=["REVIEW","REQUEST_NEW_SANITIZED_REPORT",
              "BLOCK","SCHEDULE_DOCUMENTARY_ANALYSIS"]
MATRIX_RULES={
    "B09":{
        "depends_on":[],
        "review_kind":"CLONE_PROVENANCE",
        "criteria":["independent_source_provenance","physical_clone_integrity",
                    "human_receipt_identity_review"]},
    "B10":{
        "depends_on":["B09"],
        "review_kind":"WSB_CONFIGURATION",
        "criteria":["independent_b09_b10_binding","sandbox_readonly_policy_review",
                    "host_environment_not_verified_from_json"]},
    "B11":{
        "depends_on":["B09","B10"],
        "review_kind":"LIMITED_SAVE_SCOPE",
        "criteria":["private_session_link_review_outside_github",
                    "full_engine_save_path_coverage_separate_review",
                    "save_snapshot_unchanged_not_global_proof"]},
    "R07":{
        "depends_on":[],
        "review_kind":"REGIONAL_MAPID_RESERVATIONS",
        "criteria":["physical_region_inventory_review",
                    "other_region_ownership_review","future_conflict_review"]},
    "R08":{
        "depends_on":[],
        "review_kind":"ASSET_RIGHTS_AND_BINDINGS",
        "criteria":["per_asset_license_documents_review",
                    "native_graphics_maps_and_warps_review",
                    "real_pbs_compilation_separate_review"]},
}
FIXED_TRUE=(
    "no_authorization_from_documentary_status","no_automatic_approval",
    "no_private_evidence_in_reconciliation",
    "every_source_self_reported_not_authenticated",
    "no_game_exe_or_joiplay_execution","no_windows_sandbox_execution",
    "no_user_saves_access","no_auto_upload",
)
FIXED_FALSE=(
    "verified_timestamps_in_public_input",
    "verifiable_b11_session_link_in_public_input",
    "r07_complete","r08_complete","r09_complete",
    "can_schedule_native_qa","can_install_sinnoh","sinnoh_playable",
)
ROW_KEYS={
    "stage","depends_on","review_kind","criteria","baseline_status",
    "independent_evidence_accepted","physical_ready",
}
MANIFEST_KEYS={
    "schema","region","stage","version","status",
    "source_review","source_envelope","status_actions",
    "allowed_human_dispositions",*FIXED_TRUE,*FIXED_FALSE,
    "native_test_cases_total","windows_cases","android_cases",
    "passed_native_cases","phase_b_approved","phase_c_approved",
    "phase_d_approved","rows",
}
def blocked(reason):
    # Never interpolate untrusted values into public error messages.
    raise ValueError("SINNOH_L03_BLOCKED: "+reason)

def validate_manifest(manifest):
    if type(manifest) is not dict or set(manifest)!=MANIFEST_KEYS:
        blocked("unexpected protocol fields")
    expected={
        "schema":1,"region":"SINNOH","stage":"L03","version":1,
        "status":"DOCUMENTARY_PROTOCOL_ONLY_NO_NATIVE_APPROVAL",
        "source_review":"scripts/regions/review_sinnoh_l02_evidence.py",
        "source_envelope":"data/regions/sinnoh-l00-public-reports.json",
    }
    for field,value in expected.items():
        if type(manifest[field]) is not type(value) or manifest[field]!=value:
            blocked("protocol identity or version was changed")
    if type(manifest["status_actions"]) is not dict or manifest["status_actions"]!=ACTIONS:
        blocked("invalid documentary action map")
    if manifest["allowed_human_dispositions"]!=DISPOSITIONS:
        blocked("invalid human dispositions")
    if any(manifest[k] is not True for k in FIXED_TRUE):
        blocked("missing non-executable and no-approval safety gate")
    if any(manifest[k] is not False for k in FIXED_FALSE):
        blocked("documentary review claims native physical approval")
    for key,value in (("native_test_cases_total",44),("windows_cases",43),
                      ("android_cases",1),("passed_native_cases",0),
                      ("phase_b_approved",0),("phase_c_approved",0),
                      ("phase_d_approved",0)):
        if type(manifest[key]) is not int or manifest[key]!=value:
            blocked("native case total or phase was modified")
    rows=manifest["rows"]
    if type(rows) is not list or len(rows)!=5:
        blocked("five source rows are required")
    if [row.get("stage") if type(row) is dict else None for row in rows]!=list(STAGES):
        blocked("row order, stage identity or unique stages changed")
    for row in rows:
        if set(row)!=ROW_KEYS:
            blocked("row includes unapproved or missing fields")
        spec=MATRIX_RULES[row["stage"]]
        if (row["depends_on"]!=spec["depends_on"]
            or row["review_kind"]!=spec["review_kind"]
            or row["criteria"]!=spec["criteria"]
            or row["baseline_status"]!=l02.STATUS_MISSING
            or row["independent_evidence_accepted"] is not False
            or row["physical_ready"] is not False):
            blocked("stage-specific gate, prerequisite or acceptance altered")
    return True

def reconcile(manifest,l02_result):
    validate_manifest(manifest)
    if (type(l02_result) is not dict or l02_result.get("stage")!="L02"
        or l02_result.get("mode")!="OFFLINE_SANITIZED_METADATA_REVIEW_ONLY"
        or l02_result.get("native_cases_total")!=44
        or l02_result.get("native_cases_completed")!=0
        or l02_result.get("native_cases_approved")!=0
        or l02_result.get("r07_complete") is not False
        or l02_result.get("r08_complete") is not False
        or l02_result.get("r09_complete") is not False
        or l02_result.get("may_start_game_in_vm") is not False
        or l02_result.get("may_install_live_game") is not False
        or l02_result.get("sinnoh_playable") is not False
        or l02_result.get("chronology_dates_in_sanitized_sources_available") is not False
        or l02_result.get("b11_session_link_in_sanitized_sources_available") is not False
        or l02_result.get("independent_receipt_authenticity_proven") is not False):
        blocked("L02 review claims unsupported evidence or native progress")
    original=l02_result.get("reports")
    if type(original) is not dict or set(original)!=set(STAGES):
        blocked("L02 source rows differ from the five stages")
    output=[]
    for row in manifest["rows"]:
        stage=row["stage"]
        source=original[stage]
        if (type(source) is not dict
            or set(source)!={"status","reason_code","human_review_required",
                            "physical_origin_authenticated","native_approval",
                            "next_human_action"}
            or source["status"] not in STATUSES
            or source["human_review_required"] is not True
            or source["physical_origin_authenticated"] is not False
            or source["native_approval"] is not False
            or source["next_human_action"]!=l02.STAGE_CHECKS[stage]
            or type(source["reason_code"]) is not str):
            blocked("L02 status shape or human review requirement changed")
        # Never embed reason_code values (which may in future be untrusted).
        # All output text comes from versioned, fixed protocol tokens.
        status=source["status"]
        output.append({
            "stage":stage,
            "status":status,
            "safe_next_action":ACTIONS[status],
            "depends_on":list(row["depends_on"]),
            "documentary_review_kind":row["review_kind"],
            "required_separate_human_checks":list(row["criteria"]),
            "self_report_authenticity_verified":False,
            "physical_acceptance_decided":False,
            "native_qa_allowed":False,
        })
    statuses={row["stage"]:row["status"] for row in output}
    counts={k:sum(v==k for v in statuses.values()) for k in STATUSES}
    if counts!={
        l02.STATUS_MISSING:l02_result["counts"]["missing"],
        l02.STATUS_UNVERIFIED:l02_result["counts"]["self_reported_unverified"],
        l02.STATUS_DEPENDENCY:l02_result["counts"]["missing_prerequisite"],
        l02.STATUS_BLOCKED:l02_result["counts"]["conflicting"],
    }:
        blocked("L02 aggregate counts cannot be reconciled")
    return {
        "schema":1,"region":"SINNOH","stage":"L03","version":1,
        "status":"DOCUMENTARY_HANDOFF_REQUIRES_SEPARATE_HUMAN_REVIEW",
        "source_documentary_status":l02_result["status"],
        "mode":"OFFLINE_FIXED_METADATA_ONLY",
        "rows":output,
        "counts":{
            "missing":counts[l02.STATUS_MISSING],
            "self_reported_unverified":counts[l02.STATUS_UNVERIFIED],
            "dependency_blocked":counts[l02.STATUS_DEPENDENCY],
            "conflicting":counts[l02.STATUS_BLOCKED],
            "human_physical_evidence_accepted":0,
        },
        "human_dispositions_only":list(DISPOSITIONS),
        "human_acceptance_protocol":{
            "documentary_decision_only":True,
            "independent_host_evidence_required":True,
            "proof_of_execution_unavailable":True,
            "chronology_not_verified":True,
            "b11_session_link_not_verified":True,
            "private_source_and_save_paths_not_accepted":True,
            "never_authorize_runtime_from_report":True,
            "separate_future_authorization_required":True,
        },
        "windows_cases":43,"android_cases":1,"native_cases_total":44,
        "native_cases_completed":0,"native_cases_approved":0,
        "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
        "r07_complete":False,"r08_complete":False,"r09_complete":False,
        "physical_qa_preapproved":False,"sinnoh_playable":False,
        "may_run_game_exe":False,"may_run_joiplay":False,
        "may_start_windows_sandbox":False,"may_install_live_game":False,
        "auto_uploaded":False,"private_receipts_exported":False,
    }

def run(root=ROOT,*,workspace=False):
    root=Path(root)
    matrix=l02.l00.read_json(root,MATRIX,maxsize=65536)
    review=l02.run(root,workspace=workspace)
    return reconcile(matrix,review)

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if argv not in ([],["--workspace-reports"],["--help"],["-h"]):
        print("SINNOH_L03_BLOCKED: unsafe CLI arguments",file=sys.stderr)
        return 2
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-reports",action="store_true",
        help="read only explicitly provided fixed L00/L01 sanitized workspace JSON")
    args=parser.parse_args(argv)
    try:
        result=run(workspace=args.workspace_reports)
        print(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=True))
        if result["counts"]["dependency_blocked"] or result["counts"]["conflicting"]:
            return 2
        return 0
    except (OSError,ValueError,KeyError,IndexError,TypeError,AttributeError,UnicodeError):
        print("SINNOH_L03_BLOCKED: invalid documentary protocol or sanitized evidence",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
