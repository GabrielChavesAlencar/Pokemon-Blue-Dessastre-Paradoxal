"""F12D: recover only unambiguous, physically walkable original seams.
Never modify terrain, portal events, MapIDs, prior connections or saves.
The caller commits the candidate only if the full ordered chase also passes.
"""
import hashlib
import sinnoh_f12d_pastoria_preview as p
import sinnoh_private_visual as pv
import sinnoh_connection_expansion as conn
import sinnoh_f10b7_field_audit as gates
import sinnoh_qa_teleport as tp

def ends(r):
    return ((r[0],r[1],r[2],r[3],r[4],r[5]),(r[3],r[4],r[5],r[0],r[1],r[2]))

def point(axis,d,offset,size):
    w,h=size; n=axis+offset
    return (n,0 if d=="N" else h-1) if d in ("N","S") else (0 if d=="W" else w-1,n)

def aligned_axes(da,oa,size_a,db,ob,size_b):
    """All physical intersections; do not assume either QA spawn is connected."""
    na=size_a[0] if da in ("N","S") else size_a[1]
    nb=size_b[0] if db in ("N","S") else size_b[1]
    return range(max(-oa,-ob),min(na-oa,nb-ob))

def lane_allowed(source_a,source_b,qa_a,qa_b,occupied_a,occupied_b):
    # Match ordered terrain/passage stacks after remapping; never open a wall.
    return (source_a==qa_a and source_b==qa_b and
            source_a.get("ordinary_walkable") is True and
            source_b.get("ordinary_walkable") is True and
            not occupied_a and not occupied_b)

