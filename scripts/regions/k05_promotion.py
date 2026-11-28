"""Compose validated K05 stage adapters into an ordinary prepared Kanto build."""
from __future__ import annotations

from audit import inventory, load
from audit_cerulean_interiors import inspect_events
from audit_k05_lavender import assemble
from build_k05_city import add_city_events, verify_source
from build_k05_tower import GHOST_CONTACTS, STAIRS, SUMMIT_GATE, compile_stair, ghost_warning, verify_evidence
from k05_contract import CITY, LAVENDER_BOUNDARY, MAPS, NAMES, SLOTS, TOWER, predecessor_sets
import k05_lavender_services as services
import k05_tower_actors as actors
from pilot import EVENT_CLASSES, new_event, write_map


def verify_plan(mapping,plan):
    if len(mapping)!=178 or any(mapping.get(sid)!=mid for sid,mid in SLOTS.items()):
        raise ValueError("K05 product requires its thirteen exact nonrelocatable slots")
    rows=[tuple(row) for row in plan["connections"] if {row[0],row[3]} & set(SLOTS.values())]
    s0,d0,o0,s1,d1,o1=LAVENDER_BOUNDARY
    if rows!=[(mapping[s0],d0,o0,mapping[s1],d1,o1)]:
        raise ValueError("K05 must have just the original route 10 seam")


def install(source,target,mapping,plan,catalog):
    """Prepared only; never edits old published save/maps in an installation."""
    verify_plan(mapping,plan)
    old_catalog=predecessor_sets(catalog["maps"]).get(165)
    if old_catalog is None or set(catalog.get("preview_only",())) & MAPS.keys():
        raise ValueError("K05 invalid published baseline or protected preview")
    historic={**catalog,"maps":{k:catalog["maps"][k] for k in old_catalog}}
    report=assemble(source,inspect_events(source,MAPS),historic,SLOTS)
    verify_source(report)
    verify_evidence(report)
    services.verify_name_rater(report)
    specs=actors.profiles(report)
    sources={row["id"]:row for row in report["maps"]}
    from build_k05_city import digest
    _,src=inventory(source)
    for sid,role in MAPS.items():
        path=target/"Data"/f"Map{mapping[sid]:03}.rxdata"
        if digest(src[sid])!=sources[sid]["sha256"] or sources[sid]["name"]!=NAMES[role]:
            raise ValueError(f"K05 product source changed: {sid}")
        donor,native=load(src[sid]),load(path)
        if native.attrs["@events"] or any(native.attrs[k]!=donor.attrs[k]
                          for k in ("@width","@height","@data")):
            raise ValueError(f"K05 product copied source events or changed terrain: {sid}")
        if sid in CITY:
            add_city_events(source,target,donor,native,sid,mapping)
            services.add_services(source,target,donor,native,sid)
        if sid in TOWER or sid==93:
            events=native.attrs["@events"]
            originals=donor.attrs["@events"]
            for (area,eid),row in STAIRS.items():
                if area!=sid:
                    continue
                e=originals[eid]
                if eid in events or (e.attrs["@x"],e.attrs["@y"])!=row[0]:
                    raise ValueError(f"K05 product stair anchor changed: {sid}/{eid}")
                events[eid]=new_event(e,compile_stair(row,mapping,(sid,eid)==SUMMIT_GATE),1,b"")
            if sid==105:
                for eid,xy in GHOST_CONTACTS.items():
                    e=originals[eid]
                    if eid in events or (e.attrs["@x"],e.attrs["@y"])!=xy:
                        raise ValueError("K05 product ghost contact moved")
                    events[eid]=new_event(e,[ghost_warning()],1,b"")
            if sid in TOWER:
                actors.install_events(source,target,donor,native,sid)
        write_map(path,native,EVENT_CLASSES)
        if load(path)!=native:
            raise ValueError(f"K05 product map did not survive Marshal roundtrip: {sid}")
    actors.install_trainer_pbs(source,target,specs)
    actors.install_encounter_pbs(source,target,mapping,report)
    services.install_runtime(target)
    actors.install_runtime(target)
