"""F10B: rebuild ordinary route trainer events, never execute donor scripts.
F10B3 evidence: Justin and Sean accepted in source job 138855505090.
Historical Platinum teams are independently referenced, not donor PBS.
Candidates without exact identity, assets or safe placement remain pending.
"""
import hashlib
import json
import re
from collections import deque
from contextlib import nullcontext
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

def literal_identity(event):
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
    return next(iter(found)),None

# Source literal aliases, never fuzzy. Kath is retained as the displayed name;
# the historical reference is Katherine, a distinct provenance field.
REVIEWED_NAME_ALIASES={(79,"BIRDKEEPER","Kath"):"Katherine"}
# Explicit project art choice, NOT an assertion of the original sprite.
SEAN_ART=("NPC_007_Black_Belt.png","NPC_008_Black_Belt.png")
# Historical pair rosters; installation waits for a verified double battle.
PAIR_TEAMS={(42,29):("CAMPER","Anthony",[("CHIMCHAR",22)]),
            (42,30):("PICNICKER","Lauren",[("PACHIRISU",22)])}

def identity(event,sid,revision=2):
    literal,reason=literal_identity(event)
    if literal is None:return None,reason
    kind,name=literal
    reference_name=REVIEWED_NAME_ALIASES.get((sid,kind,name),name) if revision>=3 else name
    matches=[(n,ref) for n,ref in REFERENCES.get(sid,{}).items() if n.casefold()==reference_name.casefold()]
    if len(matches)!=1:return None,"identity_not_in_reviewed_first_battles"
    canonical,ref=matches[0]
    if kind not in ALIASES[ref[0]]:return None,"class_not_in_reviewed_aliases"
    return (kind,name if reference_name!=name else canonical,ref[0],ref[1]),None

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

def sprite_names(event):
    names=set()
    for page in event.attrs.get("@pages",[]):
        graphic=getattr(page.attrs.get("@graphic"),"attrs",{})
        name=graphic.get("@character_name",b"")
        if name:names.add(name)
    return names

def sprite(z,event,base=None):
    names=sprite_names(event)
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

# Explicit class tokens, not fuzzy substring matching or an arbitrary NPC.
# Replacement is identified in the report as a class-equivalent sprite,
# never as the original donor asset. Multiple exact class sheets remain pending.
CLASS_ART={
    "HIKER":("Hiker",),"YOUNGSTER":("Youngster",),
    "BATTLEGIRL":("BattleGirl","Battle Girl","Battle_Girl"),
    "NINJABOY":("NinjaBoy","Ninja Boy","Ninja_Boy"),
    "BLACKBELT":("BlackBelt","Black Belt","Black_Belt"),
    "BIRDKEEPER":("BirdKeeper","Bird Keeper","Bird_Keeper"),
    "RUINMANIAC":("RuinManiac","Ruin Maniac","Ruin_Maniac")
}

def class_art_candidates(z,kind):
    if z is None or kind not in CLASS_ART:return []
    pattern=re.compile(re.escape(pv.OW_ROOT)+r"NPC_\d+_(?:"+"|".join(re.escape(s) for s in CLASS_ART[kind])+r")\.png",re.I)
    return sorted(i.filename for i in z.infolist() if not i.is_dir() and pattern.fullmatch(i.filename))

def resolve_sprite(maps,ow,event,kind,base=None,selected_variant=None):
    exact=sprite(maps,event,base)
    if exact:return exact,"EXACT_DONOR_OR_LOCAL_SHEET",[]
    candidates=class_art_candidates(ow,kind)
    labels=[n.rsplit("/",1)[-1] for n in candidates]
    provenance="CLASS_EQUIVALENT_DPPt_OVERWORLD"
    if selected_variant:
        # Limit the exception to precisely the two audited Black Belt sheets.
        if kind!="BLACKBELT" or tuple(labels)!=SEAN_ART or selected_variant!=SEAN_ART[0]:
            return None,None,labels
        chosen=[n for n in candidates if n.rsplit("/",1)[-1]==selected_variant]
        if len(chosen)!=1:return None,None,labels
        candidates=chosen
        provenance="CLASS_EQUIVALENT_PROJECT_SELECTED"
    elif len(candidates)!=1:return None,None,labels
    raw=pv.member(ow,candidates[0],1_000_000)
    try:
        if pv.dims(raw)!=(256,256):return None,None,labels
    except ValueError:return None,None,labels
    return raw,provenance,labels

