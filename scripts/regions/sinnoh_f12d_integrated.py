"""Integrated F12D3J-D6 private gameplay compiler; never modifies input maps."""
import json
import hashlib
import re
import zlib
import struct
import sinnoh_f12d_corridor as corridor
import sinnoh_private_visual as pv
import sinnoh_f12d_assets as assets
import sinnoh_f12d3_secretpotion_catalogue as item_catalogue
import sinnoh_f12d3_secretpotion_audit as secret_audit
import sinnoh_f12d3_expanded_evidence as expanded_audit
import sinnoh_f12d3_original_network as original_audit
import sinnoh_f12d3_canonical_network as canonical
import sinnoh_f12d_pastoria_preview as chase
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10b_trainers as trainers
import sinnoh_connection_expansion as conn
import sinnoh_qa_teleport as tp
import sinnoh_f12b5_authored_quest as mars
import sinnoh_f12d3_gated_alignment as gated
from build_johto_events import EVENT_CLASSES,ruby,event_page

ORDER=("VALOR","VERITY","ACUITY")
# Condensed project-authored teams, not claimed as imported source teams.
LAKES={
    "VALOR":("SINNOH_VALOR_CAVERN","Saturn",("COMMANDER_SATURN","GALACTIC_SATURN","GALACTIC_ADMIN","GALACTICADMIN","SATURN"),15001,(("GOLBAT",38),("BRONZOR",38),("TOXICROAK",40))),
    "VERITY":("SINNOH_LAKE_VERITY","Mars",mars.COMMANDERS,15002,(("GOLBAT",38),("BRONZOR",38),("PURUGLY",40))),
    "ACUITY":("SINNOH_LAKE_ACUITY","Jupiter",(),15003,()),
}
def graph(data,mapping,components,root,seed,rock=(),valor_rock=(),blocked_cells=(),blocked_lanes=(),post_chase_story=False):
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    w,t,i,_,r,_=gates.access_graph(data,old,components,root,seed_cells=[seed],directional=True,strict_movement=True,rock_cells=rock,valor_rock=valor_rock,blocked_cells=blocked_cells,blocked_lanes=blocked_lanes,post_chase_story=post_chase_story)
    return w,t,trainers.reached_cells(i,r)

def add_event(data,mid,xy,key,sprite,cleared=False):
    rel="Data/Map%03d.rxdata"%mid
    world=conn.read_marshal(data[rel],"F12D_INTEGRATED_EVENT")
    events=world.attrs["@events"]
    if any((e.attrs["@x"],e.attrs["@y"])==xy for e in events.values()):raise ValueError("F12D_INTEGRATED_OCCUPIED")
    eid=max(max(events,default=0)+1,3001)
    page=event_page(script='BlueSinnohF12DIntegrated.interact("'+key+'")',sprite=sprite)
    pages=[page]
    if cleared:
        off=event_page(script="nil")
        off.attrs["@through"]=True
        off.attrs["@condition"].attrs["@self_switch_valid"]=True
        pages.append(off)
    events[eid]=ruby("RPG::Event",id=eid,name=("SN_F12D_INTEGRATED_"+key).encode("ascii"),x=xy[0],y=xy[1],pages=pages)
    out=dict(data);out[rel]=conn.serialize(world,EVENT_CLASSES)
    del events[eid]
    if conn.serialize(world,EVENT_CLASSES)!=data[rel]:raise ValueError("F12D_INTEGRATED_EVENT_DELTA")
    return out,{"map_id":mid,"event_id":eid,"position":list(xy)}

def protected(data,mapping,components,root):
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    result={tuple(r[3]) for r in tp.build(data,old,components,root) if r[3]}
    for mid in mapping.values():
        w=conn.read_marshal(data["Data/Map%03d.rxdata"%mid],"F12D_INTEGRATED_PROTECT")
        for e in w.attrs["@events"].values():
            a=e.attrs;result.add((mid,a["@x"],a["@y"]))
            tr,_=conn.classify_transfer(e)
            if tr:result.add((tr[2],tr[3],tr[4]))
    return result

