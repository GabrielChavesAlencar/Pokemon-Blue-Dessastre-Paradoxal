#!/usr/bin/env python3
"""L16 immutable public-document exit criteria, all pending; never native approval."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l15_consistency_diff as l15

MATRIX = "data/regions/sinnoh-l16-public-exit-gates.json"
MIRROR = "site/public/data/sinnoh-l16-public-exit-gates.json"
L15_MERGE = "0192075fb02587c9f3d9db6b170500cba365251c"
PINNED = (
    ("L13", l15.l14.l13.QUEUE, "357215cdfd96b37eaac291e1c0ab3873069a12fe", l15.l14.l13.MIRROR),
    ("L14", l15.l14.MATRIX, "d882d6a20b1c01be33744f14ab7826af2fb6ef41", l15.l14.MIRROR),
    ("L15", l15.REPORT, "1a19883a3f0523add6aeaa4f78262b922a041e95", l15.MIRROR),
)
CODES = {
    "BLOCKER_DEPENDENCY": ["INDEPENDENT_BLOCKER_SOURCE_NOT_APPROVED", "APPLICABLE_HUMAN_REVIEW_PENDING"],
    "GLOBAL_REGIONAL_GATE": ["REGIONAL_R09_SIGNOFF_PENDING"],
    "LOCAL_REPORT_SLOT": ["ANONYMOUS_REPORT_SLOT_UNASSIGNED", "LOCAL_REPORT_NOT_RECEIVED"],
    "HUMAN_CRITERION": ["INDEPENDENT_L04_SIGNOFF_PENDING", "PHYSICAL_EVIDENCE_NOT_ACCEPTED"],
    "BCD_PENDING_SLOT": ["ANONYMOUS_BCD_SLOT_UNASSIGNED", "BCD_APPROVAL_PENDING"],
    "NATIVE_CASE": ["NATIVE_G12_QA_NOT_EXECUTED", "APPLICABLE_HUMAN_GATES_PENDING", "PHYSICAL_AUTHORIZATION_ABSENT"],
}
BLOCKER_TEXT = {
    "B09": "Proveniência independente da fonte física ainda não confirmada",
    "B10": "Configuração e escopo do Windows Sandbox ainda não revisados",
    "B11": "watch_unchanged não confirma isolamento global dos saves",
    "R07": "MapIDs reais e reservas regionais ainda não aprovados",
    "R08": "Direitos sobre ativos ainda não aprovados",
    "R09": "Gate de validação regional global ainda pendente",
}
POLICY = {
    "public_documentary_metadata_only": True,
    "criteria_are_future_requirements_not_signoffs": True,
    "priority_is_not_native_execution_order": True,
    "links_do_not_authenticate_physical_evidence": True,
    "anonymous_slots_not_mapped": True,
    "r09_is_global_not_case_scoped": True,
    "android_does_not_inherit_windows_b10_b11": True,
    "watch_unchanged_not_global_save_isolation": True,
    "asset_rights_not_approved": True, "mapids_not_reserved": True,
    "local_reports_received": False, "human_criteria_approved": False,
    "native_cases_executed": False,
    "no_private_inputs": True, "no_uploads": True, "no_saves": True,
    "no_game_exe": True, "no_windows_sandbox": True, "no_joiplay": True,
    "sinnoh_playable": False,
}

def blocked():
    raise ValueError("SINNOH_L16_BLOCKED: invalid public exit gate, false evidence or missing provenance")

def check_public_blobs(root=ROOT):
    root = Path(root)
    for _stage, path, sha, mirror in PINNED:
        for rel in (path, mirror):
            p = root / rel
            if p.is_symlink() or not p.is_file():
                blocked()
            raw = p.read_bytes()
            if len(raw) > 190000:
                blocked()
            git_blob = b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
            if hashlib.sha1(git_blob).hexdigest() != sha:
                blocked()
    return True

def expected_matrix(source13, source14, source15):
    if not (len(source13["queue"]) == len(source14["rows"]) == len(source15["records"]) == 88):
        blocked()
    rows = []
    for item, entry, diff in zip(source13["queue"], source14["rows"], source15["records"]):
        if (item["request_id"] != entry["request_id"]
            or entry["request_id"] != diff["request_id"]
            or item["platform"] != entry["platform"]
            or item["kind"] != entry["kind"]
            or entry["readiness"] != "BLOCKED"):
            blocked()
        kind = entry["kind"]
        if kind not in CODES:
            blocked()
        if kind == "BLOCKER_DEPENDENCY":
            description = BLOCKER_TEXT[entry["subject_id"]]
        elif kind == "GLOBAL_REGIONAL_GATE":
            description = BLOCKER_TEXT["R09"]
        elif kind in ("LOCAL_REPORT_SLOT", "BCD_PENDING_SLOT"):
            description = "Slot contábil anônimo sem identidade física atribuída"
        elif kind == "HUMAN_CRITERION":
            description = "Revisão independente de critério L04 ainda não realizada"
        else:
            description = "Caso G12 sem execução nativa ou autorização física"
        rows.append({
            "order": entry["order"], "request_id": entry["request_id"],
            "subject_id": entry["subject_id"], "kind": kind,
            "platform": entry["platform"],
            "priority": entry["priority"],
            "priority_label": entry["priority_label"],
            "documentary_dependency_request_ids": list(entry["documentary_dependency_request_ids"]),
            "documentary_dependency_count": entry["documentary_dependency_count"],
            "prerequisite_blocker_ids": list(item["blocker_ids"]),
            "linked_l04_criterion_ids": list(item["criterion_ids"]),
            "exit_criteria_codes": list(CODES[kind]),
            "criterion_description": description,
            "anonymous_bookkeeping_slot": entry["anonymous_bookkeeping_slot"],
            "scope_known": entry["scope_known"],
            "documentary_check": "PUBLIC_METADATA_LINKS_VERIFIED",
            "physical_source_verified": False,
            "human_review_completed": False,
            "physical_evidence_received": False,
            "native_execution_approved": False,
            "exit_criteria_met": False,
            "readiness": "BLOCKED", "status": "PENDING",
            "action_authorization": "NONE",
        })
    group_summary = []
    for kind in CODES:
        group = [r for r in rows if r["kind"] == kind]
        group_summary.append({
            "kind": kind, "requests": len(group), "blocked": len(group),
            "criteria_met": 0, "physical_signoffs": 0,
            "documentary_links": sum(r["documentary_dependency_count"] for r in group),
            "state": "PENDING_BLOCKED",
        })
    counts = dict(source15["counts"])
    counts.update({
        "exit_rows": 88, "exit_blocked": 88, "exit_ready": 0,
        "exit_criteria_met": 0, "required_human_reviews_pending": 20,
        "required_native_cases_pending": 44,
        "global_r09_pending": 1, "anonymous_unassigned": 18,
        "documentary_link_count": 1084, "physical_evidence_accepted": 0,
    })
    return {
        "schema": 1, "region": "SINNOH", "stage": "L16",
        "version": 1,
        "status": "EXIT_CRITERIA_DOCUMENTED_ALL_PENDING_NO_NATIVE_AUTHORIZATION",
        "mode": "PUBLIC_READ_ONLY_EXIT_GATE_REGISTER",
        "baseline_commits": {**source15["baseline_commits"], "L15": L15_MERGE},
        "public_sources": [
            {"stage": stage, "path": path, "git_blob_sha1": sha}
            for stage, path, sha, _mirror in PINNED
        ],
        "exit_criteria_version": 1,
        "exit_code_templates": [
            {"kind": kind, "exit_criteria_codes": list(codes)}
            for kind, codes in CODES.items()
        ],
        "counts": counts, "gates": dict(source15["gates"]),
        "priority_rules": list(source15["priority_rules"]),
        "group_summary": group_summary, "records": rows,
        "platform_partition": [
            {**p, "exit_met": 0, "exit_state": "BLOCKED", "native_authorization": False}
            for p in source15["platform_partition"]
        ],
        "global_r09": {
            "id": "R09", "status": "PENDING", "case_ids": [],
            "documentary_dependency_request_ids": [],
            "exit_criteria_codes": list(CODES["GLOBAL_REGIONAL_GATE"]),
            "exit_met": False, "global_gate_only": True, "approval": False,
        },
        "policy": dict(POLICY),
    }

def audit(matrix, mirror, l15report, l15mirror, l14matrix, l14mirror,
          l13queue, l13mirror, report12, mirror12, graph, graphmirror,
          index, indexmirror, packet, *l08_inputs):
    if len(l08_inputs) != 13:
        blocked()
    prev = l15.audit(
        l15report, l15mirror, l14matrix, l14mirror,
        l13queue, l13mirror, report12, mirror12, graph, graphmirror,
        index, indexmirror, packet, *l08_inputs
    )
    if (prev["status"] != "PUBLIC_CONSISTENCY_VALID_PHYSICAL_QA_PENDING"
        or prev["request_rows_matched"] != 88
        or prev["documentary_links"] != 1084
        or prev["native_approved"] != 0 or prev["human_approved"] != 0
        or prev["sinnoh_playable"] is not False):
        blocked()
    try:
        expected = expected_matrix(l13queue, l14matrix, l15report)
        same = l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.same
        if not same(matrix, expected) or not same(mirror, expected):
            blocked()
        rec = matrix["records"]
        if (len(rec) != 88 or len({r["request_id"] for r in rec}) != 88
            or sum(r["documentary_dependency_count"] for r in rec) != 1084
            or sum(r["anonymous_bookkeeping_slot"] for r in rec) != 18
            or any(r["status"] != "PENDING" or r["readiness"] != "BLOCKED"
                   or r["exit_criteria_met"] is not False
                   or r["native_execution_approved"] is not False
                   or r["human_review_completed"] is not False
                   or r["physical_evidence_received"] is not False
                   or r["action_authorization"] != "NONE"
                   for r in rec)
            or any(r["documentary_dependency_count"] != 0
                   for r in rec if r["anonymous_bookkeeping_slot"])
            or matrix["global_r09"]["case_ids"] != []
            or matrix["global_r09"]["documentary_dependency_request_ids"] != []
            or matrix["counts"]["exit_ready"] != 0):
            blocked()
    except (KeyError, TypeError, IndexError, AttributeError):
        blocked()
    return {
        "schema": 1, "region": "SINNOH", "stage": "L16",
        "status": "PUBLIC_EXIT_GATES_VALID_ALL_UNMET",
        "baseline_commits": dict(expected["baseline_commits"]),
        "public_sources": list(expected["public_sources"]),
        "requests_total": 88, "requests_blocked": 88, "exit_criteria_met": 0,
        "public_documentary_links": 1084,
        "anonymous_slots": 18, "human_criteria_pending": 20,
        "native_cases_pending": 44,
        "windows_native_pending": 43, "android_native_pending": 1,
        "local_reports_received": 0, "human_approved": 0,
        "native_executed": 0, "native_approved": 0,
        "phase_bcd_approved": 0, "phase_bcd_total": 13,
        "r07_pending": True, "r08_pending": True, "r09_pending": True,
        "r09_global_only": True, "no_private_uploads": True,
        "no_native_authorization": True, "sinnoh_playable": False,
    }

def run(root=ROOT):
    root = Path(root)
    l15.l14.l13.l12.l11.l10.l09.l08.check_pinned_blobs(root)
    l15.l14.l13.l12.l11.l10.l09.check_source_blobs(root)
    l15.l14.l13.l12.l11.l10.check_l09_blob(root)
    l15.l14.l13.l12.l11.check_l10_blob(root)
    l15.l14.l13.l12.check_public_l11_blobs(root)
    l15.l14.l13.check_l12_public_blobs(root)
    l15.l14.check_l13_public_blobs(root)
    l15.check_l13_l14_blobs(root)
    check_public_blobs(root)
    read = l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
    refs = {k: read(root, p, maxsize=175000)
            for k, p, _ in l15.l14.l13.l12.l11.l10.l09.l08.PINNED}
    args = [
        read(root, MATRIX, maxsize=185000),
        read(root, MIRROR, maxsize=185000),
        read(root, l15.REPORT, maxsize=145000),
        read(root, l15.MIRROR, maxsize=145000),
        read(root, l15.l14.MATRIX, maxsize=180000),
        read(root, l15.l14.MIRROR, maxsize=180000),
        read(root, l15.l14.l13.QUEUE, maxsize=190000),
        read(root, l15.l14.l13.MIRROR, maxsize=190000),
        read(root, l15.l14.l13.l12.REPORT, maxsize=145000),
        read(root, l15.l14.l13.l12.MIRROR, maxsize=145000),
        read(root, l15.l14.l13.l12.l11.GRAPH, maxsize=200000),
        read(root, l15.l14.l13.l12.l11.MIRROR, maxsize=200000),
        read(root, l15.l14.l13.l12.l11.l10.INDEX, maxsize=155000),
        read(root, l15.l14.l13.l12.l11.l10.MIRROR, maxsize=155000),
        read(root, l15.l14.l13.l12.l11.l10.l09.PACKET, maxsize=155000),
        read(root, l15.l14.l13.l12.l11.l10.l09.l08.SNAPSHOT, maxsize=125000),
        read(root, l15.l14.l13.l12.l11.l10.l09.l08.DIFF, maxsize=16000),
        *(refs[k] for k in ("G12", "L04", "L05", "L06", "L07", "L07_SITE")),
        l15.l14.l13.l12.l11.l10.l09.l08.l07.run(root),
        l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.run(root),
        l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.run(root),
        l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.l04.run(root),
        l15.l14.l13.l12.l11.l10.l09.l08.l07.l06.l05.G12.run(root),
    ]
    return audit(*args)

def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args not in ([], ["--help"], ["-h"]):
        print("SINNOH_L16_BLOCKED: fixed public inputs only", file=sys.stderr)
        return 2
    if args:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), ensure_ascii=True, sort_keys=True, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, UnicodeError):
        print("SINNOH_L16_BLOCKED: public criteria or provenance invalid", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
