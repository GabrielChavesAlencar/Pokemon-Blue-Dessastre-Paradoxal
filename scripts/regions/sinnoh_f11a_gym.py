"""F11A: private authored Oreburgh challenge room, not an original gym import.
Real job 138898048760: zero rooms, exact Roark sprite missing.
"""
import copy
import hashlib
import json
import re
import struct
import sinnoh_connection_expansion as conn
import sinnoh_f10b_trainers as f
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10c_npcs as npc
import sinnoh_f08c_expansion as f08c
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as tp
from build_johto_events import EVENT_CLASSES,ruby,event_page
from server.ruby_marshal import RubyData
from stage import serialize

SYMBOL="SINNOH_OREBURGH_GYM"
CITY="SINNOH_OREBURGH_CITY"
TYPE_ALIASES=("LEADER_ROARK","LEADER_Roark","LEADERROARK","BLUE_SINNOH_LEADER_ROARK")
TEAM=[["GEODUDE",12],["ONIX",12],["CRANIDOS",14]]
VERSION=11001
GARDENIA_SYMBOL="SINNOH_ETERNA_GYM"
GARDENIA_CITY="SINNOH_ETERNA_CITY"
GARDENIA_TEAM=[["TURTWIG",20],["CHERRIM",20],["ROSERADE",22]]
GARDENIA_TYPES=("LEADER_GARDENIA","LEADER_Gardenia","LEADERGARDENIA","BLUE_SINNOH_LEADER_GARDENIA")
GARDENIA_VERSION=11002
FANTINA_SYMBOL="SINNOH_HEARTHOME_GYM"
FANTINA_CITY="SINNOH_HEARTHOME_CITY"
FANTINA_TEAM=[["DUSKULL",24],["HAUNTER",24],["MISMAGIUS",26]]
FANTINA_TYPES=("LEADER_FANTINA","LEADER_Fantina","LEADERFANTINA","BLUE_SINNOH_LEADER_FANTINA")
FANTINA_VERSION=11003
MAYLENE_SYMBOL="SINNOH_VEILSTONE_GYM"
MAYLENE_CITY="SINNOH_VEILSTONE_CITY"
MAYLENE_TEAM=[["MEDITITE",28],["MACHOKE",29],["LUCARIO",32]]
MAYLENE_TYPES=("LEADER_MAYLENE","LEADER_Maylene","LEADERMAYLENE","BLUE_SINNOH_LEADER_MAYLENE")
MAYLENE_VERSION=11004
GYM_SETS=(f08c.ALL|{SYMBOL},f08c.ALL|{SYMBOL,GARDENIA_SYMBOL},f08c.ALL|{SYMBOL,GARDENIA_SYMBOL,FANTINA_SYMBOL},f08c.ALL|{SYMBOL,GARDENIA_SYMBOL,FANTINA_SYMBOL,MAYLENE_SYMBOL})
GYM_SPECS={
    "Roark":(SYMBOL,CITY,TEAM,TYPE_ALIASES,VERSION,"F11A","Oreburgh Gym - QA"),
    "Gardenia":(GARDENIA_SYMBOL,GARDENIA_CITY,GARDENIA_TEAM,GARDENIA_TYPES,GARDENIA_VERSION,"F11B","Eterna Gym - QA"),
    "Fantina":(FANTINA_SYMBOL,FANTINA_CITY,FANTINA_TEAM,FANTINA_TYPES,FANTINA_VERSION,"F11C","Hearthome Gym - QA"),
    "Maylene":(MAYLENE_SYMBOL,MAYLENE_CITY,MAYLENE_TEAM,MAYLENE_TYPES,MAYLENE_VERSION,"F11D","Veilstone Gym - QA"),
}
LEADER_ORDER=("Roark","Gardenia","Fantina","Maylene")
W,H=15,12
LEADER=(7,3)
EXIT=(7,10)
ENTRY=(7,9)

