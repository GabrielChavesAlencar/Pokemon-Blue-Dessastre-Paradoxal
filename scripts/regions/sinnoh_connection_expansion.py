"""F08 safe subset of original transfers and seamless borders; isolated QA only."""
import hashlib
import json
import struct
from collections import Counter
from pathlib import Path
import sinnoh_private_visual as pv
import sinnoh_city_expansion as city
import sinnoh_route_expansion as route
import sinnoh_natural_expansion as natural
import sinnoh_interior_expansion as interior
from audit_sinnoh_rxdata import read_marshal
from build_johto_events import EVENT_CLASSES,ruby,event_page
from stage import serialize

ROOT=Path(__file__).resolve().parents[2]
CATALOG="data/regions/sinnoh-f08-connections.json"
OPPOSITE={"N":"S","S":"N","E":"W","W":"E"}

def graph(root=ROOT):
    doc=json.loads((root/CATALOG).read_text("utf-8"))
    rows=doc["source_maps"];source={r["source_id"]:r for r in rows}
    symbols={r["symbol"] for r in rows}
    if doc["schema"]!=1 or doc["scope"]!="PRIVATE_QA_ONLY" or len(rows)!=123 or len(source)!=123 or symbols!=interior.ALL-set(pv.INTERIOR_SIZES):
        raise ValueError("F08_INVALID_SOURCE_GRAPH")
    directed={(a,b) for a,r in source.items() for b in r["targets"] if b in source and a!=b}
    reciprocal={(a,b) for a,b in directed if a<b and (b,a) in directed}
    if len(directed)!=145 or len(reciprocal)!=69 or directed!={tuple(r) for r in doc["directed_candidates"]} or reciprocal!={tuple(r) for r in doc["reciprocal_candidates"]}:
        raise ValueError("F08_GRAPH_COUNTS")
    return source,directed,reciprocal

def static_targets(events):
    targets=set()
    for e in events.values():
        for p in e.attrs.get("@pages",[]):
            for c in p.attrs.get("@list",[]):
                a=c.attrs;args=a.get("@parameters",[])
                if a.get("@code")==201 and len(args)>1 and args[0]==0 and type(args[1]) is int:targets.add(args[1])
    return targets

def visual_only(command):
    # Rebuild a plain native transfer, not the donor animation. Only commands
    # whose effects are cosmetic and bounded may be omitted. No move routes,
    # scripts, switches, variables, player movement or dialogue are accepted.
    code=command.get("@code");args=command.get("@parameters",[])
    if command.get("@indent")!=0:return False
    if code in (108,408):return True
    if code==106:return len(args)==1 and type(args[0]) is int and 0<=args[0]<=120
    if code==250:
        return (len(args)==1 and getattr(args[0],"name",None)=="RPG::AudioFile"
                and isinstance(args[0].attrs.get("@name"),bytes)
                and all(type(args[0].attrs.get(k)) is int and 0<=args[0].attrs[k]<=150 for k in ("@volume","@pitch")))
    if code==221:return not args
    if code==222:return len(args)==1 and isinstance(args[0],bytes)
    return False

def classify_transfer(event):
    pages=event.attrs.get("@pages",[])
    if len(pages)!=1:return None,"multiple_pages"
    p=pages[0].attrs
    if p.get("@trigger") not in (0,1,2):return None,"noninteractive_trigger"
    if p.get("@move_type")!=0:return None,"moving_event"
    cond=p.get("@condition")
    if cond is None or any(cond.attrs.get("@"+k) is not False for k in ("switch1_valid","switch2_valid","variable_valid","self_switch_valid")):return None,"page_conditions"
    ops=[c.attrs for c in p.get("@list",[])]
    if any(c.get("@indent")!=0 for c in ops):return None,"nested_commands"
    core=[c for c in ops if not visual_only(c)]
    if [c.get("@code") for c in core]!=[201,0]:return None,"unsupported_commands"
    args=core[0].get("@parameters",[])
    if len(args)!=6 or any(type(x) is not int for x in args) or args[0]!=0 or args[4] not in (0,2,4,6,8) or args[5] not in (0,1):return None,"transfer_parameters"
    if any(type(event.attrs.get(k)) is not int for k in ("@x","@y")):return None,"event_coordinates"
    return (event.attrs["@x"],event.attrs["@y"],*args[1:]),"accepted"

def simple_transfer(event):
    return classify_transfer(event)[0]

