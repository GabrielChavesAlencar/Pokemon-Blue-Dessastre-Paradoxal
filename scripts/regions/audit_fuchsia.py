"""Read-only reconnaissance for Kanto phase 10 — Fuchsia, Safari and approaches.

Always read the pinned Essentials FRLG data in a disposable workspace.
This never executes scripts, copies trainer events, or modifies the game.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path

from audit import ROOT, inventory, load
from server.ruby_marshal import text

TARGET = re.compile(
    r"(?i)(fuchsia|safari|route\s*0?(?:1[2-9])\b|cycling|warden|"
    r"snorlax|gatehouse|saffron|celadon|lavender)"
)

def describe(source: Path):
    infos, paths = inventory(source)
    found = []
    selected = set()
    for source_id, info in sorted(infos.items()):
        if source_id not in paths:
            continue
        name = text(info.attrs["@name"])
        if not TARGET.search(name):
            continue
        selected.add(source_id)
        m = load(paths[source_id]).attrs
        warps = []
        for event_id, event in sorted(m["@events"].items()):
            for page in event.attrs["@pages"]:
                for op in page.attrs["@list"]:
                    row = op.attrs
                    p = row["@parameters"]
                    if row["@code"] == 201 and len(p) >= 4 and p[0] == 0:
                        warps.append([event_id, int(p[1]), int(p[2]), int(p[3])])
        found.append({"id": source_id, "name": name,
                      "size": [m["@width"], m["@height"]],
                      "events": len(m["@events"]), "warps": warps})
    connections = []
    for raw in (source/"PBS/map_connections.txt").read_text(encoding="utf-8-sig").splitlines():
        values = raw.split("#", 1)[0].strip().split(",")
        if len(values) == 6 and values[0].strip().isdigit() and values[3].strip().isdigit():
            if int(values[0]) in selected or int(values[3]) in selected:
                connections.append(raw.split("#", 1)[0].strip())
    return {"phase": 10, "source_only": True, "events_imported": False,
            "maps": found, "connections": connections}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=ROOT/".blue-work/frlg-source/Essentials FRLG")
    parser.add_argument("--output", type=Path, default=ROOT/".blue-work/kanto-phase-10-audit.json")
    args = parser.parse_args()
    report = describe(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print("KANTO_PHASE_10_MAP_COUNT:" + str(len(report["maps"])))
    for m in report["maps"]:
        print(f"KANTO_PHASE_10_MAP:{m['id']}|{m['name']}|{m['size']}|events={m['events']}")
        for event_id, dest, x, y in m["warps"][:12]:
            print(f"KANTO_PHASE_10_WARP:{m['id']}|{event_id}|{dest}|{x}|{y}")
    for link in report["connections"]:
        print("KANTO_PHASE_10_CONNECTION:" + link)

if __name__ == "__main__":
    main()
