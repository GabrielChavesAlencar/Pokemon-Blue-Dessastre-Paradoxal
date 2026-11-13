"""Plan isolated Johto map slots, never writing to game/ or importing foreign events.

The plan is deliberately unusable as an installer: source audit, names and
source hashes are prerequisites. Keep an append-only mapping for old saves.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from audit_johto import DEFAULT_MANIFEST, DEFAULT_REPORT, ROOT, write_report

NAME = re.compile(r"^[A-Z][A-Z0-9_]{2,70}$")
SOURCE_ID = re.compile(r"^[1-9][0-9]*$")
ID_FLOOR, ID_LIMIT = 600, 999


def read_json(path: Path) -> dict:
    result = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(result, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return result


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan(manifest: dict, report: dict, *, previous: dict | None = None) -> dict:
    """Allocate only manually confirmed Johto maps, preserving previous slots."""
    if (manifest.get("schema"), manifest.get("region")) != (1, "JOHTO"):
        raise ValueError("Wrong Johto manifest")
    if (report.get("schema"), report.get("region"), report.get("mode")) != (
        1, "JOHTO", "READ_ONLY_NO_INSTALL"
    ):
        raise ValueError("Johto plan needs a genuine read-only source report")
    if report.get("can_install") is not False:
        raise ValueError("Source report must prohibit installing")
    if not isinstance(report.get("maps"), list) or not report["maps"]:
        raise ValueError("No inventoried Johto source maps")
    game = report.get("game", {})
    if not game.get("present"):
        raise ValueError("A read-only snapshot of the installed game is required")
    current_ids = set(game.get("existing_ids", []))
    current_ids.update(game.get("registered_ids", []))
    if any(type(i) is not int or i < 1 or i > ID_LIMIT for i in current_ids):
        raise ValueError("Unexpected existing map IDs; do not guess an allocation")
    audited = {}
    for row in report["maps"]:
        num, name, digest = row.get("source_id"), row.get("name"), row.get("sha256")
        if (type(num) is not int or num in audited or
                not isinstance(name, str) or
                not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest)):
            raise ValueError("Incomplete, repeated or corrupt map audit")
        audited[num] = row

    selection = manifest.get("maps", {})
    if not isinstance(selection, dict):
        raise ValueError("manifest.maps must be an object of audited IDs and Johto keys")
    wanted = {}
    for raw_id, key in selection.items():
        if (not isinstance(raw_id, str) or not SOURCE_ID.fullmatch(raw_id)
                or int(raw_id) not in audited or not isinstance(key, str)
                or not NAME.fullmatch(key) or not key.startswith("JOHTO_")):
            raise ValueError(f"Unverified Johto map selection {raw_id!r}={key!r}")
        if key in wanted.values():
            raise ValueError("Duplicate symbolic map name")
        wanted[int(raw_id)] = key

    old = previous.get("mapping", {}) if previous is not None else {}
    if not isinstance(old, dict):
        raise ValueError("Prior Johto plan has no valid mapping")
    if previous is not None:
        if (previous.get("schema"), previous.get("region")) != (1, "JOHTO"):
            raise ValueError("Previous map plan belongs to another region")
    mapping = {}
    used = set(current_ids)
    previous_ids = set()
    for raw_src, raw_dst in old.items():
        if (not isinstance(raw_src, str) or not SOURCE_ID.fullmatch(raw_src)
                or type(raw_dst) is not int or not ID_FLOOR <= raw_dst <= ID_LIMIT
                or raw_dst in used or raw_dst in previous_ids
                or int(raw_src) not in wanted):
            raise ValueError("Prior Johto IDs conflict, disappeared or are invalid")
        if previous.get("symbols", {}).get(raw_src) != wanted[int(raw_src)]:
            raise ValueError("Existing Johto symbolic key was changed")
        previous_ids.add(raw_dst)
        mapping[int(raw_src)] = raw_dst
    used.update(previous_ids)

    next_id = max(ID_FLOOR, max(used, default=ID_FLOOR - 1) + 1)
    for source_id in sorted(wanted):
        if source_id in mapping:
            continue
        while next_id in used:
            next_id += 1
        if next_id > ID_LIMIT:
            raise ValueError("No available Johto map IDs in supported 600–999 range")
        mapping[source_id] = next_id
        used.add(next_id)
        next_id += 1

    pinned = manifest.get("source", {}).get("archive_sha256")
    digest_ok = (isinstance(pinned, str)
                 and re.fullmatch(r"[a-f0-9]{64}", pinned) is not None
                 and report.get("archive_hash_pinned_and_verified") is True
                 and report.get("source_archive_sha256") == pinned)
    missing = []
    if not wanted:
        missing.append("NO_VERIFIED_JOHTO_MAP_SELECTION")
    if not digest_ok:
        missing.append("SOURCE_ARCHIVE_HASH_NOT_VERIFIED")
    if not manifest.get("mapping_verified"):
        missing.append("SOURCE_MAPS_NOT_CONFIRMED")
    if report.get("missing_tileset_ids"):
        missing.append("MISSING_TILESETS")
    # The uploaded v1 resource has a MapInfo container for Intro (ID 1)
    # without Map001.rxdata. Only explicitly audited, unselected metadata
    # entries may be omitted; all other missing/orphan files block staging.
    accepted_missing = manifest.get("source", {}).get("accepted_missing_mapinfo_ids", [])
    if (not isinstance(accepted_missing, list) or
            any(type(i) is not int or i <= 0 or i in wanted
                for i in accepted_missing) or
            len(set(accepted_missing)) != len(accepted_missing)):
        raise ValueError("Invalid selected/duplicate missing MapInfos exception")
    reported_missing = report.get("missing_map_files", [])
    if (not isinstance(reported_missing, list) or
            any(type(i) is not int or i <= 0 for i in reported_missing)):
        raise ValueError("Invalid source missing MapInfos report")
    if report.get("orphan_map_files") or set(reported_missing) - set(accepted_missing):
        missing.append("MAPINFOS_MISMATCH")

    # This is a PREVIEW plan, not a license or installer approval.
    return {
        "schema": 1, "region": "JOHTO",
        "status": "READY_FOR_GEOMETRY_PREVIEW" if not missing else "BLOCKED",
        "can_install": False,
        "blocking_reasons": missing,
        "source_archive_sha256": pinned,
        "source_map_hashes": {str(n): audited[n]["sha256"] for n in sorted(wanted)},
        "source_mapinfos_sha256": report.get("mapinfos_sha256"),
        "source_tilesets_sha256": report.get("tilesets_sha256"),
        "original_names": {str(n): audited[n]["name"] for n in sorted(wanted)},
        "symbols": {str(n): wanted[n] for n in sorted(wanted)},
        "mapping": {str(n): mapping[n] for n in sorted(mapping)},
        "protected_game_hashes": game.get("protected_hashes", {}),
        "existing_map_ids": sorted(current_ids),
        "warnings": ["Proposed IDs are not an authorization to install anything.",
                     "Every re-run must supply --previous to preserve frozen Johto IDs.",
                     "Original foreign event scripts must not be copied to the Blue game."]
    }


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    cli.add_argument("--audit", type=Path, default=DEFAULT_REPORT)
    cli.add_argument("--previous", type=Path, help="Previous frozen Johto preview plan")
    cli.add_argument("--output", type=Path, default=ROOT / ".blue-work/johto-map-plan.json")
    args = cli.parse_args(argv)
    try:
        manifest, report = read_json(args.manifest), read_json(args.audit)
        previous = read_json(args.previous) if args.previous else None
        result = plan(manifest, report, previous=previous)
        write_report(args.output, result)
    except (OSError, TypeError, KeyError, ValueError) as error:
        print("[JOHTO][BLOQUEADO] " + str(error), file=sys.stderr)
        return 2
    print(f"[JOHTO] {len(result['mapping'])} mapas selecionados. Estado: {result['status']}.")
    print("[JOHTO] Plano de PREVIA, sem alterar Decades, Kanto ou saves.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
