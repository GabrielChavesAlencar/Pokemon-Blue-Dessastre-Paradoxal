"""F10C: append-only, stationary dialogue NPCs in private Sinnoh QA.

F10C source job 138893998333 accepted both pinned residents.
Source event shapes and coordinates are verified, but dialogue and fallback
art are authored for this project. Never execute/copy donor scripts or text.
"""
import hashlib
import json
import struct
import zlib
import sinnoh_connection_expansion as conn
import sinnoh_f08c_expansion as f08c
import sinnoh_f10a_inventory as inv
import sinnoh_f10b_trainers as trainers
import sinnoh_f10b7_field_audit as gates
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as teleport
from build_johto_events import EVENT_CLASSES,ruby,event_page
from stage import serialize

# Source keys, exact original cells, project-authored contextual messages.
SPECS={
    (42,28):("SINNOH_ROUTE_207",(24,17),"route_resident",
             ["Esta é a Rota 207. As montanhas de Sinnoh têm caminhos bem diferentes.",
              "Observe o terreno antes de seguir. Nem toda passagem pode ser atravessada a pé."]),
    (81,2):("SINNOH_F07_INTERIOR_081",(5,5),"interior_resident",
            ["Olá, viajante! Já conheceu os arredores de Sinnoh?",
             "Cuide dos seus Pokémon e explore com calma. Cada lugar tem algo novo para descobrir."]),
}
PENDING={(148,4):(13,7),(149,2):(12,7)}
EXTRA={
    (148,4):("SINNOH_F07_INTERIOR_148",(13,7),"south_gate_resident",
             ["Você está no portão sul da Cycling Road.","Confira os requisitos de acesso antes de continuar."]),
    (149,2):("SINNOH_F07_INTERIOR_149",(12,7),"north_gate_resident",
             ["Este é o portão norte da Cycling Road.","As rotas de Sinnoh têm caminhos diferentes. Planeje sua viagem!"]),
}

def authored_sheet(role):
    # Two distinct, neutral resident designs, no donor image or likeness.
    palettes={"route_resident":((71,103,142),(200,146,71),(77,60,47)),
              "interior_resident":((139,87,118),(105,151,119),(84,51,35)),
              "south_gate_resident":((66,111,103),(194,160,76),(57,47,44)),
              "north_gate_resident":((83,96,155),(160,185,196),(103,70,45)),
              "gym_guide":((65,78,110),(225,189,78),(78,52,37)),
              "gym_roark":((103,105,113),(207,85,49),(151,80,40)),
              "gym_gardenia":((74,129,66),(231,184,75),(171,83,47)),
              "gym_fantina":((115,69,150),(229,190,218),(139,86,177)),
              "gym_maylene":((235,222,206),(166,55,65),(211,103,126)),
              "gym_crasher_wake":((48,107,176),(235,173,57),(57,84,126)),
              "gym_byron":((89,105,120),(199,152,69),(86,70,62)),
              "gym_candice":((122,157,186),(240,240,230),(58,57,70)),
              "gym_volkner":((48,69,111),(236,201,77),(205,169,74)),
              "galactic_grunt":((166,169,178),(66,85,124),(63,154,158)),
              "galactic_mars":((159,168,180),(85,83,121),(190,54,64)),
              "galactic_honey_man":((118,112,72),(208,178,65),(172,166,150))}
    shirt,accent,hair=palettes[role]
    w=h=128;raw=bytearray(w*h*4);ink=(42,44,52);skin=(222,178,138)
    for direction in range(4):
        for frame in range(4):
            sx,sy=frame*32,direction*32;bob=frame%2
            def rect(x0,y0,x1,y1,color):
                for y in range(y0,y1):
                    for x in range(x0,x1):
                        i=((sy+y)*w+sx+x)*4
                        raw[i:i+4]=bytes((*color,255))
            rect(9,4+bob,23,16+bob,ink);rect(10,5+bob,22,15+bob,hair)
            if direction!=3:
                rect(11,9+bob,21,15+bob,skin)
                if direction in (0,1):rect(12,11+bob,14,13+bob,ink)
                if direction in (0,2):rect(18,11+bob,20,13+bob,ink)
            if role=="gym_roark":
                rect(8,3+bob,24,8+bob,ink);rect(9,4+bob,23,7+bob,(207,85,49))
                rect(11,9+bob,21,10+bob,ink)
            if role=="gym_gardenia":
                rect(8,5+bob,24,8+bob,hair);rect(9,8+bob,12,16+bob,hair);rect(20,8+bob,23,16+bob,hair)
                rect(11,7+bob,21,9+bob,accent)
            if role=="gym_fantina":
                rect(7,4+bob,12,12+bob,hair);rect(20,4+bob,25,12+bob,hair)
                rect(11,3+bob,21,7+bob,hair);rect(14,4+bob,18,6+bob,accent)
            if role=="gym_maylene":
                rect(8,5+bob,12,13+bob,hair);rect(20,5+bob,24,13+bob,hair)
                rect(11,3+bob,21,7+bob,hair);rect(13,6+bob,19,8+bob,(235,155,172))
            if role=="gym_volkner":
                rect(8,4+bob,24,8+bob,hair);rect(10,3+bob,14,6+bob,hair)
                rect(16,2+bob,20,6+bob,hair);rect(20,7+bob,24,12+bob,hair)
            if role=="gym_candice":
                rect(7,5+bob,12,16+bob,hair);rect(20,5+bob,25,16+bob,hair)
                rect(10,3+bob,22,8+bob,hair);rect(12,6+bob,20,8+bob,accent)
            if role=="gym_byron":
                rect(8,3+bob,24,8+bob,hair);rect(10,12+bob,22,16+bob,hair)
                rect(12,10+bob,20,12+bob,skin)
            if role=="gym_crasher_wake":
                rect(8,4+bob,24,10+bob,shirt);rect(10,8+bob,22,11+bob,accent)
                rect(11,12+bob,21,15+bob,skin)
            rect(9,16+bob,23,26+bob,ink);rect(10,17+bob,22,25+bob,shirt)
            if role=="gym_crasher_wake":
                rect(9,17+bob,12,23+bob,skin);rect(20,17+bob,23,23+bob,skin)
                rect(12,22+bob,20,25+bob,accent)
            if role=="gym_maylene":
                rect(10,22+bob,22,24+bob,accent)
            x=(10,10,19,13)[direction];rect(x,17+bob,x+3,24+bob,accent)
            stride=(0,1,0,-1)[frame]
            for x,dy in ((11,stride),(17,-stride)):
                rect(x,25,x+4,29+dy,(69,73,88));rect(x-1,28+dy,x+5,30+dy,ink)
    def chunk(tag,data):
        return struct.pack(">I",len(data))+tag+data+struct.pack(">I",zlib.crc32(tag+data)&0xffffffff)
    scan=b"".join(b"\x00"+raw[y*w*4:(y+1)*w*4] for y in range(h))
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(scan,9))+chunk(b"IEND",b"")

