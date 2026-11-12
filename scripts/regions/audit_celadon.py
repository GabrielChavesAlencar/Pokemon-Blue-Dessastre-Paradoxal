"""Kanto phase 09: read-only Celadon and approach map inventory.

Do not execute source scripts or import NPC/battle/story events. The pinned FRLG
archive is prepared and verified by the existing workflow before this audit.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from audit import ROOT, inventory, load
from server.ruby_marshal import text

TARGET = re.compile(
    r"(?i)(celadon|route\s*0?[789]\b|saffron|lavender|underground|"
    r"cycling|rocket|game\s*corner)"
)


def audit(source: Path) -> dict:
    infos, paths = inventory(source)
    selected = {
        map_id: text(info.attrs["@name"])
        for map_id, info in sorted(infos.items())
        if map_id in paths and TARGET.search(text(info.attrs["@name"]))
    }
    maps = []
    for map_id, name in selected.items():
        raw = load(paths[map_id]).attrs
        transfers = []
        event_names = []
        for event_id, event in sorted(raw["@events"].items()):
            event_name = text(event.attrs["@name"])
            event_names.append({"id": event_id, "name": event_name})
            for page in event.attrs["@pages"]:
                for opcode in page.attrs["@list"]:
                    row = opcode.attrs
                    if row["@code"] == 201 and len(row["@parameters"]) >= 4:
                        mode, destination, x, y = row["@parameters"][:4]
                        if mode == 0:
                            transfers.append({
                                "event": event_id, "name": event_name,
                                "to": int(destination), "x": int(x), "y": int(y)
                            })
        maps.append({
            "id": map_id, "name": name,
            "size": [raw["@width"], raw["@height"]],
            "events": len(event_names),
            "event_names": event_names if re.search("(?i)celadon.*(gym|city)|route 7|route 8", name) else [],
            "transfers": transfers,
        })
    connections = []
    for raw in (source / "PBS/map_connections.txt").read_text(encoding="utf-8-sig").splitlines():
        line = raw.split("#", 1)[0].strip()
        values = line.split(",")
        if len(values) == 6 and values[0].strip().isdigit() and values[3].strip().isdigit():
            if int(values[0]) in selected or int(values[3]) in selected:
                connections.append(line)
    return {"phase": 9, "selected_maps": len(maps), "maps": maps,
            "connections": connections, "source_only": True,
            "events_imported": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / ".blue-work/frlg-source/Essentials FRLG")
    parser.add_argument("--output", type=Path, default=ROOT / ".blue-work/kanto-phase-09-audit.json")
    args = parser.parse_args()
    report = audit(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"KANTO_PHASE_09_MAP_COUNT:{report['selected_maps']}")
    for row in report["maps"]:
        print(f"KANTO_PHASE_09_MAP:{row['id']}|{row['name']}|{row['size']}|warps={len(row['transfers'])}")
        for warp in row["transfers"][:24]:
            print(f"KANTO_PHASE_09_WARP:{row['id']}|{warp['event']}|{warp['to']}|{warp['x']}|{warp['y']}|{warp['name'][:40]}")
    for line in report["connections"]:
        print("KANTO_PHASE_09_CONNECTION:" + line)


if __name__ == "__main__":
    main()