def roster(root):
    contract=json.loads((root/"data/regions/sinnoh-gyms-s15.json").read_text("utf-8"))
    teams=json.loads((root/"data/regions/sinnoh-trainer-teams-ch15.json").read_text("utf-8"))
    gyms=contract["gyms"];first=gyms[0];r=next(t for t in teams["trainers"] if t["id"]==first["id"])
    if len(gyms)!=8 or first["id"]!="SINNOH_ROARK" or first["badge"]!="COAL" or first["prerequisite_badges"] or list(map(list,zip(r["first_battle"]["species"],r["first_battle"]["historical_levels"])))!=TEAM:
        raise ValueError("F11A_GYM_CONTRACT_CHANGED")
    second=gyms[1];s=next(t for t in teams["trainers"] if t["id"]==second["id"])
    if second["id"]!="SINNOH_GARDENIA" or second["badge"]!="FOREST" or second["prerequisite_badges"]!=["COAL"] or list(map(list,zip(s["first_battle"]["species"],s["first_battle"]["historical_levels"])))!=GARDENIA_TEAM:
        raise ValueError("F11B_GYM_CONTRACT_CHANGED")
    third=gyms[2];t=next(t for t in teams["trainers"] if t["id"]==third["id"])
    if third["id"]!="SINNOH_FANTINA" or third["badge"]!="RELIC" or third["prerequisite_badges"]!=["COAL","FOREST"] or list(map(list,zip(t["first_battle"]["species"],t["first_battle"]["historical_levels"])))!=FANTINA_TEAM:
        raise ValueError("F11C_GYM_CONTRACT_CHANGED")
    fourth=gyms[3];m=next(t for t in teams["trainers"] if t["id"]==fourth["id"])
    if fourth["id"]!="SINNOH_MAYLENE" or fourth["badge"]!="COBBLE" or fourth["prerequisite_badges"]!=["COAL","FOREST","RELIC"] or list(map(list,zip(m["first_battle"]["species"],m["first_battle"]["historical_levels"])))!=MAYLENE_TEAM:
        raise ValueError("F11D_GYM_CONTRACT_CHANGED")
    return [{"id":g["id"],"badge":g["badge"],"order":g["order"],"installed":False} for g in gyms]