def dialogue_shape(event):
    shape=inv.classify(event)
    if shape["kind"]!="simple_dialogue_candidate":return False
    page=event.attrs["@pages"][0].attrs
    codes=[c.attrs.get("@code") for c in page["@list"]]
    return bool(codes and codes[-1]==0 and codes.count(0)==1 and 101 in codes and
                all(c in (0,101,401,108,408) for c in codes) and
                len(trainers.sprite_names(event))==1)

def safe_cell(points,xy,reserved,occupied):
    if xy in occupied or any(abs(x-xy[0])+abs(y-xy[1])<=1 for x,y in reserved):return False
    if any(abs(x-xy[0])+abs(y-xy[1])<=1 for x,y in occupied):return False
    return trainers.non_cut(points-occupied,xy)

def build(blobs,mapping,masks,components,path,base=None,root=trainers.ROOT,revision=1):
    if len(mapping)!=131 or len(set(mapping.values()))!=131:raise ValueError("F10C_MAPIDS")
    source,_,_=conn.graph(root);source={**source,**{r["source_id"]:r for r in f08c.rows(root)}}
    report=inv.audit(blobs,mapping,masks,components,path,root)
    queue={(q["source_id"],q["source_event_id"]):q for q in report["queue"] if q["kind"]=="simple_dialogue_candidate"}
    if set(queue)!=set(SPECS)|set(PENDING):raise ValueError("F10C_DIALOGUE_INVENTORY_CHANGED")
    entries=teleport.build(blobs,mapping,components,root)
    reserved={tuple(row[3]) for row in entries if row[3]}
    worlds={mid:conn.read_marshal(blobs["Data/Map%03d.rxdata"%mid],"F10C_QA") for mid in mapping.values()}
    for world in worlds.values():
        for e in world.attrs["@events"].values():
            for p in e.attrs["@pages"]:
                for c in p.attrs["@list"]:
                    args=c.attrs.get("@parameters",[])
                    if c.attrs.get("@code")==201 and len(args)==6 and args[0]==0 and all(type(v) is int for v in args):
                        reserved.add(tuple(args[1:4]))
    if revision not in (1,2):raise ValueError('F10C_REVISION')
    specs={**SPECS,**EXTRA} if revision==2 else SPECS
    out=dict(blobs);rows=[];accepted=[];rejected=[]
    with pv.verified_archive(path,"maps") as z:
        for key,q in sorted(queue.items()):
            sid,eid=key;mid=q["qa_map_id"];xy=tuple(q["position"])
            row={"source_id":sid,"source_event_id":eid,"map_id":mid,"position":list(xy)}
            if key not in specs:
                if xy!=PENDING[key]:raise ValueError("F10C_PENDING_POSITION")
                rejected.append({**row,"reason":"outside_original_approved_component"});continue
            sym,expected,role,messages=specs[key]
            if q["symbol"]!=sym or xy!=expected:raise ValueError("F10C_PIN_CHANGED")
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=source[sid]["sha256"]:raise ValueError("F10C_SOURCE_HASH")
            donor=conn.read_marshal(raw,"F10C_DONOR").attrs["@events"][eid]
            if not dialogue_shape(donor):
                rejected.append({**row,"reason":"source_not_simple_dialogue"});continue
            if q["geometry_blockers"] and not (revision==2 and key in EXTRA and q["geometry_blockers"]==["outside_known_component"]):
                rejected.append({**row,"reason":"source_geometry_blocked","blockers":q["geometry_blockers"]});continue
            world=worlds[mid];events=world.attrs["@events"]
            occupied={(e.attrs["@x"],e.attrs["@y"]) for e in events.values()}
            tiles=conn.read_marshal(out["Data/Tilesets.rxdata"],"F10C_TILES")
            plain=conn.safe_cells(world,tiles,sym,allowed={0})
            points=conn.safe_cells(world,tiles,sym,allowed={0,2})
            if revision==1 or key not in EXTRA:points&=components[sym]
            else:points=trainers.component(points-occupied,xy)
            if xy not in plain or not safe_cell(points,xy,{(x,y) for m,x,y in reserved if m==mid},occupied):
                rejected.append({**row,"reason":"unsafe_or_reserved_cell"});continue
            _,_,index,_,reached,_=gates.access_graph(out,mapping,components,root,directional=True)
            label=index[mid].get(xy)
            if label is None or (mid,label) not in reached:
                rejected.append({**row,"reason":"no_existing_safe_access"});continue
            before=trainers.reached_cells(index,reached)-{(mid,*xy)}
            data=trainers.sprite(z,donor,base)
            provenance="EXACT_DONOR_OR_LOCAL_SHEET" if data else "PROJECT_AUTHORED_RESIDENT_NOT_DONOR"
            if not data:data=authored_sheet(role)
            event_id=max(events,default=0)+1
            # Reserve slots 1..6 for future F10B additions, independently of
            # current trainer count. Existing IDs are never reassigned.
            event_id=max(event_id,1000+eid)
            if event_id in events:raise ValueError("F10C_EVENT_ID_COLLISION")
            k="F10C_%d_%d"%key;sn="SNQA_"+k
            page=event_page(script='BlueSinnohF10C.talk("%s")'%k,sprite=sn)
            events[event_id]=ruby("RPG::Event",id=event_id,name=("SN_"+k).encode("ascii"),x=xy[0],y=xy[1],pages=[page])
            rel="Data/Map%03d.rxdata"%mid;trial=dict(out);trial[rel]=serialize(world,EVENT_CLASSES)
            try:
                _,_,after_index,_,after_reached,_=gates.access_graph(trial,mapping,components,root,directional=True)
                safe=before<=trainers.reached_cells(after_index,after_reached) and teleport.build(trial,mapping,components,root)==entries
            except ValueError:safe=False
            if not safe:
                del events[event_id];rejected.append({**row,"reason":"existing_access_or_spawn_changed"});continue
            out=trial;out["Graphics/Characters/"+sn+".png"]=data
            rows.append([k,[mid,event_id,messages]])
            accepted.append({**row,"key":k,"event_id":event_id,"role":role,"sprite_provenance":provenance,
                             "sprite_sha256":hashlib.sha256(data).hexdigest(),"dialogue_language":"pt-BR",
                             "dialogue_provenance":"PROJECT_AUTHORED_NOT_TRANSLATED_DONOR","message_count":len(messages)})
    template=(root/"scripts/regions/SinnohF10C.rb").read_text("utf-8")
    if template.count("__F10C_ROWS__")!=1:raise ValueError("F10C_TEMPLATE")
    plugin=template.replace("__F10C_ROWS__",json.dumps(rows,ensure_ascii=False)).encode("utf-8")
    return out,{"maps_audited":131,"source_candidates":len(queue),"accepted":accepted,"rejected":rejected,
                "new_npcs":len(accepted),"revision":revision,"native_verified":False,"source_scripts_executed":False,
                "source_dialogue_copied":False,"saves_accessed":False,"water_enabled":False},plugin
