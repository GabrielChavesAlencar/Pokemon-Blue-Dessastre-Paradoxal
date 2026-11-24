"""F04: append twelve original city exteriors to the isolated pilot.
Never import donor events/scripts, mutate existing map bytes or touch saves.
"""
import copy
import hashlib
import json
import re
import struct
from collections import deque
from pathlib import Path

import sinnoh_private_visual as pv
import sinnoh_qa_teleport as teleport
from server.ruby_marshal import RubyData
from audit_sinnoh_rxdata import read_marshal
from stage import serialize
from build_johto_events import EVENT_CLASSES

ROOT=Path(__file__).resolve().parents[2]
CITIES=frozenset("SINNOH_"+s for s in ("JUBILIFE_CITY","OREBURGH_CITY","FLOAROMA_TOWN","ETERNA_CITY","HEARTHOME_CITY","SOLACEON_TOWN","VEILSTONE_CITY","PASTORIA_CITY","CELESTIC_TOWN","CANALAVE_CITY","SNOWPOINT_CITY","SUNYSHORE_CITY"))
OLD=frozenset(pv.DONOR)|{pv.LAKEFRONT}|frozenset(pv.INTERIOR_SIZES)
def fail(reason):raise ValueError("SINNOH_F04_"+reason)

def rows(root=ROOT):
    data=json.loads((root/"data/regions/sinnoh-f04-city-sources.json").read_text("utf-8"))
    result=data["cities"]
    if data["schema"]!=1 or len(result)!=12 or {r["symbol"] for r in result}!=CITIES or len({r["source_id"] for r in result})!=12:
        fail("INVALID_CITY_CATALOG")
    return result

def allocate(mapping,occupied,root=ROOT):
    if set(mapping)!=OLD or len(set(mapping.values()))!=10 or set(mapping.values())&occupied:
        fail("PILOT_MAPIDS_CHANGED")
    free=[i for i in range(442,518) if i not in occupied and i not in mapping.values()]
    if len(free)<12:fail("INSUFFICIENT_FREE_CITY_MAPIDS")
    return {**mapping,**{r["symbol"]:mid for r,mid in zip(rows(root),free)}}

def component(cells,w,h,p,tags=None):
    # Choose the largest conservative walking component that contains an
    # ordinary-ground arrival AND two ordinary-ground neighbours, rather
    # than the largest component regardless of terrain.
    free={(x,y) for y in range(h) for x in range(w)
          if (stack:=[cells[z*w*h+y*w+x] for z in range(3) if cells[z*w*h+y*w+x]])
          and all(t<len(p) and not p[t]&15 for t in stack)}
    ground={q for q in free if 0<q[0]<w-1 and 0<q[1]<h-1 and
            (tags is None or all(tags[t]==0 for z in range(3)
            if (t:=cells[z*w*h+q[1]*w+q[0]])))}
    arrivals={q for q in ground if sum(n in ground for n in
              ((q[0]-1,q[1]),(q[0]+1,q[1]),(q[0],q[1]-1),(q[0],q[1]+1)))>=2}
    best=set()
    while free:
        seed=min(free,key=lambda q:(q[1],q[0]))
        part={seed};free.remove(seed);todo=deque([seed])
        while todo:
            x,y=todo.popleft()
            for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if q in free:free.remove(q);part.add(q);todo.append(q)
        if len(part)>len(best) and part & arrivals:best=part
    if len(best)<12:
        fail("NO_SAFE_WALKABLE_COMPONENT:ordinary_ground=%d:arrival_candidates=%d"%(len(ground),len(arrivals)))
    return best

