"""Read-only structural verification of the separately installed Kanto pilot.

Run after pilot.py creates .blue-work/kanto-pilot, before the native smoke test.
This checks data integrity; it does not prove walkability, battle UI or PC/Android compatibility.
"""
from __future__ import annotations

import argparse
import json
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
    expected = {int(source): name for source, name in json_file(KANTO)["maps"].items()}
    if set(mapping) != set(expected) or len(set(mapping.values())) != len(expected):
        raise ValueError("Pilot map manifest is missing locations or contains duplicate destination IDs")
    ids = set(mapping.values())
    maps = {}
    for source, dest in mapping.items():
        file = game / "Data" / f"Map{dest:03d}.rxdata"
        if not file.is_file():
            raise ValueError(f"Missing {expected[source]} map: {file.name}")
        maps[dest] = load(file)
    system = load(game / "Data/System.rxdata").attrs
    if system["@start_map_id"] != mapping[5]:
        raise ValueError("New game does not start at Kanto's Pallet Town")
    if not (0 <= system["@start_x"] < maps[mapping[5]].attrs["@width"] and
            0 <= system["@start_y"] < maps[mapping[5]].attrs["@height"]):
        raise ValueError("New-game start position is outside Pallet Town")

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

    if found != set(anchors):
        missing = sorted(set(anchors) - found)
        raise ValueError(f"Required Kanto event scripts are missing: {missing}")

    seen = reachable(edges, mapping[5])
    if seen != ids:
        missing = [expected[source] for source, dest in mapping.items() if dest not in seen]
        raise ValueError(f"Maps unreachable FROM Pallet by real transfer direction: {missing}")
    backwards = {map_id: set() for map_id in ids}
    for origin, destinations in edges.items():
        for destination in destinations:
            backwards[destination].add(origin)
    returnable = reachable(backwards, mapping[5])
    if returnable != ids:
        trapped = [expected[source] for source, dest in mapping.items() if dest not in returnable]
        raise ValueError(f"Maps without a directed route BACK to Pallet: {trapped}")
    route = [5, 9, 10, 18, 19, 24, 20, 25, 28, 32, 33, 34,
             36, 37, 38, 39, 40, 41, 42]
    for source in route:
        if mapping[source] not in seen:
            raise ValueError(f"Story route is not connected to Pallet: {expected[source]}")
    # The test-only teleport manifest must refer exclusively to prepared maps
    # and coordinates proven in the pinned FRLG source's incoming warps.
    stops_file = game / "Data/blue-kanto-experimental-stops.txt"
    if not stops_file.is_file():
        raise ValueError("Experimental Kanto destinations were not generated")
    required_stops = {"PALLET", "PEWTER", "ROUTE4", "MOON_CENTER",
                      "MOON_1F", "MOON_B1F", "MOON_B2F", "CERULEAN", "MISTY"}
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
        "connections": count_connections,
        "mapped_transfers": warps,
        "returnable_maps": len(returnable),
        "required_events": len(found),
        "experimental_stops": len(seen_stops),
        "route": [expected[source] for source in route],
        "limitations": "Topology and data only; physical walkability, player controls, real battles and saves still need testing.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot", type=Path, nargs="?", default=ROOT / ".blue-work/kanto-pilot")
    args = parser.parse_args()
    print(json.dumps(inspect(args.pilot), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
