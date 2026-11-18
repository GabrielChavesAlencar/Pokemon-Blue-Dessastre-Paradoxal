#!/usr/bin/env python3
"""Sinnoh L09 — independent HUMAN REVIEW HANDOFF, not independent review approval.

Audits only fixed public GitHub metadata from L08 and earlier. No PC, game,
Windows Sandbox, Android/JoiPlay, saves, network, local evidence, private
asset files, runtime execution, approvals, tokens, or automatic upload.
A verified Git blob is NOT proof of physical source identity or licensing.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l08_pinned_snapshot as l08

PACKET = "data/regions/sinnoh-l09-independent-public-handoff.json"
L08_MERGE = "8617ef47ea6745920cb6fe4be251982380d7628d"
PINNED_PUBLIC = (
    ("L08", l08.SNAPSHOT, "63f520c26cdb13d88c6e027ec371e2a2de7d0b30"),
    ("L08_DIFF", l08.DIFF, "e8198e0b94d45c187d295d416aaec63241793a7b"),
    ("L04", l08.l07.l06.l05.l04.CHECKLIST, "cffdaac87c0dc542b99dd9bdebe54d49038d940d"),
)
REVIEW_KINDS = {
    "B09": "ORIGIN_AND_CLONE_PROVENANCE",
    "B10": "WINDOWS_SANDBOX_CONFIGURATION",
    "B11": "WINDOWS_LIMITED_SAVE_SCOPE",
    "R07": "MAPID_CONFLICTS_AND_RESERVATIONS",
    "R08": "ASSET_RIGHTS_AND_BINDINGS",
}
SAFETY = {
    "github_only": True,
    "private_paths_excluded": True,
    "do_not_upload_saves": True,
    "no_game_execution": True,
    "no_windows_sandbox_execution": True,
    "no_joiplay_execution": True,
    "no_installer_creation": True,
    "no_auto_upload": True,
    "source_receipts_not_host_authentication": True,
    "unchanged_watch_not_global_save_isolation": True,
    "candidate_mapid_not_real_reservation": True,
    "asset_listing_not_license_approval": True,
    "windows_android_review_independent": True,
    "L09_documental_not_G12_android_local_L05": True,
}


def blocked():
    # Fixed message, never print attacker-supplied values, paths or private data.
    raise ValueError("SINNOH_L09_BLOCKED: public handoff inconsistent or unsafe")


def check_source_blobs(root=ROOT):
    """Git blob SHA-1 of public files only; never follow symlinks."""
    root = Path(root)
    for _stage, relative, expected in PINNED_PUBLIC:
        p = root / relative
        if p.is_symlink() or not p.is_file():
            blocked()
        raw = p.read_bytes()
        if len(raw) > 175000:
            blocked()
        data = b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
        if hashlib.sha1(data).hexdigest() != expected:
            blocked()
    return True


def expected_packet(snapshot, diff, checklist):
    # Sources are trusted ONLY after l08.audit validates full G12 -> L08 chain.
    criteria = {c["id"]: c for c in snapshot["criteria"]}
    review_tasks = []
    for stage in checklist["rows"]:
        for criterion in stage["criteria"]:
            row = criteria[criterion["id"]]
            review_tasks.append({
                "criterion_id": criterion["id"],
                "stage": stage["stage"],
                "kind": REVIEW_KINDS[stage["stage"]],
                "public_requirement": criterion["requirement"],
                "reviewer_action": "KEEP_PENDING",
                "review_state": "NOT_REVIEWED",
                "needs_external_independent_human_review": True,
                "independent_evidence_accepted": False,
                "local_human_signoff": False,
                "matching_case_count": row["dependent_cases"],
                "windows_cases": row["windows_dependencies"],
                "android_cases": row["android_dependencies"],
            })
    handoff = []
    for c in snapshot["cases"]:
        handoff.append({
            "case_id": c["id"],
            "kind": c["kind"],
            "platform": c["platform"],
            "required_criteria_ids": list(c["required_criteria_ids"]),
            "blocked_by": list(c["blocked_by"]),
            "future_native_gate": c["future_native_gate"],
            "reviewer_lane": (
                "WINDOWS_INDEPENDENT_HOST_DOCUMENTARY_REVIEW"
                if c["platform"] == "windows" else
                "ANDROID_INDEPENDENT_DEVICE_DOCUMENTARY_REVIEW"
            ),
            "expected_review_codes": [
                "REQUEST_" + item for item in c["required_criteria_ids"]
            ],
            "review_state": "NOT_REVIEWED",
            "reviewer_action": "KEEP_PENDING",
            "native_status": "pending",
            "human_signoff": False,
            "real_evidence_accepted": False,
            "native_qa_authorized": False,
            "private_file_attached": False,
        })
    return {
        "schema": 1,
        "region": "SINNOH",
        "stage": "L09",
        "version": 1,
        "status": "HUMAN_REVIEW_HANDOFF_ONLY_ALL_GATES_BLOCKED",
        "baseline_commit_l07": l08.ANCHOR,
        "baseline_commit_l08": L08_MERGE,
        "public_sources": [
            {"stage": stage, "path": path, "git_blob_sha1": sha}
            for stage, path, sha in PINNED_PUBLIC
        ],
        "counts": dict(l08.l07.COUNTS),
        "gates": dict(l08.l07.GATES),
        "allowed_documentary_actions": list(l08.l07.l06.ACTIONS),
        "default_action": "KEEP_PENDING",
        "human_review_completed": 0,
        "independent_signoffs": 0,
        "physical_evidence_received": 0,
        "external_human_authorization_present": False,
        "can_start_native_qa": False,
        "review_safety": dict(SAFETY),
        "review_tasks": review_tasks,
        "case_handoff": handoff,
    }


def audit(packet, *l08_inputs):
    if len(l08_inputs) != 13:
        blocked()
    # This is a real re-validation of L08 and all its nested upstream sources:
    # [snapshot,diff,g12,l04,l05,l06,l07,site,l07_report,...,g12_report].
    verified = l08.audit(*l08_inputs)
    if verified["status"] != "PUBLIC_PINNED_SNAPSHOT_VALID_ZERO_DRIFT_NATIVE_PENDING":
        blocked()
    snap, diff, _g12, checklist = l08_inputs[:4]
    try:
        reference = expected_packet(snap, diff, checklist)
        if not l08.l07.l06.same(packet, reference):
            blocked()
        if (len(packet["case_handoff"]) != 44
            or len({r["case_id"] for r in packet["case_handoff"]}) != 44
            or len(packet["review_tasks"]) != 20
            or len({r["criterion_id"] for r in packet["review_tasks"]}) != 20
            or len([r for r in packet["case_handoff"] if r["platform"] == "windows"]) != 43
            or len([r for r in packet["case_handoff"] if r["platform"] == "android"]) != 1):
            blocked()
        criteria = {c["criterion_id"] for c in packet["review_tasks"]}
        if criteria != {c for row in packet["case_handoff"]
                       for c in row["required_criteria_ids"]}:
            blocked()
        if (any(row["platform"] == "android"
                and ("B10" in row["blocked_by"] or "B11" in row["blocked_by"])
                for row in packet["case_handoff"])
            or any(row["platform"] == "windows"
                   and ("B10" not in row["blocked_by"] or "B11" not in row["blocked_by"])
                   for row in packet["case_handoff"])):
            blocked()
    except (KeyError, TypeError, IndexError, AttributeError):
        blocked()
    return {
        "schema": 1,
        "region": "SINNOH",
        "stage": "L09",
        "status": "PUBLIC_HUMAN_HANDOFF_VALID_NO_APPROVAL",
        "baseline_commit_l07": l08.ANCHOR,
        "baseline_commit_l08": L08_MERGE,
        "public_git_blobs_pinned": len(PINNED_PUBLIC),
        "upstream_public_drift": 0,
        "criteria_total": 20,
        "criteria_reviewed": 0,
        "cases_total": 44,
        "windows_cases": 43,
        "android_cases": 1,
        "human_reviews_accepted": 0,
        "native_cases_completed": 0,
        "native_cases_approved": 0,
        "local_reports_received": 0,
        "phase_bcd_approved": 0,
        "phase_bcd_total": 13,
        "r07_complete": False,
        "r08_complete": False,
        "r09_complete": False,
        "b11_global_isolation_proven": False,
        "asset_rights_approved": False,
        "mapids_reserved": False,
        "may_run_game_exe": False,
        "may_start_windows_sandbox": False,
        "may_run_joiplay": False,
        "may_install_live_game": False,
        "auto_uploaded": False,
        "android_local_l05_complete": False,
        "sinnoh_playable": False,
        "human_review_tasks": [
            {"id": t["criterion_id"], "stage": t["stage"], "state": "NOT_REVIEWED"}
            for t in packet["review_tasks"]
        ],
        "case_review_queue": [
            {"id": c["case_id"], "platform": c["platform"],
             "reviewer_lane": c["reviewer_lane"],
             "native_status": "pending",
             "native_execution_authorized": False}
            for c in packet["case_handoff"]
        ],
    }


def run(root=ROOT):
    root = Path(root)
    l08.check_pinned_blobs(root)
    check_source_blobs(root)
    reader = l08.l07.l06.l05.l04.l03.l02.l00.read_json
    docs = {
        stage: reader(root, path, maxsize=175000)
        for stage, path, _sha in l08.PINNED
    }
    packet = reader(root, PACKET, maxsize=155000)
    snapshot = reader(root, l08.SNAPSHOT, maxsize=125000)
    diff = reader(root, l08.DIFF, maxsize=16000)
    return audit(
        packet,
        snapshot, diff,
        docs["G12"], docs["L04"], docs["L05"], docs["L06"],
        docs["L07"], docs["L07_SITE"],
        l08.l07.run(root), l08.l07.l06.run(root),
        l08.l07.l06.l05.run(root), l08.l07.l06.l05.l04.run(root),
        l08.l07.l06.l05.G12.run(root),
    )


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ["--help"], ["-h"]):
        print("SINNOH_L09_BLOCKED: arbitrary paths and evidence forbidden", file=sys.stderr)
        return 2
    if args:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), sort_keys=True, indent=2, ensure_ascii=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            UnicodeError):
        print("SINNOH_L09_BLOCKED: public review handoff failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
