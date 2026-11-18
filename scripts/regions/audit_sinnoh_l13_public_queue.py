#!/usr/bin/env python3
"""L13: fail-closed PUBLIC document request queue, never evidence intake.

Only reads fixed public Git JSON. Never accesses host installation, private
sources, saves, Game.exe, Windows Sandbox, JoiPlay, credentials or uploaded data.
A Git blob proves public file bytes, NOT an independently reviewed source.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l12_coverage_gaps as l12

QUEUE = "data/regions/sinnoh-l13-public-evidence-queue.json"
MIRROR = "site/public/data/sinnoh-l13-public-evidence-queue.json"
L12_MERGE = "58b7f2fec9f66dee06d95676eec66fb2ded6a1de"
L12_BLOB = "dbd9181a5910c7fc711eaaa20d0e3b24a9d1710e"
PRIORITIES = (
    (0, "P0_DOCUMENTARY_PRECONDITION",
     ("BLOCKER_DEPENDENCY", "GLOBAL_REGIONAL_GATE"),
     "Documentary prerequisite tracking, not physical approval"),
    (1, "P1_MISSING_REPORT_SLOT", ("LOCAL_REPORT_SLOT",),
     "Anonymous bookkeeping placeholders only; no private files"),
    (2, "P2_INDEPENDENT_HUMAN_REVIEW", ("HUMAN_CRITERION",),
     "Human signoff still missing"),
    (3, "P3_BCD_PENDING_BOOKKEEPING", ("BCD_PENDING_SLOT",),
     "Anonymous counters; no invented specific BCD steps"),
    (4, "P4_NATIVE_QA_UNAUTHORIZED", ("NATIVE_CASE",),
     "Not executed, not authorized; inventory only"),
)
DISCLAIMER = {
    "public_documentary_only": True,
    "requires_independent_human_review": True,
    "no_reports_received": True,
    "no_acceptance_of_private_evidence": True,
    "no_upload_or_attachments": True,
    "no_local_paths_or_saves": True,
    "no_game_execution": True,
    "no_windows_sandbox_execution": True,
    "no_joiplay_execution": True,
    "watch_unchanged_is_not_global_save_isolation": True,
    "mapids_not_reserved": True,
    "asset_rights_not_approved": True,
    "android_local_l05_not_completed": True,
    "sinnoh_playable": False,
}


def blocked():
    # Never echo input paths, identifiers or private tokens in error messages.
    raise ValueError("SINNOH_L13_BLOCKED: unsafe or inconsistent public request queue")


def check_l12_public_blobs(root=ROOT):
    """Immutable exact blob hashes for the two fixed L12 public JSON files."""
    for relative in (l12.REPORT, l12.MIRROR):
        p = Path(root) / relative
        if p.is_symlink() or not p.is_file():
            blocked()
        content = p.read_bytes()
        if len(content) > 145000:
            blocked()
        blob = b"blob " + str(len(content)).encode("ascii") + b"\x00" + content
        if hashlib.sha1(blob).hexdigest() != L12_BLOB:
            blocked()
    return True


def expected_queue(source):
    """Pure, deterministic projection from validated L12. No evidence ingestion."""
    rows = []

    def add_request(item):
        rows.append({
            "order": len(rows) + 1,
            **item,
            "status": "PENDING",
            "accepted_evidence": False,
            "human_approved": False,
            "native_qa_authorized": False,
            "read_only": True,
            "request_mode": "SANITIZED_PUBLIC_STATUS_ONLY",
        })

    for block in source["blockers"]:
        if block["id"] == "R09":
            continue
        stage = block["id"]
        add_request({
            "request_id": "L13-BLOCKER-" + stage,
            "priority": 0,
            "priority_label": PRIORITIES[0][1],
            "kind": "BLOCKER_DEPENDENCY",
            "subject_id": stage,
            "platform": ("windows" if block["scope"] == "WINDOWS_ONLY"
                         else "cross-platform"),
            "blocker_ids": [stage],
            "criterion_ids": [c["id"] for c in source["criterion_handoff"]
                              if c["stage"] == stage],
            "case_ids": list(block["case_ids"]),
            "reason": "Documentary prerequisite pending; this item requests only sanitized public status.",
        })

    add_request({
        "request_id": "L13-GLOBAL-R09",
        "priority": 0,
        "priority_label": PRIORITIES[0][1],
        "kind": "GLOBAL_REGIONAL_GATE",
        "subject_id": "R09",
        "platform": "global",
        "blocker_ids": ["R09"],
        "criterion_ids": [],
        "case_ids": [],
        "reason": "R09 remains a regional global gate; never add per-case edges or a native test.",
    })

    for index in range(1, 6):
        ident = f"{index:02d}"
        add_request({
            "request_id": "L13-REPORT-" + ident,
            "priority": 1,
            "priority_label": PRIORITIES[1][1],
            "kind": "LOCAL_REPORT_SLOT",
            "subject_id": "LOCAL_REPORT_SLOT_" + ident,
            "platform": "unassigned",
            "blocker_ids": [],
            "criterion_ids": [],
            "case_ids": [],
            "reason": "Anonymous bookkeeping slot only: actual private report names, locations and evidence have not been supplied.",
            "placeholder_not_a_real_artifact": True,
        })

    for c in source["criterion_handoff"]:
        add_request({
            "request_id": "L13-HUMAN-" + c["id"],
            "priority": 2,
            "priority_label": PRIORITIES[2][1],
            "kind": "HUMAN_CRITERION",
            "subject_id": c["id"],
            "platform": ("windows" if c["stage"] in ("B10", "B11")
                         else "cross-platform"),
            "blocker_ids": [c["stage"]],
            "criterion_ids": [c["id"]],
            "case_ids": list(c["case_ids"]),
            "reason": "Independent review of this L04 criterion is missing; GitHub metadata is not proof of review.",
        })

    for index in range(1, 14):
        ident = f"{index:02d}"
        add_request({
            "request_id": "L13-BCD-" + ident,
            "priority": 3,
            "priority_label": PRIORITIES[3][1],
            "kind": "BCD_PENDING_SLOT",
            "subject_id": "BCD_PENDING_SLOT_" + ident,
            "platform": "global",
            "blocker_ids": [],
            "criterion_ids": [],
            "case_ids": [],
            "reason": "Anonymous B/C/D backlog count only; no stage ownership or physical approval inferred.",
            "placeholder_not_a_real_artifact": True,
        })

    for c in source["case_handoff"]:
        add_request({
            "request_id": "L13-NATIVE-" + c["id"],
            "priority": 4,
            "priority_label": PRIORITIES[4][1],
            "kind": "NATIVE_CASE",
            "subject_id": c["id"],
            "platform": c["platform"],
            "blocker_ids": list(c["blocker_ids"]),
            "criterion_ids": list(c["criterion_ids"]),
            "case_ids": [c["id"]],
            "reason": "Native G12 case remains unexecuted; this entry is not permission to run Windows, Android or any game.",
        })

    counts = dict(source["counts"])
    kinds = ("BLOCKER_DEPENDENCY", "GLOBAL_REGIONAL_GATE",
             "LOCAL_REPORT_SLOT", "HUMAN_CRITERION",
             "BCD_PENDING_SLOT", "NATIVE_CASE")
    keys = ("blocker_requests", "global_gate_requests", "report_slots",
            "human_criterion_requests", "bcd_slots", "native_case_requests")
    counts.update({
        "public_edges_verified": 1084,
        "evidence_requests_total": len(rows),
        **{key: sum(r["kind"] == kind for r in rows)
           for key, kind in zip(keys, kinds)},
        "requests_pending": len(rows),
        "requests_approved": 0,
    })

    return {
        "schema": 1, "region": "SINNOH", "stage": "L13", "version": 1,
        "status": "PUBLIC_REQUEST_QUEUE_PENDING_NO_PHYSICAL_EVIDENCE",
        "mode": "PUBLIC_READ_ONLY_NO_UPLOAD_NO_QA",
        "baseline_commits": {
            **source["baseline_commits"], "L12": L12_MERGE
        },
        "source_l12": {"path": l12.REPORT, "git_blob_sha1": L12_BLOB},
        "priority_rule_version": 1,
        "priority_rules": [
            {"priority": rank, "code": code, "kinds": list(kinds),
             "interpretation": desc}
            for rank, code, kinds, desc in PRIORITIES
        ],
        "counts": counts,
        "gates": dict(source["gates"]),
        "coverage_layers": list(source["coverage_layers"]),
        "queue": rows,
        "platform_queues": [{
            "platform": platform,
            "case_ids": list(source["platform_handoff"][i]["case_ids"]),
            "native_requests": total,
            "native_completed": 0,
            "requires_windows_sandbox_b10_b11": platform == "windows",
            "authorization": False,
        } for i, (platform, total) in enumerate((("windows", 43),
                                                  ("android", 1)))],
        "global_r09": {
            "id": "R09", "status": "PENDING", "case_ids": [],
            "not_case_scoped": True, "approved": False,
        },
        "disclaimer": dict(DISCLAIMER),
    }


def audit(queue, mirror, report, report_mirror, graph, graph_mirror,
          index, index_mirror, packet, *l08_inputs):
    if len(l08_inputs) != 13:
        blocked()
    verified = l12.audit(report, report_mirror, graph, graph_mirror,
                         index, index_mirror, packet, *l08_inputs)
    if (verified["status"] != "PUBLIC_COVERAGE_AUDITED_REAL_EVIDENCE_MISSING"
        or verified["public_documentary"]["edges_checked"] != 1084
        or verified["missing_evidence"]["native_qa_total"] != 44
        or verified["missing_evidence"]["human_signoffs"] != 20
        or verified["native_approved"] != 0
        or verified["sinnoh_playable"] is not False):
        blocked()
    try:
        expected = expected_queue(report)
        strict = l12.l11.l10.l09.l08.l07.l06.same
        if not strict(queue, expected) or not strict(mirror, expected):
            blocked()
        if (len(queue["queue"]) != 88
            or len({r["request_id"] for r in queue["queue"]}) != 88
            or [r["order"] for r in queue["queue"]] != list(range(1, 89))
            or any(item["status"] != "PENDING"
                   or item["accepted_evidence"] is not False
                   or item["native_qa_authorized"] is not False
                   for item in queue["queue"])
            or queue["global_r09"]["case_ids"] != []
            or any("B10" in r["blocker_ids"] or "B11" in r["blocker_ids"]
                   for r in queue["queue"]
                   if r["kind"] == "NATIVE_CASE" and r["platform"] == "android")
            or queue["counts"]["human_approved"] != 0
            or queue["counts"]["native_completed"] != 0
            or queue["counts"]["local_reports"] != 0):
            blocked()
    except (KeyError, IndexError, AttributeError, TypeError):
        blocked()
    return {
        "schema": 1, "region": "SINNOH", "stage": "L13",
        "status": "PUBLIC_QUEUE_AUDITED_ALL_REQUESTS_PENDING",
        "baseline_commits": dict(expected["baseline_commits"]),
        "source_l12_git_blob": L12_BLOB,
        "request_counts": {k: expected["counts"][k] for k in (
            "evidence_requests_total", "blocker_requests",
            "global_gate_requests", "report_slots",
            "human_criterion_requests", "bcd_slots",
            "native_case_requests", "requests_pending", "requests_approved")},
        "documentary_links_verified": 1084,
        "human_criteria_approved": 0,
        "native_cases_approved": 0,
        "native_cases_executed": 0,
        "local_reports_received": 0,
        "bcd_approved": 0,
        "bcd_total": 13,
        "windows_cases": 43, "android_cases": 1,
        "r07_pending": True, "r08_pending": True, "r09_pending": True,
        "r09_global_only": True,
        "no_private_uploads": True,
        "no_runtime_authorization": True,
        "sinnoh_playable": False,
    }


def run(root=ROOT):
    root = Path(root)
    l12.l11.l10.l09.l08.check_pinned_blobs(root)
    l12.l11.l10.l09.check_source_blobs(root)
    l12.l11.l10.check_l09_blob(root)
    l12.l11.check_l10_blob(root)
    l12.check_public_l11_blobs(root)
    check_l12_public_blobs(root)
    read = l12.l11.l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
    upstream = {
        name: read(root, path, maxsize=175000)
        for name, path, _sha in l12.l11.l10.l09.l08.PINNED
    }
    queue = read(root, QUEUE, maxsize=190000)
    mirror = read(root, MIRROR, maxsize=190000)
    report = read(root, l12.REPORT, maxsize=145000)
    report_mirror = read(root, l12.MIRROR, maxsize=145000)
    graph = read(root, l12.l11.GRAPH, maxsize=200000)
    graph_mirror = read(root, l12.l11.MIRROR, maxsize=200000)
    index = read(root, l12.l11.l10.INDEX, maxsize=155000)
    index_mirror = read(root, l12.l11.l10.MIRROR, maxsize=155000)
    packet = read(root, l12.l11.l10.l09.PACKET, maxsize=155000)
    snapshot = read(root, l12.l11.l10.l09.l08.SNAPSHOT, maxsize=125000)
    delta = read(root, l12.l11.l10.l09.l08.DIFF, maxsize=16000)
    return audit(
        queue, mirror, report, report_mirror, graph, graph_mirror,
        index, index_mirror, packet,
        snapshot, delta, upstream["G12"], upstream["L04"],
        upstream["L05"], upstream["L06"], upstream["L07"],
        upstream["L07_SITE"],
        l12.l11.l10.l09.l08.l07.run(root),
        l12.l11.l10.l09.l08.l07.l06.run(root),
        l12.l11.l10.l09.l08.l07.l06.l05.run(root),
        l12.l11.l10.l09.l08.l07.l06.l05.l04.run(root),
        l12.l11.l10.l09.l08.l07.l06.l05.G12.run(root),
    )


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ["-h"], ["--help"]):
        print("SINNOH_L13_BLOCKED: arguments and private inputs forbidden", file=sys.stderr)
        return 2
    if args:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), sort_keys=True, indent=2, ensure_ascii=True))
        return 0
    except (OSError, ValueError, IndexError, KeyError,
            AttributeError, TypeError, UnicodeError):
        print("SINNOH_L13_BLOCKED: public queue audit failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