def event_shape(event):
    # No donor scripts, text, audio names or serialized event pages in logs.
    pages=[]
    for p in event.attrs.get("@pages",[]):
        a=p.attrs;cond=a.get("@condition")
        flags=[k for k in ("switch1_valid","switch2_valid","variable_valid","self_switch_valid") if cond is None or cond.attrs.get("@"+k) is not False]
        ops=[c.attrs for c in a.get("@list",[])]
        pages.append({"trigger":a.get("@trigger"),"move_type":a.get("@move_type"),
            "conditions":flags,"codes":[c.get("@code") for c in ops],
            "transfers":[{"length":len(c.get("@parameters",[])),
                "mode":c["@parameters"][0] if c.get("@parameters") and type(c["@parameters"][0]) is int else None,
                "direction":c["@parameters"][4] if len(c.get("@parameters",[]))>4 and type(c["@parameters"][4]) is int else None,
                "fade":c["@parameters"][5] if len(c.get("@parameters",[]))>5 and type(c["@parameters"][5]) is int else None}
                for c in ops if c.get("@code")==201],
            "move_routes":[{"target":c["@parameters"][0] if c.get("@parameters") and type(c["@parameters"][0]) is int else None,
                "codes":[m.attrs.get("@code") for m in getattr(c["@parameters"][1],"attrs",{}).get("@list",[])]}
                for c in ops if c.get("@code")==209 and len(c.get("@parameters",[]))==2]})
    return pages

