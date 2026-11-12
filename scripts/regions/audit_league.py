"""Source-only audit of Kanto Route 22/23, Victory Road and Indigo Plateau.

Never executes the FRLG event scripts or writes to the installed game.
Use the pinned FRLG source archive verified by the CI workflow.
"""
from __future__ import annotations
import argparse
import json
import re
from pathlib import Path
from audit import ROOT, inventory, load
from server.ruby_marshal import text

PATTERN = re.compile(
    r"(?i)(route\s*2[23]\b|victory\s*road|indigo|elite\s*four|"
    r"lorelei|bruno|agatha|lance|hall\s*of\s*fame|champion|"
    r"poke.?mon\s*league|pok[eé]mon\s*league|badge\s*check)"
)
CALL = re.compile(
    r"(?i)(pbTrainerBattle|TrainerBattle|pbMessage|pbReceiveItem|"
    r"pbLeague|pbHall|pbStart|pbSetSelfSwitch|pbShow|"
    r"pbAddPokemon|Game\.|Badge|Elite|League|Champion|"
    r"pbChange|pbTeleport|pbFade)"
)

def string(value, limit=240):
    if isinstance(value, bytes):
        value = text(value)
    return str(value).replace("\n", " ").replace("\r", " ")[:limit]

def event_audit(event):
    ev = event.attrs
    pages = []
    for index, page in enumerate(ev["@pages"]):
        p = page.attrs
        warps, scripts, conditionals = [], [], []
        for row in p["@list"]:
            cmd = row.attrs
            code = cmd["@code"]
            params = cmd["@parameters"]
            if code == 201 and len(params) >= 6 and params[0] == 0:
                warps.append([int(v) for v in params[1:6]])
            elif code in (355, 655) and params:
                scripts.append(string(params[0], 450))
            elif code in (111, 121, 122, 123, 125, 126) and params:
                conditionals.append([code, [string(v) for v in params[:6]]])
        pages.append({
            "index": index, "trigger": p["@trigger"], "through": p["@through"],
            "graphic": string(p["@graphic"].attrs["@character_name"]),
            "tile_id": p["@graphic"].attrs["@tile_id"],
            "warps": warps, "scripts": scripts[:25],
            "conditions": {k: string(v) for k, v in p["@condition"].attrs.items()
                           if k.endswith("_valid") or k.endswith("_id") or k.endswith("_ch")},
            "control": conditionals[:20],
        })
    return {"id": int(ev["@id"]), "name": string(ev["@name"]),
            "x": int(ev["@x"]), "y": int(ev["@y"]), "pages": pages}

def audit(source):
    infos, files = inventory(source)
    maps = []
    for source_id, info in sorted(infos.items()):
        name = string(info.attrs["@name"])
        if source_id not in files or not PATTERN.search(name):
            continue
        m = load(files[source_id]).attrs
        maps.append({"id": source_id, "name": name,
                     "width": m["@width"], "height": m["@height"],
                     "events": [event_audit(ev) for _, ev in sorted(m["@events"].items())]})
    selected = {m["id"] for m in maps}
    edges = []
    for raw in (source/"PBS/map_connections.txt").read_text(encoding="utf-8-sig").splitlines():
        line = raw.split("#",1)[0].strip()
        fields = [x.strip() for x in line.split(",")]
        if len(fields)==6 and fields[0].isdigit() and fields[3].isdigit():
            if int(fields[0]) in selected or int(fields[3]) in selected:
                edges.append(line)
    trainers = []
    for raw in (source/"PBS/trainers.txt").read_text(encoding="utf-8-sig").splitlines():
        header = raw.strip()
        if header.startswith("[") and header.endswith("]"):
            if re.search(r"(?i)(lorelei|bruno|agatha|lance|champion|rival|blue)", header):
                trainers.append(header[1:-1])
    metadata = []
    for raw in (source/"PBS/map_metadata.txt").read_text(encoding="utf-8-sig").splitlines():
        if any(raw.startswith(f"[{i}]") for i in selected):
            metadata.append(raw.strip())
    return {"phase": 14, "source_only": True, "foreign_scripts_executed": False,
            "maps": maps, "connections": edges, "trainer_headers": trainers,
            "map_metadata_sections": metadata}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path,
                        default=ROOT/".blue-work/frlg-source/Essentials FRLG")
    parser.add_argument("--output", type=Path,
                        default=ROOT/".blue-work/kanto-phase-14-audit.json")
    args=parser.parse_args()
    report=audit(args.source)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("LEAGUE_AUDIT_MAPS:"+str(len(report["maps"])))
    for m in report["maps"]:
        print(f'LEAGUE_MAP:{m["id"]}|{m["name"]}|{m["width"]}x{m["height"]}|events={len(m["events"])}')
        for ev in m["events"]:
            transfers=[p["warps"] for p in ev["pages"] if p["warps"]]
            scripts=[s for p in ev["pages"] for s in p["scripts"] if CALL.search(s)]
            if transfers or scripts or re.search(r"(?i)(guard|badge|elite|champ|lorelei|bruno|agatha|lance|oak|nurse|blue|rock|boulder|door|stairs|warp|rival|league)",ev["name"]):
                print("LEAGUE_EVENT:"+json.dumps({
                    "map":m["id"],"id":ev["id"],"name":ev["name"],
                    "xy":[ev["x"],ev["y"]],"warps":transfers[:3],
                    "scripts":scripts[:3],"triggers":[p["trigger"] for p in ev["pages"]]},
                    ensure_ascii=True))
    print("LEAGUE_CONNECTIONS:"+json.dumps(report["connections"],ensure_ascii=True))
    print("LEAGUE_TRAINERS:"+json.dumps(report["trainer_headers"],ensure_ascii=True))

if __name__ == "__main__":
    main()
