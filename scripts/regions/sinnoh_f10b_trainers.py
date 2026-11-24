"""F10B: rebuild ordinary route trainer events, never execute donor scripts.
Historical Platinum teams are independently referenced, not donor PBS.
Candidates without exact identity, assets or safe placement remain pending.
"""
import hashlib
import json
import re
from collections import deque
from pathlib import Path
import sinnoh_f10a_inventory as f10a
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as teleport
from build_johto_events import EVENT_CLASSES,ruby,event_page
from stage import serialize
from pbs import catalogue,read_blocks

ROOT=Path(__file__).resolve().parents[2]
PIN={(42,29):(37,10),(42,30):(37,4),(42,31):(48,9),(79,34):(56,31),(79,35):(57,12)}
# First battles, historical Platinum (not native or donor PBS).
REFERENCES={
 42:{"Justin":("HIKER",[("GEODUDE",20),("NOSEPASS",20)]),
     "Austin":("YOUNGSTER",[("BUIZEL",18),("LUXIO",18),("GLIGAR",21)]),
     "Kevin":("HIKER",[("GEODUDE",17),("GEODUDE",17),("ONIX",19),("GEODUDE",19)]),
     "Helen":("BATTLEGIRL",[("MACHOP",21),("MEDITITE",21)])},
 79:{"Zach":("NINJABOY",[("ZUBAT",14),("ZUBAT",14),("ZUBAT",14)]),
     "Louis":("HIKER",[("GEODUDE",14),("ONIX",18)]),
     "Sean":("BLACKBELT",[("CROAGUNK",31),("MEDITITE",31),("MACHOKE",31)]),
     "Katherine":("BIRDKEEPER",[("NOCTOWL",34)]),
     "Harry":("RUINMANIAC",[("BRONZOR",28),("BRONZOR",30),("BRONZOR",32)]),
     "Nick":("NINJABOY",[("SKORUPI",32),("CROAGUNK",30)])}}
# Double-battle pair Anthony/Lauren, and Rock Smash-gated Alexandra deliberately
# excluded pending story and field gates. Aliases are explicit, never fuzzy.
ALIASES={
 "HIKER":("HIKER",),"YOUNGSTER":("YOUNGSTER",),
 "BATTLEGIRL":("BATTLEGIRL","BATTLE_GIRL"),
 "NINJABOY":("NINJABOY","NINJA_BOY"),
 "BLACKBELT":("BLACKBELT","BLACK_BELT"),
 "BIRDKEEPER":("BIRDKEEPER","BIRD_KEEPER","BIRDKEEPER_F"),
 "RUINMANIAC":("RUINMANIAC","RUIN_MANIAC")}
CALL=re.compile(rb"^\s*(?:if\s+)?(?:pbTrainerBattle(?:100)?|TrainerBattle\s*\.\s*start)\s*\(\s*(?::|PBTrainers::)?([A-Za-z][A-Za-z0-9_]*)\s*,\s*(?:(_I|_INTL)\s*\(\s*)?(['\"])([A-Za-z]+)\3\s*(?=[,)])")
ASSET=re.compile(rb"[A-Za-z0-9_ -]{1,80}")

def identity(event,sid):
    found=set()
    for page in event.attrs.get("@pages",[]):
        for command in page.attrs.get("@list",[]):
            # RMXP conditional scripts are code 111, not just 355/655.
            if command.attrs.get("@code") not in (111,355,655):continue
            params=command.attrs.get("@parameters",[])
            if command.attrs.get("@code")==111 and (len(params)<2 or params[0]!=12):continue
            for value in params:
                if not isinstance(value,bytes):continue
                for m in CALL.finditer(value):
                    found.add((m[1].decode().upper(),m[4].decode()))
                    # Multiple statements are not trusted as a first-battle identity.
                    if b";" in value: return None,"multiple_script_statements"
    if len(found)!=1:return None,"missing_or_ambiguous_literal_identity"
    kind,name=next(iter(found))
    ref=REFERENCES.get(sid,{}).get(name)
    if ref is None or kind not in ALIASES[ref[0]]:return None,"identity_not_in_reviewed_first_battles"
    return (kind,name,ref[0],ref[1]),None

