"""F12D3 authored gate fixture: never loaded by installer.
Uses audited dry lanes, no tiles changed, no artificial transfers.
The closed fixture is an occupancy proof, not a native runtime gate.
"""
import sinnoh_f12d_pastoria_preview as chase
import sinnoh_f12d_seams as seams
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10b_trainers as trainers
import sinnoh_f12d3_route210_recovery as recovery
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as tp
from build_johto_events import EVENT_CLASSES,ruby,event_page

def all_lanes(record,index,dims):
    a,da,oa,b,db,ob=record
    return [(n,seams.point(n,da,oa,dims[a]),seams.point(n,db,ob,dims[b]))
        for n in seams.aligned_axes(da,oa,dims[a],db,ob,dims[b])
        if seams.point(n,da,oa,dims[a]) in index[a] and seams.point(n,db,ob,dims[b]) in index[b]]

def prepare(blobs,mapping,components,chase_report,expanded,offset,root):
    chase.validate(blobs,mapping)
    def blocked(reason,attempts=()):
        return blobs,{"status":"F12D3_GATED_ALIGNMENT_BLOCKED","reason":reason,
            "attempts":list(attempts),"new_seams":0,"new_portals":0,"installed":False,"native_verified":False}
    if (expanded.get("input_hashes")!=chase.digest(blobs) or
        offset.get("status")!="F12D3_AUTHORED_OFFSET_EVIDENCE_ONLY" or
        not chase_report.get("runtime_install_enabled")):
        return blocked("missing_fresh_evidence")
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    a=mapping["SINNOH_ROUTE_210"];b=mapping["SINNOH_PASTORIA_CITY"];s=mapping["SINNOH_ROUTE_210_SEGMENT_2"]
    current=pv.parse_connections(blobs["PBS/map_connections.txt"])
    if conn.read_marshal(blobs["Data/map_connections.dat"],"F12D3_GATED_CONNECTIONS")!=[recovery.encode(r) for r in current]:
        return blocked("compiled_mismatch")
    if any((u,d) in {(a,"E"),(b,"W"),(a,"N"),(s,"S")} for r in current for u,d,*_ in seams.ends(r)):
        return blocked("existing_side_conflict")
    origin=chase_report["placements"][-1]
    def graph(data):
        return gates.access_graph(data,old,components,root,
            seed_cells=[(origin["map_id"],*origin["stand"])],directional=True,strict_movement=True)
    worlds,tiles,idx,_,reached,_=graph(blobs)
    prior_cells=trainers.reached_cells(idx,reached)
    dims={mid:(v.attrs["@width"],v.attrs["@height"]) for mid,v in worlds.items()}
    entries=tp.build(blobs,old,components,root)
    protected={tuple(r[3]) for r in entries if r[3]}
    for world in worlds.values():
        for event in world.attrs["@events"].values():
            trans,_=conn.classify_transfer(event)
            if trans:
                _,_,dst,x,y,_,_=trans
                protected.add((dst,x,y))
    continuation=(s,"S",0,a,"N",0)
    cont=next((r for r in expanded["edge_candidates"] if tuple(r["qa_record"])==continuation),None)
    if not cont or cont["source_side_conflict"] or cont["installed"] or not cont["matching_walkable_axes"]:
        return blocked("continuation_conflict")
    axes=all_lanes(continuation,idx,dims)
    if [x[0] for x in axes]!=cont["matching_walkable_axes"]:
        return blocked("continuation_unverified_lanes")
    attempts=[]
    # Prefer broad verified passage, then the smallest offset among ties.
    candidates=sorted((r for r in offset["candidate_offsets"] if r["reaches_segment2"]),
        key=lambda r:(-len(r["lanes"]),r["offset_west"],r["offset_east"]))
    for row in candidates:
        record=(a,"E",row["offset_east"],b,"W",row["offset_west"])
        lanes=all_lanes(record,idx,dims)
        pairs={(x[1],y[1]) for _,x,y in lanes}
        expected={(r["east_y"],r["west_y"]) for r in row["lanes"]}
        cells={(a,*x) for _,x,_ in lanes}
        if not pairs or pairs!=expected or cells&protected or cells&prior_cells:
            attempts.append({"record":list(record),"reason":"unverified_or_protected_lane"})
            continue
        linked=dict(blobs);new_rows=[record,continuation]
        linked["PBS/map_connections.txt"]=blobs["PBS/map_connections.txt"]+(
            "\n# F12D3 AUTHORIAL alignment fixture; original continuation\n"+
            "\n".join(",".join(map(str,r)) for r in new_rows)+"\n").encode("ascii")
        linked["Data/map_connections.dat"]=conn.serialize([recovery.encode(r) for r in current+new_rows])
        _,_,i1,_,r1,_=graph(linked);open_cells=trainers.reached_cells(i1,r1)
        counts={str(mid):sum(p[0]==mid for p in open_cells) for mid in (a,s)}
        if not prior_cells<=open_cells or not all(counts.values()) or tp.build(linked,old,components,root)!=entries:
            attempts.append({"record":list(record),"reason":"open_graph_or_entries_failed"});continue
        # Block every verified crossing on the new Route210 side. These events
        # are temporary graph witnesses, not actual runtime event pages.
        world=conn.read_marshal(blobs["Data/Map%03d.rxdata"%a],"F12D3_GATE_MAP")
        events=world.attrs["@events"];start=max(max(events,default=0)+1,3001)
        for i,(_,x,y) in enumerate(sorted(cells)):
            eid=start+i
            events[eid]=ruby("RPG::Event",id=eid,name=b"SN_F12D3_GATE_WITNESS",
                x=x,y=y,pages=[event_page(script="nil",sprite="")])
        closed=dict(linked);closed["Data/Map%03d.rxdata"%a]=conn.serialize(world,EVENT_CLASSES)
        _,_,i2,_,r2,_=graph(closed)
        closed_cells=trainers.reached_cells(i2,r2)
        if closed_cells!=prior_cells:
            attempts.append({"record":list(record),"reason":"closed_progression_changed"});continue
        if pv.parse_connections(linked["PBS/map_connections.txt"])!=current+new_rows or any(
            linked[k]!=v for k,v in blobs.items() if k not in ("PBS/map_connections.txt","Data/map_connections.dat")):
            raise ValueError("F12D3_GATE_BASELINE_CHANGED")
        return linked,{"status":"F12D3_GATED_ALIGNMENT_FIXTURE_PREPARED","authored_record":list(record),
            "original_continuation":list(continuation),"gate_cells":[list(p) for p in sorted(cells)],
            "crossing_lanes":[{"axis":n,"route":list(x),"pastoria":list(y)} for n,x,y in lanes],
            "open_reachable_cells":counts,"closed_reachable_cells":len(closed_cells),
            "baseline_reachable_cells":len(prior_cells),"closed_equals_baseline":True,
            "competing_source_records":offset["competing_source_records"],
            "attempts":attempts,"new_seams":2,"new_portals":0,"installed":False,
            "requires_native_gate_and_future_topology_review":True,"native_verified":False}
    return blocked("no_safe_gated_offset",attempts)
