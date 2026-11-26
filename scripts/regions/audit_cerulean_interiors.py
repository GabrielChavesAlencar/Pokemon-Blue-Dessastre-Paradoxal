"""K02-C isolated terrain migration and source-event receipts.

The published 145-map pilot is read-only. No donor script, foreign switch,
save, or preview map is installed into the player's game.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from audit import ROOT, KANTO, inventory, json_file, load, stable_source_order, allocate_kanto_ids
from stage import stage
from server.ruby_marshal import text

ADDITIONS = {
    "43": "CERULEAN_BIKE_SHOP", "44": "CERULEAN_HOUSE_A",
    "45": "CERULEAN_HOUSE_B", "46": "CERULEAN_HOUSE_C",
    "47": "CERULEAN_HOUSE_D", "48": "CERULEAN_RANSACKED_HOUSE",
}
CITY_DOORS = {3: 44, 7: 43, 8: 46, 9: 48, 10: 44, 11: 45, 12: 47, 27: 48}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scalar(value):
    if isinstance(value, bytes):
        return text(value)
    if isinstance(value, (int, float, str, bool)) or value is None:
        return value
    if isinstance(value, (tuple, list)):
        return [scalar(v) for v in value]
    if isinstance(value, dict):
        return {str(k): scalar(v) for k, v in value.items()}
    return {"type": getattr(value, "name", type(value).__name__)}


def inspect_events(source, ids):
    infos, files = inventory(source)
    report = {}
    for mid in ids:
        m = load(files[mid]).attrs
        events = []
        for eid, event in sorted(m["@events"].items()):
            ev = event.attrs
            pages = []
            for index, page in enumerate(ev["@pages"], 1):
                p = page.attrs
                commands = []
                for op in p["@list"]:
                    cmd = op.attrs
                    code = cmd["@code"]
                    # Review only: no code from the donor is executed or copied
                    # to the staged native event table.
                    params = cmd["@parameters"]
                    commands.append({"code": code, "indent": cmd.get("@indent", 0),
                                     "parameters": scalar(params)})
                pages.append({"page": index, "condition": scalar(p["@condition"].attrs),
                              "graphic": scalar(p["@graphic"].attrs),
                              "trigger": p["@trigger"], "through": p["@through"],
                              "commands": commands})
            events.append({"id": eid, "name": text(ev["@name"]),
                           "xy": [ev["@x"], ev["@y"]], "pages": pages})
        report[str(mid)] = {"name": text(infos[mid].attrs["@name"]),
                            "dimensions": [m["@width"], m["@height"]],
                            "source_sha256": sha(files[mid]), "events": events}
    return report


def transfers(event):
    for page in event["pages"]:
        for cmd in page["commands"]:
            p = cmd["parameters"]
            if cmd["code"] == 201 and len(p) >= 6 and p[0] == 0:
                yield {"page": page["page"], "destination": p[1],
                       "xy": p[2:4], "direction": p[4]}


def run():
    source = ROOT / ".blue-work/frlg-source/Essentials FRLG"
    pilot = ROOT / ".blue-work/kanto-pilot"
    output = ROOT / ".blue-work/kanto-k02c-geometry"
    receipt = ROOT / ".blue-work/kanto-k02c-source.json"
    catalog = json_file(KANTO)
    wanted = set(map(int, catalog["maps"]))
    prior = wanted - set(map(int, ADDITIONS))
    if len(prior) != 145 or len(wanted) != 151 or any(catalog["maps"].get(k) != v for k,v in ADDITIONS.items()):
        raise ValueError("K02-C requires exact 151-map catalogue")
    expanded = catalog
    if stable_source_order(wanted)[:145] != stable_source_order(prior):
        raise ValueError("K02-C changed published allocation order")
    active = {int(k): v for k, v in json_file(pilot / "Kanto pilot.json")["maps"].items()}
    base_infos, base_files = inventory(ROOT / "game")
    existing = allocate_kanto_ids(prior, base_infos.keys() | base_files.keys())
    if set(active) != wanted or len(set(active.values())) != 151 or any(active[k] != v for k,v in existing.items()):
        raise ValueError("K02-C invalid expanded pilot or changed baseline IDs")
    _, before_files = inventory(pilot)
    before_hashes = {mid: sha(before_files[mid]) for mid in existing.values()}
    registry_before = {name: sha(pilot / "Data" / name)
                       for name in ("MapInfos.rxdata", "Tilesets.rxdata")}
    evidence = inspect_events(source, [39, *map(int, ADDITIONS)])
    city = {event["id"]: event for event in evidence["39"]["events"]}
    for eid, dest in CITY_DOORS.items():
        if not any(t["destination"] == dest for t in transfers(city[eid])):
            raise ValueError(f"K02-C missing original city door {eid} -> {dest}")
    returns = {}
    for sid in ADDITIONS:
        rows = [{"event_id": e["id"], "event_xy": e["xy"], **t}
                for e in evidence[sid]["events"] for t in transfers(e)
                if t["destination"] == 39]
        if not rows:
            raise ValueError(f"K02-C missing original return for {sid}")
        returns[sid] = rows
    report = {"status": "SOURCE_REVIEW_REQUIRED", "manual_gameplay": False,
              "source_events": evidence, "city_doors": CITY_DOORS, "returns": returns}
    # Write evidence before staging, so an asset failure cannot hide the
    # original event pages necessary to implement the local adapters.
    receipt.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf8")
    for sid in ("39", *ADDITIONS):
        for event in evidence[sid]["events"]:
            print("KANTO_K02C_SOURCE_EVENT:" + json.dumps({"source": sid, **event}, ensure_ascii=True), flush=True)
    plan = stage(ROOT, source, pilot, output, existing=active, manifest=expanded)
    mapping = {row["source_id"]: row["proposed_id"] for row in plan["maps"]}
    if mapping != active or any(mapping[k] != v for k, v in existing.items()):
        raise ValueError("K02-C migration changed existing map IDs")
    source_infos, source_files = inventory(source)
    geometry = []
    for sid in map(int, ADDITIONS):
        dst = mapping[sid]
        old = load(source_files[sid]).attrs
        new = load(output / "Data" / f"Map{dst:03d}.rxdata").attrs
        if (old["@data"] != new["@data"] or
                (old["@width"], old["@height"]) != (new["@width"], new["@height"]) or
                new["@events"] or not load(before_files[dst]).attrs["@events"]):
            raise ValueError(f"K02-C geometry changed or foreign events imported: {sid}")
        geometry.append({"source": sid, "destination": dst,
                         "dimensions": [new["@width"], new["@height"]],
                         "tiles_sha256": hashlib.sha256(new["@data"].data).hexdigest()})
    if any(sha(before_files[mid]) != digest for mid, digest in before_hashes.items()):
        raise ValueError("K02-C baseline map bytes modified")
    if any(sha(pilot / "Data" / name) != digest for name, digest in registry_before.items()):
        raise ValueError("K02-C baseline registry modified")
    report.update(status="GEOMETRY_FIXTURE_READY", maps=151, preserved=145,
                  geometry=geometry, published=False, gameplay_installed=False)
    receipt.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf8")
    print("KANTO_K02C_GEOMETRY_REPORT:" + json.dumps({k:v for k,v in report.items()
          if k != "source_events"}, ensure_ascii=True), flush=True)
    print("KANTO_K02C_151_GEOMETRY_FIXTURE_145_BASELINE_PRESERVED_OK", flush=True)


if __name__ == "__main__":
    run()
