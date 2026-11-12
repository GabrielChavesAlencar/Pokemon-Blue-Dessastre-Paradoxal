"""Audit missing interior destinations in the manually visited Kanto corridor.

Read only the pinned FRLG map data. Never follow or execute Ruby event scripts.
"""
from __future__ import annotations
import json
from audit import KANTO, ROOT, inventory, json_file, load
from server.ruby_marshal import text

EARLY = (5, 6, 7, 9, 10, 11, 12, 18, 19, 20, 24, 25, 26, 27, 28)


def transfer_rows(events):
    for event_id, event in events.items():
        names = text(event.attrs["@name"])
        for page_index, page in enumerate(event.attrs["@pages"], 1):
            for op in page.attrs["@list"]:
                p = op.attrs["@parameters"]
                if op.attrs["@code"] == 201 and len(p) >= 6 and p[0] == 0:
                    yield {"event_id": event_id, "name": names, "page": page_index,
                           "dest": int(p[1]), "x": int(p[2]), "y": int(p[3])}


def audit():
    root = ROOT / ".blue-work/frlg-source/Essentials FRLG"
    infos, maps = inventory(root)
    included = set(map(int, json_file(KANTO)["maps"]))
    outgoing = {}
    for source in EARLY:
        found = list(transfer_rows(load(maps[source]).attrs["@events"]))
        outgoing[source] = [dict(row, target_name=text(infos[row["dest"]].attrs["@name"])
                                 if row["dest"] in infos else "MISSING SOURCE")
                            for row in found if row["dest"] not in included]
    candidates = sorted({r["dest"] for rows in outgoing.values() for r in rows
                         if r["dest"] in maps})
    for dest in candidates:
        return_links = list(transfer_rows(load(maps[dest]).attrs["@events"]))
        reciprocal = [row for row in return_links if row["dest"] in EARLY]
        print("KANTO_EARLY_INTERIOR:" + json.dumps({
            "id": dest, "name": text(infos[dest].attrs["@name"]),
            "size": [load(maps[dest]).attrs["@width"], load(maps[dest]).attrs["@height"]],
            "from": [{"source": src, **v} for src, rows in outgoing.items()
                     for v in rows if v["dest"] == dest],
            "reciprocal": reciprocal[:25],
            "total_event_count": len(load(maps[dest]).attrs["@events"]),
        }, ensure_ascii=False))
    print("KANTO_EARLY_INTERIOR_COUNT:" + str(len(candidates)))


if __name__ == "__main__":
    audit()
