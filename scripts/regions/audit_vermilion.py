"""Read-only reconnaissance for Kanto phase 08 (Vermilion / S.S. Anne).

The pinned FRLG source is inspected in CI, not redistributed. All map IDs,
transfer points, trainer calls, and HM/ticket conditions are evidence to review
before adding gameplay. This tool never executes foreign Ruby scripts.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from audit import ROOT, inventory, load
from server.ruby_marshal import text

TARGET = re.compile(
    r"(?i)(route\s*0?[56]\b|vermilion|s\.?s\.?\s*anne|ship|harbor|"
    r"port|underground|diglett|surge|cerulean|bike shop)"
)
IMPORTANT = re.compile(
    r"(?i)(TrainerBattle|Surge|Ticket|Captain|Cut|Guard|Ship|Sailor|"
    r"Vermilion|Pok[eé]monMart|PokemonMart|pbPokemonCenter|pbHeal|"
    r"badge|switch|door|warp|gym)"
)


def describe(source: Path) -> dict:
    infos, maps = inventory(source)
    identified = [
        (map_id, text(info.attrs["@name"]))
        for map_id, info in sorted(infos.items())
        if map_id in maps and TARGET.search(text(info.attrs["@name"]))
    ]
    result = []
    for map_id, name in identified:
        map_data = load(maps[map_id]).attrs
        events = []
        for event_id, event in sorted(map_data["@events"].items()):
            event_name = text(event.attrs["@name"])
            warps = []
            scripts = []
            conditions = []
            for page_idx, page in enumerate(event.attrs["@pages"], 1):
                cond = page.attrs["@condition"].attrs
                active = {k: str(v)[:90] for k, v in cond.items()
                          if k.endswith("_valid") and v}
                if active:
                    conditions.append({"page": page_idx, "active": active})
                for command in page.attrs["@list"]:
                    row = command.attrs
                    code, args = row["@code"], row["@parameters"]
                    if code == 201 and args and args[0] == 0:
                        warps.append([int(args[1]), int(args[2]), int(args[3])])
                    elif code in (355, 655, 111) and args:
                        for value in args:
                            if isinstance(value, (bytes, str)):
                                decoded = text(value)
                                if IMPORTANT.search(decoded):
                                    scripts.append({"page": page_idx, "code": code,
                                                    "script": decoded[:350]})
            if warps or scripts or IMPORTANT.search(event_name):
                events.append({"id": event_id, "name": event_name[:90],
                               "x": event.attrs["@x"], "y": event.attrs["@y"],
                               "warps": warps[:6], "scripts": scripts[:10],
                               "conditions": conditions[:3]})
        result.append({"id": map_id, "name": name,
                       "size": [map_data["@width"], map_data["@height"]],
                       "events": events[:100], "event_count": len(events)})
    pbs = (source / "PBS/map_connections.txt").read_text("utf-8-sig")
    selected = {n for n, _ in identified}
    links = []
    for line in pbs.splitlines():
        row = line.split("#", 1)[0].strip()
        if not row:
            continue
        parts = row.split(",")
        if len(parts) == 6 and parts[0].strip().isdigit() and parts[3].strip().isdigit():
            if int(parts[0]) in selected or int(parts[3]) in selected:
                links.append(row)
    return {"phase": "08", "matched": len(identified),
            "maps": result, "connections": links}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=ROOT / ".blue-work/frlg-source/Essentials FRLG")
    arguments = parser.parse_args()
    print(json.dumps(describe(arguments.source), ensure_ascii=False, indent=2))
