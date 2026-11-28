"""Isolated K05 Tower terrain, source stairs and a fail-closed summit."""
from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from audit import KANTO, ROOT, inventory, json_file, load
from audit_k05_lavender import TOWER
from build_k05_city import CITY_SLOTS, digest, extend_terrain, isolate
from pilot import EVENT_CLASSES, PILOT_META, command, new_event, write_map

LABELS = {sid: f"POKEMON_TOWER_{sid-99}F" for sid in TOWER}
SLOTS = {sid: sid+515 for sid in TOWER}
SAVE_APP = "Kanto K05 Tower CI"
# Exact original touch tile, source destination, landing and direction.
STAIRS = {
    (93,8):((18,6),100,(9,18),8),
    (100,1):((9,19),93,(18,7),0), (100,7):((17,9),101,(16,10),4),
    (101,1):((17,10),100,(16,9),4), (101,5):((1,10),102,(2,10),6),
    (102,5):((17,10),103,(16,10),4), (102,6):((1,10),101,(2,10),6),
    (103,7):((17,10),102,(16,10),4), (103,8):((1,10),104,(2,10),6),
    (104,9):((1,10),103,(2,10),6), (104,10):((17,10),105,(16,10),4),
    (105,7):((17,10),104,(16,10),4), (105,8):((8,16),106,(9,16),6),
    (106,12):((8,16),105,(9,16),6),
}
SUMMIT_GATE = (105,8)
FUJI_RETURN = (106,1)
# Two authored warning contacts flank the original summit staircase. In the
# source they own the apparition logic; K05 retains only their refusal.
GHOST_CONTACTS = {6: (9,15), 10:(10,16)}


def ghost_warning():
    return command(355, b'pbMessage(BlueKantoPilot.t("An unidentified ghost blocks the way.", "Um fantasma impede a passagem."))')



def verify_evidence(report):
    source = {(r["source"],r["event"]):(tuple(r["at"]),r["destination"],tuple(r["xy"]),r["direction"])
              for r in report["transfers"] if r["source"] in TOWER or (r["source"],r["event"]) == (93,8)}
    if source != {**STAIRS,FUJI_RETURN:((9,4),98,(4,7),8)}:
        raise ValueError("K05 Tower original staircase or deferred Fuji return changed")
    refs = {(r["source"],r["event"]):set(r["references"]) for r in report["actors"]
            if r["source"]==105 and "SILPHSCOPE" in r["references"]}
    anchored = {(r["event"],tuple(r["at"])) for r in report["actors"]
                if r["source"]==105 and r["event"] in GHOST_CONTACTS and r["trigger"]==2}
    if anchored!=set(GHOST_CONTACTS.items()) or not {(105,6),(105,9),(105,10)} <= refs.keys() or not all(
            "MAROWAK" in refs[(105,e)] for e in (6,10)):
        raise ValueError("K05 lacked original Scope/ghost evidence near the summit")


def compile_stair(row, mapping, blocked=False):
    _, dest, xy, direction = row
    if blocked:
        if dest!=106:
            raise ValueError("Only the original summit stair may be blocked here")
        # K05 intentionally never unlocks upper-floor progression. K06
        # introduces the item, and K07 separately owns Marowak/Rocket/Fuji.
        return [ghost_warning()]
    return [command(201,0,mapping[dest],*xy,direction,0)]


