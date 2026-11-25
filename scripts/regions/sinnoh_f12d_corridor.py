"""F12D2 bounded authored terrestrial corridor, only for the audited source gap.
Preserve original map dimensions, events, tilesets, MapIDs and connections.
No transfer events, passage-table changes, source scripts, or save writes.
"""
import hashlib
import heapq
import struct
from collections import Counter
import sinnoh_f12d_pastoria_preview as p
import sinnoh_f12d_seams as seams
import sinnoh_private_visual as pv
import sinnoh_connection_expansion as conn
import sinnoh_qa_teleport as tp
from build_johto_events import EVENT_CLASSES

WEST=(219,"E",1,218,"W",0)
NORTH=(218,"N",32,214,"S",0)
MAX_EDITS_PER_LEG=16
MAX_EDITS_TOTAL=32

def grid(world,tiles):
    a=world.attrs;w,h=a["@width"],a["@height"]
    ts=tiles[a["@tileset_id"]].attrs
    passages=struct.unpack("<%dH"%((len(ts["@passages"].data)-20)//2),ts["@passages"].data[20:])
    tags=struct.unpack("<%dH"%((len(ts["@terrain_tags"].data)-20)//2),ts["@terrain_tags"].data[20:])
    cells=struct.unpack_from("<%dH"%(w*h*3),a["@data"].data,20)
    stacks={};shapes={}
    for y in range(h):
        for x in range(w):
            stack=tuple(cells[z*w*h+y*w+x] for z in range(3))
            used=[i for i in stack if i]
            if any(i>=len(passages) or i>=len(tags) for i in used):
                raise ValueError("F12D_CORRIDOR_TILE_RANGE")
            masks=tuple(passages[i]&15 for i in used);terrain=tuple(tags[i] for i in used)
            stacks[x,y]=stack
            shapes[x,y]=(masks,terrain)
    return stacks,shapes

def ordinary(shape):
    masks,tags=shape
    return bool(masks) and all(m==0 for m in masks) and all(t in (0,2) for t in tags)

def editable(source,qa):
    # Never change water, ledges, special terrain, unknown conversion or
    # a partially directional tile. Limit to proven fully blocked dry stacks.
    masks,tags=qa
    return source==qa and bool(masks) and 15 in masks and all(m in (0,15) for m in masks) and all(t==0 for t in tags)

def shortest(seed,target,shapes,source,protected,size,existing_edits=()):
    """Lexicographically minimize changed cells, then walking distance.
    Only the requested boundary point may be changed on the map perimeter.
    """
    w,h=size;already=set(existing_edits)
    if seed not in shapes or not ordinary(shapes[seed]):return None
    if target not in shapes:return None
    def cost(q):
        if q in protected:return None
        if ordinary(shapes[q]) or q in already:return 0
        if q!=target and (q[0] in (0,w-1) or q[1] in (0,h-1)):return None
        if not editable(source[q],shapes[q]):return None
        return 1
    dist={seed:(0,0)};prev={};todo=[(0,0,seed)]
    while todo:
        edits,length,xy=heapq.heappop(todo)
        if dist.get(xy)!=(edits,length):continue
        if xy==target:
            path=[xy]
            while path[-1]!=seed:path.append(prev[path[-1]])
            path.reverse()
            return path,[q for q in path if not ordinary(shapes[q]) and q not in already]
        for q in tp.neighbours(*xy):
            if q not in shapes:continue
            n=cost(q)
            if n is None or edits+n>MAX_EDITS_PER_LEG:continue
            score=(edits+n,length+1)
            if score>=dist.get(q,(10**9,10**9)):continue
            dist[q]=score;prev[q]=xy;heapq.heappush(todo,(*score,q))
    return None

def repair(original,candidate,mapping,components,source_path,root,report):
    """Return candidate geometry and sanitized proof; caller rolls back on failure."""
    info={"status":"F12D_AUTHORED_CORRIDOR_BLOCKED","native_verified":False,
          "provenance":"PROJECT_AUTHORED_MINIMAL_DRY_GROUND_NOT_ORIGINAL",
          "changed_cells":0,"new_seams":0,"edits":[]}
    def blocked(reason):
        return candidate,{**info,"reason":reason}
    pairs=report.get("pairs",[])
    if len(pairs)!=2:return blocked("unexpected_source_pairs")
    west,north=pairs
    if west.get("source_candidates")!=[list(WEST)] or north.get("source_candidates")!=[list(NORTH)]:
        return blocked("source_connections_changed")
    if west.get("reason")!="source_has_no_ordinary_lane" or north.get("reason")!="candidate_verified":
        return blocked("source_gap_not_proven")
    if any(q.get("source_qa_mismatch_axes") or q.get("competing_intervals") for q in pairs):
        return blocked("source_alignment_or_conversion_changed")
    if west.get("aligned_axis_count")!=66 or north.get("aligned_axis_count")!=64:
        return blocked("source_dimensions_changed")
    old={k:v for k,v in mapping.items() if k in p.prior.ALL}
    entries=tp.build(original,old,components,root)
    arrivals={r[0]:tuple(r[3][1:]) for r in entries if r[3]}
    ids={sid:mapping[sym] for sid,(sym,_) in p.SOURCES.items()}
    tiles=conn.read_marshal(original["Data/Tilesets.rxdata"],"F12D_CORRIDOR_TILES")
    worlds={sid:conn.read_marshal(original["Data/Map%03d.rxdata"%mid],"F12D_CORRIDOR_MAP") for sid,mid in ids.items()}
    sizes={sid:(w.attrs["@width"],w.attrs["@height"]) for sid,w in worlds.items()}
    qa={sid:grid(w,tiles) for sid,w in worlds.items()}
    src={};protected={sid:set() for sid in ids}
    with pv.verified_archive(source_path,"maps") as z:
        st=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D_CORRIDOR_SOURCE_TILES")
        for sid,(_,digest) in p.SOURCES.items():
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError("F12D_CORRIDOR_SOURCE_HASH")
            w=conn.read_marshal(raw,"F12D_CORRIDOR_SOURCE")
            if (w.attrs["@width"],w.attrs["@height"])!=sizes[sid]:raise ValueError("F12D_CORRIDOR_DIMENSIONS")
            src[sid]=grid(w,st)[1]
            protected[sid].update((e.attrs["@x"],e.attrs["@y"]) for e in w.attrs["@events"].values())
    # Protect every existing QA event and every literal transfer destination.
    for mid in mapping.values():
        w=conn.read_marshal(original["Data/Map%03d.rxdata"%mid],"F12D_CORRIDOR_PORTALS")
        for e in w.attrs["@events"].values():
            for sid,id_ in ids.items():
                if mid==id_:protected[sid].add((e.attrs["@x"],e.attrs["@y"]))
            for page in e.attrs["@pages"]:
                for command in page.attrs["@list"]:
                    a=command.attrs;args=a.get("@parameters",[])
                    if a.get("@code")==201 and len(args)==6 and args[0]==0 and all(type(x) is int for x in args):
                        for sid,id_ in ids.items():
                            if args[1]==id_:protected[sid].add(tuple(args[2:4]))
    # Avoid editing cells adjacent to events or arrivals; ordinary traversal
    # past them remains legal except on actual event/landing cells.
    forbidden={sid:set(cells) for sid,cells in protected.items()}
    for sid,cells in protected.items():
        forbidden[sid].update(q for xy in cells for q in tp.neighbours(*xy) if q in qa[sid][1] and not ordinary(qa[sid][1][q]))
    seeds={sid:arrivals[sym] for sid,(sym,_) in p.SOURCES.items()}
    def route(sid,target,edits=()):
        return shortest(seeds[sid],target,qa[sid][1],src[sid],forbidden[sid],sizes[sid],edits)
    west_options=[]
    for row in west["axis_evidence"]:
        a,b=tuple(row["a"]),tuple(row["b"])
        if not row["a_from_local_spawn"] or not row["source_a"]["ordinary_walkable"] or row["source_b"]["ordinary_walkable"]:continue
        if a in forbidden[219] or b in forbidden[218]:continue
        if row["source_a"]!=row["qa_a"] or row["source_b"]!=row["qa_b"]:continue
        result=route(218,b)
        if result:west_options.append((len(result[1]),len(result[0]),row["axis"],result))
    if not west_options:return blocked("no_bounded_dry_west_corridor")
    # North physical lanes already exist. Find a pair of interior approaches
    # connecting the two arrival components, minimizing edits over both legs.
    options=[]
    for _,_,wa,wr in sorted(west_options):
        for row in north["axis_evidence"]:
            if not row["eligible"]:continue
            rr=route(218,tuple(row["a"]),wr[1]);vr=route(214,tuple(row["b"]))
            if not rr or not vr:continue
            edits218=set(wr[1])|set(rr[1]);edits214=set(vr[1])
            count=len(edits218)+len(edits214)
            if count>MAX_EDITS_TOTAL:continue
            options.append((count,len(wr[0])+len(rr[0])+len(vr[0]),wa,row["axis"],wr,rr,vr))
    if not options:return blocked("no_bounded_dry_north_corridor")
    _,_,wa,na,wr,rr,vr=min(options,key=lambda x:x[:4])
    edits={218:set(wr[1])|set(rr[1]),214:set(vr[1])}
    out=dict(candidate);records=[]
    for sid,positions in edits.items():
        if not positions:continue
        mid=ids[sid];rel="Data/Map%03d.rxdata"%mid;world=worlds[sid]
        stacks,shapes=qa[sid];w,h=sizes[sid];data=world.attrs["@data"];before=data.data
        # Use only existing dry zero-mask ground from the same map/tileset.
        floor=[q for q,v in shapes.items() if ordinary(v) and all(t==0 for t in v[1]) and q not in protected[sid]]
        if not floor:return blocked("no_existing_dry_ground_stack")
        changed=bytearray(before)
        for x,y in sorted(positions):
            q=(x,y)
            if q in forbidden[sid] or not editable(src[sid][q],shapes[q]):raise ValueError("F12D_CORRIDOR_UNSAFE_EDIT")
            donor=min(floor,key=lambda t:(conn.distance(q,t),t[1],t[0]))
            new=stacks[donor]
            for z,t in enumerate(new):struct.pack_into("<H",changed,20+2*(z*w*h+y*w+x),t)
            records.append({"map_id":mid,"position":[x,y],"floor_reference":list(donor),
                "before_masks":list(shapes[q][0]),"before_tags":list(shapes[q][1]),
                "after_masks":list(shapes[donor][0]),"after_tags":list(shapes[donor][1])})
        # Restore data and compare canonical serialization to prove all other
        # fields, events, geometry dimensions and tileset identities unchanged.
        data.data=bytes(changed)
        raw=conn.serialize(world,EVENT_CLASSES)
        check=conn.read_marshal(raw,"F12D_CORRIDOR_VERIFY")
        _,after=grid(check,tiles)
        if {q for q in shapes if after[q]!=shapes[q]}!=positions or not all(ordinary(after[q]) for q in positions):
            raise ValueError("F12D_CORRIDOR_CELL_DELTA")
        check.attrs["@data"].data=before;data.data=before
        if conn.serialize(check,EVENT_CLASSES)!=conn.serialize(world,EVENT_CLASSES):
            raise ValueError("F12D_CORRIDOR_MAP_METADATA_CHANGED")
        out[rel]=raw
    west_record=(ids[219],"E",1,ids[218],"W",0)
    prior=pv.parse_connections(candidate["PBS/map_connections.txt"])
    compiled=conn.read_marshal(candidate["Data/map_connections.dat"],"F12D_CORRIDOR_CONNECTIONS")
    if west_record in prior or any((m,d) in {(ids[219],"E"),(ids[218],"W")} for r in prior for m,d,*_ in seams.ends(r)):
        return blocked("west_side_already_used")
    out["PBS/map_connections.txt"]=candidate["PBS/map_connections.txt"]+("\n# F12D authored dry approach on original alignment\n"+",".join(map(str,west_record))+"\n").encode("ascii")
    out["Data/map_connections.dat"]=conn.serialize(compiled+[[west_record[0],b"E",1,west_record[3],b"W",0]])
    if pv.parse_connections(out["PBS/map_connections.txt"])!=prior+[west_record]:raise ValueError("F12D_CORRIDOR_PRIOR_CONNECTIONS")
    if tp.build(out,old,components,root)!=entries:return blocked("qa_arrival_changed")
    allowed={"Data/Map%03d.rxdata"%ids[s] for s in edits if edits[s]}|{"PBS/map_connections.txt","Data/map_connections.dat"}
    if any(out[k]!=v for k,v in candidate.items() if k not in allowed):raise ValueError("F12D_CORRIDOR_UNRELATED_CHANGE")
    info.update(status="F12D_AUTHORED_CORRIDOR_CANDIDATE",reason=None,changed_cells=len(records),
                new_seams=1,edits=records,west_axis=wa,north_axis=na,
                path_lengths=[len(wr[0]),len(rr[0]),len(vr[0])],
                map_hashes={str(ids[s]):{"before":hashlib.sha256(original["Data/Map%03d.rxdata"%ids[s]]).hexdigest(),
                    "after":hashlib.sha256(out["Data/Map%03d.rxdata"%ids[s]]).hexdigest()} for s in edits if edits[s]})
    return out,info
