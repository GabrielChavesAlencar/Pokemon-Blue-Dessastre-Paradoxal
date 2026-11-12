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
from pilot import PILOT_META


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

    # A topology audit is undirected: manual gameplay still needs to verify
    # that warps, doors and route transitions actually work both ways.
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
        (28, 6): 'BlueKantoPilot.battle(:BLUE_KANTO_CAMPER, "Liam")',
        (28, 7): 'BlueKantoPilot.battle(:BLUE_KANTO_LEADER, "Brock")',
        (24, 16): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Rick")',
        (24, 17): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Doug")',
        (24, 18): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Anthony")',
        (24, 19): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Charlie")',
        (24, 20): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Sammy")',
    }
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
                        edges[target].add(dest)
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
        raise ValueError(f"Maps unreachable in the combined transfer/connection graph: {missing}")
    route = [5, 9, 10, 18, 19, 24, 20, 25, 28]
    for source in route:
        if mapping[source] not in seen:
            raise ValueError(f"Story route is not connected to Pallet: {expected[source]}")
    return {
        "result": "structural_check_passed",
        "maps": len(maps),
        "connections": count_connections,
        "mapped_transfers": warps,
        "required_events": len(found),
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
