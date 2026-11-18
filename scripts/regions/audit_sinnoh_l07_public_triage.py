#!/usr/bin/env python3
"""Sinnoh L07: fail-closed public read-only triage, sourced from audited L06/L04/G12.

GitHub-only fixed public JSON inputs. No host, Game.exe, Sandbox, JoiPlay,
saves, private paths, remote calls, runtime tokens, or user upload.
This documentary L07 never approves human evidence or native tests.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l06_human_evidence as l06

SOURCE = "data/regions/sinnoh-l07-public-triage.json"
MIRROR = "site/public/data/sinnoh-l07-public-triage.json"
HEAD = {
    "schema": 1,
    "region": "SINNOH",
    "stage": "L07",
    "version": 1,
    "status": "PUBLIC_READ_ONLY_TRIAGE_ALL_NATIVE_PENDING",
    "mode": "GITHUB_STATIC_DOCUMENTARY_ONLY",
    "source_l06": l06.MATRIX,
    "source_l05": l06.l05.MATRIX,
    "source_l04": l06.l05.l04.CHECKLIST,
    "source_g12": l06.l05.HANDOFF,
    "allowed_documentary_actions": list(l06.ACTIONS),
    "current_action": "KEEP_PENDING",
}
COUNTS = {
    "cases_total": 44,
    "windows": 43,
    "android": 1,
    "criteria_total": 20,
    "human_approved": 0,
    "native_completed": 0,
    "native_approved": 0,
    "local_reports": 0,
    "phase_bcd_completed": 0,
    "phase_bcd_total": 13,
}
GATES = {
    "r07": "PENDING",
    "r08": "PENDING",
    "r09": "PENDING",
    "b11_global_save_isolation_proven": False,
    "mapids_reserved": False,
    "asset_rights_approved": False,
    "windows_sandbox_executed": False,
    "joiplay_tested": False,
    "phase_b_approved": 0,
    "phase_c_approved": 0,
    "phase_d_approved": 0,
    "sinnoh_playable": False,
    "can_launch_game_exe": False,
    "can_launch_joiplay": False,
    "can_start_windows_sandbox": False,
    "can_install_live_game": False,
    "auto_upload": False,
}

def blocked():
    # Constant error: never echo arbitrary/private values.
    raise ValueError("SINNOH_L07_BLOCKED: invalid or unsafe public triage")

def expected_document(l06_doc, l04_doc):
    # Run ONLY after the L06/L04/L05/G12 chain has been independently audited.
    rows = l06_doc["rows"]
    criteria = [{
        "id": c["id"],
        "stage": stage["stage"],
        "requirement": c["requirement"],
        "status": "NOT_REVIEWED",
        "human_signoff": False,
        "physical_evidence_accepted": False,
        "dependent_cases": sum(c["id"] in r["required_criteria_ids"] for r in rows),
        "windows_dependencies": sum(r["platform"] == "windows"
                                    and c["id"] in r["required_criteria_ids"]
                                    for r in rows),
        "android_dependencies": sum(r["platform"] == "android"
                                    and c["id"] in r["required_criteria_ids"]
                                    for r in rows),
    } for stage in l04_doc["rows"] for c in stage["criteria"]]
    cases = [{
        "id": r["case_id"],
        "kind": r["kind"],
        "platform": r["platform"],
        "required_criteria_ids": list(r["required_criteria_ids"]),
        "blocked_by": list(r["blocking_stages"]),
        "documentary_check_codes": list(r["documentary_check_codes"]),
        "review_queue": r["human_review_queue"],
        "future_native_gate": r["future_native_gate"],
        "action": "KEEP_PENDING",
        "review_state": "NOT_REVIEWED",
        "native_status": "pending",
        "evidence_accepted": False,
        "native_qa_authorized": False,
    } for r in rows]
    queues = [{
        "platform": p,
        "count": sum(r["platform"] == p for r in cases),
        "case_ids": [r["id"] for r in cases if r["platform"] == p],
        "native_gate": (
            "WINDOWS_QA_REQUIRES_INDEPENDENT_LATER_AUTHORIZATION" if p == "windows"
            else "ANDROID_QA_REQUIRES_INDEPENDENT_LATER_AUTHORIZATION"
        ),
        "documentary_only": True,
        "approved": False,
    } for p in ("windows", "android")]
    return {**HEAD, "counts": dict(COUNTS), "gates": dict(GATES),
            "platform_queues": queues, "criteria": criteria, "cases": cases}


def audit(doc, mirror, l06_doc, l05_doc, l04_doc, g12_doc,
          l06_report, l05_report, l04_report, g12_report):
    try:
        verified = l06.audit(l06_doc, l05_doc, l04_doc, g12_doc,
                             l05_report, l04_report, g12_report)
        if not l06.l05.l04.l03.l02.l00.g12:
            blocked()
        if not l06.l05.l04.validate_checklist(l04_doc):
            blocked()
        if not l06.same(l06_report, verified):
            blocked()
        if (verified["native_cases_total"] != 44
            or verified["native_cases_approved"] != 0
            or verified["criteria_human_approved"] != 0
            or verified["windows_cases"] != 43
            or verified["android_cases"] != 1
            or verified["sinnoh_playable"] is not False):
            blocked()
        reference = expected_document(l06_doc, l04_doc)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError):
        blocked()
    if (not l06.same(doc, reference)
        or not l06.same(mirror, reference)
        or type(doc["cases"]) is not list
        or len({r["id"] for r in doc["cases"]}) != 44
        or len({r["id"] for r in doc["criteria"]}) != 20
        or any(r["platform"] == "android"
               and ("B10" in r["blocked_by"] or "B11" in r["blocked_by"])
               for r in doc["cases"])
        or any(r["platform"] == "windows"
               and ("B10" not in r["blocked_by"] or "B11" not in r["blocked_by"])
               for r in doc["cases"])):
        blocked()
    return {
        "schema": 1,
        "region": "SINNOH",
        "stage": "L07",
        "status": "PUBLIC_READ_ONLY_TRIAGE_ALL_NATIVE_PENDING",
        "mode": "GITHUB_STATIC_DOCUMENTARY_ONLY",
        "counts": dict(COUNTS),
        "gates": dict(GATES),
        "cases": list(doc["cases"]),
        "criteria": list(doc["criteria"]),
        "platform_queues": list(doc["platform_queues"]),
        "allowed_documentary_actions": list(l06.ACTIONS),
        "current_action": "KEEP_PENDING",
        "windows_android_review_is_independent": True,
        "physical_proof_accepted": False,
        "global_save_isolation_proven": False,
        "native_qa_authorized": False,
        "sinnoh_playable": False,
        "l07_is_not_android_g12_local_l05": True,
    }


def run(root=ROOT):
    root = Path(root)
    reader = l06.l05.l04.l03.l02.l00.read_json
    doc = reader(root, SOURCE, maxsize=175000)
    mirror = reader(root, MIRROR, maxsize=175000)
    source_l06 = reader(root, l06.MATRIX, maxsize=175000)
    source_l05 = reader(root, l06.l05.MATRIX, maxsize=150000)
    source_l04 = reader(root, l06.l05.l04.CHECKLIST, maxsize=65536)
    source_g12 = reader(root, l06.l05.HANDOFF, maxsize=150000)
    return audit(doc, mirror, source_l06, source_l05, source_l04, source_g12,
                 l06.run(root), l06.l05.run(root), l06.l05.l04.run(root),
                 l06.l05.G12.run(root))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv not in ([], ["--help"], ["-h"]):
        print("SINNOH_L07_BLOCKED: only public fixed inputs permitted", file=sys.stderr)
        return 2
    if argv:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            UnicodeError):
        print("SINNOH_L07_BLOCKED: public triage audit failed", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
