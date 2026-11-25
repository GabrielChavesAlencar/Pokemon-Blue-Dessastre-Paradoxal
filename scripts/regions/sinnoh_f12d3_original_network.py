"""Original-only component network, with no new offsets or terrain edits.
Investigate routes beyond the bounded 212/215 pair; no installer activation.
"""
import heapq
import hashlib
from collections import Counter
import sinnoh_f12d_pastoria_preview as chase
import sinnoh_f12d_seams as seams
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10b_trainers as trainers
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as tp
import sinnoh_f08c_expansion as f08c
import sinnoh_f12d3_celestic_cut as cut
import sinnoh_f12d3_gated_alignment as gated
import sinnoh_f12d3_route210_recovery as recovery
from sinnoh_f12d3_alternate_route212 import reserved

LIMIT=12

def component_paths(edges,seeds):
    """Minimum number of new original seams, then crossings.
    Physical component adjacency only. Each edge carries its exact record.
    """
    d={};parents={};todo=[]
    for s in sorted(set(seeds)):
        d[s]=(0,0);heapq.heappush(todo,(0,0,s))
    while todo:
        a,b,u=heapq.heappop(todo)
        if d[u]!=(a,b):continue
        for v,record,installed in sorted(edges.get(u,())):
            score=(a+int(not installed),b+1)
            if score<d.get(v,(10**9,10**9)):
                d[v]=score;parents[v]=(u,record,installed);heapq.heappush(todo,(*score,v))
    return d,parents

def trace(node,parents):
    result=[]
    while node in parents:
        u,r,installed=parents[node]
        result.append((u,node,r,installed));node=u
    return result[::-1]

