#!/usr/bin/env python3
"""Sinnoh L11: fail-closed PUBLIC documentary cross-traceability of G12/L04.

Validates six old public contracts through L10 then the exact L11 projection.
The verified Git objects concern public metadata, not local saves, protected
assets, host identity, map reservations, independent signoffs or gameplay.
No network, runtime, Sandbox, JoiPlay, Game.exe, environment or arbitrary paths.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l10_public_index as l10

GRAPH = "data/regions/sinnoh-l11-public-traceability.json"
MIRROR = "site/public/data/sinnoh-l11-public-traceability.json"
L10_MERGE = "7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a"
L10_BLOB = "ebb2559d59fcb9a2318173da4bf649e3d3af7567"
PUBLIC_SOURCE = l10.INDEX
AUDIT_EMPTY = {
    "missing_case_ids": [], "added_case_ids": [], "reordered_case_ids": [],
    "missing_criterion_ids": [], "added_criterion_ids": [],
    "reordered_criterion_ids": [], "missing_links": [], "unexpected_links": [],
    "platform_mismatches": [], "blocker_scope_mismatches": [],
    "differences_found": 0, "zero_drift": True,
}
GUARANTEES = {
    "r07_pending": True,
    "r08_pending": True,
    "r09_pending": True,
    "windows_android_independent": True,
    "watch_unchanged_not_global_save_isolation": True,
    "mapids_not_reserved": True,
    "asset_rights_not_approved": True,
    "no_human_review_accepted": True,
    "no_native_qa_completed": True,
    "no_game_exe_execution": True,
    "no_windows_sandbox_execution": True,
    "no_joiplay_execution": True,
    "no_local_save_access": True,
    "no_private_attachments": True,
    "no_installer": True,
    "no_upload": True,
    "sinnoh_playable": False,
    "local_android_l05_complete": False,
}


def blocked():
    # Constant error messages: no echo of user-supplied data, tokens or paths.
    raise ValueError("SINNOH_L11_BLOCKED: public traceability drift or unsafe approval")


def check_l10_blob(root=ROOT):
    """Verify both fixed public Git blobs by SHA-1, without invoking Git itself."""
    for rel_path in (l10.INDEX, l10.MIRROR):
        file_path = Path(root) / rel_path
        if file_path.is_symlink() or not file_path.is_file():
            blocked()
        raw = file_path.read_bytes()
        if len(raw) > 155000:
            blocked()
        git_object = b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
        if hashlib.sha1(git_object).hexdigest() != L10_BLOB:
            blocked()
    return True


def expected_graph(index):
    criteria = [{
        "id": row["id"],
        "stage": row["stage"],
        "case_ids": list(row["case_ids"]),
        "review_state": "NOT_REVIEWED",
        "human_signoff": False,
    } for row in index["criteria"]]
    cases = [{
        "id": row["id"],
        "kind": row["kind"],
        "platform": row["platform"],
        "criteria_ids": list(row["criteria"]),
        "blocker_ids": list(row["blocked_by"]),
        "review_state": "NOT_REVIEWED",
        "native_status": "pending",
        "human_signoff": False,
        "native_qa_authorized": False,
    } for row in index["cases"]]
    blockers = [{
        "id": row["id"],
        "scope": row["scope"],
        "case_ids": list(row["case_ids"]),
        "status": "PENDING",
        "native_qa_authorized": False,
    } for row in index["blockers"]]
    edges = {
        "case_to_criterion": [
            [row["id"], cid] for row in index["cases"]
            for cid in row["criteria"]
        ],
        "case_to_blocker": [
            [row["id"], bid] for row in index["cases"]
            for bid in row["blocked_by"]
        ],
        "criterion_to_blocker": [
            [row["id"], row["stage"]] for row in index["criteria"]
        ],
    }
    counts = dict(index["counts"])
    counts.update({
        "blockers_case_scoped": 5,
        "global_blockers": 1,
        "case_to_criterion_edges": len(edges["case_to_criterion"]),
        "case_to_blocker_edges": len(edges["case_to_blocker"]),
        "criterion_to_blocker_edges": len(edges["criterion_to_blocker"]),
    })
    return {
        "schema": 1, "region": "SINNOH", "stage": "L11", "version": 1,
        "status": "PUBLIC_TRACEABILITY_ALL_NATIVE_AND_HUMAN_PENDING",
        "mode": "PUBLIC_READ_ONLY_NO_NATIVE_QA",
        "baseline_commits": {**index["baseline_commits"], "L10": L10_MERGE},
        "source_l10": {"path": PUBLIC_SOURCE, "git_blob_sha1": L10_BLOB},
        "counts": counts,
        "gates": dict(index["gates"]),
        "platform_lanes": [{
            "platform": p,
            "case_ids": [row["id"] for row in index["cases"]
                         if row["platform"] == p],
            "status": "PENDING",
            "separate_native_gate": True,
            "approved": False,
        } for p in ("windows", "android")],
        "case_nodes": cases,
        "criterion_nodes": criteria,
        "blocker_nodes": blockers,
        "edges": edges,
        "global_region_gate": {
            "id": "R09", "status": "PENDING", "case_ids": [],
            "is_case_scoped": False, "not_human_approved": True,
            "native_qa_authorized": False,
        },
        "public_drift_audit": dict(AUDIT_EMPTY),
        "guarantees": dict(GUARANTEES),
    }


def compare_trace(index, graph):
    """Return deterministic public-only difference categories for synthetic QA."""
    case_a = [row["id"] for row in index["cases"]]
    case_b = [row["id"] for row in graph["case_nodes"]]
    crit_a = [row["id"] for row in index["criteria"]]
    crit_b = [row["id"] for row in graph["criterion_nodes"]]
    expected_edges = expected_graph(index)["edges"]
    provided = graph["edges"]
    missing = []
    unexpected = []
    for kind in ("case_to_criterion", "case_to_blocker", "criterion_to_blocker"):
        original = expected_edges[kind]
        observed = provided[kind]
        missing.extend([kind for item in original if item not in observed])
        unexpected.extend([kind for item in observed if item not in original])
        # Ordered lists matter even if their sets contain the same links.
        if original != observed and not missing and not unexpected:
            unexpected.append(kind)
    platforms = {
        row["id"]: row["platform"] for row in index["cases"]
    }
    scopes = {row["id"]: row["scope"] for row in index["blockers"]}
    result = {
        "missing_case_ids": [value for value in case_a if value not in case_b],
        "added_case_ids": [value for value in case_b if value not in case_a],
        "reordered_case_ids": ([a for a,b in zip(case_a,case_b) if a != b]
                               if set(case_a) == set(case_b)
                               and len(case_a) == len(case_b) else []),
        "missing_criterion_ids": [value for value in crit_a if value not in crit_b],
        "added_criterion_ids": [value for value in crit_b if value not in crit_a],
        "reordered_criterion_ids": ([a for a,b in zip(crit_a,crit_b) if a != b]
                                    if set(crit_a) == set(crit_b)
                                    and len(crit_a) == len(crit_b) else []),
        "missing_links": missing,
        "unexpected_links": unexpected,
        "platform_mismatches": [
            c["id"] for c in graph["case_nodes"]
            if c["id"] in platforms and c["platform"] != platforms[c["id"]]
        ],
        "blocker_scope_mismatches": [
            c["id"] for c in graph["blocker_nodes"]
            if c["id"] in scopes and c["scope"] != scopes[c["id"]]
        ],
    }
    result["differences_found"] = sum(len(v) for v in result.values())
    result["zero_drift"] = result["differences_found"] == 0
    return result


def audit(graph, mirror, index, index_mirror, packet, *l08_inputs):
    if len(l08_inputs) != 13:
        blocked()
    # The L10 auditor recursively calls L09/L08/L07/L06/L05/L04/G12 auditors.
    report = l10.audit(index, index_mirror, packet, *l08_inputs)
    if (report["status"] != "PUBLIC_INDEX_VALID_NATIVE_PENDING"
        or report["cases_total"] != 44
        or report["criteria_total"] != 20
        or report["native_approved"] != 0
        or report["criteria_human_approved"] != 0
        or report["sinnoh_playable"] is not False):
        blocked()
    try:
        reference = expected_graph(index)
        same = l10.l09.l08.l07.l06.same
        if (not same(graph, reference)
            or not same(mirror, reference)
            or not same(compare_trace(index, graph), AUDIT_EMPTY)):
            blocked()
        if (len(graph["case_nodes"]) != 44
            or len({c["id"] for c in graph["case_nodes"]}) != 44
            or len(graph["criterion_nodes"]) != 20
            or len({c["id"] for c in graph["criterion_nodes"]}) != 20
            or len(graph["blocker_nodes"]) != 6
            or len(graph["edges"]["case_to_criterion"]) != 846
            or len(graph["edges"]["case_to_blocker"]) != 218
            or len(graph["edges"]["criterion_to_blocker"]) != 20
            or graph["blocker_nodes"][-1]["case_ids"] != []
            or any(c["platform"] == "android" and (
                "B10" in c["blocker_ids"] or "B11" in c["blocker_ids"])
                for c in graph["case_nodes"])):
            blocked()
    except (KeyError, TypeError, IndexError, AttributeError):
        blocked()
    return {
        "schema": 1,
        "region": "SINNOH",
        "stage": "L11",
        "status": "PUBLIC_TRACEABILITY_VALID_NATIVE_PENDING",
        "baseline_commits": dict(reference["baseline_commits"]),
        "source_l10_git_blob": L10_BLOB,
        "counts": dict(reference["counts"]),
        "edges_checked": dict(
            (name, len(items)) for name, items in reference["edges"].items()
        ),
        "public_documentary_differences": 0,
        "case_ids": [node["id"] for node in graph["case_nodes"]],
        "criterion_ids": [node["id"] for node in graph["criterion_nodes"]],
        "blocker_ids": [node["id"] for node in graph["blocker_nodes"]],
        "windows_cases": 43, "android_cases": 1,
        "r09_global_not_per_case": True,
        "criteria_human_approved": 0, "native_cases_completed": 0,
        "native_cases_approved": 0, "local_reports": 0,
        "phase_bcd_completed": 0, "phase_bcd_total": 13,
        "guards": dict(GUARANTEES),
        "native_qa_authorized": False,
        "sinnoh_playable": False,
    }


def run(root=ROOT):
    root = Path(root)
    l10.l09.l08.check_pinned_blobs(root)
    l10.l09.check_source_blobs(root)
    l10.check_l09_blob(root)
    check_l10_blob(root)
    reader = l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
    sources = {
        name: reader(root, path, maxsize=175000)
        for name, path, _sha in l10.l09.l08.PINNED
    }
    graph = reader(root, GRAPH, maxsize=200000)
    mirror = reader(root, MIRROR, maxsize=200000)
    index = reader(root, l10.INDEX, maxsize=155000)
    index_mirror = reader(root, l10.MIRROR, maxsize=155000)
    packet = reader(root, l10.l09.PACKET, maxsize=155000)
    snap = reader(root, l10.l09.l08.SNAPSHOT, maxsize=125000)
    diff = reader(root, l10.l09.l08.DIFF, maxsize=16000)
    return audit(
        graph, mirror, index, index_mirror, packet,
        snap, diff, sources["G12"], sources["L04"], sources["L05"],
        sources["L06"], sources["L07"], sources["L07_SITE"],
        l10.l09.l08.l07.run(root), l10.l09.l08.l07.l06.run(root),
        l10.l09.l08.l07.l06.l05.run(root),
        l10.l09.l08.l07.l06.l05.l04.run(root),
        l10.l09.l08.l07.l06.l05.G12.run(root),
    )


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ["--help"], ["-h"]):
        print("SINNOH_L11_BLOCKED: only fixed public metadata allowed", file=sys.stderr)
        return 2
    if args:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), sort_keys=True, indent=2, ensure_ascii=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError,
            AttributeError, UnicodeError):
        print("SINNOH_L11_BLOCKED: unsafe public traceability source", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
