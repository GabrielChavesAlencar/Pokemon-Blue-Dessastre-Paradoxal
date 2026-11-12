"""Read-only source audit for phase 13 — Viridian Gym, Giovanni and puzzle.

No original event commands may be executed and no source switches are reused.
Produces a structured CI artifact with event/warp/script identities.
"""
import argparse
import json
import re
from pathlib import Path
from audit import ROOT, load
from server.ruby_marshal import text

CITY = 10
GYM = 13

def printable(value):
    if isinstance(value, bytes):
        return text(value)
    return str(value)

def event_rows(source, map_id):
    data = load(source / "Data" / f"Map{map_id:03}.rxdata").attrs
    rows = []
    for event_id, ev in sorted(data["@events"].items()):
        pages = []
        for page in ev.attrs["@pages"]:
            p = page.attrs
            ops = []
            for cmd in p["@list"]:
                op = cmd.attrs
                params = op["@parameters"]
                if op["@code"] == 201 and len(params) >= 6 and params[0] == 0:
                    ops.append({"code":201, "map":params[1],"x":params[2],"y":params[3]})
                elif op["@code"] in (355,655,111,121,122,123,117):
                    ops.append({"code":op["@code"],"args":[printable(v)[:200] for v in params[:5]]})
            condition = p["@condition"].attrs
            pages.append({"trigger":p["@trigger"],"through":p["@through"],
                          "graphic":printable(p["@graphic"].attrs["@character_name"]),
                          "tile_id":p["@graphic"].attrs["@tile_id"],
                          "condition":{k:printable(v) for k,v in condition.items()
                                       if k.endswith("_valid") or k.endswith("_id") or k.endswith("_ch")},
                          "commands":ops[:50]})
        rows.append({"id":event_id,"name":printable(ev.attrs["@name"]),
                     "x":ev.attrs["@x"],"y":ev.attrs["@y"],"pages":pages})
    return {"id":map_id,"width":data["@width"],"height":data["@height"],"events":rows}

def audit(source):
    trainers = []
    for line in (source / "PBS/trainers.txt").read_text(encoding="utf-8-sig").splitlines():
        if line.startswith("[") and line.endswith("]") and (
            "Giovanni" in line or re.search(r"(COOLTRAINER|BLACKBELT|TAMER|KARATE|LEADER)",line,re.I)):
            trainers.append(line.strip("[]"))
    return {"phase":13,"source_only":True,"commands_executed":False,
            "city":event_rows(source,CITY),"gym":event_rows(source,GYM),
            "trainer_candidates":trainers}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=ROOT/".blue-work/frlg-source/Essentials FRLG")
    p.add_argument("--output",type=Path,default=ROOT/".blue-work/kanto-phase-13-audit.json")
    a=p.parse_args()
    report=audit(a.source)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    for section in ("city","gym"):
        m=report[section]
        print("VIRIDIAN_SOURCE_MAP:"+json.dumps({"section":section,"id":m["id"],"size":[m["width"],m["height"]],"event_count":len(m["events"])},ensure_ascii=False))
        for ev in m["events"]:
            compact={"id":ev["id"],"name":ev["name"],"xy":[ev["x"],ev["y"]],
                     "page_count":len(ev["pages"]),
                     "trigger":[p["trigger"] for p in ev["pages"]],
                     "graphic":[p["graphic"] or f"tile:{p['tile_id']}" for p in ev["pages"]],
                     "commands":[cmd for p in ev["pages"] for cmd in p["commands"]
                                 if cmd["code"] in (201,355,655,111,121,122,123)]}
            print("VIRIDIAN_SOURCE_EVENT:"+section+":"+json.dumps(compact,ensure_ascii=True))
    print("VIRIDIAN_TRAINER_CANDIDATES:"+json.dumps(report["trainer_candidates"],ensure_ascii=True))

if __name__=="__main__":
    main()
