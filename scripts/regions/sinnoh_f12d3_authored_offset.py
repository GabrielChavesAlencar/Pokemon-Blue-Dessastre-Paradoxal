"""Authorial alignment investigation of the invalid original 80 E201 ->219 W0.
Read-only. Does not claim this is canonical Platinum geography or install a shortcut.
"""
import hashlib
import sinnoh_f12d3_secretpotion_audit as audit
import sinnoh_f12d_pastoria_preview as chase
import sinnoh_f12d_seams as seams
import sinnoh_f10b7_field_audit as gates
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv

ORIGINAL=(80,"E",201,219,"W",0)

def offset_rows(east,west,continuation):
    # east/west maps y -> local component id, west already reachable
    offsets=sorted({y-z for y in east for z in west})
    rows=[]
    for delta in offsets:
        lanes=[{"east_y":y,"west_y":y-delta,"route_component":label,
                "segment2_components":sorted(continuation.get(label,set()))}
               for y,label in sorted(east.items()) if y-delta in west]
        rows.append({"offset_east":max(delta,0),"offset_west":max(-delta,0),
            "lanes":lanes,"reaches_segment2":any(x["segment2_components"] for x in lanes)})
    return rows

def competing_side_report(candidates,competitors,dims,edge_candidates):
    """Conservative reservation of the entire aligned interval, not just dry cells."""
    def oriented(record,sid,side):
        return next((r for r in seams.ends(record) if r[:2]==(sid,side)),None)
    def axes(record):
        a,da,oa,b,db,ob=record
        return {n+oa for n in seams.aligned_axes(da,oa,dims[a],db,ob,dims[b])}
    def known_dry(record,sid,side):
        edge=next((e for e in edge_candidates if tuple(e["source_record"]) in seams.ends(record)),None)
        if edge is None:
            return None
        end=oriented(tuple(edge["source_record"]),sid,side)
        return {n+end[2] for n in edge["matching_walkable_axes"]}
    result=[]
    for row in candidates:
        if not row["reaches_segment2"]:continue
        record=(80,"E",row["offset_east"],219,"W",row["offset_west"])
        conflicts=[]
        for competitor in competitors:
            for sid,side,key in ((80,"E","east_y"),(219,"W","west_y")):
                other=oriented(tuple(competitor),sid,side)
                if other is None:continue
                own=axes(oriented(record,sid,side))
                reserved=axes(other)
                common=own&reserved
                dry=known_dry(tuple(competitor),sid,side)
                dry_overlap=None if dry is None else sorted(dry&{x[key] for x in row["lanes"]})
                conflicts.append({"source_id":sid,"side":side,"competitor":list(competitor),
                    "candidate_interval":sorted(own),"reserved_interval":sorted(reserved),
                    "geometric_overlap":sorted(common),"dry_overlap":dry_overlap})
        result.append({"record":list(record),"competing_sides":conflicts,
            "activation_allowed":bool(conflicts) and not any(x["geometric_overlap"] or x["dry_overlap"] is None for x in conflicts)})
    return result

def inspect(blobs,mapping,components,chase_report,expanded,source,root):
    chase.validate(blobs,mapping)
    before=chase.digest(blobs)
    if expanded.get("input_hashes")!=before:raise ValueError("F12D3_OFFSET_STALE")
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    origin=chase_report["placements"][-1]
    worlds,tiles,idx,_,reached,_=gates.access_graph(blobs,old,components,root,
        seed_cells=[(origin["map_id"],*origin["stand"])],directional=True,strict_movement=True)
    a=mapping[audit.SOURCES[80][0]];b=mapping[chase.SOURCES[219][0]];s=mapping[audit.SOURCES[116][0]]
    current=pv.parse_connections(blobs["PBS/map_connections.txt"])
    if any((u,d) in {(a,"E"),(b,"W"),(a,"N"),(s,"S")}
           for r in current for u,d,*_ in seams.ends(r)):
        return {"status":"F12D3_OFFSET_BLOCKED_EXISTING_SIDE","new_seams":0,"native_verified":False}
    with pv.verified_archive(source,"maps") as z:
        rows=pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt"))
        if rows.count(ORIGINAL)!=1:raise ValueError("F12D3_OFFSET_SOURCE_RECORD")
        st=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D3_OFFSET_TILES")
        src={}
        for sid,(sym,digest) in {80:audit.SOURCES[80],116:audit.SOURCES[116],219:chase.SOURCES[219]}.items():
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError("F12D3_OFFSET_SOURCE_HASH")
            src[sid]=conn.read_marshal(raw,"F12D3_OFFSET_MAP")
        def border(sid,mid,direction,only_reached=False):
            donor=src[sid];world=worlds[mid]
            w,h=donor.attrs["@width"],donor.attrs["@height"]
            if (w,h)!=(world.attrs["@width"],world.attrs["@height"]):raise ValueError("F12D3_OFFSET_DIMS")
            result={}
            for y in range(h):
                xy=(w-1 if direction=="E" else 0,y)
                label=idx[mid].get(xy)
                if label is None or (only_reached and (mid,label) not in reached):continue
                ss=gates.cell_shape(donor,st,xy);qq=gates.cell_shape(world,tiles,xy)
                if ss==qq and ss.get("ordinary_walkable") is True:result[y]=label
            return result
        east=border(80,a,"E");west=border(219,b,"W",True)
        edge=next((r for r in expanded["edge_candidates"] if r["source_record"]==[116,"S",0,80,"N",0]),None)
        if edge is None:raise ValueError("F12D3_OFFSET_CONTINUATION_MISSING")
        continuation={}
        for axis in edge["matching_walkable_axes"]:
            x=(axis,0);y=(axis,worlds[s].attrs["@height"]-1)
            if x in idx[a] and y in idx[s]:continuation.setdefault(idx[a][x],set()).add(idx[s][y])
        candidates=offset_rows(east,west,continuation)
        competitors=[list(r) for r in rows if r!=ORIGINAL and any((u,d) in {(80,"E"),(219,"W")} for u,d,*_ in seams.ends(r))]
        dims={sid:(w.attrs["@width"],w.attrs["@height"]) for sid,w in src.items()}
        neighbor_hashes={}
        for sid in sorted({sid for r in competitors for sid in (r[0],r[3])}-set(dims)):
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            world=conn.read_marshal(raw,"F12D3_FUTURE_NEIGHBOR")
            dims[sid]=(world.attrs["@width"],world.attrs["@height"])
            neighbor_hashes[str(sid)]=hashlib.sha256(raw).hexdigest()
        future=competing_side_report(candidates,competitors,dims,expanded["edge_candidates"])
    if before!=chase.digest(blobs):raise ValueError("F12D3_OFFSET_MUTATED")
    return {"status":"F12D3_AUTHORED_OFFSET_EVIDENCE_ONLY","original_record":list(ORIGINAL),
        "source_layout":"PROJECT_AUTHORED_ALIGNMENT_HYPOTHESIS_NOT_CANONICAL",
        "east_dry_axes":sorted(east),"west_reachable_dry_axes":sorted(west),
        "candidate_offsets":candidates,"continuation_axes":edge["matching_walkable_axes"],
        "candidate_offsets_reaching_both":sum(r["reaches_segment2"] for r in candidates),
        "competing_source_records":competitors,"future_topology_conflicts":future,
        "future_neighbor_hashes":neighbor_hashes,"future_activation_allowed":any(x["activation_allowed"] for x in future),
        "new_seams":0,"new_portals":0,
        "native_verified":False,"installed":False}
