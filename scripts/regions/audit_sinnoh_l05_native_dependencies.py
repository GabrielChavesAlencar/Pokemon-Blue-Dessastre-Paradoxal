#!/usr/bin/env python3
"""Sinnoh L05: strict CH20/G12 44-case vs L04 20-criterion DOCUMENTARY audit.

Works only on repository contracts. Optional --workspace-reports reads ONLY
the fixed L00/L01 sanitized JSON through L04 (never a custom path). No
game executable, Sandbox, JoiPlay, save, map, PNG, asset or network is used.
A matching JSON is NOT proof of physical integrity or permission to run QA.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_l04_human_review as l04

MATRIX="data/regions/sinnoh-l05-native-case-dependencies.json"
G12=l04.l03.l02.l00.g12
HANDOFF=G12.HANDOFF
KIND_EXTRA={
    "starter":("R07_TOPOLOGY","R08_EVENTS","R08_PBS"),
    "barry":("R07_TOPOLOGY","R08_EVENTS","R08_PBS"),
    "save_reload":("R08_EVENTS",),
    "warp":("R07_TOPOLOGY","R08_EVENTS"),
    "npc":("R07_TOPOLOGY","R08_EVENTS","R08_PBS"),
    "regression":("R07_TOPOLOGY","R08_EVENTS"),
    "android":(),
}
WINDOWS_BASE=(
    "B09_ORIGIN","B09_CLONE","B09_ASSETS","B09_RECEIPT",
    "B10_LINK","B10_READONLY","B10_OFFLINE","B10_PLATFORM",
    "B11_SESSION","B11_SCOPE","B11_DIFFERENCE","B11_LIMIT",
    "R07_NATIVE","R07_REGIONS","R07_CONFLICT",
    "R08_LICENSE","R08_GRAPHICS",
)
ANDROID_BASE=(
    "B09_ORIGIN","B09_CLONE","B09_ASSETS","B09_RECEIPT",
    "R07_NATIVE","R07_REGIONS","R07_CONFLICT","R07_TOPOLOGY",
    "R08_LICENSE","R08_GRAPHICS","R08_EVENTS","R08_PBS",
)
KINDS={"starter":3,"barry":12,"save_reload":3,"warp":16,
       "npc":5,"regression":4,"android":1}
EXPECTED_FIELDS={
    "schema","region","stage","version","status",
    "source_l04","source_g12","expected_criteria_ids",
    "criteria_total","criteria_reviewed","native_cases_total",
    "windows_cases","android_cases","native_cases_completed",
    "native_cases_approved","phase_b_approved","phase_c_approved",
    "phase_d_approved","r07_complete","r08_complete","r09_complete",
    "sinnoh_playable","auto_upload","can_execute_windows_qa",
    "can_execute_android_qa","can_install_live_game",
    "b11_session_independently_proven","global_save_isolation_proven",
    "asset_rights_approved","mapids_reserved","rows",
}
ROW_FIELDS={
    "case_id","kind","platform","required_criteria_ids",
    "blocking_stages","review_state","native_status",
    "native_evidence_accepted","independent_criteria_satisfied",
    "native_execution_authorized","platform_gate",
}
FALSE_FIELDS=(
    "r07_complete","r08_complete","r09_complete","sinnoh_playable",
    "auto_upload","can_execute_windows_qa","can_execute_android_qa",
    "can_install_live_game","b11_session_independently_proven",
    "global_save_isolation_proven","asset_rights_approved",
    "mapids_reserved",
)
COUNTS={"starter":3,"barry":12,"save_reload":3,"warp":16,
        "npc":5,"regression":4,"android":1}
DECLARATION="DOCUMENTARY_DEPENDENCIES_DEFINED_NATIVE_QA_NOT_AUTHORIZED"

def blocked(reason):
    # Never interpolate report values or file paths into errors.
    raise ValueError("SINNOH_L05_BLOCKED: "+reason)

def criterion_ids(l04_checklist):
    # Preserve L04 fail-closed behavior while exposing only the L05 safe code.
    # Never echo source values or nested validator errors in CLI or output.
    try:
        l04.validate_checklist(l04_checklist)
    except (ValueError,TypeError,KeyError,IndexError,AttributeError):
        blocked("L04 human criterion contract invalid")
    return [criterion["id"] for stage in l04_checklist["rows"]
            for criterion in stage["criteria"]]

def criteria_for(kind,platform):
    if kind not in KIND_EXTRA or platform not in ("windows","android"):
        blocked("native category or platform is unknown")
    if (kind=="android")!=(platform=="android"):
        blocked("Android case must remain Android-only")
    if kind=="android":
        return list(ANDROID_BASE)
    return list(WINDOWS_BASE+KIND_EXTRA[kind])

def expected_stages(criteria):
    return list(dict.fromkeys(c.split("_")[0] for c in criteria))

def check_manifest(matrix,checklist,handoff):
    if type(matrix) is not dict or set(matrix)!=EXPECTED_FIELDS:
        blocked("matrix fields missing or unauthorized")
    fixed={"schema":1,"region":"SINNOH","stage":"L05","version":1,
           "status":DECLARATION,
           "source_l04":l04.CHECKLIST,"source_g12":HANDOFF}
    for key,value in fixed.items():
        if type(matrix[key]) is not type(value) or matrix[key]!=value:
            blocked("matrix origin or version has changed")
    for key,value in (
        ("criteria_total",20),("criteria_reviewed",0),
        ("native_cases_total",44),("windows_cases",43),
        ("android_cases",1),("native_cases_completed",0),
        ("native_cases_approved",0),("phase_b_approved",0),
        ("phase_c_approved",0),("phase_d_approved",0),
    ):
        if type(matrix[key]) is not int or matrix[key]!=value:
            blocked("native case or human progress was forged")
    if any(matrix[key] is not False for key in FALSE_FIELDS):
        blocked("runtime, rights or safety claim forbidden")
    expected_ids=criterion_ids(checklist)
    if (len(expected_ids)!=20 or len(set(expected_ids))!=20
        or type(matrix["expected_criteria_ids"]) is not list
        or matrix["expected_criteria_ids"]!=expected_ids):
        blocked("L04 criterion IDs missing, repeated or altered")
    if (type(handoff) is not dict or handoff.get("stage")!="G12"
        or handoff.get("status")!="GITHUB_HANDOFF_ONLY_NATIVE_QA_NOT_STARTED"
        or handoff.get("total_cases")!=44
        or handoff.get("windows_cases")!=43
        or handoff.get("android_cases")!=1
        or handoff.get("completed_native_cases")!=0
        or handoff.get("manually_reviewed_cases")!=0
        or any(handoff.get("phase_"+p+"_approved")!=0 for p in ("b","c","d"))
        or any(handoff.get("r"+r+"_complete") is not False
               for r in ("07","08","09"))
        or handoff.get("can_launch_game_now") is not False
        or handoff.get("can_install_live_game") is not False):
        blocked("G12 native acceptance or handoff contract has drifted")
    original=handoff.get("cases")
    rows=matrix["rows"]
    if (type(original) is not list or len(original)!=44
        or type(rows) is not list or len(rows)!=44):
        blocked("native case matrix must contain exactly 44 rows")
    if (len({x.get("id") for x in original if type(x) is dict})!=44
        or len({x.get("case_id") for x in rows if type(x) is dict})!=44):
        blocked("native case ID duplication or missing ID")
    if Counter(x.get("kind") for x in original)!=KINDS:
        blocked("G12 kind distribution unexpectedly changed")
    union=set()
    for i,(source,entry) in enumerate(zip(original,rows)):
        if type(source) is not dict or type(entry) is not dict or set(entry)!=ROW_FIELDS:
            blocked("native row structure contains unexpected fields")
        if (entry["case_id"]!=source["id"]
            or entry["kind"]!=source["kind"]
            or entry["platform"]!=source["platform"]
            or source["native_status"]!="pending"
            or source["evidence"] is not None
            or source["observation"] is not None):
            blocked("G12 case ID, platform or evidence was changed")
        criteria=criteria_for(source["kind"],source["platform"])
        union.update(criteria)
        if (type(entry["required_criteria_ids"]) is not list
            or entry["required_criteria_ids"]!=criteria
            or type(entry["blocking_stages"]) is not list
            or entry["blocking_stages"]!=expected_stages(criteria)):
            blocked("case-to-criterion mapping or blocked stages altered")
        if (entry["review_state"]!="DOCUMENTARY_DEPENDENCIES_NOT_REVIEWED"
            or entry["native_status"]!="pending"
            or entry["native_evidence_accepted"] is not False
            or entry["independent_criteria_satisfied"] is not False
            or entry["native_execution_authorized"] is not False):
            blocked("case falsely marked reviewed or executable")
        platform_gate=("ANDROID_DEVICE_QA_NOT_AUTHORIZED"
                       if source["platform"]=="android"
                       else "WINDOWS_ISOLATED_QA_NOT_AUTHORIZED")
        if entry["platform_gate"]!=platform_gate:
            blocked("case platform gate was altered")
    if union!=set(expected_ids):
        blocked("not all 20 L04 criteria are covered by 44 test dependencies")
    return True

def audit(matrix,checklist,handoff,l04_report,g12_report):
    check_manifest(matrix,checklist,handoff)
    if (type(g12_report) is not dict
        or g12_report.get("native_cases_total")!=44
        or g12_report.get("completed_native_cases")!=0
        or g12_report.get("evidence_accepted_cases")!=0
        or g12_report.get("game_exe_tested") is not False
        or g12_report.get("joiplay_tested") is not False):
        blocked("G12 reconciled runtime tests are not all pending")
    original=g12_report.get("native_case_matrix")
    if (type(original) is not list or len(original)!=44
        or [x.get("id") if type(x) is dict else None for x in original]
        !=[x["case_id"] for x in matrix["rows"]]
        or any(type(x) is not dict or x.get("status")!="pending"
               or x.get("evidence") is not None for x in original)):
        blocked("G12 CH20 case matrix was modified or claims evidence")
    if (type(l04_report) is not dict
        or l04_report.get("stage")!="L04"
        or l04_report.get("criteria_total")!=20
        or l04_report.get("criteria_reviewed")!=0
        or l04_report.get("human_decisions_recorded")!=0
        or l04_report.get("human_evidence_independently_authenticated")!=0
        or l04_report.get("native_cases_total")!=44
        or l04_report.get("native_cases_approved")!=0
        or any(l04_report.get("phase_"+p+"_approved")!=0 for p in ("b","c","d"))
        or l04_report.get("may_launch_game_exe") is not False
        or l04_report.get("may_launch_joiplay") is not False
        or l04_report.get("may_start_windows_sandbox") is not False
        or l04_report.get("may_install_live_game") is not False):
        blocked("L04 independent human-review contract was forged")
    source=l04_report.get("source_rows")
    if (type(source) is not list or len(source)!=5
        or [s.get("stage") if type(s) is dict else None for s in source]
        !=[s["stage"] for s in checklist["rows"]]):
        blocked("L04 human-review rows are incomplete")
    stages={}
    for row in source:
        if (type(row) is not dict
            or row.get("independent_proof_confirmed") is not False
            or row.get("physical_readiness_approved") is not False
            or row.get("runtime_permission") is not False
            or type(row.get("criteria")) is not list
            or any(type(c) is not dict or c.get("state")!="NOT_REVIEWED"
                   or c.get("external_human_review_required") is not True
                   for c in row["criteria"])):
            blocked("L04 criterion or human approval has changed")
        stages[row["stage"]]=row["source_status"]
    status_counts=Counter(r["kind"] for r in matrix["rows"])
    return {
        "schema":1,"region":"SINNOH","stage":"L05",
        "status":"DOCUMENTARY_MATRIX_VALID_NATIVE_44_ALL_PENDING",
        "mode":"GITHUB_ONLY_HUMAN_READINESS_CROSSCHECK",
        "source_stage_states":stages,
        "criteria_total":20,"criteria_human_approved":0,
        "native_cases_total":44,"windows_cases":43,"android_cases":1,
        "native_cases_completed":0,"native_cases_approved":0,
        "cases_by_kind":dict(status_counts),
        "cases":[{
            "id":entry["case_id"],
            "kind":entry["kind"],
            "platform":entry["platform"],
            "required_criteria_ids":list(entry["required_criteria_ids"]),
            "blocked_by":list(entry["blocking_stages"]),
            "state":"NATIVE_QA_NOT_AUTHORIZED",
            "human_physical_evidence_accepted":False,
        } for entry in matrix["rows"]],
        "review_handoff":{
            "only_documentary_review_or_request_more_evidence":True,
            "receipt_shas_not_independent_authenticity":True,
            "b11_unchanged_is_not_global_save_isolation":True,
            "b11_private_session_link_not_authenticatable_publicly":True,
            "r07_reserved_ids_not_physically_verified":True,
            "r08_asset_rights_not_approved":True,
            "windows_guest_has_not_been_executed":True,
            "android_device_has_not_been_tested":True,
            "separate_human_gate_for_future_native_QA_required":True,
            "L05_documentary_is_not_android_local_gate_L05":True,
        },
        "r07_complete":False,"r08_complete":False,"r09_complete":False,
        "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
        "sinnoh_playable":False,"native_test_can_start":False,
        "may_run_game_exe":False,"may_run_joiplay":False,
        "may_start_windows_sandbox":False,"may_install_live_game":False,
        "auto_uploaded":False,
    }

def run(root=ROOT,*,workspace=False):
    root=Path(root)
    read=l04.l03.l02.l00.read_json
    manifest=read(root,MATRIX,maxsize=150000)
    checklist=read(root,l04.CHECKLIST,maxsize=65536)
    handoff=read(root,HANDOFF,maxsize=150000)
    l04_report=l04.run(root,workspace=workspace)
    g12_report=G12.run(root)
    return audit(manifest,checklist,handoff,l04_report,g12_report)

def main(argv=None):
    argv=list(sys.argv[1:] if argv is None else argv)
    if argv not in ([],["--workspace-reports"],["--help"],["-h"]):
        print("SINNOH_L05_BLOCKED: unsafe option",file=sys.stderr)
        return 2
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-reports",action="store_true",
        help="only read previously supplied fixed L00 sanitized reports, no arbitrary paths")
    args=parser.parse_args(argv)
    try:
        result=run(workspace=args.workspace_reports)
        print(json.dumps(result,sort_keys=True,indent=2,ensure_ascii=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError,IndexError,AttributeError,UnicodeError):
        print("SINNOH_L05_BLOCKED: invalid or unsafe public documentary dependency matrix",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
