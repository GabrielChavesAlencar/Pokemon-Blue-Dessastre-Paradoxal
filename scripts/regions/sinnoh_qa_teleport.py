"""F01: catalog-driven private QA teleport, with conservative spawn checks."""
import json
import re
import struct
from collections import deque
from pathlib import Path
from audit_sinnoh_rxdata import read_marshal

ROOT=Path(__file__).resolve().parents[2]
CATALOG="data/regions/sinnoh-expansion-destinations.json"

def catalog(root=ROOT):
    data=json.loads((root/CATALOG).read_text("utf-8"))
    rows=data["destinations"]
    keys=[r["symbol"] for r in rows]
    if data["region"]!="SINNOH" or len(keys)!=len(set(keys)) or any(not re.fullmatch(r"SINNOH_[A-Z0-9_]+",k) for k in keys):
        raise ValueError("SINNOH_F01_CATALOG_INVALID")
    if {r["symbol"] for r in rows if r["category"]=="Rotas"}!={f"SINNOH_ROUTE_{n}" for n in range(201,231)}:
        raise ValueError("SINNOH_F01_ROUTES_INCOMPLETE")
    if sum(r["category"]=="Cidades e vilarejos" for r in rows)!=14:
        raise ValueError("SINNOH_F01_CITIES_INCOMPLETE")
    return rows

def arrival_policy(symbol=None):
    # Exact F05 exceptions, never applied to prior maps or other routes.
    # 165: only four fully passable tag-0 cells, all on the map boundary.
    # 142: Essentials Rock (4) is a battle environment, not a movement mode.
    # Require a connected ordinary/rock pocket; never admit grass or water.
    if symbol=="SINNOH_ROUTE_225_SEGMENT_2":
        return frozenset({0}),True,1,2
    if symbol=="SINNOH_ROUTE_228_SEGMENT_2":
        return frozenset({0,4}),False,2,12
    return frozenset({0}),False,2,12

def arrival_ground(cells,w,h,passages,tags,symbol=None):
    allowed,edge,_,_=arrival_policy(symbol)
    return {(x,y) for y in range(h) for x in range(w)
            if (edge or (0<x<w-1 and 0<y<h-1))
            and (stack:=[cells[z*w*h+y*w+x] for z in range(3) if cells[z*w*h+y*w+x]])
            and all(i<len(passages) and i<len(tags) and not passages[i]&15 and tags[i] in allowed for i in stack)}

def neighbours(x,y):
    return ((x-1,y),(x+1,y),(x,y-1),(x,y+1))

def safe_spawn(raw,tiles,component,symbol=None):
    m=read_marshal(raw,"F01_MAP").attrs
    w,h=m["@width"],m["@height"]
    ts=tiles[m["@tileset_id"]].attrs
    p=ts["@passages"].data[20:]
    t=ts["@terrain_tags"].data[20:]
    passages=struct.unpack("<%dH"%(len(p)//2),p)
    tags=struct.unpack("<%dH"%(len(t)//2),t)
    cells=struct.unpack_from("<%dH"%(w*h*3),m["@data"].data,20)
    events={(e.attrs["@x"],e.attrs["@y"]) for e in m["@events"].values()}
    ground=arrival_ground(cells,w,h,passages,tags,symbol)
    _,_,min_neighbours,_=arrival_policy(symbol)
    if component is not None: ground.intersection_update(component)
    # Stay away from events/warps and require an unobstructed adjacent tile.
    free=ground-events
    choices=[(x,y) for x,y in free if all(abs(x-a)+abs(y-b)>1 for a,b in events)
             and sum(q in free for q in neighbours(x,y))>=min_neighbours]
    if not choices: raise ValueError("SINNOH_F01_NO_SAFE_SPAWN")
    # For the narrow boundary strip prefer the greatest number of exits.
    if symbol=="SINNOH_ROUTE_225_SEGMENT_2":
        return min(choices,key=lambda q:(-sum(n in free for n in neighbours(*q)),abs(q[0]-w//2)+abs(q[1]-h//2),q[1],q[0]))
    return min(choices,key=lambda q:(abs(q[0]-w//2)+abs(q[1]-h//2),q[1],q[0]))

def build(blobs,mapping,components,root=ROOT):
    rows=catalog(root)
    # F05 adds six segment entries only when those maps are installed.
    if any("_SEGMENT_" in sym for sym in mapping):
        from sinnoh_route_expansion import extra_destinations
        rows += extra_destinations(root)
    if not set(mapping)<={r["symbol"] for r in rows}:
        raise ValueError("SINNOH_F01_UNCATALOGUED_MAP")
    if len(set(mapping.values()))!=len(mapping):
        raise ValueError("SINNOH_F01_MAPID_COLLISION")
    tiles=read_marshal(blobs["Data/Tilesets.rxdata"],"F01_TILESETS")
    entries=[]
    for row in rows:
        sym=row["symbol"]
        dest=None
        if sym in mapping:
            mid=mapping[sym]
            x,y=safe_spawn(blobs["Data/Map%03d.rxdata"%mid],tiles,components.get(sym),sym)
            dest=[mid,x,y]
        entries.append([sym,row["label"],row["category"],dest])
    return entries

def plugin(entries,root=ROOT):
    # JSON arrays/strings/integers are also Ruby literals after null -> nil.
    literal="[\n"+",\n".join(
        "["+",".join(json.dumps(v,ensure_ascii=False) for v in row[:3])+","+
        (str(row[3]) if row[3] is not None else "nil")+"]" for row in entries)+"\n]"
    body=(root/"scripts/regions/SinnohQATeleport.rb").read_text("utf-8")
    if body.count("__F01_DESTINATIONS__")!=1:raise ValueError("SINNOH_F01_TEMPLATE_INVALID")
    return body.replace("__F01_DESTINATIONS__",literal).encode("utf-8")
