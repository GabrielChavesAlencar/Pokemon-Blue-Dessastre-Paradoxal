#!/usr/bin/env python3
"""Conservative Sinnoh map-ID capacity study: produces NO allocation or install.

The source maps must have been audited inertly, and the installed game must
be scanned. Johto 600..999 remains protected. Never assume MapIDs >=1000 or
unclaimed IDs below 600 are safe for Sinnoh: Hoenn is still in development.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from audit_sinnoh_rxdata import audit_rxdata

LEGACY_ID_MAX = 999
JOHTO_PROTECTED = (600, 999)


def capacity(report: dict) -> dict:
    if (report.get("region"), report.get("mode"), report.get("import_allowed")) != (
            "SINNOH", "READ_ONLY_INERT_RMXP", False):
        raise ValueError("Planejamento exige auditoria Sinnoh inerte e não instalável")
    ids = report.get("source_map_ids")
    if (not isinstance(ids, list) or not ids or
            any(type(i) is not int or i < 1 for i in ids) or len(ids) != len(set(ids))):
        raise ValueError("Lista de mapas de origem incompleta ou repetida")
    native = report.get("native", {})
    if native.get("status") != "LOCAL_READ_ONLY":
        raise ValueError("É obrigatório inventariar game/Data real antes de considerar MapIDs")
    occupied = native.get("occupied_ids")
    if (not isinstance(occupied, list) or
            any(type(i) is not int or i < 1 for i in occupied)):
        raise ValueError("MapIDs nativos não foram inventariados")
    used = set(occupied)
    # This is an *upper bound* of unclaimed legacy slots, not a reservation.
    # Hoenn/other region owners may already have pending plans for these IDs.
    legacy_unclaimed = [mid for mid in range(1, LEGACY_ID_MAX + 1)
                        if mid not in used
                        and not JOHTO_PROTECTED[0] <= mid <= JOHTO_PROTECTED[1]]
    shortfall = max(0, len(ids) - len(legacy_unclaimed))
    return {
        "schema": 1, "region": "SINNOH", "mode": "CAPACITY_ONLY_NO_ALLOCATION",
        "source_map_count": len(ids),
        "native_occupied_map_count": len(used),
        "native_highest_id": max(used) if used else None,
        "protected_johto_range": list(JOHTO_PROTECTED),
        "upper_bound_unclaimed_ids_at_or_below_999": len(legacy_unclaimed),
        "provisional_unclaimed_legacy_ids": legacy_unclaimed,
        "minimum_legacy_id_shortfall_if_only_these_ids_were_available": shortfall,
        "four_digit_ids_verified_on_runtime": False,
        "hoenn_reserved_ids_fully_audited": False,
        "safe_to_allocate": False,
        "mapping": {},
        "disclaimer": (
            "These are only physically unused IDs in the local snapshot, "
            "NOT available reservations. Hoenn and other regions may own "
            "unpublished plans. Validate RMXP/Essentials 1000+ handling, "
            "all regional reservations and save compatibility before "
            "creating any persistent map-ID mapping."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True,
                        help="ZIP ou pasta RMXP com conteúdo Sinnoh legítimo")
    parser.add_argument("--game-data", type=Path, required=True,
                        help="Pasta local game/Data, lida somente para mapear ocupação")
    args = parser.parse_args()
    try:
        result = capacity(audit_rxdata(args.source, args.game_data))
    except (OSError, ValueError, KeyError, TypeError, ImportError) as exc:
        print("SINNOH_CAPACITY_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
