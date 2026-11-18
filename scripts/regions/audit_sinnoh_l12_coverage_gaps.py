#!/usr/bin/env python3
"""Sinnoh L12: fail-closed gap report for public documentary vs missing real QA.

Audits fixed public JSON files only; never reads user/host paths, saves,
private evidence, Game.exe, Windows Sandbox, JoiPlay or authenticates assets.
Public Git blob integrity MUST NOT be described as physical human approval.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l11_traceability as l11

REPORT = "data/regions/sinnoh-l12-public-coverage-gaps.json"
MIRROR = "site/public/data/sinnoh-l12-public-coverage-gaps.json"
L11_MERGE = "9d901a0cf21aa2742f731ee387a51f945bac8a5d"
L11_BLOB = "c39f81867568fb95c65ca8113431e1db05919168"
COVERAGE_ROWS = (
    ("PUBLIC_METADATA_LINKS", "PUBLIC_GITHUB_ONLY", 1084, 1084, "DOCUMENTARY_LINKS_PRESENT_NO_PHYSICAL_APPROVAL"),
    ("INDEPENDENT_HUMAN_REVIEW", "HUMAN_EXTERNAL", 20, 0, "ALL_PENDING"),
    ("WINDOWS_NATIVE_QA", "WINDOWS", 43, 0, "NOT_EXECUTED"),
    ("ANDROID_NATIVE_QA", "ANDROID_JOIPLAY", 1, 0, "NOT_EXECUTED"),
    ("LOCAL_REPORTS", "PRIVATE_HOST_NOT_ACCESSED", 5, 0, "NOT_RECEIVED"),
    ("B_C_D_APPROVALS", "REGIONAL_GATES", 13, 0, "NOT_APPROVED"),
)


def blocked():
    raise ValueError("SINNOH_L12_BLOCKED: incomplete or forged public coverage/evidence")


def check_public_l11_blobs(root=ROOT):
    """Verify immutable L11 public JSON blobs by Git blob SHA-1; never user inputs."""
    for name in (l11.GRAPH, l11.MIRROR):
        p = Path(root) / name
        if p.is_symlink() or not p.is_file():
            blocked()
        payload = p.read_bytes()
        if len(payload) > 200000:
            blocked()
        blob = b"blob " + str(len(payload)).encode("ascii") + b"\x00" + payload
        if hashlib.sha1(blob).hexdigest() != L11_BLOB:
            blocked()
    return True


def expected_report(graph):
    cases = [{
        "id": row["id"], "kind": row["kind"], "platform": row["platform"],
        "criterion_ids": list(row["criteria_ids"]),
        "blocker_ids": list(row["blocker_ids"]),
        "documentary_criterion_links": len(row["criteria_ids"]),
        "documentary_blocker_links": len(row["blocker_ids"]),
        "documentary_link_status": "DOCUMENTARY_ONLY",
        "independent_human_review_state": "NOT_REVIEWED",
        "native_qa_state": "NOT_EXECUTED",
        "authorized_native_qa": False, "evidence_accepted": False,
        "pending_gates": list(row["blocker_ids"]),
    } for row in graph["case_nodes"]]
    criteria = [{
        "id": row["id"], "stage": row["stage"],
        "case_ids": list(row["case_ids"]),
        "documentary_links": len(row["case_ids"]),
        "documentary_link_state": "DOCUMENTARY_ONLY",
        "independent_review_state": "NOT_REVIEWED",
        "accepted_evidence": False, "human_signoff": False,
    } for row in graph["criterion_nodes"]]
    blockers = [{
        "id": row["id"], "scope": row["scope"],
        "case_ids": list(row["case_ids"]),
        "pending_cases": len(row["case_ids"]),
        "state": "PENDING", "approved": False,
    } for row in graph["blocker_nodes"]]
    counts = dict(graph["counts"])
    counts.update({
        "documentary_links_expected": 1084,
        "documentary_links_verified": 1084,
        "documentary_links_missing": 0,
        "local_reports_expected": 5, "local_reports_missing": 5,
        "human_evidence_expected": 20, "human_evidence_missing": 20,
        "native_tests_expected": 44, "native_tests_missing": 44,
        "phase_bcd_expected": 13, "phase_bcd_missing": 13,
    })
    integrity = {
        "case_ids_checked": 44, "criterion_ids_checked": 20,
        "blocker_ids_checked": 6,
        "case_to_criterion_links": 846,
        "case_to_blocker_links": 218,
        "criterion_to_blocker_links": 20,
        "links_checked": 1084,
        "missing_links": [], "added_links": [], "reordered_links": [],
        "case_id_drift": [], "criterion_id_drift": [], "platform_drift": [],
        "blocker_scope_drift": [], "differences_found": 0,
        "verified_public_metadata_only": True,
        "physical_source_authenticated": False,
        "human_review_completed": False, "native_qa_completed": False,
    }
    return {
        "schema": 1, "region": "SINNOH", "stage": "L12", "version": 1,
        "status": "DOCUMENTARY_COVERAGE_COMPLETE_PHYSICAL_EVIDENCE_MISSING",
        "mode": "PUBLIC_READ_ONLY_EVIDENCE_GAPS",
        "baseline_commits": {
            **graph["baseline_commits"], "L11": L11_MERGE
        },
        "source_l11": {"path": l11.GRAPH, "git_blob_sha1": L11_BLOB},
        "counts": counts,
        "gates": dict(graph["gates"]),
        "coverage_layers": [
            {"id": name, "scope": scope, "expected": expected,
             "observed": observed, "missing": expected - observed,
             "state": state, "native_evidence": False}
            for name, scope, expected, observed, state in COVERAGE_ROWS
        ],
        "case_handoff": cases, "criterion_handoff": criteria,
        "blockers": blockers,
        "global_r09": {
            "id": "R09", "scope": "GLOBAL_REGION_PENDING_NOT_CASE_GATE",
            "state": "PENDING", "case_ids": [],
            "not_a_new_case": True, "approved": False,
        },
        "platform_handoff": [{
            "platform": name,
            "case_ids": list(lane["case_ids"]),
            "documentary_cases": total, "native_cases_tested": 0,
            "native_cases_missing": total,
            "requires_windows_b10_b11": name == "windows",
            "shares_android_approval": False,
            "state": "PENDING",
        } for lane, (name, total) in zip(
            graph["platform_lanes"], (("windows", 43), ("android", 1))
        )],
        "documentary_integrity": integrity,
        "guardrails": {
            **graph["guarantees"],
            "local_reports_received": 0, "human_criteria_approved": 0,
            "native_cases_completed": 0, "bcd_approved": 0,
            "all_gate_flags_pending": True,
            "private_handoff_not_authorized": True,
        },
    }


def audit(report, mirror, graph, graph_mirror, index, index_mirror, packet,
          *l08_inputs):
    if len(l08_inputs) != 13:
        blocked()
    verified = l11.audit(graph, graph_mirror, index, index_mirror,
                         packet, *l08_inputs)
    if (verified["status"] != "PUBLIC_TRACEABILITY_VALID_NATIVE_PENDING"
        or verified["public_documentary_differences"] != 0
        or verified["native_cases_approved"] != 0
        or verified["criteria_human_approved"] != 0
        or verified["sinnoh_playable"] is not False):
        blocked()
    try:
        expected = expected_report(graph)
        same = l11.l10.l09.l08.l07.l06.same
        if not same(report, expected) or not same(mirror, expected):
            blocked()
        if (len(report["case_handoff"]) != 44
            or len({x["id"] for x in report["case_handoff"]}) != 44
            or len(report["criterion_handoff"]) != 20
            or len({x["id"] for x in report["criterion_handoff"]}) != 20
            or len(report["blockers"]) != 6
            or report["documentary_integrity"]["links_checked"] != 1084
            or report["counts"]["native_tests_missing"] != 44
            or report["counts"]["human_evidence_missing"] != 20
            or report["counts"]["local_reports_missing"] != 5
            or report["counts"]["phase_bcd_missing"] != 13
            or report["global_r09"]["case_ids"] != []
            or any("B10" in row["pending_gates"] or "B11" in row["pending_gates"]
                   for row in report["case_handoff"] if row["platform"] == "android")
            or any("B10" not in row["pending_gates"] or "B11" not in row["pending_gates"]
                   for row in report["case_handoff"] if row["platform"] == "windows")):
            blocked()
    except (KeyError, TypeError, IndexError, AttributeError):
        blocked()
    return {
        "schema": 1, "region": "SINNOH", "stage": "L12",
        "status": "PUBLIC_COVERAGE_AUDITED_REAL_EVIDENCE_MISSING",
        "baseline_commits": dict(report["baseline_commits"]),
        "source_l11_git_blob": L11_BLOB,
        "public_documentary": {
            "case_ids_checked": 44, "criteria_ids_checked": 20,
            "edges_checked": 1084, "missing_public_edges": 0,
        },
        "missing_evidence": {
            "local_reports": 5, "human_signoffs": 20,
            "windows_native_qa": 43, "android_native_qa": 1,
            "native_qa_total": 44, "bcd_approvals": 13,
        },
        "cases_total": 44, "criteria_total": 20,
        "windows_cases": 43, "android_cases": 1,
        "human_approved": 0, "native_approved": 0, "local_reports_received": 0,
        "phase_bcd_approved": 0, "phase_bcd_total": 13,
        "blocker_ids": [b["id"] for b in report["blockers"]],
        "r09_global_only": True,
        "gates": dict(report["gates"]),
        "guardrails": dict(report["guardrails"]),
        "human_qa_authorized": False, "native_qa_authorized": False,
        "sinnoh_playable": False,
    }


def run(root=ROOT):
    root = Path(root)
    l11.l10.l09.l08.check_pinned_blobs(root)
    l11.l10.l09.check_source_blobs(root)
    l11.l10.check_l09_blob(root)
    l11.check_l10_blob(root)
    check_public_l11_blobs(root)
    read = l11.l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
    sources = {
        name: read(root, path, maxsize=175000)
        for name, path, _sha in l11.l10.l09.l08.PINNED
    }
    report = read(root, REPORT, maxsize=145000)
    mirror = read(root, MIRROR, maxsize=145000)
    graph = read(root, l11.GRAPH, maxsize=200000)
    graph_mirror = read(root, l11.MIRROR, maxsize=200000)
    index = read(root, l11.l10.INDEX, maxsize=155000)
    index_mirror = read(root, l11.l10.MIRROR, maxsize=155000)
    packet = read(root, l11.l10.l09.PACKET, maxsize=155000)
    snapshot = read(root, l11.l10.l09.l08.SNAPSHOT, maxsize=125000)
    delta = read(root, l11.l10.l09.l08.DIFF, maxsize=16000)
    return audit(
        report, mirror, graph, graph_mirror, index, index_mirror, packet,
        snapshot, delta, sources["G12"], sources["L04"], sources["L05"],
        sources["L06"], sources["L07"], sources["L07_SITE"],
        l11.l10.l09.l08.l07.run(root),
        l11.l10.l09.l08.l07.l06.run(root),
        l11.l10.l09.l08.l07.l06.l05.run(root),
        l11.l10.l09.l08.l07.l06.l05.l04.run(root),
        l11.l10.l09.l08.l07.l06.l05.G12.run(root),
    )


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ["--help"], ["-h"]):
        print("SINNOH_L12_BLOCKED: no user-selected paths or evidence", file=sys.stderr)
        return 2
    if args:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), sort_keys=True, indent=2, ensure_ascii=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError,
            AttributeError, UnicodeError):
        print("SINNOH_L12_BLOCKED: public report or evidence guard failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
