#!/usr/bin/env python3
"""Sinnoh L04: fixed offline human-provenance checklist, NEVER an authorization.

Default input: repository's public L00→L03 contracts, no user-PC access.
Optional --workspace-reports: ONLY the existing fixed L00 sanitized JSON.
No Game.exe, WSB guest, JoiPlay, asset, save, private baseline, or uploader.
The output contains only literal reviewed checklist text and fixed statuses.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_l03_matrix as l03

CHECKLIST="data/regions/sinnoh-l04-independent-review-checklist.json"
# Intentional duplicate of the public manifest's expected *immutable* policy.
# This prevents a changed manifest from authorizing approval by editing itself.
EXPECTED_HEADER=json.loads(r'''{"schema":1,"region":"SINNOH","stage":"L04","version":1,"status":"HUMAN_PROVENANCE_CHECKLIST_NO_RUNTIME_AUTHORIZATION","source_matrix":"data/regions/sinnoh-l03-documentary-review.json","source_auditor":"scripts/regions/audit_sinnoh_l03_matrix.py","allowed_documentary_actions":["REVIEW","REQUEST_NEW_SANITIZED_REPORT","BLOCK","SCHEDULE_DOCUMENTARY_ANALYSIS"],"review_states":["NOT_REVIEWED","NEEDS_INDEPENDENT_PRIVATE_REVIEW","CONFLICTING_OR_INCOMPLETE"],"independent_host_authority_required":true,"raw_native_evidence_not_in_github":true,"no_unsigned_or_self_reported_approval":true,"no_cli_execution_tokens":true,"no_auto_qa_scheduling":true,"no_upload":true,"verified_timestamps_available":false,"b11_session_correlation_publicly_verifiable":false,"global_save_isolation_proven":false,"asset_rights_approved":false,"map_ids_reserved":false,"native_cases_total":44,"windows_cases":43,"android_cases":1,"passed_native_cases":0,"phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,"r07_complete":false,"r08_complete":false,"r09_complete":false,"game_exe_tested":false,"joiplay_tested":false,"windows_sandbox_executed":false,"can_launch_game":false,"can_install_region":false,"sinnoh_playable":false}''')
EXPECTED_ROWS=json.loads(r'''[{"stage":"B09","documentary_kind":"CLONE_PROVENANCE","depends_on":[],"criteria":[{"id":"B09_ORIGIN","requirement":"Check independent, authorized provenance of source game and donor materials"},{"id":"B09_CLONE","requirement":"Compare physically observed clone inventory against the declared B09 count and SHA outside GitHub"},{"id":"B09_ASSETS","requirement":"Review ownership and redistribution restrictions of the individual staged assets"},{"id":"B09_RECEIPT","requirement":"Compare local receipt with dry-run and native clone in a separate human session"}]},{"stage":"B10","documentary_kind":"WSB_CONFIGURATION","depends_on":["B09"],"criteria":[{"id":"B10_LINK","requirement":"Independently confirm that the B10 configuration belongs to the reviewed B09 clone"},{"id":"B10_READONLY","requirement":"Inspect WSB mount paths and read-only flags locally without uploading those paths"},{"id":"B10_OFFLINE","requirement":"Inspect disabled network, clipboard, autostart and guest mapping on the actual host"},{"id":"B10_PLATFORM","requirement":"Verify host Windows Sandbox compatibility and isolation separately from a config JSON"}]},{"stage":"B11","documentary_kind":"LIMITED_SAVE_SCOPE","depends_on":["B09","B10"],"criteria":[{"id":"B11_SESSION","requirement":"Correlate B11 with its B10 guest session outside the public repository"},{"id":"B11_SCOPE","requirement":"Review actual engine save directories and completeness of the monitored scopes locally"},{"id":"B11_DIFFERENCE","requirement":"Inspect before/after results and any differences without publishing save identifiers"},{"id":"B11_LIMIT","requirement":"Explicitly reject watch_unchanged as proof of global save isolation"}]},{"stage":"R07","documentary_kind":"REGIONAL_MAPID_RESERVATIONS","depends_on":[],"criteria":[{"id":"R07_NATIVE","requirement":"Verify physical MapInfos and ownership of occupied native MapIDs"},{"id":"R07_REGIONS","requirement":"Confirm future regional reservations including Kanto, Johto, Hoenn and planned regions"},{"id":"R07_CONFLICT","requirement":"Independently inspect conflicting and candidate map IDs before approving any allocation"},{"id":"R07_TOPOLOGY","requirement":"Verify nine symbolic Twinleaf bindings and sixteen real transfers in the isolated clone"}]},{"stage":"R08","documentary_kind":"ASSET_RIGHTS_AND_BINDINGS","depends_on":[],"criteria":[{"id":"R08_LICENSE","requirement":"Review per-asset source provenance and express permission/redistribution scope"},{"id":"R08_GRAPHICS","requirement":"Inspect fourteen real PNGs and renderer compatibility without uploading copyrighted files"},{"id":"R08_EVENTS","requirement":"Check physical maps, handlers, collision and warp connections after rights approval"},{"id":"R08_PBS","requirement":"Verify real authored PBS compilation and Berry/Rowan event contracts in isolated QA"}]}]''')
STAGES=tuple(x["stage"] for x in EXPECTED_ROWS)
CRITERIA_STATES=tuple(EXPECTED_HEADER["review_states"])
ACTIONS=tuple(EXPECTED_HEADER["allowed_documentary_actions"])
L03_FLAGS_FALSE=(
    "physical_qa_preapproved","sinnoh_playable",
    "may_run_game_exe","may_run_joiplay",
    "may_start_windows_sandbox","may_install_live_game",
    "auto_uploaded","private_receipts_exported",
    "r07_complete","r08_complete","r09_complete",
)

def blocked(reason):
    # Error strings MUST NOT echo values, paths, SHA or evidence.
    raise ValueError("SINNOH_L04_BLOCKED: "+reason)

def validate_checklist(doc):
    if type(doc) is not dict or set(doc)!=set(EXPECTED_HEADER)|{"rows"}:
        blocked("checklist schema or fields changed")
    for key,val in EXPECTED_HEADER.items():
        if type(doc[key]) is not type(val) or doc[key]!=val:
            blocked("checklist non-approval policy changed")
    rows=doc["rows"]
    if type(rows) is not list or len(rows)!=len(EXPECTED_ROWS):
        blocked("source checklist rows missing or duplicated")
    for row,expected in zip(rows,EXPECTED_ROWS):
        if type(row) is not dict or set(row)!={
            "stage","documentary_kind","depends_on","criteria"
        }:
            blocked("checklist source changed")
        for key in ("stage","documentary_kind","depends_on"):
            if row[key]!=expected[key]:
                blocked("source stage, type or dependency modified")
        if type(row["criteria"]) is not list or len(row["criteria"])!=len(expected["criteria"]):
            blocked("human criteria count changed")
        for criterion,target in zip(row["criteria"],expected["criteria"]):
            if type(criterion) is not dict or set(criterion)!={
                "id","requirement","review_state","independent_evidence_present",
                "local_human_signoff"
            }:
                blocked("unexpected private fields in human checklist")
            if (criterion["id"]!=target["id"] or
                criterion["requirement"]!=target["requirement"] or
                criterion["review_state"]!="NOT_REVIEWED" or
                criterion["independent_evidence_present"] is not False or
                criterion["local_human_signoff"] is not False):
                blocked("human approval, review status or criterion altered")
    return True

def validate_l03_result(doc,matrix):
    l03.validate_manifest(matrix)
    if (type(doc) is not dict or doc.get("schema")!=1
        or doc.get("region")!="SINNOH" or doc.get("stage")!="L03"
        or doc.get("version")!=1
        or doc.get("status")!="DOCUMENTARY_HANDOFF_REQUIRES_SEPARATE_HUMAN_REVIEW"
        or doc.get("mode")!="OFFLINE_FIXED_METADATA_ONLY"):
        blocked("L03 output is not a trusted documentary format")
    for k in L03_FLAGS_FALSE:
        if doc.get(k) is not False:
            blocked("L03 claims unsupported native readiness")
    for k,v in (("windows_cases",43),("android_cases",1),
                ("native_cases_total",44),("native_cases_completed",0),
                ("native_cases_approved",0),("phase_b_approved",0),
                ("phase_c_approved",0),("phase_d_approved",0)):
        if type(doc.get(k)) is not int or doc[k]!=v:
            blocked("native case count or approval was forged")
    counts=doc.get("counts")
    if (type(counts) is not dict or set(counts)!={
        "missing","self_reported_unverified","dependency_blocked",
        "conflicting","human_physical_evidence_accepted"
    } or type(counts["human_physical_evidence_accepted"]) is not int
        or counts["human_physical_evidence_accepted"]!=0
        or any(type(x) is not int or not 0<=x<=5 for x in counts.values())
        or sum(counts[x] for x in ("missing","self_reported_unverified",
                                  "dependency_blocked","conflicting"))!=5):
        blocked("L03 documentary summary is internally inconsistent")
    protocol=doc.get("human_acceptance_protocol")
    if (type(protocol) is not dict or set(protocol)!={
        "documentary_decision_only","independent_host_evidence_required",
        "proof_of_execution_unavailable","chronology_not_verified",
        "b11_session_link_not_verified",
        "private_source_and_save_paths_not_accepted",
        "never_authorize_runtime_from_report",
        "separate_future_authorization_required",
    } or any(v is not True for v in protocol.values())):
        blocked("human independent evidence protocol changed")
    if doc.get("human_dispositions_only")!=l03.DISPOSITIONS:
        blocked("L03 disposition policy modified")
    stage_rows=doc.get("rows")
    if (type(stage_rows) is not list or len(stage_rows)!=len(STAGES)
        or [r.get("stage") if type(r) is dict else None for r in stage_rows]!=list(STAGES)):
        blocked("L03 stages missing or out of order")
    stat_count={s:0 for s in l03.STATUSES}
    for row,origin in zip(stage_rows,matrix["rows"]):
        if (type(row) is not dict or set(row)!={
            "stage","status","safe_next_action","depends_on",
            "documentary_review_kind","required_separate_human_checks",
            "self_report_authenticity_verified","physical_acceptance_decided",
            "native_qa_allowed"
        }):
            blocked("L03 row includes arbitrary private data")
        status=row["status"]
        if status not in stat_count:
            blocked("L03 status unrecognized")
        stat_count[status]+=1
        if (row["safe_next_action"]!=l03.ACTIONS[status]
            or row["depends_on"]!=origin["depends_on"]
            or row["documentary_review_kind"]!=origin["review_kind"]
            or row["required_separate_human_checks"]!=origin["criteria"]
            or row["self_report_authenticity_verified"] is not False
            or row["physical_acceptance_decided"] is not False
            or row["native_qa_allowed"] is not False):
            blocked("L03 stage evidence or native gate was altered")
    for status,field in (
        (l03.l02.STATUS_MISSING,"missing"),
        (l03.l02.STATUS_UNVERIFIED,"self_reported_unverified"),
        (l03.l02.STATUS_DEPENDENCY,"dependency_blocked"),
        (l03.l02.STATUS_BLOCKED,"conflicting"),
    ):
        if stat_count[status]!=counts[field]:
            blocked("L03 counts do not match source rows")
    if counts["conflicting"]:
        expected="BLOCKED_CONFLICTING_OR_UNSAFE_REPORTS"
    elif counts["dependency_blocked"]:
        expected="BLOCKED_MISSING_CHAIN_PREREQUISITES"
    elif counts["missing"]:
        expected="INCOMPLETE_DOCUMENTARY_HANDOFF"
    else:
        expected="DOCUMENTARY_REVIEW_ONLY_NATIVE_APPROVAL_PENDING"
    if doc.get("source_documentary_status")!=expected:
        blocked("L03 global documentary state is contradictory")
    return True

def audit(manifest,matrix,l03_report):
    validate_checklist(manifest)
    validate_l03_result(l03_report,matrix)
    return {
        "schema":1,"region":"SINNOH","stage":"L04","version":1,
        "status":"HUMAN_REVIEW_NOT_STARTED_NO_NATIVE_AUTHORIZATION",
        "mode":"OFFLINE_DOCUMENTARY_PROTOCOL_ONLY",
        "documentary_source_status":l03_report["source_documentary_status"],
        "human_decisions_recorded":0,
        "human_evidence_independently_authenticated":0,
        "criteria_total":sum(len(x["criteria"]) for x in EXPECTED_ROWS),
        "criteria_reviewed":0,
        "source_rows":[{
            "stage":row["stage"],
            "source_status":s["status"],
            "documentary_action":s["safe_next_action"],
            "criteria":[{"id":item["id"],"state":"NOT_REVIEWED",
                         "external_human_review_required":True}
                        for item in row["criteria"]],
            "independent_proof_confirmed":False,
            "physical_readiness_approved":False,
            "runtime_permission":False,
        } for row,s in zip(EXPECTED_ROWS,l03_report["rows"])],
        "independent_human_protocol":{
            "human_decisions_allowed":list(ACTIONS),
            "external_source_review_required":True,
            "physical_host_evidence_cannot_be_substituted_by_JSON":True,
            "B09_clone_origin_needs_review":True,
            "B10_guest_execution_unverified":True,
            "B11_global_save_coverage_unproven":True,
            "R07_mapids_unreserved":True,
            "R08_asset_rights_not_approved":True,
            "native_qa_authorization_requires_distinct_future_process":True,
            "no_authorization_code_or_token_issued":True,
        },
        "native_cases_total":44,"windows_cases":43,"android_cases":1,
        "native_cases_completed":0,"native_cases_approved":0,
        "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
        "r07_complete":False,"r08_complete":False,"r09_complete":False,
        "sinnoh_playable":False,"may_launch_game_exe":False,
        "may_launch_joiplay":False,"may_start_windows_sandbox":False,
        "may_install_live_game":False,"auto_uploaded":False,
    }

def run(root=ROOT,*,workspace=False):
    root=Path(root)
    manifest=l03.l02.l00.read_json(root,CHECKLIST,maxsize=65536)
    matrix=l03.l02.l00.read_json(root,l03.MATRIX,maxsize=65536)
    source=l03.run(root,workspace=workspace)
    return audit(manifest,matrix,source)

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if argv not in ([],["--workspace-reports"],["--help"],["-h"]):
        print("SINNOH_L04_BLOCKED: unsafe option",file=sys.stderr)
        return 2
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace-reports",action="store_true",
                   help="read only manually supplied, fixed L00 sanitised JSON")
    args=p.parse_args(argv)
    try:
        print(json.dumps(run(workspace=args.workspace_reports),
                         sort_keys=True,ensure_ascii=True,indent=2))
        return 0
    except (ValueError,OSError,KeyError,TypeError,IndexError,AttributeError,UnicodeError):
        print("SINNOH_L04_BLOCKED: invalid versioned protocol or sanitized source",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
