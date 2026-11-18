#!/usr/bin/env python3
"""Sinnoh L10: fail-closed public read-only 44-case/20-criterion blocker index.

Revalidates L09/L08/L07/L06/L05/L04/G12. Checks only fixed public GitHub
files; no PC, save, private paths, game runtime, Windows Sandbox or JoiPlay.
A Git object ID proves a byte match, not human evidence or runtime rights.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l09_public_handoff as l09

INDEX = "data/regions/sinnoh-l10-public-blocker-index.json"
MIRROR = "site/public/data/sinnoh-l10-public-blocker-index.json"
L09_BLOB = "1245ceab070796455da4772ddab0ce974f80605d"
L09_MERGE = "39e51de92aafdab3f5aea3f929f57f5c0bb72b2d"
DESCRIPTIONS = {
    "B09": "Proveniência independente de origem e clone físico não comprovada",
    "B10": "Configuração Windows Sandbox não verificada em host independente",
    "B11": "Escopo limitado dos saves não comprova isolamento global nem vínculo de sessão",
    "R07": "MapIDs reais, conflitos e reservas regionais não validados",
    "R08": "Direitos de ativos, gráficos, eventos e PBS ainda não aprovados",
    "R09": "Gate regional posterior ainda pendente; não constitui teste nativo nem prova física",
}
STAGES = ("B09", "B10", "B11", "R07", "R08")


def blocked():
    # Prevent exposing untrusted identifiers, paths, tokens or save names.
    raise ValueError("SINNOH_L10_BLOCKED: public index integrity or safety violation")


def check_l09_blob(root=ROOT):
    """Check exact Git blob SHA-1 of a fixed public document, not private sources."""
    p = Path(root) / l09.PACKET
    if p.is_symlink() or not p.is_file():
        blocked()
    raw = p.read_bytes()
    if len(raw) > 155000:
        blocked()
    blob = b"blob " + str(len(raw)).encode("ascii") + b"\x00" + raw
    if hashlib.sha1(blob).hexdigest() != L09_BLOB:
        blocked()
    return True


def expected_index(packet):
    cases = [{
        "id": row["case_id"],
        "kind": row["kind"],
        "platform": row["platform"],
        "criteria": list(row["required_criteria_ids"]),
        "blocked_by": list(row["blocked_by"]),
        "queue": row["reviewer_lane"],
        "native_gate": row["future_native_gate"],
        "review_state": "NOT_REVIEWED",
        "action": "KEEP_PENDING",
        "native_status": "pending",
        "approved": False,
        "native_execution_authorized": False,
    } for row in packet["case_handoff"]]
    criteria = [{
        "id": t["criterion_id"],
        "stage": t["stage"],
        "requirement": t["public_requirement"],
        "case_ids": [
            row["case_id"] for row in packet["case_handoff"]
            if t["criterion_id"] in row["required_criteria_ids"]
        ],
        "windows_cases": t["windows_cases"],
        "android_cases": t["android_cases"],
        "review_state": "NOT_REVIEWED",
        "signoff": False,
    } for t in packet["review_tasks"]]
    blockers = []
    for stage in STAGES:
        rows = [row for row in cases if stage in row["blocked_by"]]
        blockers.append({
            "id": stage,
            "description": DESCRIPTIONS[stage],
            "scope": "WINDOWS_ONLY" if stage in ("B10", "B11") else "CROSS_PLATFORM",
            "status": "PENDING",
            "case_ids": [row["id"] for row in rows],
            "windows_cases": sum(row["platform"] == "windows" for row in rows),
            "android_cases": sum(row["platform"] == "android" for row in rows),
            "not_a_native_approval": True,
        })
    blockers.append({
        "id": "R09", "description": DESCRIPTIONS["R09"],
        "scope": "GLOBAL_REGION_PENDING_NOT_CASE_GATE",
        "status": "PENDING",
        "case_ids": [],
        "windows_cases": 0,
        "android_cases": 0,
        "not_a_native_approval": True,
    })
    return {
        "schema": 1, "region": "SINNOH", "stage": "L10", "version": 1,
        "status": "PUBLIC_BLOCKER_INDEX_ONLY_ALL_PENDING",
        "mode": "PUBLIC_GITHUB_READ_ONLY",
        "baseline_commits": {
            "L07": l09.l08.ANCHOR,
            "L08": l09.L08_MERGE,
            "L09": L09_MERGE,
        },
        "source_l09": {"path": l09.PACKET, "git_blob_sha1": L09_BLOB},
        "counts": dict(l09.l08.l07.COUNTS),
        "gates": dict(l09.l08.l07.GATES),
        "global_r09_pending": True,
        "windows_android_review_independent": True,
        "watch_unchanged_not_global_isolation": True,
        "asset_rights_not_approved": True,
        "mapids_not_reserved": True,
        "can_run_game_exe": False,
        "can_run_windows_sandbox": False,
        "can_run_joiplay": False,
        "can_install_live_game": False,
        "sinnoh_playable": False,
        "local_android_l05_completed": False,
        "criteria": criteria,
        "cases": cases,
        "blockers": blockers,
    }


def audit(index, mirror, packet, *l08_inputs):
    if len(l08_inputs) != 13:
        blocked()
    verified = l09.audit(packet, *l08_inputs)
    if (verified["status"] != "PUBLIC_HUMAN_HANDOFF_VALID_NO_APPROVAL"
        or verified["cases_total"] != 44
        or verified["criteria_total"] != 20
        or verified["human_reviews_accepted"] != 0
        or verified["native_cases_completed"] != 0
        or verified["native_cases_approved"] != 0
        or verified["sinnoh_playable"] is not False):
        blocked()
    try:
        expected = expected_index(packet)
        same = l09.l08.l07.l06.same
        if not same(index, expected) or not same(mirror, expected):
            blocked()
        if (len(index["cases"]) != 44
            or len(index["criteria"]) != 20
            or len({c["id"] for c in index["cases"]}) != 44
            or len({c["id"] for c in index["criteria"]}) != 20
            or [r["id"] for r in index["blockers"]] != list(STAGES) + ["R09"]
            or any(c["platform"] == "android" and (
                "B10" in c["blocked_by"] or "B11" in c["blocked_by"])
                for c in index["cases"])
            or any(c["platform"] == "windows" and (
                "B10" not in c["blocked_by"] or "B11" not in c["blocked_by"])
                for c in index["cases"])):
            blocked()
    except (KeyError, TypeError, IndexError, AttributeError):
        blocked()
    return {
        "schema": 1, "region": "SINNOH", "stage": "L10",
        "status": "PUBLIC_INDEX_VALID_NATIVE_PENDING",
        "baseline_commits": dict(index["baseline_commits"]),
        "source_l09_blob_verified": L09_BLOB,
        "counts": dict(l09.l08.l07.COUNTS),
        "cases_total": 44, "windows_cases": 43, "android_cases": 1,
        "criteria_total": 20, "criteria_human_approved": 0,
        "native_completed": 0, "native_approved": 0, "local_reports": 0,
        "blocker_ids": list(STAGES) + ["R09"],
        "global_r09_pending": True,
        "windows_android_review_independent": True,
        "r07_pending": True,
        "r08_pending": True,
        "r09_pending": True,
        "b11_global_isolation_proven": False,
        "mapids_reserved": False,
        "asset_rights_approved": False,
        "can_run_game_exe": False,
        "can_run_windows_sandbox": False,
        "can_run_joiplay": False,
        "can_install_live_game": False,
        "sinnoh_playable": False,
        "case_ids": [c["id"] for c in index["cases"]],
        "criteria_ids": [c["id"] for c in index["criteria"]],
        "cases_pending": 44,
        "criteria_unreviewed": 20,
    }


def run(root=ROOT):
    root = Path(root)
    l09.l08.check_pinned_blobs(root)
    l09.check_source_blobs(root)
    check_l09_blob(root)
    reader = l09.l08.l07.l06.l05.l04.l03.l02.l00.read_json
    docs = {
        stage: reader(root, path, maxsize=175000)
        for stage, path, _sha in l09.l08.PINNED
    }
    index = reader(root, INDEX, maxsize=155000)
    mirror = reader(root, MIRROR, maxsize=155000)
    packet = reader(root, l09.PACKET, maxsize=155000)
    snap = reader(root, l09.l08.SNAPSHOT, maxsize=125000)
    diff = reader(root, l09.l08.DIFF, maxsize=16000)
    return audit(
        index, mirror, packet,
        snap, diff, docs["G12"], docs["L04"], docs["L05"], docs["L06"],
        docs["L07"], docs["L07_SITE"],
        l09.l08.l07.run(root), l09.l08.l07.l06.run(root),
        l09.l08.l07.l06.l05.run(root), l09.l08.l07.l06.l05.l04.run(root),
        l09.l08.l07.l06.l05.G12.run(root),
    )


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv not in ([], ["--help"], ["-h"]):
        print("SINNOH_L10_BLOCKED: only fixed public inputs allowed", file=sys.stderr)
        return 2
    if argv:
        print(__doc__)
        return 0
    try:
        print(json.dumps(run(), ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            AttributeError, UnicodeError):
        print("SINNOH_L10_BLOCKED: index or upstream source invalid", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