def repair(blobs,mapping,components,path,root):
    p.validate(blobs,mapping)
    old={k:v for k,v in mapping.items() if k in p.prior.ALL}
    entries=tp.build(blobs,old,components,root)
    arrivals={r[0]:tuple(r[3][1:]) for r in entries if r[3]}
    original=pv.parse_connections(blobs["PBS/map_connections.txt"])
    compiled=conn.read_marshal(blobs["Data/map_connections.dat"],"F12D_CONNECTIONS")
    def encode(r):
        return [r[0],r[1].encode("ascii"),r[2],r[3],r[4].encode("ascii"),r[5]]
    if compiled!=[encode(r) for r in original]:
        raise ValueError("F12D_COMPILED_CONNECTIONS_MISMATCH")
    tiles=conn.read_marshal(blobs["Data/Tilesets.rxdata"],"F12D_TILES")
    worlds={sid:conn.read_marshal(blobs["Data/Map%03d.rxdata"%mapping[sym]],"F12D_MAP") for sid,(sym,_) in p.SOURCES.items()}
    dims={sid:(w.attrs["@width"],w.attrs["@height"]) for sid,w in worlds.items()}
    masks={sid:gates.directional_masks(w,tiles) for sid,w in worlds.items()}
    reached={};occupied={}
    for sid,w in worlds.items():
        sym=p.SOURCES[sid][0]
        busy={(e.attrs["@x"],e.attrs["@y"]) for e in w.attrs["@events"].values()}
        occupied[sid]=busy
        strict={xy:mask for xy,mask in masks[sid].items() if mask==0}
        reached[sid]=gates.directional_component(set(strict)-busy,arrivals[sym],strict)
    records=[];details=[]
    with pv.verified_archive(path,"maps") as z:
        rows=pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt"))
        source_worlds={}
        source_tiles=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D_SOURCE_TILES")
        for sid,(_,expected) in p.SOURCES.items():
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("F12D_SOURCE_HASH")
            source_worlds[sid]=conn.read_marshal(raw,"F12D_SOURCE_EDGE")
            a=source_worlds[sid].attrs
            if (a["@width"],a["@height"])!=dims[sid]:raise ValueError("F12D_SOURCE_DIMENSIONS")
        def axis_size(sid,d):
            if sid in dims: w,h=dims[sid]
            else:
                a=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid),"F12D_NEIGHBOR").attrs
                w,h=a["@width"],a["@height"]
            return w if d in ("N","S") else h
        for src,dst in ((219,218),(218,214)):
            choices=[r for row in rows for r in ends(row) if r[0]==src and r[3]==dst]
            d={"source_pair":[src,dst],"source_candidates":[list(r) for r in choices]}
            details.append(d)
            if len(choices)!=1:
                d["reason"]="missing_or_ambiguous_original_connection";continue
            a,da,oa,b,db,ob=choices[0]
            if conn.OPPOSITE.get(da)!=db:
                d["reason"]="non_opposite_source_sides";continue
            target=(mapping[p.SOURCES[a][0]],da,oa,mapping[p.SOURCES[b][0]],db,ob)
            if target in original or ends(target)[1] in original:
                d["reason"]="already_preserved";continue
            if any((m,side) in {(target[0],da),(target[3],db)} for r in original+records for m,side,*_ in ends(r)):
                d["reason"]="existing_target_side_in_use";continue
            competing=[];overlap=False
            for u,du,ou,v,dv,ov in ends(choices[0]):
                lo=max(0,ou-ov);hi=min(axis_size(u,du)-1,ou-ov+axis_size(v,dv)-1)
                for row in rows:
                    for rr in ends(row):
                        x,dx,ox,y,dy,oy=rr
                        if (x,dx)!=(u,du) or rr in ends(choices[0]):continue
                        l=max(0,ox-oy);h=min(axis_size(x,dx)-1,ox-oy+axis_size(y,dy)-1)
                        clash=max(lo,l)<=min(hi,h)
                        competing.append({"source_id":x,"neighbor":y,"interval":[l,h],"overlap":clash})
                        overlap|=clash
            d["competing_intervals"]=competing
            if overlap:
                d["reason"]="source_side_overlap";continue
            lanes=[];local_lanes=[];source_lanes=[];qa_lanes=[];mismatches=[];axis_rows=[]
            for n in aligned_axes(da,oa,dims[a],db,ob,dims[b]):
                x=point(n,da,oa,dims[a]);y=point(n,db,ob,dims[b])
                sa=gates.cell_shape(source_worlds[a],source_tiles,x)
                sb=gates.cell_shape(source_worlds[b],source_tiles,y)
                qa=gates.cell_shape(worlds[a],tiles,x)
                qb=gates.cell_shape(worlds[b],tiles,y)
                busy_a=x in occupied[a];busy_b=y in occupied[b]
                if sa["ordinary_walkable"] and sb["ordinary_walkable"]:source_lanes.append(n)
                if qa["ordinary_walkable"] and qb["ordinary_walkable"]:qa_lanes.append(n)
                if sa!=qa or sb!=qb:mismatches.append(n)
                allowed=lane_allowed(sa,sb,qa,qb,busy_a,busy_b)
                if allowed:
                    lanes.append(n)
                    if x in reached[a] and y in reached[b]:local_lanes.append(n)
                axis_rows.append({"axis":n,"a":list(x),"b":list(y),
                    "source_a":sa,"source_b":sb,"qa_a":qa,"qa_b":qb,
                    "occupied_a":busy_a,"occupied_b":busy_b,
                    "a_from_local_spawn":x in reached[a],"b_from_local_spawn":y in reached[b],
                    "eligible":allowed})
            d["aligned_axis_count"]=len(axis_rows)
            d["source_walkable_lanes"]=source_lanes
            d["qa_walkable_lanes"]=qa_lanes
            d["source_qa_mismatch_axes"]=mismatches
            d["local_spawn_shared_lanes"]=local_lanes
            d["shared_walkable_lanes"]=lanes
            d["axis_evidence"]=axis_rows
            # Local spawn components are diagnostic, not a mandatory seed on
            # both sides. The complete ordered chase proves actual reachability
            # from Pastoria before any candidate connection can be installed.
            if not lanes:
                d["reason"]=("source_has_no_ordinary_lane" if not source_lanes else
                    "source_qa_remap_mismatch_or_occupied" if mismatches or qa_lanes else
                    "no_shared_walkable_source_lane");continue
            records.append(target);d["reason"]="candidate_verified";d["record"]=list(target)
    out=dict(blobs)
    if records:
        out["Data/map_connections.dat"]=conn.serialize(compiled+[encode(r) for r in records])
        out["PBS/map_connections.txt"]=blobs["PBS/map_connections.txt"]+("\n# F12D verified original candidate seams\n"+"\n".join(",".join(map(str,r)) for r in records)+"\n").encode("ascii")
    if pv.parse_connections(out["PBS/map_connections.txt"])!=original+records:
        raise ValueError("F12D_PRIOR_CONNECTIONS_CHANGED")
    if tp.build(out,old,components,root)!=entries:
        raise ValueError("F12D_QA_TELEPORT_CHANGED")
    return out,{"status":"F12D_SOURCE_SEAMS_AUDITED","baseline_preserved":True,
        "prior_connection_count":len(original),"candidate_seams":len(records),"pairs":details,
        "native_verified":False,"new_portals":0}