def diagnostics(event,sid,ow,revision=2):
    literal,reason=literal_identity(event)
    # Only constrained identifiers, never source dialogue or script bodies.
    # Character names are filenames, not save/player names.
    names=sorted(n.decode("ascii") for n in sprite_names(event) if isinstance(n,bytes) and ASSET.fullmatch(n))
    spec,why=identity(event,sid,revision)
    return {"literal_type":literal[0] if literal else None,"literal_name":literal[1] if literal else None,
            "identity_status":why or "reviewed_historical_match",
            "historical_reference_name":REVIEWED_NAME_ALIASES.get((sid,*literal)) if revision>=3 and literal else None,
            "source_sprite_labels":names,
            "class_art_candidates":[n.rsplit("/",1)[-1] for n in class_art_candidates(ow,spec[2])] if spec else []}

# F10B4: the original pair is atomic; Harry is an explicitly authored
# stationary alternative, not a copy of the donor's autonomous move route.
EXTRA_ART={"CAMPER":("Camper",),"PICNICKER":("Picnicker","Picnic_Ker"),
           "BIRDKEEPER":("Bird Keeper F","Bird_Keeper_F","BirdKeeper_F","Bird Keeper Female","Bird_Keeper_Female")}
def extra_sprite(maps,ow,event,kind,base=None):
    data,provenance,labels=resolve_sprite(maps,ow,event,kind,base)
    if data:return data,provenance,labels
    if ow is None or kind not in EXTRA_ART:return None,None,labels
    pattern=re.compile(re.escape(pv.OW_ROOT)+r"NPC_\d+_(?:"+"|".join(re.escape(s) for s in EXTRA_ART[kind])+r")\.png",re.I)
    candidates=sorted(i.filename for i in ow.infolist() if not i.is_dir() and pattern.fullmatch(i.filename))
    labels=sorted(set(labels+[n.rsplit("/",1)[-1] for n in candidates]))
    if len(candidates)!=1 or len(labels)!=1:return None,None,labels
    raw=pv.member(ow,candidates[0],1_000_000)
    try:
        if pv.dims(raw)!=(256,256):return None,None,labels
    except ValueError:return None,None,labels
    return raw,"CLASS_EQUIVALENT_DPPt_OVERWORLD",labels


# F10B5: only pre-existing arrival/seam witnesses may establish additional
# accessible components. No new warp, terrain edit, movement override or HM.
F10B5_PENDING={(42,32):("YOUNGSTER","Austin"),(42,33):("HIKER","Kevin"),
              (42,34):("CRUSHGIRL","Helen"),(79,32):("HIKER","Louis"),
              (79,35):("BIRDKEEPER","Kath")}
F10B5_GATED={(79,33):"possible_Alexandra_requires_rock_smash_identity_unproven",
             (80,1):"possible_Jogger_Wyatt_morning_and_bicycle_identity_unproven"}
AUSTIN_ART=("NPC_023_Youngster.png","NPC_024_Youngster.png")
LOCAL_ART={"BIRDKEEPER":("trainer_BIRDKEEPER","trainer_BIRDKEEPER_F","trainer_BIRD_KEEPER_F"),
           "BATTLEGIRL":("trainer_CRUSHGIRL","trainer_BATTLEGIRL","trainer_BATTLE_GIRL")}

