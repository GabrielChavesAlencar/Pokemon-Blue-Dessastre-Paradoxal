"""Audit the next contiguous Kanto segment from the already pinned FRLG source.

Read-only: print map IDs, names, adjacent gates, NPC names and event operations
so that stage 07 never assumes an original map ID or executes unknown scripts.
"""
from __future__ import annotations
import argparse, json, re
from pathlib import Path
from audit import ROOT, inventory, load
from server.ruby_marshal import text

TARGET = re.compile(r"(?i)(route\s*0?[345]\b|mt\.?\s*moon|mount\s*moon|cerulean|pewter|moon\s*cave)")
NPC = re.compile(r"(?i)(misty|rocket|hiker|lass|youngster|bug|trainer|rival|gym|moon|center|poke.?mart)")


def audit(source: Path) -> dict:
    infos, maps = inventory(source)
    matches = []
    for source_id, info in sorted(infos.items()):
        name = text(info.attrs["@name"])
        if not TARGET.search(name) or source_id not in maps:
            continue
        map_data = load(maps[source_id]).attrs
        events = []
        for event_id, event in sorted(map_data["@events"].items()):
            name_event = text(event.attrs["@name"])
            pages = event.attrs["@pages"]
            operations = []
            for page in pages:
                for raw in page.attrs["@list"]:
                    row = raw.attrs
                    code, params = row["@code"], row["@parameters"]
                    if code == 201 and params and params[0] == 0:
                        operations.append({"warp": [int(n) for n in params[1:4]]})
                    elif code in (355, 655, 111) and params:
                        script = text(params[-1]) if isinstance(params[-1], (bytes, str)) else ""
                        if script and NPC.search(script):
                            operations.append({"script": script[:180]})
                    elif code in (121, 122):
                        operations.append({"flag": code})
            if operations or NPC.search(name_event):
                events.append({"id": event_id, "name": name_event[:65], "x": event.attrs["@x"],
                               "y": event.attrs["@y"], "ops": operations[:5]})
        matches.append({"id": source_id, "name": name, "width": map_data["@width"],
                        "height": map_data["@height"], "events": events[:50]})
    return {"candidates": matches, "count": len(matches)}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / ".blue-work/frlg-source/Essentials FRLG")
    args = parser.parse_args()
    print(json.dumps(audit(args.source), ensure_ascii=False, indent=2))
