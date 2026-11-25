"""Authorial four-Psyduck exit cut investigation; never loaded by installer.
Requires an independently verified source seam to Celestic Town.
Direct conflicting alignment is diagnostic only, never activation evidence.
"""
from collections import deque
import sinnoh_f12d_pastoria_preview as chase
import sinnoh_f12d_seams as seams
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10b_trainers as trainers
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as tp
import sinnoh_f12d3_route210_recovery as recovery
import sinnoh_f12d3_gated_alignment as gated
from sinnoh_f12d3_alternate_route212 import reserved
from build_johto_events import EVENT_CLASSES,ruby,event_page

EXIT=(116,"W",0,77,"E",5)
LIMIT=12

def local_reach(cells,seeds):
    seen=set(seeds)&cells;todo=list(seen)
    while todo:
        for q in tp.neighbours(*todo.pop()):
            if q in cells and q not in seen:seen.add(q);todo.append(q)
    return seen

def cuts(cells,ingress,exit_cells,eligible):
    """Rank contiguous rows of four; local prefilter only, global proof required."""
    if not ingress or not exit_cells or not exit_cells<=local_reach(cells,ingress):
        return []
    result=[]
    for x,y in sorted(eligible):
        for dx,dy in ((1,0),(0,1)):
            line={(x+i*dx,y+i*dy) for i in range(4)}
            if not line<=eligible:continue
            reached=local_reach(cells-line,ingress)
            if reached&exit_cells:continue
            stands={q for pos in line for q in tp.neighbours(*pos)}&reached
            if not stands:continue
            result.append((len(cells-reached-line),tuple(sorted(line))))
    return sorted(result,key=lambda p:(p[0],p[1]))

def minimum_vertex_cut(cells,ingress,exit_cells,eligible):
    """Exact vertex-capacity cut up to four removable dry event positions.
    A fifth augmenting path proves that four blocking events are insufficient.
    No terrain or existing events are changed by this search."""
    source=("source",);sink=("sink",);cap={};adj={}
    def edge(a,b,n):
        cap[a,b]=cap.get((a,b),0)+n;cap.setdefault((b,a),0)
        adj.setdefault(a,set()).add(b);adj.setdefault(b,set()).add(a)
    eligible=set(eligible)-set(ingress)-set(exit_cells)
    for x,y in sorted(cells):
        p=(x,y);a=(0,x,y);b=(1,x,y)
        edge(a,b,1 if p in eligible else 5)
        if p in ingress:edge(source,a,5)
        if p in exit_cells:edge(b,sink,5)
        for u,v in tp.neighbours(x,y):
            if (u,v) in cells:edge(b,(0,u,v),5)
    flow=0
    while flow<5:
        parent={source:None};queue=deque([source])
        while queue and sink not in parent:
            a=queue.popleft()
            for b in sorted(adj.get(a,()),key=str):
                if b not in parent and cap[a,b]>0:parent[b]=a;queue.append(b)
        if sink not in parent:
            cut={p for p in eligible if (0,*p) in parent and (1,*p) not in parent}
            if len(cut)!=flow or not cut or local_reach(cells-cut,ingress)&exit_cells:return None
            return cut
        p=sink;n=5-flow
        while parent[p] is not None:
            a=parent[p];n=min(n,cap[a,p]);p=a
        p=sink
        while parent[p] is not None:
            a=parent[p];cap[a,p]-=n;cap[p,a]+=n;p=a
        flow+=n
    return None

def integrated_cuts(cells,ingress,exit_cells,eligible):
    """Include non-collinear cuts; add nearby eligible companions if needed.
    Every candidate still has to pass the full serialized global graph proof."""
    found={line:score for score,line in cuts(cells,ingress,exit_cells,eligible)}
    cut=minimum_vertex_cut(cells,ingress,exit_cells,eligible)
    if cut:
        for excluded in [set()]+[{p} for p in sorted(cut)]:
            line=minimum_vertex_cut(cells,ingress,exit_cells,set(eligible)-excluded)
            if not line:continue
            line=set(line)
            while len(line)<4:
                nearby={q for p in line for q in tp.neighbours(*p) if q in eligible and q not in line}
                if not nearby:break
                line.add(min(nearby))
            if len(line)!=4:continue
            reached=local_reach(cells-line,ingress)
            if reached&exit_cells or not any(q in reached for p in line for q in tp.neighbours(*p)):continue
            found[tuple(sorted(line))]=len(cells-reached-line)
    return sorted((score,line) for line,score in found.items())

