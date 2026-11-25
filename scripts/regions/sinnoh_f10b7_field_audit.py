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

def access_graph(blobs,mapping,components,root,seed_symbols=None,directional=False,seed_cells=None,strict_movement=False,rock_cells=()):
    reverse={mid:sym for sym,mid in mapping.items()}
    tiles=conn.read_marshal(blobs["Data/Tilesets.rxdata"],"F10B7_QA_TILES")
    worlds={mid:conn.read_marshal(blobs["Data/Map%03d.rxdata"%mid],"F10B7_QA") for mid in reverse}
    index={};groups={};free={};passages={}
    rock_cells=set(rock_cells)
    if rock_cells and (not directional or not strict_movement or reverse.get(473)!="SINNOH_ROUTE_210_SEGMENT_2" or not rock_cells<={(473,57,y) for y in (25,26,27)}):
        raise ValueError("F12D3_ROCK_GRAPH_SCOPE")
    for mid,world in worlds.items():
        occupied={(e.attrs["@x"],e.attrs["@y"]) for e in world.attrs["@events"].values()}
        if directional:
            passages[mid]=directional_masks(world,tiles)
            # The private movement guard rejects every stack with any passage bit.
            # Chase witnesses must not use cells that the runtime will reject.
            if strict_movement:
                passages[mid]={xy:mask for xy,mask in passages[mid].items() if mask==0}
            for _,x,y in sorted(p for p in rock_cells if p[0]==mid):
                a=world.attrs;w,h=a["@width"],a["@height"]
                shape=cell_shape(world,tiles,(x,y))
                raw=a["@data"].data
                stack=tuple(struct.unpack_from("<H",raw,20+2*(z*w*h+y*w+x))[0] for z in range(3))
                priority=struct.unpack_from("<H",tiles[a["@tileset_id"]].attrs["@priorities"].data,20+2*462)[0]
                if stack!=(462,0,0) or shape.get("passage_masks")!=[0] or shape.get("terrain_tags")!=[4] or priority!=0 or (x,y) in occupied:
                    raise ValueError("F12D3_ROCK_GRAPH_CELL_CHANGED")
                passages[mid][x,y]=0
            free[mid]=set(passages[mid])-occupied
            index[mid],groups[mid]=index_components(free[mid],passages[mid])
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
                add(node(src,x),node(dst,y),"existing_continuous_edge")
    reached=closure(edges,seeds)
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
