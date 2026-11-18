#!/usr/bin/env python3
"""Sinnoh L19 fail-closed public gap consolidation, without native QA.

Read only fixed public JSON checked into the Git repository. Git blob SHA-1
is a provenance anchor for repository bytes, NEVER an authorization, native
test result, physical-origin check, asset right, or save-isolation proof.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l18_review_gaps as l18

REPORT = "data/regions/sinnoh-l19-public-gap-consolidation.json"
MIRROR = "site/public/data/sinnoh-l19-public-gap-consolidation.json"
L18_MERGE = "38ff6e635287f84464e1371160f3a06ae8dba953"
L18_BLOB = "649e85b2daef7635d00e19201ad5f39cc43c5c90"
SOURCE = l18.REPORT
SOURCE_MIRROR = l18.MIRROR
SOURCE_LINKS = 1084
COUNTS = {
    "consolidated_requests": 88,
    "consolidated_pending": 88,
    "consolidated_blocked": 88,
    "consolidated_gaps_open": 88,
    "consolidated_gaps_closed": 0,
    "consolidated_links": 1084,
    "consolidated_anonymous_slots": 18,
    "consolidated_human_signoffs": 0,
    "consolidated_native_passes": 0,
    "consolidated_exit_criteria_met": 0,
    "consolidated_physical_evidence_accepted": 0,
}
POLICY = {
    "document_only": True,
    "comparison_does_not_approve_native_qa": True,
    "priorities_P0_P4_are_documentary_only": True,
    "public_links_are_not_physical_evidence": True,
    "r09_global_only_no_case_edges": True,
    "no_private_uploads": True,
    "no_private_reviewer_identity": True,
    "anonymous_slots_unassigned": True,
    "android_does_not_inherit_windows_b10_b11": True,
    "B11_watch_unchanged_is_not_global_save_isolation": True,
    "R07_mapids_not_authorized": True,
    "R08_asset_rights_not_approved": True,
    "no_game_exe": True, "no_windows_sandbox": True,
    "no_joiplay": True, "no_saves": True, "no_private_files": True,
    "sinnoh_playable": False,
}

def blocked():
    raise ValueError("SINNOH_L19_BLOCKED: public-only gap invariant violated")

def check_l18_git_blobs(root=ROOT):
    """Check both L18 public file and byte-identical portal mirror against Git."""
    root = Path(root)
    for rel in (SOURCE, SOURCE_MIRROR):
        p = root / rel
        if p.is_symlink() or not p.is_file():
            blocked()
        content = p.read_bytes()
        if len(content) > 210000:
            blocked()
        git = b"blob " + str(len(content)).encode("ascii") + b"\x00" + content
        if hashlib.sha1(git).hexdigest() != L18_BLOB:
            blocked()
    return True

def expected_report(source):
    """Construct exactly what L19 is allowed to report from audited L18."""
    summary = []
    for item in source["group_summary"]:
        summary.append({
            "kind": item["kind"], "requests": item["requests"],
            "pending": item["requests"], "blocked": item["blocked"],
            "documentary_edges": item["documentary_links"],
            "independent_signoffs": 0, "native_qa_passed": 0,
            "missing_reviews": item["requests"],
            "coverage": "PUBLIC_RECORD_MATCHED_EVIDENCE_MISSING",
        })
    records = []
    for x in source["records"]:
        records.append({
            "order": x["order"], "request_id": x["request_id"],
            "kind": x["kind"], "subject_id": x["subject_id"],
            "platform": x["platform"], "priority": x["priority"],
            "priority_label": x["priority_label"],
            "gap_types": list(x["gap_types"]),
            "next_documentary_step": x["next_documentary_step"],
            "exit_criteria_codes": list(x["exit_criteria_codes"]),
            "prerequisite_blocker_ids": list(x["prerequisite_blocker_ids"]),
            "linked_l04_criterion_ids": list(x["linked_l04_criterion_ids"]),
            "documentary_dependency_request_ids":
                list(x["documentary_dependency_request_ids"]),
            "documentary_dependency_count": x["documentary_dependency_count"],
            "anonymous_bookkeeping_slot": x["anonymous_bookkeeping_slot"],
            "public_coverage": "LINKS_DOCUMENTED_NOT_PHYSICAL_EVIDENCE",
            "missing_evidence": "INDEPENDENT_REVIEW_AND_NATIVE_QA_UNAVAILABLE",
            "review_state": "NOT_REVIEWED",
            "review_gap_status": "OPEN_DOCUMENTARY_ONLY",
            "status": "PENDING", "readiness": "BLOCKED",
            "independent_review_approved": False,
            "exit_criteria_met": False, "native_qa_executed": False,
            "physical_evidence_accepted": False,
            "assigned_reviewer": False, "anonymous_identity_assigned": False,
        })
    counts = dict(source["counts"])
    counts.update(COUNTS)
    return {
        "schema": 1, "region": "SINNOH", "stage": "L19", "version": 1,
        "status": "PUBLIC_GAP_CONSOLIDATION_VALID_METADATA_ALL_BLOCKED",
        "mode": "READ_ONLY_PUBLIC_GIT_DOCUMENTS_NO_NATIVE_QA",
        "baseline_commits":
            {**source["baseline_commits"], "L18": L18_MERGE},
        "public_sources": [
            *source["public_sources"],
            {"stage": "L18", "path": SOURCE, "git_blob_sha1": L18_BLOB},
        ],
        "counts": counts, "gates": dict(source["gates"]),
        "priority_rules": list(source["priority_rules"]),
        "edge_summary": {
            "case_to_criterion": 846, "case_to_blocker": 218,
            "criterion_to_blocker": 20, "total": 1084,
        },
        "gap_types_by_kind": [
            {"kind": x["kind"], "gap_types": list(x["gap_types"]),
             "next_documentary_step": x["next_documentary_step"]}
            for x in source["gap_templates"]
        ],
        "kind_summary": summary,
        "records": records,
        "platform_partition": [
            {**x, "documentary_coverage": "PUBLIC_ONLY",
             "review_complete": False, "native_authorization": False}
            for x in source["platform_partition"]
        ],
        "global_r09": {
            **source["global_r09"],
            "case_ids": [], "documentary_dependency_request_ids": [],
            "signoff": False, "review_complete": False,
        },
        "policy": dict(POLICY),
    }

def audit(report, mirror, source, source_mirror, l17index, l17mirror,
          l16matrix, parent_l16):
    # A direct in-memory invocation must fail-closed on forged upstream data,
    # not merely trust the L18 status label.
    previous = l18.audit(source, source_mirror, l17index, l17mirror,
                         l16matrix, parent_l16)
    if (previous.get("status") != "PUBLIC_REVIEW_GAPS_VALID_ALL_OPEN_NO_REAL_QA"
        or previous.get("requests") != 88
        or previous.get("review_gaps_open") != 88
        or previous.get("review_gaps_closed") != 0
        or previous.get("independent_reviews_completed") != 0
        or previous.get("exit_criteria_met") != 0
        or previous.get("links") != 1084
        or previous.get("anonymous_slots") != 18
        or previous.get("human_approved") != 0
        or previous.get("native_executed") != 0
        or previous.get("native_approved") != 0
        or previous.get("r07_pending") is not True
        or previous.get("r08_pending") is not True
        or previous.get("r09_pending") is not True
        or previous.get("r09_global_only") is not True
        or previous.get("no_private_uploads") is not True
        or previous.get("no_native_authorization") is not True
        or previous.get("sinnoh_playable") is not False):
        blocked()
    try:
        expected = expected_report(source)
        same = l18.l17.l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.same
        if not same(report, expected) or not same(mirror, expected):
            blocked()
        rows = report["records"]
        if (len(rows) != 88
            or len({x["request_id"] for x in rows}) != 88
            or sum(x["documentary_dependency_count"] for x in rows) != 1084
            or sum(x["anonymous_bookkeeping_slot"] for x in rows) != 18
            or any(x["review_state"] != "NOT_REVIEWED"
                   or x["status"] != "PENDING" or x["readiness"] != "BLOCKED"
                   or x["review_gap_status"] != "OPEN_DOCUMENTARY_ONLY"
                   or x["independent_review_approved"] is not False
                   or x["exit_criteria_met"] is not False
                   or x["native_qa_executed"] is not False
                   or x["physical_evidence_accepted"] is not False
                   or x["assigned_reviewer"] is not False
                   or x["anonymous_identity_assigned"] is not False
                   for x in rows)
            or any(x["documentary_dependency_count"] != 0
                   or x["linked_l04_criterion_ids"] != []
                   for x in rows if x["anonymous_bookkeeping_slot"])
            or any("R09" in x["prerequisite_blocker_ids"]
                   for x in rows if x["kind"] == "NATIVE_CASE")
            or any("B10" in x["prerequisite_blocker_ids"]
                   or "B11" in x["prerequisite_blocker_ids"]
                   for x in rows if x["kind"] == "NATIVE_CASE"
                   and x["platform"] == "android")
            or report["global_r09"]["case_ids"] != []
            or report["global_r09"]["documentary_dependency_request_ids"] != []
            or report["counts"]["consolidated_gaps_closed"] != 0):
            blocked()
    except (KeyError, IndexError, TypeError, AttributeError):
        blocked()
    return {
        "schema": 1, "region": "SINNOH", "stage": "L19",
        "status": "PUBLIC_GAP_CONSOLIDATION_AUDITED_ALL_BLOCKED",
        "baseline_commits": dict(expected["baseline_commits"]),
        "public_sources": list(expected["public_sources"]),
        "requests": 88, "pending": 88, "blocked": 88,
        "gaps_open": 88, "gaps_closed": 0,
        "human_reviews": 0, "exit_criteria_met": 0,
        "links": 1084, "case_to_criterion_links": 846,
        "case_to_blocker_links": 218, "criterion_to_blocker_links": 20,
        "anonymous_slots": 18, "local_reports_received": 0,
        "human_approved": 0, "native_executed": 0,
        "native_approved": 0, "phase_bcd_approved": 0,
        "phase_bcd_total": 13, "windows_native_pending": 43,
        "android_native_pending": 1,
        "r07_pending": True, "r08_pending": True,
        "r09_pending": True, "r09_global_only": True,
        "no_native_authorization": True, "no_private_uploads": True,
        "sinnoh_playable": False,
    }

def run(root=ROOT):
    root = Path(root)
    # Includes fail-closed checks for all prior L18–L00/G12 public contracts.
    parent = l18.l17.l16.run(root)
    check_l18_git_blobs(root)
    read = l18.l17.l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
    return audit(
        read(root, REPORT, maxsize=225000),
        read(root, MIRROR, maxsize=225000),
        read(root, l18.REPORT, maxsize=210000),
        read(root, l18.MIRROR, maxsize=210000),
        read(root, l18.l17.INDEX, maxsize=195000),
        read(root, l18.l17.MIRROR, maxsize=195000),
        read(root, l18.l17.l16.MATRIX, maxsize=185000),
        parent,
    )

def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ["-h"], ["--help"]):
        print("SINNOH_L19_BLOCKED: no arbitrary paths accepted", file=sys.stderr)
        return 2
    if args:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), ensure_ascii=True, sort_keys=True, indent=2))
        return 0
    except (ValueError, OSError, KeyError, IndexError, TypeError,
            AttributeError, UnicodeError):
        print("SINNOH_L19_BLOCKED: invalid public metadata or provenance", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
