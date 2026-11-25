"""F12D3 follow-up: investigate unidentified event groups and original edge gaps.
Audit only; no map/event replacement or source execution.
"""
import hashlib
from collections import deque
import audit_sinnoh_expansion_f03 as f03
import sinnoh_f12d3_secretpotion_audit as audit
import sinnoh_f12d_pastoria_preview as chase
import sinnoh_f12d_seams as seams
import sinnoh_f08c_expansion as f08c
import sinnoh_f10b7_field_audit as gates
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as tp

GROUPS={80:(10,11,12,13),116:(32,33,34,35)}
TARGETS={80,116}

def reached_source_ids(bound,groups,reached):
    # access_graph returns a list of cell sets per map. The graph node is
    # (map_id, integer component index), never (map_id, cell set).
    return {sid for sid,mid in bound.items()
            if any((mid,label) in reached for label in range(len(groups[mid])))}

def topology_path(edges,starts,target):
    parents={n:None for n in sorted(starts)}
    todo=deque(sorted(starts))
    while todo:
        n=todo.popleft()
        if n==target:
            path=[]
            while n is not None:path.append(n);n=parents[n]
            return path[::-1]
        for v in sorted(edges.get(n,set())):
            if v not in parents:parents[v]=n;todo.append(v)
    return None

def group_rows(report):
    rows=[]
    for m in report["maps"]:
        sid=m["source_id"]
        if sid not in GROUPS:continue
        group=[e for e in m["events"] if e["event_id"] in GROUPS[sid]]
        if tuple(e["event_id"] for e in group)!=GROUPS[sid]:
            raise ValueError("F12D3_GROUP_INVENTORY_CHANGED")
        rows.append({"source_id":sid,"map_id":m["map_id"],"events":[
            {"event_id":e["event_id"],"position":e["position"],"source_cell":e["source_cell"],
             "qa_cell":e["qa_cell"],"page_conditions":[p["shape"]["conditions"] for p in e["pages"]],
             "quest_markers":e["quest_markers"]} for e in group],
             "identity_proven":False})
    return rows

