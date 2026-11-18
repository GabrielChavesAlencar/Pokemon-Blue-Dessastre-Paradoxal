#!/usr/bin/env python3
"""Sinnoh L18 fail-closed audit: public documentary review gaps, never native QA.

Only fixed public Git JSON and Git blobs. L17–L00/G12 ancestry is revalidated.
No host files, Game.exe, Sandbox, JoiPlay, saves, uploads or private evidence.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l17_public_review as l17

REPORT = "data/regions/sinnoh-l18-public-review-gaps.json"
MIRROR = "site/public/data/sinnoh-l18-public-review-gaps.json"
L17_MERGE = "eb1333953d02d319e9b44a96c23fe2e071bd2a2e"
L17_BLOB = "273feb1460b9200cd3c0af63cf4ebb092b8691df"

GAPS = {
    "BLOCKER_DEPENDENCY": ["UNVERIFIED_PUBLIC_DEPENDENCY", "INDEPENDENT_HUMAN_GATE_PENDING"],
    "GLOBAL_REGIONAL_GATE": ["GLOBAL_REGIONAL_SIGNOFF_NOT_REVIEWED"],
    "LOCAL_REPORT_SLOT": ["ANONYMOUS_LOCAL_REPORT_MISSING", "SLOT_IDENTITY_UNASSIGNED"],
    "HUMAN_CRITERION": ["INDEPENDENT_HUMAN_REVIEW_MISSING", "NO_PHYSICAL_EVIDENCE_ACCEPTED"],
    "BCD_PENDING_SLOT": ["ANONYMOUS_BCD_POSITION_UNASSIGNED", "BCD_SIGNOFF_PENDING"],
    "NATIVE_CASE": ["NATIVE_QA_NOT_EXECUTED", "HUMAN_GATES_PENDING",
                    "NO_NATIVE_EXECUTION_AUTHORIZATION"],
}
STEPS = {
    "BLOCKER_DEPENDENCY": "Conferir e organizar somente as referências públicas do bloqueio; manter a validação independente física fora desta fase.",
    "GLOBAL_REGIONAL_GATE": "Documentar R09 como decisão regional futura isolada, sem relacionar o gate a novos casos G12.",
    "LOCAL_REPORT_SLOT": "Manter cinco posições contábeis sem inventar relatórios, origens, nomes ou anexos.",
    "HUMAN_CRITERION": "Conferir a relação pública entre critério L04 e seus bloqueios; não preencher revisão ou signoff.",
    "BCD_PENDING_SLOT": "Preservar 13 posições B/C/D como pendências anônimas sem mapear para conteúdo físico.",
    "NATIVE_CASE": "Conferir a cobertura pública G12 de casos, plataforma e critérios L04; não executar QA nativa.",
}
POLICY = {
    "public_documentary_only": True, "gaps_are_not_human_signoffs": True,
    "next_steps_are_not_native_instructions": True,
    "no_new_case_links_to_r09": True, "priorities_are_documentary_only": True,
    "anonymous_slots_unassigned": True,
    "android_separate_from_windows_b10_b11": True,
    "no_physical_evidence_inferred": True,
    "no_uploads": True, "no_private_evidence_intake": True,
    "no_reviewer_identification": True, "no_native_execution": True,
    "no_game_exe": True, "no_windows_sandbox": True,
    "no_joiplay": True, "no_saves": True, "no_private_files": True,
    "watch_unchanged_not_global_save_isolation": True,
    "asset_rights_not_approved": True, "mapids_not_reserved": True,
    "sinnoh_playable": False,
}

def blocked():
    raise ValueError("SINNOH_L18_BLOCKED: public-only gaps or ancestry invalid")

def check_l17_blob(root=ROOT):
    for rel in (l17.INDEX, l17.MIRROR):
        p = Path(root) / rel
        if p.is_symlink() or not p.is_file():
            blocked()
        raw = p.read_bytes()
        if len(raw) > 185000:
            blocked()
        git_data = b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
        if hashlib.sha1(git_data).hexdigest() != L17_BLOB:
            blocked()
    return True

def expected_report(source):
    rows = []
    for x in source["records"]:
        kind = x["kind"]
        if kind not in GAPS:
            blocked()
        rows.append({
            "order": x["order"], "request_id": x["request_id"],
            "subject_id": x["subject_id"], "kind": kind,
            "platform": x["platform"], "priority": x["priority"],
            "priority_label": x["priority_label"],
            "gap_types": list(GAPS[kind]),
            "next_documentary_step": STEPS[kind],
            "exit_criteria_codes": list(x["exit_criteria_codes"]),
            "prerequisite_blocker_ids": list(x["prerequisite_blocker_ids"]),
            "linked_l04_criterion_ids": list(x["linked_l04_criterion_ids"]),
            "documentary_dependency_request_ids":
                list(x["documentary_dependency_request_ids"]),
            "documentary_dependency_count": x["documentary_dependency_count"],
            "anonymous_bookkeeping_slot": x["anonymous_bookkeeping_slot"],
            "review_state": "NOT_REVIEWED",
            "review_gap_status": "OPEN_DOCUMENTARY_ONLY",
            "next_step_scope": "READ_ONLY_PUBLIC_DOCUMENTATION",
            "status": "PENDING", "readiness": "BLOCKED",
            "exit_criteria_met": False, "human_signoff": False,
            "native_qa_executed": False, "native_qa_approved": False,
            "local_report_received": False, "assigned_reviewer": False,
            "source_authenticated": False,
        })
    groups = [{
        "kind": x["kind"], "requests": x["requests"],
        "blocked": x["blocked"], "documentary_links": x["documentary_links"],
        "physical_evidence_accepted": 0, "reviewed": 0, "ready": 0,
        "gap_status": "OPEN_DOCUMENTARY_ONLY",
    } for x in source["group_summary"]]
    counts = dict(source["counts"])
    counts.update({
        "gaps_total_requests": 88, "review_gaps_open": 88,
        "review_gaps_closed": 0, "documentary_next_steps": 88,
        "independent_reviews_completed": 0, "exit_criteria_met": 0,
        "physical_evidence_accepted": 0, "links_preserved": 1084,
        "unassigned_anonymous_slots": 18,
    })
    return {
        "schema": 1, "region": "SINNOH", "stage": "L18",
        "version": 1,
        "status": "PUBLIC_REVIEW_GAPS_DOCUMENTED_ALL_OPEN_NO_NATIVE_QA",
        "mode": "PUBLIC_READ_ONLY_DOCUMENTARY_HANDOFF",
        "baseline_commits":
            {**source["baseline_commits"], "L17": L17_MERGE},
        "public_sources": [
            *source["public_sources"],
            {"stage": "L17", "path": l17.INDEX, "git_blob_sha1": L17_BLOB},
        ],
        "gap_taxonomy_version": 1,
        "gap_templates": [
            {"kind": kind, "gap_types": list(gap_types),
             "next_documentary_step": STEPS[kind]}
            for kind, gap_types in GAPS.items()
        ],
        "counts": counts, "gates": dict(source["gates"]),
        "priority_rules": list(source["priority_rules"]),
        "group_summary": groups, "records": rows,
        "platform_partition": [
            {**x, "gaps_open": x["native_requests"],
             "native_authorization": False, "review_completed": False,
             "gap_status": "OPEN_DOCUMENTARY_ONLY"}
            for x in source["platform_partition"]
        ],
        "global_r09": {
            **source["global_r09"],
            "gaps_open": 1, "review_completed": False,
            "case_ids": [], "documentary_dependency_request_ids": [],
            "gap_status": "OPEN_DOCUMENTARY_ONLY",
        },
        "policy": dict(POLICY),
    }

def audit(report, mirror, source, source_mirror, l16matrix, parent_l16):
    prior = l17.audit(source, source_mirror, l16matrix, parent_l16)
    if (prior.get("status") != "PUBLIC_REVIEW_GUIDANCE_VERIFIED_ALL_UNREVIEWED"
        or prior.get("indexed_requests") != 88
        or prior.get("pending_blocked") != 88
        or prior.get("exit_criteria_met") != 0
        or prior.get("documentary_links") != 1084
        or prior.get("human_reviewed") != 0
        or prior.get("human_approved") != 0
        or prior.get("native_executed") != 0
        or prior.get("native_approved") != 0
        or prior.get("r07_pending") is not True
        or prior.get("r08_pending") is not True
        or prior.get("r09_pending") is not True
        or prior.get("r09_global_only") is not True
        or prior.get("no_private_uploads") is not True
        or prior.get("no_native_authorization") is not True
        or prior.get("sinnoh_playable") is not False):
        blocked()
    try:
        expected = expected_report(source)
        same = l17.l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.same
        if not same(report, expected) or not same(mirror, expected):
            blocked()
        rows = report["records"]
        if (len(rows) != 88 or len({r["request_id"] for r in rows}) != 88
            or sum(r["documentary_dependency_count"] for r in rows) != 1084
            or sum(r["anonymous_bookkeeping_slot"] for r in rows) != 18
            or any(r["review_gap_status"] != "OPEN_DOCUMENTARY_ONLY"
                   or r["review_state"] != "NOT_REVIEWED"
                   or r["status"] != "PENDING" or r["readiness"] != "BLOCKED"
                   or r["human_signoff"] is not False
                   or r["native_qa_executed"] is not False
                   or r["native_qa_approved"] is not False
                   or r["local_report_received"] is not False
                   or r["assigned_reviewer"] is not False
                   or r["source_authenticated"] is not False
                   for r in rows)
            or any(r["documentary_dependency_count"] != 0
                   or r["linked_l04_criterion_ids"]
                   for r in rows if r["anonymous_bookkeeping_slot"])
            or any("R09" in r["prerequisite_blocker_ids"]
                   for r in rows if r["kind"] == "NATIVE_CASE")
            or any(("B10" in r["prerequisite_blocker_ids"]
                    or "B11" in r["prerequisite_blocker_ids"])
                   for r in rows if r["kind"] == "NATIVE_CASE"
                   and r["platform"] == "android")
            or report["global_r09"]["case_ids"]
            or report["global_r09"]["documentary_dependency_request_ids"]
            or report["counts"]["review_gaps_closed"] != 0):
            blocked()
    except (KeyError, TypeError, AttributeError, IndexError):
        blocked()
    return {
        "schema": 1, "region": "SINNOH", "stage": "L18",
        "status": "PUBLIC_REVIEW_GAPS_VALID_ALL_OPEN_NO_REAL_QA",
        "baseline_commits": dict(expected["baseline_commits"]),
        "public_sources": list(expected["public_sources"]),
        "requests": 88, "requests_blocked": 88,
        "review_gaps_open": 88, "review_gaps_closed": 0,
        "documentary_next_steps": 88, "independent_reviews_completed": 0,
        "exit_criteria_met": 0, "links": 1084,
        "case_to_criterion_links": 846,
        "case_to_blocker_links": 218,
        "criterion_to_blocker_links": 20,
        "anonymous_slots": 18, "human_approved": 0,
        "native_executed": 0, "native_approved": 0,
        "windows_native_pending": 43, "android_native_pending": 1,
        "local_reports_received": 0, "phase_bcd_approved": 0,
        "phase_bcd_total": 13, "r07_pending": True,
        "r08_pending": True, "r09_pending": True,
        "r09_global_only": True,
        "no_private_uploads": True, "no_native_authorization": True,
        "sinnoh_playable": False,
    }

def run(root=ROOT):
    root = Path(root)
    # L17 run validates every public-only upstream auditor through L00 and G12.
    ancestor = l17.l16.run(root)
    check_l17_blob(root)
    read = l17.l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
    return audit(
        read(root, REPORT, maxsize=205000),
        read(root, MIRROR, maxsize=205000),
        read(root, l17.INDEX, maxsize=195000),
        read(root, l17.MIRROR, maxsize=195000),
        read(root, l17.l16.MATRIX, maxsize=185000),
        ancestor,
    )

def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ["--help"], ["-h"]):
        print("SINNOH_L18_BLOCKED: fixed public inputs only", file=sys.stderr)
        return 2
    if args:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), ensure_ascii=True, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            AttributeError, UnicodeError):
        print("SINNOH_L18_BLOCKED: invalid public review gaps or provenance",
              file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
