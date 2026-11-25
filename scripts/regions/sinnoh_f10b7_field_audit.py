"""F10B7: inert field-gate investigation; never add or move an event.

Only existing QA entries, plain/grass terrain and verified simple transfers
or continuous edges contribute reachability. Historical prerequisites are
hypotheses until the donor and native campaign implementation prove them.
"""
from collections import Counter,deque
import hashlib
import re
import struct
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
import sinnoh_f08c_expansion as f08c
import sinnoh_f10a_inventory as f10a
import sinnoh_f10b_trainers as f
import sinnoh_qa_teleport as teleport

PENDING={
    (42,32):("Austin","YOUNGSTER","route207_bicycle_slope"),
    (42,33):("Kevin","HIKER","route207_bicycle_slope"),
    (42,34):("Helen","CRUSHGIRL","route207_bicycle_slope"),
    (79,32):("Louis","HIKER","route211_west_access"),
    (79,33):("Alexander","BIRDKEEPER","possible_Alexandra_rock_smash_identity_unproven"),
    (80,1):("Wyatt","CAMPER","possible_Jogger_Wyatt_morning_bicycle_identity_unproven"),
}
# Whitelisted token families only. Never return donor script text or execute it.
TOKENS={
    "bicycle":re.compile(rb"\b(?:pbMountBike|pbDismountBike|pbBike|BICYCLE|bicycle|cycling)\b",re.I),
    "rock_smash":re.compile(rb"\b(?:pbRockSmash|ROCKSMASH|RockSmash|rock_smash)\b",re.I),
    "rock_climb":re.compile(rb"\b(?:pbRockClimb|ROCKCLIMB|RockClimb|rock_climb)\b",re.I),
    "morning":re.compile(rb"\b(?:isMorning\??|morning|pbIsMorning)\b",re.I),
    "time":re.compile(rb"\b(?:PBDayNight|pbGetTimeNow|Time\.now)\b",re.I),
}
def gate_shape(event):
    result=[]
    for page in event.attrs.get("@pages",[]):
        p=page.attrs;c=getattr(p.get("@condition"),"attrs",{})
        flags=[k for k in ("switch1_valid","switch2_valid","variable_valid","self_switch_valid") if c.get("@"+k) is not False]
        kinds=Counter();branch=Counter();codes=Counter()
        for command in p.get("@list",[]):
            op=command.attrs;code=op.get("@code");codes[code]+=1
            args=op.get("@parameters",[])
            if code==111 and args and type(args[0]) is int:branch[args[0]]+=1
            if code not in (111,355,655):continue
            if code==111 and (not args or args[0]!=12):continue
            for arg in args:
                if isinstance(arg,bytes):
                    for label,pattern in TOKENS.items():
                        if pattern.search(arg):kinds[label]+=1
        result.append({"trigger":p.get("@trigger"),"move_type":p.get("@move_type"),
                       "condition_flags":flags,"conditional_types":dict(branch),
                       "command_counts":dict(codes),"script_gate_tokens":dict(kinds)})
    return result

