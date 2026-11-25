"""Read-only F12D3 alternative via existing Route212/215 donor adjacency.
Authorial re-alignment only of originally non-overlapping (empty) records.
No new map, terrain edit, portal, event, runtime gate or save operation.
"""
import hashlib
import sinnoh_f12d_pastoria_preview as chase
import sinnoh_f12d_seams as seams
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10b_trainers as trainers
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as tp
import sinnoh_f12d3_route210_recovery as recovery
import sinnoh_f12d3_gated_alignment as gated

FIXED=((223,"E",0,219,"W",34),(223,"N",0,222,"S",0),
       (126,"W",0,80,"E",0),(116,"S",0,80,"N",0))
BROKEN=((222,"E",0,126,"W",136),(223,"E",0,126,"W",235))
LIMIT=8

def interval(r,dims):
    a,da,oa,b,db,ob=r
    return {n+oa for n in seams.aligned_axes(da,oa,dims[a],db,ob,dims[b])}

def reserved(record,rows,dims):
    for end in seams.ends(record):
        own=interval(end,dims)
        for row in rows:
            for other in seams.ends(row):
                if other[:2]==end[:2] and own&interval(other,dims):
                    return True
    return False

def offsets(left,right):
    return sorted({x-y for x in left for y in right})

def reachable(edges,seeds):
    seen=set(seeds);queue=list(seen)
    while queue:
        for node in edges.get(queue.pop(),()):
            if node not in seen:seen.add(node);queue.append(node)
    return seen

