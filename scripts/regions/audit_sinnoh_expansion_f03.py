#!/usr/bin/env python3
"""F03: read-only inventory of the two SHA-pinned original ZIPs.
No extraction, donor code execution, installation, saves or asset publication.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import unicodedata

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from audit_sinnoh_rxdata import read_marshal
from server.ruby_marshal import RubyObject, RubyData, text
from sinnoh_private_visual import PACKS, MAP_ROOT, member, verified_archive, dims, DONOR, LAKEFRONT, INTERIOR_SIZES
from sinnoh_qa_teleport import catalog

MAP_RE=re.compile(r"Map(\d+)\.rxdata",re.I)
# Explicit name aliases only; no fuzzy binding or invented source IDs.
ALIASES={"SINNOH_PROFESSOR_ROWAN_LABORATORY":["Rowan's Lab","Professor Rowan's Lab","Rowan Laboratory"],
         "SINNOH_MT_CORONET_INTERIOR_ROUTES":["Mt. Coronet"],
         "SINNOH_MT_CORONET_WEST_APPROACH":["Mt. Coronet"],
         "SINNOH_MT_CORONET_SUMMIT_ASCENT":["Mt. Coronet"],
         "SINNOH_ANCIENT_TOWER":["Hallowed Tower"]}
PREPARED=set(DONOR)|{LAKEFRONT}|set(INTERIOR_SIZES)

def norm(s):
    return re.sub(r"[^a-z0-9]","",unicodedata.normalize("NFKD",s).encode("ascii","ignore").decode().lower())

def index(z):
    result={}
    for i in z.infolist():
        # ZipInfo normalizes separators on Windows. Inspect the raw name
        # before trusting the normalized filename or skipping directories.
        name=i.orig_filename
        if name!=i.filename or "\x00" in name:
            raise ValueError("F03_UNSAFE_MEMBER")
        if name.startswith("/") or "\\" in name or ".." in name.split("/") or re.match(r"^[A-Za-z]:",name) or ((i.external_attr>>16)&0o170000)==0o120000:
            raise ValueError("F03_UNSAFE_MEMBER")
        if i.is_dir():continue
        key=name.casefold()
        if key in result:raise ValueError("F03_DUPLICATE_MEMBER")
        result[key]=name
    return result

def obj(value,kind):
    if not isinstance(value,RubyObject) or value.name!=kind:raise ValueError("F03_EXPECTED_"+kind)
    return value.attrs

def table(raw,shape):
    if not isinstance(raw,RubyData) or raw.name!="Table" or len(raw.data)<20:
        raise ValueError("F03_BAD_TABLE")
    dim,w,h,z,n=struct.unpack_from("<5I",raw.data)
    if (dim,w,h,z)!=shape or n!=w*h*z or len(raw.data)!=20+2*n:
        raise ValueError("F03_BAD_TABLE_SHAPE")
    return struct.unpack_from("<%dH"%n,raw.data,20)

def table1(raw):
    if not isinstance(raw,RubyData) or len(raw.data)<20:raise ValueError("F03_BAD_TILE_TABLE")
    n=struct.unpack_from("<I",raw.data,4)[0]
    return table(raw,(1,n,1,1))

def png_row(z,path):
    raw=member(z,path)
    w,h=dims(raw)
    if not (0<w<=32768 and 0<h<=32768):raise ValueError("F03_PNG_DIMENSIONS")
    return {"path":path,"width":w,"height":h,"sha256":hashlib.sha256(raw).hexdigest()}

def audit_maps(z):
    ix=index(z)
    infos=read_marshal(member(z,MAP_ROOT+"Data/MapInfos.rxdata"),"F03_INFOS")
    tiles=read_marshal(member(z,MAP_ROOT+"Data/Tilesets.rxdata"),"F03_TILES")
    if not isinstance(infos,dict) or any(type(i) is not int or i<=0 for i in infos):raise ValueError("F03_MAPINFOS")
    if not isinstance(tiles,(list,dict)):raise ValueError("F03_TILESETS")
    files={}
    for p in ix.values():
        if not p.casefold().startswith((MAP_ROOT+"Data/").casefold()):continue
        m=MAP_RE.fullmatch(p[len(MAP_ROOT+"Data/"):])
        if m:
            mid=int(m[1])
            if mid<=0 or mid in files:raise ValueError("F03_DUPLICATE_MAP_ID")
            files[mid]=p
    if not files:raise ValueError("F03_NO_MAPS")
    cache={}
    def graphics(folder,name):
        if not name:return None
        if "/" in name or "\\" in name or name in (".",".."):return {"name":name,"status":"invalid_reference"}
        key=(MAP_ROOT+"Graphics/"+folder+"/"+name+".png").casefold()
        if key not in ix:return {"name":name,"status":"missing"}
        if key not in cache:
            try:cache[key]={"status":"present",**png_row(z,ix[key])}
            except (ValueError,OSError,struct.error):cache[key]={"status":"invalid_png","name":name}
        return cache[key]
    tsrows={};tables={}
    for tid,t in (enumerate(tiles) if isinstance(tiles,list) else sorted(tiles.items())):
        if not t or tid==0:continue
        row={"source_tileset_id":tid,"issues":[]}
        try:
            a=obj(t,"RPG::Tileset")
            row["name"]=text(a.get("@name",b""))
            row["sheet"]=graphics("Tilesets",text(a.get("@tileset_name",b"")))
            row["autotiles"]=[graphics("Autotiles",text(n)) for n in a["@autotile_names"]]
            if row["sheet"] is None or row["sheet"]["status"]!="present" or any(g and g["status"]!="present" for g in row["autotiles"]):row["issues"].append("graphic_missing_or_invalid")
            p,pr,tags=[table1(a[k]) for k in ("@passages","@priorities","@terrain_tags")]
            if not len(p)==len(pr)==len(tags):raise ValueError("table_lengths")
            tables[tid]=p
            row["table_entries"]=len(p)
        except (ValueError,TypeError,KeyError,IndexError,struct.error) as exc:
            row["issues"].append("invalid_tileset:"+type(exc).__name__)
        tsrows[tid]=row
    maps=[]
    for mid in sorted(set(files)|set(infos)):
        row={"source_id":mid,"name":"","parent_id":None,"issues":[],"destination_map_id":None}
        if mid in infos:
            a=obj(infos[mid],"RPG::MapInfo")
            row.update(name=text(a.get("@name",b"")).strip(),parent_id=a.get("@parent_id"))
        else:row["issues"].append("missing_mapinfo")
        if mid not in files:row["issues"].append("missing_map_file");maps.append(row);continue
        try:
            raw=member(z,files[mid])
            a=obj(read_marshal(raw,"F03_MAP"),"RPG::Map")
            w,h,tid=a["@width"],a["@height"],a["@tileset_id"]
            if not all(type(x) is int for x in (w,h,tid)) or not (0<w<=500 and 0<h<=500):raise ValueError("dimensions")
            cells=table(a["@data"],(3,w,h,3))
            row.update(width=w,height=h,source_tileset_id=tid,sha256=hashlib.sha256(raw).hexdigest(),nonzero_tiles=sum(v!=0 for v in cells))
            if not row["nonzero_tiles"]:row["issues"].append("empty_geometry")
            if tid not in tables or tsrows[tid]["issues"]:row["issues"].append("tileset_unresolved")
            if tid in tables and max(cells)>=len(tables[tid]):row["issues"].append("tile_id_out_of_table")
            events=a["@events"]
            if not isinstance(events,dict):raise ValueError("events")
            row["donor_events"]=len(events)
            refs=set();scripts=0
            for e in events.values():
                for page in obj(e,"RPG::Event").get("@pages",[]):
                    pa=obj(page,"RPG::Event::Page")
                    for c in pa.get("@list",[]):
                        ca=obj(c,"RPG::EventCommand")
                        if ca.get("@code") in (355,655):scripts+=1
                        args=ca.get("@parameters",[])
                        if ca.get("@code")==201 and len(args)>1 and args[0]==0 and type(args[1]) is int:refs.add(args[1])
            row["donor_scripts_not_executed"]=scripts
            row["static_transfer_targets"]=sorted(refs)
            row["unresolved_transfer_targets"]=sorted(refs-set(files))
        except (ValueError,TypeError,KeyError,IndexError,struct.error) as exc:
            row["issues"].append("invalid_map:"+type(exc).__name__)
        maps.append(row)
    return maps,list(tsrows.values())

def reconcile(rows,maps):
    byname={}
    for m in maps:
        if m["name"]:byname.setdefault(norm(m["name"]),[]).append(m)
    out=[]
    for r in rows:
        names=[r["label"],*ALIASES.get(r["symbol"],[])]
        matches={m["source_id"]:m for n in names for m in byname.get(norm(n),[])}
        ready=[m["source_id"] for m in matches.values() if not m["issues"]]
        state="unique_candidate" if len(matches)==1 and len(ready)==1 else "ambiguous" if len(matches)>1 else "blocked_candidate" if matches else "no_exact_match"
        out.append({**r,"source_candidates":sorted(matches),"geometry_candidates":sorted(ready),
                    "source_status":state,"prepared_in_pilot":r["symbol"] in PREPARED,
                    "destination_map_id":None,"import_approved":False})
    return out

def inventory(paths):
    with verified_archive(paths["maps"],"maps") as z:maps,tilesets=audit_maps(z)
    sprites=[]
    with verified_archive(paths["overworlds"],"overworlds") as z:
        for p in sorted(index(z).values()):
            if not p.lower().endswith(".png"):continue
            try:sprites.append({"status":"present",**png_row(z,p)})
            except (ValueError,OSError,struct.error):sprites.append({"status":"invalid_png","path":p})
    if not sprites:raise ValueError("F03_NO_SPRITES")
    destinations=reconcile(catalog(),maps)
    bycat={}
    for cat in sorted({r["category"] for r in destinations}):
        rr=[r for r in destinations if r["category"]==cat]
        bycat[cat]={"total":len(rr),"prepared":sum(r["prepared_in_pilot"] for r in rr),"source_status":dict(Counter(r["source_status"] for r in rr))}
    cities=[r for r in destinations if r["category"]=="Cidades e vilarejos"]
    return {"schema":1,"mode":"PINNED_SOURCE_READ_ONLY","source_sha256":{k:v[1] for k,v in PACKS.items()},
            "maps":maps,"tilesets":tilesets,"sprites":sprites,"destinations":destinations,"categories":bycat,
            "counts":{"map_records":len(maps),"map_files":sum("missing_map_file" not in m["issues"] for m in maps),
                      "geometry_candidates":sum(not m["issues"] for m in maps),"tilesets":len(tilesets),
                      "sprites":len(sprites),"valid_sprite_headers":sum(s["status"]=="present" for s in sprites)},
            "f04_city_queue":cities,"rights_approved":False,"native_qa_verified":False,"installed_new_maps":0}

def local_capacity(base,existing):
    # Read actual game/Data, never open save files. Require the exact prior
    # mapping to preserve old IDs; this is a capacity proposal, not allocation.
    from install_sinnoh_experimental_windows import native_map_ids
    infos=read_marshal((base/"Data/MapInfos.rxdata").read_bytes(),"F03_BASE")
    occupied=set(infos)|native_map_ids(base)
    old=list(existing.values())
    if set(existing)!=PREPARED or len(set(old))!=10 or any(type(n) is not int or not 442<=n<=517 or n in occupied for n in old):
        raise ValueError("F03_EXISTING_MAPIDS_CONFLICT")
    free=[i for i in range(442,518) if i not in occupied and i not in old]
    return {"occupied_count":len(occupied),"prior_mapids":existing,"unallocated_qa_capacity":len(free),
            "f04_twelve_city_capacity":len(free)>=12,"base_mapinfos_sha256":hashlib.sha256((base/"Data/MapInfos.rxdata").read_bytes()).hexdigest(),
            "allocated":False,"r07_approved":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--maps",type=Path,required=True);p.add_argument("--overworlds",type=Path,required=True)
    p.add_argument("--base",type=Path);p.add_argument("--prior-manifest",type=Path)
    p.add_argument("--summary",action="store_true",help="Emit only counts, category statuses and F04 city candidates")
    a=p.parse_args()
    if bool(a.base)!=bool(a.prior_manifest):p.error("base and prior manifest must be supplied together")
    report=inventory({"maps":a.maps,"overworlds":a.overworlds})
    if a.base:report["local_capacity"]=local_capacity(a.base,json.loads(a.prior_manifest.read_text("utf-8"))["mapids"])
    if a.summary:report={k:report[k] for k in ("schema","mode","source_sha256","counts","categories","f04_city_queue","rights_approved","native_qa_verified","installed_new_maps")}
    print(json.dumps(report,ensure_ascii=True,indent=2))
if __name__=="__main__":main()
