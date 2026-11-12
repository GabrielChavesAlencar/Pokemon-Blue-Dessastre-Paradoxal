"""Read-only phase 12 FRLG audit: Cinnabar Island, Mansion, Seafoam and access routes.

This tool examines the pinned source in an isolated build; it NEVER executes
its Ruby scripts, copies story events, or modifies native Decades maps/saves.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from audit import ROOT, inventory, load
from server.ruby_marshal import text

NAMES = re.compile(r"(?i)(cinnabar|seafoam|pokemon mansion|pok[eé]mon mansion|"
                   r"mansion|blaine|route\s*(?:19|20|21)\b|fossil lab|research lab)")
SCRIPTS = re.compile(r"(?i)(trainer|battle|leader|blaine|switch|door|key|secret|"
                     r"fossil|quiz|teleport|surf|strength)")
CALL = re.compile(r"(?i)(TrainerBattle\.start|pbTrainerBattle|pbMessage|pbSetSelfSwitch|"
                  r"pbReceiveItem|pbItemBall|pbPokemonMart)")


def clean(value):
    if isinstance(value, bytes):
        value = text(value)
    return str(value).replace("\r", " ").replace("\n", " ")[:190]


def audit(source: Path):
    infos, files = inventory(source)
    maps, selected = [], set()
    for map_id, info in sorted(infos.items()):
        if map_id not in files:
            continue
        name = clean(info.attrs["@name"])
        if not NAMES.search(name):
            continue
        selected.add(map_id)
        raw = load(files[map_id]).attrs
        events = []
        for event_id, event in sorted(raw["@events"].items()):
            warps, scripts = [], []
            page_meta = []
            for page in event.attrs["@pages"]:
                p = page.attrs
                page_meta.append({"trigger": p["@trigger"], "graphic": clean(p["@graphic"].attrs["@character_name"])})
                for op in p["@list"]:
                    row = op.attrs
                    params = row["@parameters"]
                    if row["@code"] == 201 and len(params) >= 6 and params[0] == 0:
                        warps.append([int(x) for x in params[1:6]])
                    if row["@code"] in (355, 655) and params and (CALL.search(clean(params[0])) or SCRIPTS.search(clean(params[0]))):
                        scripts.append(clean(params[0]))
            events.append({"id": event_id, "name": clean(event.attrs["@name"]),
                           "x": event.attrs["@x"], "y": event.attrs["@y"],
                           "warps": sorted(set(tuple(w) for w in warps)),
                           "pages": page_meta, "scripts": scripts[:5]})
        maps.append({"id": map_id, "name": name, "width": raw["@width"],
                     "height": raw["@height"], "events": events})
    edges = []
    for raw in (source / "PBS/map_connections.txt").read_text(encoding="utf-8-sig").splitlines():
        line = raw.split("#", 1)[0].strip()
        fields = line.split(",")
        if len(fields) == 6 and fields[0].strip().isdigit() and fields[3].strip().isdigit():
            if int(fields[0]) in selected or int(fields[3]) in selected:
                edges.append(line)
    trainers = []
    for line in (source / "PBS/trainers.txt").read_text(encoding="utf-8-sig").splitlines():
        key = line.strip()
        if key.startswith("[") and key.endswith("]") and re.search(r"(?i)(blaine|burglar|supernerd|swimmer|scientist)", key):
            trainers.append(key[1:-1])
    return {"phase": 12, "source_only": True, "foreign_events_executed": False,
            "maps": maps, "connections": edges, "trainer_headers": trainers}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / ".blue-work/frlg-source/Essentials FRLG")
    parser.add_argument("--output", type=Path, default=ROOT / ".blue-work/kanto-phase-12-audit.json")
    args = parser.parse_args()
    report = audit(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"CINNABAR_AUDIT_MAPS:{len(report['maps'])}")
    for m in report["maps"]:
        print(f"CINNABAR_MAP:{m['id']}|{m['name']}|{m['width']}x{m['height']}|events={len(m['events'])}")
        for ev in m["events"]:
            if ev["warps"] or ev["scripts"] or SCRIPTS.search(ev["name"]):
                print(f"CINNABAR_EVENT:{m['id']}|{ev['id']}|{ev['name']}|"
                      f"xy={ev['x']},{ev['y']}|warps={ev['warps'][:2]}|"
                      f"script={ev['scripts'][:2]}|trigger={ev['pages'][0]['trigger'] if ev['pages'] else '?'}")
    for e in report["connections"]:
        print("CINNABAR_CONNECTION:" + e)
    print("CINNABAR_TRAINER_HEADERS:" + ",".join(report["trainer_headers"][:60]))


if __name__ == "__main__":
    main()