def inspect(blobs,mapping,components,cr,expanded,source,root):
    chase.validate(blobs,mapping);before=chase.digest(blobs)
    if expanded.get("input_hashes")!=before or not cr.get("runtime_install_enabled"):
        raise ValueError("F12D3_ORIGINAL_NETWORK_STALE")
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    origin=cr["placements"][-1]
    def graph(data):
        return gates.access_graph(data,old,components,root,seed_cells=[(origin["map_id"],*origin["stand"])],
            directional=True,strict_movement=True)
    worlds,tiles,idx,groups,rr,_=graph(blobs);prior=trainers.reached_cells(idx,rr)
    dims={m:(w.attrs["@width"],w.attrs["@height"]) for m,w in worlds.items()}
    current=pv.parse_connections(blobs["PBS/map_connections.txt"])
    if conn.read_marshal(blobs["Data/map_connections.dat"],"F12D3_ORIGINAL_NETWORK_COMPILED")!=[recovery.encode(r) for r in current]:
        raise ValueError("F12D3_ORIGINAL_NETWORK_COMPILED")
    entries=tp.build(blobs,old,components,root)
    catalog,_,_=conn.graph(root);catalog={**catalog,**{r["source_id"]:r for r in f08c.rows(root)}}
    bound={s:mapping[r["symbol"]] for s,r in catalog.items() if r["symbol"] in old}
    town=bound[77];mid=bound[116]
    result={"status":"F12D3_ORIGINAL_NETWORK_EVIDENCE_ONLY","activation_allowed":False,"installed":False,
        "native_verified":False,"new_maps":0,"new_events":0,"new_portals":0,"changed_cells_installed":0,
        "bound_source_maps":len(bound),"records":[],"trials":[],"witness":None}
    def finish(reason):
        if chase.digest(blobs)!=before:raise ValueError("F12D3_ORIGINAL_NETWORK_MUTATED")
        result["reason"]=reason;return result
    evidence={tuple(e["source_record"]):e for e in expanded["edge_candidates"]}
    exit=evidence.get(cut.EXIT)
    if not exit or exit["source_side_conflict"] or exit["installed"]:return finish("exit_unverified")
    exit_r=tuple(exit["qa_record"]);lanes=gated.all_lanes(exit_r,idx,dims)
    if [n for n,x,y in lanes]!=exit["matching_walkable_axes"] or not lanes:return finish("exit_lane_mismatch")
    goals={(mid,idx[mid][x]) for _,x,y in lanes}
    # Celestic cannot be used as an entry/shortcut to its own blocked route.
    if any(m==town for m,label in rr):return finish("celestic_already_reachable")
    edges={};stats=Counter();protected=set()
    def add(record,walk,installed):
        a,_,_,b,_,_=record
        if town in (a,b):return
        for n,x,y in walk:
            u=(a,idx[a][x]);v=(b,idx[b][y])
            edges.setdefault(u,set()).add((v,record,installed))
            edges.setdefault(v,set()).add((u,record,installed))
    # Existing seams are permitted, but cannot add a new portal or transfer.
    for r in current:
        if r[0] in worlds and r[3] in worlds:add(r,gated.all_lanes(r,idx,dims),True)
    with pv.verified_archive(source,"maps") as z:
        raw_records=pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt"))
        if any(raw_records.count(s)!=1 for s in evidence):raise ValueError("F12D3_ORIGINAL_NETWORK_RECORD")
        raw=pv.member(z,pv.MAP_ROOT+"Data/Map116.rxdata")
        if hashlib.sha256(raw).hexdigest()!=catalog[116]["sha256"]:raise ValueError("F12D3_ORIGINAL_NETWORK_HASH")
        w=conn.read_marshal(raw,"F12D3_ORIGINAL_NETWORK_PROTECTED")
        protected={(mid,e.attrs["@x"],e.attrs["@y"]) for e in w.attrs["@events"].values()}
        for s in sorted(evidence):
            e=evidence[s];r=tuple(e["qa_record"]);reason=None
            if r!=(bound[s[0]],s[1],s[2],bound[s[3]],s[4],s[5]):raise ValueError("F12D3_ORIGINAL_NETWORK_MAPIDS")
            walk=gated.all_lanes(r,idx,dims)
            if e["installed"]:reason="already_installed"
            elif town in (r[0],r[3]):reason="celestic_excluded_until_cut"
            elif e["source_side_conflict"] or reserved(r,current,dims):reason="reserved_interval"
            elif not e["matching_walkable_axes"]:reason="no_verified_dry_lane"
            elif [n for n,x,y in walk]!=e["matching_walkable_axes"]:reason="source_qa_lane_mismatch"
            else:
                reason="candidate";add(r,walk,False)
            stats[reason]+=1
            result["records"].append({"source_record":list(s),"qa_record":list(r),"reason":reason,
                "aligned_axes":e["aligned_axes"],"walkable_axes":e["matching_walkable_axes"]})
    d,p=component_paths(edges,rr)
    result["counts"]=dict(stats)
    result["goal_components"]=sorted(label for m,label in goals)
    result["goal_costs"]=[{"component":label,"minimum_new_original_seams":d[(m,label)][0] if (m,label) in d else None} for m,label in sorted(goals)]
    result["reachable_source_components"]={str(s):sorted(label for m,label in d if m==bound[s])
        for s in (84,80,116,126,222,223) if s in bound}
    result["frontier_records"]=[x for x in result["records"] if x["reason"]!="candidate" and
        any(m in (x["qa_record"][0],x["qa_record"][3]) for m,label in d)]
    if not goals<=set(d):return finish("no_complete_original_component_path")
    # Paths to all five axes must coexist; reject intersecting reservations.
    paths=[trace(q,p) for q in sorted(goals)]
    added=[]
    for path in paths:
        for u,v,r,installed in path:
            if not installed and r not in added:
                if reserved(r,current+added,dims):return finish("candidate_paths_conflict")
                added.append(r)
    if len(added)>LIMIT:return finish("original_seam_budget")
    trial=dict(blobs)
    trial["PBS/map_connections.txt"]=blobs["PBS/map_connections.txt"]+("\n# F12D3 original-only network fixture\n"+"\n".join(",".join(map(str,r)) for r in added)+"\n").encode("ascii")
    trial["Data/map_connections.dat"]=conn.serialize([recovery.encode(r) for r in current+added])
    _,_,ix,_,reach,_=graph(trial);cells=trainers.reached_cells(ix,reach)
    row={"qa_records":[list(r) for r in added],"paths":[[{"from":list(u),"to":list(v),"record":list(r),"installed":i} for u,v,r,i in path] for path in paths],
        "fixture_passed":False}
    result["trials"].append(row)
    required={bound[s] for s in (80,116,126,222,223)}
    if not prior<=cells or not required<={m for m,x,y in cells} or not {(mid,*x) for _,x,y in lanes}<=cells or tp.build(trial,old,components,root)!=entries:
        return finish("original_network_global_fixture_failed")
    row["fixture_passed"]=True
    row["cut"]=cut.inspect(blobs,blobs,mapping,components,cr,expanded,{},root,recovered_alternative=trial,source_protected=protected)
    result["witness"]=row
    return finish("original_network_fixture_only")
