"""Append Windworks for QA exploration only if exact source seam is walkable.
No donor event, script, item, battle, story flag or collision alteration.
"""
from pathlib import Path
import hashlib
from collections import deque
import sinnoh_f12b_windworks as wind
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as tp

ROOT=Path(__file__).resolve().parents[2]
SYMBOL=wind.SYMBOL
ROUTE="SINNOH_ROUTE_205_SEGMENT_2"
ALL=wind.gym.GYM_SETS[7]|{SYMBOL}
SOURCE=(111,"W",0,94,"E",57)
OTHER=(111,"W",252,199,"E",0)
OTHER_HASH="e01834a4260b2ba490e45bde2f3145cd3818081652ec239d978767f71c4ab759"

def component(points,seed):
    if seed not in points:return set()
    found={seed};todo=deque([seed])
    while todo:
        for p in tp.neighbours(*todo.popleft()):
            if p in points and p not in found:found.add(p);todo.append(p)
    return found

def shared_edge(a,b,aw,bw):
    return sorted(pv.edge_axis(a,aw,"W",0)&pv.edge_axis(b,bw,"E",57))

def append(blobs,mapping,components,path,occupied,root=ROOT):
    def blocked(reason,**details):
        return blobs,mapping,components,{"status":"WINDWORKS_ACCESS_BLOCKED","reason":reason,"runtime_install_enabled":False,
            "new_maps":0,"new_portals":0,"new_seams":0,"native_bindings":0,"items_granted":0,"native_verified":False,**details}
    if set(mapping)!=wind.gym.GYM_SETS[7] or len(mapping)!=139:return blocked("requires_full_f11h")
    before={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}
    with pv.verified_archive(path,"maps") as z:
        rows=pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt"))
        relevant=[r for r in rows if 111 in (r[0],r[3])]
        if len(relevant)!=2 or set(relevant)!={SOURCE,OTHER}:return blocked("source_seam_changed")
        # The second west-side link has a disjoint coordinate interval:
        # its Windworks axis is [-252,-224], and Route 220 is [0,34].
        other=pv.member(z,pv.MAP_ROOT+"Data/Map199.rxdata")
        if hashlib.sha256(other).hexdigest()!=OTHER_HASH:return blocked("alternate_source_hash_changed")
        other_map=conn.read_marshal(other,"F12B4_OTHER").attrs
        if (other_map["@width"],other_map["@height"])!=(64,35):return blocked("alternate_source_dimensions")
        if set(range(-252,29-252))&set(range(other_map["@height"])):return blocked("alternate_source_overlap")
        competing=[]
        for r in rows:
            if r==SOURCE:continue
            if (r[0],r[1])==(94,"E"):local_off,other_id,other_dir,other_off=r[2],r[3],r[4],r[5]
            elif (r[3],r[4])==(94,"E"):local_off,other_id,other_dir,other_off=r[5],r[0],r[1],r[2]
            else:continue
            other_raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%other_id)
            a=conn.read_marshal(other_raw,"F12B5_COMPETING_EDGE").attrs
            size=a["@height"] if other_dir in ("E","W") else a["@width"]
            competing.append({"source_id":other_id,"local_y_interval":[local_off-other_off,local_off-other_off+size-1],"opposite":other_dir=="W"})
        rr=pv.member(z,pv.MAP_ROOT+"Data/Map094.rxdata")
        if hashlib.sha256(rr).hexdigest()!="0624b353d4b1e0817b8b735714e314aa778a234c3dfe011b2ef60473543d9b2a":return blocked("route_source_hash_changed")
    infos=conn.read_marshal(blobs["Data/MapInfos.rxdata"],"F12B4_INFOS")
    mid=wind.gym.allocate(mapping,occupied,infos)
    if mid is None:return blocked("no_free_map_id")
    row=wind.source_row(root)
    expanded={**mapping,SYMBOL:mid}
    out,ids,comps,geometry=wind.city.append_exteriors(blobs,mapping,components,path,expanded,[row],"F12B")
    old=tp.build(blobs,mapping,components,root);new=tp.build(out,ids,comps,root)
    if [r for r in old if r[0]!=SYMBOL]!=[r for r in new if r[0]!=SYMBOL]:raise ValueError("F12B4_PRIOR_TELEPORT_CHANGED")
    arrivals={r[0]:tuple(r[3][1:]) for r in new if r[3]}
    tiles=conn.read_marshal(out["Data/Tilesets.rxdata"],"F12B4_TILES")
    worlds={s:conn.read_marshal(out["Data/Map%03d.rxdata"%ids[s]],"F12B4_MAP") for s in (SYMBOL,ROUTE)}
    if (worlds[ROUTE].attrs["@width"],worlds[ROUTE].attrs["@height"])!=(32,88):return blocked("route_geometry_changed")
    # Require ordinary ground, event-free approach and an ordinary-ground path
    # from each existing QA arrival. Never open walls or change terrain flags.
    reach={}
    for s,w in worlds.items():
        points=conn.safe_cells(w,tiles,s)&comps[s]
        points-={(e.attrs["@x"],e.attrs["@y"]) for e in w.attrs["@events"].values()}
        reach[s]=component(points,arrivals[s])
    lanes=shared_edge(reach[SYMBOL],reach[ROUTE],(33,29),(32,88))
    detail={"windworks_reachable_cells":len(reach[SYMBOL]),"route_reachable_cells":len(reach[ROUTE]),
        "windworks_edge":sorted(pv.edge_axis(reach[SYMBOL],(33,29),"W",0)),
        "route_edge":sorted(pv.edge_axis(reach[ROUTE],(32,88),"E",57)),
        "preview_map_id":mid,"safe_spawn":geometry[SYMBOL]["safe_spawn"]}
    detail["competing_source_intervals"]=competing
    detail["shared_lanes"]=lanes
    conflict=any(not c["opposite"] or max(57,c["local_y_interval"][0])<=min(85,c["local_y_interval"][1]) for c in competing)
    seam_reason="source_edge_overlap" if conflict else ("no_shared_ordinary_walkable_seam" if not lanes else None)
    original=pv.parse_connections(blobs["PBS/map_connections.txt"])
    compiled=conn.read_marshal(blobs["Data/map_connections.dat"],"F12B4_CONNECTIONS")
    expected=[[r[0],r[1].encode("ascii"),r[2],r[3],r[4].encode("ascii"),r[5]] for r in original]
    if compiled!=expected:return blocked("compiled_pbs_connections_mismatch",**detail)
    if any(m==mid for r in original for m in (r[0],r[3])):return blocked("existing_map_id_collision",**detail)
    if any((m,d)==(ids[ROUTE],"E") for r in original for m,d in ((r[0],r[1]),(r[3],r[4]))):
        seam_reason="existing_route_side_in_use"
    record=None
    if seam_reason is None:
        record=[mid,"W",0,ids[ROUTE],"E",57]
        out["Data/map_connections.dat"]=conn.serialize(compiled+[[mid,b"W",0,ids[ROUTE],b"E",57]])
        out["PBS/map_connections.txt"]=blobs["PBS/map_connections.txt"]+("\n# F12B5 original Windworks QA seam\n"+",".join(map(str,record))+"\n").encode("ascii")
    # The existing private QA teleport is bidirectional by design. A verified
    # isolated geometry may be explored without claiming a natural connection.
    # No story or event completion is triggered by this fallback.
    mutable={"Data/MapInfos.rxdata","Data/Tilesets.rxdata","PBS/map_metadata.txt","Data/map_connections.dat","PBS/map_connections.txt"}
    if any(out.get(k)!=v for k,v in blobs.items() if k not in mutable):raise ValueError("F12B4_BASELINE_CHANGED")
    if before!={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}:raise ValueError("F12B4_INPUT_MUTATED")
    return out,ids,comps,{"status":"WINDWORKS_EXPLORATION_PREPARED" if record else "WINDWORKS_QA_TELEPORT_ONLY",
        "runtime_install_enabled":True,"new_maps":1,"new_seams":int(record is not None),"new_portals":0,
        "native_bindings":0,"items_granted":0,"source_seam":list(SOURCE),"record":record,
        "seam_blocker":seam_reason,"baseline_preserved":True,"native_verified":False,"story_enabled":False,**detail}