def inspect(blobs,mapping,components,chase_report,report,source,root):
    chase.validate(blobs,mapping)
    if not chase_report.get("runtime_install_enabled") or report.get("status")!="F12D3_SOURCE_GEOMETRY_AUDITED":
        raise ValueError("F12D3_FOLLOWUP_REQUIRES_AUDIT")
    before=chase.digest(blobs)
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    origin=chase_report["placements"][-1]
    worlds,tiles,idx,groups,reached,_=gates.access_graph(blobs,old,components,root,
        seed_cells=[(origin["map_id"],*origin["stand"])],directional=True,strict_movement=True)
    source_map,_,_=conn.graph(root)
    source_map={**source_map,**{r["source_id"]:r for r in f08c.rows(root)}}
    bound={sid:mapping[r["symbol"]] for sid,r in source_map.items() if r["symbol"] in old}
    reached_ids=reached_source_ids(bound,groups,reached)
    current=pv.parse_connections(blobs["PBS/map_connections.txt"])
    candidates=[];hits=[];scanned=0;events=0;pbs_hits=[];topology={}
    with pv.verified_archive(source,"maps") as z:
        index=f03.index(z)
        st=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D3_FOLLOWUP_TILES")
        source_worlds={};source_dims={}
        for name in sorted(index.values()):
            if name.casefold().startswith((pv.MAP_ROOT+"Data/").casefold()):
                m=f03.MAP_RE.fullmatch(name[len(pv.MAP_ROOT+"Data/"):])
                if not m:continue
                sid=int(m[1]);raw=pv.member(z,name);digest=hashlib.sha256(raw).hexdigest()
                if sid in source_map and digest!=source_map[sid]["sha256"]:raise ValueError("F12D3_FOLLOWUP_HASH")
                world=conn.read_marshal(raw,"F12D3_FOLLOWUP_SOURCE");scanned+=1
                for eid,e in sorted(world.attrs["@events"].items()):
                    events+=1;marks=audit.markers(e)
                    if marks:hits.append({"source_id":sid,"map_id":bound.get(sid),"event_id":eid,
                        "position":[e.attrs["@x"],e.attrs["@y"]],"markers":marks,"sha256":digest})
                source_dims[sid]=(world.attrs["@width"],world.attrs["@height"])
                if sid in bound:source_worlds[sid]=world
            elif name.lower().startswith((pv.MAP_ROOT+"PBS/").lower()) and name.lower().endswith(".txt"):
                raw=pv.member(z,name);marks=audit.tokens(raw)
                if marks:pbs_hits.append({"file":name.rsplit("/",1)[-1],"markers":marks,"sha256":hashlib.sha256(raw).hexdigest()})
        source_records=pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt"))
        for a,da,oa,b,db,ob in source_records:
            if a not in bound or b not in bound or conn.OPPOSITE.get(da)!=db:continue
            sa,sb=source_worlds[a],source_worlds[b];ma,mb=bound[a],bound[b]
            size_a=(sa.attrs["@width"],sa.attrs["@height"]);size_b=(sb.attrs["@width"],sb.attrs["@height"])
            axes=list(seams.aligned_axes(da,oa,size_a,db,ob,size_b))
            target=(ma,da,oa,mb,db,ob);installed=target in current or seams.ends(target)[1] in current
            if axes:
                topology.setdefault(a,set()).add(b);topology.setdefault(b,set()).add(a)
            record=(a,da,oa,b,db,ob)
            conflict=False
            for u,du,ou,v,dv,ov in seams.ends(record):
                for other in source_records:
                    for x,dx,ox,y,dy,oy in seams.ends(other):
                        if (x,dx)!=(u,du) or (x,dx,ox,y,dy,oy) in seams.ends(record):continue
                        if y not in source_dims:
                            conflict=True;continue
                        left={n+ou for n in seams.aligned_axes(du,ou,source_dims[u],dv,ov,source_dims[v])}
                        right={n+ox for n in seams.aligned_axes(dx,ox,source_dims[x],dy,oy,source_dims[y])}
                        if left&right:conflict=True
            allowed=[];mismatch=0;reachable_a=[];reachable_b=[]
            for n in axes:
                x=seams.point(n,da,oa,size_a);y=seams.point(n,db,ob,size_b)
                aa=gates.cell_shape(sa,st,x);bb=gates.cell_shape(sb,st,y)
                qa=gates.cell_shape(worlds[ma],tiles,x);qb=gates.cell_shape(worlds[mb],tiles,y)
                if aa!=qa or bb!=qb:mismatch+=1
                if not seams.lane_allowed(aa,bb,qa,qb,x not in idx[ma],y not in idx[mb]):continue
                allowed.append(n)
                if (ma,idx[ma][x]) in reached:reachable_a.append(n)
                if (mb,idx[mb][y]) in reached:reachable_b.append(n)
            candidates.append({"source_record":[a,da,oa,b,db,ob],"qa_record":list(target),
                "installed":installed,"source_side_conflict":conflict,"aligned_axes":len(axes),"matching_walkable_axes":allowed,
                "source_qa_mismatch_count":mismatch,"reachable_a_axes":reachable_a,"reachable_b_axes":reachable_b,
                "target_side_already_used":any((u,d) in {(ma,da),(mb,db)} for rr in current for u,d,*_ in seams.ends(rr))})
    if before!=chase.digest(blobs):raise ValueError("F12D3_FOLLOWUP_MUTATION")
    return {"status":"F12D3_EXPANDED_EVIDENCE_ONLY","source_maps_scanned":scanned,"source_events_scanned":events,
        "exact_marker_events":hits,"pbs_marker_files":pbs_hits,"unidentified_groups":group_rows(report),
        "reached_source_ids":sorted(reached_ids),"edge_candidates":candidates,
        "topology_paths_only_not_walk_witnesses":{str(s):topology_path(topology,reached_ids,s) for s in sorted(TARGETS)},
        "input_hashes":before,"baseline_maps":144,"baseline_preserved":True,"new_events":0,"new_portals":0,
        "items_granted":0,"runtime_install_enabled":False,"native_verified":False}
