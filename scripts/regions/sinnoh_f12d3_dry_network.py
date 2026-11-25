"""Bounded authorial dry-network fixture. Never called by installer.
Find a complete physical Pastoria -> Route212 -> Route215 -> Route210 -> Celestic
path, not an isolated boundary pair. No transfer events or native QA claims.
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
import sinnoh_f12d3_alternate_route212 as alt
import sinnoh_f12d3_celestic_cut as cut
import sinnoh_f12d3_route210_recovery as recovery
import sinnoh_f12d3_gated_alignment as gated
from build_johto_events import EVENT_CLASSES

EXTRA=(116,"S",98,126,"N",0)
BUDGET=32
LIMIT=12

def search(seeds,adjacent,cost):
    dist={};parents={};queue=[]
    for p in sorted(set(seeds)):
        if cost(p)==0:dist[p]=(0,0);heapq.heappush(queue,(0,0,p))
    while queue:
        a,b,p=heapq.heappop(queue)
        if dist[p]!=(a,b):continue
        for q in adjacent(p):
            c=cost(q)
            if c is None:continue
            score=(a+c,b+1)
            if score<dist.get(q,(10**9,10**9)):
                dist[q]=score;parents[q]=p;heapq.heappush(queue,(*score,q))
    return dist,parents

def trace(q,parents):
    path=[q]
    while q in parents:q=parents[q];path.append(q)
    return path[::-1]

def endpoint(q,dist,parents,cost,neighbours):
    # Permit a new perimeter endpoint only as the final cell, never as
    # a chain of unrelated newly opened perimeter cells.
    options=[]
    if q in dist:options.append((dist[q],q,False))
    if cost is not None:
        for p in neighbours:
            if p in dist:options.append(((dist[p][0]+cost,dist[p][1]+1),p,True))
    if not options:return None
    score,p,append=min(options)
    return score,trace(p,parents)+([q] if append else [])

def inspect(blobs,mapping,components,cr,expanded,previous,source_path,root):
    chase.validate(blobs,mapping);before=chase.digest(blobs)
    if (expanded.get("input_hashes")!=before or not cr.get("runtime_install_enabled") or
        previous.get("status")!="F12D3_DRY_RECOVERY_EVIDENCE_ONLY" or previous.get("activation_allowed") is not False):
        raise ValueError("F12D3_NETWORK_STALE")
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL};origin=cr["placements"][-1]
    def graph(data):
        return gates.access_graph(data,old,components,root,seed_cells=[(origin["map_id"],*origin["stand"])],
            directional=True,strict_movement=True)
    worlds,tiles,idx,_,rr,_=graph(blobs);prior=trainers.reached_cells(idx,rr)
    dims={m:(w.attrs["@width"],w.attrs["@height"]) for m,w in worlds.items()}
    current=pv.parse_connections(blobs["PBS/map_connections.txt"])
    if conn.read_marshal(blobs["Data/map_connections.dat"],"F12D3_NET_COMPILED")!=[recovery.encode(r) for r in current]:
        raise ValueError("F12D3_NETWORK_COMPILED")
    entries=tp.build(blobs,old,components,root)
    ids={80,116,126,222,223};catalog,_,_=conn.graph(root)
    bound={s:mapping[catalog[s]["symbol"]] for s in ids|{77,219}}
    inv={v:k for k,v in bound.items() if k in ids}
    result={"status":"F12D3_DRY_NETWORK_EVIDENCE_ONLY","installed":False,"native_verified":False,
        "activation_allowed":False,"new_events":0,"new_portals":0,"new_maps":0,"changed_cells_installed":0,
        "budget":BUDGET,"trials":[],"counts":{},"witness":None}
    def finish(reason):
        if before!=chase.digest(blobs):raise ValueError("F12D3_NETWORK_MUTATED")
        result["reason"]=reason;return result
    def qrecord(r):return (bound[r[0]],r[1],r[2],bound[r[3]],r[4],r[5])
    def append(data,rows):
        out=dict(data)
        out["PBS/map_connections.txt"]=data["PBS/map_connections.txt"]+("\n# F12D3 authorial network fixture only\n"+"\n".join(",".join(map(str,r)) for r in rows)+"\n").encode("ascii")
        out["Data/map_connections.dat"]=conn.serialize([recovery.encode(r) for r in current+rows])
        return out
    evidence={tuple(e["source_record"]):e for e in expanded["edge_candidates"]}
    fixed=[]
    for s in alt.FIXED:
        e=evidence.get(s);r=qrecord(s)
        if not e or e["installed"] or e["source_side_conflict"] or alt.reserved(r,current+fixed,dims):
            return finish("fixed_record_conflict")
        if [n for n,x,y in gated.all_lanes(r,idx,dims)]!=e["matching_walkable_axes"] or not e["matching_walkable_axes"]:
            return finish("fixed_record_lane_mismatch")
        fixed.append(r)
    fixed_data=append(blobs,fixed)
    _,_,fi,_,fr,_=graph(fixed_data);fixed_cells=trainers.reached_cells(fi,fr)
    if not prior<=fixed_cells or tp.build(fixed_data,old,components,root)!=entries:
        return finish("fixed_fixture_changes_baseline")
    left={222,223};right={80,116,126}
    qa={s:corridor.grid(worlds[bound[s]],tiles) for s in ids};src={};sdims={}
    protected={s:set() for s in ids};occupied={s:{(e.attrs["@x"],e.attrs["@y"]) for e in worlds[bound[s]].attrs["@events"].values()} for s in ids}
    for row in entries:
        if row[3]:
            m,x,y=row[3]
            if m in inv:protected[inv[m]].add((x,y))
    for world in worlds.values():
        for e in world.attrs["@events"].values():
            t,_=conn.classify_transfer(e)
            if t:
                _,_,m,x,y,_,_=t
                if m in inv:protected[inv[m]].add((x,y))
    with pv.verified_archive(source_path,"maps") as z:
        rows=pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt"))
        relevant=[r for r in rows if r[0] in ids or r[3] in ids]
        needed=ids|{i for r in relevant for i in (r[0],r[3])}
        st=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D3_NET_TILES")
        for s in sorted(needed):
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%s)
            w=conn.read_marshal(raw,"F12D3_NET_SOURCE");sdims[s]=(w.attrs["@width"],w.attrs["@height"])
            if s not in ids:continue
            if hashlib.sha256(raw).hexdigest()!=catalog[s]["sha256"] or sdims[s]!=dims[bound[s]]:
                raise ValueError("F12D3_NETWORK_SOURCE_IDENTITY")
            src[s]=corridor.grid(w,st)[1]
            protected[s].update((e.attrs["@x"],e.attrs["@y"]) for e in w.attrs["@events"].values())
            protected[s].update(occupied[s])
            protected[s].update(q for xy in tuple(protected[s]) for q in tp.neighbours(*xy)
                if q in qa[s][1] and not corridor.ordinary(qa[s][1][q]))
    if any(rows.count(r)!=1 for r in alt.FIXED+alt.BROKEN+(EXTRA,cut.EXIT)):
        return finish("source_record_inventory_changed")
    if any(alt.interval(r,sdims) for r in alt.BROKEN):return finish("broken_record_not_empty")
    result["protected_counts"]={str(s):len(protected[s]) for s in sorted(ids)}
    def cell_cost(p,edge=False):
        s,x,y=p;q=(x,y)
        if s not in qa or q not in src[s] or q in occupied[s] or src[s][q]!=qa[s][1][q]:return None
        shape=qa[s][1][q];w,h=sdims[s]
        if corridor.ordinary(shape):return 0
        if q in protected[s] or not corridor.editable(src[s][q],shape):return None
        if edge or (0<x<w-1 and 0<y<h-1):return 1
        return None
    def local(p):return [(p[0],*q) for q in tp.neighbours(*p[1:])]
    cross={};extra_edges=set();extra_points=set()
    def add(a,b):cross.setdefault(a,set()).add(b);cross.setdefault(b,set()).add(a)
    # Existing fixed ordinary lanes only, source/QA matched.
    for s in alt.FIXED[1:]:
        if s[0] not in ids or s[3] not in ids:continue
        for _,x,y in gated.all_lanes(qrecord(s),idx,dims):
            a,b=(s[0],*x),(s[3],*y)
            if cell_cost(a)==cell_cost(b)==0:add(a,b)
    extra=qrecord(EXTRA)
    if not alt.reserved(EXTRA,[r for r in relevant if r!=EXTRA],sdims) and not alt.reserved(extra,current+fixed,dims):
        for n in seams.aligned_axes(EXTRA[1],EXTRA[2],sdims[116],EXTRA[4],EXTRA[5],sdims[126]):
            x=seams.point(n,EXTRA[1],EXTRA[2],sdims[116]);y=seams.point(n,EXTRA[4],EXTRA[5],sdims[126])
            a,b=(116,*x),(126,*y)
            if cell_cost(a,True) is not None and cell_cost(b,True) is not None:
                add(a,b);extra_edges.add(frozenset((a,b)));extra_points.update((a,b))
    result["original_215_to_210_segment2_potential_axes"]=len(extra_edges)
    def adjacent(p):return local(p)+sorted(cross.get(p,()))
    def cost(p):return cell_cost(p,p in extra_points)
    exit_e=evidence.get(cut.EXIT)
    if not exit_e or exit_e["source_side_conflict"] or exit_e["installed"]:return finish("exit_evidence_missing")
    exit_record=qrecord(cut.EXIT);lanes=gated.all_lanes(exit_record,idx,dims)
    if [n for n,x,y in lanes]!=exit_e["matching_walkable_axes"] or not lanes:return finish("exit_lane_mismatch")
    exits={(116,*x) for _,x,y in lanes}
    seeds={(inv[m],x,y) for m,x,y in fixed_cells if m in inv and inv[m] in left}
    ld,lp=search(seeds,lambda p:(q for q in adjacent(p) if q[0] in left),cost)
    rd,rp=search(exits,lambda p:(q for q in adjacent(p) if q[0] in right),cost)
    result["approach_cells"]={"from_pastoria":len(ld),"from_celestic_exit":len(rd)}
    result["reverse_components"]={str(s):sorted({idx[bound[s]][p[1:]] for p in rd if p[0]==s and p[1:] in idx[bound[s]]}) for s in sorted(right)}
    cache={}
    def end(p,side):
        key=(p,side)
        if key not in cache:
            d,par=(ld,lp) if side==0 else (rd,rp)
            cache[key]=endpoint(p,d,par,cell_cost(p,True),local(p)) if cell_cost(p,True) is not None else None
        return cache[key]
    proposals=[];stats=Counter()
    for sid in sorted(left):
        for direction in ("N","S","E","W"):
            opposite=conn.OPPOSITE[direction];a,b=sdims[sid],sdims[126]
            na=a[0] if direction in ("N","S") else a[1];nb=b[0] if direction in ("N","S") else b[1]
            for delta in range(1-nb,na):
                s=(sid,direction,max(delta,0),126,opposite,max(-delta,0));r=qrecord(s)
                if alt.reserved(s,relevant,sdims) or alt.reserved(r,current+fixed+[extra],dims):stats["reserved"]+=1;continue
                stats["free_intervals"]+=1;best=None
                for n in seams.aligned_axes(s[1],s[2],a,s[4],s[5],b):
                    x=seams.point(n,s[1],s[2],a);y=seams.point(n,s[4],s[5],b)
                    # Do not build new seams at ambiguous corner cells.
                    if (x[0] in (0,a[0]-1) and x[1] in (0,a[1]-1)) or (y[0] in (0,b[0]-1) and y[1] in (0,b[1]-1)):continue
                    l=end((sid,*x),0);rr=end((126,*y),1)
                    if not l or not rr:continue
                    stats["approach_pairs"]+=1
                    path=l[1]+rr[1][::-1]
                    if len(set(path))!=len(path):continue
                    edits={p for p in path if cell_cost(p,True)==1}
                    jumps={frozenset((u,v)) for u,v in zip(path,path[1:]) if u[0]!=v[0]}
                    used=bool(jumps&extra_edges)
                    endpoints=set().union(*jumps) if jumps else set()
                    if any(cell_cost(p) is None and p not in endpoints for p in edits):continue
                    score=(len(edits),len(path),s,n)
                    if best is None or score<best[0]:best=(score,path,edits,used)
                if best:proposals.append(best)
    result["counts"]=dict(stats);proposals.sort(key=lambda q:q[0])
    result["complete_interval_candidates"]=len(proposals)
    result["minimum_edits"]=proposals[0][0][0] if proposals else None
    if not proposals:return finish("no_connected_dry_network")
    for score,path,edits,used in proposals[:LIMIT]:
        count,_,s,n=score
        row={"source_record":list(s),"axis":n,"minimum_edits":count,"uses_original_215_segment2":used,"fixture_passed":False}
        result["trials"].append(row)
        if count>BUDGET:row["reason"]="over_budget";break
        r=qrecord(s);new=fixed+[r]+([extra] if used else [])
        trial=append(blobs,new);hashes={};donors=[];failed=False
        for sid in sorted(ids):
            changes={p[1:] for p in edits if p[0]==sid}
            if not changes:continue
            m=bound[sid];rel="Data/Map%03d.rxdata"%m;world=conn.read_marshal(blobs[rel],"F12D3_NET_MAP")
            stacks,shapes=qa[sid];w,h=sdims[sid];data=world.attrs["@data"];raw=data.data;patch=bytearray(raw)
            floor=[q for q in shapes if corridor.ordinary(shapes[q]) and all(t==0 for t in shapes[q][1]) and q not in protected[sid] and shapes[q]==src[sid][q]]
            if not floor:failed=True;break
            for x,y in sorted(changes):
                q=(x,y)
                if q in protected[sid] or not corridor.editable(src[sid][q],shapes[q]):raise ValueError("F12D3_NET_UNSAFE_EDIT")
                f=min(floor,key=lambda t:(conn.distance(q,t),t[1],t[0]))
                for z,t in enumerate(stacks[f]):struct.pack_into("<H",patch,20+2*(z*w*h+y*w+x),t)
                donors.append({"map_id":m,"position":list(q),"floor_reference":list(f)})
            data.data=bytes(patch);out=conn.serialize(world,EVENT_CLASSES)
            check=conn.read_marshal(out,"F12D3_NET_VERIFY");_,after=corridor.grid(check,tiles)
            if {q for q in shapes if shapes[q]!=after[q]}!=changes or not all(corridor.ordinary(after[q]) for q in changes):
                raise ValueError("F12D3_NET_DELTA")
            data.data=raw;check.attrs["@data"].data=raw
            if conn.serialize(check,EVENT_CLASSES)!=conn.serialize(world,EVENT_CLASSES):raise ValueError("F12D3_NET_METADATA")
            trial[rel]=out;hashes[str(m)]={"before":hashlib.sha256(blobs[rel]).hexdigest(),"after":hashlib.sha256(out).hexdigest()}
        if failed:row["reason"]="no_local_floor";continue
        _,_,ix,_,reach,_=graph(trial);cells=trainers.reached_cells(ix,reach)
        totals={str(s):sum(p[0]==bound[s] for p in cells) for s in ids}
        row["reachable_cells"]=totals
        if not prior<=cells or not all(totals.values()) or not {(bound[116],*p[1:]) for p in exits}<=cells or tp.build(trial,old,components,root)!=entries:
            row["reason"]="global_reach_or_entries_failed";continue
        if not all((bound[p[0]],*p[1:]) in cells for p in path):row["reason"]="path_not_reachable";continue
        row.update(fixture_passed=True,reason=None,qa_records=[list(r) for r in new],path=[list(p) for p in path],edits=donors,map_hashes=hashes)
        row["cut"]=cut.inspect(blobs,blobs,mapping,components,cr,expanded,{},root,recovered_alternative=trial,
            source_protected={(bound[116],*q) for q in protected[116]})
        result["witness"]=row
        if any(c["status"]=="AUTHORIAL_EXIT_CUT_FIXTURE_ONLY" for c in row["cut"]["cases"]):break
    return finish("network_fixture_only" if result["witness"] else "no_verified_network_fixture")
