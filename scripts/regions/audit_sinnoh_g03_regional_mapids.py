#!/usr/bin/env python3
"""Sinnoh G03: static multiregion MapID matrix using GitHub-only metadata.

Never reads a user's game, files, saves, or binaries. No allocations, imports,
scripts executed, or native gameplay approvals. The B05 verifier is the
authoritative conservative source gate; this module adds cross-region
partition checks and exposes an explainable, fail-closed status report.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import audit_sinnoh_b05_mapid_planning as b05

B05 = "data/regions/sinnoh-b05-mapid-planning.json"
B01 = "data/regions/sinnoh-b01-actual-native.json"
B03 = "data/regions/sinnoh-b03-installer-evidence.json"
B07 = "data/regions/sinnoh-b07-private-stage.json"
UNOVA = "data/regions/unova-u03-areas.json"

IDENTIFIED = ("KANTO", "JOHTO", "HOENN")
PHYSICAL_OWNERS = {
    "BASE_OR_UNATTRIBUTED": "base_or_other_manifest_unattributed",
    "KANTO": "KANTO",
    "JOHTO": "JOHTO",
    "HOENN": "HOENN",
}
EXPECTED = {
    "BASE_OR_UNATTRIBUTED": 207,
    "KANTO": 142,
    "JOHTO": 100,
    "HOENN": 199,
}
FUTURE_REQUIRED = ("KANTO", "JOHTO", "HOENN", "UNOVA", "SINNOH")


def blocked(reason: str) -> None:
    raise ValueError("SINNOH_G03_BLOCKED: " + reason)


def ranges(ids: set[int]) -> list[dict]:
    """Compact deterministic ranges, without assigning ownership."""
    if any(type(x) is not int or x < 1 or x > 999 for x in ids):
        blocked("MapID invalido para matriz de faixa")
    out = []
    for n in sorted(ids):
        if out and n == out[-1]["end"] + 1:
            out[-1]["end"] = n
            out[-1]["count"] += 1
        else:
            out.append({"start": n, "end": n, "count": 1})
    return out


def strict_ids(entries: object, label: str) -> set[int]:
    if type(entries) is not list or len(entries) > 999:
        blocked("lista ausente ou grande demais: " + label)
    if any(type(x) is not int or x < 1 or x > 999 for x in entries):
        blocked("MapID nao inteiro ou fora de 1..999: " + label)
    if len(entries) != len(set(entries)):
        blocked("MapID duplicado: " + label)
    return set(entries)


def require_false(obj: dict, fields: tuple[str, ...], name: str) -> None:
    for field in fields:
        if obj.get(field) is not False:
            blocked("aprovacao indevida em " + name + ": " + field)


def build_matrix(catalog: dict, native: dict, installer: dict,
                 unova: dict, stage: dict) -> dict:
    # Reuse B05's frozen B01/B04 provenance / SHA / regional claims validation.
    try:
        b05.audit(catalog, native, installer, unova)
    except (ValueError, KeyError, TypeError) as exc:
        blocked("contrato B05 ou baseline B01 inconsistente")

    occupied = b05.expand(catalog["occupied"]["ranges"], limit=999)
    claims = catalog["occupied"]["identified_from_regional_manifests"]
    groups: dict[str, set[int]] = {
        "BASE_OR_UNATTRIBUTED": b05.expand(
            catalog["occupied"]["base_or_other_manifest_unattributed"]["ranges"], limit=999
        )
    }
    for region in IDENTIFIED:
        groups[region] = b05.expand(claims[region]["ranges"], limit=999)

    if any(len(groups[name]) != EXPECTED[name] for name in EXPECTED):
        blocked("contagens de procedencia divergentes")
    owners: dict[int, str] = {}
    for name, ids in groups.items():
        for mid in ids:
            if mid in owners:
                blocked("dupla atribuicao de MapID fisico: " + str(mid))
            owners[mid] = name
    if set(owners) != occupied or len(occupied) != 648:
        blocked("atibuicoes nao reconciliam 648 MapIDs fisicos")

    hold_row = catalog["sinnoh"]["administrative_planning_hold"]
    hold = set(range(hold_row["start"], hold_row["end"] + 1))
    if hold != set(range(442, 518)):
        blocked("retencao administrativa Sinnoh fora da faixa")
    if (type(stage) is not dict or stage.get("schema") != 1
            or stage.get("region") != "SINNOH" or stage.get("stage") != "B07"):
        blocked("manifesto B07 ausente ou nao pertence a Sinnoh")
    require_false(stage, (
        "r07_complete", "r08_complete", "r09_complete",
        "can_install_into_game", "rights_per_asset_verified",
        "native_game_exe_tested", "joiplay_tested"
    ), "B07")
    geometry = strict_ids(stage.get("candidate_terrain_destinations"), "geometria B07")
    empty = strict_ids(stage.get("excluded_empty_destinations"), "placeholders B07")
    if geometry != set(range(442, 496)) or empty != set(range(496, 518)):
        blocked("MapIDs da geometria/placeholder divergiram de B07")
    if len(geometry) != 54 or len(empty) != 22 or geometry & empty or geometry | empty != hold:
        blocked("particao 54+22 da retencao Sinnoh incorreta")
    if stage.get("preserves_game_data") is not True or stage.get("preserves_saves") is not True:
        blocked("B07 nao garante protecao do jogo e saves")

    candidates = b05.expand(catalog["unova"]["candidate_ranges"], limit=999)
    preferred = catalog["unova"]["preferred_contiguous_candidate"]
    proposed_window = set(range(preferred["start"], preferred["end"] + 1))
    hoenn_protected = set(range(700, 1000))
    johto_protected = set(range(600, 700))
    legacy = set(range(800, 806))
    if (candidates != set(range(1, 600)) - occupied - hold
            or len(candidates) != 174 or proposed_window != set(range(518, 600))):
        blocked("proposta Unova diverge dos vazios conservadores")
    if candidates & (occupied | hold | johto_protected | hoenn_protected):
        blocked("candidato Unova sobrepoe MapID ocupado ou protegido")
    if hold & occupied or legacy - groups["HOENN"]:
        blocked("retencao Sinnoh colide com instalacao ou legado 800..805 nao protegido")
    if not legacy <= hoenn_protected:
        blocked("legado Sinnoh nao excluido do compartilhamento")
    if preferred.get("count") != len(proposed_window):
        blocked("faixa preferida Unova incompleta")

    require_false(installer, (
        "future_reservations_reconciled", "r07_complete", "r08_complete",
        "r09_complete", "can_install", "native_game_exe_tested",
        "joiplay_tested"
    ), "B03")
    for name in ("kanto", "johto", "hoenn"):
        if installer.get("confirmed_future_ids_" + name) != []:
            blocked("reserva futura foi declarada sem reconciliar R07: " + name)
    if (unova.get("state") != "PLANNED_REFERENCE_ONLY"
            or unova.get("may_install") is not False
            or any(area.get("destination_map_id") is not None
                   for area in unova.get("areas", []))):
        blocked("Unova declarada instalada indevidamente")

    physical = []
    for name in ("BASE_OR_UNATTRIBUTED", "KANTO", "JOHTO", "HOENN"):
        physical.append({
            "scope": name,
            "kind": "NATIVE_PHYSICAL_B01_WITH_MANIFEST_ATTRIBUTION",
            "count": len(groups[name]),
            "ranges": ranges(groups[name]),
            "ownership": "manifest_attribution_not_future_exhaustive_proof",
        })

    return {
        "schema": 1,
        "region": "MULTIREGION",
        "stage": "SINNOH_G03",
        "mode": "STATIC_GITHUB_PROVENANCE_ONLY",
        "status": "STATIC_MATRIX_RECONCILED_FUTURE_RESERVATIONS_UNVERIFIED",
        "baseline": {
            "b01_reported_native_physical_maps": len(occupied),
            "mapinfos_sha256": native["mapinfos_sha256"],
            "b01_inventory_sha256": native["inventory_archive_sha256"],
            "b04_regional_attribution_is_self_reported": True,
            "native_game_reinspected_in_github_ci": False,
        },
        "physical_claims": physical,
        "sinnoh": {
            "kind": "ADMINISTRATIVE_HOLD_NOT_INSTALLED",
            "hold_range": [442, 517],
            "hold_count": len(hold),
            "geometry_staged_ids": ranges(geometry),
            "geometry_count": len(geometry),
            "empty_placeholder_ids": ranges(empty),
            "empty_placeholder_count": len(empty),
            "source_to_destination_mapping_approved": False,
            "installed_in_live_game": False,
        },
        "unova": {
            "kind": "VACANT_CANDIDATES_NOT_RESERVED_OR_INSTALLED",
            "vacant_candidates_1_to_599": len(candidates),
            "candidate_ranges": ranges(candidates),
            "preferred_window": [518, 599],
            "preferred_window_size": len(proposed_window),
            "destination_mapids_approved": False,
            "installed_in_live_game": False,
        },
        "other_protected": {
            "johto_excluded_600_to_699": len(johto_protected),
            "hoenn_excluded_700_to_999": len(hoenn_protected),
            "hoenn_protected_not_observed_899_to_999": 101,
            "legacy_sinnoh_800_to_805_within_native_hoenn_attribution": True,
            "four_digit_mapids_homologated": False,
        },
        "crosscheck": {
            "physical_region_claims_disjoint": True,
            "physical_claims_reconcile_b01": True,
            "sinnoh_hold_overlaps_native": False,
            "unova_candidates_overlap_protected_or_occupied": False,
            "vacant_1_to_599_count": len(set(range(1, 600)) - occupied),
            "hold_plus_unova_candidates": len(hold | candidates),
            "native_reserved_future_regions_approved": [],
            "legacy_sinnoh_shared_installation_allowed": False,
        },
        "unknown_future_reservations": list(FUTURE_REQUIRED),
        "blockers": [
            "B01/B04 is a recorded baseline, not a fresh scan of the user's current installation",
            "Kanto/Johto/Hoenn future MapIDs are unverified (R07 still pending)",
            "Unova 518..599 is a suggestion, not a physical or permanent reservation",
            "Sinnoh 442..517 is an administrative hold, not approved installation",
            "Legacy Sinnoh 800..805 conflicts with protected Hoenn/Johto shared space",
            "MapIDs >=1000 have no native runtime approval",
            "Per-asset rights, safe events, Windows/JoiPlay tests and save isolation pending",
        ],
        "r07_complete": False,
        "r08_complete": False,
        "r09_complete": False,
        "future_reservations_verified": False,
        "game_exe_tested": False,
        "joiplay_tested": False,
        "can_install_live_game": False,
        "phase_b_approved": 0,
        "phase_c_approved": 0,
        "phase_d_approved": 0,
    }


def run(root: Path = ROOT) -> dict:
    root = Path(root)
    return build_matrix(
        b05.load(root / B05), b05.load(root / B01),
        b05.load(root / B03), b05.load(root / UNOVA), b05.load(root / B07),
    )


if __name__ == "__main__":
    try:
        print(json.dumps(run(), ensure_ascii=False, indent=2))
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print("SINNOH_G03_BLOCKED: dados publicos invalidos ou contraditorios", file=sys.stderr)
        raise SystemExit(2)
