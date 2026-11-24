"""F08C: four verified original exteriors and append-only reciprocal doors."""
import hashlib
import json
from pathlib import Path
import sinnoh_city_expansion as city
import sinnoh_interior_expansion as interior
import sinnoh_natural_expansion as natural
import sinnoh_connection_expansion as conn

ROOT=Path(__file__).resolve().parents[2]
SYMBOLS={139:"SINNOH_RESORT_AREA",147:"SINNOH_CYCLING_ROAD",163:"SINNOH_SURVIVAL_AREA",166:"SINNOH_FIGHT_AREA"}
EXTERIORS=frozenset(SYMBOLS.values())
ALL=interior.ALL|EXTERIORS
COUNT=131
CATALOG="data/regions/sinnoh-f08c-exterior-sources.json"
BASELINE="data/regions/sinnoh-f08b-approved-portals.json"

def rows(root=ROOT):
    doc=json.loads((root/CATALOG).read_text("utf-8"))
    r=doc["source_maps"]
    if doc["schema"]!=1 or doc["scope"]!="PRIVATE_QA_ONLY" or len(r)!=4 or {x["source_id"]:x["symbol"] for x in r}!=SYMBOLS or any(x["source_tileset_id"]!=24 or x["outdoor"] is not True for x in r):
        raise ValueError("F08C_INVALID_CATALOG")
    return r

def allocate(mapping,occupied,root=ROOT):
    if set(mapping)!=interior.ALL or len(set(mapping.values()))!=127 or any(type(i) is not int or not 442<=i<=natural.PRIVATE_MAX for i in mapping.values()) or set(mapping.values())&occupied:
        raise ValueError("F08C_PRIOR_MAPIDS_CHANGED")
    free=[i for i in range(442,natural.PRIVATE_MAX+1) if i not in occupied and i not in mapping.values()]
    if len(free)<4:raise ValueError("F08C_INSUFFICIENT_FREE_MAPIDS")
    return {**mapping,**{r["symbol"]:i for r,i in zip(rows(root),free)}}

def extra_destinations(root=ROOT):
    return [{k:r[k] for k in ("symbol","label","category")} for r in rows(root)]

def signature(p):
    return {"source_id":p["source_id"],"source_event_id":p["source_event_id"],"target_source_id":p["target_source_id"],
        "from_xy":p["from"][1:],"to_xy":p["to"][1:],"trigger":p["trigger"],"event_id":p["event_id"]}