def strict_local_art(base,kind):
    if base is None or kind not in LOCAL_ART:return None,None,[]
    folder=base/"Graphics"/"Characters"
    if not folder.is_dir() or folder.is_symlink():return None,None,[]
    allowed={name.casefold()+".png" for name in LOCAL_ART[kind]}
    matches=sorted((p for p in folder.iterdir() if p.name.casefold() in allowed),key=lambda p:p.name)
    labels=[p.name for p in matches]
    if len(matches)!=1:return None,None,labels
    p=matches[0]
    if p.is_symlink() or not p.is_file() or p.stat().st_size>1_000_000:return None,None,labels
    raw=p.read_bytes()
    try:w,h=pv.dims(raw)
    except ValueError:return None,None,labels
    if w%4 or h%4 or not (32<=w<=512 and 32<=h<=512):return None,None,labels
    return raw,"CLASS_EQUIVALENT_LOCAL_VERIFIED_FILENAME",labels

def f10b5_art(maps,ow,event,kind,base,source_key):
    data,provenance,labels=extra_sprite(maps,ow,event,kind,base)
    if data:return data,provenance,labels
    if source_key==(42,32) and kind=="YOUNGSTER" and tuple(labels)==AUSTIN_ART:
        raw=pv.member(ow,pv.OW_ROOT+AUSTIN_ART[0],1_000_000)
        try:
            if pv.dims(raw)==(256,256):return raw,"CLASS_EQUIVALENT_PROJECT_SELECTED",labels
        except ValueError:pass
    return strict_local_art(base,kind) if kind in LOCAL_ART else (None,None,labels)

def witness_component(points,anchors,xy):
    """Exact safe cell and a path from a verified existing entry.
    Reject articulation points and never move the candidate.
    """
    if xy not in points:return None,set()
    for label,seed in anchors:
        reached=component(points,seed)
        if xy in reached and non_cut(reached,xy):
            return {"kind":label,"entry":list(seed),"reachable_cells":len(reached)},reached
    return None,set()

def access_witnesses(blobs,worlds,mapping,components,entries):
    """Read only existing QA transfer and seam records, with conservative
    plain/grass passability. Do not use the permissive movement mask alone:
    it can contain special terrain not approved for ordinary access.
    """
    reverse={mid:sym for sym,mid in mapping.items()}
    tiles=conn.read_marshal(blobs["Data/Tilesets.rxdata"],"F10B5_TILES")
    ground={mid:conn.safe_cells(m,tiles,reverse[mid],allowed={0,2}) for mid,m in worlds.items()}
    occupied={mid:{(e.attrs["@x"],e.attrs["@y"]) for e in m.attrs["@events"].values()} for mid,m in worlds.items()}
    primary={mid:ground[mid]&components[reverse[mid]]-occupied[mid] for mid in worlds}
    anchors={mid:[] for mid in worlds}
    for row in entries:
        if row[3]:
            mid,x,y=row[3]
            if (x,y) in primary[mid]:anchors[mid].append(("QA_EXISTING_ARRIVAL",(x,y)))
    # Only static direct transfers reachable from a primary component.
    for mid,m in worlds.items():
        for e in m.attrs["@events"].values():
            xy=(e.attrs["@x"],e.attrs["@y"])
            if not any(q in primary[mid] for q in teleport.neighbours(*xy)):continue
            for page in e.attrs["@pages"]:
                condition=getattr(page.attrs.get("@condition"),"attrs",{})
                if any(condition.get("@"+key) is not False for key in ("switch1_valid","switch2_valid","variable_valid","self_switch_valid")):continue
                for cmd in page.attrs["@list"]:
                    args=cmd.attrs.get("@parameters",[])
                    if cmd.attrs.get("@code")!=201 or len(args)!=6 or args[0]!=0 or not all(type(v) is int for v in args):continue
                    dst,x,y=args[1:4]
                    if dst in worlds and (x,y) in ground[dst]-occupied[dst]:
                        anchors[dst].append(("EXISTING_STATIC_PORTAL",(x,y)))
    # Native connections are not changed. Match opposite safe edge cells
    # against an existing connection's exact offset, from primary ground.
    if "PBS/map_connections.txt" in blobs:
        for a,da,oa,b,db,ob in pv.parse_connections(blobs["PBS/map_connections.txt"]):
            if a not in worlds or b not in worlds or conn.OPPOSITE.get(da)!=db:continue
            for src,sd,so,dst,dd,do in ((a,da,oa,b,db,ob),(b,db,ob,a,da,oa)):
                sw,sh=worlds[src].attrs["@width"],worlds[src].attrs["@height"]
                dw,dh=worlds[dst].attrs["@width"],worlds[dst].attrs["@height"]
                axes=pv.edge_axis(primary[src],(sw,sh),sd,so)
                for axis in sorted(axes):
                    index=axis+do
                    xy=(index,0 if dd=="N" else dh-1) if dd in ("N","S") else (0 if dd=="W" else dw-1,index)
                    if xy in ground[dst]-occupied[dst]:anchors[dst].append(("EXISTING_CONTINUOUS_EDGE",xy))
    return ground,{mid:sorted(set(rows),key=lambda r:(r[0],r[1])) for mid,rows in anchors.items()}

