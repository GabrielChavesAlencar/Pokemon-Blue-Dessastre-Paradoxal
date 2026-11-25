"""F12D3 dry-ground recovery fixtures, not installer code.
Diagnose the disconnected Celestic exit and reserved Route212/215 boundaries.
No source script execution, native claims, or persistent map/save writes.
"""
import hashlib
import heapq
import struct
from collections import Counter
import sinnoh_f12d_pastoria_preview as chase
import sinnoh_f12d_corridor as corridor
import sinnoh_f12d_seams as seams
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10b_trainers as trainers
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as tp
import sinnoh_f12d3_secretpotion_audit as audit
import sinnoh_f12d3_gated_alignment as gated
import sinnoh_f12d3_route210_recovery as recovery
import sinnoh_f12d3_alternate_route212 as alt
import sinnoh_f12d3_celestic_cut as cut
from build_johto_events import EVENT_CLASSES

BUDGET=32

def path_search(shapes,source,seeds,occupied,protected,size,edge_edits=()):
    """Multi-source lexicographic shortest paths, minimum edits then steps.
    Existing ordinary landings remain walkable; all protected cells immutable.
    No water, ledge, partial mask, mismatch or unapproved perimeter edit.
    """
    w,h=size;allowed=set(edge_edits);dist={};parents={};queue=[]
    for xy in sorted(set(seeds)-occupied):
        if xy in shapes and corridor.ordinary(shapes[xy]) and shapes[xy]==source[xy]:
            dist[xy]=(0,0);heapq.heappush(queue,(0,0,xy))
    while queue:
        n,d,xy=heapq.heappop(queue)
        if dist[xy]!=(n,d):continue
        for q in tp.neighbours(*xy):
            if q not in shapes or q in occupied or shapes[q]!=source[q]:continue
            if corridor.ordinary(shapes[q]):cost=0
            elif (q not in protected and corridor.editable(source[q],shapes[q]) and
                  (q in allowed or (0<q[0]<w-1 and 0<q[1]<h-1))):cost=1
            else:continue
            score=(n+cost,d+1)
            if score>=dist.get(q,(10**9,10**9)):continue
            dist[q]=score;parents[q]=xy;heapq.heappush(queue,(*score,q))
    return dist,parents

def witness(q,parents,shapes):
    path=[q]
    while path[-1] in parents:path.append(parents[path[-1]])
    path.reverse()
    return path,[p for p in path if not corridor.ordinary(shapes[p])]