def city_atlases(raw,sets):
    """Decode pinned source once, produce independent compact city atlases."""
    groups={};out={};remaps={}
    for sym,ids in sets.items():
        if not ids or any(t<384 or t>=7880 for t in ids):fail("INVALID_TILE_ID")
        remap={t:384+i for i,t in enumerate(sorted(ids))}
        h=((len(ids)+7)//8)*32
        if h>4096:fail("CITY_ATLAS_TOO_TALL")
        out[sym]=(h,bytearray(256*h*4));remaps[sym]=remap
        for old,new in remap.items():
            old-=384;new-=384
            groups.setdefault(old//8,[]).append((sym,old%8,new%8,new//8))
    for y,row in enumerate(pv.rgba_rows(raw)):
        for sym,x,nx,ny in groups.get(y//32,()):
            pos=((ny*32+y%32)*256+nx*32)*4
            out[sym][1][pos:pos+128]=row[x*128:x*128+128]
    return {sym:(pv.png(256,h,bytes(buf)),remaps[sym]) for sym,(h,buf) in out.items()}

def append(blobs,mapping,components,path,occupied,root=ROOT):
    expanded=allocate(mapping,occupied,root)
    return append_exteriors(blobs,mapping,components,path,expanded,rows(root),"F04")

def append_exteriors(blobs,mapping,components,path,expanded,source_rows,phase):
    # Appending only; existing tileset indices and map bytes are immutable.
    if not all(expanded.get(k)==v for k,v in mapping.items()) or len(set(expanded.values()))!=len(expanded):
        fail("INVALID_APPEND_MAPPING")
    if set(expanded)-set(mapping)!={r["symbol"] for r in source_rows}:
        fail("INVALID_APPEND_ROWS")
    out=dict(blobs);comps=dict(components);report={}
    infos=read_marshal(out["Data/MapInfos.rxdata"],"F04_TARGET_INFOS")
    tiles=read_marshal(out["Data/Tilesets.rxdata"],"F04_TARGET_TILES")
    template=out["Data/Map%03d.rxdata"%mapping["SINNOH_SANDGEM_TOWN"]]
    existing_tile=read_marshal(template,"F04_TEMPLATE").attrs["@tileset_id"]
    pbs=out["PBS/map_metadata.txt"]
    metadata_ids={int(n) for n in re.findall(rb"(?m)^\s*\[(\d+)\]",pbs)}
    if (set(expanded.values())-set(mapping.values())) & (set(infos)|metadata_ids):
        fail("NEW_ID_ALREADY_REGISTERED")
    with pv.verified_archive(path,"maps") as z:
        donor_infos=read_marshal(pv.member(z,pv.MAP_ROOT+"Data/MapInfos.rxdata"),"F04_SOURCE_INFOS")
        source=read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F04_SOURCE_TILES")[24]
        if source.attrs["@tileset_name"]!=b"outdoors":fail("SOURCE_TILESET")
        tables={k:pv.table(source.attrs[k],7880) for k in ("@passages","@priorities","@terrain_tags")}
        sets={};source_cells={}
        for row in source_rows:
            sym,mid=row["symbol"],row["source_id"]
            info=donor_infos[mid].attrs
            if info["@name"]!=row.get("source_name",row["label"]).encode("ascii") or info["@parent_id"]!=row.get("parent_id",0):fail("SOURCE_EXTERIOR_IDENTITY")
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%mid)
            if hashlib.sha256(raw).hexdigest()!=row["sha256"]:fail("SOURCE_MAP_HASH")
            w,h=row["width"],row["height"]
            m=read_marshal(raw,"F04_DONOR_MAP").attrs
            if (m["@width"],m["@height"],m["@tileset_id"])!=(w,h,24):fail("SOURCE_DIMENSIONS")
            data=m["@data"];n=w*h*3
            if len(data.data)!=20+2*n or struct.unpack_from("<5I",data.data)!=(3,w,h,3,n):fail("SOURCE_TABLE")
            cells=struct.unpack_from("<%dH"%n,data.data,20)
            if any(t>=7880 for t in cells):fail("SOURCE_TILE_RANGE")
            # Retain original autotile indices; reject references to empty slots.
            if any(48<=t<384 and not source.attrs["@autotile_names"][t//48-1] for t in cells):fail("SOURCE_AUTOTILE_MISSING")
            if any(0<t<48 for t in cells):fail("SOURCE_RESERVED_TILE")
            sets[sym]={t for t in cells if t>=384};source_cells[sym]=cells
            try:
                comps[sym]=component(cells,w,h,tables["@passages"],tables["@terrain_tags"])
            except ValueError as exc:
                raise ValueError("F04_CITY:"+sym+":"+str(exc)) from exc
        atlases=city_atlases(pv.member(z,pv.MAP_ROOT+"Graphics/Tilesets/outdoors.png"),sets)
    order=max(v.attrs["@order"] for v in infos.values())
    for row in source_rows:
        sym=row["symbol"];mid=expanded[sym];w,h=row["width"],row["height"];n=w*h*3
        atlas,remap=atlases[sym];tid=len(tiles)
        if tid>=5000:fail("TILESET_CAPACITY")
        tile=copy.deepcopy(source);a=tile.attrs
        name="SNQA_%s_%03d"%(phase,row["source_id"])
        a.update({"@id":tid,"@name":name.encode("ascii"),"@tileset_name":name.encode("ascii"),
                  "@autotile_names":copy.deepcopy(tiles[existing_tile].attrs["@autotile_names"])})
        total=384+((len(remap)+7)//8)*8
        for k,values in tables.items():
            entries=list(values[:384])+([15] if k=="@passages" else [0])*(total-384)
            for old,new in remap.items():entries[new]=values[old]
            a[k]=pv.table1(entries)
        tiles.append(tile);out["Graphics/Tilesets/"+name+".png"]=atlas
        m=read_marshal(template,"F04_SAFE_TEMPLATE")
        cells=source_cells[sym]
        m.attrs.update({"@width":w,"@height":h,"@tileset_id":tid,"@events":{},
                        "@data":RubyData("Table",struct.pack("<5I",3,w,h,3,n)+struct.pack("<%dH"%n,*(remap[t] if t>=384 else t for t in cells)))})
        # Deliberately retain the already verified Sandgem BGM as temporary fallback.
        rel="Data/Map%03d.rxdata"%mid
        out[rel]=serialize(m,EVENT_CLASSES)
        try:
            x,y=teleport.safe_spawn(out[rel],tiles,comps[sym])
        except ValueError as exc:
            raise ValueError("F04_CITY:"+sym+":"+str(exc)) from exc
        info=copy.deepcopy(infos[mapping["SINNOH_SANDGEM_TOWN"]]);order+=1
        info.attrs.update({"@name":row["label"].encode("ascii"),"@parent_id":0,"@order":order})
        infos[mid]=info
        pbs+=("\n# %s private exterior\n[%03d]\nName = %s\nOutdoor = true\nShowArea = true\nBicycle = true\nSnapEdges = true\n"%(phase,mid,row["label"])).encode("ascii")
        report[sym]={"source_id":row["source_id"],"target_id":mid,"width":w,"height":h,
                     "source_sha256":row["sha256"],"source_tileset_id":24,"target_tileset_id":tid,
                     "safe_spawn":[mid,x,y],"model_connected_cells":len(comps[sym]),
                     "donor_events_copied":0,"native_verified":False}
    out["Data/MapInfos.rxdata"]=serialize(infos)
    out["Data/Tilesets.rxdata"]=serialize(tiles)
    out["PBS/map_metadata.txt"]=pbs
    if any(out["Data/Map%03d.rxdata"%mid]!=blobs["Data/Map%03d.rxdata"%mid] for mid in mapping.values()):
        fail("EXISTING_MAP_CHANGED")
    return out,expanded,comps,report
