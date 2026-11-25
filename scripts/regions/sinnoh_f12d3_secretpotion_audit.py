"""F12D3 evidence-first audit: no donor script execution or item grants."""
import hashlib
import re
import sinnoh_f12d_pastoria_preview as chase
import sinnoh_f12b2_windworks_evidence as evidence
import sinnoh_f10b7_field_audit as gates
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as tp

SOURCES={
    214:chase.SOURCES[214],
    80:("SINNOH_ROUTE_210","b80337a98cfdeb0d02a431cb55ff95566b8647b9d602a3a2fcbdbd39a71da293"),
    116:("SINNOH_ROUTE_210_SEGMENT_2","0415779012d672d9018800ac09ddd48ed7650648188cf94b97f9242e4112584d"),
}
MARKERS=re.compile(rb"(?<![A-Za-z0-9_])(?:SECRET_?POTION|PSYDUCK|CYNTHIA)(?![A-Za-z0-9_])",re.I)
ORDER=("PASTORIA","ROUTE_213","VALOR_BATTLE")

def tokens(raw):
    return sorted({x.upper().replace(b"_",b"").decode("ascii") for x in MARKERS.findall(raw)})

def chase_prepared(report):
    return (report.get("status")=="F12D_RUNTIME_PREPARED" and report.get("runtime_install_enabled") is True
        and report.get("baseline_maps")==144 and report.get("new_events")==3 and report.get("new_seams")==2
        and report.get("new_portals")==0 and report.get("new_maps")==0
        and tuple(p.get("id") for p in report.get("placements",()))==ORDER)

def markers(event):
    a=event.attrs
    values=[a.get("@name")]
    for page in a["@pages"]:
        p=page.attrs
        values.append(getattr(p.get("@graphic"),"attrs",{}).get("@character_name"))
        for command in p["@list"]:
            c=command.attrs
            if c.get("@code") not in (101,401,108,408,111,355,655):continue
            values.extend(c.get("@parameters",[]))
    return sorted({token for raw in values if isinstance(raw,bytes) for token in tokens(raw)})

def audit(blobs,mapping,components,report,source,root):
    chase.validate(blobs,mapping)
    if not chase_prepared(report):raise ValueError("F12D3_REQUIRES_F12D2")
    before=chase.digest(blobs)
    for sid in chase.AREAS:
        mid=mapping[sid]
        if report.get("final_map_hashes",{}).get(str(mid))!=before["Data/Map%03d.rxdata"%mid]:
            raise ValueError("F12D3_CHASE_HASH_MISMATCH")
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    entries=tp.build(blobs,old,components,root)
    origin=report["placements"][-1]
    worlds,tiles,idx,groups,reached,graph=gates.access_graph(blobs,old,components,root,
        seed_cells=[(origin["map_id"],*origin["stand"])],directional=True,strict_movement=True)
    rows=[]
    with pv.verified_archive(source,"maps") as z:
        st=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D3_SOURCE_TILES")
        for sid,(sym,expected) in SOURCES.items():
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("F12D3_SOURCE_HASH")
            donor=conn.read_marshal(raw,"F12D3_SOURCE")
            mid=mapping[sym];qa=worlds[mid]
            if (donor.attrs["@width"],donor.attrs["@height"])!=(qa.attrs["@width"],qa.attrs["@height"]):
                raise ValueError("F12D3_SOURCE_DIMENSIONS")
            events=[]
            for eid,event in sorted(donor.attrs["@events"].items()):
                xy=(event.attrs["@x"],event.attrs["@y"])
                if not (0<=xy[0]<qa.attrs["@width"] and 0<=xy[1]<qa.attrs["@height"]):
                    raise ValueError("F12D3_EVENT_COORDINATE")
                adjacent=[list(q) for q in tp.neighbours(*xy) if (mid,idx[mid].get(q)) in reached]
                ev=evidence.event_evidence(event,eid)
                ev.update(quest_markers=markers(event),source_cell=gates.cell_shape(donor,st,xy),
                    qa_cell=gates.cell_shape(qa,tiles,xy),reachable_adjacent_from_valor=adjacent)
                events.append(ev)
            rows.append({"source_id":sid,"symbol":sym,"map_id":mid,"source_sha256":expected,
                "qa_sha256":before["Data/Map%03d.rxdata"%mid],"event_count":len(events),"events":events,
                "reachable_cells_from_valor":sum((mid,label) in reached for label in idx[mid].values())})
        seams=[list(row) for row in pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt")) if any(x in SOURCES for x in (row[0],row[3]))]
    if before!=chase.digest(blobs) or tp.build(blobs,old,components,root)!=entries:
        raise ValueError("F12D3_BASELINE_MUTATED")
    return {"status":"F12D3_SOURCE_GEOMETRY_AUDITED","baseline_maps":144,"baseline_preserved":True,
        "maps":rows,"source_connections":seams,"graph":graph,"origin":origin,
        "marker_candidates":sum(bool(e["quest_markers"]) for row in rows for e in row["events"]),
        "runtime_install_enabled":False,"native_verified":False,"items_granted":0,
        "new_events":0,"new_maps":0,"new_portals":0,"new_seams":0,"saves_accessed":False,
        "source_scripts_executed":False,"binding_requires":"source identity, strict walking, local unique item catalogue, regional ledger and atomic grant/consume"}