def cell_shape(world,tiles,xy):
    a=world.attrs;w,h=a["@width"],a["@height"];x,y=xy
    if not (0<=x<w and 0<=y<h):return {"in_bounds":False}
    ts=tiles[a["@tileset_id"]].attrs
    p=ts["@passages"].data[20:];t=ts["@terrain_tags"].data[20:]
    p=struct.unpack("<%dH"%(len(p)//2),p);t=struct.unpack("<%dH"%(len(t)//2),t)
    cells=struct.unpack_from("<%dH"%(w*h*3),a["@data"].data,20)
    stack=[cells[z*w*h+y*w+x] for z in range(3) if cells[z*w*h+y*w+x]]
    if any(i>=len(p) or i>=len(t) for i in stack):raise ValueError("F10B7_TILE_RANGE")
    return {"in_bounds":True,"terrain_tags":[t[i] for i in stack],
            "passage_masks":[p[i]&15 for i in stack],
            "ordinary_walkable":bool(stack) and all(not p[i]&15 and t[i] in (0,2) for i in stack)}

# Essentials v21.1 Game_Character#passable? checks the outgoing
# direction on the current cell AND the opposite bit on the destination.
# This conservative model ORs every nonempty layer (never overrides a block
# based on priority), and excludes all special terrain modes.
DIR_BITS={(0,1):(1,8),(-1,0):(2,4),(1,0):(4,2),(0,-1):(8,1)}
EDGE_BITS={"N":8,"S":1,"W":2,"E":4}

def step_allowed(a,b,delta):
    if delta not in DIR_BITS:return False
    outgoing,incoming=DIR_BITS[delta]
    return (a&outgoing)==0 and (b&incoming)==0 and a!=15 and b!=15

def directional_masks(world,tiles):
    a=world.attrs;w,h=a["@width"],a["@height"]
    ts=tiles[a["@tileset_id"]].attrs
    p=ts["@passages"].data[20:];t=ts["@terrain_tags"].data[20:]
    p=struct.unpack("<%dH"%(len(p)//2),p);t=struct.unpack("<%dH"%(len(t)//2),t)
    cells=struct.unpack_from("<%dH"%(w*h*3),a["@data"].data,20)
    masks={}
    for y in range(h):
        for x in range(w):
            stack=[cells[z*w*h+y*w+x] for z in range(3) if cells[z*w*h+y*w+x]]
            if any(i>=len(p) or i>=len(t) for i in stack):raise ValueError("F10B8_TILE_RANGE")
            if not stack or any(t[i] not in (0,2) for i in stack):continue
            mask=0
            for i in stack:mask|=p[i]&15
            if mask!=15:masks[x,y]=mask
    return masks

def directional_component(points,seed,masks):
    if seed not in points:return set()
    seen={seed};todo=deque([seed])
    while todo:
        x,y=todo.popleft()
        for q in teleport.neighbours(x,y):
            if q not in points or q in seen:continue
            if not step_allowed(masks[x,y],masks[q],(q[0]-x,q[1]-y)):continue
            seen.add(q);todo.append(q)
    return seen

def index_components(points,masks=None):
    remaining=set(points);index={};groups=[]
    while remaining:
        seed=min(remaining,key=lambda p:(p[1],p[0]))
        group=f.component(remaining,seed) if masks is None else directional_component(remaining,seed,masks)
        label=len(groups);groups.append(group)
        for xy in group:index[xy]=label
        remaining.difference_update(group)
    return index,groups

def closure(edges,seeds):
    seen=set(seeds);todo=deque(sorted(seen))
    while todo:
        for node in edges.get(todo.popleft(),()):
            if node not in seen:seen.add(node);todo.append(node)
    return seen

def verified_verity_entry(event,src,mapping):
    if src!=mapping.get("SINNOH_VERITY_LAKEFRONT"):return None
    name=event.attrs.get("@name")
    if name not in (b"SN_LAKEFRONT_TO_LAKE_1",b"SN_LAKEFRONT_TO_LAKE_2"):return None
    lane=0 if name.endswith(b"1") else 1
    if (event.attrs.get("@x"),event.attrs.get("@y"))!=(10+lane,2):return None
    pages=event.attrs.get("@pages",[])
    if len(pages)!=1:return None
    p=pages[0].attrs;condition=p.get("@condition")
    if p.get("@trigger")!=1 or p.get("@move_type")!=0 or condition is None or any(
        condition.attrs.get("@"+k) is not False for k in ("switch1_valid","switch2_valid","variable_valid","self_switch_valid")):return None
    ops=[c.attrs for c in p.get("@list",[])]
    if [c.get("@code") for c in ops]!=[111,201,0,412,0] or [c.get("@indent") for c in ops]!=[0,1,1,0,0]:return None
    if ops[0].get("@parameters")!=[12,b"BlueSinnohPilot.lake_entry_allowed?"]:return None
    a=ops[1].get("@parameters",[])
    dst=mapping.get("SINNOH_LAKE_VERITY")
    if dst is None or len(a)!=6 or a[:5]!=[0,dst,44+lane,42,8] or a[5] not in (0,1):return None
    return (10+lane,2,dst,44+lane,42,8,a[5])

ORIGINAL_LAKE_SYMBOLS={159:"SINNOH_ACUITY_LAKEFRONT",161:"SINNOH_LAKE_ACUITY",
    162:"SINNOH_ACUITY_CAVERN",195:"SINNOH_VERITY_LAKEFRONT",196:"SINNOH_LAKE_VERITY",214:"SINNOH_VALOR_LAKEFRONT",215:"SINNOH_LAKE_VALOR",217:"SINNOH_VALOR_CAVERN"}
ORIGINAL_LAKE_EVENT_CONTRACTS={
    (159,3,161):(20,32,8,49),(161,2,159):(8,49,20,33),
    (161,3,162):(26,26,20,34),(162,1,161):(20,34,26,26),
    # The Verity pair is accepted only when the pinned donor transfer matches
    # the existing lakefront lanes and a safe adjacent return landing.
    (195,2,196):(10,2,44,42),(195,3,196):(11,2,45,42),
    (196,1,195):(44,43,10,3),(196,2,195):(45,43,11,3),
    (214,6,215):(45,22,45,6),(214,7,215):(45,23,45,7),
    (215,2,214):(46,6,46,22),(215,3,214):(46,7,46,23),
    (215,4,217):(26,24,22,36),(217,1,215):(22,36,26,24),
}
ORIGINAL_LAKE_PAIRS={(a,b) for a,_,b in ORIGINAL_LAKE_EVENT_CONTRACTS}
ORIGINAL_CAVE_CALLS={b"pbCaveEntrance",b"pbCaveExit"}

def verified_original_lake_entry(event,src,mapping):
    name=event.attrs.get("@name",b"")
    if not isinstance(name,bytes):return None
    match=re.fullmatch(rb"SN_F12D_ORIGINAL_LAKE_(\d+)_(\d+)_(\d+)",name)
    if not match:return None
    a,eid,b=map(int,match.groups())
    if (a,b) not in ORIGINAL_LAKE_PAIRS or src!=mapping.get(ORIGINAL_LAKE_SYMBOLS[a]):return None
    dst=mapping.get(ORIGINAL_LAKE_SYMBOLS[b])
    pages=event.attrs.get("@pages",[])
    if dst is None or len(pages)!=1:return None
    p=pages[0].attrs;condition=p.get("@condition")
    if p.get("@trigger") not in (0,1,2) or p.get("@move_type")!=0 or p.get("@through") is not True or condition is None or any(
        condition.attrs.get("@"+k) is not False for k in ("switch1_valid","switch2_valid","variable_valid","self_switch_valid")):return None
    ops=[c.attrs for c in p.get("@list",[])]
    if len(ops)<5 or ops[0].get("@code")!=111 or ops[0].get("@indent")!=0 or ops[0].get("@parameters")!=[12,("BlueSinnohF12DIntegrated.original_lake_entry_allowed?(%d,%d)"%(a,b)).encode("ascii")]:return None
    if [c.get("@code") for c in ops[-3:]]!=[0,412,0] or [c.get("@indent") for c in ops[-3:]]!=[1,0,0]:return None
    body=ops[1:-3]
    if not body or body[-1].get("@code")!=201 or any(c.get("@indent")!=1 for c in body):return None
    if len(body)>2:return None
    if len(body)==2 and (body[0].get("@code")!=355 or len(body[0].get("@parameters",[]))!=1 or body[0]["@parameters"][0] not in ORIGINAL_CAVE_CALLS):return None
    v=body[-1].get("@parameters",[])
    if len(v)!=6 or any(type(x) is not int for x in v) or v[:2]!=[0,dst] or v[4] not in (0,2,4,6,8) or v[5] not in (0,1):return None
    if ORIGINAL_LAKE_EVENT_CONTRACTS.get((a,eid,b))!=(event.attrs["@x"],event.attrs["@y"],v[2],v[3]):return None
    return (event.attrs["@x"],event.attrs["@y"],dst,*v[2:])

def valor_rock_mask_allowed(threshold, occupied, verified_portal, post_chase_story):
    # A normal Rock cell may be occupied by an NPC. Its terrain mask is
    # unchanged, and the common free-cell subtraction excludes that NPC.
    # The decorative threshold is narrower: an occupied threshold is
    # usable only for the verified original portal in the post-chase model.
    return not (threshold and occupied) or (verified_portal and post_chase_story)

def access_graph(blobs,mapping,components,root,seed_symbols=None,directional=False,seed_cells=None,strict_movement=False,rock_cells=(),valor_rock=(),blocked_cells=(),blocked_lanes=(),post_chase_story=False,edge_sink=None):
    reverse={mid:sym for sym,mid in mapping.items()}
    tiles=conn.read_marshal(blobs["Data/Tilesets.rxdata"],"F10B7_QA_TILES")
    worlds={mid:conn.read_marshal(blobs["Data/Map%03d.rxdata"%mid],"F10B7_QA") for mid in reverse}
    index={};groups={};free={};passages={};arrival_only={};portal_events={}
    rock_cells=set(rock_cells);valor_rock=dict(valor_rock);blocked_cells=set(blocked_cells);blocked_lanes=set(blocked_lanes)
    if (blocked_cells or blocked_lanes or post_chase_story) and (not directional or not strict_movement):raise ValueError("F12D_GATE_GRAPH_SCOPE")
    if valor_rock and (not directional or not strict_movement or any(reverse.get(m)!="SINNOH_VALOR_CAVERN" for m,x,y in valor_rock)):
        raise ValueError("F12D_VALOR_ROCK_SCOPE")
    rock_symbols={"SINNOH_ROUTE_210","SINNOH_SOLACEON_TOWN","SINNOH_ROUTE_209","SINNOH_ROUTE_210_SEGMENT_2","SINNOH_HEARTHOME_CITY","SINNOH_F07_INTERIOR_125","SINNOH_ROUTE_215","SINNOH_VEILSTONE_CITY","SINNOH_ROUTE_214","SINNOH_VALOR_LAKEFRONT","SINNOH_ROUTE_213","SINNOH_PASTORIA_CITY","SINNOH_ROUTE_212","SINNOH_ROUTE_212_SEGMENT_2"}
    if rock_cells and (not directional or not strict_movement or reverse.get(473)!="SINNOH_ROUTE_210_SEGMENT_2" or any(reverse.get(m) not in rock_symbols for m,x,y in rock_cells)):
        raise ValueError("F12D3_ROCK_GRAPH_SCOPE")
    for mid,world in worlds.items():
        occupied={(e.attrs["@x"],e.attrs["@y"]) for e in world.attrs["@events"].values()}
        if post_chase_story:
            # Only existing statically recognised through transfers qualify.
            # Ordinary NPCs, conditions and solid events remain occupied.
            by_cell={}
            for e in world.attrs["@events"].values():
                by_cell.setdefault((e.attrs["@x"],e.attrs["@y"]),[]).append(e)
            for xy,events in by_cell.items():
                if len(events)!=1:continue
                e=events[0]
                transfer,_=conn.classify_transfer(e)
                if not transfer:transfer=verified_verity_entry(e,mid,mapping) or verified_original_lake_entry(e,mid,mapping)
                if not transfer:continue
                p=e.attrs["@pages"][0].attrs
                if p.get("@through") is not True:continue
                portal_events[mid,xy]=p.get("@trigger")
                if p.get("@trigger")==0:occupied.discard(xy)
        if directional:
            passages[mid]=directional_masks(world,tiles)
            # The private movement guard rejects every stack with any passage bit.
            # Chase witnesses must not use cells that the runtime will reject.
            if strict_movement:
                passages[mid]={xy:mask for xy,mask in passages[mid].items() if mask==0}
            for _,x,y in sorted(p for p in rock_cells if p[0]==mid):
                a=world.attrs;w,h=a["@width"],a["@height"]
                if not (0<x<w-1 and 0<y<h-1):raise ValueError("F12D3_ROCK_GRAPH_PERIMETER")
                raw=a["@data"].data
                stack=tuple(struct.unpack_from("<H",raw,20+2*(z*w*h+y*w+x))[0] for z in range(3))
                ta=tiles[a["@tileset_id"]].attrs
                priority=struct.unpack_from("<H",ta["@priorities"].data,20+2*462)[0]
                mask=struct.unpack_from("<H",ta["@passages"].data,20+2*462)[0]&15
                tag=struct.unpack_from("<H",ta["@terrain_tags"].data,20+2*462)[0]
                if stack!=(462,0,0) or mask!=0 or tag!=4 or priority!=0 or (x,y) in occupied:
                    raise ValueError("F12D3_ROCK_GRAPH_CELL_CHANGED")
                passages[mid][x,y]=0
            for (m,x,y),expected in valor_rock.items():
                if m!=mid:continue
                a=world.attrs;w,h=a["@width"],a["@height"]
                if not (0<x<w-1 and 0<y<h-1):raise ValueError("F12D_VALOR_ROCK_PERIMETER")
                stack=tuple(struct.unpack_from("<H",a["@data"].data,20+2*(z*w*h+y*w+x))[0] for z in range(3))
                ts=tiles[a["@tileset_id"]].attrs
                tags=[struct.unpack_from("<H",ts["@terrain_tags"].data,20+2*k)[0] for k in stack if k]
                priorities=tuple(struct.unpack_from("<H",ts["@priorities"].data,20+2*k)[0] for k in stack if k)
                threshold=(x,y)==(22,36) and tags==[4,0] and priorities==(0,1)
                if stack!=expected or 4 not in tags or any(tag not in (0,4) for tag in tags) or any(
                    struct.unpack_from("<H",ts["@passages"].data,20+2*k)[0]&15 for k in stack if k) or (not threshold and any(priorities)):
                    raise ValueError("F12D_VALOR_ROCK_CHANGED")
                valid=threshold and (x,y) in occupied and any(verified_original_lake_entry(e,mid,mapping)
                    for e in world.attrs["@events"].values() if (e.attrs["@x"],e.attrs["@y"])==(x,y))
                if not valor_rock_mask_allowed(threshold,(x,y) in occupied,valid,post_chase_story):
                    continue
                passages[mid][x,y]=0
            for m,x,y in blocked_cells:
                if m==mid:passages[mid].pop((x,y),None)
            free[mid]=set(passages[mid])-occupied
            index[mid],groups[mid]=index_components(free[mid],passages[mid])
            if post_chase_story:
                # An actual transfer can land on an automatic through portal.
                # Such a cell can be left, but stepping onto it must trigger
                # the transfer rather than silently connecting components.
                for (m,xy),trigger in sorted(portal_events.items()):
                    if m!=mid or trigger not in (1,2) or xy not in passages[mid]:continue
                    adjacent=[q for q in teleport.neighbours(*xy) if q in free[mid] and
                        step_allowed(passages[mid][xy],passages[mid][q],(q[0]-xy[0],q[1]-xy[1]))]
                    if not adjacent:continue
                    label=len(groups[mid])
                    groups[mid].append({xy});index[mid][xy]=label
                    arrival_only[mid,xy]=adjacent
        else:
            free[mid]=conn.safe_cells(world,tiles,reverse[mid],allowed={0,2})-occupied
            index[mid],groups[mid]=index_components(free[mid])
    edges={};seeds=set();counts=Counter()
    def add(a,b,kind):
        if a is None or b is None:return
        targets=edges.setdefault(a,set())
        if b not in targets:targets.add(b);counts[kind]+=1
    def node(mid,xy):
        if mid not in index or xy not in index[mid]:return None
        return mid,index[mid][xy]
    for (mid,xy),neighbours in arrival_only.items():
        for q in neighbours:add(node(mid,xy),node(mid,q),"existing_portal_arrival_exit")
    if seed_cells is None:
        for row in teleport.build(blobs,mapping,components,root):
            if row[3] and (seed_symbols is None or row[0] in seed_symbols):
                mid,x,y=row[3];n=node(mid,(x,y))
                if n is not None:seeds.add(n)
    else:
        for mid,x,y in seed_cells:
            n=node(mid,(x,y))
            if n is not None:seeds.add(n)
    for mid,world in worlds.items():
        for e in world.attrs["@events"].values():
            transfer,why=conn.classify_transfer(e)
            if not transfer and post_chase_story:transfer=verified_verity_entry(e,mid,mapping) or verified_original_lake_entry(e,mid,mapping)
            if not transfer:continue
            x,y,dst,dx,dy,_,_=transfer
            # Native action portal can be activated from a safe adjacent cell.
            # Touch portals require the event cell itself to be ordinary ground.
            trigger=e.attrs["@pages"][0].attrs.get("@trigger")
            if trigger!=0 and not directional and not cell_shape(world,tiles,(x,y))["ordinary_walkable"]:continue
            for xy in teleport.neighbours(x,y):
                if trigger!=0 and directional:
                    p=passages[mid]
                    if xy not in p or (x,y) not in p or not step_allowed(p[xy],p[x,y],(x-xy[0],y-xy[1])):continue
                add(node(mid,xy),node(dst,(dx,dy)),"simple_existing_portal")
    for a,da,oa,b,db,ob in pv.parse_connections(blobs["PBS/map_connections.txt"]):
        if a not in worlds or b not in worlds or conn.OPPOSITE.get(da)!=db:continue
        for src,sd,so,dst,dd,do in ((a,da,oa,b,db,ob),(b,db,ob,a,da,oa)):
            sw,sh=worlds[src].attrs["@width"],worlds[src].attrs["@height"]
            dw,dh=worlds[dst].attrs["@width"],worlds[dst].attrs["@height"]
            for axis in pv.edge_axis(free[src],(sw,sh),sd,so):
                i=axis+so;j=axis+do
                x=(i,0 if sd=="N" else sh-1) if sd in ("N","S") else (0 if sd=="W" else sw-1,i)
                y=(j,0 if dd=="N" else dh-1) if dd in ("N","S") else (0 if dd=="W" else dw-1,j)
                if directional and (x not in passages[src] or y not in passages[dst] or
                    passages[src][x]&EDGE_BITS[sd] or passages[dst][y]&EDGE_BITS[dd]):continue
                if post_chase_story and ((src,x) in arrival_only or (dst,y) in arrival_only):continue
                if (src,*x,dst,*y) not in blocked_lanes:add(node(src,x),node(dst,y),"existing_continuous_edge")
    reached=closure(edges,seeds)
    if edge_sink is not None:
        edge_sink.clear();edge_sink.update({k:set(v) for k,v in edges.items()})
    return worlds,tiles,index,groups,reached,{"seed_components":len(seeds),"reachable_components":len(reached),"edge_counts":dict(counts),**({"movement_model":"BOTH_DIRECTION_BITS_CONSERVATIVE"} if directional else {})}

def audit(blobs,mapping,components,path,root=f.ROOT):
    if len(mapping)!=131 or len(set(mapping.values()))!=131:raise ValueError("F10B7_MAPIDS")
    source,_,_=conn.graph(root)
    source={**source,**{r["source_id"]:r for r in f08c.rows(root)}}
    if len(source)!=127:raise ValueError("F10B7_SOURCE_COUNT")
    worlds,tiles,index,groups,reached,graph=access_graph(blobs,mapping,components,root)
    rows=[];inventory=Counter();extra=[]
    with pv.verified_archive(path,"maps") as z:
        donor_tiles=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F10B7_SOURCE_TILES")
        for sid,record in sorted(source.items()):
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=record["sha256"]:raise ValueError("F10B7_SOURCE_HASH")
            donor=conn.read_marshal(raw,"F10B7_SOURCE")
            mid=mapping[record["symbol"]]
            for eid,event in sorted(donor.attrs["@events"].items()):
                literal,why=f.literal_identity(event)
                shape=f10a.classify(event)
                inventory["source_events"]+=1
                if literal:
                    inventory["literal_battle_identities"]+=1
                    if shape["kind"]!="trainer_candidate":
                        inventory["outside_original_trainer_queue"]+=1
                        extra.append({"source_id":sid,"source_event_id":eid,"kind":shape["kind"],
                                      "literal_type":literal[0],"literal_name":literal[1]})
                if (sid,eid) not in PENDING:continue
                name,kind,hypothesis=PENDING[sid,eid]
                if literal!=(kind,name):raise ValueError("F10B7_LITERAL_IDENTITY_CHANGED")
                xy=(event.attrs["@x"],event.attrs["@y"])
                label=index[mid].get(xy);group=groups[mid][label] if label is not None else set()
                incoming=[]
                for other_id,other in sorted(donor.attrs["@events"].items()):
                    if other_id==eid:continue
                    if not conn.static_targets({other_id:other}):continue
                    transfer,reason=conn.classify_transfer(other)
                    incoming.append({"event_id":other_id,"position":[other.attrs["@x"],other.attrs["@y"]],
                                     "target_source_ids":sorted(conn.static_targets({other_id:other})),
                                     "classification":reason})
                rows.append({"source_id":sid,"source_event_id":eid,"name":name,"type":kind,
                             "map_id":mid,"position":list(xy),"historical_hypothesis":hypothesis,
                             "source_cell":cell_shape(donor,donor_tiles,xy),
                             "qa_cell":cell_shape(worlds[mid],tiles,xy),
                             "qa_neighbors":[{"position":list(n),"cell":cell_shape(worlds[mid],tiles,n)}
                                             for n in teleport.neighbours(*xy)],
                             "ordinary_component_size":len(group),
                             "reachable_from_existing_entries":label is not None and (mid,label) in reached,
                             "non_articulation":f.non_cut(group,xy),
                             "source_event_gate_shape":gate_shape(event),"source_map_transfers":incoming,
                             "historical_gate_proven":False,"installed":False})
    if len(rows)!=len(PENDING) or inventory["source_events"]!=2124:raise ValueError("F10B7_INVENTORY_CHANGED")
    return {"maps_audited":131,"source_maps_audited":127,"pending_candidates":len(rows),
            "rows":rows,"ordinary_access_graph":graph,"literal_inventory":dict(inventory),
            "additional_literal_candidates":extra,"new_trainers":0,"native_verified":False,
            "water_enabled":False,"field_gates_enabled":False,"source_scripts_executed":False,
            "saves_accessed":False}
