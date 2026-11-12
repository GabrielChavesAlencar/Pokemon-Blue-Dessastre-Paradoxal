"""Read-only structural verification of the separately installed Kanto pilot.

Run after pilot.py creates .blue-work/kanto-pilot, before the native smoke test.
This checks data integrity; it does not prove walkability, battle UI or PC/Android compatibility.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import deque
from pathlib import Path

from audit import KANTO, ROOT, json_file, load
from pilot import PILOT_META, TRAINERS


def reachable(edges: dict[int, set[int]], start: int) -> set[int]:
    seen = {start}
    pending = deque([start])
    while pending:
        for neighbor in edges[pending.popleft()]:
            if neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    return seen


def inspect(game: Path) -> dict:
    game = game.resolve()
    workspace = (ROOT / ".blue-work").resolve()
    if not game.is_relative_to(workspace):
        raise ValueError("Verification only accepts a copy within .blue-work")
    meta_path = game / PILOT_META
    if not meta_path.is_file():
        raise ValueError("Not a prepared Kanto pilot")
    mapping = {int(source): int(dest) for source, dest in json_file(meta_path)["maps"].items()}
    manifest = json_file(KANTO)
    expected = {int(source): name for source, name in manifest["maps"].items()}
    preview_only = set(manifest.get("preview_only", []))
    if preview_only - expected.keys():
        raise ValueError("Preview map IDs do not exist in the Kanto manifest")
    if preview_only & set(TRAINERS):
        raise ValueError("No trainer scripts can be installed on preview-only maps")
    if set(mapping) != set(expected) or len(set(mapping.values())) != len(expected):
        raise ValueError("Pilot map manifest is missing locations or contains duplicate destination IDs")
    ids = set(mapping.values())
    maps = {}
    for source, dest in mapping.items():
        file = game / "Data" / f"Map{dest:03d}.rxdata"
        if not file.is_file():
            raise ValueError(f"Missing {expected[source]} map: {file.name}")
        maps[dest] = load(file)
    # Celadon phase 09 is map-terrain only. Not even source self-switches,
    # NPCs, warps or trainer events may slip into these compiled RPG maps.
    for source in preview_only:
        if maps[mapping[source]].attrs["@events"]:
            raise ValueError(f"Phase 09-11 preview must not import events into {expected[source]}")
    system = load(game / "Data/System.rxdata").attrs
    if system["@start_map_id"] != mapping[5]:
        raise ValueError("New game does not start at Kanto's Pallet Town")
    if not (0 <= system["@start_x"] < maps[mapping[5]].attrs["@width"] and
            0 <= system["@start_y"] < maps[mapping[5]].attrs["@height"]):
        raise ValueError("New-game start position is outside Pallet Town")

    # MAN-01: only audited pairs of original exterior/interior door events.
    # Both directions must be present after remapping to Blue map IDs; an
    # accessible house with no exit is a softlock, not a successful import.
    safe_interior_pairs = (
        (5, 2, 8, 1),          # Pallet rival house
        (10, 2, 14, 4),        # Viridian houses
        (10, 3, 15, 3),
        (18, 8, 21, 4),        # Route 2 gatehouse
        (18, 2, 22, 4),        # Route 2 hidden house
        (25, 1, 29, 1),        # Pewter Museum
        (25, 3, 30, 1),        # Pewter homes
        (25, 7, 31, 1),
    )

    def event_transfers(source_id: int, event_id: int) -> set[int]:
        source_events = maps[mapping[source_id]].attrs["@events"]
        if event_id not in source_events:
            raise ValueError(f"Missing interior door event {source_id}/{event_id}")
        results = set()
        for page in source_events[event_id].attrs["@pages"]:
            for opcode in page.attrs["@list"]:
                code = opcode.attrs
                args = code["@parameters"]
                if code["@code"] == 201 and len(args) >= 4 and args[0] == 0:
                    results.add(args[1])
        return results

    for outer, entry, inside, exit_id in safe_interior_pairs:
        if mapping[inside] not in event_transfers(outer, entry):
            raise ValueError(f"Interior {inside}: missing entry from {outer}/{entry}")
        if mapping[outer] not in event_transfers(inside, exit_id):
            raise ValueError(f"Interior {inside}: missing return to {outer}/{entry}")
    if 13 in mapping or 23 in mapping:
        raise ValueError("Viridian Gym or Diglett Cave unlocked before story audit")

    # MAN-02: the source-proven 50 line-of-sight trainers require Event Touch,
    # with a non-triggering second page selected by self-switch A after victory.
    sight_count = 0
    for original, profiles in TRAINERS.items():
        for event_id, spec in profiles.items():
            event = maps[mapping[original]].attrs["@events"][event_id]
            pages = event.attrs["@pages"]
            if len(pages) != 2:
                raise ValueError(f"Trainer {original}/{event_id} missing win-state page")
            sight = bool(re.search(r"(?i)(?:trainer|sight)\\(\\d+\\)",
                                   event.attrs["@name"].decode("utf-8", errors="replace")))
            expected_trigger = 2 if sight else 0
            if pages[0].attrs["@trigger"] != expected_trigger:
                raise ValueError(f"Trainer {original}/{event_id} has wrong sight trigger")
            post = pages[1].attrs
            condition = post["@condition"].attrs
            if (post["@trigger"] != 0 or
                condition["@self_switch_valid"] is not True or
                condition["@self_switch_ch"] != b"A"):
                raise ValueError(f"Trainer {original}/{event_id} has unsafe repeat behavior")
            commands = [
                opcode.attrs["@parameters"][0]
                for opcode in pages[0].attrs["@list"]
                if opcode.attrs["@code"] in (355, 655) and opcode.attrs["@parameters"]
            ]
            script = "\\n".join(value.decode("utf-8") if isinstance(value, bytes)
                                  else str(value) for value in commands)
            key = f"KANTO_{original:03d}_{event_id:03d}"
            if ("BlueKantoPilot.battle(" not in script or
                f'BlueKantoPilot.sync_trainer_event("{key}"' not in script):
                raise ValueError(f"Trainer {original}/{event_id} does not persist victory")
            if sight:
                sight_count += 1
                if "pbNoticePlayer(get_self)" not in script:
                    raise ValueError(f"Trainer {original}/{event_id} will not alert the player")
    if sight_count != 50:
        raise ValueError(f"Source-proven trainer sight count changed: {sight_count}")

    # Route connections are bidirectional, but transfer events are directed.
    # Check reachability both from and back to Pallet to avoid accepting
    # one-way maps as if their exit events were reciprocal.
    edges = {map_id: set() for map_id in ids}
    connections = game / "PBS/map_connections_kanto.txt"
    if not connections.is_file():
        raise ValueError("The regional map connections PBS is missing")
    count_connections = 0
    for raw in connections.read_text(encoding="utf-8-sig").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        fields = [item.strip() for item in line.split(",")]
        if len(fields) != 6:
            raise ValueError(f"Invalid map connection: {line}")
        left, right = int(fields[0]), int(fields[3])
        if left not in ids or right not in ids:
            raise ValueError(f"Map connection refers outside the prepared pilot: {line}")
        edges[left].add(right)
        edges[right].add(left)
        count_connections += 1

    anchors = {
        (6, 15): "BlueKantoPilot.choose_starter",
        (6, 14): "BlueKantoPilot.rival",
        (11, 2): "BlueKantoPilot.heal",
        (26, 2): "BlueKantoPilot.heal",
        (34, 2): "BlueKantoPilot.heal",
        (40, 2): "BlueKantoPilot.heal",
        (65, 2): "BlueKantoPilot.heal",
        (64, 7): "BlueKantoPilot.ticketmaster",
        (76, 2): "BlueKantoPilot.captain",
        (36, 18): 'BlueKantoPilot.pickup(:MOONSTONE, "KANTO_036_018")',
        (28, 6): 'BlueKantoPilot.battle(:BLUE_KANTO_CAMPER, "Liam", "KANTO_028_006")',
        (28, 7): 'BlueKantoPilot.battle(:BLUE_KANTO_LEADER, "Brock", "KANTO_028_007")',
        (24, 16): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Rick", "KANTO_024_016")',
        (24, 17): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Doug", "KANTO_024_017")',
        (24, 18): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Anthony", "KANTO_024_018")',
        (24, 19): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Charlie", "KANTO_024_019")',
        (24, 20): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Sammy", "KANTO_024_020")',
    }
    for source_id, entries in TRAINERS.items():
        for event_id, spec in entries.items():
            kind, name = spec[:2]
            key = f"KANTO_{source_id:03d}_{event_id:03d}"
            anchors[(source_id, event_id)] = (
                f'BlueKantoPilot.battle(:BLUE_KANTO_{kind}, "{name}", "{key}"'
            )
    for entry in (9, 29, 30):
        anchors[(64, entry)] = "BlueKantoPilot.harbor_gate"
    for entry in (4, 10, *range(22, 35)):
        anchors[(67, entry)] = "BlueKantoPilot.surge_can"
    for entry in (8, *range(11, 20)):
        anchors[(67, entry)] = "BlueKantoPilot.surge_gate"
    found = set()
    warps = 0
    for source, dest in mapping.items():
        data = maps[dest].attrs
        for event_id, event in data["@events"].items():
            for page in event.attrs["@pages"]:
                for op in page.attrs["@list"]:
                    code = op.attrs["@code"]
                    params = op.attrs["@parameters"]
                    if code == 201 and params[0] == 0:
                        target, x, y = params[1:4]
                        if target not in ids:
                            raise ValueError(f"Unmapped transfer: {source}/{event_id} -> {target}")
                        target_map = maps[target].attrs
                        if not (0 <= x < target_map["@width"] and 0 <= y < target_map["@height"]):
                            raise ValueError(f"Out-of-bounds transfer: {source}/{event_id} -> {target} ({x},{y})")
                        edges[dest].add(target)
                        warps += 1
                    if code in (355, 655) and params:
                        script = params[0].decode("utf-8") if isinstance(params[0], bytes) else str(params[0])
                        expected_script = anchors.get((source, event_id))
                        if expected_script and expected_script in script:
                            found.add((source, event_id))
                        # The harbor entrance is a ticket-gated scripted
                        # transfer, not an RPG::EventCommand 201. Admit it into
                        # the topology only if the whitelisted destination
                        # agrees with the pinned FRLG harbor exit.
                        if source == 64 and event_id in (9, 29, 30):
                            allowed = f"BlueKantoPilot.harbor_gate({mapping[72]}, 9, 7)"
                            if script == allowed:
                                edges[dest].add(mapping[72])

    if found != set(anchors):
        missing = sorted(set(anchors) - found)
        raise ValueError(f"Required Kanto event scripts are missing: {missing}")

    seen = reachable(edges, mapping[5])
    active_ids = {dest for source, dest in mapping.items() if source not in preview_only}
    if not active_ids.issubset(seen):
        missing = [expected[source] for source, dest in mapping.items()
                   if source not in preview_only and dest not in seen]
        raise ValueError(f"Maps unreachable FROM Pallet by real transfer direction: {missing}")
    backwards = {map_id: set() for map_id in ids}
    for origin, destinations in edges.items():
        for destination in destinations:
            backwards[destination].add(origin)
    returnable = reachable(backwards, mapping[5])
    if not active_ids.issubset(returnable):
        trapped = [expected[source] for source, dest in mapping.items()
                   if source not in preview_only and dest not in returnable]
        raise ValueError(f"Maps without a directed route BACK to Pallet: {trapped}")
    route = [5, 9, 10, 18, 19, 24, 20, 25, 28, 32, 33, 34,
             36, 37, 38, 39, 40, 41, 42,
             56, 59, 60, 63, 61, 64, 65, 66, 67,
             72, 74, 75, 76, 77, 78]
    for source in route:
        if mapping[source] not in seen:
            raise ValueError(f"Story route is not connected to Pallet: {expected[source]}")
    # The test-only teleport manifest must refer exclusively to prepared maps
    # and coordinates proven in the pinned FRLG source's incoming warps.
    stops_file = game / "Data/blue-kanto-experimental-stops.txt"
    if not stops_file.is_file():
        raise ValueError("Experimental Kanto destinations were not generated")
    required_stops = {"PALLET", "PEWTER", "ROUTE4", "MOON_CENTER",
                      "MOON_1F", "MOON_B1F", "MOON_B2F", "CERULEAN", "MISTY",
                      "ROUTE5", "ROUTE6", "VERMILION", "SURGE", "HARBOR",
                      "SSANNE", "SSCAPTAIN", "SSDECK",
                      "ROUTE7", "CELADON", "ERIKA", "CEL_CENTER", "CEL_STORE",
                      "FUCHSIA", "KOGA", "FUCH_CENTER", "FUCH_WARDEN",
                      "SAF_GATE", "SAF_SOUTH", "SAF_NORTH", "SAF_WEST", "ROUTE15",
                      "ROUTE8", "SAFF_WEST", "SAFFRON", "SABRINA", "SAFF_DOJO",
                      "SAFF_CENTER", "SILPH_1F", "SILPH_5F", "SILPH_11F", "SILPH_LIFT"}
    seen_stops = set()
    for raw in stops_file.read_text(encoding="utf-8").splitlines():
        parts = raw.split("|")
        if len(parts) != 6:
            raise ValueError(f"Malformed experimental destination: {raw}")
        code, label, map_no, x, y, direction = parts
        if code in seen_stops or code not in required_stops or not label:
            raise ValueError(f"Invalid test destination: {code}")
        seen_stops.add(code)
        dest_map, tx, ty, direction = map(int, (map_no, x, y, direction))
        if dest_map not in maps or not 0 <= tx < maps[dest_map].attrs["@width"] or not 0 <= ty < maps[dest_map].attrs["@height"] or direction not in (2,4,6,8):
            raise ValueError(f"Experimental destination outside prepared map: {code}")
    if seen_stops != required_stops:
        raise ValueError(f"Missing experimental stops: {required_stops - seen_stops}")

    return {
        "result": "structural_check_passed",
        "maps": len(maps),
        "preview_geometry_only": len(preview_only),
        "phase09_geometry_only": len(preview_only & {111,114,115,117,118,119,120,121,122,123,124}),
        "phase10_geometry_only": len(preview_only & {141,142,143,144,145,146,147,152,153,155,156,157,158,159,160,161,162,163,164,165}),
        "phase11_geometry_only": len(preview_only & {57,62,107,108,109,110,112,113,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189}),
        "preview_event_count": sum(len(maps[mapping[source]].attrs["@events"])
                                   for source in preview_only),
        "active_maps": len(active_ids),
        "audited_interiors_bidirectional": len(safe_interior_pairs),
        "trainers_with_line_of_sight": sight_count,
        "connections": count_connections,
        "mapped_transfers": warps,
        "returnable_maps": len(returnable),
        "required_events": len(found),
        "experimental_stops": len(seen_stops),
        "route": [expected[source] for source in route],
        "limitations": "Phase 09-11 maps are scenery previews WITHOUT events, encounters, trainers, Erika/Rainbow, Koga/Soul, Sabrina/Marsh, Safari or Silph gameplay. All controls, collisions and prior gameplay still require manual testing.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot", type=Path, nargs="?", default=ROOT / ".blue-work/kanto-pilot")
    args = parser.parse_args()
    print(json.dumps(inspect(args.pilot), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