def placement(data,mapping,components,root,mid,seed,rock=(),valor_rock=(),post_chase_story=False):
    worlds,tiles,reached=graph(data,mapping,components,root,seed,rock,valor_rock,post_chase_story=post_chase_story)
    if mid not in worlds:return None
    world=worlds[mid];w,h=world.attrs["@width"],world.attrs["@height"]
    forbid=protected(data,mapping,components,root)|{seed}
    if mid==mapping.get("SINNOH_VALOR_CAVERN"):
        forbid.add((mid,22,36))  # Preserve the exact original cave threshold.
    candidates={(x,y) for m,x,y in reached if m==mid and 1<x<w-2 and 1<y<h-2 and
        (m,x,y) not in forbid and (gates.cell_shape(world,tiles,(x,y))["ordinary_walkable"] or (m,x,y) in valor_rock)}
    for xy in sorted(candidates,key=lambda q:(abs(q[0]-w//2)+abs(q[1]-h//2),q)):
        stands=[q for q in tp.neighbours(*xy) if (mid,*q) in reached and (mid,*q) not in forbid]
        if not stands:continue
        trial,loc=add_event(data,mid,xy,"PLACEMENT_PROBE","")
        _,_,after=graph(trial,mapping,components,root,seed,rock,valor_rock,post_chase_story=post_chase_story)
        if reached-{(mid,*xy)}<=after:
            for q in sorted(stands):
                if (mid,*q) in after:return xy,q
    return None

def valor_rock_reference(blobs,mapping,source):
    """Pinned source 217 only; matching local Rock stacks, never conversion."""
    mid=mapping["SINNOH_VALOR_CAVERN"]
    world=conn.read_marshal(blobs["Data/Map%03d.rxdata"%mid],"F12D_VALOR_QA")
    tiles=conn.read_marshal(blobs["Data/Tilesets.rxdata"],"F12D_VALOR_TILES")
    with pv.verified_archive(source,"maps") as z:
        raw=pv.member(z,pv.MAP_ROOT+"Data/Map217.rxdata")
        if hashlib.sha256(raw).hexdigest()!="e7d80aa507ee7112ccf301d5cc441ad8184a50054a7cca5dcc027dd544cc35b6":
            raise ValueError("F12D_VALOR_SOURCE_HASH")
        src=conn.read_marshal(raw,"F12D_VALOR_SOURCE")
        st=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D_VALOR_SOURCE_TILES")
    ss,sh=corridor.grid(src,st);qs,qh=corridor.grid(world,tiles)
    if set(ss)!=set(qs):raise ValueError("F12D_VALOR_DIMENSIONS")
    w,h=world.attrs["@width"],world.attrs["@height"]
    guard=pv.movement_masks(blobs,mapping,extra_symbols={"SINNOH_VALOR_CAVERN"})[mid]
    def zero_priority(a,ts,stack):
        data=ts[a.attrs["@tileset_id"]].attrs["@priorities"].data
        return all(struct.unpack_from("<H",data,20+2*k)[0]==0 for k in stack if k)
    cells={(mid,x,y):qs[x,y] for x,y in qs if 0<x<w-1 and 0<y<h-1 and
        sh[x,y]==qh[x,y] and 4 in qh[x,y][1] and all(k in (0,4) for k in qh[x,y][1])
        and all(k==0 for k in qh[x,y][0]) and guard[y][x]=="." and
        zero_priority(src,st,ss[x,y]) and zero_priority(world,tiles,qs[x,y])}
    door=(22,36)
    def priorities(a,ts,stack):
        data=ts[a.attrs["@tileset_id"]].attrs["@priorities"].data
        return tuple(struct.unpack_from("<H",data,20+2*k)[0] for k in stack if k)
    if (ss.get(door)==(6833,7001,0) and sh.get(door)==((0,0),(4,0)) and qh.get(door)==sh[door] and
        priorities(src,st,ss[door])==(0,1) and priorities(world,tiles,qs[door])==(0,1) and
        guard[36][22]=="." and (mid,22,35) in cells):
        cells[mid,*door]=qs[door]
    return cells

# Candidate aquatic paths never enter the dry progression graph. RMXP
# source water has mask 15; only native Surf may override that water mask.
# Match the original and remapped tile attributes, not numeric tile IDs.
def lake_surface_mode(shape,priorities):
    masks,tags=shape
    if corridor.ordinary(shape):return "walk"
    if len(tags)==1 and tags[0] in (5,6) and masks==(15,) and priorities==(0,):
        return "surf"
    return None

def lake_surface_path(modes,start,goal,allow_surf=False):
    from collections import deque
    if modes.get(start)!="walk" or modes.get(goal)!="walk":return None
    allowed={"walk","surf"} if allow_surf else {"walk"}
    previous={start:None};queue=deque([start])
    while queue:
        q=queue.popleft()
        if q==goal:break
        for n in sorted(tp.neighbours(*q)):
            if n not in previous and modes.get(n) in allowed:
                previous[n]=q;queue.append(n)
    if goal not in previous:return None
    path=[];q=goal
    while q is not None:path.append(q);q=previous[q]
    return list(reversed(path))

def lake_surf_geometry(data,mapping,source,root,previews):
    catalog,_,_=conn.graph(root)
    targets={215:("SINNOH_LAKE_VALOR",(45,6),(26,24)),
        161:("SINNOH_LAKE_ACUITY",(8,49),tuple(previews["ACUITY"]["stand"]) if "ACUITY" in previews else None)}
    hms=json.loads((root/"data/regions/sinnoh-hms-s16.json").read_text("utf-8"))
    hm=next(r for r in hms["hms"] if r["action"]=="SURF")
    if (hm["badge"],hm["hm_item"])!=("FEN","HM03"):
        raise ValueError("F12D_SURF_CONTRACT_CHANGED")
    result={"required_badge":"FEN","required_item":"HM03","local_pickup_required":True,
        "compatible_party_required":True,"local_pickup_verified":hm["local_receipt_verified"] is True,
        "native_surf_movement_verified":False,"activation_allowed":False,"maps":{}}
    qt=conn.read_marshal(data["Data/Tilesets.rxdata"],"F12D_SURF_QA_TILES")
    with pv.verified_archive(source,"maps") as z:
        st=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D_SURF_SOURCE_TILES")
        for sid,(symbol,start,goal) in targets.items():
            if not goal or symbol not in mapping:continue
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=catalog[sid]["sha256"]:raise ValueError("F12D_SURF_SOURCE_HASH")
            sw=conn.read_marshal(raw,"F12D_SURF_SOURCE")
            mid=mapping[symbol];qw=conn.read_marshal(data["Data/Map%03d.rxdata"%mid],"F12D_SURF_QA")
            ss,sh=corridor.grid(sw,st);qs,qh=corridor.grid(qw,qt)
            if set(ss)!=set(qs):raise ValueError("F12D_SURF_DIMENSIONS")
            def pri(world,tiles,stack):
                table=tiles[world.attrs["@tileset_id"]].attrs["@priorities"].data
                return tuple(struct.unpack_from("<H",table,20+2*k)[0] for k in stack if k)
            occupied={(e.attrs["@x"],e.attrs["@y"]) for e in qw.attrs["@events"].values()}
            modes={}
            for q in ss:
                if q in occupied or sh[q]!=qh[q]:continue
                sp=pri(sw,st,ss[q]);qp=pri(qw,qt,qs[q])
                if sp!=qp:continue
                mode=lake_surface_mode(sh[q],sp)
                if mode:modes[q]=mode
            path=lake_surface_path(modes,start,goal,True)
            dry=lake_surface_path(modes,start,goal,False)
            row={"source_id":sid,"map_id":mid,"start":list(start),"goal":list(goal),
                "source_sha256":catalog[sid]["sha256"],"matched_water_cells":sum(v=="surf" for v in modes.values()),
                "dry_path":dry is not None,"surf_candidate":path is not None,
                "terrain_changes":0,"native_verified":False}
            if path:
                row.update(steps=len(path)-1,water_steps=sum(modes[q]=="surf" for q in path),
                    transitions=[{"from":list(a),"to":list(b),"mode":modes[b]} for a,b in zip(path,path[1:]) if modes[a]!=modes[b]],
                    path_sha256=hashlib.sha256(json.dumps(path,separators=(",",":")).encode("ascii")).hexdigest())
            result["maps"][str(sid)]=row
    return result

def lake_contract(key,types,species,existing):
    symbol,name,aliases,version,team=LAKES[key]
    if not team:return {"symbol":symbol,"name":name,"team":[],"kind":"scene"}
    kind=mars.choose(types,aliases)
    if not kind or any(s not in species for s,l in team) or (kind,name,version) in existing:return None
    return {"symbol":symbol,"name":name,"type":kind,"version":version,"team":[list(p) for p in team],"kind":"battle"}

def ruby_hash(mapping):
    return "{"+",".join(json.dumps(k)+"=>"+json.dumps(v) for k,v in sorted(mapping.items()))+"}"

# Exact misnumbered original transfer records independently recovered from
# F03 job 138719583390 and the pinned source archive (no donor code execution).
# These are references to the source, not local MapIDs or arbitrary new warps.
LAKE_REFERENCE_REPAIRS={
    (214,6):(26,215,(45,22),(45,6)),
    (214,7):(26,215,(45,23),(45,7)),
    (215,2):(25,214,(46,6),(46,22)),
    (215,3):(25,214,(46,7),(46,23)),
}
LAKE_STALE_DEMO_MAPS={
    25:("067f4510f90050b44f1db93be6460f5939e1340eaf278eb2788af61c32e791c1",5),
    26:("8f14169c7f6b6b6ad9f03ce55bcc9ab7a33e86cb8a5e6f275f7e2f41880387e6",3),
}

def original_lake_reference_destination(sid,eid,transfer,stale):
    row=LAKE_REFERENCE_REPAIRS.get((sid,eid))
    if row is None:return transfer[2]
    wrong,right,xy,landing=row
    x,y,t,dx,dy,_,_=transfer
    if (t,(x,y),(dx,dy))!=(wrong,xy,landing) or wrong not in stale:
        raise ValueError("F12D_LAKE_STALE_REFERENCE_CHANGED")
    if 0<=dx<stale[wrong]["@width"] and 0<=dy<stale[wrong]["@height"]:
        raise ValueError("F12D_LAKE_STALE_REFERENCE_NOT_OUT_OF_BOUNDS")
    return right

def original_lake_candidates(data,mapping,components,root,source,rock,valor_rock,seed):
    import copy
    from build_johto_events import command
    from sinnoh_f08c_expansion import rows
    catalog,_,_=conn.graph(root)
    catalog={**catalog,**{r["source_id"]:r for r in rows(root)}}
    bound={sid:mapping[r["symbol"]] for sid,r in catalog.items() if r["symbol"] in mapping}
    focus={159,161,162,195,196,197,214,215,216,217}
    result={"source_entries":[],"missing_dependencies":[],"candidate_records":[],"accepted_records":[]}
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    worlds,tiles,ix,_,_,_=gates.access_graph(data,old,components,root,seed_cells=[seed],
        directional=True,strict_movement=True,rock_cells=rock,valor_rock=valor_rock,post_chase_story=True)
    staged={}
    with pv.verified_archive(source,"maps") as z:
        st=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D_LAKE_SOURCE_TILES")
        infos=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/MapInfos.rxdata"),"F12D_LAKE_SOURCE_INFOS")
        donor={};hashes={};stale={}
        for sid,(digest,tileset) in LAKE_STALE_DEMO_MAPS.items():
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError("F12D_LAKE_STALE_DEMO_HASH")
            w=conn.read_marshal(raw,"F12D_LAKE_STALE_DEMO").attrs
            if (w["@width"],w["@height"],w["@tileset_id"])!=(20,15,tileset) or conn.static_targets(w["@events"])!={23} or infos[sid].attrs["@parent_id"]!=1:
                raise ValueError("F12D_LAKE_STALE_DEMO_IDENTITY")
            stale[sid]=w
        for sid in sorted(focus):
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            digest=hashlib.sha256(raw).hexdigest()
            if sid not in catalog or digest!=catalog[sid]["sha256"]:raise ValueError("F12D_LAKE_SOURCE_HASH")
            hashes[sid]=digest;donor[sid]=conn.read_marshal(raw,"F12D_LAKE_SOURCE_MAP")
        missing=set()
        for sid in sorted(focus):
            w=donor[sid]
            for eid,e in sorted(w.attrs["@events"].items()):
                targets=conn.static_targets({eid:e})
                if not targets:continue
                missing.update(t for t in targets if t not in bound)
                row={"source_id":sid,"event_id":eid,"target_source_ids":sorted(targets),
                    "source_position":[e.attrs["@x"],e.attrs["@y"]],"source_map_sha256":hashes[sid]}
                result["source_entries"].append(row)
                if len(targets)!=1:row["reason"]="ambiguous_targets";continue
                original_dst=next(iter(targets))
                repair=LAKE_REFERENCE_REPAIRS.get((sid,eid))
                dst=repair[1] if repair else original_dst
                if dst not in bound:row["reason"]="unmapped_source_dependency";continue
                if (sid,dst) not in gates.ORIGINAL_LAKE_PAIRS:
                    row["reason"]="outside_reciprocal_lake_scope";continue
                cloned=copy.deepcopy(e);pages=cloned.attrs.get("@pages",[])
                if len(pages)!=1:row["reason"]="conditional_or_multiple_pages";continue
                page=pages[0].attrs
                ops=page.get("@list",[]);scripts=[q for q in ops if q.attrs.get("@code") in (355,655)]
                call=None
                if scripts:
                    q=scripts[0].attrs;args=q.get("@parameters",[])
                    if len(scripts)!=1 or q.get("@code")!=355 or q.get("@indent")!=0 or len(args)!=1 or not isinstance(args[0],bytes):
                        row["reason"]="unknown_source_script_shape";continue
                    name=args[0].strip()
                    if name.endswith(b"()"):name=name[:-2]
                    row["source_script_sha256"]=hashlib.sha256(args[0]).hexdigest()
                    if name not in gates.ORIGINAL_CAVE_CALLS or ops.index(scripts[0])>next((i for i,op in enumerate(ops) if op.attrs.get("@code")==201),-1):
                        row["reason"]="unrecognised_source_transition_script";continue
                    call=name;row["canonical_transition"]=name.decode("ascii")
                    page["@list"]=[op for op in ops if op is not scripts[0]]
                transfer,why=conn.classify_transfer(cloned)
                if not transfer:row["reason"]=why;continue
                x,y,t,dx,dy,direction,fade=transfer
                if t!=original_dst or original_lake_reference_destination(sid,eid,transfer,stale)!=dst:
                    row["reason"]="source_destination_mismatch";continue
                if repair:
                    row["reference_repair"]={"original_target_source_id":original_dst,"resolved_target_source_id":dst,"reason":"pinned_out_of_bounds_demo_reference_and_reciprocal_corridor"}
                a,b=bound[sid],bound[dst];xy=(x,y);landing=(dx,dy)
                row["from"]=[a,x,y];row["to"]=[b,dx,dy]
                if a not in worlds or b not in worlds:row["reason"]="missing_local_map";continue
                wa,wb=worlds[a],worlds[b]
                def exact_ground(source_world,qa_world,mid,point):
                    sa=gates.cell_shape(source_world,st,point);qa=gates.cell_shape(qa_world,tiles,point)
                    return sa==qa and (qa.get("ordinary_walkable") is True or (mid,*point) in valor_rock)
                if not exact_ground(w,wa,a,xy) or not exact_ground(donor[dst],wb,b,landing):
                    row["reason"]="source_or_destination_ground_unproved";continue
                if landing not in ix[b] or not any(n in ix[a] for n in tp.neighbours(*xy)):
                    row["reason"]="local_component_unproved";continue
                if any((v.attrs["@x"],v.attrs["@y"])==xy for v in wa.attrs["@events"].values()):
                    row["reason"]="existing_event_preserved";continue
                key=(sid,dst);staged.setdefault(key,[]).append((row,eid,call,page["@trigger"],direction,fade))
                row["reason"]="exact_original_candidate"
        for sid in sorted(missing):
            info=infos.get(sid);path=pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid
            exists=path in z.namelist()
            entry={"source_id":sid,"present_in_archive":exists,"mapped":False}
            if info:
                name=info.attrs.get("@name",b"")
                if isinstance(name,bytes):entry["name"]=name.decode("utf-8","replace")[:100]
            if exists:
                raw=pv.member(z,path);world=conn.read_marshal(raw,"F12D_LAKE_DEPENDENCY")
                entry.update(sha256=hashlib.sha256(raw).hexdigest(),
                    dimensions=[world.attrs["@width"],world.attrs["@height"]],
                    original_targets=sorted(conn.static_targets(world.attrs["@events"])))
            if sid in stale:entry["classification"]="STALE_DEMO_INTERIOR_NOT_A_LAKE_DEPENDENCY"
            if sid==9:entry["classification"]="STALE_DEMO_REFERENCE_TO_VERITY_CAVERN_NOT_INSTALLED"
            result["missing_dependencies"].append(entry)
    # No arbitrary landing/door shift. Require both directions of an exact
    # original pair; never attach the nonreciprocal source 216 variant.
    trial=dict(data)
    for sid,dst in sorted(staged):
        if (dst,sid) not in staged:continue
        for row,eid,call,trigger,direction,fade in staged[sid,dst]:
            a,x,y=row["from"];b,dx,dy=row["to"]
            rel="Data/Map%03d.rxdata"%a
            world=conn.read_marshal(trial[rel],"F12D_ORIGINAL_LAKE_TRIAL")
            events=world.attrs["@events"]
            if any((e.attrs["@x"],e.attrs["@y"])==(x,y) for e in events.values()):continue
            p=event_page(warp=(b,dx,dy),touch=trigger!=0);p.attrs["@trigger"]=trigger;p.attrs["@through"]=True
            transfer=p.attrs["@list"][0];transfer.attrs["@indent"]=1;transfer.attrs["@parameters"][4:6]=[direction,fade]
            guard=command(111,12,("BlueSinnohF12DIntegrated.original_lake_entry_allowed?(%d,%d)"%(sid,dst)).encode("ascii"))
            body=[guard]
            if call:
                q=command(355,call);q.attrs["@indent"]=1;body.append(q)
            ending=command(0);ending.attrs["@indent"]=1
            p.attrs["@list"]=body+[transfer,ending,command(412),command(0)]
            new_id=max(max(events,default=0)+1,3001)
            e=ruby("RPG::Event",id=new_id,name=("SN_F12D_ORIGINAL_LAKE_%d_%d_%d"%(sid,eid,dst)).encode("ascii"),x=x,y=y,pages=[p])
            if not gates.verified_original_lake_entry(e,a,mapping):raise ValueError("F12D_ORIGINAL_LAKE_GATE")
            events[new_id]=e;trial[rel]=conn.serialize(world,EVENT_CLASSES)
            result["candidate_records"].append({**row,"event_id_local":new_id})
    if tp.build(trial,old,components,root)!=tp.build(data,old,components,root):
        result["reason"]="qa_entries_changed";return data,result
    result["reason"]="complete_sequence_required"
    return trial,result

def recover_lake_seams(data,mapping,components,root,expanded,seed,previews,rock,valor_rock,surf_geometry=None):
    from sinnoh_f12d3_alternate_route212 import reserved
    import sinnoh_f12d3_route210_recovery as recovery
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    edge_sink={}
    worlds,_,index,_,_,_=gates.access_graph(data,old,components,root,seed_cells=[seed],
        directional=True,strict_movement=True,rock_cells=rock,valor_rock=valor_rock,
        post_chase_story=True,edge_sink=edge_sink)
    dims={m:(w.attrs["@width"],w.attrs["@height"]) for m,w in worlds.items()}
    current=pv.parse_connections(data["PBS/map_connections.txt"])
    if conn.read_marshal(data["Data/map_connections.dat"],"F12D_LAKE_CONNECTIONS")!=[recovery.encode(r) for r in current]:
        raise ValueError("F12D_LAKE_COMPILED_CONNECTIONS_MISMATCH")
    edges={u:{(v,(),True) for v in vs} for u,vs in edge_sink.items()}
    eligible=[]
    for e in expanded["edge_candidates"]:
        r=tuple(e["qa_record"])
        if r[0] not in index or r[3] not in index or e["installed"] or e["source_side_conflict"] or reserved(r,current,dims):continue
        if e["source_qa_mismatch_count"] or not e["matching_walkable_axes"]:continue
        lanes=gated.all_lanes(r,index,dims)
        if [n for n,_,_ in lanes]!=e["matching_walkable_axes"]:continue
        eligible.append(r)
        for _,a,b in lanes:
            u=(r[0],index[r[0]][a]);v=(r[3],index[r[3]][b])
            edges.setdefault(u,set()).add((v,r,False));edges.setdefault(v,set()).add((u,r,False))
    report={"eligible_original_seams":len(eligible),"legs":{},"accepted_records":[],"new_portals":0,"terrain_changes":0,
        "existing_directed_edges":sum(len(v) for v in edge_sink.values()),
        "portal_arrival_model":"ACTION_THROUGH_AND_DIRECTED_TOUCH_LANDING"}
    def node(q):
        label=index.get(q[0],{}).get(tuple(q[1:]))
        return (q[0],label) if label is not None else None
    # Conditional witnesses are an independent graph: never install these
    # edges in the dry graph or accept them as native movement evidence.
    conditional={k:set(v) for k,v in edges.items()}
    surf_edges=[]
    for row in (surf_geometry or {}).get("maps",{}).values():
        if not row.get("surf_candidate") or not row.get("water_steps"):continue
        a=node((row["map_id"],*row["start"]));b=node((row["map_id"],*row["goal"]))
        if a is None or b is None or a==b:continue
        conditional.setdefault(a,set()).add((b,(),True))
        conditional.setdefault(b,set()).add((a,(),True))
        surf_edges.append({"map_id":row["map_id"],"from":row["start"],"to":row["goal"],"requires":"SINNOH_HM03_FEN_LOCAL_RECEIPT_COMPATIBLE_PARTY_NATIVE_SURF"})
    conditional_legs={};prior=seed
    for key in ORDER:
        loc=previews.get(key)
        goal=(loc["map_id"],*loc["stand"]) if loc else None
        a=node(prior) if prior else None;b=node(goal) if goal else None
        distances,_=original_audit.component_paths(conditional,[a]) if a is not None else ({},{})
        conditional_legs[key]={"candidate_reachable":b is not None and b in distances,"native_verified":False}
        prior=goal
    report["conditional_surf"]={"edges":surf_edges,"legs":conditional_legs,"activation_allowed":False}
    added=[];predecessor=seed;complete=True
    for key in ORDER:
        loc=previews.get(key)
        if not loc:
            report["legs"][key]={"reason":"missing_local_position"};complete=False;predecessor=None;continue
        goal=(loc["map_id"],*loc["stand"])
        a=node(predecessor) if predecessor is not None else None;b=node(goal)
        predecessor=goal
        if a is None or b is None:
            report["legs"][key]={"reason":"missing_component"};complete=False;continue
        d,p=original_audit.component_paths(edges,[a])
        if b not in d:
            frontier={u[0] for u in d}
            report["legs"][key]={"reason":"no_original_dry_seam_path",
                "reachable_maps":sorted(frontier),"reachable_components":len(d),
                "destination_components_reached":sorted(label for m,label in d if m==goal[0]),
                "unreached_adjacent_original_records":[list(r) for r in eligible if (r[0] in frontier)!=(r[3] in frontier)]}
            complete=False;continue
        candidate=[r for _,_,r,installed in original_audit.trace(b,p) if not installed]
        report["legs"][key]={"minimum_new_original_seams":d[b][0],"records":[list(r) for r in candidate]}
        for r in candidate:
            if r in added:continue
            if reserved(r,current+added,dims):
                complete=False;report["legs"][key]["reason"]="candidate_interval_conflict";break
            added.append(r)
    if not complete or len(added)>12:
        report["reason"]="complete_original_sequence_not_proved" if not complete else "original_seam_budget_exceeded"
        return data,[],report
    trial=dict(data)
    if added:
        trial["PBS/map_connections.txt"]=data["PBS/map_connections.txt"]+("\n# F12D verified original lake seams\n"+"\n".join(",".join(map(str,r)) for r in added)+"\n").encode("ascii")
        trial["Data/map_connections.dat"]=conn.serialize([recovery.encode(r) for r in current+added])
    if tp.build(trial,old,components,root)!=tp.build(data,old,components,root):
        report["reason"]="qa_entries_changed";return data,[],report
    predecessor=seed
    for key in ORDER:
        loc=previews[key];goal=(loc["map_id"],*loc["stand"])
        _,_,prior=graph(data,mapping,components,root,predecessor,rock,valor_rock,post_chase_story=True)
        _,_,after=graph(trial,mapping,components,root,predecessor,rock,valor_rock,post_chase_story=True)
        if not prior<=after or goal not in after:
            report["reason"]="serialized_original_sequence_not_proved";return data,[],report
        predecessor=goal
    report["accepted_records"]=[list(r) for r in added]
    report["reason"]="complete_original_sequence_fixture_proved"
    return trial,added,report

def compile_story(blobs,mapping,components,cr,expanded,original,source,root,types,species,items,existing):
    chase.validate(blobs,mapping);before=chase.digest(blobs)
    prepared={}
    report=canonical.inspect(blobs,mapping,components,cr,expanded,original,source,root,
        directional_repair=True,rock_repair=True,rock_network=True,integrated_payload=prepared)
    sprites=assets.build()
    result={"geometry":report,"status":"F12D_INTEGRATED_BLOCKED","mission_prepared":False,
        "authored_sprite_hashes":{k:hashlib.sha256(v).hexdigest() for k,v in sprites.items()},
        "lake_contracts":{k:lake_contract(k,types,species,existing) for k in ORDER},
        "lake_placements":{},"lake_local_previews":{},"runtime_install_enabled":False,"native_verified":False,"new_maps":0,"new_portals":0}
    origin=cr["placements"][-1];seed=(origin["map_id"],*origin["stand"])
    # Compile local lake event previews independently. QA entry seeds
    # are local placement evidence, not proof of progression travel.
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    entries=tp.build(blobs,old,components,root)
    valor_rock=valor_rock_reference(blobs,mapping,source)
    threshold=(mapping["SINNOH_VALOR_CAVERN"],22,36)
    result["valor_rock_threshold_cells"]=int(threshold in valor_rock)
    result["valor_rock_reference_cells"]=len(valor_rock)-result["valor_rock_threshold_cells"]
    for key in ORDER:
        contract=result["lake_contracts"][key]
        if not contract or contract["symbol"] not in mapping:continue
        mid=mapping[contract["symbol"]]
        local_seed=next((tuple(r[3]) for r in entries if r[3] and r[3][0]==mid),None)
        # Saturn is authorial, not pinned to a donor NPC coordinate. Use
        # the exact original cave entrance component, not an isolated QA spawn.
        # Preserve the QA teleport itself and never open any new cave tile.
        entry_seed=threshold if key=="VALOR" and threshold in valor_rock else local_seed
        if entry_seed:
            local=placement(blobs,mapping,components,root,mid,entry_seed,valor_rock=valor_rock)
            if local:
                preview,loc=add_event(blobs,mid,local[0],key,"SNQA_F12D_"+key)
                loc.update(stand=list(local[1]),qa_seed=list(local_seed) if local_seed else None,
                    placement_seed=list(entry_seed),placement_policy="ORIGINAL_CAVE_ENTRY_COMPONENT" if key=="VALOR" and entry_seed==threshold else "LOCAL_QA_COMPONENT",
                    walk_from_predecessor_proved=False,
                    candidate_map_sha256=hashlib.sha256(preview["Data/Map%03d.rxdata"%mid]).hexdigest())
                result["lake_local_previews"][key]=loc
        pos=placement(blobs,mapping,components,root,mid,seed,valor_rock=valor_rock)
        if pos:result["lake_placements"][key]={"map_id":mid,"position":list(pos[0]),"stand":list(pos[1]),"from_chase_only":True}
    if not prepared:
        result["reason"]="geometry_or_four_cell_cut_unproved";return {},result,b""
    if "SECRETPOTION" not in items:
        result["reason"]="local_secretpotion_catalog_missing";return {},result,b""
    opened=prepared["open_maps"];rock=prepared["rock_cells"];mid=prepared["cut_map_id"]
    value=placement(opened,mapping,components,root,origin["map_id"],seed,rock)
    if not value:result["reason"]="cynthia_no_noncut_position";return {},result,b""
    xy,stand=value
    out,loc=add_event(opened,origin["map_id"],xy,"CYNTHIA","SNQA_F12D_CYNTHIA")
    loc["stand"]=list(stand);locations={"CYNTHIA":loc};ducks=[]
    for i,xy in enumerate(prepared["cut_positions"],1):
        key="PSYDUCK_"+str(i)
        out,duck=add_event(out,mid,xy,key,"SNQA_F12D_PSYDUCK",cleared=True)
        locations[key]=duck;ducks.append(duck)
    _,_,baseline=graph(blobs,mapping,components,root,seed)
    _,_,closed=graph(out,mapping,components,root,seed,rock)
    town=mapping["SINNOH_CELESTIC_TOWN"];targets={(mid,*xy) for xy in prepared["exit_cells"]}
    removed={(loc["map_id"],*loc["position"])}
    if not (baseline-removed<=closed and not targets&closed and not any(p[0]==town for p in closed) and
            (loc["map_id"],*loc["stand"]) in closed and
            any((mid,*q) in closed for d in ducks for q in tp.neighbours(*d["position"]))):
        result["reason"]="final_mission_graph_failed";return {},result,b""
    reopened=dict(out);rel="Data/Map%03d.rxdata"%mid
    world=conn.read_marshal(reopened[rel],"F12D_INTEGRATED_REOPEN")
    for d in ducks:del world.attrs["@events"][d["event_id"]]
    reopened[rel]=conn.serialize(world,EVENT_CLASSES)
    _,_,restored=graph(reopened,mapping,components,root,seed,rock)
    if not targets<=restored or not any(p[0]==town for p in restored):
        result["reason"]="final_reopen_failed";return {},result,b""
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    if tp.build(out,old,components,root)!=tp.build(blobs,old,components,root):
        result["reason"]="qa_entries_changed";return {},result,b""
    specs={};pbs=[];lake_seed=min(q for q in restored if q[0]==town);lake_ready=[]
    result["lake_sequence_seed"]=list(lake_seed)
    result["lake_sequence_checks"]={}
    # Authorial local HM03 pickup: reachable after the existing Psyduck gate.
    # Do not move a QA seed, add a warp, or change terrain.
    pickup=placement(reopened,mapping,components,root,town,lake_seed,rock)
    result["surf_pickup"]={"prepared":False,"authorial":True,"native_verified":False,"item":"HM03","badge":"FEN"}
    if pickup:
        xy,stand=pickup
        trial,loc=add_event(reopened,town,xy,"SURF_HM03","SNQA_F12D_CYNTHIA")
        if tp.build(trial,old,components,root)==entries:
            closed_trial,closed_loc=add_event(out,town,xy,"SURF_HM03","SNQA_F12D_CYNTHIA")
            if closed_loc==loc:
                reopened=trial;out=closed_trial;loc["stand"]=list(stand);locations["SURF_HM03"]=loc
                result["surf_pickup"].update(prepared=True,location=loc)
    # All three legs must be proved before any original seam is staged.
    original_trial,entry_report=original_lake_candidates(reopened,mapping,components,root,source,rock,valor_rock,lake_seed)
    surf_geometry=lake_surf_geometry(reopened,mapping,source,root,result["lake_local_previews"])
    recovered,lake_seams,lake_recovery=recover_lake_seams(original_trial,mapping,components,root,expanded,lake_seed,result["lake_local_previews"],rock,valor_rock,surf_geometry)
    result["lake_original_seam_recovery"]=lake_recovery
    result["lake_original_entries"]=entry_report
    result["lake_surf_geometry"]=surf_geometry
    accepted_entries=[]
    if lake_recovery.get("reason")=="complete_original_sequence_fixture_proved":
        accepted_entries=entry_report["candidate_records"] if original_trial!=reopened else []
        # Reapply only the new original portals to the still-closed mission
        # maps; never copy the reopened Psyduck map wholesale.
        for row in accepted_entries:
            a,x,y=row["from"];rel="Data/Map%03d.rxdata"%a
            before_world=conn.read_marshal(out[rel],"F12D_LAKE_CLOSED_MAP")
            after_world=conn.read_marshal(recovered[rel],"F12D_LAKE_OPEN_MAP")
            eid=row["event_id_local"]
            if eid in before_world.attrs["@events"]:raise ValueError("F12D_LAKE_EVENT_COLLISION")
            before_world.attrs["@events"][eid]=after_world.attrs["@events"][eid]
            out[rel]=conn.serialize(before_world,EVENT_CLASSES)
        entry_report["accepted_records"]=accepted_entries
        for path in ("PBS/map_connections.txt","Data/map_connections.dat"):
            out[path]=recovered[path]
        reopened=recovered
    # Independent physical legs are useful for implementing all three at once.
    # They never grant a sequential payload without the actual predecessor.
    result["lake_independent_legs"]={}
    predecessor=lake_seed
    for key in ORDER:
        preview=result["lake_local_previews"].get(key)
        if preview is None:
            result["lake_independent_legs"][key]={"reason":"local_position_missing"}
            predecessor=None;continue
        if predecessor is not None:
            _,_,cells=graph(reopened,mapping,components,root,predecessor,rock,valor_rock,post_chase_story=True)
            goal=(preview["map_id"],*preview["stand"])
            result["lake_independent_legs"][key]={"from":list(predecessor),"to":list(goal),
                "reachable":goal in cells,"target_map_reachable_cells":sum(q[0]==goal[0] for q in cells)}
        else:
            result["lake_independent_legs"][key]={"reason":"predecessor_position_missing"}
        predecessor=(preview["map_id"],*preview["stand"])
    for key in ORDER:
        contract=result["lake_contracts"][key]
        if not contract or contract["symbol"] not in mapping:
            result["lake_sequence_checks"][key]={"reason":"missing_contract_or_map"};break
        lm=mapping[contract["symbol"]]
        pos=placement(reopened,mapping,components,root,lm,lake_seed,rock,valor_rock,post_chase_story=True)
        if not pos:
            result["lake_sequence_checks"][key]={"from":list(lake_seed),"map_id":lm,"reason":"no_proven_reachable_noncut_position"};break
        xy,stand=pos;sprite="SNQA_F12D_"+key
        result["lake_sequence_checks"][key]={"from":list(lake_seed),"map_id":lm,"stand":list(stand),"walk_from_predecessor_proved":True}
        out,loc=add_event(out,lm,xy,key,sprite)
        reopened,_=add_event(reopened,lm,xy,key,sprite)
        loc["stand"]=list(stand);locations[key]=loc;lake_seed=(lm,*stand);lake_ready.append(key)
        if contract["kind"]=="battle":
            spec=[contract["type"],contract["name"],contract["version"],lm,contract["team"]]
            specs[key]=spec
            pbs.append("[%s,%s,%d]\nLoseText = Voce venceu!\n%s\n"%(spec[0],spec[1],spec[2],"\n".join("Pokemon = %s,%d"%tuple(p) for p in spec[4])))
        result["lake_placements"][key]=loc
    if (lake_seams or accepted_entries) and lake_ready!=list(ORDER):
        result["reason"]="original_lake_sequence_events_not_proved";return {},result,b""
    # Staging only until the private engine, sprites and pre-chase seam gate pass.
    template=(root/"scripts/regions/SinnohF12DIntegrated.rb").read_text("utf-8")
    literal={k:[v["map_id"],*v["position"],v["event_id"]] for k,v in locations.items()}
    worlds,_,index,_,_,_=gates.access_graph(opened,old,components,root,seed_cells=[seed],
        directional=True,strict_movement=True,rock_cells=rock)
    dims={m:(w.attrs["@width"],w.attrs["@height"]) for m,w in worlds.items()}
    def lane_keys(records):
        keys=[]
        for rec in records:
            for _,a,b in gated.all_lanes(rec,index,dims):
                left=[rec[0],*a];right=[rec[3],*b]
                keys.extend([left+right,right+left])
        return sorted(keys)
    edits=sorted([row["map_id"],*row["position"]] for row in prepared["edits"])
    chase_lanes=lane_keys(prepared["connections"]);celestic_lanes=lane_keys([prepared["exit_record"]])
    # Gate every physically aligned coordinate of a new original lake seam,
    # not just dry model lanes, to prevent pre-SecretPotion bypass.
    if lake_seams:
        import sinnoh_f12d_seams as seams
        for a,da,oa,b,db,ob in lake_seams:
            for n in seams.aligned_axes(da,oa,dims[a],db,ob,dims[b]):
                left=[a,*seams.point(n,da,oa,dims[a])]
                right=[b,*seams.point(n,db,ob,dims[b])]
                celestic_lanes.extend([left+right,right+left])
        celestic_lanes=sorted(celestic_lanes)
    blocked={tuple(q) for q in edits};lanes={tuple(q) for q in chase_lanes+celestic_lanes}
    event_cells={(v["map_id"],*v["position"]) for v in locations.values()}|{tuple(row["from"]) for row in accepted_entries}
    checks=[]
    for sym in ("SINNOH_TWINLEAF_TOWN","SINNOH_PASTORIA_CITY","SINNOH_VALOR_LAKEFRONT"):
        start=next((tuple(row[3]) for row in entries if row[0]==sym and row[3]),None)
        if not start:result["reason"]="missing_progression_seed";return {},result,b""
        _,_,prior=graph(blobs,mapping,components,root,start,rock,valor_rock)
        _,_,locked=graph(out,mapping,components,root,start,rock,valor_rock,blocked,lanes)
        if not prior or not prior-event_cells<=locked or not locked<=prior:
            result["reason"]="pre_chase_gate_graph_failed";return {},result,b""
        checks.append({"symbol":sym,"prior":len(prior),"locked":len(locked)})
    if tp.build(out,old,components,root)!=entries:
        result["reason"]="final_lake_qa_entries_changed";return {},result,b""
    _,_,final_closed=graph(out,mapping,components,root,seed,rock,valor_rock)
    _,_,final_open=graph(reopened,mapping,components,root,seed,rock,valor_rock)
    if not targets<=final_open or targets&final_closed or any(q[0]==town for q in final_closed) or not any(q[0]==town for q in final_open):
        result["reason"]="final_lake_gate_graph_failed";return {},result,b""
    result["pre_chase_graph_checks"]=checks
    template=template.replace("__LOCATIONS__",ruby_hash(literal)).replace("__SPECS__",ruby_hash(specs))
    for key,value in (("__EDIT_CELLS__",edits),("__CHASE_LANES__",chase_lanes),("__CELESTIC_LANES__",celestic_lanes)):
        if template.count(key)!=1:raise ValueError("F12D_INTEGRATED_GATE_TEMPLATE")
        template=template.replace(key,json.dumps(value))
    result["progression_gate"]={"edited_cells":len(edits),"chase_directional_lanes":len(chase_lanes),
        "celestic_directional_lanes":len(celestic_lanes),"model_verified":True,"runtime_verified":False}
    plugin=(root/"scripts/regions/SinnohF12D3Transaction.rb").read_bytes()+b"\n"+template.encode("utf-8")
    if pbs:
        name="PBS/trainers_sinnoh_f12d_integrated.txt"
        if name in blobs:raise ValueError("F12D_INTEGRATED_PBS_COLLISION")
        out[name]=("\n"+"\n".join(pbs)).encode("ascii")
    if chase.digest(blobs)!=before:raise ValueError("F12D_INTEGRATED_INPUT_CHANGED")
    if set(sprites)&set(blobs):raise ValueError("F12D_INTEGRATED_SPRITE_COLLISION")
    out.update(sprites)
    delta={k:v for k,v in out.items() if blobs.get(k)!=v}
    result.update(status="F12D_INTEGRATED_GAMEPLAY_FIXTURE",mission_prepared=True,locations=locations,
        lake_payloads=lake_ready,restored_original_portals=len(accepted_entries),new_events=len(locations)+len(accepted_entries),new_seams=len(prepared["connections"])+1+len(lake_seams),geometry_delta_count=len(prepared["edits"]),
        closed_cells=len(closed),reopened_cells=len(restored),requires_local_engine=True,
        requires_pre_chase_seam_gate=True,reason="local_engine_and_progression_activation_pending",
        payload_hashes={k:hashlib.sha256(v).hexdigest() for k,v in delta.items()})
    return delta,result,plugin

# Read-only local engine reference comparison. A matching script blob is NOT
# proof that plugins have not overridden it, or that native movement works.
ENGINE_REFS={
    "terrain_tag":"52ec76c28f718f6fc98a34e5069f28ea3275445c",
    "game_map":"3fda78303080bf7be450d110ecaf9df834bec691",
    "game_character":"d7f33659c6627b2bf08fff4e61d43886c76d7b6c",
    "game_player":"6c03a8b19c35d75163283c6121c062bf78ffd9c5",
}
def git_blob_id(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

PLAYER_METHOD_REFS={"passable?":"977b23fd76fe77c4e1354afdd16c91a83503ec69","move_generic":"7f8264d1f61a9c5d39560e71ce5c979e1f3baf74","turn_generic":"1af790fbb2dc434267b0d65213733df9d784bb2f","jump":"e50b4e66179b41222ff406811078df8b988c9318","pbTerrainTag":"fc0c1f63f8766e8397276e0dd16ffef8def34cda","pbFacingTerrainTag":"affd58d712dc601b572ca564491aee86b69d176d","map":"18b03922821628a5827127991217889aae678de1","map_id":"e7520df7bf974bc7e29106a9f8090581fbe8227f","moveto":"4e353355950f307ae0cafc272545fa61eb24043d","update":"782cd09f1cc6d4d08e204082e1bbb1955893b293","update_command_new":"93431966887129b10736486956bb062b56a6217d","update_move":"26db92af0cdd30dd91be314ae44e5abd04fb7bf8","update_stop":"5ff90a8a99cc761065227f218abf3e254f208aeb","update_event_triggering":"00efca900d69a4d834e2378d2897866eb7c08e05"}
def player_method_receipt(raw,expected=PLAYER_METHOD_REFS):
    lines=raw.replace(b"\r\n",b"\n").split(b"\n")
    result={}
    for name,digest in expected.items():
        prefix=b"  def "+name.encode("ascii")
        starts=[i for i,line in enumerate(lines) if line==prefix or line.startswith(prefix+b"(") or line.startswith(prefix+b" ")]
        if len(starts)!=1:result[name]="missing_or_duplicate";continue
        start=starts[0]
        end=next((i for i in range(start+1,len(lines)) if lines[i]==b"  end"),None)
        result[name]="match" if end is not None and hashlib.sha1(b"\n".join(lines[start:end+1])).hexdigest()==digest else "different"
    return result

def player_declarations(raw):
    """Conservative static extraction of conventional top-level Ruby class blocks.

    No scripts are evaluated. Dynamic definitions and plugin overrides are not
    certified by this receipt; do not substitute it for the exact engine gate.
    """
    lines=raw.replace(b"\r\n",b"\n").split(b"\n")
    for start,line in enumerate(lines):
        if not re.match(rb"^class Game_Player(?:\s|$)",line):continue
        end=next((i for i in range(start+1,len(lines)) if lines[i]==b"end"),None)
        if end is None:
            yield start+1,None
        else:
            yield start+1,b"\n".join(lines[start+1:end])

def effective_player_receipt(player_rows,expected=PLAYER_METHOD_REFS):
    # Scripts.rxdata array order is load order for ordinary class declarations.
    # Later direct definitions replace earlier ones; absent methods do not.
    history={name:[] for name in expected};declarations=[]
    for row_index,raw in player_rows:
        for line,body in player_declarations(raw):
            entry={"script_index":row_index,"class_line":line,
                "script_sha256":hashlib.sha256(raw).hexdigest(),"methods":{}}
            if body is None:
                entry["unparsed_class"]=True
                for name in expected:history[name].append({"script_index":row_index,"status":"unresolved"})
            else:
                lines=body.split(b"\n")
                receipt=player_method_receipt(body,expected)
                for name,status in receipt.items():
                    prefix=b"  def "+name.encode("ascii")
                    starts=[i for i,q in enumerate(lines) if q==prefix or q.startswith(prefix+b"(") or q.startswith(prefix+b" ")]
                    if not starts:continue
                    row={"script_index":row_index,"class_line":line,"status":status}
                    if len(starts)==1:
                        stop=next((i for i in range(starts[0]+1,len(lines)) if lines[i]==b"  end"),None)
                        if stop is not None:
                            method=b"\n".join(lines[starts[0]:stop+1])
                            row["method_sha1"]=hashlib.sha1(method).hexdigest()
                            if name=="passable?":
                                row["indexed_state_identifiers"]=[v.decode("ascii") for v in sorted(set(re.findall(rb"(?:\$|@)[A-Za-z_][A-Za-z0-9_]*(?=\s*\[)",method)))]
                        else:row["status"]="unresolved"
                    entry["methods"][name]=row["status"];history[name].append(row)
            declarations.append(entry)
    effective={name:(rows[-1]["status"] if rows else "missing_or_inherited") for name,rows in history.items()}
    return effective,history,declarations

def engine_reference_rows(rows,expected=ENGINE_REFS):
    found={k:0 for k in expected};player_rows=[]
    for row_index,row in enumerate(rows):
        if not isinstance(row,list) or len(row)<3 or not isinstance(row[2],bytes):
            raise ValueError("F12D_ENGINE_SCRIPT_SHAPE")
        raw=zlib.decompress(row[2])
        if re.search(rb"(?m)^class Game_Player(?:\s|$)",raw):player_rows.append((row_index,raw))
        digests={git_blob_id(raw),git_blob_id(raw.replace(b"\r\n",b"\n"))}
        for k,v in expected.items():
            if v in digests:found[k]+=1
    methods,history,declarations=effective_player_receipt(player_rows)
    return {"reference":"Essentials v21.1","matched_scripts":found,
        "game_player_script_count":len(player_rows),"game_player_methods":methods,
        "game_player_method_history":history,"game_player_declarations":declarations,
        "game_player_receipt_scope":"STATIC_DIRECT_DEFINITIONS_NOT_RUNTIME_DISPATCH",
        "reference_match":all(n==1 for n in found.values()),"local_engine_native_verified":False,
        "plugin_overrides_verified":False,"source_scripts_executed":False}

def local_engine(base):
    path=base/"Data/Scripts.rxdata"
    try:
        if path.is_symlink() or not path.is_file():raise ValueError("F12D_ENGINE_MISSING")
        return engine_reference_rows(conn.read_marshal(path.read_bytes(),"F12D_ENGINE_REFERENCE"))
    except (OSError,ValueError,TypeError,KeyError,zlib.error) as exc:
        return {"reference":"Essentials v21.1","reference_match":False,
            "local_engine_native_verified":False,"plugin_overrides_verified":False,
            "source_scripts_executed":False,"reason":type(exc).__name__}

# Exact installed Decades profile observed in runner 139393190451.
# This is NOT an upstream equivalence claim. Only a quarantined private
# compiler candidate is permitted; the native boot guard must prove behavior.
DECADES_PLAYER_DECLARATIONS=(
    (46,"e2eb5cb6cd2665d2bf0339439122bbae7d5b7a5fca287257616b83378e6e57de"),
    (343,"c5ebb0ca3aa3a2f0dc52e001c77358b1d7020b357ae849fb0675351e72a86832"),
)
DECADES_PASSABLE_SHA1="6cd26df1733a6e1c02077dc948c792b461cddf6e"

def known_decades_profile(engine):
    methods=engine.get("game_player_methods",{})
    declarations=engine.get("game_player_declarations",[])
    history=engine.get("game_player_method_history",{})
    return bool(engine.get("game_player_script_count")==2
        and engine.get("matched_scripts")=={"terrain_tag":1,"game_map":1,"game_character":1,"game_player":0}
        and engine.get("reference_match") is False
        and [(r.get("script_index"),r.get("script_sha256")) for r in declarations]==list(DECADES_PLAYER_DECLARATIONS)
        and not any(r.get("unparsed_class") for r in declarations)
        and declarations[1].get("methods")=={}
        and set(methods)==set(PLAYER_METHOD_REFS)
        and set(history)==set(PLAYER_METHOD_REFS)
        and all(methods[n]==("different" if n=="passable?" else "match") for n in methods)
        and all(len(history[n])==1 and history[n][0].get("script_index")==46
            and history[n][0].get("status")==methods[n]
            and history[n][0].get("method_sha1")== (DECADES_PASSABLE_SHA1 if n=="passable?" else PLAYER_METHOD_REFS[n])
            for n in methods))

def payload_verified(story,delta,plugin,item):
    expected={"CYNTHIA","PSYDUCK_1","PSYDUCK_2","PSYDUCK_3","PSYDUCK_4"}
    return bool(story.get("status")=="F12D_INTEGRATED_GAMEPLAY_FIXTURE" and story.get("mission_prepared") is True
        and story.get("progression_gate",{}).get("model_verified") is True
        and {row.get("symbol") for row in story.get("pre_chase_graph_checks",[])}==
            {"SINNOH_TWINLEAF_TOWN","SINNOH_PASTORIA_CITY","SINNOH_VALOR_LAKEFRONT"}
        and story.get("new_maps")==0 and story.get("new_portals")==0
        and expected<=set(story.get("locations",{}))
        and (item.get("local_catalog_valid") is True or item.get("authored_candidate") is True)
        and delta and plugin and story.get("payload_hashes")=={k:hashlib.sha256(v).hexdigest() for k,v in delta.items()})

def activation_allowed(story,delta,plugin,engine,item):
    # Historical strict static gate; never label Decades as reference-identical.
    return bool(engine.get("reference_match") is True and payload_verified(story,delta,plugin,item))

def private_compile_candidate_allowed(story,delta,plugin,engine,item):
    # Alternate private compile-only path; all geometry/catalogue/hash gates
    # remain mandatory. Native checks and a matching compile token are needed
    # before ANY normal Game.exe session in the resulting copy.
    return activation_allowed(story,delta,plugin,engine,item) or (
        known_decades_profile(engine) and payload_verified(story,delta,plugin,item))

def installer_preflight(blobs,mapping,components,cr,base,root,source,staged=None):
    """Generate a private copy candidate only after model and local preflight.
    Native compilation must still verify the actual item, terrain and teams."""
    if staged is not None:staged.clear()
    result={"status":"F12D_INTEGRATED_INSTALLER_PREFLIGHT","runtime_install_enabled":False,
        "native_verified":False,"candidate_ready":False,"new_maps":0,"new_portals":0,
        "engine":local_engine(base),"item_catalogue":item_catalogue.audit(base)}
    try:
        if not secret_audit.chase_prepared(cr):raise ValueError("F12D_INTEGRATED_REQUIRES_CHASE")
        existing=set()
        for path in (base/"PBS").glob("trainers*.txt"):
            if path.is_symlink() or not path.is_file():raise ValueError("F12D_INTEGRATED_UNSAFE_PBS")
            for header in trainers.read_blocks(path):
                v=[x.strip() for x in header.split(",")]
                if len(v) in (2,3) and (len(v)==2 or v[2].isdigit()):
                    existing.add((v[0],v[1],int(v[2]) if len(v)==3 else 0))
        for path,raw in blobs.items():
            if path.startswith("PBS/trainers") and path.endswith(".txt"):
                for header in re.findall(r"^\s*\[([^\]]+)\]\s*$",raw.decode("utf-8-sig"),re.M):
                    v=[x.strip() for x in header.split(",")]
                    if len(v) in (2,3) and (len(v)==2 or v[2].isdigit()):
                        existing.add((v[0],v[1],int(v[2]) if len(v)==3 else 0))
        if any((base/path).exists() for path in assets.build()):raise ValueError("F12D_INTEGRATED_LOCAL_SPRITE_COLLISION")
        item_delta,item_report=item_catalogue.prepare_missing(base,blobs)
        result["item_catalogue"]=item_report
        audited=secret_audit.audit(blobs,mapping,components,cr,source,root)
        expanded=expanded_audit.inspect(blobs,mapping,components,cr,audited,source,root)
        original=original_audit.inspect(blobs,mapping,components,cr,expanded,source,root)
        delta,story,plugin=compile_story(blobs,mapping,components,cr,expanded,original,source,root,
            trainers.catalogue(base,"trainer_types",blobs),trainers.catalogue(base,"pokemon"),
            {"SECRETPOTION"} if item_report["local_catalog_valid"] or item_delta else set(),existing)
        # Do not embed private map bytes or huge path reports in the manifest.
        result.update(story_status=story["status"],mission_prepared=story["mission_prepared"],
            lake_local_previews=story.get("lake_local_previews",{}),lake_payloads=story.get("lake_payloads",[]),
            lake_sequence_checks=story.get("lake_sequence_checks",{}),
            lake_independent_legs=story.get("lake_independent_legs",{}),
            lake_original_seam_recovery=story.get("lake_original_seam_recovery",{}),
            lake_original_entries=story.get("lake_original_entries",{}),
            lake_surf_geometry=story.get("lake_surf_geometry",{}),
            surf_pickup=story.get("surf_pickup",{}),
            restored_original_portals=story.get("restored_original_portals",0),
            pre_chase_graph_checks=story.get("pre_chase_graph_checks",[]),
            geometry_delta_count=story.get("geometry_delta_count",0),
            progression_gate=story.get("progression_gate",{}),
            reason=story.get("reason"),candidate_ready=bool(delta and plugin),
            payload_hashes=story.get("payload_hashes",{}),authored_sprite_hashes=story["authored_sprite_hashes"])
        if delta and plugin:
            eligible=private_compile_candidate_allowed(story,delta,plugin,result["engine"],item_report)
            result["engine_profile"]="EXACT_ESSENTIALS_REFERENCE" if result["engine"].get("reference_match") else (
                "PINNED_DECADES_PRIVATE_COMPILE_ONLY" if known_decades_profile(result["engine"]) else "UNKNOWN_BLOCKED")
            result["native_movement_and_item_proof_required"]=True
            delta.update(item_delta)
            result["payload_hashes"]={k:hashlib.sha256(v).hexdigest() for k,v in delta.items()}
            result["candidate_plugin_sha256"]=hashlib.sha256(plugin).hexdigest()
            result["reason"]="runtime_movement_binding_and_native_compatibility_pending"
            if staged is not None and eligible:
                allowed={"PBS/map_connections.txt","Data/map_connections.dat","PBS/trainers_sinnoh_f12d_integrated.txt",item_catalogue.FRAGMENT}|set(assets.build())|{"Data/Map%03d.rxdata"%m for m in mapping.values()}
                if set(delta)-allowed:raise ValueError("F12D_INTEGRATED_UNEXPECTED_DELTA")
                out={**blobs,**delta};chase.validate(out,mapping)
                staged.update(maps=out,plugin=plugin)
                result.update(runtime_install_enabled=True,new_events=story["new_events"],new_seams=story["new_seams"],locations=story["locations"],status="F12D_INTEGRATED_PRIVATE_COPY_PREPARED",reason="native_compilation_movement_item_proof_and_qa_pending",
                    native_compile_verified=False,normal_launch_allowed=False)
        return result
    except (OSError,ValueError,TypeError,KeyError,UnicodeError) as exc:
        code=str(exc)
        # Report only project-defined, non-sensitive invariant identifiers.
        detail=code if isinstance(exc,ValueError) and re.fullmatch(r"(?:F12D|F10B7|F10B8)_[A-Z0-9_]{1,100}",code) else None
        return {**result,"reason":"preflight_failed:"+type(exc).__name__,
            "invariant":detail}
