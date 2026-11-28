#!/usr/bin/env python3
"""MapID census for an exact historical fixture, not an allocator or current-world proof."""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts/regions")]
from audit_unova_a04_mapids import MAX_FILE_BYTES, safe_path, sha256_file
from audit_unova_a06_references import parse_map
from qa.kalos.ka00_baseline import (
    ANDROID_247_BYTES, ANDROID_247_SHA256, ANDROID_247_TAG, file_report, static_controls,
)

ARCHIVE_ROOT = "Pokemon-Blue-Android/"
MAP = re.compile(r"Data/Map([0-9]{3,})\.rxdata$", re.I)
SIDES = {"north", "south", "east", "west", "n", "s", "e", "w"}

def protected(control: dict) -> set[int]:
    result = set()
    for value in control["protected"].values():
        if isinstance(value, list):
            result.update(value)
        else:
            start, end = value["start"], value["end"]
            if type(start) is not int or type(end) is not int or not 1 <= start <= end <= 999:
                raise ValueError("Invalid protected range")
            result.update(range(start, end + 1))
    if not set(range(442, 1000)) <= result:
        raise ValueError("A protected regional hold was removed")
    return result

def census(control: dict, snapshot: dict, static_refs: set[int], pbs_refs: set[int],
           dynamic: int, script_sections: int, parsable: int, pbs_lines: int) -> dict:
    occupied = set(snapshot["occupied_or_declared_ids"])
    published = protected(control)
    if snapshot["source_proof"]["archive_sha256"] != ANDROID_247_SHA256:
        raise ValueError("Wrong historical archive identity")
    if parsable != snapshot["file_count"]:
        raise ValueError("Missing physical files during reference audit")
    if not all(type(i) is int and i >= 1 for i in occupied | published | static_refs | pbs_refs):
        raise ValueError("Invalid physical, reserved, or referenced ID")
    union = occupied | published | static_refs | pbs_refs
    return {
        "phase": "KA02", "mode": "HISTORICAL_ONLY_DO_NOT_RESERVE",
        "source_release": ANDROID_247_TAG, "mapinfos_sha256": snapshot["mapinfos_sha256"],
        "observed_physical_count": snapshot["file_count"],
        "occupied_protected_or_statically_referenced_count_1_999": len(union & set(range(1,1000))),
        "reserved_region_count_1_999": len(published),
        "remaining_historical_unclaimed_count_1_999_not_vacancy_proof": len(set(range(1,1000)) - union),
        "unresolved_static_or_connection_destination_ids": sorted((static_refs | pbs_refs) - occupied),
        "transfer_201_dynamic_count_not_resolved": dynamic,
        "event_code_355_655_count_not_executed": script_sections,
        "pbs_connection_lines_seen": pbs_lines, "maps_inertly_parsed": parsable,
        "common_event_and_compiled_script_targets_verified": False,
        "current_sources_and_claims_verified": False,
        "four_digit_native_verified": False, "joiplay_native_verified": False,
        "may_allocate": False, "mapids_allocated": 0, "game_files_written": False,
    }

def connection_ids(data: bytes) -> tuple[set[int], int]:
    ids = set()
    lines = 0
    for line in data.decode("utf-8-sig").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [f.strip() for f in line.split(",")]
        if (len(parts) != 6 or parts[1].casefold() not in SIDES or parts[4].casefold() not in SIDES
                or any(not re.fullmatch(r"[+-]?\d{1,5}", parts[n]) for n in (0,2,3,5)) or
                min(int(parts[0]),int(parts[3])) < 1):
            raise ValueError("Unsupported PBS map connection row; manual review required")
        ids.update((int(parts[0]), int(parts[3])))
        lines += 1
    return ids, lines

def scan(path: Path) -> dict:
    path = safe_path(path, file=True)
    if path.stat().st_size != ANDROID_247_BYTES or sha256_file(path) != ANDROID_247_SHA256:
        raise ValueError("Android fixture is not the exact published artifact")
    snapshot = file_report(path, "android-247-historical")
    static_refs, pbs_refs, ids = set(), set(), set()
    dynamic = scripts = pbs_lines = 0
    with zipfile.ZipFile(path) as src:
        for entry in src.infolist():
            if not entry.filename.startswith(ARCHIVE_ROOT):
                continue
            rel = entry.filename.removeprefix(ARCHIVE_ROOT)
            if rel.casefold() == "pbs/map_connections.txt":
                if entry.file_size > MAX_FILE_BYTES:
                    raise ValueError("Oversized map connection file")
                pbs_refs, pbs_lines = connection_ids(src.read(entry))
            match = MAP.fullmatch(rel)
            if not match:
                continue
            mid = int(match[1])
            if mid in ids or not 0 < entry.file_size <= MAX_FILE_BYTES:
                raise ValueError("Invalid or duplicate MapNNN data")
            ids.add(mid)
            findings = parse_map(src.read(entry), mid)
            static_refs.update(findings["static_destinations"])
            dynamic += findings["dynamic_transfer_commands"]
            scripts += findings["script_commands_not_executed"]
    if not pbs_lines:
        raise ValueError("PBS map connections not observed")
    return census(static_controls(), snapshot, static_refs, pbs_refs, dynamic, scripts, len(ids), pbs_lines)

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(scan(args.archive), indent=2))

if __name__ == "__main__":
    main()
