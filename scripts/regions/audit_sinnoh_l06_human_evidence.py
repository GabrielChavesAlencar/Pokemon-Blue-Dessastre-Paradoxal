#!/usr/bin/env python3
"""Sinnoh L06: PUBLIC, immutable human-documentary queues for the 44 G12 cases.

Only public repository metadata. No runtime QA or evidence collection, no host
access, no private paths, no entitlement to execute Windows Sandbox/JoiPlay.
L06 is NOT the G12 local Android L05 gate.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l05_native_dependencies as l05

MATRIX = "data/regions/sinnoh-l06-human-evidence-routing.json"
ACTIONS = (
    "REQUEST_SANITIZED_DOCUMENTATION",
    "REVIEW_DOCUMENTARY_ONLY",
    "BLOCK",
    "KEEP_PENDING",
)
KIND_CODES = {
    "starter": "REVIEW_STARTER_CHOICE_CONTRACT",
    "barry": "REVIEW_BARRY_WIN_LOSS_SCALING",
    "save_reload": "REVIEW_SAVE_RELOAD_SCOPE_NOT_GLOBAL",
    "warp": "REVIEW_WARP_TOPOLOGY_NOT_RESERVED",
    "npc": "REVIEW_NPC_EVENTS_NOT_INSTALLED",
    "regression": "REVIEW_REGIONAL_BOUNDARIES_NO_ASSUMED_PASS",
    "android": "REVIEW_JOIPLAY_INDEPENDENT_DEVICE_GATE",
}
HEAD = {
    "schema": 1,
    "region": "SINNOH",
    "stage": "L06",
    "version": 1,
    "status": "PUBLIC_HUMAN_EVIDENCE_ROUTING_NO_NATIVE_AUTHORIZATION",
    "source_l05": l05.MATRIX,
    "source_l04": l05.l04.CHECKLIST,
    "source_g12": l05.HANDOFF,
    "allowed_documentary_actions": list(ACTIONS),
    "locally_received_reports": 0,
    "criteria_total": 20,
    "criteria_human_approved": 0,
    "native_cases_total": 44,
    "windows_cases": 43,
    "android_cases": 1,
    "native_cases_completed": 0,
    "native_cases_approved": 0,
    "phase_b_approved": 0,
    "phase_c_approved": 0,
    "phase_d_approved": 0,
    "r07_complete": False,
    "r08_complete": False,
    "r09_complete": False,
    "global_save_isolation_proven": False,
    "asset_rights_approved": False,
    "mapids_reserved": False,
    "windows_sandbox_executed": False,
    "joiplay_tested": False,
    "auto_upload": False,
    "can_execute_windows_qa": False,
    "can_execute_android_qa": False,
    "can_install_live_game": False,
    "sinnoh_playable": False,
}


def blocked():
    # Fixed error intentionally prevents leaking untrusted/private values.
    raise ValueError("SINNOH_L06_BLOCKED: unsafe or inconsistent documentary routing")


def same(a, b):
    """Strict recursive JSON equality (bool never equals int, no extra keys)."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    return a == b


def expected_matrix(matrix):
    """Derive only public case identifiers and criterion codes from audited L05."""
    out = dict(HEAD)
    out["rows"] = [
        {
            "case_id": r["case_id"],
            "kind": r["kind"],
            "platform": r["platform"],
            "required_criteria_ids": list(r["required_criteria_ids"]),
            "blocking_stages": list(r["blocking_stages"]),
            "human_review_queue": (
                "WINDOWS_HOST_DOCUMENTARY_REVIEW" if r["platform"] == "windows"
                else "ANDROID_DEVICE_DOCUMENTARY_REVIEW"
            ),
            "future_native_gate": (
                "WINDOWS_QA_REQUIRES_INDEPENDENT_LATER_AUTHORIZATION"
                if r["platform"] == "windows"
                else "ANDROID_QA_REQUIRES_INDEPENDENT_LATER_AUTHORIZATION"
            ),
            "documentary_check_codes": [
                *("REQUEST_" + s for s in r["required_criteria_ids"]),
                KIND_CODES[r["kind"]],
            ],
            "allowed_actions": list(ACTIONS),
            "current_action": "KEEP_PENDING",
            "review_state": "NOT_REVIEWED",
            "native_status": "pending",
            "human_evidence_accepted": False,
            "independent_reviewer_signoff": False,
            "native_qa_authorized": False,
        }
        for r in matrix["rows"]
    ]
    return out