def append(blobs,mapping,components,path,occupied,baseline,root=ROOT):
    pinned=json.loads((root/BASELINE).read_text("utf-8"))
    if [signature(p) for p in baseline["portals"]]!=pinned["portals"] or [s["source_ids"] for s in baseline["seams"]]!=pinned["seams"]:
        raise ValueError("F08C_BASELINE_CHANGED")
    out,expanded,comps,report=city.append_exteriors(blobs,mapping,components,path,allocate(mapping,occupied,root),rows(root),"F08C")
    entries=city.teleport.build(out,expanded,comps,root)
    arrivals={r[0]:tuple(r[3][1:]) for r in entries if r[3]}
    source,_,_=conn.graph(root)
    source={**source,**{r["source_id"]:r for r in rows(root)}}
    pairs={(a,b) for a,r in source.items() for b in r["targets"] if b in source and a!=b and (a in SYMBOLS or b in SYMBOLS) and a in source[b]["targets"]}
    relevant={a for a,b in pairs}
    worlds={source[a]["symbol"]:conn.read_marshal(out["Data/Map%03d.rxdata"%expanded[source[a]["symbol"]]],"F08C_MAP") for a in relevant}
    tiles=conn.read_marshal(out["Data/Tilesets.rxdata"],"F08C_TILES")
    safe={s:conn.safe_cells(m,tiles,s)&comps[s] for s,m in worlds.items()}
    used={s:{(e.attrs["@x"],e.attrs["@y"]) for e in m.attrs["@events"].values()} for s,m in worlds.items()}
    raw=[];rejected=[]
    with conn.pv.verified_archive(path,"maps") as z:
        for a in sorted(relevant):
            r=source[a];sym=r["symbol"];data=conn.pv.member(z,conn.pv.MAP_ROOT+"Data/Map%03d.rxdata"%a)
            if hashlib.sha256(data).hexdigest()!=r["sha256"]:raise ValueError("F08C_SOURCE_MAP_HASH")
            events=conn.read_marshal(data,"F08C_DONOR").attrs["@events"]
            if conn.static_targets(events)!=set(r["targets"]):raise ValueError("F08C_SOURCE_GRAPH_CHANGED")
            for eid,event in sorted(events.items()):
                targets=conn.static_targets({eid:event})
                if not any((a,b) in pairs for b in targets):continue
                result,reason=conn.classify_transfer(event)
                if result is None:
                    rejected.append({"source_id":a,"event_id":eid,"reason":reason,"targets":sorted(targets)});continue
                x,y,b,dx,dy,direction,fade=result
                if (a,b) not in pairs:continue
                dest=source[b]["symbol"];wa,wb=worlds[sym].attrs,worlds[dest].attrs
                if not (0<=x<wa["@width"] and 0<=y<wa["@height"] and 0<=dx<wb["@width"] and 0<=dy<wb["@height"]):
                    rejected.append({"source_id":a,"event_id":eid,"reason":"out_of_bounds","targets":[b]});continue
                raw.append({"source_id":a,"source_event_id":eid,"target_source_id":b,"symbol":sym,
                    "from":[expanded[sym],x,y],"to":[expanded[dest],dx,dy],"direction":direction,"fade":fade,"trigger":0})
    # Lock all 63 existing portal positions and their landing tiles. New pairs
    # cannot trigger an old automatic portal or place a new event on a landing.
    old=baseline["portals"];reserved={tuple(p["to"]) for p in old};old_touch={tuple(p["from"]) for p in old if p["trigger"]!=0}
    claimed=set();added=[]
    for r in raw:
        key=(r["source_id"],r["source_event_id"])
        if key in claimed:continue
        def matches(e):
            return [w for w in raw if w["source_id"]==e["target_source_id"] and w["target_source_id"]==e["source_id"]
                and conn.near_door(w["from"][1:],e["to"][1:]) and conn.near_door(w["to"][1:],e["from"][1:])]
        reverse=matches(r)
        if len(reverse)!=1 or matches(reverse[0])!=[r]:continue
        w=reverse[0];wkey=(w["source_id"],w["source_event_id"])
        if wkey in claimed:continue
        pair=[]
        for e,other in ((r,w),(w,r)):
            sym=e["symbol"];dest=source[e["target_source_id"]]["symbol"]
            mid,x,y=e["from"];dst,dx,dy=e["to"];origin=(x,y);landing=tuple(other["to"][1:])
            if (dx,dy) not in safe[dest] or (dx,dy) in used[dest] or tuple(e["to"]) in old_touch or origin in used[sym]:break
            if origin in safe[sym]:approach=origin
            elif conn.distance(origin,landing)==1 and landing in safe[sym]:approach=landing
            else:approach=conn.diagonal_approach(origin,landing,safe[sym])
            if approach is None or approach in used[sym] or (mid,*approach) in reserved or conn.distance(approach,arrivals[sym])<=1:break
            if not any(n in safe[sym] for n in city.teleport.neighbours(*approach)) or not any(n in safe[dest] for n in city.teleport.neighbours(dx,dy)):break
            pair.append({**e,"original_from":e["from"],"from":[mid,*approach]})
        if len(pair)!=2:continue
        for e in pair:
            sym=e["symbol"];mid,x,y=e["from"];dst,dx,dy=e["to"]
            events=worlds[sym].attrs["@events"];eid=max(events,default=0)+1
            page=conn.event_page(warp=(dst,dx,dy),touch=False)
            page.attrs["@through"]=True
            page.attrs["@list"][0].attrs["@parameters"][4:6]=[e["direction"],e["fade"]]
            events[eid]=conn.ruby("RPG::Event",id=eid,name=("SN_F08C_PORTAL_%d_%d"%(e["source_id"],e["source_event_id"])).encode("ascii"),x=x,y=y,pages=[page])
            used[sym].add((x,y));e["event_id"]=eid;added.append(e)
        claimed.update((key,wkey))
    for sym in {e["symbol"] for e in added}:
        out["Data/Map%03d.rxdata"%expanded[sym]]=conn.serialize(worlds[sym],conn.EVENT_CLASSES)
    if city.teleport.build(out,expanded,comps,root)!=entries:raise ValueError("F08C_QA_SPAWN_CHANGED")
    for e in raw:
        if (e["source_id"],e["source_event_id"]) not in claimed:rejected.append({"source_id":e["source_id"],"event_id":e["source_event_id"],"reason":"reciprocal_geometry_or_collision","targets":[e["target_source_id"]],"from":e["from"],"to":e["to"]})
    links={(e["source_id"],e["target_source_id"]) for e in added}
    stats={"maps":report,"portals":added,"new_portals":len(added),"new_directed":len(links),"new_pairs":sum(a<b and (b,a) in links for a,b in links),"eligible_directed":len(pairs),"rejected":rejected,"native_verified":False}
    print("SINNOH_F08C_REPORT "+json.dumps(stats,sort_keys=True),flush=True)
    return out,expanded,comps,stats
