#!/usr/bin/env python3
"""Sinnoh L17: audit only fixed public Git-document reviewer guidance.

Review guidance and SHA-1 Git blobs never authenticate physical origin,
private files, approval, native execution, rights, MapIDs, or save isolation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l16_exit_gates as l16

INDEX = "data/regions/sinnoh-l17-public-review-index.json"
MIRROR = "site/public/data/sinnoh-l17-public-review-index.json"
L16_MERGE = "709776022679dc5831748ea4ed2254c6ced1da84"
L16_BLOB = "c9e3047106d7860bb966b5927a1fd8304506d395"

GUIDANCE = {
    "BLOCKER_DEPENDENCY": "Revisão independente futura da origem e do bloqueio identificado; integridade de JSON não é prova física.",
    "GLOBAL_REGIONAL_GATE": "Gate R09 regional global depende de decisão humana futura, sem vínculo adicional por caso.",
    "LOCAL_REPORT_SLOT": "Posição anônima de relatório: não atribuir nome, arquivo, caminho ou comprovação que não existe.",
    "HUMAN_CRITERION": "Critério L04 requer revisão humana independente e evidências autorizadas externas; nenhum signoff atual.",
    "BCD_PENDING_SLOT": "Posição contábil B/C/D anônima: não inferir o objeto, titularidade ou revisão.",
    "NATIVE_CASE": "Caso G12 não executado; QA futura depende de comprovações físicas, critérios humanos e autorização externa específica.",
}
POLICY = {
    "public_documentation_only": True,
    "review_guidance_is_not_signoff": True,
    "independent_review_not_performed": True,
    "no_evidence_intake": True, "no_private_uploads": True,
    "no_assigned_reviewers": True, "no_native_test_authority": True,
    "priority_not_execution_order": True,
    "r09_global_only": True,
    "android_not_windows_sandbox": True,
    "anonymous_slots_have_no_identity": True,
    "links_not_physical_evidence": True,
    "watch_unchanged_not_global_save_isolation": True,
    "rights_not_approved": True, "mapids_not_reserved": True,
    "no_game_exe": True, "no_windows_sandbox": True,
    "no_joiplay": True, "no_saves": True, "no_private_files": True,
    "sinnoh_playable": False,
}

def blocked():
    raise ValueError("SINNOH_L17_BLOCKED: public review index invalid or signoff forged")

def check_l16_blob(root=ROOT):
    for rel in (l16.MATRIX, l16.MIRROR):
        p = Path(root) / rel
        if p.is_symlink() or not p.is_file():
            blocked()
        data = p.read_bytes()
        if len(data) > 185000:
            blocked()
        git_blob = b"blob " + str(len(data)).encode("ascii") + b"\x00" + data
        if hashlib.sha1(git_blob).hexdigest() != L16_BLOB:
            blocked()
    return True

def expected_index(source):
    rows = []
    for x in source["records"]:
        kind = x["kind"]
        if kind not in GUIDANCE:
            blocked()
        rows.append({
            "order": x["order"], "request_id": x["request_id"],
            "subject_id": x["subject_id"], "kind": kind,
            "platform": x["platform"],
            "priority": x["priority"], "priority_label": x["priority_label"],
            "exit_criteria_codes": list(x["exit_criteria_codes"]),
            "prerequisite_blocker_ids": list(x["prerequisite_blocker_ids"]),
            "linked_l04_criterion_ids": list(x["linked_l04_criterion_ids"]),
            "documentary_dependency_request_ids": list(x["documentary_dependency_request_ids"]),
            "documentary_dependency_count": x["documentary_dependency_count"],
            "anonymous_bookkeeping_slot": x["anonymous_bookkeeping_slot"],
            "reviewer_guidance": GUIDANCE[kind],
            "review_scope": "PUBLIC_METADATA_ORIENTATION_ONLY",
            "review_state": "NOT_REVIEWED",
            "status": "PENDING", "readiness": "BLOCKED",
            "exit_criteria_met": False,
            "independent_signoff": False,
            "physical_evidence_accepted": False,
            "native_qa_authorized": False,
            "assigned_reviewer": False,
            "private_document_reference": False,
        })
    groups = [{
        "kind": g["kind"],
        "requests": g["requests"], "blocked": g["blocked"],
        "documentary_links": g["documentary_links"],
        "independent_reviews_completed": 0,
        "physical_evidence_accepted": 0,
        "review_state": "NOT_REVIEWED",
    } for g in source["group_summary"]]
    counts = dict(source["counts"])
    counts.update({
        "indexed_requests": 88, "requests_pending": 88,
        "requests_blocked": 88, "reviews_completed": 0,
        "physical_signoffs": 0, "exit_criteria_fulfilled": 0,
        "anonymous_slots_unassigned": 18,
        "review_index_documentary_links": 1084,
        "windows_native_pending": 43, "android_native_pending": 1,
    })
    return {
        "schema": 1, "region": "SINNOH", "stage": "L17", "version": 1,
        "status": "PUBLIC_REVIEWER_INDEX_ALL_UNREVIEWED_NO_NATIVE_QA",
        "mode": "PUBLIC_READ_ONLY_NO_EVIDENCE_INTAKE",
        "baseline_commits": {**source["baseline_commits"], "L16": L16_MERGE},
        "public_sources": [
            *source["public_sources"],
            {"stage": "L16", "path": l16.MATRIX, "git_blob_sha1": L16_BLOB},
        ],
        "review_guidance_version": 1,
        "review_guidance_templates": [
            {"kind": k, "guidance": v} for k, v in GUIDANCE.items()
        ],
        "counts": counts, "gates": dict(source["gates"]),
        "priority_rules": list(source["priority_rules"]),
        "group_summary": groups, "records": rows,
        "platform_partition": [
            {**p, "independent_review_complete": False,
             "source_status": "PENDING_BLOCKED"}
            for p in source["platform_partition"]
        ],
        "global_r09": {
            **source["global_r09"],
            "independent_review_complete": False,
            "source_status": "PENDING_BLOCKED",
        },
        "policy": dict(POLICY),
    }

def audit(index, mirror, source, parent_report):
    if (parent_report.get("stage") != "L16"
        or parent_report.get("status") != "PUBLIC_EXIT_GATES_VALID_ALL_UNMET"
        or parent_report.get("requests_total") != 88
        or parent_report.get("requests_blocked") != 88
        or parent_report.get("public_documentary_links") != 1084
        or parent_report.get("exit_criteria_met") != 0
        or parent_report.get("native_approved") != 0
        or parent_report.get("human_approved") != 0
        or parent_report.get("r07_pending") is not True
        or parent_report.get("r08_pending") is not True
        or parent_report.get("r09_pending") is not True
        or parent_report.get("r09_global_only") is not True
        or parent_report.get("no_private_uploads") is not True
        or parent_report.get("no_native_authorization") is not True
        or parent_report.get("sinnoh_playable") is not False):
        blocked()
    try:
        # In-memory audit callers must not bypass L16 source gate validation.
        if (len(source["records"]) != 88
            or source["counts"]["exit_ready"] != 0
            or source["counts"]["exit_criteria_met"] != 0
            or source["gates"]["r07"] != "PENDING"
            or source["gates"]["r08"] != "PENDING"
            or source["gates"]["r09"] != "PENDING"
            or any(x["human_review_completed"] is not False
                   or x["physical_evidence_received"] is not False
                   or x["native_execution_approved"] is not False
                   or x["exit_criteria_met"] is not False
                   or x["status"] != "PENDING"
                   or x["readiness"] != "BLOCKED"
                   for x in source["records"])):
            blocked()
        expected = expected_index(source)
        same = l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.same
        if not same(index, expected) or not same(mirror, expected):
            blocked()
        records = index["records"]
        if (len(records) != 88
            or len({x["request_id"] for x in records}) != 88
            or sum(x["documentary_dependency_count"] for x in records) != 1084
            or sum(x["anonymous_bookkeeping_slot"] for x in records) != 18
            or any(x["review_state"] != "NOT_REVIEWED"
                   or x["status"] != "PENDING" or x["readiness"] != "BLOCKED"
                   or x["independent_signoff"] is not False
                   or x["physical_evidence_accepted"] is not False
                   or x["native_qa_authorized"] is not False
                   or x["assigned_reviewer"] is not False
                   or x["private_document_reference"] is not False
                   for x in records)
            or any(x["documentary_dependency_count"] != 0
                   or x["linked_l04_criterion_ids"] != []
                   for x in records if x["anonymous_bookkeeping_slot"])
            or any("R09" in x["prerequisite_blocker_ids"]
                   for x in records if x["kind"] == "NATIVE_CASE")
            or any("B10" in x["prerequisite_blocker_ids"]
                   or "B11" in x["prerequisite_blocker_ids"]
                   for x in records if x["kind"] == "NATIVE_CASE"
                   and x["platform"] == "android")
            or index["global_r09"]["case_ids"] != []
            or index["global_r09"]["documentary_dependency_request_ids"] != []
            or index["counts"]["reviews_completed"] != 0):
            blocked()
    except (KeyError, TypeError, AttributeError, IndexError):
        blocked()
    return {
        "schema": 1, "region": "SINNOH", "stage": "L17",
        "status": "PUBLIC_REVIEW_GUIDANCE_VERIFIED_ALL_UNREVIEWED",
        "baseline_commits": dict(expected["baseline_commits"]),
        "public_sources": list(expected["public_sources"]),
        "indexed_requests": 88, "pending_blocked": 88,
        "exit_criteria_met": 0, "documentary_links": 1084,
        "anonymous_slots": 18, "human_reviewed": 0,
        "native_executed": 0, "native_approved": 0,
        "windows_native_pending": 43, "android_native_pending": 1,
        "local_reports_received": 0, "human_approved": 0,
        "phase_bcd_approved": 0, "phase_bcd_total": 13,
        "r07_pending": True, "r08_pending": True,
        "r09_pending": True, "r09_global_only": True,
        "no_private_uploads": True, "no_native_authorization": True,
        "sinnoh_playable": False,
    }

def run(root=ROOT):
    root = Path(root)
    # Revalidate all L16→L00/G12 public-only ancestry contracts.
    upstream = l16.run(root)
    check_l16_blob(root)
    read = l16.l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
    result = audit(
        read(root, INDEX, maxsize=195000),
        read(root, MIRROR, maxsize=195000),
        read(root, l16.MATRIX, maxsize=185000),
        upstream,
    )
    return result

def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ["-h"], ["--help"]):
        print("SINNOH_L17_BLOCKED: no arbitrary paths accepted", file=sys.stderr)
        return 2
    if args:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), ensure_ascii=True, sort_keys=True, indent=2))
        return 0
    except (ValueError, OSError, TypeError, KeyError, IndexError,
            AttributeError, UnicodeError):
        print("SINNOH_L17_BLOCKED: public-only reviewer index invalid", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