def validate_manifest(doc, l05_matrix):
    if type(doc) is not dict or type(l05_matrix) is not dict:
        blocked()
    try:
        reference = expected_matrix(l05_matrix)
    except (KeyError, TypeError, IndexError, AttributeError):
        blocked()
    if not same(doc, reference):
        blocked()
    return True


def audit(doc, l05_matrix, checklist, handoff, l05_report, l04_report, g12_report):
    # Strictly re-validate the independent upstream chain (not just duplicated JSON).
    l05.audit(l05_matrix, checklist, handoff, l04_report, g12_report)
    if type(l05_report) is not dict or (
        l05_report.get("status") != "DOCUMENTARY_MATRIX_VALID_NATIVE_44_ALL_PENDING"
        or l05_report.get("native_cases_approved") != 0
        or l05_report.get("criteria_human_approved") != 0
        or l05_report.get("windows_cases") != 43
        or l05_report.get("android_cases") != 1
        or l05_report.get("sinnoh_playable") is not False
        or l05_report.get("native_test_can_start") is not False
    ):
        blocked()
    validate_manifest(doc, l05_matrix)
    counts = {kind: sum(r["kind"] == kind for r in doc["rows"])
              for kind in KIND_CODES}
    if counts != l05.KINDS:
        blocked()
    return {
        "schema": 1,
        "region": "SINNOH",
        "stage": "L06",
        "status": "DOCUMENTARY_REVIEW_QUEUE_VALID_44_NATIVE_BLOCKED",
        "mode": "PUBLIC_GITHUB_ONLY",
        "locally_received_reports": 0,
        "criteria_total": 20,
        "criteria_human_approved": 0,
        "native_cases_total": 44,
        "windows_cases": 43,
        "android_cases": 1,
        "native_cases_completed": 0,
        "native_cases_approved": 0,
        "cases_by_kind": counts,
        "allowed_documentary_actions": list(ACTIONS),
        "cases": [
            {
                "id": r["case_id"],
                "kind": r["kind"],
                "platform": r["platform"],
                "criteria": list(r["required_criteria_ids"]),
                "blocked_by": list(r["blocking_stages"]),
                "documentary_check_codes": list(r["documentary_check_codes"]),
                "review_queue": r["human_review_queue"],
                "future_native_gate": r["future_native_gate"],
                "action": "KEEP_PENDING",
                "review_state": "NOT_REVIEWED",
                "native_status": "pending",
                "evidence_accepted": False,
                "native_qa_authorized": False,
            }
            for r in doc["rows"]
        ],
        "windows_android_review_is_independent": True,
        "human_private_provenance_not_verified": True,
        "global_save_isolation_not_proven": True,
        "r07_mapids_not_reserved": True,
        "r08_rights_not_approved": True,
        "r09_pending": True,
        "L06_is_not_local_android_L05": True,
        "phase_b_approved": 0,
        "phase_c_approved": 0,
        "phase_d_approved": 0,
        "sinnoh_playable": False,
        "may_run_game_exe": False,
        "may_run_joiplay": False,
        "may_start_windows_sandbox": False,
        "may_install_live_game": False,
        "auto_upload": False,
    }


def run(root=ROOT):
    root = Path(root)
    reader = l05.l04.l03.l02.l00.read_json
    doc = reader(root, MATRIX, maxsize=175000)
    matrix = reader(root, l05.MATRIX, maxsize=150000)
    checklist = reader(root, l05.l04.CHECKLIST, maxsize=65536)
    handoff = reader(root, l05.HANDOFF, maxsize=150000)
    return audit(
        doc, matrix, checklist, handoff,
        l05.run(root, workspace=False),
        l05.l04.run(root, workspace=False),
        l05.G12.run(root),
    )


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv not in ([], ["--help"], ["-h"]):
        print("SINNOH_L06_BLOCKED: only public GitHub metadata allowed", file=sys.stderr)
        return 2
    if argv:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError,
            UnicodeError):
        print("SINNOH_L06_BLOCKED: public documentary audit failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