def component(points,seed):
    if seed not in points:return set()
    seen={seed};todo=deque([seed])
    while todo:
        for q in teleport.neighbours(*todo.popleft()):
            if q in points and q not in seen:seen.add(q);todo.append(q)
    return seen

def non_cut(points,xy):
    if xy not in points:return False
    adjacent=[p for p in teleport.neighbours(*xy) if p in points]
    if len(adjacent)<2:return False
    return set(adjacent)<=component(points-{xy},adjacent[0])

def sprite(z,event,base=None):
    names=set()
    for page in event.attrs.get("@pages",[]):
        graphic=getattr(page.attrs.get("@graphic"),"attrs",{})
        name=graphic.get("@character_name",b"")
        if name:names.add(name)
    if len(names)!=1:return None
    name=next(iter(names))
    if not isinstance(name,bytes) or not ASSET.fullmatch(name):return None
    name=name.decode("ascii")
    member=pv.MAP_ROOT+"Graphics/Characters/"+name+".png"
    matching=[i for i in z.infolist() if i.filename.casefold()==member.casefold()]
    if len(matching)==1 and matching[0].filename==member:
        data=pv.member(z,member,1_000_000)
    elif not matching and base is not None:
        path=base/"Graphics"/"Characters"/(name+".png")
        if path.is_symlink() or not path.is_file() or path.stat().st_size>1_000_000:return None
        data=path.read_bytes()
    else:return None
    try:w,h=pv.dims(data)
    except (ValueError,TypeError):return None
    if w%4 or h%4 or not (32<=w<=512 and 32<=h<=512):return None
    return data

