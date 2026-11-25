"""Author four real Marshal interior candidates in memory. No runtime activation.
Only a complete F12C1 source report permits a preview; a candidate is not
a recovered original. Entry is deliberately inert pending regional Cut binding.
"""
import copy
import hashlib
import struct
import sinnoh_connection_expansion as conn
import sinnoh_f11a_gym as gym
import sinnoh_f12b4_windworks_access as access
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as tp
from build_johto_events import EVENT_CLASSES,ruby,event_page
from server.ruby_marshal import RubyData
from stage import serialize

CITY="SINNOH_ETERNA_CITY"
SYMBOLS=tuple("SINNOH_GALACTIC_ETERNA_%dF"%i for i in range(1,5))
W,H=19,15
UP=(15,3)
DOWN=(3,11)
UP_LAND=(14,3)
DOWN_LAND=(4,11)
ENTRANCE=(9,12)
EXIT=(9,13)
BOSS=(9,3)
OBSTACLES=(
    {(5,y) for y in (3,4,5)}|{(13,y) for y in (8,9,10)},
    {(x,5) for x in range(4,9)}|{(x,9) for x in range(10,15)},
    {(6,y) for y in (3,4,5,6)}|{(12,y) for y in (8,9,10,11)},
    {(x,6) for x in (3,4,5,6,12,13,14,15)},
)
def allocate(mapping,occupied,infos,blobs):
    used=set(mapping.values())|set(occupied)|set(infos)
    free=[i for i in range(442,600) if i not in used and "Data/Map%03d.rxdata"%i not in blobs]
    return free[:4] if len(free)>=4 else []

def entry_allowed(private_copy,current_region,badges,regional_hm,compatible_pokemon,field_cut_allowed):
    # This pure contract is not a replacement for the engine's field-move API.
    return (private_copy is True and current_region=="SINNOH" and
            isinstance(badges,(list,tuple)) and "FOREST" in badges and
            regional_hm is True and compatible_pokemon is True and field_cut_allowed is True)

def layout(floor):
    if type(floor) is not int or not 1<=floor<=4:raise ValueError("F12C2_FLOOR")
    ground={(x,y) for y in range(1,H-1) for x in range(1,W-1)}-OBSTACLES[floor-1]
    stairs=({DOWN,DOWN_LAND} if floor>1 else {ENTRANCE,EXIT})|({UP,UP_LAND} if floor<4 else {BOSS})
    if not stairs<=ground or access.component(ground,next(iter(stairs)))!=ground:
        raise ValueError("F12C2_LAYOUT_DISCONNECTED")
    # Landing squares must not be the trigger squares.
    if UP==UP_LAND or DOWN==DOWN_LAND or ENTRANCE==EXIT:raise ValueError("F12C2_LANDING")
    return ground