def inspect(blobs,mapping,components,chase_report,expanded,source,root):
    chase.validate(blobs,mapping);before=chase.digest(blobs)
    if expanded.get("input_hashes")!=before or not chase_report.get("runtime_install_enabled"):
        raise ValueError("F12D3_ALTERNATE_STALE")
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    origin=chase_report["placements"][-1]
    def graph(data):
        return gates.access_graph(data,old,components,root,seed_cells=[(origin["map_id"],*origin["stand"])],
            directional=True,strict_movement=True)
    worlds,tiles,idx,_,reached,_=graph(blobs)
    qdims={mid:(w.attrs["@width"],w.attrs["@height"]) for mid,w in worlds.items()}
    current=pv.parse_connections(blobs["PBS/map_connections.txt"])
    if conn.read_marshal(blobs["Data/map_connections.dat"],"F12D3_ALT_COMPILED")!=[recovery.encode(r) for r in current]:
        raise ValueError("F12D3_ALT_COMPILED_MISMATCH")
    edges={};fixed=[];trials=[];counts={};witness=None
    def finish(reason):
        if before!=chase.digest(blobs):raise ValueError("F12D3_ALT_MUTATED")
        return {"status":"F12D3_ALTERNATE_EVIDENCE_ONLY","reason":reason,"candidate_counts":counts,
            "fixed_records":[list(r) for r in fixed],"candidate_trials":trials,"witness":witness,
            "baseline_maps":144,"baseline_preserved":True,"installed":False,"native_verified":False,
            "new_maps":0,"new_portals":0,"new_events":0,"new_seams":0}
    records={tuple(e["source_record"]):e for e in expanded["edge_candidates"]}
    source_map,_,_=conn.graph(root)
    ids={i for row in FIXED+BROKEN for i in (row[0],row[3])}
    bound={i:mapping[source_map[i]["symbol"]] for i in ids}
    baseline=trainers.reached_cells(idx,reached)
    entries=tp.build(blobs,old,components,root)
    def qa(r):return (bound[r[0]],r[1],r[2],bound[r[3]],r[4],r[5])
    def add_links(network,r,lanes):
        for n,x,y in lanes:
            u=(r[0],idx[r[0]][x]);v=(r[3],idx[r[3]][y])
            network.setdefault(u,set()).add(v);network.setdefault(v,set()).add(u)
    with pv.verified_archive(source,"maps") as z:
        source_rows=pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt"))
        donors={};dims={}
        needed=ids|{i for row in source_rows if row[0] in ids or row[3] in ids for i in (row[0],row[3])}
        st=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D3_ALT_TILES")
        for sid in sorted(needed):
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if sid in ids and hashlib.sha256(raw).hexdigest()!=source_map[sid]["sha256"]:
                raise ValueError("F12D3_ALT_SOURCE_HASH")
            w=conn.read_marshal(raw,"F12D3_ALT_SOURCE");dims[sid]=(w.attrs["@width"],w.attrs["@height"])
            if sid in ids:
                if dims[sid]!=qdims[bound[sid]]:raise ValueError("F12D3_ALT_DIMENSIONS")
                donors[sid]=w
        if any(source_rows.count(r)!=1 or interval(r,dims) for r in BROKEN):
            return finish("broken_records_no_longer_empty")
        for s in FIXED:
            e=records.get(s);r=qa(s)
            if not e or e["installed"] or e["source_side_conflict"] or e["target_side_already_used"]:
                return finish("fixed_original_seam_unavailable")
            lanes=gated.all_lanes(r,idx,qdims)
            if not lanes or [n for n,x,y in lanes]!=e["matching_walkable_axes"]:
                return finish("fixed_original_lanes_unverified")
            fixed.append(r);add_links(edges,r,lanes)
        reached_fixed=reachable(edges,reached)
        if not any(mid==bound[223] for mid,_ in reached_fixed):
            return finish("route212_component_unreachable")
        reserve=[row for row in source_rows if row[0] in ids or row[3] in ids]
        def border(sid,d):
            mid=bound[sid];w,h=dims[sid];size=w if d in ("N","S") else h
            out={}
            for n in range(size):
                xy=seams.point(n,d,0,(w,h))
                if xy not in idx[mid]:continue
                a=gates.cell_shape(donors[sid],st,xy);b=gates.cell_shape(worlds[mid],tiles,xy)
                if a==b and a["ordinary_walkable"]:out[n]=xy
            return out
        proposals=[]
        for broken in BROKEN:
            sid,_,_,dst,_,_=broken
            for direction in ("N","S","E","W"):
                opposite=conn.OPPOSITE[direction];left=border(sid,direction);right=border(dst,opposite)
                stats={"offsets":0,"reserved":0,"unverified":0,"component_candidates":0}
                counts["%s_%s_%s"%(sid,direction,dst)]=stats
                for delta in offsets(left,right):
                    stats["offsets"]+=1
                    s=(sid,direction,max(delta,0),dst,opposite,max(-delta,0));r=qa(s)
                    if reserved(s,reserve,dims) or reserved(r,current+fixed,qdims):
                        stats["reserved"]+=1;continue
                    lanes=gated.all_lanes(r,idx,qdims)
                    expected={(left[n],right[n-delta]) for n in left if n-delta in right}
                    if not lanes or {(x,y) for _,x,y in lanes}!=expected:
                        stats["unverified"]+=1;continue
                    network={k:set(v) for k,v in edges.items()};add_links(network,r,lanes)
                    reach=reachable(network,reached)
                    if not all(any(mid==bound[i] for mid,_ in reach) for i in (223,222,126,80,116)):
                        continue
                    stats["component_candidates"]+=1
                    proposals.append((len(lanes),r,lanes,s))
        for _,r,lanes,s in sorted(proposals,key=lambda p:(-p[0],p[1]))[:LIMIT]:
            records2=current+fixed+[r];trial=dict(blobs)
            trial["PBS/map_connections.txt"]=blobs["PBS/map_connections.txt"]+("\n# F12D3 authorial alternative fixture only\n"+"\n".join(",".join(map(str,k)) for k in fixed+[r])+"\n").encode("ascii")
            trial["Data/map_connections.dat"]=conn.serialize([recovery.encode(k) for k in records2])
            _,_,ix,_,rr,_=graph(trial);cells=trainers.reached_cells(ix,rr)
            totals={str(i):sum(p[0]==bound[i] for p in cells) for i in (223,222,126,80,116)}
            ok=baseline<=cells and all(totals.values()) and tp.build(trial,old,components,root)==entries
            trials.append({"source_record":list(s),"qa_record":list(r),"lanes":len(lanes),"reachable_cells":totals,"fixture_passed":ok})
            if ok:
                witness=trials[-1];break
    return finish("candidate_fixture_only" if witness else "no_verified_alternative_in_bounded_search")
