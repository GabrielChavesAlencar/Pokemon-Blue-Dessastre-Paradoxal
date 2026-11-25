"""Inert F12C3 candidate: actual event and plugin bytes, never writes the base.
Historical Jupiter roster; condensed authored grunts/rescue/bicycle layout.
"""
import hashlib
import json
import sinnoh_connection_expansion as conn
import sinnoh_f10b_trainers as trainers
import sinnoh_f10c_npcs as npc
import sinnoh_f12b2_windworks_evidence as evidence
import sinnoh_f12b5_authored_quest as mars
import sinnoh_f12c2_eterna_preview as preview
import sinnoh_private_visual as pv
from build_johto_events import EVENT_CLASSES,ruby,event_page
from stage import serialize

GRUNTS=mars.GRUNTS
JUPITER=("COMMANDER_JUPITER","GALACTIC_JUPITER","GALACTIC_ADMIN","GALACTICADMIN","ADMIN_JUPITER","JUPITER","BLUE_SINNOH_BOSS_JUPITER")
BIKES=("BICYCLE","BIKE")
ROWS=(("GRUNT_1",1,(9,5),[["ZUBAT",17]]),
      ("GRUNT_2",2,(9,4),[["STUNKY",17]]),
      ("GRUNT_3",3,(9,5),[["GLAMEOW",19]]),
      ("JUPITER",4,preview.BOSS,[["ZUBAT",21],["SKUNTANK",23]]),
      ("RESCUE",4,(7,3),None),("BICYCLE",4,(11,3),None))

def entrance_source(path):
    with pv.verified_archive(path,"maps") as z:
        raw=pv.member(z,pv.MAP_ROOT+"Data/Map090.rxdata")
        if hashlib.sha256(raw).hexdigest()!="b28d2a456cc4cb4218fa1c4387cd3159ed84ef8b945585597ee98ac10be4139e":
            raise ValueError("F12C3_ETERNA_HASH")
        e=conn.read_marshal(raw,"F12C3_ETERNA").attrs["@events"][22]
        r=evidence.event_evidence(e,22)
        if r["position"]!=[14,15]:raise ValueError("F12C3_EVENT22_POSITION")
        return {"source_id":90,"event_id":22,"source_position":r["position"],
                "markers":r["markers"],"pages":r["pages"],
                "static_targets":r["source_transfer_targets"],"binding_approved":False}

def build(blobs,mapping,delta,report,types,species,items,existing,root):
    def blocked(reason):
        return {},{"status":"F12C3_BLOCKED","reason":reason,"new_events":0,"items_granted":0,
                  "runtime_install_enabled":False,"native_verified":False},b""
    if report.get("status")!="AUTHORED_FOUR_MAP_PREVIEW" or report.get("baseline_preserved") is not True or len(mapping)!=140:
        return blocked("requires_valid_144_map_preview")
    rooms=report.get("rooms",[])
    if len(rooms)!=4 or [r["floor"] for r in rooms]!=[1,2,3,4]:return blocked("invalid_room_inventory")
    grunt=mars.choose(types,GRUNTS);jupiter=mars.choose(types,JUPITER);bike=mars.choose(items,BIKES)
    if not grunt or not jupiter or grunt==jupiter or not bike:return blocked("local_types_or_bicycle_missing_or_ambiguous")
    if any(mon not in species for _,_,_,team in ROWS for mon,_ in team or []):return blocked("local_species_missing")
    ids=[r["map_id"] for r in rooms];entry=report["city_entry_candidate"]
    if set(ids)&set(mapping.values()) or len(set(ids))!=4:return blocked("mapid_collision")
    candidate=dict(delta);specs={};positions=[];pbs=[]
    for i,(key,floor,xy,team) in enumerate(ROWS):
        mid=ids[floor-1];rel="Data/Map%03d.rxdata"%mid
        world=conn.read_marshal(candidate[rel],"F12C3_ROOM");ev=world.attrs["@events"]
        busy={(e.attrs["@x"],e.attrs["@y"]) for e in ev.values()}
        ground=preview.layout(floor)
        if xy not in ground-busy or preview.access.component(ground-busy-{xy},next(iter(ground-busy-{xy})))!=ground-busy-{xy}:
            return blocked("unsafe_event_position:"+key)
        eid=max(max(ev,default=0)+1,3001)
        sprite="SNQA_F12C3_"+key
        ev[eid]=ruby("RPG::Event",id=eid,name=("SN_F12C3_"+key).encode(),x=xy[0],y=xy[1],
                     pages=[event_page(script='BlueSinnohF12C3.interact("'+key+'")',sprite=sprite)])
        candidate[rel]=serialize(world,EVENT_CLASSES)
        candidate["Graphics/Characters/"+sprite+".png"]=npc.authored_sheet("galactic_jupiter" if key=="JUPITER" else "galactic_grunt" if team else "galactic_rescue")
        if team:
            identity=(jupiter if key=="JUPITER" else grunt,"Jupiter" if key=="JUPITER" else "Grunt",13001+i)
            if identity in existing:return blocked("trainer_pbs_collision")
            specs[key]=[*identity,mid,team]
            pbs.append("\n[%s,%s,%d]\nLoseText = Voce venceu!\n"%identity+"".join("Pokemon = %s,%d\n"%(m,l) for m,l in team))
        else:specs[key]=[None,None,None,mid,[]]
        positions.append({"id":key,"map_id":mid,"event_id":eid,"position":list(xy)})
    city=entry["map_id"];xy=tuple(entry["position"]);rel="Data/Map%03d.rxdata"%city
    world=conn.read_marshal(blobs[rel],"F12C3_CITY");ev=world.attrs["@events"]
    if xy in {(e.attrs["@x"],e.attrs["@y"]) for e in ev.values()}:return blocked("city_entry_collision")
    eid=max(max(ev,default=0)+1,3001)
    ev[eid]=ruby("RPG::Event",id=eid,name=b"SN_F12C3_ENTRY",x=xy[0],y=xy[1],
                 pages=[event_page(script="BlueSinnohF12C3.enter",sprite="SNQA_F12C3_ENTRY")])
    candidate[rel]=serialize(world,EVENT_CLASSES)
    del ev[eid]
    if serialize(world,EVENT_CLASSES)!=blobs[rel]:return blocked("existing_city_content_changed")
    candidate["Graphics/Characters/SNQA_F12C3_ENTRY.png"]=npc.authored_sheet("galactic_grunt")
    candidate["PBS/trainers_sinnoh_f12c3.txt"]="".join(pbs).encode()
    template=(root/"scripts/regions/SinnohF12C3.rb").read_text("utf-8")
    literal="{"+",".join(json.dumps(k)+"=>"+json.dumps(v).replace("null","nil") for k,v in specs.items())+"}"
    for placeholder,value in (("__F12C3_SPECS__",literal),("__F12C3_ENTRY__",json.dumps([city,*xy,*entry["destination"]])),("__F12C3_BIKE__",json.dumps(bike))):
        if template.count(placeholder)!=1:raise ValueError("F12C3_TEMPLATE")
        template=template.replace(placeholder,value)
    return candidate,{"status":"AUTHORED_QUEST_CANDIDATE","source_layout":"CONDENSED_AUTHORIAL_RESCUE_AND_BICYCLE",
        "placements":positions,"new_events":6,"battle_candidates":4,"entry_candidate":entry,"items_granted":0,
        "native_verified":False,"runtime_install_enabled":False,"local_bike_id":bike,
        "historical_jupiter_team":specs["JUPITER"][4],"catalog_provenance":"CALLER_SUPPLIED_NOT_COMPILED"},template.encode("utf-8")