def tileset_png():
    w,h=256,32;raw=bytearray(w*h*4)
    colors=[(132,154,168),(40,57,74),(98,155,190),(66,82,104),(117,209,219),(180,160,94),(55,71,87),(45,52,65)]
    for y in range(h):
        for x in range(w):
            n=x//32;xx=x%32;c=colors[n]
            shade=-14 if xx in (0,31) or y in (0,31) else (8 if (xx//8+y//8)%2==0 else 0)
            k=(y*w+x)*4;raw[k:k+4]=bytes(tuple(max(0,min(255,v+shade)) for v in c)+(255,))
    return pv.png(w,h,bytes(raw))

def preview(blobs,mapping,components,occupied,report,root):
    result={"status":"F12C2_PREVIEW_BLOCKED","maps_before":len(mapping),"maps_after":len(mapping),
            "native_verified":False,"runtime_install_enabled":False,"new_portals":0,"items_granted":0,
            "native_bindings":0,"source_layout":"PROJECT_AUTHORED_CANDIDATE_NOT_ORIGINAL",
            "entry_requires":["FOREST","REGIONAL_HM01","COMPATIBLE_PARTY","ENGINE_CUT_GATE"]}
    def blocked(reason):
        return {},result|{"reason":reason}
    if set(mapping)!=access.ALL or len(set(mapping.values()))!=140:return blocked("requires_140_baseline")
    if not isinstance(report,dict) or report.get("status")!="SOURCE_CANDIDATES_ONLY" or report.get("source_maps_scanned")!=238 or report.get("baseline_preserved") is not True or report.get("native_verified") is not False:
        return blocked("requires_complete_f12c1_report")
    # No authoring over any recovered candidate: require human review of identities.
    if report.get("named_candidates"):return blocked("named_source_candidate_requires_review")
    before={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}
    infos=conn.read_marshal(blobs["Data/MapInfos.rxdata"],"F12C2_INFOS")
    ids=allocate(mapping,occupied,infos,blobs)
    if len(ids)!=4:return blocked("insufficient_free_mapids")
    city=mapping[CITY]
    entrance=next(gym.city_entrance(blobs,mapping,components,root,CITY),None)
    if entrance is None:return blocked("no_safe_city_entrance")
    _,entry,return_xy=entrance
    tiles=conn.read_marshal(blobs["Data/Tilesets.rxdata"],"F12C2_TILES")
    template=conn.read_marshal(blobs["Data/Map%03d.rxdata"%mapping["SINNOH_PLAYER_HOUSE_1F"]],"F12C2_TEMPLATE")
    tid=len(tiles)
    if tid>=5000:return blocked("tileset_capacity")
    tile=copy.deepcopy(tiles[template.attrs["@tileset_id"]])
    name="SNQA_F12C2_GALACTIC"
    tile.attrs.update({"@id":tid,"@name":name.encode(),"@tileset_name":name.encode(),
      "@autotile_names":[b""]*7,"@passages":pv.table1([15]*384+[0,15,0,15,0,0,15,15]),
      "@priorities":pv.table1([0]*392),"@terrain_tags":pv.table1([0]*392)})
    tiles.append(tile)
    delta={};links=[];rooms=[]
    def warp(eid,xy,mid,land,label):
        return ruby("RPG::Event",id=eid,name=label.encode("ascii"),x=xy[0],y=xy[1],
                    pages=[event_page(warp=(mid,*land),touch=True)])
    for i,mid in enumerate(ids):
        ground=layout(i+1)
        cells=[0]*(W*H*3)
        for y in range(H):
            for x in range(W):
                p=(x,y)
                cells[y*W+x]=(385 if p not in ground else 384)
        if i<3:cells[UP[1]*W+UP[0]]=388
        if i>0:cells[DOWN[1]*W+DOWN[0]]=389
        if i==0:cells[EXIT[1]*W+EXIT[0]]=389
        room=copy.deepcopy(template)
        events={}
        if i<3:
            events[1]=warp(1,UP,ids[i+1],DOWN_LAND,"SN_F12C2_UP")
            links.append([mid,list(UP),ids[i+1],list(DOWN_LAND)])
        if i>0:
            events[2]=warp(2,DOWN,ids[i-1],UP_LAND,"SN_F12C2_DOWN")
            links.append([mid,list(DOWN),ids[i-1],list(UP_LAND)])
        else:
            events[2]=warp(2,EXIT,city,return_xy,"SN_F12C2_EXIT")
            links.append([mid,list(EXIT),city,list(return_xy)])
        room.attrs.update({"@width":W,"@height":H,"@tileset_id":tid,"@events":events,
          "@data":RubyData("Table",struct.pack("<5I",3,W,H,3,len(cells))+struct.pack("<%dH"%len(cells),*cells))})
        rel="Data/Map%03d.rxdata"%mid
        raw=serialize(room,EVENT_CLASSES)
        decoded=conn.read_marshal(raw,"F12C2_ROUNDTRIP")
        if conn.safe_cells(decoded,tiles,SYMBOLS[i],allowed={0})!=ground:
            raise ValueError("F12C2_SERIALIZED_COLLISION_MISMATCH")
        # Validate the actual serialized warp commands, not only the plan.
        actual=[]
        for event in decoded.attrs["@events"].values():
            for page in event.attrs["@pages"]:
                for command in page.attrs["@list"]:
                    c=command.attrs
                    if c.get("@code")==201:
                        a=c["@parameters"]
                        if len(a)!=6 or a[0]!=0:raise ValueError("F12C2_WARP_FORMAT")
                        actual.append([mid,[event.attrs["@x"],event.attrs["@y"]],a[1],list(a[2:4])])
        if sorted(actual)!=sorted(x for x in links if x[0]==mid):raise ValueError("F12C2_WARP_MISMATCH")
        delta[rel]=raw
        info=copy.deepcopy(infos[city])
        label="Galactic Eterna Building %dF - QA"%(i+1)
        info.attrs.update({"@name":label.encode("ascii"),"@parent_id":0,
            "@order":max(x.attrs["@order"] for x in infos.values())+1})
        infos[mid]=info
        rooms.append({"symbol":SYMBOLS[i],"map_id":mid,"floor":i+1,"walkable_cells":len(ground),
                      "sha256":hashlib.sha256(raw).hexdigest(),"native_verified":False})
    for src,xy,dst,land in links:
        if dst in ids:
            i=ids.index(dst)
            triggers={tuple(x[1]) for x in links if x[0]==dst}
            if tuple(land) not in layout(i+1) or tuple(land) in triggers:raise ValueError("F12C2_UNSAFE_LANDING")
    delta["Data/MapInfos.rxdata"]=serialize(infos)
    delta["Data/Tilesets.rxdata"]=serialize(tiles)
    delta["Graphics/Tilesets/"+name+".png"]=tileset_png()
    if before!={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}:raise ValueError("F12C2_BASELINE_MUTATED")
    result.update(status="AUTHORED_FOUR_MAP_PREVIEW",maps_after=144,rooms=rooms,preview_links=links,
       preview_portal_candidates=8,baseline_preserved=True,city_entry_candidate={"map_id":city,
       "position":list(entry),"return":list(return_xy),"destination":[ids[0],*ENTRANCE],"active":False},
       jupiter_position_candidate=[ids[3],*BOSS],source_candidates_pending_review=len(report.get("event_candidates",[])))
    return delta,result
