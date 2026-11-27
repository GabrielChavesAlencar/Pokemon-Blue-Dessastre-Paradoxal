"""K03-E: pinned FRLG Route 11/Diglett source and isolated geometry gate.

No foreign event scripts, switches, music or maps are installed in the game.
The output is a CI-only migration candidate, not a playable release.
"""
from __future__ import annotations

import hashlib
import json
import re
from audit import ROOT, KANTO, inventory, json_file, load, stable_source_order, allocate_kanto_ids
from audit_cerulean_interiors import inspect_events, transfers
from server.ruby_marshal import text
from stage import stage

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run():
    source = ROOT / ".blue-work/frlg-source/Essentials FRLG"
    pilot = ROOT / ".blue-work/kanto-pilot"
    output = ROOT / ".blue-work/kanto-k03e-geometry"
    receipt = ROOT / ".blue-work/kanto-k03e-source.json"
    catalog = json_file(KANTO)
    baseline = set(map(int, catalog["maps"]))
    infos, files = inventory(source)
    names = {i: text(info.attrs["@name"]) for i, info in infos.items() if i in files}
    route = [i for i, name in names.items() if re.fullmatch(r"Route\s*0?11", name.strip(), re.I)]
    cave = [23, 81, 82]
    if len(route) != 1 or any(i not in names or "diglett" not in names[i].lower() for i in cave):
        raise ValueError(f"K03-E source identity mismatch: Route 11={route}, caves={[(i,names.get(i)) for i in cave]}")
    additions = dict(zip([route[0], *cave], ["ROUTE_11", "DIGLETT_ENTRANCE_ROUTE_2", "DIGLETT_ENTRANCE_ROUTE_11", "DIGLETT_TUNNEL"]))
    if len(baseline) != 156 or baseline.intersection(additions) or set(catalog["preview_only"]).intersection(additions):
        raise ValueError("K03-E requires intact 156-map baseline and four absent source maps")
    candidate = {**catalog, "maps": {**catalog["maps"], **{str(i): key for i,key in additions.items()}}}
    wanted = baseline | set(additions)
    if stable_source_order(wanted)[:156] != stable_source_order(baseline):
        raise ValueError("K03-E allocation would move existing slots")
    active = {int(k): v for k,v in json_file(pilot / "Kanto pilot.json")["maps"].items()}
    bi,bf = inventory(ROOT / "game")
    if active != allocate_kanto_ids(baseline, bi.keys() | bf.keys()):
        raise ValueError("K03-E pilot does not match published baseline mapping")
    expected = allocate_kanto_ids(wanted, bi.keys() | bf.keys())
    if any(expected[k] != v for k,v in active.items()):
        raise ValueError("K03-E candidate moved clean install slots")
    _, before = inventory(pilot)
    baseline_hashes = {mid: sha(before[mid]) for mid in active.values()}
    registry = {name: sha(pilot/"Data"/name) for name in ("MapInfos.rxdata","Tilesets.rxdata")}
    evidence = inspect_events(source, [18,64,*additions])
    warps = [{"source": int(sid), "event": e["id"], "event_xy": e["xy"], **t}
             for sid, m in evidence.items() for e in m["events"] for t in transfers(e)]
    connections = []
    focus = {18,64,*additions}
    for line in (source/"PBS/map_connections.txt").read_text("utf-8-sig").splitlines():
        row = line.split("#",1)[0].strip().split(",")
        if len(row)==6 and row[0].strip().isdigit() and row[3].strip().isdigit():
            if int(row[0]) in focus or int(row[3]) in focus:
                connections.append([v.strip() for v in row])
    from pbs import read_blocks
    encounters = (source/"PBS/encounters.txt").read_text("utf-8-sig")
    sections = re.split(r"(?m)(?=^\[\d+(?:,\d+)?\])", encounters)
    encounter_blocks = [s.strip() for s in sections if (m:=re.match(r"\[(\d+)(?:,\d+)?\]",s)) and int(m[1]) in additions]
    report = {"status":"SOURCE_REVIEW_REQUIRED","manual_gameplay":False,
              "source_events":evidence,"source_connections":connections,"source_transfers":warps,
              "source_encounter_blocks":encounter_blocks,
              "candidate_ids":{str(i):expected[i] for i in additions},"baseline_count":156}
    receipt.write_text(json.dumps(report,ensure_ascii=True,indent=2),encoding="utf-8")
    for sid in additions:
        for e in evidence[str(sid)]["events"]:
            print("KANTO_K03E_SOURCE_EVENT:"+json.dumps({"source":sid,**e},ensure_ascii=True),flush=True)
    print("KANTO_K03E_SOURCE_REPORT:"+json.dumps({k:v for k,v in report.items() if k!="source_events"},ensure_ascii=True),flush=True)
    plan = stage(ROOT, source, pilot, output, existing=active, manifest=candidate)
    mapping = {row["source_id"]:row["proposed_id"] for row in plan["maps"]}
    if mapping != expected or len(mapping)!=160 or len(set(mapping.values()))!=160:
        raise ValueError("K03-E staged allocation mismatch")
    geometry = []
    for sid in additions:
        old = load(files[sid]).attrs
        new = load(output/"Data"/f"Map{mapping[sid]:03d}.rxdata").attrs
        if old["@data"] != new["@data"] or (old["@width"],old["@height"]) != (new["@width"],new["@height"]) or new["@events"]:
            raise ValueError(f"K03-E geometry or unsafe foreign event mismatch: {sid}")
        geometry.append({"source":sid,"destination":mapping[sid],"dimensions":[new["@width"],new["@height"]],
                         "tiles_sha256":hashlib.sha256(new["@data"].data).hexdigest()})
    if any(sha(before[mid]) != digest for mid,digest in baseline_hashes.items()) or any(sha(pilot/"Data"/name)!=digest for name,digest in registry.items()):
        raise ValueError("K03-E changed installed pilot files")
    report.update({"status":"GEOMETRY_CANDIDATE_ONLY","geometry":geometry,"baseline_preserved":156,"candidate_count":160})
    receipt.write_text(json.dumps(report,ensure_ascii=True,indent=2),encoding="utf-8")
    print("KANTO_K03E_156_TO_160_GEOMETRY_CANDIDATE_OK",flush=True)

if __name__ == "__main__":
    run()