def run():
    if os.getenv("GITHUB_ACTIONS")!="true":
        raise ValueError("K05 Tower staging is for a disposable Actions workspace")
    work=ROOT/".blue-work"
    source=work/"frlg-source/Essentials FRLG"
    baseline=work/"kanto-k05-city"
    output=work/"kanto-k05-tower"
    if output.exists():
        raise ValueError("K05 Tower candidate already exists")
    meta=json_file(baseline/PILOT_META)
    current={int(k):v for k,v in meta["maps"].items()}
    if (len(current)!=171 or not meta.get("k05_city_fixture_only") or
            any(current.get(sid)!=mid for sid,mid in CITY_SLOTS.items())):
        raise ValueError("K05 Tower requires the isolated city stage")
    report=json_file(work/"kanto-k05-source.json")
    verify_evidence(report)
    source_info={row["id"]:row for row in report["maps"]}
    _,old=inventory(baseline)
    _,donors=inventory(source)
    before={p.relative_to(baseline):digest(p) for p in old.values()}
    mapping={**current,**SLOTS}
    expected_city=Path("Data")/f"Map{current[93]:03d}.rxdata"
    with TemporaryDirectory(prefix=".k05-tower-",dir=work) as td:
        target,actual=extend_terrain(source,baseline,Path(td),json_file(KANTO),LABELS,SLOTS)
        if actual!=SLOTS or set(SLOTS.values()) & old.keys():
            raise ValueError("K05 Tower MapID collision")
        infos=target/"Data/MapInfos.rxdata"
        map_info=load(infos)
        for sid in (93,*TOWER):
            n=mapping[sid]
            original=donors[sid]
            ours=target/"Data"/f"Map{n:03d}.rxdata"
            if digest(original)!=source_info[sid]["sha256"]:
                raise ValueError(f"K05 source receipt digest changed for {sid}")
            donor,native=load(original),load(ours)
            if any(donor.attrs[k]!=native.attrs[k] for k in ("@width","@height","@data")):
                raise ValueError(f"K05 Tower terrain differs from source {sid}")
            events=native.attrs["@events"]
            if sid in TOWER and events:
                raise ValueError("K05 Tower cannot carry donor events")
            for (src,eid),row in STAIRS.items():
                if sid!=src:
                    continue
                event=donor.attrs["@events"][eid]
                if eid in events or tuple(event.attrs[k] for k in ("@x","@y"))!=row[0]:
                    raise ValueError("K05 Tower anchor or destination changed")
                events[eid]=new_event(event,compile_stair(row,mapping,(src,eid)==SUMMIT_GATE),1,b"")
            if sid==105:
                for eid,xy in GHOST_CONTACTS.items():
                    event=donor.attrs["@events"][eid]
                    if eid in events or tuple(event.attrs[k] for k in ("@x","@y"))!=xy:
                        raise ValueError("K05 warning moved from the original ghost anchor")
                    events[eid]=new_event(event,[ghost_warning()],1,b"")
            if sid in TOWER:
                map_info[n].attrs["@name"]=source_info[sid]["name"].encode("utf8")
            write_map(ours,native,EVENT_CLASSES)
            if load(ours)!=native:
                raise ValueError("K05 Tower event lost in Marshal roundtrip")
        write_map(infos,map_info)
        with (target/"PBS/map_metadata_kanto.txt").open("a",encoding="utf8") as pbs:
            for sid,n in actual.items():
                pbs.write(f"\n[{n:03d}]\nName = {source_info[sid]['name']}\n")
        if any(digest(baseline/p)!=h or (p!=expected_city and digest(target/p)!=h) for p,h in before.items()):
            raise ValueError("K05 Tower changed an outside map or prior city service")
        meta["maps"]=mapping
        meta.pop("k05_city_fixture_only")
        isolate(target,meta,profile=SAVE_APP,fixture="k05_tower_fixture_only")
        target.rename(output)
    result={"map_ids":SLOTS,"guard":list(SUMMIT_GATE),"ghost_contacts":GHOST_CONTACTS,"summit_activated":False,
            "fuji_transfer_enabled":False,"encounters_and_actors_enabled":False,
            "native_gameplay":False,"published":False,"preserved_prior_maps":len(before)-1,
            "city_entrance_event_only":[mapping[93],8]}
    (work/"kanto-k05-tower-stage.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    print("KANTO_K05_TOWER_STAGE_OK:"+json.dumps(result),flush=True)


if __name__=="__main__":
    run()