def build(blobs,mapping,masks,components,path,types,species,existing,base=None,root=ROOT):
    inventory=f10a.audit(blobs,mapping,masks,components,path,root)
    eligible={(q["source_id"],q["source_event_id"]):q for q in inventory["queue"]
              if q["kind"]=="trainer_candidate" and not q["geometry_blockers"]}
    if set(eligible)!=set(PIN) or any(tuple(eligible[k]["position"])!=v for k,v in PIN.items()):
        raise ValueError("F10B_PINNED_F10A_GEOMETRY_CHANGED")
    entries=teleport.build(blobs,mapping,components,root)
    reserved={tuple(row[3]) for row in entries if row[3]}
    worlds={}
    for mid in mapping.values():
        m=conn.read_marshal(blobs["Data/Map%03d.rxdata"%mid],"F10B_QA")
        worlds[mid]=m
        for e in m.attrs["@events"].values():
            for p in e.attrs["@pages"]:
                for c in p.attrs["@list"]:
                    args=c.attrs.get("@parameters",[])
                    if c.attrs.get("@code")==201 and len(args)==6 and args[0]==0 and all(type(v) is int for v in args):
                        reserved.add(tuple(args[1:4]))
    out=dict(blobs);accepted=[];rejected=[];rows=[];used=set();changed=set()
    source,_,_=conn.graph(root)
    with pv.verified_archive(path,"maps") as z:
        for sid,eid in sorted(PIN):
            q=eligible[sid,eid];mid=q["qa_map_id"];xy=PIN[sid,eid]
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=source[sid]["sha256"]:raise ValueError("F10B_SOURCE_HASH")
            donor=conn.read_marshal(raw,"F10B_DONOR").attrs["@events"][eid]
            spec,reason=identity(donor,sid)
            data=None
            if spec:
                src_kind,name,kind,team=spec
                local=next((k for k in (src_kind,*ALIASES[kind]) if k in types),None)
                version=1000+sid*100+eid
                if not local:reason="local_trainer_type_missing"
                elif any(m not in species for m,l in team):reason="local_species_missing"
                elif (local,name,version) in existing:reason="local_pbs_collision"
                elif (sid,name) in used:reason="duplicate_identity"
                elif not (data:=sprite(z,donor,base)):reason="exact_sprite_missing_or_invalid"
            m=worlds[mid];events=m.attrs["@events"]
            occupied={(e.attrs["@x"],e.attrs["@y"]) for e in events.values()}
            grid=masks[mid]
            points={(x,y) for x,y in components[q["symbol"]] if 0<=y<len(grid) and 0<=x<len(grid[y]) and grid[y][x] in (".","g")}-occupied
            if not reason:
                if any(a==mid and abs(x-xy[0])+abs(y-xy[1])<=1 for a,x,y in reserved):reason="reserved_arrival"
                elif not (0<xy[0]<len(grid[0])-1 and 0<xy[1]<len(grid)-1) or not non_cut(points,xy):reason="route_connectivity"
            if reason:
                rejected.append({"source_id":sid,"source_event_id":eid,"reason":reason,
                    "literal_identity_confirmed":spec is not None})
                continue
            key="F10B_%d_%d"%(sid,eid)
            sprite_name="SNQA_"+key
            event_id=max(events,default=0)+1
            page=event_page(script='BlueSinnohF10B.battle("%s")'%key,sprite=sprite_name)
            # Action-only until sight paths receive native collision QA.
            events[event_id]=ruby("RPG::Event",id=event_id,name=("SN_"+key).encode("ascii"),x=xy[0],y=xy[1],pages=[page])
            out["Graphics/Characters/"+sprite_name+".png"]=data
            changed.add(mid);used.add((sid,name))
            rows.append([key,[local,name,version,mid,team]])
            accepted.append({"key":key,"source_id":sid,"source_event_id":eid,"map_id":mid,"event_id":event_id,
                             "position":list(xy),"type":local,"name":name,"version":version,
                             "team":team,"sprite_sha256":hashlib.sha256(data).hexdigest(),"team_source":"PLATINUM_HISTORICAL_REFERENCE"})
    for mid in changed:
        out["Data/Map%03d.rxdata"%mid]=serialize(worlds[mid],EVENT_CLASSES)
    if teleport.build(out,mapping,components,root)!=entries:raise ValueError("F10B_QA_SPAWN_CHANGED")
    if rows:
        lines=[]
        for key,(kind,name,version,mid,team) in rows:
            lines.extend(["[%s,%s,%d]"%(kind,name,version),"LoseText = Boa batalha!"])
            lines.extend("Pokemon = %s,%d"%(m,l) for m,l in team)
            lines.append("")
        out["PBS/trainers_sinnoh_f10b.txt"]=("\n".join(lines)+"\n").encode("ascii")
    template=(root/"scripts/regions/SinnohF10B.rb").read_text("utf-8")
    if template.count("__F10B_ROWS__")!=1:raise ValueError("F10B_TEMPLATE")
    plugin=template.replace("__F10B_ROWS__",json.dumps(rows,ensure_ascii=True)).encode("utf-8")
    report={"maps_audited":131,"pinned_candidates":5,"accepted":accepted,"rejected":rejected,
            "new_trainers":len(accepted),"native_verified":False,"water_enabled":False,
            "team_reference":["https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_207","https://bulbapedia.bulbagarden.net/wiki/Sinnoh_Route_211"],
            "source_pbs_present":False,"action_only":True}
    return out,report,plugin

def append(blobs,mapping,masks,components,path,base,root=ROOT):
    existing=set()
    for p in (base/"PBS").glob("trainers*.txt"):
        if p.is_symlink():raise ValueError("F10B_UNSAFE_PBS")
        for header in read_blocks(p):
            fields=[v.strip() for v in header.split(",")]
            if len(fields) in (2,3) and (len(fields)==2 or fields[2].isdigit()):
                existing.add((fields[0],fields[1],int(fields[2]) if len(fields)==3 else 0))
    out,report,plugin=build(blobs,mapping,masks,components,path,catalogue(base,"trainer_types"),catalogue(base,"pokemon"),existing,base,root)
    print("SINNOH_F10B_TRAINER_REPORT "+json.dumps(report,sort_keys=True),flush=True)
    return out,report,plugin