def safe_cells(world,tiles,symbol):
    a=world.attrs;w,h=a["@width"],a["@height"];ts=tiles[a["@tileset_id"]].attrs
    p=ts["@passages"].data[20:];t=ts["@terrain_tags"].data[20:]
    p=struct.unpack("<%dH"%(len(p)//2),p);t=struct.unpack("<%dH"%(len(t)//2),t)
    cells=struct.unpack_from("<%dH"%(w*h*3),a["@data"].data,20)
    allowed=city.teleport.arrival_policy(symbol)[0]
    return {(x,y) for y in range(h) for x in range(w) if
        (stack:=[cells[z*w*h+y*w+x] for z in range(3) if cells[z*w*h+y*w+x]])
        and all(i<len(p) and i<len(t) and not p[i]&15 and t[i] in allowed for i in stack)}

def append(blobs,mapping,components,path,root=ROOT):
    if set(mapping)!=interior.ALL or len(set(mapping.values()))!=127:raise ValueError("F08_MAPIDS")
    source,directed,reciprocal=graph(root)
    reciprocal_dirs=reciprocal|{(b,a) for a,b in reciprocal}
    worlds={s:read_marshal(blobs["Data/Map%03d.rxdata"%mid],"F08_MAP") for s,mid in mapping.items()}
    tiles=read_marshal(blobs["Data/Tilesets.rxdata"],"F08_TILES")
    safe={s:safe_cells(m,tiles,s)&components[s] for s,m in worlds.items() if s not in city.OLD}
    occupied={s:{(e.attrs["@x"],e.attrs["@y"]) for e in m.attrs["@events"].values()} for s,m in worlds.items()}
    entries=city.teleport.build(blobs,mapping,components,root)
    arrivals={r[0]:tuple(r[3][1:]) for r in entries if r[3]}
    candidates=[];rejected=Counter();shapes=Counter();diagnostics=[]
    with pv.verified_archive(path,"maps") as z:
        for a,row in source.items():
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%a)
            if hashlib.sha256(raw).hexdigest()!=row["sha256"]:raise ValueError("F08_SOURCE_MAP_HASH")
            events=read_marshal(raw,"F08_DONOR").attrs["@events"]
            if static_targets(events)!=set(row["targets"]):raise ValueError("F08_SOURCE_GRAPH_CHANGED")
            sym=row["symbol"]
            for eid,event in sorted(events.items()):
                result,reason=classify_transfer(event)
                if not static_targets({eid:event}):continue
                shape=event_shape(event)
                shapes[(reason,json.dumps(shape,sort_keys=True))]+=1
                if result is None:
                    rejected[reason]+=1
                    diagnostics.append({"source_id":a,"event_id":eid,"reason":reason,"targets":sorted(static_targets({eid:event})),"pages":shape})
                    continue
                x,y,b,dx,dy,direction,fade=result
                if (a,b) not in reciprocal_dirs:rejected["outside_or_nonreciprocal"]+=1;continue
                dest=source[b]["symbol"]
                if sym in city.OLD or dest in city.OLD:rejected["protected_opening"]+=1;continue
                if ((x,y) not in safe[sym] or (dx,dy) not in safe[dest]
                    or not any(n in safe[sym] for n in city.teleport.neighbours(x,y))
                    or not any(n in safe[dest] for n in city.teleport.neighbours(dx,dy))
                    or (x,y) in occupied[sym] or (dx,dy) in occupied[dest]):
                    rejected["unsafe_coordinates"]+=1;continue
                if abs(x-arrivals[sym][0])+abs(y-arrivals[sym][1])<=1:rejected["qa_arrival_reserved"]+=1;continue
                candidates.append({"source_id":a,"source_event_id":eid,"target_source_id":b,"symbol":sym,
                    "from":[mapping[sym],x,y],"to":[mapping[dest],dx,dy],"direction":direction,"fade":fade,"trigger":event.attrs["@pages"][0].attrs["@trigger"]})
        donor_seams=pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt"))
    positions=Counter(tuple(r["from"]) for r in candidates)
    portals=[r for r in candidates if positions[tuple(r["from"])]==1 and tuple(r["to"]) not in positions]
    rejected["ambiguous_or_loop_arrival"]+=len(candidates)-len(portals)
    edges={(r["source_id"],r["target_source_id"]) for r in portals}
    kept=[r for r in portals if (r["target_source_id"],r["source_id"]) in edges]
    rejected["no_safe_reverse"]+=len(portals)-len(kept)
    out=dict(blobs);changed=set()
    for r in kept:
        sym=r["symbol"];mid,x,y=r["from"];dest,dx,dy=r["to"]
        events=worlds[sym].attrs["@events"];eid=max(events,default=0)+1
        page=event_page(warp=(dest,dx,dy),touch=r["trigger"]!=0)
        page.attrs["@trigger"]=r["trigger"]
        # An action-button portal must not become an automatic touch warp.
        page.attrs["@list"][0].attrs["@parameters"][4:6]=[r["direction"],r["fade"]]
        events[eid]=ruby("RPG::Event",id=eid,name=("SN_F08_PORTAL_%d_%d"%(r["source_id"],r["source_event_id"])).encode("ascii"),x=x,y=y,pages=[page])
        r["event_id"]=eid;changed.add(sym)
    for sym in changed:out["Data/Map%03d.rxdata"%mapping[sym]]=serialize(worlds[sym],EVENT_CLASSES)
    existing=pv.parse_connections(blobs["PBS/map_connections.txt"])
    compiled=read_marshal(blobs["Data/map_connections.dat"],"F08_CONNECTIONS")
    used={(r[0],r[1]) for r in existing}|{(r[3],r[4]) for r in existing}
    counts=Counter((m,d) for r in donor_seams for m,d in ((r[0],r[1]),(r[3],r[4])))
    outdoors=city.CITIES|route.ROUTES|natural.OUTDOORS
    seams=[];records=[]
    for a,da,oa,b,db,ob in donor_seams:
        if a==b or a not in source or b not in source:continue
        sa,sb=source[a]["symbol"],source[b]["symbol"]
        if sa not in outdoors or sb not in outdoors or sa in city.OLD or sb in city.OLD or OPPOSITE.get(da)!=db:continue
        if counts[(a,da)]!=1 or counts[(b,db)]!=1 or (mapping[sa],da) in used or (mapping[sb],db) in used:continue
        wa,wb=worlds[sa].attrs,worlds[sb].attrs
        common=pv.edge_axis(safe[sa],(wa["@width"],wa["@height"]),da,oa)&pv.edge_axis(safe[sb],(wb["@width"],wb["@height"]),db,ob)
        if not common:continue
        record=[mapping[sa],da,oa,mapping[sb],db,ob]
        records.append(record);used.update({(record[0],da),(record[3],db)})
        seams.append({"source_ids":[a,b],"record":record,"reachable_seam_tiles":len(common)})
    if records:
        out["Data/map_connections.dat"]=serialize(compiled+[[r[0],r[1].encode("ascii"),r[2],r[3],r[4].encode("ascii"),r[5]] for r in records])
        out["PBS/map_connections.txt"]=blobs["PBS/map_connections.txt"]+("\n# Sinnoh F08 verified seams\n"+"\n".join(",".join(map(str,r)) for r in records)+"\n").encode("ascii")
    print("SINNOH_F08_TRANSFER_SHAPES "+json.dumps([{"reason":reason,"pages":json.loads(shape),"count":count}
        for (reason,shape),count in shapes.most_common()],sort_keys=True),flush=True)
    for item in diagnostics:
        print("SINNOH_F08_REJECTED_EVENT "+json.dumps(item,sort_keys=True),flush=True)
    if not kept and not seams:raise ValueError("F08_NO_SAFE_CONNECTIONS:"+json.dumps(dict(rejected),sort_keys=True))
    if city.teleport.build(out,mapping,components,root)!=entries:raise ValueError("F08_QA_TELEPORT_CHANGED")
    accepted={(r["source_id"],r["target_source_id"]) for r in kept}
    report={"source_maps":123,"directed_candidates":145,"reciprocal_candidates":69,"portals":kept,"seams":seams,
        "portal_directed_accepted":len(accepted),"portal_directed_pending":len(directed-accepted),"rejected":dict(rejected),
        "maps_with_new_events":len(changed),"native_verified":False,"all_connections_approved":False,
        "portal_pairs_accepted":sum(a<b and (b,a) in accepted for a,b in accepted)}
    print("SINNOH_F08_CONNECTION_REPORT "+json.dumps(report,sort_keys=True),flush=True)
    return out,report
