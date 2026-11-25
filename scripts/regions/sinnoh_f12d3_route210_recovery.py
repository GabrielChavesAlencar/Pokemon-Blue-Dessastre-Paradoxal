"""Route 210 conservative append-only connection candidate (not installed).
Only consumes fresh expanded evidence computed against the same immutable maps.
No tile edits, event edits, teleport creation, or save access.
"""
import sinnoh_f12d_pastoria_preview as chase
import sinnoh_f12d_seams as seams
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10b_trainers as trainers
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as tp

LIMIT=12

def encode(row):
    a,da,oa,b,db,ob=row
    return [a,da.encode("ascii"),oa,b,db.encode("ascii"),ob]

def sides(row):
    return {(row[0],row[1]),(row[3],row[4])}

def frontier_candidates(rows,current,index,reached,dimensions):
    used=set().union(*(sides(r) for r in current))
    for row in rows:
        r=tuple(row["qa_record"])
        if row["installed"] or row["source_side_conflict"] or sides(r)&used:
            continue
        a,da,oa,b,db,ob=r
        if a not in index or b not in index:continue
        lanes=[]
        for n in row["matching_walkable_axes"]:
            x=seams.point(n,da,oa,dimensions[a]);y=seams.point(n,db,ob,dimensions[b])
            if x not in index[a] or y not in index[b]:continue
            u=(a,index[a][x]);v=(b,index[b][y])
            if (u in reached)!=(v in reached):lanes.append(n)
        if lanes:yield r,lanes

def preview(blobs,mapping,components,chase_report,evidence,root):
    chase.validate(blobs,mapping)
    def blocked(reason,attempts=()):
        return blobs,{"status":"F12D3_ROUTE210_RECOVERY_BLOCKED","reason":reason,
            "attempts":list(attempts),"new_seams":0,"new_portals":0,"native_verified":False}
    if (evidence.get("status")!="F12D3_EXPANDED_EVIDENCE_ONLY" or
        evidence.get("input_hashes")!=chase.digest(blobs) or
        not chase_report.get("runtime_install_enabled")):
        return blocked("requires_fresh_expanded_evidence")
    if any(v is None for v in evidence.get("topology_paths_only_not_walk_witnesses",{}).values()):
        return blocked("no_aligned_original_topology_path")
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    initial=pv.parse_connections(blobs["PBS/map_connections.txt"])
    if conn.read_marshal(blobs["Data/map_connections.dat"],"F12D3_CONNECTIONS")!=[encode(r) for r in initial]:
        return blocked("compiled_connections_mismatch")
    entries=tp.build(blobs,old,components,root)
    origin=chase_report["placements"][-1]
    def graph(candidate):
        return gates.access_graph(candidate,old,components,root,
            seed_cells=[(origin["map_id"],*origin["stand"])],directional=True,strict_movement=True)
    worlds,_,idx,_,reached,_=graph(blobs)
    dims={mid:(w.attrs["@width"],w.attrs["@height"]) for mid,w in worlds.items()}
    required={mapping["SINNOH_ROUTE_210"],mapping["SINNOH_ROUTE_210_SEGMENT_2"]}
    original_cells=trainers.reached_cells(idx,reached)
    current=list(initial);out=dict(blobs);attempts=[]
    # Candidate only: greedy bounded frontier expansion; not an exhaustive proof
    # of impossibility if blocked. All non-connection blobs stay byte-identical.
    def counts(ix,reach):
        return {mid:sum((mid,label) in reach for label in ix[mid].values()) for mid in required}
    for _ in range(LIMIT+1):
        if all(counts(idx,reached).values()):
            if tp.build(out,old,components,root)!=entries:
                return blocked("qa_entries_changed",attempts)
            if any(out[k]!=v for k,v in blobs.items() if k not in ("PBS/map_connections.txt","Data/map_connections.dat")):
                return blocked("baseline_modified",attempts)
            if pv.parse_connections(out["PBS/map_connections.txt"])!=current:
                return blocked("connection_roundtrip",attempts)
            return out,{"status":"F12D3_ROUTE210_CONNECTION_CANDIDATE","new_seams":len(current)-len(initial),
                "attempts":attempts,"reachable_cells":counts(idx,reached),"new_portals":0,"native_verified":False,
                "installed":False,"geometry_model":"STRICT_COMPONENT_REACHABILITY"}
        if len(attempts)>=LIMIT:break
        options=list(frontier_candidates(evidence["edge_candidates"],current,idx,reached,dims))
        if not options:break
        # Prefer edges touching a target; all other choices deterministic.
        options.sort(key=lambda p:(not bool({p[0][0],p[0][3]}&required),p[0]))
        r,lanes=options[0]
        current.append(r)
        trial=dict(out)
        trial["PBS/map_connections.txt"]=out["PBS/map_connections.txt"]+("\n# F12D3 original candidate\n"+",".join(map(str,r))+"\n").encode("ascii")
        trial["Data/map_connections.dat"]=conn.serialize([encode(x) for x in current])
        _,_,next_idx,_,next_reach,_=graph(trial)
        cells=trainers.reached_cells(next_idx,next_reach)
        if not original_cells<=cells or len(cells)<=len(trainers.reached_cells(idx,reached)):
            return blocked("candidate_did_not_expand_reach",attempts)
        out=trial;idx=next_idx;reached=next_reach
        attempts.append({"record":list(r),"witness_axes":lanes,"reachable_cells":counts(idx,reached)})
    return blocked("bounded_frontier_exhausted",attempts)
