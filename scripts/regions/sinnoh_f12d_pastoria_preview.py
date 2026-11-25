"""F12D1/D2: pinned source audit and inert authored event preview.
No donor execution, new portals, map allocation, save writes or runtime activation.
"""
import hashlib
import sinnoh_private_visual as pv
import sinnoh_connection_expansion as conn
import sinnoh_f12b2_windworks_evidence as evidence
import sinnoh_f12c4_install as baseline
import sinnoh_f12b4_windworks_access as prior
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10b_trainers as trainers
import sinnoh_f11a_gym as gym
import sinnoh_qa_teleport as tp
from build_johto_events import EVENT_CLASSES,ruby,event_page

SOURCES={
    219:("SINNOH_PASTORIA_CITY","7aa39abbf594db53c1e95a87707132b3c7b1282a62ba91b6f0958062ca8dcd41"),
    218:("SINNOH_ROUTE_213","bb14b09bddbcd5ec96b33c897406e08579de9b61652a7a87d9d7567d81614ac3"),
    214:("SINNOH_VALOR_LAKEFRONT","01dd1e09fc9228d1ed5077a87cd79fa53234948451d06c6a732356bace5dfc32"),
}
ORDER=("PASTORIA","ROUTE_213","VALOR_BATTLE")
AREAS=tuple(v[0] for v in SOURCES.values())
TEAM=(("CROAGUNK",31),)

def validate(blobs,mapping):
    if set(mapping)!=baseline.ALL or len(mapping)!=144 or len(set(mapping.values()))!=144:
        raise ValueError("F12D_REQUIRES_144_BASELINE")
    if any("Data/Map%03d.rxdata"%m not in blobs for m in mapping.values()):
        raise ValueError("F12D_MAP_MISSING")

def digest(blobs):
    return {k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}

def audit(blobs,mapping,path):
    validate(blobs,mapping)
    before=digest(blobs); rows=[]
    with pv.verified_archive(path,"maps") as z:
        for sid,(sym,expected) in SOURCES.items():
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=expected:
                raise ValueError("F12D_SOURCE_HASH:"+str(sid))
            events=conn.read_marshal(raw,"F12D_SOURCE").attrs["@events"]
            entries=[evidence.event_evidence(e,eid) for eid,e in sorted(events.items())]
            rows.append({"source_id":sid,"qa_map_id":mapping[sym],"symbol":sym,
                "source_sha256":expected,"event_count":len(entries),"events":entries,
                "static_targets":sorted(conn.static_targets(events))})
    if before!=digest(blobs):raise ValueError("F12D_BASELINE_CHANGED")
    return {"status":"F12D1_SOURCE_AUDITED","maps":rows,"baseline_maps":144,
        "baseline_preserved":True,"native_verified":False,"source_scripts_executed":False,
        "items_granted":0,"new_maps":0,"new_portals":0,"saves_accessed":False}

def preview(blobs,mapping,components,root):
    validate(blobs,mapping)
    before=digest(blobs)
    # Galactic interiors are deliberately excluded from the QA teleport catalogue.
    old={k:v for k,v in mapping.items() if k in prior.ALL}
    if len(old)!=140:raise ValueError("F12D_TELEPORT_SCOPE")
    entries=tp.build(blobs,old,components,root)
    _,_,idx,_,reach,_=gates.access_graph(blobs,old,components,root,directional=True)
    old_cells=trainers.reached_cells(idx,reach)
    _,_,start_idx,_,start_reach,_=gates.access_graph(blobs,old,components,root,
        seed_symbols={AREAS[0]},directional=True,strict_movement=True)
    reachable_counts={sym:sum((old[sym],label) in start_reach for label in start_idx[old[sym]].values()) for sym in AREAS}
    def report(status,reason=None,placements=()):
        return {"status":status,"reason":reason,"placements":list(placements),
            "baseline_maps":144,"baseline_preserved":before==digest(blobs),
            "new_maps":0,"new_portals":0,"new_seams":0,"items_granted":0,
            "runtime_install_enabled":False,"native_verified":False,
            "source_layout":"PROJECT_AUTHORED_CONDENSED_CHASE",
            "historical_team":[list(row) for row in TEAM],
            "reachable_cells_from_pastoria":reachable_counts}
    out=dict(blobs); locations=[]; positions=set()
    for key,sym in zip(ORDER,AREAS):
        mid=old[sym]; rel="Data/Map%03d.rxdata"%mid
        accepted=False
        for world,xy,land in gym.city_entrance(out,old,components,root,sym):
            label=start_idx[mid].get(land)
            if label is None or (mid,label) not in start_reach:continue
            ev=world.attrs["@events"]; eid=max(max(ev,default=0)+1,3001)
            ev[eid]=ruby("RPG::Event",id=eid,name=("SN_F12D_"+key).encode("ascii"),
                x=xy[0],y=xy[1],pages=[event_page(script='BlueSinnohF12D.interact("'+key+'")',
                sprite="SNQA_F12D_GRUNT")])
            trial=dict(out);trial[rel]=conn.serialize(world,EVENT_CLASSES)
            del ev[eid]
            if tp.build(trial,old,components,root)!=entries:continue
            _,_,post,_,reached,_=gates.access_graph(trial,old,components,root,directional=True)
            if not (old_cells-positions-{(mid,*xy)})<=trainers.reached_cells(post,reached):continue
            _,_,pidx,_,preach,_=gates.access_graph(trial,old,components,root,
                seed_symbols={AREAS[0]},directional=True,strict_movement=True)
            if not all((loc["map_id"],pidx[loc["map_id"]].get(tuple(loc["stand"]))) in preach for loc in locations):continue
            if (mid,pidx[mid].get(land)) not in preach:continue
            out=trial; positions.add((mid,*xy));locations.append({"id":key,"map_id":mid,
                "event_id":eid,"position":list(xy),"stand":list(land)})
            accepted=True;break
        if not accepted:return {},report("F12D2_BLOCKED","no_safe_walkable_chase_witness:"+key,locations)
    # Prove ordered travel from the actual interaction cells, without reseeding QA teleports.
    for a,b in zip(locations,locations[1:]):
        _,_,index,_,reached,_=gates.access_graph(out,old,components,root,directional=True,
            seed_cells=[(a["map_id"],*a["stand"])],strict_movement=True)
        if (b["map_id"],index[b["map_id"]].get(tuple(b["stand"]))) not in reached:
            return {},report("F12D2_BLOCKED","no_safe_walkable_chase_witness:"+b["id"],locations)
    # No map allocation or change to existing event, terrain or connection.
    changed={loc["map_id"] for loc in locations}
    for mid in mapping.values():
        rel="Data/Map%03d.rxdata"%mid
        if mid not in changed:
            if out[rel]!=blobs[rel]:raise ValueError("F12D_PRIOR_MAP_CHANGED")
            continue
        world=conn.read_marshal(out[rel],"F12D_PREVIEW")
        for loc in locations:
            if loc["map_id"]==mid:del world.attrs["@events"][loc["event_id"]]
        if conn.serialize(world,EVENT_CLASSES)!=blobs[rel]:
            raise ValueError("F12D_EXISTING_EVENT_CHANGED")
    if before!=digest(blobs):raise ValueError("F12D_BASELINE_CHANGED")
    delta={k:v for k,v in out.items() if blobs.get(k)!=v}
    return delta,report("F12D2_EVENT_PREVIEW",placements=locations)
