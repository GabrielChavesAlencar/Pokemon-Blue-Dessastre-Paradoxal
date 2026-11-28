"""Stage the six Lavender city/service maps in a disposable CI copy only."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from audit import KANTO, ROOT, inventory, json_file, load, text
from audit_cerulean_interiors import inspect_events
from audit_k05_lavender import assemble, K05, propose_slots
from k04_corridor import LAVENDER_BOUNDARY, published_destinations
from k04_gameplay import sprite
from k05_lavender_services import add_services, install_runtime, verify_name_rater
from pbs import catalogue
from pilot import EVENT_CLASSES, PILOT_META, command, new_event, write_map
from qa_k04_migration import copy_for_ci
from stage import stage

CITY_MAPS = {93: "LAVENDER_TOWN", 94:"LAVENDER_CENTER", 95:"LAVENDER_MART",
             96:"LAVENDER_HOUSE", 97:"LAVENDER_NAME_RATER", 98:"LAVENDER_FUJI_HOUSE"}
CITY_SLOTS = {sid: mid for sid,mid in zip(CITY_MAPS,range(609,615))}
CITY_NAMES = ("Lavender Town", "Lavender Pokémon Center", "Lavender Poké Mart",
              "Lavender House", "Name Rater's House", "Mr. Fuji's House")
# source event -> (source anchor, destination source, landing, native direction)
CITY_DOORS = {
    (93,6):((6,5),94,(7,8),8), (93,7):((20,15),95,(4,7),8),
    (93,14):((10,11),98,(4,7),8), (93,15):((5,16),96,(4,7),8),
    (93,16):((10,16),97,(4,7),8),
    (94,1):((7,9),93,(6,6),0), (95,1):((4,8),93,(20,16),0),
    (96,5):((4,8),93,(5,17),0), (97,5):((4,8),93,(10,17),0),
    (98,1):((4,8),93,(10,12),0),
}
SAVE_APP = "Kanto K05 City CI"
MART_ARRAY = re.compile(r"\bpbPokemonMart\s*\(\s*\[\s*((?::[A-Z][A-Z_0-9]*\s*,\s*)*:[A-Z][A-Z_0-9]*\s*,?)\s*\]", re.S)


def script_lines(page):
    return [text(op.attrs["@parameters"][0]) for op in page.attrs["@list"]
            if op.attrs["@code"] in (355,655) and op.attrs["@parameters"]]


def mart_stock(lines, items):
    body = "\n".join(lines)
    entries = MART_ARRAY.findall(body)
    if len(entries) != 1 or body.count("pbPokemonMart") != 1:
        raise ValueError("K05 Lavender shop input is not one auditable literal catalog")
    stock = re.findall(r":([A-Z][A-Z_0-9]*)",entries[0])
    if not stock or len(stock) != len(set(stock)) or not set(stock) <= items:
        raise ValueError("K05 original shop stock conflicts with the native item catalog")
    return stock


def verify_source(report):
    ranked = {r["id"]:(r["name"],r["slot_unreserved"]) for r in report["maps"] if r["id"] in CITY_MAPS}
    if ranked != {sid:(name,CITY_SLOTS[sid]) for sid,name in zip(CITY_MAPS,CITY_NAMES)}:
        raise ValueError("K05 city identity or collision-free destination changed")
    rows = [r for r in report["transfers"] if r["source"] in CITY_MAPS and r["destination"] in CITY_MAPS]
    if (len(rows) != len(CITY_DOORS) or
        {(r["source"],r["event"]):(tuple(r["at"]),r["destination"],tuple(r["xy"]),r["direction"])
        for r in rows} != CITY_DOORS):
        raise ValueError("K05 original city door anchor or return destination changed")
    if LAVENDER_BOUNDARY not in {tuple(link["source_row"]) for link in report["links"]}:
        raise ValueError("K05 Route 10 to Lavender seam is not source-proven")


def add_city_events(source,target,donor,native,sid,mapping):
    events = native.attrs["@events"]
    originals = donor.attrs["@events"]
    if events:
        raise ValueError("K05 terrain copied donor events")
    for (area, eid), (at,dst,landing,face) in CITY_DOORS.items():
        if sid != area:
            continue
        event = originals[eid]
        if tuple(event.attrs[k] for k in ("@x","@y")) != at:
            raise ValueError("K05 source door moved before map staging")
        ops = [command(201,0,mapping[dst],*landing,face,0)]
        events[eid] = new_event(event,ops,1,b"")
    if sid == 94:
        nurse = originals[2]
        page = nurse.attrs["@pages"][0]
        if (tuple(nurse.attrs[k] for k in ("@x","@y")) != (7,2)
                or page.attrs["@trigger"] != 0
                or not any(op.attrs["@code"] == 314 for op in page.attrs["@list"])):
            raise ValueError("K05 Lavender nurse no longer proves native healing")
        events[2] = new_event(nurse,[command(355,b"BlueKantoPilot.heal")],0,sprite(source,target,nurse))
    if sid == 95:
        clerk = originals[2]
        page = clerk.attrs["@pages"][0]
        if tuple(clerk.attrs[k] for k in ("@x","@y")) != (2,3) or page.attrs["@trigger"] != 0:
            raise ValueError("K05 Lavender clerk moved")
        stock = mart_stock(script_lines(page),catalogue(target,"items"))
        script = "pbPokemonMart([" + ", ".join(":"+k for k in stock) + "])"
        events[2] = new_event(clerk,[command(355,script.encode("ascii"))],0,sprite(source,target,clerk))
        return stock
    return []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def isolate(target,meta,profile=SAVE_APP,fixture="k05_city_fixture_only"):
    for name in ("Game.ini","mkxp.json"):
        config = target/name
        value=config.read_text(encoding="utf-8-sig")
        if value.count(meta["save_app"]) != 1:
            raise ValueError("K05 cannot isolate test save namespace")
        config.write_text(value.replace(meta["save_app"],profile),encoding="utf8")
    meta.update(save_app=profile)
    meta[fixture] = True
    (target/PILOT_META).write_text(json.dumps(meta),encoding="utf8")


def extend_terrain(source,baseline,tmp,catalog,labels,slots):
    """Append exact donor terrain with a collision-safe graphics merge."""
    terrain,target = tmp/"terrain",tmp/"game"
    # Stage against an inert view of the exact released registry/PBS.
    # The existing game already contains shared FRLG Preview graphics;
    # stage() refuses preexisting assets without owned mapping, so merge
    # and hash-check just the new geometry resources below.
    registry_view = tmp/"registry"
    shutil.copytree(baseline/"Data",registry_view/"Data")
    shutil.copytree(baseline/"PBS",registry_view/"PBS")
    planned = stage(ROOT,source,registry_view,terrain,manifest={
        **catalog,"maps":{str(k):v for k,v in labels.items()},"preview_only":[]})
    actual = {r["source_id"]:r["proposed_id"] for r in planned["maps"]}
    if actual != slots or planned["connections"]:
        raise ValueError("K05 terrain slots or internal connections changed")
    copy_for_ci(baseline,target)
    shutil.copytree(terrain/"Data",target/"Data",dirs_exist_ok=True)
    for src in (terrain/"Graphics").rglob("*"):
        if src.is_file():
            dst = target/src.relative_to(terrain)
            if dst.exists() and (dst.is_symlink() or digest(dst)!=digest(src)):
                raise ValueError(f"K05 terrain conflicts with an existing graphic: {dst.name}")
            if not dst.exists():
                dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(src,dst)
    return target,actual


def run():
    if os.getenv("GITHUB_ACTIONS")!="true":
        raise ValueError("K05 city staging requires a disposable GitHub Actions workspace")
    work = ROOT/".blue-work"
    source = work/"frlg-source/Essentials FRLG"
    baseline = work/"kanto-k05-baseline"
    output = work/"kanto-k05-city"
    if output.exists():
        raise ValueError("K05 staged directory already exists")
    catalog = json_file(KANTO)
    base = json_file(baseline/PILOT_META)
    mapping = {int(k):v for k,v in base["maps"].items()}
    if (len(mapping)!=165 or set(mapping)!=set(map(int,catalog["maps"])) or
            any(mapping.get(int(k))!=v for k,v in published_destinations().items())):
        raise ValueError("K05 baseline is not the published K04 pilot")
    occup,files = inventory(ROOT/"game")
    report = assemble(source,inspect_events(source,K05),catalog,propose_slots(catalog,occup.keys()|files.keys()))
    verify_source(report)
    verify_name_rater(report)
    _,prior_files = inventory(baseline)
    old_hashes = {path.relative_to(baseline):digest(path) for mid,path in prior_files.items() if mid in mapping.values()}
    _,source_maps = inventory(source)
    with TemporaryDirectory(prefix=".k05-city-",dir=work) as folder:
        tmp = Path(folder)
        target,actual = extend_terrain(source,baseline,tmp,catalog,CITY_MAPS,CITY_SLOTS)
        if set(actual.values()) & prior_files.keys():
            raise ValueError("K05 stage collided with a prior MapID")
        info_path=target/"Data/MapInfos.rxdata"
        info=load(info_path)
        stock=[]
        service_events={}
        for sid,name in zip(CITY_MAPS,CITY_NAMES):
            mid=actual[sid]
            path=target/"Data"/f"Map{mid:03d}.rxdata"
            donor,native=load(source_maps[sid]),load(path)
            if any(donor.attrs[k]!=native.attrs[k] for k in ("@data","@width","@height")):
                raise ValueError("K05 altered the original Lavender terrain")
            found=add_city_events(source,target,donor,native,sid,actual)
            if found:
                stock=found
            service_events[sid]=add_services(source,target,donor,native,sid)
            info[mid].attrs["@name"]=name.encode("utf8")
            write_map(path,native,EVENT_CLASSES)
            if load(path)!=native:
                raise ValueError("K05 city changed in Marshal round trip")
        write_map(info_path,info)
        map_rows=target/"PBS/map_metadata_kanto.txt"
        with map_rows.open("a",encoding="utf8") as out:
            for sid,name in zip(CITY_MAPS,CITY_NAMES):
                out.write(f"\n[{actual[sid]:03d}]\nName = {name}\n")
                if sid==93:
                    out.write("Outdoor = true\nShowArea = true\n")
        routes=target/"PBS/map_connections_kanto.txt"
        seam=f"{actual[93]},North,0,{mapping[87]},South,0"
        with routes.open("a",encoding="ascii") as out:
            out.write("\n"+seam+"\n")
        if len(old_hashes)!=165 or any(digest(target/r)!=h or digest(baseline/r)!=h for r,h in old_hashes.items()):
            raise ValueError("K05 changed a previously published map")
        install_runtime(target)
        base["maps"]={**mapping,**actual}
        isolate(target,base)
        (target/"Data/blue-compile-request.txt").write_text("compile",encoding="ascii")
        (target/"Data/PluginScripts.rxdata").unlink(missing_ok=True)
        target.rename(output)
    proof={"maps":actual,"preserved_k04_maps":len(old_hashes),"doors":len(CITY_DOORS),
           "seam":seam,"shop_stock":stock,"center":[actual[94],2],"name_rater":[actual[97],1],
           "service_events":service_events,
           "tower_enabled":False,"fuji_reward_enabled":False,"published":False,"native_gameplay":False}
    (work/"kanto-k05-city-stage.json").write_text(json.dumps(proof,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("KANTO_K05_CITY_STAGE_OK:"+json.dumps(proof),flush=True)


if __name__=="__main__":
    run()