def inspect(baseline,direct,mapping,components,cr,expanded,alternative,source_path,root):
    chase.validate(baseline,mapping);before=chase.digest(baseline);dh=chase.digest(direct)
    if expanded.get("input_hashes")!=before or not cr.get("runtime_install_enabled"):
        raise ValueError("F12D3_DRY_RECOVERY_STALE")
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    origin=cr["placements"][-1]
    def graph(data):
        return gates.access_graph(data,old,components,root,seed_cells=[(origin["map_id"],*origin["stand"])],
            directional=True,strict_movement=True)
    result={"status":"F12D3_DRY_RECOVERY_EVIDENCE_ONLY","installed":False,"native_verified":False,
            "activation_allowed":False,"new_portals":0,"new_events":0,"new_maps":0,"changed_cells_installed":0,
            "alternate_frontier":[],"celestic":{}}
    base_worlds,tiles,ib,_,rb,_=graph(baseline);prior=trainers.reached_cells(ib,rb)
    dims={m:(w.attrs["@width"],w.attrs["@height"]) for m,w in base_worlds.items()}
    mid=mapping[audit.SOURCES[116][0]]
    original=pv.parse_connections(baseline["PBS/map_connections.txt"])
    protected={m:set() for m in dims}
    occupied={m:{(e.attrs["@x"],e.attrs["@y"]) for e in w.attrs["@events"].values()} for m,w in base_worlds.items()}
    for row in tp.build(baseline,old,components,root):
        if row[3]:
            m,x,y=row[3];protected[m].add((x,y))
    for w in base_worlds.values():
        for event in w.attrs["@events"].values():
            transfer,_=conn.classify_transfer(event)
            if transfer:
                _,_,m,x,y,_,_=transfer
                if m in protected:protected[m].add((x,y))
    catalog,_,_=conn.graph(root)
    ids=(116,222,223,126);source_dims={};qa={};src={};bound={}
    with pv.verified_archive(source_path,"maps") as z:
        rows=pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt"))
        st=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D3_DRY_SOURCE_TILES")
        relevant=[row for row in rows if row[0] in ids or row[3] in ids]
        needed=set(ids)|{i for row in relevant for i in (row[0],row[3])}
        for sid in sorted(needed):
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            w=conn.read_marshal(raw,"F12D3_DRY_SOURCE");source_dims[sid]=(w.attrs["@width"],w.attrs["@height"])
            if sid not in ids:continue
            rec=catalog[sid]
            if hashlib.sha256(raw).hexdigest()!=rec["sha256"]:raise ValueError("F12D3_DRY_SOURCE_HASH")
            m=mapping[rec["symbol"]];bound[sid]=m
            if source_dims[sid]!=dims[m]:raise ValueError("F12D3_DRY_DIMENSIONS")
            src[sid]=corridor.grid(w,st)[1];qa[sid]=corridor.grid(base_worlds[m],tiles)
            protected[m].update((e.attrs["@x"],e.attrs["@y"]) for e in w.attrs["@events"].values())
            protected[m].update(occupied[m])
            protected[m].update(q for xy in tuple(protected[m]) for q in tp.neighbours(*xy)
                if q in qa[sid][1] and not corridor.ordinary(qa[sid][1][q]))
        # Count all geometrically free intervals, even where no dry crossing currently exists.
        # This is not a walk witness; it tells whether interior reconstruction could help.
        for sid in (222,223):
            for d in ("N","S","E","W"):
                opposite=conn.OPPOSITE[d];sa=source_dims[sid];sb=source_dims[126]
                na=sa[0] if d in ("N","S") else sa[1];nb=sb[0] if d in ("N","S") else sb[1]
                counts=Counter();examples=[]
                for delta in range(1-nb,na):
                    rec=(sid,d,max(delta,0),126,opposite,max(-delta,0))
                    if alt.reserved(rec,relevant,source_dims) or alt.reserved((bound[sid],d,rec[2],bound[126],opposite,rec[5]),original,dims):
                        counts["reserved"]+=1;continue
                    counts["free_interval"]+=1
                    for n in seams.aligned_axes(d,rec[2],sa,opposite,rec[5],sb):
                        x=seams.point(n,d,rec[2],sa);y=seams.point(n,opposite,rec[5],sb)
                        def usable(i,q):
                            m=bound[i];shape=qa[i][1][q];s=src[i][q]
                            return q not in occupied[m] and s==shape and (corridor.ordinary(shape) or
                                (q not in protected[m] and corridor.editable(s,shape)))
                        if usable(sid,x) and usable(126,y):
                            counts["potential_dry_pairs"]+=1
                            if len(examples)<8:examples.append({"record":list(rec),"axis":n,"positions":[list(x),list(y)]})
                result["alternate_frontier"].append({"source_pair":[sid,126],"side":d,"counts":dict(counts),"examples":examples})
    if direct==baseline:
        result["celestic"]={"reason":"no_direct_diagnostic_fixture"};return result
    worlds,_,idx,groups,reached,_=graph(direct)
    route_cells={xy for xy,label in idx[mid].items() if (mid,label) in reached}
    e=next((x for x in expanded["edge_candidates"] if tuple(x["source_record"])==cut.EXIT),None)
    if not e or e["source_side_conflict"] or e["installed"]:raise ValueError("F12D3_DRY_EXIT_EVIDENCE")
    exit_record=tuple(e["qa_record"]);lanes=gated.all_lanes(exit_record,idx,dims)
    if [n for n,x,y in lanes]!=e["matching_walkable_axes"]:raise ValueError("F12D3_DRY_EXIT_LANES")
    targets={x for _,x,y in lanes}
    shapes=qa[116][1];stacks=qa[116][0]
    d,p=path_search(shapes,src[116],route_cells,occupied[mid],protected[mid],dims[mid])
    report={"variant":"direct_conflicting_diagnostic","source_hash":audit.SOURCES[116][1],
        "qa_hash":hashlib.sha256(baseline["Data/Map%03d.rxdata"%mid]).hexdigest(),
        "entry_components":sorted(i for m,i in reached if m==mid),
        "exit_components":sorted({idx[mid][q] for q in targets}),
        "exit_costs":[{"position":list(q),"minimum_edits":d[q][0] if q in d else None} for q in sorted(targets)],
        "budget":BUDGET,"fixture_prepared":False}
    result["celestic"]=report
    possible=[q for q in targets if q in d]
    if not possible:
        report["reason"]="no_source_matched_dry_corridor"
        frontier=Counter()
        for xy in d:
            for q in tp.neighbours(*xy):
                if q not in shapes or q in d:continue
                masks,tags=shapes[q]
                reason=("occupied" if q in occupied[mid] else "source_mismatch" if shapes[q]!=src[116][q] else
                    "protected" if q in protected[mid] else "special_terrain" if any(t not in (0,2) for t in tags) else
                    "directional_mask" if any(0<m<15 for m in masks) else "perimeter_or_noneditable")
                frontier[reason]+=1
        report["frontier_edges"]=dict(frontier);return result
    target=min(possible,key=lambda q:(d[q],q));path,edits=witness(target,p,shapes)
    report.update(minimum_edits=len(edits),path=[list(q) for q in path],edit_positions=[list(q) for q in edits])
    if len(edits)>BUDGET:
        report["reason"]="dry_corridor_over_budget";return result
    floor=[q for q,s in shapes.items() if corridor.ordinary(s) and all(t==0 for t in s[1])
           and q not in protected[mid] and s==src[116][q]]
    if not floor:report["reason"]="no_matching_floor";return result
    rel="Data/Map%03d.rxdata"%mid
    world=conn.read_marshal(direct[rel],"F12D3_DRY_TRIAL");data=world.attrs["@data"];raw=data.data
    w,h=dims[mid];changed=bytearray(raw);donors=[]
    for x,y in edits:
        q=(x,y)
        if q in protected[mid] or not corridor.editable(src[116][q],shapes[q]):raise ValueError("F12D3_DRY_UNSAFE_EDIT")
        donor=min(floor,key=lambda t:(conn.distance(q,t),t[1],t[0]))
        for z,t in enumerate(stacks[donor]):struct.pack_into("<H",changed,20+2*(z*w*h+y*w+x),t)
        donors.append({"position":list(q),"floor_reference":list(donor)})
    data.data=bytes(changed);patched=conn.serialize(world,EVENT_CLASSES)
    check=conn.read_marshal(patched,"F12D3_DRY_VERIFY");_,after=corridor.grid(check,tiles)
    if {q for q in shapes if after[q]!=shapes[q]}!=set(edits) or not all(corridor.ordinary(after[q]) for q in edits):
        raise ValueError("F12D3_DRY_DELTA")
    data.data=raw;check.attrs["@data"].data=raw
    if conn.serialize(check,EVENT_CLASSES)!=conn.serialize(world,EVENT_CLASSES):
        raise ValueError("F12D3_DRY_METADATA")
    trial=dict(direct);trial[rel]=patched
    _,_,ix,_,rr,_=graph(trial);cells=trainers.reached_cells(ix,rr)
    direct_cells=trainers.reached_cells(idx,reached)
    if not prior<=direct_cells<=cells or not {(mid,*q) for q in targets}<=cells or tp.build(trial,old,components,root)!=tp.build(baseline,old,components,root):
        report["reason"]="dry_fixture_reach_or_entries_failed";return result
    report.update(fixture_prepared=True,reason=None,reachable_exit_cells=len(targets),donors=donors,
        trial_map_hash=hashlib.sha256(patched).hexdigest(),newly_reachable_cells=len(cells-direct_cells))
    # Only diagnostic: the direct Pastoria alignment still has future conflicts.
    report["cut_after_dry_fixture"]=cut.inspect(baseline,trial,mapping,components,cr,expanded,alternative,root)
    if chase.digest(baseline)!=before or chase.digest(direct)!=dh:raise ValueError("F12D3_DRY_INPUT_MUTATED")
    return result