def inspect(baseline,direct,mapping,components,chase_report,expanded,alternative,root,recovered_alternative=None,source_protected=(),rock_cells=(),prepared=None):
    chase.validate(baseline,mapping);before=chase.digest(baseline)
    direct_hash=chase.digest(direct)
    if expanded.get("input_hashes")!=before or not chase_report.get("runtime_install_enabled"):
        raise ValueError("F12D3_CELESTIC_STALE")
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    origin=chase_report["placements"][-1]
    def graph(data):
        return gates.access_graph(data,old,components,root,seed_cells=[(origin["map_id"],*origin["stand"])],
            directional=True,strict_movement=True,rock_cells=rock_cells)
    def append(data,rows):
        out=dict(data);current=pv.parse_connections(data["PBS/map_connections.txt"])
        if conn.read_marshal(data["Data/map_connections.dat"],"F12D3_CUT_COMPILED")!=[recovery.encode(r) for r in current]:
            raise ValueError("F12D3_CUT_COMPILED_MISMATCH")
        out["PBS/map_connections.txt"]=data["PBS/map_connections.txt"]+("\n# F12D3 cut witness only\n"+"\n".join(",".join(map(str,r)) for r in rows)+"\n").encode("ascii")
        out["Data/map_connections.dat"]=conn.serialize([recovery.encode(r) for r in current+rows])
        return out
    _,_,ib,_,rb,_=graph(baseline)
    prior=trainers.reached_cells(ib,rb)
    mid=mapping["SINNOH_ROUTE_210_SEGMENT_2"];town=mapping["SINNOH_CELESTIC_TOWN"]
    result={"status":"F12D3_CELESTIC_CUT_EVIDENCE_ONLY","cases":[],"new_events":0,"new_portals":0,
            "installed":False,"native_verified":False,"activation_allowed":False}
    e=next((r for r in expanded["edge_candidates"] if tuple(r["source_record"])==EXIT),None)
    if not e or e["source_side_conflict"] or e["installed"] or not e["matching_walkable_axes"]:
        result["reason"]="unverified_original_celestic_exit";return result
    exit_record=tuple(e["qa_record"])
    if (exit_record[0],exit_record[3])!=(mid,town):raise ValueError("F12D3_CELESTIC_MAPIDS")
    variants=[]
    if alternative.get("witness") and alternative["witness"].get("fixture_passed"):
        rows=[tuple(r) for r in alternative["fixed_records"]]+[tuple(alternative["witness"]["qa_record"])]
        variants.append(("alternative",append(baseline,rows)))
    if recovered_alternative is not None:variants.append(("dry_network_candidate",recovered_alternative))
    if direct!=baseline:variants.append(("direct_conflicting_diagnostic",direct))
    if not variants:result["reason"]="no_linked_fixture";return result
    for label,linked in variants:
        case={"variant":label,"status":"BLOCKED","tested":0};result["cases"].append(case)
        worlds,tiles,idx,_,rr,_=graph(linked);opened=trainers.reached_cells(idx,rr)
        dims={m:(w.attrs["@width"],w.attrs["@height"]) for m,w in worlds.items()}
        records=pv.parse_connections(linked["PBS/map_connections.txt"])
        if reserved(exit_record,records,dims):
            case["reason"]="existing_interval_conflict";continue
        lanes=gated.all_lanes(exit_record,idx,dims)
        if [n for n,x,y in lanes]!=e["matching_walkable_axes"]:
            case["reason"]="exit_lanes_not_verified";continue
        targets={(mid,*x) for _,x,y in lanes}
        case["exit_axes"]=[n for n,x,y in lanes]
        case["exit_components"]=[idx[mid][x] for _,x,y in lanes]
        case["reachable_components"]=sorted(i for m,i in rr if m==mid)
        case["exit_cells_reachable_before_seam"]=sum(x in opened for x in targets)
        if not targets<=opened:
            case["reason"]="celestic_exit_not_reachable";continue
        if any(p[0]==town for p in prior):
            case["reason"]="celestic_already_reachable_in_baseline";continue
        with_exit=append(linked,[exit_record])
        worlds,tiles,idx,_,rr,_=graph(with_exit);opened=trainers.reached_cells(idx,rr)
        if not prior<=opened or not any(p[0]==town for p in opened):
            case["reason"]="celestic_open_graph_failed";continue
        if tp.build(with_exit,old,components,root)!=tp.build(baseline,old,components,root):
            case["reason"]="qa_entries_changed";continue
        world=worlds[mid];w,h=dims[mid]
        protected={tuple(r[3]) for r in tp.build(with_exit,old,components,root) if r[3]}
        for src in worlds.values():
            for event in src.attrs["@events"].values():
                trans,_=conn.classify_transfer(event)
                if trans:
                    _,_,dst,x,y,_,_=trans;protected.add((dst,x,y))
        cells={(x,y) for m,x,y in opened if m==mid}
        exit_xy={(x,y) for _,x,y in targets}
        ingress=set()
        for record in records:
            for end in seams.ends(record):
                if end[0]!=mid:continue
                for _,x,y in gated.all_lanes(end,idx,dims):
                    if x in cells and (end[3],*y) in opened:ingress.add(x)
        ingress|={(x,y) for m,x,y in protected&opened if m==mid and (x,y) not in exit_xy}
        if origin["map_id"]==mid:ingress.add(tuple(origin["stand"]))
        # Source-only event cells are immutable, not new entrances.
        protected.update(source_protected)
        # An ingress on the destination side is a potential bypass, not ignored.
        eligible={xy for xy in cells if 0<xy[0]<w-1 and 0<xy[1]<h-1 and
                  (mid,*xy) not in protected|prior and xy not in ingress|exit_xy and
                  gates.cell_shape(world,tiles,xy)["ordinary_walkable"]}
        ranked=integrated_cuts(cells,ingress,exit_xy,eligible) if prepared is not None else cuts(cells,ingress,exit_xy,eligible)
        case["local_candidate_count"]=len(ranked);case["ingress_cells"]=[list(x) for x in sorted(ingress)]
        rel="Data/Map%03d.rxdata"%mid
        for _,line in (ranked if prepared is not None else ranked[:LIMIT]):
            case["tested"]+=1;copy=conn.read_marshal(with_exit[rel],"F12D3_CUT_TRIAL")
            events=copy.attrs["@events"];start=max(max(events,default=0)+1,3001)
            for i,(x,y) in enumerate(line):
                eid=start+i;events[eid]=ruby("RPG::Event",id=eid,name=b"SN_F12D3_AUTHORIAL_CUT_WITNESS",
                    x=x,y=y,pages=[event_page(script="nil",sprite="")])
            trial=dict(with_exit);trial[rel]=conn.serialize(copy,EVENT_CLASSES)
            _,_,ic,_,rc,_=graph(trial);closed=trainers.reached_cells(ic,rc)
            barrier={(mid,*xy) for xy in line}
            stands={(mid,*q) for xy in line for q in tp.neighbours(*xy)}&closed
            preserve_routes={mapping[s] for s in ("SINNOH_ROUTE_210","SINNOH_ROUTE_212","SINNOH_ROUTE_212_SEGMENT_2","SINNOH_ROUTE_215") if s in mapping}
            if label=="dry_network_candidate" and any(p[0] in preserve_routes for p in opened-closed):continue
            if not (prior<=closed<=opened and not barrier&closed and not targets&closed and stands and
                    not any(p[0]==town for p in closed) and tp.build(trial,old,components,root)==tp.build(with_exit,old,components,root)):
                continue
            # Reopen from the same trial by restoring only the four-witness map.
            restored=dict(trial);restored[rel]=with_exit[rel]
            _,_,io,_,ro,_=graph(restored)
            if trainers.reached_cells(io,ro)!=opened or chase.digest(restored)!=chase.digest(with_exit):
                raise ValueError("F12D3_CUT_REOPEN_MISMATCH")
            case.update(status="AUTHORIAL_EXIT_CUT_FIXTURE_ONLY",positions=[list(x) for x in line],
                interaction_stands=[list(p[1:]) for p in sorted(stands)],open_cells=len(opened),
                closed_cells=len(closed),restored_cells=len(opened),source_identity_proven=False)
            if prepared is not None:prepared.update(open_maps=with_exit,cut_positions=tuple(line),cut_map_id=mid,exit_record=exit_record,exit_cells=tuple(sorted(exit_xy)),interaction_stands=tuple(sorted(p[1:] for p in stands)))
            break
        if case["status"]=="BLOCKED":case["reason"]="no_verified_four_cell_cut"
    if chase.digest(baseline)!=before or chase.digest(direct)!=direct_hash:
        raise ValueError("F12D3_CELESTIC_INPUT_MUTATED")
    return result
