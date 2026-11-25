"""Canonical route recovery in private fixtures only.
Do not re-align a source record with the wrong destination (223 -> Oreburgh).
Explore the two canonical return corridors, existing native gatehouse transfers,
and exact original seams with local, source-matched dry reconstruction.
No installer, runtime gate or persistent content is modified.
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
import sinnoh_f12d3_celestic_cut as cut
import sinnoh_f12d3_gated_alignment as gated
import sinnoh_f12d3_route210_recovery as recovery
from sinnoh_f12d3_alternate_route212 import reserved,interval
from build_johto_events import EVENT_CLASSES
import sinnoh_f12d3_dry_network as dry

# Catalog symbols checked explicitly. Source 22 is Oreburgh, NOT Hearthome.
SYMBOLS={80:"SINNOH_ROUTE_210",84:"SINNOH_SOLACEON_TOWN",104:"SINNOH_ROUTE_209",
    116:"SINNOH_ROUTE_210_SEGMENT_2",123:"SINNOH_HEARTHOME_CITY",
    125:"SINNOH_F07_INTERIOR_125",126:"SINNOH_ROUTE_215",
    205:"SINNOH_VEILSTONE_CITY",206:"SINNOH_ROUTE_214",
    214:"SINNOH_VALOR_LAKEFRONT",218:"SINNOH_ROUTE_213",219:"SINNOH_PASTORIA_CITY",
    222:"SINNOH_ROUTE_212",223:"SINNOH_ROUTE_212_SEGMENT_2"}
WRONG=(223,"N",0,22,"S",171)
# Authorial hypotheses, not source records. Route212 north is gated in Platinum;
# no installation is allowed without a separate progression-gate witness.
AUTHORIAL=((222,"N",123,"S"),(205,"W",126,"E"))
REPAIR={(223,"N",0,222,"S",0),(116,"S",0,80,"N",0),
    (116,"S",98,126,"N",0),(206,"N",0,205,"S",38),
    (126,"W",0,80,"E",0),(84,"N",0,80,"S",60)}
BUDGET=32
LIMIT=12

def path_search(seeds,adj,cost,banned):
    """Lexicographic dry cell edits, authorial crossings, seam crossings, steps."""
    d={};parent={};todo=[]
    for p in sorted(set(seeds)):
        if cost(p)==0:d[p]=(0,0,0,0);heapq.heappush(todo,(*d[p],p))
    while todo:
        a,b,c,n,u=heapq.heappop(todo)
        if d[u]!=(a,b,c,n):continue
        for v,record,kind in adj(u):
            if record in banned:continue
            edit=cost(v)
            if edit is None:continue
            score=(a+edit,b+int(kind=="authorial"),c+int(kind in ("authorial","original")),n+1)
            if score<d.get(v,(10**9,)*4):
                d[v]=score;parent[v]=(u,record,kind);heapq.heappush(todo,(*score,v))
    return d,parent

def trace(p,parent):
    out=[]
    while p in parent:
        u,r,k=parent[p];out.append((u,p,r,k));p=u
    return out[::-1]

def frontier_summary(forward,reverse,neighbours,reason):
    """Bounded sanitized boundary report; never authorizes an edit."""
    def boundary(cells):
        return {q for p in cells for q in neighbours(p) if q not in cells}
    a,b=boundary(forward),boundary(reverse)
    return {"forward_cells":len(forward),"reverse_cells":len(reverse),
        "overlap":len(forward&reverse),
        "forward_counts":dict(Counter(reason(q) for q in a)),
        "reverse_counts":dict(Counter(reason(q) for q in b)),
        "shared_boundary_count":len(a&b),
        "shared_boundary":[{"position":list(q),"reason":reason(q)} for q in sorted(a&b)[:64]]}

def guard_cell_kind(shape,source_shape,mask_cell,occupied=False,protected=False):
    """Diagnostic only: runtime mask admission is not terrain permission."""
    masks,tags=shape
    if occupied or shape!=source_shape or not masks or any(masks) or mask_cell not in (".","g"):
        return None
    if corridor.ordinary(shape):return "ordinary"
    if protected:return None
    return "special_unverified"

def guard_local_paths(seeds,goals,adjacent,kind):
    """Minimize unverified special cells, then upstream edits/crossings/steps.
    No map changes; each result is explicitly NOT a native walking witness.
    """
    d={};parent={};todo=[]
    for p,score in sorted(seeds.items()):
        if kind(p)!="ordinary":continue
        d[p]=(0,*score);heapq.heappush(todo,(*d[p],p))
    while todo:
        a,b,c,e,n,p=heapq.heappop(todo)
        if d[p]!=(a,b,c,e,n):continue
        for q in adjacent(p):
            k=kind(q)
            if k is None:continue
            score=(a+int(k=="special_unverified"),b,c,e,n+1)
            if score>=d.get(q,(10**9,)*5):continue
            d[q]=score;parent[q]=p;heapq.heappush(todo,(*score,q))
    rows=[]
    for goal in sorted(goals):
        row={"position":list(goal),"cost":None,"local_path":None,"special_cells":[]}
        if goal in d:
            path=[goal]
            while path[-1] in parent:path.append(parent[path[-1]])
            path.reverse()
            row.update(cost=list(d[goal]),local_path=[list(p) for p in path],
                special_cells=[list(p) for p in path if kind(p)=="special_unverified"])
        rows.append(row)
    return rows

ROCK_FRONTIER=frozenset(((57,25),(57,26),(57,27)))

def rock_frontier_match(q,source_stack,qa_stack,source_shape,qa_shape,source_priority,qa_priority,guard,occupied,protected):
    """Only the exact three evidenced cells; no generic terrain relaxation."""
    return (q in ROCK_FRONTIER and source_stack==(3225,0,0) and qa_stack==(462,0,0)
        and source_shape==qa_shape==((0,),(4,)) and source_priority==qa_priority==0
        and guard=="." and not occupied and not protected)

def rock_network_match(q,dims,source_stack,qa_stack,source_shape,qa_shape,source_priority,qa_priority,guard,occupied,protected):
    """Identical known Rock tile pair, interior only; no boundary expansion."""
    x,y=q;w,h=dims
    return (0<x<w-1 and 0<y<h-1 and
        source_stack==(3225,0,0) and qa_stack==(462,0,0)
        and source_shape==qa_shape==((0,),(4,)) and source_priority==qa_priority==0
        and guard=="." and not occupied and not protected)

def edit_attribution(edits,partial,edge_points):
    counts=Counter()
    for p in edits:
        counts[(p[0],"directional" if partial(p) else "full_wall",
            "seam_endpoint" if p in edge_points else "interior")]+=1
    return [{"source_id":s,"kind":k,"location":where,"count":n}
        for (s,k,where),n in sorted(counts.items())]

def inspect(blobs,mapping,components,cr,expanded,original,source,root,directional_repair=False,rock_repair=False,rock_network=False):
    chase.validate(blobs,mapping);before=chase.digest(blobs)
    if expanded.get("input_hashes")!=before or not cr.get("runtime_install_enabled") or original.get("status")!="F12D3_ORIGINAL_NETWORK_EVIDENCE_ONLY":
        raise ValueError("F12D3_CANONICAL_STALE")
    catalog,_,_=conn.graph(root)
    if catalog[22]["symbol"]!="SINNOH_OREBURGH_CITY" or any(catalog[s]["symbol"]!=k for s,k in SYMBOLS.items()):
        raise ValueError("F12D3_CANONICAL_SYMBOLS")
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL};origin=cr["placements"][-1]
    rock_cells=frozenset()
    def graph(data):
        return gates.access_graph(data,old,components,root,seed_cells=[(origin["map_id"],*origin["stand"])],directional=True,strict_movement=True,rock_cells=rock_cells)
    worlds,tiles,idx,_,rr,_=graph(blobs);prior=trainers.reached_cells(idx,rr)
    dims={m:(w.attrs["@width"],w.attrs["@height"]) for m,w in worlds.items()}
    current=pv.parse_connections(blobs["PBS/map_connections.txt"])
    if conn.read_marshal(blobs["Data/map_connections.dat"],"F12D3_CANONICAL_COMPILED")!=[recovery.encode(r) for r in current]:
        raise ValueError("F12D3_CANONICAL_COMPILED_MISMATCH")
    entries=tp.build(blobs,old,components,root)
    bound={s:mapping[k] for s,k in SYMBOLS.items()};inv={m:s for s,m in bound.items()}
    def qr(r):return (bound[r[0]],r[1],r[2],bound[r[3]],r[4],r[5])
    qa={s:corridor.grid(worlds[m],tiles) for s,m in bound.items()};src={};sdims={}
    occupied={s:{(e.attrs["@x"],e.attrs["@y"]) for e in worlds[m].attrs["@events"].values()} for s,m in bound.items()}
    protected={s:set(occupied[s]) for s in bound};source_events={};source_mid_stacks={};source_mid_priorities=();source_stacks={};source_priorities={}
    if rock_network and not rock_repair:raise ValueError("F12D3_ROCK_NETWORK_REQUIRES_FRONTIER")
    result={"status":"F12D3_CANONICAL_NETWORK_EVIDENCE_ONLY","installed":False,"native_verified":False,
        "activation_allowed":False,"new_maps":0,"new_portals":0,"new_events":0,"changed_cells_installed":0,
        "budget":BUDGET,"directional_repair":directional_repair,"wrong_source_record":list(WRONG),"wrong_source_destination":"SINNOH_OREBURGH_CITY",
        "authorial_candidates":[],"exact_repair_axes":[],"trials":[],"witness":None}
    def finish(reason):
        if chase.digest(blobs)!=before:raise ValueError("F12D3_CANONICAL_MUTATED")
        result["reason"]=reason;return result
    for row in entries:
        if row[3] and row[3][0] in inv:
            m,x,y=row[3];protected[inv[m]].add((x,y))
    for w in worlds.values():
        for e in w.attrs["@events"].values():
            t,_=conn.classify_transfer(e)
            if t and t[2] in inv:protected[inv[t[2]]].add((t[3],t[4]))
    with pv.verified_archive(source,"maps") as z:
        rows=pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt"))
        if rows.count(WRONG)!=1 or any(rows.count(r)!=1 for r in REPAIR):
            raise ValueError("F12D3_CANONICAL_SOURCE_RECORDS")
        relevant=[r for r in rows if r[0] in bound or r[3] in bound]
        needed=set(bound)|{i for r in relevant for i in (r[0],r[3])}
        st=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D3_CANONICAL_TILES")
        for s in sorted(needed):
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%s)
            w=conn.read_marshal(raw,"F12D3_CANONICAL_SOURCE");sdims[s]=(w.attrs["@width"],w.attrs["@height"])
            if s not in bound:continue
            if hashlib.sha256(raw).hexdigest()!=catalog[s]["sha256"] or sdims[s]!=dims[bound[s]]:
                raise ValueError("F12D3_CANONICAL_HASH")
            source_grid=corridor.grid(w,st);src[s]=source_grid[1]
            if s==116 or rock_network:
                source_stacks[s]=source_grid[0]
                raw_priorities=st[w.attrs["@tileset_id"]].attrs["@priorities"].data[20:]
                source_priorities[s]=struct.unpack("<%dH"%(len(raw_priorities)//2),raw_priorities)
                if s==116:source_mid_stacks=source_stacks[s];source_mid_priorities=source_priorities[s]
            source_events[s]={(e.attrs["@x"],e.attrs["@y"]) for e in w.attrs["@events"].values()}
            protected[s].update(source_events[s])
            protected[s].update(q for xy in tuple(protected[s]) for q in tp.neighbours(*xy)
                if q in qa[s][1] and not corridor.ordinary(qa[s][1][q]))
    result["source_hashes"]={str(s):catalog[s]["sha256"] for s in sorted(bound)}
    result["qa_hashes"]={str(s):hashlib.sha256(blobs["Data/Map%03d.rxdata"%m]).hexdigest() for s,m in sorted(bound.items())}
    result["protected_counts"]={str(s):len(protected[s]) for s in sorted(bound)}
    if rock_repair:
        if not directional_repair or bound[116]!=473:raise ValueError("F12D3_ROCK_SCOPE")
        guard=pv.movement_masks(blobs,mapping,extra_symbols={SYMBOLS[116]})[bound[116]]
        raw=tiles[worlds[bound[116]].attrs["@tileset_id"]].attrs["@priorities"].data[20:]
        qp=struct.unpack("<%dH"%(len(raw)//2),raw)
        accepted=set()
        for q in sorted(ROCK_FRONTIER):
            a,b=source_mid_stacks[q],qa[116][0][q]
            if rock_frontier_match(q,a,b,src[116][q],qa[116][1][q],
                source_mid_priorities[a[0]],qp[b[0]],guard[q[1]][q[0]],q in occupied[116],q in protected[116]):
                accepted.add((473,*q))
        result["rock_model"]={"scope":"EXACT_THREE_ROCK_CELLS_REFERENCE_ENGINE_ONLY",
            "accepted":[list(p) for p in sorted(accepted)],"engine_reference":"Essentials v21.1 Rock tag 4",
            "local_engine_verified":False,"runtime_changed":False}
        if len(accepted)!=3:return finish("rock_frontier_identity_mismatch")
        if rock_network:
            guards=pv.movement_masks(blobs,mapping,extra_symbols=set(SYMBOLS.values()))
            counts={};other_pairs={}
            for s,m in sorted(bound.items()):
                raw=tiles[worlds[m].attrs["@tileset_id"]].attrs["@priorities"].data[20:]
                qp=struct.unpack("<%dH"%(len(raw)//2),raw)
                other=Counter()
                for q,a in source_stacks[s].items():
                    b=qa[s][0][q]
                    if src[s][q]!=qa[s][1][q] or src[s][q]!=((0,),(4,)):continue
                    if a[1:]!=(0,0) or b[1:]!=(0,0):continue
                    if rock_network_match(q,sdims[s],a,b,src[s][q],qa[s][1][q],
                        source_priorities[s][a[0]],qp[b[0]],guards[m][q[1]][q[0]],
                        q in occupied[s],q in protected[s]):
                        accepted.add((m,*q))
                    elif a[0]!=3225 or b[0]!=462:
                        other[(a[0],b[0])]+=1
                counts[str(s)]=sum(p[0]==m for p in accepted)
                other_pairs[str(s)]=[{"source_tile":a,"qa_tile":b,"count":n} for (a,b),n in sorted(other.items())]
            result["rock_network_model"]={"status":"EXACT_TILE_PAIR_INTERIOR_REFERENCE_ONLY",
                "accepted_counts_by_source":counts,"accepted_total":len(accepted),
                "other_pairs_not_admitted":other_pairs,"local_engine_verified":False,
                "runtime_changed":False,"original_budget":BUDGET}
        rock_cells=frozenset(accepted)
        _,_,idx,_,rr,_=graph(blobs)
        augmented=trainers.reached_cells(idx,rr)
        if not prior<=augmented:raise ValueError("F12D3_ROCK_PRIOR_LOSS")
        result["rock_model"]["baseline_reach_delta"]=len(augmented-prior)
        prior=augmented
        for m,x,y in rock_cells:protected[inv[m]].add((x,y))
    def ordinary_at(s,q):
        return corridor.ordinary(qa[s][1][q]) or (bound[s],*q) in rock_cells
    def partial(p):
        s,x,y=p;q=(x,y)
        if not directional_repair or s not in src or q not in src[s] or q in protected[s] or q in occupied[s]:return False
        w,h=sdims[s];shape=qa[s][1][q]
        if not (0<x<w-1 and 0<y<h-1 and dry.dry_partial(src[s][q],shape)):return False
        # Reject conversion that would open even one prohibited existing dry neighbour.
        return all(dry.permitted_step(shape,qa[s][1][v],(v[0]-x,v[1]-y),True,False)
            for v in tp.neighbours(x,y) if v in qa[s][1] and v not in occupied[s] and ordinary_at(s,v))
    def edit_ok(s,q):return corridor.editable(src[s][q],qa[s][1][q]) or partial((s,*q))
    def local_allowed(p,q):
        s=p[0]
        return q[0]==s and q[1:] in qa[s][1] and dry.permitted_step(
            qa[s][1][p[1:]],qa[s][1][q[1:]],(q[1]-p[1],q[2]-p[2]),partial(p),partial(q))
    def cell_cost(p,edge=False):
        s,x,y=p;q=(x,y)
        if s not in src or q not in src[s] or q in occupied[s] or src[s][q]!=qa[s][1][q]:return None
        shape=qa[s][1][q];w,h=sdims[s]
        if ordinary_at(s,q):return 0
        if q in protected[s] or not edit_ok(s,q):return None
        if edge or (0<x<w-1 and 0<y<h-1):return 1
        return None
    cross={};edge_points=set();kinds={}
    def add(a,b,r,k,bidirectional=True):
        cross.setdefault(a,set()).add((b,r,k))
        if bidirectional:cross.setdefault(b,set()).add((a,r,k))
        if r:kinds[r]=k
    # Only actual existing native transfer events, no synthesized transfers.
    native=0
    for s,m in bound.items():
        for e in worlds[m].attrs["@events"].values():
            t,_=conn.classify_transfer(e)
            if not t or t[2] not in inv:continue
            x,y,dst,dx,dy,_,_=t;v=(inv[dst],dx,dy)
            if cell_cost(v)!=0:continue
            trigger=e.attrs["@pages"][0].attrs.get("@trigger")
            if trigger!=0 and not corridor.ordinary(qa[s][1].get((x,y),((),()))):continue
            for q in tp.neighbours(x,y):
                u=(s,*q)
                if cell_cost(u)==0:add(u,v,(),"native",False);native+=1
    result["existing_native_transfer_edges"]=native
    for r in current:
        if r[0] not in inv or r[3] not in inv:continue
        for _,x,y in gated.all_lanes(r,idx,dims):
            u,v=(inv[r[0]],*x),(inv[r[3]],*y)
            if cell_cost(u)==cell_cost(v)==0:add(u,v,r,"installed")
    evidence={tuple(e["source_record"]):e for e in expanded["edge_candidates"]}
    for s,e in evidence.items():
        if s[0] not in bound or s[3] not in bound or e["installed"] or e["source_side_conflict"]:continue
        r=qr(s)
        if reserved(r,current,dims):continue
        lanes=gated.all_lanes(r,idx,dims)
        if [n for n,x,y in lanes]!=e["matching_walkable_axes"]:continue
        for _,x,y in lanes:
            u,v=(s[0],*x),(s[3],*y)
            if cell_cost(u)==cell_cost(v)==0:add(u,v,r,"original")
        if s not in REPAIR:continue
        if reserved(s,[x for x in relevant if x!=s],sdims):continue
        count=0
        for n in seams.aligned_axes(s[1],s[2],sdims[s[0]],s[4],s[5],sdims[s[3]]):
            x=seams.point(n,s[1],s[2],sdims[s[0]]);y=seams.point(n,s[4],s[5],sdims[s[3]])
            u,v=(s[0],*x),(s[3],*y)
            if cell_cost(u,True) is None or cell_cost(v,True) is None:continue
            if cell_cost(u,True)+cell_cost(v,True)==0:continue
            add(u,v,r,"original");edge_points.update((u,v));count+=1
        result["exact_repair_axes"].append({"source_record":list(s),"potential_new_dry_axes":count})
    for a,da,b,db in AUTHORIAL:
        na=sdims[a][0 if da in ("N","S") else 1];nb=sdims[b][0 if db in ("N","S") else 1]
        stats=Counter()
        for delta in range(1-nb,na):
            s=(a,da,max(delta,0),b,db,max(-delta,0));r=qr(s)
            if reserved(s,relevant,sdims) or reserved(r,current,dims):stats["reserved"]+=1;continue
            stats["free"]+=1;lanes=gated.all_lanes(r,idx,dims)
            if not lanes:continue
            verified=[]
            for n,x,y in lanes:
                u,v=(a,*x),(b,*y)
                if cell_cost(u)!=0 or cell_cost(v)!=0 or x in source_events[a] or y in source_events[b]:break
                if (x[0] in (0,sdims[a][0]-1) and x[1] in (0,sdims[a][1]-1)) or (y[0] in (0,sdims[b][0]-1) and y[1] in (0,sdims[b][1]-1)):break
                verified.append((u,v))
            if len(verified)!=len(lanes):stats["unverified"]+=1;continue
            stats["verified_intervals"]+=1;stats["verified_axes"]+=len(verified)
            for u,v in verified:add(u,v,r,"authorial")
        result["authorial_candidates"].append({"source_pair":[a,da,b,db],"counts":dict(stats)})
    exit=next(e for e in expanded["edge_candidates"] if tuple(e["source_record"])==cut.EXIT)
    exit_r=tuple(exit["qa_record"]);lanes=gated.all_lanes(exit_r,idx,dims)
    if exit["source_side_conflict"] or exit["installed"] or [n for n,x,y in lanes]!=exit["matching_walkable_axes"] or not lanes:
        return finish("exit_unverified")
    goals={(116,*x) for _,x,y in lanes}
    seeds={(inv[m],x,y) for m,x,y in prior if m in inv}
    def cost(p):return cell_cost(p,p in edge_points)
    def adj(p):
        for q in tp.neighbours(*p[1:]):
            v=(p[0],*q)
            if local_allowed(p,v):yield v,(),"local"
        yield from sorted(cross.get(p,()))
    banned_sets=[frozenset()];seen=set()
    while banned_sets and len(result["trials"])<LIMIT:
        banned=banned_sets.pop(0)
        if banned in seen:continue
        seen.add(banned)
        d,parents=path_search(seeds,adj,cost,banned)
        if not banned:
            result["reachable_cells_by_source"]={str(s):sum(p[0]==s for p in d) for s in sorted(bound)}
            result["exit_costs"]=[{"position":list(p[1:]),"cost":list(d[p]) if p in d else None} for p in sorted(goals)]
            # Local reverse search from all five exit cells, never through Celestic.
            def local_adj(p):
                return ((v,r,k) for v,r,k in adj(p) if k=="local")
            reverse,_=path_search(goals,local_adj,cost,frozenset())
            forward={p for p in d if p[0]==116}
            def neighbours(p):
                return ((116,*q) for q in tp.neighbours(*p[1:]) if q in qa[116][1])
            def reason(p):
                q=p[1:];shape=qa[116][1][q];masks,tags=shape
                if q in occupied[116]:return "occupied"
                if src[116][q]!=shape:return "source_qa_mismatch"
                if cost(p) is not None:return "admitted_but_disconnected"
                if q in protected[116]:return "protected"
                if not masks:return "empty_stack"
                if any(t not in (0,2) for t in tags):return "special_terrain"
                if any(0<v<15 for v in masks):return "directional_mask"
                return "perimeter_or_noneditable"
            result["celestic_frontier"]=frontier_summary(forward,set(reverse),neighbours,reason)
            result["celestic_frontier"]["forward_components"]=sorted({idx[bound[116]][p[1:]] for p in forward if p[1:] in idx[bound[116]]})
            result["celestic_frontier"]["reverse_components"]=sorted({idx[bound[116]][p[1:]] for p in reverse if p[1:] in idx[bound[116]]})
            result["celestic_frontier"]["goal_admission"]=[{"position":list(p[1:]),"admitted":cost(p) is not None,"reason":None if cost(p) is not None else reason(p)} for p in sorted(goals)]
            result["partial_candidates"]={str(s):sum(partial((s,*q)) for q in src[s]) for s in sorted(bound)}
            if directional_repair:
                # Read the exact movement mask generated by the private installer.
                # Do not relax the strict graph or edit any special terrain.
                guard=pv.movement_masks(blobs,mapping,extra_symbols={SYMBOLS[116]})[bound[116]]
                raw_priorities=tiles[worlds[bound[116]].attrs["@tileset_id"]].attrs["@priorities"].data[20:]
                qa_priorities=struct.unpack("<%dH"%(len(raw_priorities)//2),raw_priorities)
                def kind(q):
                    if q not in src[116]:return None
                    return guard_cell_kind(qa[116][1][q],src[116][q],guard[q[1]][q[0]],
                        q in occupied[116],q in protected[116])
                def meta(q):
                    masks,tags=qa[116][1][q];sm,st=src[116][q]
                    a=source_mid_stacks[q];b=qa[116][0][q]
                    return {"position":list(q),"source_tile_layers":list(a),"qa_tile_layers":list(b),
                        "source_priorities":[source_mid_priorities[i] for i in a if i],
                        "qa_priorities":[qa_priorities[i] for i in b if i],
                        "source_masks":list(sm),"source_tags":list(st),"qa_masks":list(masks),"qa_tags":list(tags),
                        "source_matches_qa_shape":src[116][q]==qa[116][1][q],
                        "guard_cell":guard[q[1]][q[0]],"occupied":q in occupied[116],"protected":q in protected[116],
                        "diagnostic_kind":kind(q),"forward_adjacent":[list(v) for v in tp.neighbours(*q) if (116,*v) in forward],
                        "reverse_adjacent":[list(v) for v in tp.neighbours(*q) if (116,*v) in reverse]}
                probes=[meta(tuple(p["position"][1:])) for p in result["celestic_frontier"]["shared_boundary"]]
                seed_cost={p[1:]:d[p] for p in forward if kind(p[1:])=="ordinary"}
                paths=guard_local_paths(seed_cost,{p[1:] for p in goals},lambda q:tp.neighbours(*q),kind)
                details={tuple(q) for row in paths for q in row["special_cells"]}
                for row in paths:
                    if row["local_path"]:
                        start=(116,*row["local_path"][0])
                        row["upstream_path"]=[{"from":list(u),"to":list(v),"record":list(r),"kind":k}
                            for u,v,r,k in trace(start,parents)]
                        row["within_dry_budget"]=row["cost"][1]<=BUDGET
                result["special_terrain_frontier"]={"status":"MASK_ONLY_DIAGNOSTIC_NOT_WALK_PROOF",
                    "activation_allowed":False,"native_verified":False,"installed":False,"changed_cells":0,
                    "source_map_id":116,"qa_map_id":bound[116],"shared_cells":probes,
                    "exit_paths":paths,"special_path_cells":[meta(q) for q in sorted(details)],
                    "cost_fields":["unverified_special_cells","upstream_dry_edits","authorial_crossings","new_seam_crossings","steps"],
                    "requires_engine_terrain_semantics_and_progression_proof":True}
        if not goals<=set(d):continue
        goal=min(goals,key=lambda p:(d[p],p));path=trace(goal,parents)
        nodes={p for u,v,r,k in path for p in (u,v)}
        edits={p for p in nodes if cost(p)==1}
        additions=[];endpoints=set()
        for u,v,r,k in path:
            if k in ("original","authorial"):
                endpoints.update((u,v))
                if r not in additions:additions.append(r)
        row={"cost":list(d[goal]),"qa_records":[list(r) for r in additions],"fixture_passed":False}
        if rock_repair:
            row["edit_attribution"]=edit_attribution(edits,partial,edge_points)
            row["unique_edits"]=len(edits)
            row["rock_cells_on_path"]=[list(p) for p in sorted(nodes) if (bound[p[0]],*p[1:]) in rock_cells]
            row["crossings"]=[{"from":list(u),"to":list(v),"record":list(r),"kind":k} for u,v,r,k in path if k!="local"]
            if not banned:row["candidate_edits"]=[{"position":list(p),"qa_map_id":bound[p[0]],"masks":list(qa[p[0]][1][p[1:]][0]),"tags":list(qa[p[0]][1][p[1:]][1])} for p in sorted(edits)]
        result["trials"].append(row)
        for r in additions:
            if kinds[r]=="authorial":banned_sets.append(banned|{r})
        if len(edits)>BUDGET:row["reason"]="over_budget";continue
        if any(cell_cost(p) is None and p not in endpoints for p in edits):row["reason"]="unrelated_perimeter_edit";continue
        selected=[];conflict=False
        for r in additions:
            if reserved(r,current+selected,dims):conflict=True;break
            selected.append(r)
        if conflict:row["reason"]="combined_reservation_conflict";continue
        trial=dict(blobs)
        trial["PBS/map_connections.txt"]=blobs["PBS/map_connections.txt"]+("\n# F12D3 canonical fixture only\n"+"\n".join(",".join(map(str,r)) for r in additions)+"\n").encode("ascii")
        trial["Data/map_connections.dat"]=conn.serialize([recovery.encode(r) for r in current+additions])
        donors=[];failed=False
        for s,m in bound.items():
            changes={p[1:] for p in edits if p[0]==s}
            if not changes:continue
            rel="Data/Map%03d.rxdata"%m;world=conn.read_marshal(blobs[rel],"F12D3_CANONICAL_MAP")
            stacks,shapes=qa[s];w,h=sdims[s];data=world.attrs["@data"];raw=data.data;patch=bytearray(raw)
            floor=[q for q in shapes if corridor.ordinary(shapes[q]) and all(t==0 for t in shapes[q][1]) and q not in protected[s] and shapes[q]==src[s][q]]
            if not floor:failed=True;row["reason"]="no_dry_floor";break
            for x,y in sorted(changes):
                q=(x,y)
                if q in protected[s] or not edit_ok(s,q):raise ValueError("F12D3_CANONICAL_UNSAFE_EDIT")
                f=min(floor,key=lambda t:(conn.distance(q,t),t[1],t[0]))
                for z,t in enumerate(stacks[f]):struct.pack_into("<H",patch,20+2*(z*w*h+y*w+x),t)
                donors.append({"map_id":m,"position":list(q),"floor_reference":list(f),"directional_conversion":partial((s,*q)),"before_masks":list(shapes[q][0]),"before_tags":list(shapes[q][1])})
            data.data=bytes(patch);out=conn.serialize(world,EVENT_CLASSES)
            check=conn.read_marshal(out,"F12D3_CANONICAL_VERIFY");_,after=corridor.grid(check,tiles)
            if {q for q in shapes if shapes[q]!=after[q]}!=changes or not all(corridor.ordinary(after[q]) for q in changes):
                raise ValueError("F12D3_CANONICAL_DELTA")
            partial_edits={q for q in changes if partial((s,*q))}
            rock_conflict=any(not dry.permitted_step(shapes[q],shapes[v],(v[0]-q[0],v[1]-q[1]),True,False)
                for q in partial_edits for v in tp.neighbours(*q) if (m,*v) in rock_cells)
            if rock_conflict or not dry.new_dry_edges_allowed(shapes,after,partial_edits,changes,occupied[s]):
                failed=True;row["reason"]="directional_conversion_opens_forbidden_neighbour";break
            data.data=raw;check.attrs["@data"].data=raw
            if conn.serialize(check,EVENT_CLASSES)!=conn.serialize(world,EVENT_CLASSES):raise ValueError("F12D3_CANONICAL_METADATA")
            trial[rel]=out
        if failed:continue
        _,_,ix,_,reach,_=graph(trial);cells=trainers.reached_cells(ix,reach)
        required={bound[s] for s in (80,116,126,222,223)}
        if not prior<=cells or not required<={m for m,x,y in cells} or not {(bound[116],*p[1:]) for p in goals}<=cells or tp.build(trial,old,components,root)!=entries:
            row["reason"]="global_fixture_failed";continue
        if not {(bound[s],x,y) for s,x,y in nodes}<=cells:row["reason"]="path_not_reachable";continue
        row.update(fixture_passed=True,edits=donors,path=[{"from":list(u),"to":list(v),"record":list(r),"kind":k} for u,v,r,k in path],
            requires_progression_gate=True,reason=None)
        row["cut"]=cut.inspect(blobs,blobs,mapping,components,cr,expanded,{},root,recovered_alternative=trial,
            source_protected={(bound[116],*q) for q in protected[116]},rock_cells=rock_cells)
        result["witness"]=row
        if any(c["status"]=="AUTHORIAL_EXIT_CUT_FIXTURE_ONLY" for c in row["cut"]["cases"]):break
    return finish("canonical_fixture_only" if result["witness"] else "no_verified_canonical_network")
