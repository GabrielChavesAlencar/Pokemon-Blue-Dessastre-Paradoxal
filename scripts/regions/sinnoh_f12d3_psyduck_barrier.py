"""Authorial Psyduck cut witness, not installed.
Checks the unidentified source-116 coordinates as a hypothesis, never treats
their identity as original. Requires a separately proved linked candidate.
"""
import sinnoh_f12d_pastoria_preview as chase
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10b_trainers as trainers
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as tp
from build_johto_events import EVENT_CLASSES,ruby,event_page

SOURCE_GROUP=((12,7),(13,7),(14,7),(15,7))

def cut_witness(open_cells,blocked_cells,prior_cells,barrier,mid):
    # A real cut must remove traversable ground beyond the four occupied cells.
    # It must not sever already available progression or other maps.
    removed=open_cells-blocked_cells
    lost=removed-barrier
    return (barrier<=open_cells and not barrier&blocked_cells and
        bool(lost) and prior_cells<=blocked_cells and
        blocked_cells<=open_cells and all(p[0]==mid for p in lost))

def inspect(baseline,linked,mapping,components,chase_report,root):
    chase.validate(baseline,mapping);chase.validate(linked,mapping)
    before=chase.digest(baseline);linked_before=chase.digest(linked)
    def blocked(reason,**extra):
        return {"status":"F12D3_PSYDUCK_BARRIER_BLOCKED","reason":reason,
            "new_events":0,"installed":False,"native_verified":False,**extra}
    if not chase_report.get("runtime_install_enabled"):
        return blocked("requires_complete_chase_fixture")
    if set(linked)!=set(baseline) or any(linked[k]!=v for k,v in baseline.items()
            if k not in ("PBS/map_connections.txt","Data/map_connections.dat")):
        return blocked("requires_connection_only_candidate")
    rows=pv.parse_connections(linked["PBS/map_connections.txt"])
    prior=pv.parse_connections(baseline["PBS/map_connections.txt"])
    if rows[:len(prior)]!=prior:
        return blocked("prior_connections_changed")
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    origin=chase_report["placements"][-1]
    def graph(blobs):
        return gates.access_graph(blobs,old,components,root,
            seed_cells=[(origin["map_id"],*origin["stand"])],directional=True,strict_movement=True)
    _,_,i0,_,r0,_=graph(baseline)
    worlds,tiles,idx,_,reached,_=graph(linked)
    a=mapping["SINNOH_ROUTE_210"];mid=mapping["SINNOH_ROUTE_210_SEGMENT_2"]
    prior_cells=trainers.reached_cells(i0,r0);open_cells=trainers.reached_cells(idx,reached)
    if not all(any(p[0]==m for p in open_cells) for m in (a,mid)):
        return blocked("route210_not_linked")
    barrier={(mid,*xy) for xy in SOURCE_GROUP}
    if not barrier<=open_cells:
        return blocked("candidate_cells_not_reachable")
    world=worlds[mid];events=world.attrs["@events"]
    protected={tuple(row[3]) for row in tp.build(linked,old,components,root) if row[3]}
    for src in worlds.values():
        for event in src.attrs["@events"].values():
            trans,_=conn.classify_transfer(event)
            if trans:
                _,_,dst,x,y,_,_=trans
                protected.add((dst,x,y))
    if barrier&protected or any(x in (0,world.attrs["@width"]-1) or y in (0,world.attrs["@height"]-1) for x,y in SOURCE_GROUP):
        return blocked("protected_landing_or_edge")
    if any(not gates.cell_shape(world,tiles,xy)["ordinary_walkable"] for xy in SOURCE_GROUP):
        return blocked("nonordinary_cell")
    rel="Data/Map%03d.rxdata"%mid
    trial=dict(linked)
    # The inert events are only occupancy witnesses in a temporary copy.
    start=max(max(events,default=0)+1,3001)
    for i,(x,y) in enumerate(SOURCE_GROUP):
        eid=start+i
        events[eid]=ruby("RPG::Event",id=eid,name=b"SN_F12D3_CUT_WITNESS",
            x=x,y=y,pages=[event_page(script="nil",sprite="")])
    trial[rel]=conn.serialize(world,EVENT_CLASSES)
    _,_,cut_idx,_,cut_reach,_=graph(trial)
    blocked_cells=trainers.reached_cells(cut_idx,cut_reach)
    access=sorted({(mid,*q) for xy in SOURCE_GROUP for q in tp.neighbours(*xy)}&blocked_cells)
    lost=open_cells-blocked_cells-barrier
    if before!=chase.digest(baseline) or linked_before!=chase.digest(linked):
        raise ValueError("F12D3_BARRIER_INPUT_MUTATED")
    if not access or protected&lost or not cut_witness(open_cells,blocked_cells,prior_cells,barrier,mid):
        return blocked("no_safe_cut_or_bypass_exists",lost_cells=len(lost),reachable_interactions=[list(p) for p in access])
    return {"status":"F12D3_PSYDUCK_AUTHORED_CUT_WITNESS","source_identity_proven":False,
        "map_id":mid,"positions":[list(p) for p in SOURCE_GROUP],
        "interaction_stands":[list(p[1:]) for p in access],
        "newly_blocked_cells":len(lost),"witness_beyond":list(min(lost)[1:]),
        "restored_cells_after_removal":len(open_cells-blocked_cells),
        "new_events":0,"installed":False,"native_verified":False}
