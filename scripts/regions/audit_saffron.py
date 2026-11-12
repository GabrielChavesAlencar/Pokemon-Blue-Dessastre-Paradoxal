"""Read-only inventory for phase 11 — Saffron City, Sabrina and Silph Co.

Inspect a SHA-pinned Essentials FRLG source in CI; never run foreign script
commands or copy NPCs, switches, trainers, items or event tables to Decades.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from audit import ROOT, inventory, load
from server.ruby_marshal import text

TARGET = re.compile(
    r"(?i)(saffron|silph|fighting dojo|dojo|route\s*0?[78]\b|"
    r"underground|copycat|mr\.?\s*psychic)"
)


def audit(source: Path) -> dict:
    infos, paths = inventory(source)
    selected = {}
    maps = []
    for source_id, info in sorted(infos.items()):
        if source_id not in paths:
            continue
        name = text(info.attrs["@name"])
        if not TARGET.search(name):
            continue
        selected[source_id] = name
        raw = load(paths[source_id]).attrs
        warps = []
        for event_id, event in sorted(raw["@events"].items()):
            for page in event.attrs["@pages"]:
                for cmd in page.attrs["@list"]:
                    row = cmd.attrs
                    params = row["@parameters"]
                    if row["@code"] == 201 and len(params) >= 4 and params[0] == 0:
                        warps.append({"event_id": event_id, "destination": int(params[1]),
                                      "x": int(params[2]), "y": int(params[3])})
        maps.append({"id": source_id, "name": name,
                     "width": raw["@width"], "height": raw["@height"],
                     "source_event_count": len(raw["@events"]), "warps": warps})
    connections = []
    for raw in (source / "PBS/map_connections.txt").read_text(encoding="utf-8-sig").splitlines():
        line = raw.split("#", 1)[0].strip()
        cols = line.split(",")
        if len(cols) == 6 and cols[0].strip().isdigit() and cols[3].strip().isdigit():
            if int(cols[0]) in selected or int(cols[3]) in selected:
                connections.append(line)
    return {"phase": 11, "source_only": True, "events_imported": False,
            "maps": maps, "connections": connections}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=ROOT / ".blue-work/frlg-source/Essentials FRLG")
    parser.add_argument("--output", type=Path,
                        default=ROOT / ".blue-work/kanto-phase-11-audit.json")
    args = parser.parse_args()
    report = audit(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print("KANTO_PHASE_11_COUNT:" + str(len(report["maps"])))
    for row in report["maps"]:
        print(f"KANTO_PHASE_11_MAP:{row['id']}|{row['name']}|{row['width']}x{row['height']}|events={row['source_event_count']}")
        for warp in row["warps"][:8]:
            print(f"KANTO_PHASE_11_WARP:{row['id']}|{warp['event_id']}|{warp['destination']}|{warp['x']}|{warp['y']}")
    for edge in report["connections"]:
        print("KANTO_PHASE_11_CONNECTION:" + edge)


if __name__ == "__main__":
    main()
