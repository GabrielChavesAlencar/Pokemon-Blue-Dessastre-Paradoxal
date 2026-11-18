#!/usr/bin/env python3
"""Sinnoh L08 public Git-blob-pinned documentary snapshot and semantic drift audit.

Read ONLY six fixed public repository JSON files plus two L08 JSON manifests.
Neither Git blob identity nor a static JSON proves host provenance, private
rights, runtime QA, safe save isolation, or any permission to execute a game.
No shell commands, network, private files, Windows Sandbox, or JoiPlay.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l07_public_triage as l07

SNAPSHOT = "data/regions/sinnoh-l08-pinned-snapshot.json"
DIFF = "data/regions/sinnoh-l08-semantic-diff.json"
ANCHOR = "d98033b362dac82347e0d97cb5606870eaa70b22"
# Only the six public GitHub blobs verified at the immutable L07 merge commit.
# No source content is accepted from user-selected paths or public PR metadata.
PINNED = (
    ("G12", "data/regions/sinnoh-g12-native-handoff.json", "e0fb08348fe5211f62acd057200d9c4a926351ab"),
    ("L04", "data/regions/sinnoh-l04-independent-review-checklist.json", "cffdaac87c0dc542b99dd9bdebe54d49038d940d"),
    ("L05", "data/regions/sinnoh-l05-native-case-dependencies.json", "4c8d35e510dd863568e34fd3cc7d2e4ba908bcde"),
    ("L06", "data/regions/sinnoh-l06-human-evidence-routing.json", "9ec4170d9c60e4d53028234e447a0a38346ddace"),
    ("L07", "data/regions/sinnoh-l07-public-triage.json", "ec42d1010293d352fba8ad96cc40793e2acc190f"),
    ("L07_SITE", "site/public/data/sinnoh-l07-public-triage.json", "ec42d1010293d352fba8ad96cc40793e2acc190f"),
)
CASE_KEYS = (
    "id", "kind", "platform", "required_criteria_ids", "blocked_by",
    "future_native_gate", "review_state", "native_status",
    "evidence_accepted", "native_qa_authorized",
)
CRITERION_KEYS = (
    "id", "stage", "dependent_cases", "windows_dependencies",
    "android_dependencies", "status", "human_signoff",
    "physical_evidence_accepted",
)
QUEUE_KEYS = (
    "platform", "count", "case_ids", "native_gate", "documentary_only", "approved",
)
DIFF_SPECS = (
    ("G12", "L05", "case_ids_kind_platform_native_status", 44),
    ("L04", "L05", "all_20_criteria_ids_and_coverage", 20),
    ("L05", "L06", "case_criteria_platform_blockers_status", 44),
    ("L06", "L07", "case_criteria_queue_gate_status", 44),
    ("L07", "L08", "case_criteria_and_native_pending_snapshot", 44),
)


def blocked():
    # Do not print attacker-supplied IDs, paths, hashes, evidence or values.
    raise ValueError("SINNOH_L08_BLOCKED: unsafe or changed documentary snapshot")


def project(row, fields):
    return {k: row[k] for k in fields}


def case_rows(rows, source):
    result = []
    for row in rows:
        out = {
            "id": row["case_id"] if source in ("L05", "L06") else row["id"],
            "kind": row["kind"],
            "platform": row["platform"],
            "native_status": row["native_status"],
        }
        if source in ("L05", "L06", "L07", "L08"):
            out["required_criteria_ids"] = list(row["required_criteria_ids"])
            out["blocked_by"] = list(
                row["blocking_stages"] if source in ("L05", "L06")
                else row["blocked_by"]
            )
        if source in ("L06", "L07", "L08"):
            out["future_native_gate"] = row["future_native_gate"]
            out["review_state"] = row["review_state"]
        if source in ("L07", "L08"):
            out["evidence_accepted"] = row["evidence_accepted"]
            out["native_qa_authorized"] = row["native_qa_authorized"]
        return_item = out
        result.append(return_item)
    return result


def compare_rows(before, after, fields):
    a_ids = [x["id"] for x in before]
    b_ids = [x["id"] for x in after]
    a = {x["id"]: x for x in before}
    b = {x["id"]: x for x in after}
    return {
        "added_ids": [v for v in b_ids if v not in a],
        "missing_ids": [v for v in a_ids if v not in b],
        "reordered_ids": ([v for v, w in zip(a_ids, b_ids) if v != w]
                          if len(a_ids) == len(b_ids) and set(a_ids) == set(b_ids)
                          else []),
        "modified_ids": [
            v for v in a_ids if v in b and
            not l07.l06.same(project(a[v], fields), project(b[v], fields))
        ],
    }


def expected_snapshot(l07_doc):
    return {
        "schema": 1, "region": "SINNOH", "stage": "L08", "version": 1,
        "status": "PUBLIC_COMMIT_PINNED_DOCUMENTARY_SNAPSHOT_NOT_NATIVE_QA",
        "baseline_commit": ANCHOR,
        "source_object_format": "git-blob-sha1",
        "sources": [
            {"stage": stage, "path": path, "blob_sha": sha, "at_commit": ANCHOR}
            for stage, path, sha in PINNED
        ],
        "counts": dict(l07.COUNTS),
        "gates": dict(l07.GATES),
        "platform_queues": [project(q, QUEUE_KEYS) for q in l07_doc["platform_queues"]],
        "criteria": [project(c, CRITERION_KEYS) for c in l07_doc["criteria"]],
        "cases": [project(c, CASE_KEYS) for c in l07_doc["cases"]],
        "physical_evidence_accepted": False,
        "human_approval_issued": False,
        "native_qa_authorized": False,
        "android_local_l05_completed": False,
    }


def expected_diff(g12, l04, l05, l06, l07_doc, snapshot):
    all_criteria = [
        {"id": c["id"]} for row in l04["rows"] for c in row["criteria"]
    ]
    mapped_criteria = [{"id": value} for value in l05["expected_criteria_ids"]]
    pairs = (
        (case_rows(g12["cases"], "G12"), case_rows(l05["rows"], "L05"),
         ("id", "kind", "platform", "native_status")),
        (all_criteria, mapped_criteria, ("id",)),
        (case_rows(l05["rows"], "L05"), case_rows(l06["rows"], "L06"),
         ("id", "kind", "platform", "required_criteria_ids", "blocked_by", "native_status")),
        (case_rows(l06["rows"], "L06"), case_rows(l07_doc["cases"], "L07"),
         ("id", "kind", "platform", "required_criteria_ids", "blocked_by",
          "future_native_gate", "review_state", "native_status")),
        (case_rows(l07_doc["cases"], "L07"), case_rows(snapshot["cases"], "L08"),
         CASE_KEYS),
    )
    comparisons = []
    for (src, dest, scope, expected_count), (left, right, keys) in zip(DIFF_SPECS, pairs):
        if len(left) != expected_count or len(right) != expected_count:
            blocked()
        differences = compare_rows(left, right, keys)
        comparisons.append({
            "from": src, "to": dest, "scope": scope, "checked": expected_count,
            **differences,
            "status": ("NO_PUBLIC_DOCUMENTARY_DRIFT"
                       if all(not v for v in differences.values())
                       else "BLOCKED_PUBLIC_DOCUMENTARY_DRIFT"),
        })
    counts = dict(l07.COUNTS)
    counts["comparisons_checked"] = 5
    counts["differences_found"] = sum(
        len(v) for c in comparisons
        for key, v in c.items() if key in (
            "added_ids", "missing_ids", "reordered_ids", "modified_ids")
    )
    return {
        "schema": 1, "region": "SINNOH", "stage": "L08_DIFF", "version": 1,
        "status": ("ZERO_PUBLIC_DOCUMENTARY_DRIFT_NATIVE_PENDING"
                   if counts["differences_found"] == 0
                   else "BLOCKED_PUBLIC_DOCUMENTARY_DRIFT"),
        "baseline_commit": ANCHOR,
        "source_stages": ["G12", "L04", "L05", "L06", "L07", "L08"],
        "comparisons": comparisons,
        "counts": counts,
        "gates": dict(l07.GATES),
        "scope": "PUBLIC_STATIC_METADATA_ONLY",
        "private_evidence_read": False,
        "can_authorize_qa": False,
        "sinnoh_playable": False,
    }


def check_pinned_blobs(root):
    """Verify checked-in public bytes against six known public Git blob IDs."""
    for _stage, rel_path, expected_sha in PINNED:
        file_path = root / rel_path
        if file_path.is_symlink() or not file_path.is_file():
            blocked()
        raw = file_path.read_bytes()
        if len(raw) > 175000:
            blocked()
        blob = b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
        if hashlib.sha1(blob).hexdigest() != expected_sha:
            blocked()
    return True


def audit(snapshot, diff, g12, l04, l05, l06, l07_doc, mirror,
          l07_report, l06_report, l05_report, l04_report, g12_report):
    # Independently validate the full upstream documentary chain.
    check = l07.audit(
        l07_doc, mirror, l06, l05, l04, g12,
        l06_report, l05_report, l04_report, g12_report,
    )
    if not l07.l06.same(l07_report, check):
        blocked()
    try:
        expected_snap = expected_snapshot(l07_doc)
        if not l07.l06.same(snapshot, expected_snap):
            blocked()
        expected_delta = expected_diff(g12, l04, l05, l06, l07_doc, snapshot)
        if expected_delta["counts"]["differences_found"] != 0:
            blocked()
        if not l07.l06.same(diff, expected_delta):
            blocked()
        criterion_ids = [r["id"] for r in snapshot["criteria"]]
        union = {c for row in snapshot["cases"] for c in row["required_criteria_ids"]}
        if (len(criterion_ids) != 20
            or len(set(criterion_ids)) != 20
            or union != set(criterion_ids)
            or len(snapshot["cases"]) != 44
            or len({r["id"] for r in snapshot["cases"]}) != 44):
            blocked()
    except (KeyError, TypeError, IndexError, AttributeError):
        blocked()
    return {
        "schema": 1, "region": "SINNOH", "stage": "L08",
        "status": "PUBLIC_PINNED_SNAPSHOT_VALID_ZERO_DRIFT_NATIVE_PENDING",
        "baseline_commit": ANCHOR,
        "source_public_git_blobs_checked": len(PINNED),
        "public_semantic_comparisons": 5,
        "public_differences": 0,
        "counts": dict(l07.COUNTS),
        "platform_counts": {"windows": 43, "android": 1},
        "criteria_total": 20,
        "case_ids": [c["id"] for c in snapshot["cases"]],
        "criterion_ids": criterion_ids,
        "human_evidence_approved": False,
        "can_run_windows_sandbox": False,
        "can_run_game_exe": False,
        "can_run_joiplay": False,
        "can_install_region": False,
        "b11_global_save_isolation_proven": False,
        "r07_mapids_reserved": False,
        "r08_asset_rights_approved": False,
        "r09_complete": False,
        "sinnoh_playable": False,
        "android_local_l05_completed": False,
    }


def run(root=ROOT):
    root = Path(root)
    check_pinned_blobs(root)
    reader = l07.l06.l05.l04.l03.l02.l00.read_json
    docs = {
        stage: reader(root, path, maxsize=175000)
        for stage, path, _sha in PINNED
    }
    snap = reader(root, SNAPSHOT, maxsize=125000)
    diff = reader(root, DIFF, maxsize=16000)
    result = audit(
        snap, diff,
        docs["G12"], docs["L04"], docs["L05"], docs["L06"],
        docs["L07"], docs["L07_SITE"],
        l07.run(root), l07.l06.run(root), l07.l06.l05.run(root),
        l07.l06.l05.l04.run(root), l07.l06.l05.G12.run(root),
    )
    return result


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ["--help"], ["-h"]):
        print("SINNOH_L08_BLOCKED: no arbitrary input paths or private data", file=sys.stderr)
        return 2
    if args:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError,
            AttributeError, UnicodeError):
        print("SINNOH_L08_BLOCKED: public snapshot or source drift", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