def tileset_png(leader='Roark'):
    # Authored rock-floor/wall arena; no protected image copied.
    w,h=256,32;raw=bytearray(w*h*4)
    colors={"Roark":[(148,139,123),(65,61,58),(193,157,95),(93,83,72)],
            "Gardenia":[(125,158,106),(53,91,64),(222,196,106),(69,119,75)],
            "Fantina":[(100,83,142),(45,34,72),(179,153,215),(66,53,103)],
            "Maylene":[(156,111,91),(73,55,49),(227,190,144),(112,78,68)]}[leader]
    for y in range(h):
        for x in range(w):
            tile=x//32;xx=x%32
            c=colors[tile] if tile<len(colors) else (32,32,32)
            shade=(-16 if xx in (0,31) or y in (0,31) else (8 if (xx//8+y//8)%2==0 else 0))
            i=(y*w+x)*4;raw[i:i+4]=bytes(tuple(max(0,min(255,v+shade)) for v in c)+(255,))
    return pv.png(w,h,bytes(raw))

def allocate(mapping,occupied,infos):
    ids=set(mapping.values())|set(occupied)|set(infos)
    return next((i for i in range(442,600) if i not in ids),None)

def exact_leader_type(types,aliases=TYPE_ALIASES):
    matches=[t for t in aliases if t in types]
    return matches[0] if len(matches)==1 else None

def city_entrance(blobs,mapping,components,root,city=CITY):
    mid=mapping[city];world=conn.read_marshal(blobs["Data/Map%03d.rxdata"%mid],"F11A_CITY")
    tiles=conn.read_marshal(blobs["Data/Tilesets.rxdata"],"F11A_TILES")
    events=world.attrs["@events"];occupied={(e.attrs["@x"],e.attrs["@y"]) for e in events.values()}
    reserved={tuple(row[3][1:]) for row in tp.build(blobs,mapping,components,root) if row[3] and row[3][0]==mid}
    for m in mapping.values():
        src=conn.read_marshal(blobs["Data/Map%03d.rxdata"%m],"F11A_PORTALS")
        for e in src.attrs["@events"].values():
            for p in e.attrs["@pages"]:
                for c in p.attrs["@list"]:
                    args=c.attrs.get("@parameters",[])
                    if c.attrs.get("@code")==201 and len(args)==6 and args[0]==0 and args[1]==mid and all(type(v) is int for v in args):
                        reserved.add(tuple(args[2:4]))
    points=conn.safe_cells(world,tiles,city,allowed={0,2})&components[city]
    plain=conn.safe_cells(world,tiles,city,allowed={0})
    w,h=world.attrs["@width"],world.attrs["@height"]
    _,_,index,_,reached,_=gates.access_graph(blobs,mapping,components,root,directional=True)
    for xy in sorted(plain&points,key=lambda xy:(abs(xy[0]-w//2)+abs(xy[1]-h//2),xy[1],xy[0])):
        x,y=xy
        if not (1<x<w-2 and 1<y<h-2):continue
        if not npc.safe_cell(points,xy,reserved,occupied):continue
        label=index[mid].get(xy)
        if label is None or (mid,label) not in reached:continue
        for land in sorted(tp.neighbours(*xy)):
            if land not in plain or land not in points-occupied or land in reserved:continue
            if any(conn.distance(land,e)<=1 for e in occupied|reserved):continue
            yield world,xy,land

def build(blobs,mapping,components,occupied,types,species,existing,root=f.ROOT,overworlds=None,base=None,leader='Roark',allow_authored=False):
    gyms=roster(root)
    if leader not in GYM_SPECS:raise ValueError('F11_UNKNOWN_LEADER')
    order=LEADER_ORDER.index(leader)
    symbol,city,team,aliases,version,tag,label=GYM_SPECS[leader]
    report={"gyms":gyms,"gym_rooms_added":0,"gym_leaders_added":0,"new_portals":0,
            "maps_before":len(mapping),"maps_after":len(mapping),"native_verified":False,
            "source_layout":"PROJECT_AUTHORED_CHALLENGE_ROOM_NOT_ORIGINAL_GYM",
            "hm_award_enabled":False,"water_enabled":False}
    expected=GYM_SETS[order-1] if order else f08c.ALL
    if order and set(mapping) in (f08c.ALL,*GYM_SETS[:order-1]):
        report["blocker"]=LEADER_ORDER[order-1].lower()+"_predecessor_not_prepared"
        for i,prior in enumerate(LEADER_ORDER[:order]):
            ps=GYM_SPECS[prior][0]
            if ps in mapping:gyms[i].update(installed=True,map_id=mapping[ps])
        return blobs,mapping,components,report,b""
    if set(mapping)!=expected:raise ValueError("F11_GYM_BASELINE")
    for i,prior in enumerate(LEADER_ORDER[:order]):
        gyms[i].update(installed=True,map_id=mapping[GYM_SPECS[prior][0]])
    local=exact_leader_type(types,aliases)
    if not local or any(s not in species for s,l in team) or (local,leader,version) in existing:
        report["blocker"]="local_"+leader.lower()+"_type_species_or_pbs_collision";return blobs,mapping,components,report,b""
    infos=conn.read_marshal(blobs["Data/MapInfos.rxdata"],"F11A_INFOS")
    mid=allocate(mapping,occupied,infos)
    if mid is None:
        report["blocker"]="no_free_mapid";return blobs,mapping,components,report,b""
    # Prefer exact overworld class sheet. Do not substitute another leader.
    art=None;labels=[]
    if overworlds:
        with pv.verified_archive(overworlds,"overworlds") as z:
            pattern=re.compile(re.escape(pv.OW_ROOT)+r"NPC_\d+_"+re.escape(leader)+r"\.png",re.I)
            matches=[i.filename for i in z.infolist() if pattern.fullmatch(i.filename)]
            labels=[s.rsplit("/",1)[-1] for s in matches]
            if len(matches)==1:
                data=pv.member(z,matches[0],1_000_000)
                if pv.dims(data)==(256,256):art=data
    provenance="EXACT_DPPt_OVERWORLD"
    if art is None and allow_authored and not labels:
        art=npc.authored_sheet("gym_"+leader.lower())
        provenance="PROJECT_AUTHORED_LEADER_NOT_DONOR"
    if art is None:
        report["blocker"]=leader.lower()+"_overworld_missing_or_ambiguous";report["sprite_candidates"]=labels
        return blobs,mapping,components,report,b""
    tiles=conn.read_marshal(blobs["Data/Tilesets.rxdata"],"F11A_TILES")
    template=conn.read_marshal(blobs["Data/Map%03d.rxdata"%mapping["SINNOH_PLAYER_HOUSE_1F"]],"F11A_TEMPLATE")
    tile=copy.deepcopy(tiles[template.attrs["@tileset_id"]]);tid=len(tiles)
    if tid>=5000:raise ValueError("F11A_TILESET_CAPACITY")
    name="SNQA_"+tag+("_ROCK_GYM","_GRASS_GYM","_GHOST_GYM","_FIGHTING_GYM")[order]
    tile.attrs.update({"@id":tid,"@name":name.encode(),"@tileset_name":name.encode(),
                       "@autotile_names":[b""]*7,"@passages":pv.table1([15]*384+[0,15,0,15,15,15,15,15]),
                       "@priorities":pv.table1([0]*392),"@terrain_tags":pv.table1([0]*392)})
    tiles.append(tile)
    floor={(x,y) for y in range(1,H-1) for x in range(1,W-1)}
    cells=[0]*(W*H*3)
    for y in range(H):
        for x in range(W):
            cells[y*W+x]=385 if (x,y) not in floor else (386 if 5<=x<=9 and 2<=y<=4 else 384)
    pillars=(((3,4),(11,4),(3,6),(11,6)) if order<2 else
             ((3,3),(11,3),(5,6),(9,6),(3,8),(11,8)) if order==2 else
             ((4,3),(10,3),(4,5),(10,5),(4,7),(10,7),(2,8),(12,8)))
    for xy in pillars:
        cells[xy[1]*W+xy[0]]=387;floor.remove(xy)
    room=copy.deepcopy(template)
    room.attrs.update({"@width":W,"@height":H,"@tileset_id":tid,"@events":{},
        "@data":RubyData("Table",struct.pack("<5I",3,W,H,3,len(cells))+struct.pack("<%dH"%len(cells),*cells))})
    city_mid=mapping[city]
    expanded={**mapping,symbol:mid};comps={**components,symbol:floor}
    old_entries=tp.build(blobs,mapping,components,root)
    _,_,idx,_,reach,_=gates.access_graph(blobs,mapping,components,root,directional=True)
    old_reached=f.reached_cells(idx,reach)
    for world,xy,land in city_entrance(blobs,mapping,components,root,city):
        ev=world.attrs["@events"];eid=max(max(ev,default=0)+1,2001)
        ev[eid]=ruby("RPG::Event",id=eid,name=("SN_"+tag+"_GYM_GUIDE").encode("ascii"),x=xy[0],y=xy[1],
                     pages=[event_page(warp=(mid,*ENTRY),sprite="SNQA_"+tag+"_GUIDE")])
        room.attrs["@events"]={
            1:ruby("RPG::Event",id=1,name=("SN_"+tag+"_"+leader.upper()).encode("ascii"),x=LEADER[0],y=LEADER[1],
                   pages=[event_page(script='BlueSinnoh'+tag+'.battle',sprite="SNQA_"+tag+"_"+leader.upper())]),
            2:ruby("RPG::Event",id=2,name=("SN_"+tag+"_EXIT").encode("ascii"),x=EXIT[0],y=EXIT[1],
                   pages=[event_page(warp=(city_mid,*land),touch=True)])}
        trial=dict(blobs);trial["Data/Map%03d.rxdata"%city_mid]=serialize(world,EVENT_CLASSES)
        trial["Data/Map%03d.rxdata"%mid]=serialize(room,EVENT_CLASSES)
        trial["Data/Tilesets.rxdata"]=serialize(tiles)
        try:
            if tp.build(trial,mapping,components,root)!=old_entries:continue
            _,_,post,_,reached,_=gates.access_graph(trial,mapping,components,root,directional=True)
            if not (old_reached-{(city_mid,*xy)})<=f.reached_cells(post,reached):continue
            new_entries=tp.build(trial,expanded,comps,root)
            if any(a!=b for a,b in zip(old_entries,new_entries) if a[0]!=symbol):continue
            if not f.non_cut(floor-{EXIT},LEADER) or ENTRY not in f.component(floor-{LEADER},EXIT):continue
        except ValueError:continue
        finally:
            del ev[eid]
        info=copy.deepcopy(infos[city_mid]);info.attrs.update({"@name":label.encode("ascii"),"@parent_id":0,
          "@order":max(i.attrs["@order"] for i in infos.values())+1})
        infos[mid]=info
        trial["Data/MapInfos.rxdata"]=serialize(infos)
        trial["PBS/map_metadata.txt"]=blobs["PBS/map_metadata.txt"]+("\n# %s authored QA gym\n[%03d]\nName = %s\nOutdoor = false\nShowArea = true\nBicycle = false\nSnapEdges = true\n"%(tag,mid,label)).encode("ascii")
        trial["Graphics/Tilesets/"+name+".png"]=tileset_png(leader)
        trial["Graphics/Characters/SNQA_"+tag+"_GUIDE.png"]=npc.authored_sheet("gym_guide")
        trial["Graphics/Characters/SNQA_"+tag+"_"+leader.upper()+".png"]=art
        trial["PBS/trainers_sinnoh_"+tag.lower()+".txt"]=("\n[%s,%s,%d]\nLoseText = Parabens pela vitoria!\n"%(local,leader,version)+"".join("Pokemon = %s,%d\n"%(s,l) for s,l in team)).encode("ascii")
        template=(root/("scripts/regions/Sinnoh"+tag+".rb")).read_text("utf-8")
        placeholder="__"+tag+"_SPEC__"
        if template.count(placeholder)!=1:raise ValueError("F11_TEMPLATE")
        plugin=template.replace(placeholder,json.dumps([local,leader,version,mid,team],ensure_ascii=True)).encode("utf-8")
        gyms[order].update(installed=True,map_id=mid,leader_event_id=1,source_layout="PROJECT_AUTHORED",team=team)
        report.update(gym_rooms_added=1,gym_leaders_added=1,new_portals=2,maps_after=len(expanded),sprite_provenance=provenance,
            city_guide={"map_id":city_mid,"event_id":eid,"position":list(xy),"return":list(land)},
            gym_entry=list(ENTRY),gym_exit=list(EXIT),sprite_sha256=hashlib.sha256(art).hexdigest(),
            trainer_type=local,source_pbs_present=False)
        return trial,expanded,comps,report,plugin
    report["blocker"]="no_city_entrance_preserving_existing_access"
    return blobs,mapping,components,report,b""

def append(blobs,mapping,components,occupied,base,root=f.ROOT,overworlds=None,leader='Roark',allow_authored=False):
    existing=set()
    for p in (base/"PBS").glob("trainers*.txt"):
        if p.is_symlink():raise ValueError("F11A_UNSAFE_PBS")
        for header in f.read_blocks(p):
            fields=[v.strip() for v in header.split(",")]
            if len(fields) in (2,3) and (len(fields)==2 or fields[2].isdigit()):
                existing.add((fields[0],fields[1],int(fields[2]) if len(fields)==3 else 0))
    return build(blobs,mapping,components,occupied,f.catalogue(base,"trainer_types"),f.catalogue(base,"pokemon"),existing,root,overworlds,base,leader,allow_authored)
