#!/usr/bin/env python3
"""MapID census for an exact historical fixture, not an allocator or current-world proof."""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
import zlib
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts/regions")]
from audit_unova_a04_mapids import MAX_FILE_BYTES, safe_path, sha256_file
from audit_unova_a06_references import parse_map
from server.ruby_marshal import RubyObject, loads, text
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

TRANSFER = re.compile(
    r"(?:\b(?:pbTransferPlayer|pbWarpToMap|pbSetPlayerPosition|reserve_transfer|setPlayerLocation)\s*\(\s*"
    r"|(?:\$game_temp\.)?player_new_map_id\s*=(?!=)\s*)([^,\r\n)]*)", re.I
)
MAX_DECODED_SCRIPT = 1024**2

def script_targets(script: str) -> tuple[set[int], int]:
    """Conservative heuristic: do not run Ruby and never claim all targets."""
    if not isinstance(script, str) or len(script) > MAX_DECODED_SCRIPT:
        raise ValueError("Invalid or oversized script section")
    ids, computed = set(), 0
    for match in TRANSFER.finditer(script):
        if re.search(r"\bdef\s*$", script[max(0,match.start()-32):match.start()]):
            continue
        arg = match[1].strip()
        if re.fullmatch(r"[1-9][0-9]{0,4}", arg):
            ids.add(int(arg))
        else:
            computed += 1
    return ids, computed

def remember_script(value: str, counters: Counter, ids: set[int]) -> None:
    literal, unknown = script_targets(value)
    ids.update(literal)
    counters["script_sections_examined"] += 1
    counters["script_transfer_unresolved"] += unknown

def command_list(commands, counters: Counter, ids: set[int], common: bool = False):
    if not isinstance(commands, list) or len(commands) > 50000:
        raise ValueError("Unexpected RPG command list")
    parts = []
    def flush():
        if parts:
            remember_script("\n".join(parts), counters, ids)
            parts.clear()
    for obj in commands:
        if not isinstance(obj, RubyObject):
            raise ValueError("Unexpected RPG command")
        code = obj.attrs.get("@code")
        params = obj.attrs.get("@parameters")
        if code != 655:
            flush()
        if code in (355,655) and isinstance(params, list) and params:
            parts.append(text(params[0]))
        if common and code == 201:
            if (isinstance(params, list) and len(params) > 1
                    and type(params[0]) is int and params[0] == 0
                    and type(params[1]) is int and 0 < params[1] <= 99999):
                ids.add(params[1])
                counters["common_event_direct"] += 1
            else:
                counters["common_event_dynamic"] += 1
    flush()

def inspect_map_scripts(content: bytes, counters: Counter, ids: set[int]) -> None:
    root = loads(content)
    for obj in root.attrs["@events"].values():
        for page in obj.attrs["@pages"]:
            command_list(page.attrs["@list"],counters,ids)

def inspect_common_events(content: bytes, counters: Counter, ids: set[int]) -> None:
    events = loads(content)
    if isinstance(events, dict):
        events = list(events.values())
    if not isinstance(events, list) or len(events) > 10000:
        raise ValueError("Unexpected CommonEvents root")
    for event in events:
        if event is None:
            continue
        if not isinstance(event, RubyObject) or event.name != "RPG::CommonEvent":
            raise ValueError("Unexpected CommonEvents entry")
        counters["common_events_examined"] += 1
        command_list(event.attrs["@list"],counters,ids,common=True)

def inspect_compiled_script_index(content: bytes, counters: Counter, ids: set[int]) -> None:
    chunks = loads(content)
    if not isinstance(chunks, list) or len(chunks) > 5000:
        raise ValueError("Unexpected compiled Script root")
    decoded_size = 0
    for row in chunks:
        if not isinstance(row,list) or len(row) < 3 or not isinstance(row[2],bytes):
            counters["unsupported_script_entries"] += 1
            continue
        decoder = zlib.decompressobj()
        block = decoder.decompress(row[2], MAX_DECODED_SCRIPT + 1)
        decoded_size += len(block)
        if not decoder.eof or decoder.unused_data or len(block) > MAX_DECODED_SCRIPT or decoded_size > 64 * MAX_DECODED_SCRIPT:
            raise ValueError("Unsafe compiled script size or encoding")
        counters["compiled_script_entries_examined"] += 1
        remember_script(block.decode("utf-8","replace"), counters, ids)

def scan(path: Path) -> dict:
    path = safe_path(path, file=True)
    if path.stat().st_size != ANDROID_247_BYTES or sha256_file(path) != ANDROID_247_SHA256:
        raise ValueError("Android fixture is not the exact published artifact")
    snapshot = file_report(path, "android-247-historical")
    static_refs, pbs_refs, ids = set(), set(), set()
    dynamic = scripts = pbs_lines = 0
    script_ids, script_counters, observed = set(), Counter(), set()
    with zipfile.ZipFile(path) as src:
        for entry in src.infolist():
            if not entry.filename.startswith(ARCHIVE_ROOT):
                continue
            rel = entry.filename.removeprefix(ARCHIVE_ROOT)
            if rel.casefold() == "pbs/map_connections.txt":
                if entry.file_size > MAX_FILE_BYTES:
                    raise ValueError("Oversized map connection file")
                pbs_refs, pbs_lines = connection_ids(src.read(entry))
            block_type = rel.casefold()
            if block_type in {"data/commonevents.rxdata", "data/scripts.rxdata", "data/pluginscripts.rxdata"}:
                if entry.file_size > MAX_FILE_BYTES:
                    raise ValueError("Oversized script metadata")
                observed.add(block_type)
                if block_type == "data/commonevents.rxdata":
                    inspect_common_events(src.read(entry), script_counters, script_ids)
                elif block_type == "data/scripts.rxdata":
                    inspect_compiled_script_index(src.read(entry), script_counters, script_ids)
            match = MAP.fullmatch(rel)
            if not match:
                continue
            mid = int(match[1])
            if mid in ids or not 0 < entry.file_size <= MAX_FILE_BYTES:
                raise ValueError("Invalid or duplicate MapNNN data")
            ids.add(mid)
            raw = src.read(entry)
            findings = parse_map(raw, mid)
            inspect_map_scripts(raw, script_counters, script_ids)
            static_refs.update(findings["static_destinations"])
            dynamic += findings["dynamic_transfer_commands"]
            scripts += findings["script_commands_not_executed"]
    if not pbs_lines:
        raise ValueError("PBS map connections not observed")
    return {
        **census(static_controls(), snapshot, static_refs | script_ids, pbs_refs, dynamic, scripts, len(ids), pbs_lines),
        "historical_script_scopes_observed": sorted(observed),
        "historical_script_heuristics": dict(script_counters),
        "plugins_rxdata_contents_examined": False,
        "dynamic_destinations_resolved": False,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(scan(args.archive), indent=2))

if __name__ == "__main__":
    main()
