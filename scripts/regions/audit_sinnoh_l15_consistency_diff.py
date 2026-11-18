#!/usr/bin/env python3
"""Sinnoh L15: fail-closed public consistency/delta audit, not native QA.

Verifies fixed public Git objects and all upstream documentary contracts.
The L14 link projection is a structural change, NEVER physical evidence.
No private files, native runtime, Sandbox, JoiPlay, saves, network or uploads.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l14_readiness as l14

REPORT = "data/regions/sinnoh-l15-public-consistency-diff.json"
MIRROR = "site/public/data/sinnoh-l15-public-consistency-diff.json"
L14_MERGE = "11eda18f7225e16b13007c1eb955ccc3d7667b66"
PINNED = (
    ("L13", l14.l13.QUEUE, "357215cdfd96b37eaac291e1c0ab3873069a12fe"),
    ("L14", l14.MATRIX, "d882d6a20b1c01be33744f14ab7826af2fb6ef41"),
)
POLICY = {
    "comparisons_are_public_json_only": True,
    "new_links_are_l14_projection_only": True,
    "zero_documentary_drift_does_not_mean_physical_approval": True,
    "p0_p4_not_native_execution_order": True,
    "no_private_evidence_intake": True, "no_game_exe": True,
    "no_windows_sandbox": True, "no_joiplay": True,
    "no_saves": True, "no_private_files": True, "no_uploads": True,
    "watch_unchanged_not_global_save_isolation": True,
    "asset_rights_not_approved": True, "mapids_not_reserved": True,
    "r07_pending": True, "r08_pending": True, "r09_pending": True,
    "anonymous_slots_unassigned": True,
    "android_not_covered_by_windows_b10_b11": True,
    "sinnoh_playable": False,
}
KINDS = ("BLOCKER_DEPENDENCY", "GLOBAL_REGIONAL_GATE",
         "LOCAL_REPORT_SLOT", "HUMAN_CRITERION",
         "BCD_PENDING_SLOT", "NATIVE_CASE")


def blocked():
    raise ValueError("SINNOH_L15_BLOCKED: public diff or safety gate invalid")


def check_l13_l14_blobs(root=ROOT):
    """Verify source AND mirror of each immutable public Git object."""
    for stage, rel, sha in PINNED:
        mirror = l14.l13.MIRROR if stage == "L13" else l14.MIRROR
        for pathname in (rel, mirror):
            p = Path(root) / pathname
            if p.is_symlink() or not p.is_file():
                blocked()
            raw = p.read_bytes()
            if len(raw) > 190000:
                blocked()
            git_blob = b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
            if hashlib.sha1(git_blob).hexdigest() != sha:
                blocked()
    return True


def expected_report(source_l13, matrix_l14):
    rows = []
    for before, after in zip(source_l13["queue"], matrix_l14["rows"]):
        # Do not silently call a mismatch "zero drift".
        if (before["request_id"] != after["request_id"]
            or before["kind"] != after["kind"]
            or before["platform"] != after["platform"]
            or before["priority"] != after["priority"]
            or before["status"] != after["status"]):
            blocked()
        rows.append({
            "order": after["order"],
            "request_id": after["request_id"],
            "subject_id": after["subject_id"],
            "kind": after["kind"], "platform": after["platform"],
            "priority": after["priority"],
            "priority_label": after["priority_label"],
            "source_l13_status": before["status"],
            "source_l14_status": after["status"],
            "readiness": after["readiness"],
            "comparison_status": "CONSISTENT_DOCUMENTARY_METADATA",
            "identity_drift": [], "priority_drift": [],
            "platform_drift": [], "status_drift": [],
            "l13_blockers_count": len(before["blocker_ids"]),
            "l13_criteria_count": len(before["criterion_ids"]),
            "l14_documentary_dependency_count":
                after["documentary_dependency_count"],
            "l14_documentary_projection_added":
                after["documentary_dependency_count"],
            "projection_only_no_physical_change": True,
            "anonymous_bookkeeping_slot":
                after["anonymous_bookkeeping_slot"],
            "accepted_evidence": False, "human_approved": False,
            "native_qa_authorized": False, "private_file_received": False,
        })

    groups = []
    for kind in KINDS:
        selected = [x for x in rows if x["kind"] == kind]
        groups.append({
            "kind": kind,
            "requests": len(selected), "blocked": len(selected),
            "ready": 0, "actual_evidence_received": 0,
            "documentary_dependency_links":
                sum(x["l14_documentary_dependency_count"]
                    for x in selected),
            "category_status": "PENDING_BLOCKED",
        })

    counts = dict(matrix_l14["counts"])
    counts.update({
        "reported_comparisons": 88, "source_records_matched": 88,
        "source_records_added": 0, "source_records_removed": 0,
        "source_records_reordered": 0,
        "id_drift_count": 0, "priority_drift_count": 0,
        "platform_drift_count": 0, "status_drift_count": 0,
        "physical_approval_change_count": 0,
        "l14_documentary_projection_links": 1084,
        "l13_direct_dependency_request_links": 0,
        "l14_metadata_projection_added": 1084,
        "actual_evidence_received": 0,
    })
    changes = [
        {"id": "REQUEST_IDENTITIES_AND_ORDER", "baseline": 88,
         "observed": 88, "added": 0, "removed": 0, "drift": 0,
         "state": "UNCHANGED_PUBLIC_METADATA"},
        {"id": "PRIORITY_PLATFORM_STATUS", "baseline": 88,
         "observed": 88, "added": 0, "removed": 0, "drift": 0,
         "state": "UNCHANGED_PUBLIC_METADATA"},
        {"id": "L14_DOCUMENTARY_DEPENDENCY_PROJECTION", "baseline": 0,
         "observed": 1084, "added": 1084, "removed": 0, "drift": 0,
         "state": "ADDED_DOCUMENTARY_PROJECTION_NOT_NATIVE_EVIDENCE"},
        {"id": "REAL_HUMAN_AND_NATIVE_APPROVAL", "baseline": 0,
         "observed": 0, "added": 0, "removed": 0, "drift": 0,
         "state": "NO_REAL_EVIDENCE_RECEIVED"},
    ]
    platforms = [{
        "platform": p["platform"],
        "case_ids": list(p["case_ids"]),
        "native_requests": p["native_requests"],
        "native_completed": 0, "native_approved": 0,
        "authorization": False, "state": "PENDING_BLOCKED",
        "requires_windows_b10_b11":
            p["requires_windows_sandbox_b10_b11"],
    } for p in matrix_l14["platform_partition"]]

    return {
        "schema": 1, "region": "SINNOH", "stage": "L15",
        "version": 1,
        "status": "PUBLIC_DOC_CONSISTENT_L14_PROJECTION_ONLY_ALL_BLOCKED",
        "mode": "PUBLIC_READ_ONLY_ZERO_PHYSICAL_APPROVAL",
        "baseline_commits":
            {**matrix_l14["baseline_commits"], "L14": L14_MERGE},
        "public_source_blobs": [
            {"stage": stage, "path": path, "git_blob_sha1": sha}
            for stage, path, sha in PINNED
        ],
        "counts": counts, "gates": dict(matrix_l14["gates"]),
        "priority_rules": list(matrix_l14["priority_rules"]),
        "change_categories": changes,
        "group_summary": groups, "records": rows,
        "platform_partition": platforms,
        "global_r09": {
            "id": "R09", "status": "PENDING", "case_ids": [],
            "documentary_dependency_request_ids": [],
            "global_gate_only": True, "approved": False,
        },
        "policy": dict(POLICY),
    }


def audit(diff, mirror, matrix, matrix_mirror, queue, queue_mirror,
          report12, report12_mirror, graph, graph_mirror, index,
          index_mirror, packet, *l08_inputs):
    if len(l08_inputs) != 13:
        blocked()
    previous = l14.audit(
        matrix, matrix_mirror, queue, queue_mirror, report12,
        report12_mirror, graph, graph_mirror, index, index_mirror,
        packet, *l08_inputs)
    if (previous["status"] !=
        "PUBLIC_DOCUMENTARY_DEPENDENCIES_VALID_ALL_BLOCKED"
        or previous["requests_total"] != 88
        or previous["requests_ready"] != 0
        or previous["documentary_links"] != 1084
        or previous["sinnoh_playable"] is not False):
        blocked()
    try:
        expected = expected_report(queue, matrix)
        same = l14.l13.l12.l11.l10.l09.l08.l07.l06.same
        if not same(diff, expected) or not same(mirror, expected):
            blocked()
        records = diff["records"]
        if (len(records) != 88
            or len({x["request_id"] for x in records}) != 88
            or sum(x["l14_documentary_projection_added"]
                   for x in records) != 1084
            or any(x["readiness"] != "BLOCKED"
                   or x["source_l13_status"] != "PENDING"
                   or x["source_l14_status"] != "PENDING"
                   or x["native_qa_authorized"] is not False
                   or x["accepted_evidence"] is not False
                   or x["human_approved"] is not False
                   for x in records)
            or any(x["l14_documentary_dependency_count"] != 0
                   for x in records if x["anonymous_bookkeeping_slot"])
            or diff["global_r09"]["case_ids"] != []
            or diff["global_r09"]["documentary_dependency_request_ids"] != []
            or diff["counts"]["requests_approved"] != 0):
            blocked()
    except (KeyError, TypeError, IndexError, AttributeError):
        blocked()
    return {
        "schema": 1, "region": "SINNOH", "stage": "L15",
        "status": "PUBLIC_CONSISTENCY_VALID_PHYSICAL_QA_PENDING",
        "baseline_commits": dict(expected["baseline_commits"]),
        "public_source_blobs": list(expected["public_source_blobs"]),
        "request_rows_matched": 88,
        "id_priority_platform_status_drift": 0,
        "new_l14_documentary_projection": 1084,
        "documentary_links": 1084,
        "case_criterion_links": 846, "case_blocker_links": 218,
        "criterion_blocker_links": 20,
        "anonymous_slots_unassigned": 18,
        "windows_native_pending": 43, "android_native_pending": 1,
        "requests_blocked": 88, "requests_ready": 0,
        "local_reports_received": 0, "human_approved": 0,
        "native_executed": 0, "native_approved": 0,
        "phase_bcd_approved": 0, "phase_bcd_total": 13,
        "r07_pending": True, "r08_pending": True, "r09_pending": True,
        "r09_global_only": True,
        "no_physical_evidence": True, "no_private_uploads": True,
        "sinnoh_playable": False,
    }


def run(root=ROOT):
    root = Path(root)
    l14.l13.l12.l11.l10.l09.l08.check_pinned_blobs(root)
    l14.l13.l12.l11.l10.l09.check_source_blobs(root)
    l14.l13.l12.l11.l10.check_l09_blob(root)
    l14.l13.l12.l11.check_l10_blob(root)
    l14.l13.l12.check_public_l11_blobs(root)
    l14.l13.check_l12_public_blobs(root)
    l14.check_l13_public_blobs(root)
    check_l13_l14_blobs(root)

    read = l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
    upstream = {
        k: read(root, p, maxsize=175000)
        for k, p, _ in l14.l13.l12.l11.l10.l09.l08.PINNED
    }
    args = [
        read(root, REPORT, maxsize=145000),
        read(root, MIRROR, maxsize=145000),
        read(root, l14.MATRIX, maxsize=180000),
        read(root, l14.MIRROR, maxsize=180000),
        read(root, l14.l13.QUEUE, maxsize=190000),
        read(root, l14.l13.MIRROR, maxsize=190000),
        read(root, l14.l13.l12.REPORT, maxsize=145000),
        read(root, l14.l13.l12.MIRROR, maxsize=145000),
        read(root, l14.l13.l12.l11.GRAPH, maxsize=200000),
        read(root, l14.l13.l12.l11.MIRROR, maxsize=200000),
        read(root, l14.l13.l12.l11.l10.INDEX, maxsize=155000),
        read(root, l14.l13.l12.l11.l10.MIRROR, maxsize=155000),
        read(root, l14.l13.l12.l11.l10.l09.PACKET, maxsize=155000),
        read(root, l14.l13.l12.l11.l10.l09.l08.SNAPSHOT, maxsize=125000),
        read(root, l14.l13.l12.l11.l10.l09.l08.DIFF, maxsize=16000),
        *(upstream[k] for k in ("G12", "L04", "L05", "L06", "L07", "L07_SITE")),
        l14.l13.l12.l11.l10.l09.l08.l07.run(root),
        l14.l13.l12.l11.l10.l09.l08.l07.l06.run(root),
        l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.run(root),
        l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.run(root),
        l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.G12.run(root),
    ]
    return audit(*args)


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ["--help"], ["-h"]):
        print("SINNOH_L15_BLOCKED: fixed public JSON only", file=sys.stderr)
        return 2
    if args:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), ensure_ascii=True, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError,
            IndexError, AttributeError, UnicodeError):
        print("SINNOH_L15_BLOCKED: invalid public consistency report", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