def build(blobs,mapping,masks,components,path,types,species,existing,base=None,root=ROOT,overworlds=None,revision=5):
    if revision not in (2,3,4,5):raise ValueError("F10B_UNSUPPORTED_REVISION")
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
    original_max={mid:max(world.attrs["@events"],default=0) for mid,world in worlds.items()}
    out=dict(blobs);accepted=[];rejected=[];rows=[];used=set();changed=set()
    source,_,_=conn.graph(root)
    all_trainers=[q for q in inventory["queue"] if q["kind"]=="trainer_candidate"]
    if len(all_trainers)!=12:raise ValueError("F10B2_SOURCE_TRAINER_COUNT_CHANGED")
    expanded=[]
    with pv.verified_archive(path,"maps") as z, (pv.verified_archive(overworlds,"overworlds") if overworlds else nullcontext()) as ow:
        # Audit all 12 source events, including the seven geometry-blocked
        # candidates. Only the five established positions may be installed.
        for q in all_trainers:
            sid,eid=q["source_id"],q["source_event_id"]
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=source[sid]["sha256"]:raise ValueError("F10B2_SOURCE_HASH")
            donor=conn.read_marshal(raw,"F10B2_DONOR").attrs["@events"][eid]
            d=diagnostics(donor,sid,ow,revision)
            if revision>=3 and (sid,eid) in PAIR_TEAMS:
                pk,pn,pt=PAIR_TEAMS[sid,eid]
                if (d["literal_type"],d["literal_name"])!=(pk,pn):raise ValueError("F10B3_PAIR_IDENTITY_CHANGED")
                d["historical_pair_team"]=pt
                d["identity_status"]="reviewed_pair_pending_double_battle"
            expanded.append({"source_id":sid,"source_event_id":eid,"map_id":q["qa_map_id"],
                "position":q["position"],"geometry_blockers":q["geometry_blockers"],**d})
        for sid,eid in sorted(PIN):
            q=eligible[sid,eid];mid=q["qa_map_id"];xy=PIN[sid,eid]
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=source[sid]["sha256"]:raise ValueError("F10B_SOURCE_HASH")
            donor=conn.read_marshal(raw,"F10B_DONOR").attrs["@events"][eid]
            spec,reason=identity(donor,sid,revision)
            if revision>=3 and (sid,eid) in PAIR_TEAMS:reason="double_battle_pending"
            data=None;sprite_provenance=None;art_candidates=[]
            if spec:
                src_kind,name,kind,team=spec
                local=next((k for k in (src_kind,*ALIASES[kind]) if k in types),None)
                version=1000+sid*100+eid
                if not local:reason="local_trainer_type_missing"
                elif any(m not in species for m,l in team):reason="local_species_missing"
                elif (local,name,version) in existing:reason="local_pbs_collision"
                elif (sid,name) in used:reason="duplicate_identity"
                else:
                    choice=SEAN_ART[0] if revision>=3 and (sid,eid)==(79,34) and (src_kind,name)==("BLACKBELT","Sean") else None
                    data,sprite_provenance,art_candidates=resolve_sprite(z,ow,donor,kind,base,choice)
                    if not data and revision>=4 and (sid,eid)==(79,35):
                        data,sprite_provenance,art_candidates=extra_sprite(z,ow,donor,kind,base)
                    if not data:reason="exact_and_unique_class_sprite_unavailable"
            m=worlds[mid];events=m.attrs["@events"]
            occupied={(e.attrs["@x"],e.attrs["@y"]) for e in events.values()}
            grid=masks[mid]
            points={(x,y) for x,y in components[q["symbol"]] if 0<=y<len(grid) and 0<=x<len(grid[y]) and grid[y][x] in (".","g")}-occupied
            geometry_reason=None
            if any(a==mid and abs(x-xy[0])+abs(y-xy[1])<=1 for a,x,y in reserved):geometry_reason="reserved_arrival"
            elif not (0<xy[0]<len(grid[0])-1 and 0<xy[1]<len(grid)-1) or not non_cut(points,xy):geometry_reason="route_connectivity"
            reason=reason or geometry_reason
            if reason:
                rejected.append({"source_id":sid,"source_event_id":eid,"reason":reason,
                    "literal_identity_confirmed":spec is not None,
                    "geometry_reason":geometry_reason,"class_art_candidates":art_candidates})
                continue
            key="F10B_%d_%d"%(sid,eid)
            sprite_name="SNQA_"+key
            # Keep Justin and Sean's F10B2 IDs even when other assets vary.
            event_id=original_max[mid]+2 if revision>=3 and (sid,eid)==(79,35) else max(events,default=0)+1
            if event_id in events:raise ValueError("F10B3_EVENT_ID_COLLISION")
            page=event_page(script='BlueSinnohF10B.battle("%s")'%key,sprite=sprite_name)
            # Action-only until sight paths receive native collision QA.
            events[event_id]=ruby("RPG::Event",id=event_id,name=("SN_"+key).encode("ascii"),x=xy[0],y=xy[1],pages=[page])
            out["Graphics/Characters/"+sprite_name+".png"]=data
            changed.add(mid);used.add((sid,name))
            rows.append([key,[local,name,version,mid,team]])
            accepted.append({"key":key,"source_id":sid,"source_event_id":eid,"map_id":mid,"event_id":event_id,
                             "position":list(xy),"type":local,"name":name,"version":version,
                             "team":team,"sprite_sha256":hashlib.sha256(data).hexdigest(),"sprite_provenance":sprite_provenance,
                             "team_source":"PLATINUM_HISTORICAL_REFERENCE",
                             "historical_reference_name":REVIEWED_NAME_ALIASES.get((sid,src_kind,name),name) if revision>=3 else name})
        extra_report=[]
        if revision>=4:
            lookup={(q["source_id"],q["source_event_id"]):q for q in all_trainers}
            # Both pair members must be accepted together. Harry may be
            # reconstructed as a stationary action event on his original cell.
            groups=[("ROUTE207_DOUBLE",[(42,29),(42,30)]),("HARRY_STATIONARY",[(79,37)])]
            for group,keys in groups:
                staged=[];blockers=[];reserved_cells=set()
                for sid,eid in keys:
                    q=lookup[sid,eid];mid=q["qa_map_id"];xy=tuple(q["position"])
                    allowed=[] if group=="ROUTE207_DOUBLE" else ["moving_event"]
                    if q["geometry_blockers"]!=allowed:
                        blockers.append([sid,eid,"source_geometry_changed"]);continue
                    raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
                    if hashlib.sha256(raw).hexdigest()!=source[sid]["sha256"]:raise ValueError("F10B4_SOURCE_HASH")
                    donor=conn.read_marshal(raw,"F10B4_DONOR").attrs["@events"][eid]
                    literal,_=literal_identity(donor)
                    if group=="ROUTE207_DOUBLE":
                        kind,name,team=PAIR_TEAMS[sid,eid]
                    else:
                        spec,why=identity(donor,sid,revision)
                        if not spec:
                            blockers.append([sid,eid,why]);continue
                        _,name,kind,team=spec
                    if literal!=(kind,name):
                        blockers.append([sid,eid,"literal_identity_changed"]);continue
                    version=1000+sid*100+eid
                    if kind not in types or any(mon not in species for mon,level in team):
                        blockers.append([sid,eid,"local_pbs_catalogue"]);continue
                    if (kind,name,version) in existing or (sid,name) in used:
                        blockers.append([sid,eid,"local_pbs_collision"]);continue
                    data,provenance,labels=extra_sprite(z,ow,donor,kind,base)
                    if not data:
                        blockers.append([sid,eid,"class_sprite_missing_or_ambiguous",labels]);continue
                    events=worlds[mid].attrs["@events"]
                    grid=masks[mid]
                    occupied={(e.attrs["@x"],e.attrs["@y"]) for e in events.values()}|{(x,y) for a,x,y in reserved_cells if a==mid}
                    points={(x,y) for x,y in components[q["symbol"]] if 0<=y<len(grid) and 0<=x<len(grid[y]) and grid[y][x] in (".","g")}-occupied
                    if any(a==mid and abs(x-xy[0])+abs(y-xy[1])<=1 for a,x,y in reserved):
                        blockers.append([sid,eid,"reserved_arrival"]);continue
                    if not (0<xy[0]<len(grid[0])-1 and 0<xy[1]<len(grid)-1) or not non_cut(points,xy):
                        blockers.append([sid,eid,"route_connectivity"]);continue
                    # Stable reserved slots after all F10B3 IDs; no renumbering.
                    event_id=original_max[mid]+({29:2,30:3,37:3}[eid])
                    if event_id in events:
                        blockers.append([sid,eid,"event_id_collision"]);continue
                    reserved_cells.add((mid,*xy))
                    key="F10B_%d_%d"%(sid,eid);sprite_name="SNQA_"+key
                    page=event_page(script='BlueSinnohF10B.battle("%s")'%key,sprite=sprite_name)
                    event=ruby("RPG::Event",id=event_id,name=("SN_"+key).encode("ascii"),x=xy[0],y=xy[1],pages=[page])
                    row={"key":key,"source_id":sid,"source_event_id":eid,"map_id":mid,"event_id":event_id,
                         "position":list(xy),"type":kind,"name":name,"version":version,"team":team,
                         "sprite_sha256":hashlib.sha256(data).hexdigest(),"sprite_provenance":provenance,
                         "team_source":"PLATINUM_HISTORICAL_REFERENCE","historical_reference_name":name,
                         "battle_group":group,"placement_policy":"AUTHORED_STATIONARY" if group=="HARRY_STATIONARY" else "ORIGINAL_POSITION_ACTION_DOUBLE"}
                    staged.append((mid,event_id,event,sprite_name,data,row))
                if not blockers and len(staged)==len(keys):
                    # Re-run the actual teleport planner with all additions.
                    # Roll back the entire group if ANY prior spawn changes.
                    candidate=dict(out)
                    trial={}
                    for mid,eid,event,sn,data,row in staged:
                        trial.setdefault(mid,dict(worlds[mid].attrs["@events"]))[eid]=event
                    previous={}
                    for mid,events in trial.items():
                        previous[mid]=worlds[mid].attrs["@events"]
                        worlds[mid].attrs["@events"]=events
                        candidate["Data/Map%03d.rxdata"%mid]=serialize(worlds[mid],EVENT_CLASSES)
                    for mid in changed-set(trial):
                        candidate["Data/Map%03d.rxdata"%mid]=serialize(worlds[mid],EVENT_CLASSES)
                    try:
                        safe=teleport.build(candidate,mapping,components,root)==entries
                    except ValueError:
                        safe=False
                    if not safe:
                        for mid,events in previous.items():worlds[mid].attrs["@events"]=events
                        blockers.append(["GROUP","ALL","qa_spawn_changed"])
                    else:
                        for mid,eid,event,sn,data,row in staged:
                            out["Graphics/Characters/"+sn+".png"]=data
                            changed.add(mid);used.add((row["source_id"],row["name"]))
                            rows.append([row["key"],[row["type"],row["name"],row["version"],mid,row["team"]]])
                            accepted.append(row)
                        if group=="ROUTE207_DOUBLE":
                            rejected[:]=[row for row in rejected if (row["source_id"],row["source_event_id"]) not in keys]
                extra_report.append({"group":group,"source_events":[list(k) for k in keys],
                                     "accepted":not blockers and len(staged)==len(keys),"blockers":blockers})
        access_report=[]
        if revision>=5:
            lookup={(q["source_id"],q["source_event_id"]):q for q in all_trainers}
            for key,gating in sorted(F10B5_GATED.items()):
                access_report.append({"source_id":key[0],"source_event_id":key[1],"accepted":False,
                                      "reason":gating,"position_preserved":True})
            for (sid,eid),(literal_kind,literal_name) in sorted(F10B5_PENDING.items()):
                q=lookup[sid,eid];mid=q["qa_map_id"];xy=tuple(q["position"])
                if any(r["source_id"]==sid and r["source_event_id"]==eid for r in accepted):
                    access_report.append({"source_id":sid,"source_event_id":eid,"accepted":True,"reason":"prior_revision"})
                    continue
                raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
                if hashlib.sha256(raw).hexdigest()!=source[sid]["sha256"]:raise ValueError("F10B5_SOURCE_HASH")
                donor=conn.read_marshal(raw,"F10B5_DONOR").attrs["@events"][eid]
                literal,_=literal_identity(donor)
                row={"source_id":sid,"source_event_id":eid,"name":literal_name,"original_position":list(xy),
                     "accepted":False,"position_preserved":True}
                access_report.append(row)
                if literal!=(literal_kind,literal_name):
                    row["reason"]="literal_identity_changed";continue
                if (sid,eid)==(42,34):
                    # Source class is CRUSHGIRL; historical Platinum uses
                    # Battle Girl. Explicit role alias only for this event.
                    name="Helen";kind="BATTLEGIRL";team=REFERENCES[42]["Helen"][1]
                    allowed_types=("CRUSHGIRL",*ALIASES[kind])
                else:
                    spec,why=identity(donor,sid,revision)
                    if not spec:row["reason"]=why;continue
                    _,name,kind,team=spec
                    allowed_types=(literal_kind,*ALIASES[kind])
                local=next((k for k in allowed_types if k in types),None)
                version=1000+sid*100+eid
                if not local or any(mon not in species for mon,level in team):
                    row["reason"]="local_pbs_catalogue";continue
                if (local,name,version) in existing or (sid,name) in used:
                    row["reason"]="local_pbs_collision";continue
                # Recompute after each addition, so occupied cells cannot be
                # used as a route or hide a newly introduced articulation.
                ground,anchors=access_witnesses(blobs,worlds,mapping,components,entries)
                events=worlds[mid].attrs["@events"]
                occupied={(e.attrs["@x"],e.attrs["@y"]) for e in events.values()}
                grid=masks[mid]
                plain=conn.safe_cells(worlds[mid],conn.read_marshal(blobs["Data/Tilesets.rxdata"],"F10B5_PLAIN_TILES"),q["symbol"],allowed={0})
                row["entry_witness_count"]=len(anchors[mid])
                if xy not in plain or not (0<xy[0]<len(grid[0])-1 and 0<xy[1]<len(grid)-1):
                    row["reason"]="original_cell_not_plain_ground";continue
                if any(a==mid and abs(x-xy[0])+abs(y-xy[1])<=1 for a,x,y in reserved):
                    row["reason"]="reserved_arrival";continue
                witness,_=witness_component(ground[mid]-occupied,anchors[mid],xy)
                row["access_witness"]=witness
                if witness is None:row["reason"]="no_existing_safe_access_witness";continue
                data,provenance,labels=f10b5_art(z,ow,donor,kind,base,(sid,eid))
                row["sprite_candidates"]=labels
                if not data:row["reason"]="class_sprite_missing_or_ambiguous";continue
                # Slots 1..3 are reserved for earlier revisions; exact
                # deterministic slots leave all previous self-switch IDs intact.
                slot={(42,32):4,(42,33):5,(42,34):6,(79,32):4,(79,35):2}[sid,eid]
                event_id=original_max[mid]+slot
                if event_id in events:row["reason"]="event_id_collision";continue
                key="F10B_%d_%d"%(sid,eid);sn="SNQA_"+key
                page=event_page(script='BlueSinnohF10B.battle("%s")'%key,sprite=sn)
                event=ruby("RPG::Event",id=event_id,name=("SN_"+key).encode("ascii"),x=xy[0],y=xy[1],pages=[page])
                events[event_id]=event
                trial=dict(out)
                for n in changed|{mid}:trial["Data/Map%03d.rxdata"%n]=serialize(worlds[n],EVENT_CLASSES)
                try:safe=teleport.build(trial,mapping,components,root)==entries
                except ValueError:safe=False
                if not safe:
                    del events[event_id];row["reason"]="qa_spawn_changed";continue
                out["Graphics/Characters/"+sn+".png"]=data
                changed.add(mid);used.add((sid,name))
                rows.append([key,[local,name,version,mid,team]])
                accepted.append({"key":key,"source_id":sid,"source_event_id":eid,"map_id":mid,"event_id":event_id,
                    "position":list(xy),"type":local,"name":name,"version":version,"team":team,
                    "sprite_sha256":hashlib.sha256(data).hexdigest(),"sprite_provenance":provenance,
                    "team_source":"PLATINUM_HISTORICAL_REFERENCE","historical_reference_name":REVIEWED_NAME_ALIASES.get((sid,literal_kind,name),name),
                    "placement_policy":"ORIGINAL_POSITION_EXISTING_ACCESS_WITNESS","access_witness":witness})
                row["accepted"]=True;row["reason"]="original_position_validated"
                rejected[:]=[r for r in rejected if (r["source_id"],r["source_event_id"])!=(sid,eid)]
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
            "source_pbs_present":False,"action_only":True,"all_trainer_diagnostics":expanded,
            "all_source_trainer_candidates":len(expanded),"overworld_archive_checked":overworlds is not None,
            "revision":revision,"f10b4_groups":extra_report if revision>=4 else [],
            "f10b5_access_report":access_report if revision>=5 else []}
    return out,report,plugin

def append(blobs,mapping,masks,components,path,base,root=ROOT,overworlds=None,revision=5):
    existing=set()
    for p in (base/"PBS").glob("trainers*.txt"):
        if p.is_symlink():raise ValueError("F10B_UNSAFE_PBS")
        for header in read_blocks(p):
            fields=[v.strip() for v in header.split(",")]
            if len(fields) in (2,3) and (len(fields)==2 or fields[2].isdigit()):
                existing.add((fields[0],fields[1],int(fields[2]) if len(fields)==3 else 0))
    out,report,plugin=build(blobs,mapping,masks,components,path,catalogue(base,"trainer_types"),catalogue(base,"pokemon"),existing,base,root,overworlds,revision)
    print(("SINNOH_F10B5_TRAINER_REPORT " if revision>=5 else "SINNOH_F10B4_TRAINER_REPORT " if revision==4 else "SINNOH_F10B3_TRAINER_REPORT " if revision==3 else "SINNOH_F10B2_ASSET_REPORT ")+json.dumps(report,sort_keys=True),flush=True)
    return out,report,plugin
