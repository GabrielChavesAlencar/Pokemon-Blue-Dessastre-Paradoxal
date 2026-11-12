"""Read-only audit of FRLG trainer sight/trigger metadata.

Only source event names and RPG Maker page metadata are exposed. No script
commands, dialogue, trainer battles or data from unselected events are copied.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from audit import ROOT, inventory, load
from pilot import TRAINERS
from server.ruby_marshal import text

SIGHT = re.compile(r"(?i)(?:trainer|sight)\(\d+\)")


def inspect_source(source: Path) -> dict:
    _, paths = inventory(source)
    rows = []
    for source_id, trainers in sorted(TRAINERS.items()):
        raw = load(paths[source_id]).attrs["@events"]
        for event_id, values in sorted(trainers.items()):
            event = raw[event_id]
            name = text(event.attrs["@name"])
            first = event.attrs["@pages"][0].attrs
            match = SIGHT.search(name)
            rows.append({
                "source_id": source_id,
                "event_id": event_id,
                "name": name,
                "sight": int(match.group(1)) if match else None,
                "trigger": first["@trigger"],
                "move_type": first["@move_type"],
                "walk_anime": first["@walk_anime"],
                "direction_fix": first["@direction_fix"],
                "through": first["@through"],
                "page_count": len(event.attrs["@pages"]),
            })
    return {"trainer_count": len(rows), "trainers": rows}


if __name__ == "__main__":
    data = inspect_source(ROOT / ".blue-work/frlg-source/Essentials FRLG")
    print("KANTO_TRAINER_AUDIT_COUNT:" + str(data["trainer_count"]))
    for row in data["trainers"]:
        print("KANTO_TRAINER_AUDIT:" + json.dumps(row, ensure_ascii=False))
