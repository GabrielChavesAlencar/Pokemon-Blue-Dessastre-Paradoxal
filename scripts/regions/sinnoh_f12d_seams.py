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
    reached={}
    for sid,w in worlds.items():
        sym=p.SOURCES[sid][0]
        busy={(e.attrs["@x"],e.attrs["@y"]) for e in w.attrs["@events"].values()}
        reached[sid]=gates.directional_component(set(masks[sid])-busy,arrivals[sym],masks[sid])
    records=[];details=[]
    with pv.verified_archive(path,"maps") as z:
        rows=pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt"))
        for sid,(_,expected) in p.SOURCES.items():
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError("F12D_SOURCE_HASH")
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
            common=pv.edge_axis(reached[a],dims[a],da,oa)&pv.edge_axis(reached[b],dims[b],db,ob)
            lanes=[]
            for n in sorted(common):
                x=point(n,da,oa,dims[a]);y=point(n,db,ob,dims[b])
                if not masks[a][x]&gates.EDGE_BITS[da] and not masks[b][y]&gates.EDGE_BITS[db]:
                    lanes.append(n)
            d["shared_walkable_lanes"]=lanes
            if not lanes:
                d["reason"]="no_shared_walkable_source_lane";continue
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
