#!/usr/bin/env python3
"""L20: fail-closed reconciliation of public Git-only Sinnoh evidence requests.

No access to local installs, Game.exe, ROMs, saves, Windows Sandbox or JoiPlay.
Git SHA-1 anchors prove only public blob bytes, NOT physical provenance, licenses,
authorizations, independent reviews or native QA execution.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l19_consolidation as l19

REPORT = "data/regions/sinnoh-l20-public-reconciliation.json"
MIRROR = "site/public/data/sinnoh-l20-public-reconciliation.json"
SOURCE = l19.REPORT
SOURCE_MIRROR = l19.MIRROR
L19_MERGE = "54bbb63a7f2f7a74a26ce8dbc61d52793a27315d"
L19_BLOB = "ff9f86e14cd28f7960331580d85e2b10d99b8240"
FIELDS = (
    "order", "request_id", "subject_id", "kind", "platform", "priority",
    "priority_label", "gap_types", "exit_criteria_codes",
    "prerequisite_blocker_ids", "linked_l04_criterion_ids",
    "documentary_dependency_request_ids", "documentary_dependency_count",
    "anonymous_bookkeeping_slot", "review_state", "review_gap_status",
    "status", "readiness", "independent_review_approved", "exit_criteria_met",
    "native_qa_executed", "physical_evidence_accepted",
    "assigned_reviewer", "anonymous_identity_assigned",
)
COUNTS = {
    "reconciled_requests": 88, "records_matched": 88,
    "records_added": 0, "records_removed": 0,
    "identity_drift": 0, "priority_drift": 0, "platform_drift": 0,
    "status_drift": 0, "approval_drift": 0, "open_gaps": 88,
    "closed_gaps": 0, "pending": 88, "blocked": 88,
    "documentary_links": 1084, "case_to_criterion": 846,
    "case_to_blocker": 218, "criterion_to_blocker": 20,
    "anonymous_unassigned": 18, "local_reports_received": 0,
    "local_reports_required": 5, "human_approved": 0,
    "human_required": 20, "native_executed": 0, "native_approved": 0,
    "native_required": 44, "phase_bcd_completed": 0,
    "phase_bcd_required": 13, "windows_pending": 43,
    "android_pending": 1, "exit_criteria_met": 0,
    "physical_evidence_accepted": 0,
}
POLICY = {
    "public_documentation_only": True, "not_a_human_review": True,
    "not_a_native_qa_result": True, "no_private_uploads": True,
    "no_reviewer_identity": True, "anonymous_slots_unassigned": True,
    "R07_mapids_pending": True, "R08_rights_pending": True,
    "R09_global_only": True, "no_case_edges_to_R09": True,
    "android_no_windows_approval_inheritance": True,
    "B11_watch_unchanged_not_global_save_isolation": True,
    "no_game_exe": True, "no_windows_sandbox": True,
    "no_joiplay": True, "no_saves": True, "no_private_files": True,
    "sinnoh_playable": False,
}

def blocked():
    raise ValueError("SINNOH_L20_BLOCKED: public reconciliation invariant violated")

def same(a, b):
    # JSON-type-sensitive comparison: bool != int, including false != 0.
    return json.dumps(a, ensure_ascii=True, sort_keys=True, separators=(",", ":")) == json.dumps(
        b, ensure_ascii=True, sort_keys=True, separators=(",", ":"))

def blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\x00" + data).hexdigest()

def check_l19_git_blobs(root=ROOT):
    for rel in (SOURCE, SOURCE_MIRROR):
        p = Path(root) / rel
        if p.is_symlink() or not p.is_file():
            blocked()
        data = p.read_bytes()
        if len(data) > 225000 or blob_sha(data) != L19_BLOB:
            blocked()
    return True

def expected_report(source):
    return {
        "schema": 1, "region": "SINNOH", "stage": "L20", "version": 1,
        "status": "PUBLIC_METADATA_RECONCILED_88_GAPS_OPEN_NO_NATIVE_QA",
        "mode": "PUBLIC_READ_ONLY_RECONCILIATION_NO_PHYSICAL_EVIDENCE",
        "source": {"stage": "L19", "path": SOURCE, "git_blob_sha1": L19_BLOB},
        "baseline_commits": {**source["baseline_commits"], "L19": L19_MERGE},
        "public_sources": [*source["public_sources"],
            {"stage": "L19", "path": SOURCE, "git_blob_sha1": L19_BLOB}],
        "counts": dict(COUNTS),
        "priority_summary": [
            {"priority": p,
             "open": sum(x["priority"] == p for x in source["records"]),
             "approved": 0} for p in range(5)],
        "kind_summary": list(source["kind_summary"]),
        "edge_summary": dict(source["edge_summary"]),
        "gates": dict(source["gates"]),
        "platform_partition": list(source["platform_partition"]),
        "global_r09": dict(source["global_r09"]),
        "records": [
            {**{field: x[field] for field in FIELDS},
             "correspondence": "MATCHED_L19_PUBLIC_METADATA_ONLY",
             "gap_open": True}
            for x in source["records"]],
        "policy": dict(POLICY),
    }

def audit(report, mirror, source, trusted_l19):
    try:
        if not same(source, trusted_l19):
            blocked()
        expected = expected_report(source)
        if not same(report, expected) or not same(mirror, expected):
            blocked()
        rows = report["records"]
        if (len(rows) != 88
            or [r["order"] for r in rows] != list(range(1, 89))
            or len({r["request_id"] for r in rows}) != 88
            or sum(r["documentary_dependency_count"] for r in rows) != 1084
            or sum(bool(r["anonymous_bookkeeping_slot"]) for r in rows) != 18
            or [(x["priority"], x["open"]) for x in report["priority_summary"]]
               != [(0, 6), (1, 5), (2, 20), (3, 13), (4, 44)]
            or sum(r["kind"] == "NATIVE_CASE" and r["platform"] == "windows"
                   for r in rows) != 43
            or sum(r["kind"] == "NATIVE_CASE" and r["platform"] == "android"
                   for r in rows) != 1
            or any(r["status"] != "PENDING" or r["readiness"] != "BLOCKED"
                   or r["review_state"] != "NOT_REVIEWED"
                   or r["review_gap_status"] != "OPEN_DOCUMENTARY_ONLY"
                   or r["correspondence"] != "MATCHED_L19_PUBLIC_METADATA_ONLY"
                   or r["gap_open"] is not True
                   or r["independent_review_approved"] is not False
                   or r["native_qa_executed"] is not False
                   or r["exit_criteria_met"] is not False
                   or r["physical_evidence_accepted"] is not False
                   or r["assigned_reviewer"] is not False
                   or r["anonymous_identity_assigned"] is not False
                   for r in rows)
            or any(r["documentary_dependency_count"] != 0
                   or r["documentary_dependency_request_ids"]
                   or r["linked_l04_criterion_ids"]
                   for r in rows if r["anonymous_bookkeeping_slot"])
            or any("R09" in r["prerequisite_blocker_ids"]
                   or "R09" in r["documentary_dependency_request_ids"]
                   for r in rows if r["kind"] != "GLOBAL_REGIONAL_GATE")
            or len([r for r in rows if r["kind"] == "GLOBAL_REGIONAL_GATE"]) != 1
            or any(r["prerequisite_blocker_ids"] != ["R09"]
                   or r["documentary_dependency_request_ids"] != []
                   or r["documentary_dependency_count"] != 0
                   for r in rows if r["kind"] == "GLOBAL_REGIONAL_GATE")
            or any(("B10" in r["prerequisite_blocker_ids"] or
                    "B11" in r["prerequisite_blocker_ids"])
                   for r in rows if r["kind"] == "NATIVE_CASE"
                   and r["platform"] == "android")
            or report["global_r09"]["case_ids"] != []
            or report["global_r09"]["documentary_dependency_request_ids"] != []
            or report["gates"]["r07"] != "PENDING"
            or report["gates"]["r08"] != "PENDING"
            or report["gates"]["r09"] != "PENDING"
            or report["counts"] != COUNTS or report["policy"] != POLICY):
            blocked()
        return {
            "stage": "L20",
            "status": "PUBLIC_METADATA_RECONCILIATION_AUDITED_ALL_BLOCKED",
            "requests_matched": 88, "gaps_open": 88, "gaps_closed": 0,
            "links": 1084, "anonymous_unassigned": 18,
            "local_reports_received": 0, "human_approved": 0,
            "native_executed": 0, "native_approved": 0,
            "windows_pending": 43, "android_pending": 1,
            "phase_bcd_completed": 0, "r07_pending": True,
            "r08_pending": True, "r09_pending": True,
            "sinnoh_playable": False,
            "baseline_commits": dict(expected["baseline_commits"]),
        }
    except (KeyError, IndexError, TypeError, AttributeError, ValueError):
        blocked()

def run(root=ROOT):
    root = Path(root)
    parent = l19.run(root)  # Recursively audits L19–L00/G12 contracts.
    if (parent.get("status") != "PUBLIC_GAP_CONSOLIDATION_AUDITED_ALL_BLOCKED"
        or parent.get("requests") != 88
        or parent.get("links") != 1084
        or parent.get("human_reviews") != 0
        or parent.get("native_executed") != 0
        or parent.get("sinnoh_playable") is not False):
        blocked()
    check_l19_git_blobs(root)
    reader = l19.l18.l17.l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
    l19_source = reader(root, SOURCE, maxsize=225000)
    l18_source = reader(root, l19.SOURCE, maxsize=210000)
    trusted = l19.expected_report(l18_source)
    for rel in (REPORT, MIRROR):
        p = root / rel
        if p.is_symlink() or not p.is_file() or p.stat().st_size > 225000:
            blocked()
    if (root / REPORT).read_bytes() != (root / MIRROR).read_bytes():
        blocked()
    return audit(
        reader(root, REPORT, maxsize=225000),
        reader(root, MIRROR, maxsize=225000),
        l19_source, trusted,
    )

def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args in (["--help"], ["-h"]):
        print(__doc__)
        return 0
    if args:
        print("SINNOH_L20_BLOCKED: no arbitrary paths or native commands", file=sys.stderr)
        return 2
    try:
        print(json.dumps(run(), ensure_ascii=True, sort_keys=True, indent=2))
        return 0
    except (ValueError, OSError, KeyError, IndexError, TypeError,
            AttributeError, UnicodeError):
        print("SINNOH_L20_BLOCKED: invalid public metadata or immutable baseline", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
