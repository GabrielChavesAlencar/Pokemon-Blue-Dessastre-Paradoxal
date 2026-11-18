#!/usr/bin/env python3
"""L14: fail-closed public-only 88-request dependency/readiness audit.

A Git blob verifies public metadata bytes, never human signatures, licenses,
MapIDs, save isolation, native QA or rights. No private inputs or runtimes.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l13_public_queue as l13

MATRIX = "data/regions/sinnoh-l14-public-readiness-matrix.json"
MIRROR = "site/public/data/sinnoh-l14-public-readiness-matrix.json"
L13_MERGE = "1f12bcc86c10dcc934b024a0562cdadb65d5e2c2"
L13_BLOB = "357215cdfd96b37eaac291e1c0ab3873069a12fe"
SEMANTICS = {
    "links_are_documentary_only": True,
    "priority_is_not_execution_order": True,
    "no_derived_dependencies_for_anonymous_slots": True,
    "no_r09_per_case_links": True,
    "physical_validation_unavailable": True,
    "scope_of_anonymous_slots_unknown": True,
    "readiness_never_infers_auth": True,
    "readiness_state": "BLOCKED",
}


def blocked():
    raise ValueError("SINNOH_L14_BLOCKED: unsafe or altered public documentary dependency")


def check_l13_public_blobs(root=ROOT):
    for rel in (l13.QUEUE, l13.MIRROR):
        f = Path(root) / rel
        if f.is_symlink() or not f.is_file():
            blocked()
        raw = f.read_bytes()
        if len(raw) > 190000:
            blocked()
        git_blob = b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
        if hashlib.sha1(git_blob).hexdigest() != L13_BLOB:
            blocked()
    return True


def expected_matrix(source):
    rows = []
    for item in source["queue"]:
        links = []
        if item["kind"] == "HUMAN_CRITERION":
            links = ["L13-BLOCKER-" + item["blocker_ids"][0]]
        if item["kind"] == "NATIVE_CASE":
            links = (["L13-BLOCKER-" + bid for bid in item["blocker_ids"]]
                     + ["L13-HUMAN-" + cid for cid in item["criterion_ids"]])
        rows.append({
            "order": item["order"],
            "request_id": item["request_id"],
            "subject_id": item["subject_id"],
            "kind": item["kind"],
            "platform": item["platform"],
            "priority": item["priority"],
            "priority_label": item["priority_label"],
            "documentary_dependency_request_ids": links,
            "documentary_dependency_count": len(links),
            "dependency_interpretation": "PUBLIC_METADATA_LINKS_ONLY_NOT_PHYSICAL_AUTHORIZATION",
            "scope_known": item["kind"] not in ("LOCAL_REPORT_SLOT", "BCD_PENDING_SLOT"),
            "anonymous_bookkeeping_slot": item.get("placeholder_not_a_real_artifact", False),
            "readiness": "BLOCKED",
            "status": "PENDING",
            "human_approval": False,
            "physical_evidence_received": False,
            "native_qa_authorized": False,
            "private_submission_allowed": False,
        })
    counts = dict(source["counts"])
    counts.update({
        "readiness_rows": 88, "rows_blocked": 88, "rows_pending": 88,
        "rows_ready": 0,
        "request_documentary_links": sum(x["documentary_dependency_count"] for x in rows),
        "case_to_criterion_request_links": 846,
        "case_to_blocker_request_links": 218,
        "criterion_to_blocker_request_links": 20,
        "anonymous_rows_unassigned": 18,
    })
    return {
        "schema": 1, "region": "SINNOH", "stage": "L14", "version": 1,
        "status": "ALL_DEPENDENCY_REQUESTS_BLOCKED_NO_NATIVE_QA",
        "mode": "PUBLIC_READ_ONLY_DOCUMENTARY_DEPENDENCIES",
        "baseline_commits": {**source["baseline_commits"], "L13": L13_MERGE},
        "source_l13": {"path": l13.QUEUE, "git_blob_sha1": L13_BLOB},
        "priority_rule_version": 1,
        "priority_rules": list(source["priority_rules"]),
        "counts": counts,
        "dependency_semantics": dict(SEMANTICS),
        "gates": dict(source["gates"]),
        "rows": rows,
        "platform_partition": [
            {**p, "readiness": "BLOCKED", "native_approved": 0}
            for p in source["platform_queues"]
        ],
        "global_r09": {
            **source["global_r09"],
            "readiness": "BLOCKED", "dependency_request_ids": [],
        },
        "disclaimer": {
            **source["disclaimer"],
            "none_ready": True, "none_physically_approved": True,
            "all_native_pending": True,
        },
    }


def audit(matrix, mirror, queue, queue_mirror, report, report_mirror,
          graph, graph_mirror, index, index_mirror, packet, *l08_inputs):
    if len(l08_inputs) != 13:
        blocked()
    parent = l13.audit(queue, queue_mirror, report, report_mirror,
                       graph, graph_mirror, index, index_mirror, packet,
                       *l08_inputs)
    if (parent["status"] != "PUBLIC_QUEUE_AUDITED_ALL_REQUESTS_PENDING"
        or parent["request_counts"]["evidence_requests_total"] != 88
        or parent["native_cases_approved"] != 0
        or parent["documentary_links_verified"] != 1084
        or parent["sinnoh_playable"] is not False):
        blocked()
    try:
        expected = expected_matrix(queue)
        same = l13.l12.l11.l10.l09.l08.l07.l06.same
        if not same(matrix, expected) or not same(mirror, expected):
            blocked()
        rows = matrix["rows"]
        valid_ids = {r["request_id"] for r in rows}
        if (len(rows) != 88 or len(valid_ids) != 88
            or len({r["order"] for r in rows}) != 88
            or any(x["status"] != "PENDING" or x["readiness"] != "BLOCKED"
                   or x["physical_evidence_received"] is not False
                   or x["human_approval"] is not False
                   or x["native_qa_authorized"] is not False
                   or x["private_submission_allowed"] is not False
                   or any(dep not in valid_ids for dep in x["documentary_dependency_request_ids"])
                   for x in rows)
            or sum(x["documentary_dependency_count"] for x in rows) != 1084
            or matrix["global_r09"]["dependency_request_ids"] != []
            or any("L13-GLOBAL-R09" in x["documentary_dependency_request_ids"]
                   for x in rows)
            or any(x["documentary_dependency_count"] for x in rows
                   if x["anonymous_bookkeeping_slot"])
            or any("L13-BLOCKER-B10" in x["documentary_dependency_request_ids"]
                   or "L13-BLOCKER-B11" in x["documentary_dependency_request_ids"]
                   for x in rows if x["kind"] == "NATIVE_CASE" and x["platform"] == "android")
            or matrix["counts"]["rows_ready"] != 0):
            blocked()
    except (KeyError, TypeError, IndexError, AttributeError):
        blocked()
    return {
        "schema": 1, "stage": "L14", "region": "SINNOH",
        "status": "PUBLIC_DOCUMENTARY_DEPENDENCIES_VALID_ALL_BLOCKED",
        "baseline_commits": dict(expected["baseline_commits"]),
        "source_l13_git_blob": L13_BLOB,
        "requests_total": 88, "requests_pending": 88, "requests_ready": 0,
        "documentary_links": 1084,
        "case_to_criterion_links": 846, "case_to_blocker_links": 218,
        "criterion_to_blocker_links": 20,
        "windows_native_pending": 43, "android_native_pending": 1,
        "anonymous_slots_unassigned": 18,
        "local_reports_received": 0, "human_criteria_approved": 0,
        "native_executed": 0, "native_approved": 0,
        "phase_bcd_approved": 0, "phase_bcd_total": 13,
        "r07_pending": True, "r08_pending": True, "r09_pending": True,
        "r09_global_only": True,
        "no_private_data": True, "no_game_execution": True,
        "no_joiplay_execution": True, "no_sandbox_execution": True,
        "sinnoh_playable": False,
    }


def run(root=ROOT):
    root = Path(root)
    l13.l12.l11.l10.l09.l08.check_pinned_blobs(root)
    l13.l12.l11.l10.l09.check_source_blobs(root)
    l13.l12.l11.l10.check_l09_blob(root)
    l13.l12.l11.check_l10_blob(root)
    l13.l12.check_public_l11_blobs(root)
    l13.check_l12_public_blobs(root)
    check_l13_public_blobs(root)
    read = l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
    sources = {
        name: read(root, path, maxsize=175000)
        for name, path, _ in l13.l12.l11.l10.l09.l08.PINNED
    }
    matrix = read(root, MATRIX, maxsize=180000)
    mirror = read(root, MIRROR, maxsize=180000)
    queue = read(root, l13.QUEUE, maxsize=190000)
    queue_mirror = read(root, l13.MIRROR, maxsize=190000)
    report = read(root, l13.l12.REPORT, maxsize=145000)
    report_mirror = read(root, l13.l12.MIRROR, maxsize=145000)
    graph = read(root, l13.l12.l11.GRAPH, maxsize=200000)
    graph_mirror = read(root, l13.l12.l11.MIRROR, maxsize=200000)
    index = read(root, l13.l12.l11.l10.INDEX, maxsize=155000)
    index_mirror = read(root, l13.l12.l11.l10.MIRROR, maxsize=155000)
    packet = read(root, l13.l12.l11.l10.l09.PACKET, maxsize=155000)
    snapshot = read(root, l13.l12.l11.l10.l09.l08.SNAPSHOT, maxsize=125000)
    diff = read(root, l13.l12.l11.l10.l09.l08.DIFF, maxsize=16000)
    return audit(
        matrix, mirror, queue, queue_mirror, report, report_mirror,
        graph, graph_mirror, index, index_mirror, packet,
        snapshot, diff, sources["G12"], sources["L04"],
        sources["L05"], sources["L06"], sources["L07"],
        sources["L07_SITE"],
        l13.l12.l11.l10.l09.l08.l07.run(root),
        l13.l12.l11.l10.l09.l08.l07.l06.run(root),
        l13.l12.l11.l10.l09.l08.l07.l06.l05.run(root),
        l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.run(root),
        l13.l12.l11.l10.l09.l08.l07.l06.l05.G12.run(root),
    )


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ["--help"], ["-h"]):
        print("SINNOH_L14_BLOCKED: fixed public inputs only", file=sys.stderr)
        return 2
    if args:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), ensure_ascii=True, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError,
            IndexError, AttributeError, UnicodeError):
        print("SINNOH_L14_BLOCKED: public readiness validation failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
