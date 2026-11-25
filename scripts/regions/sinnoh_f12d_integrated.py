"""Integrated F12D3J-D6 private gameplay compiler; never modifies input maps."""
import json
import hashlib
import re
import zlib
import struct
import sinnoh_f12d_corridor as corridor
import sinnoh_private_visual as pv
import sinnoh_f12d_assets as assets
import sinnoh_f12d3_secretpotion_catalogue as item_catalogue
import sinnoh_f12d3_secretpotion_audit as secret_audit
import sinnoh_f12d3_expanded_evidence as expanded_audit
import sinnoh_f12d3_original_network as original_audit
import sinnoh_f12d3_canonical_network as canonical
import sinnoh_f12d_pastoria_preview as chase
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10b_trainers as trainers
import sinnoh_connection_expansion as conn
import sinnoh_qa_teleport as tp
import sinnoh_f12b5_authored_quest as mars
import sinnoh_f12d3_gated_alignment as gated
from build_johto_events import EVENT_CLASSES,ruby,event_page

ORDER=("VALOR","VERITY","ACUITY")
# Condensed project-authored teams, not claimed as imported source teams.
LAKES={
    "VALOR":("SINNOH_VALOR_CAVERN","Saturn",("COMMANDER_SATURN","GALACTIC_SATURN","GALACTIC_ADMIN","GALACTICADMIN","SATURN"),15001,(("GOLBAT",38),("BRONZOR",38),("TOXICROAK",40))),
    "VERITY":("SINNOH_LAKE_VERITY","Mars",mars.COMMANDERS,15002,(("GOLBAT",38),("BRONZOR",38),("PURUGLY",40))),
    "ACUITY":("SINNOH_LAKE_ACUITY","Jupiter",(),15003,()),
}
def graph(data,mapping,components,root,seed,rock=(),valor_rock=()):
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    w,t,i,_,r,_=gates.access_graph(data,old,components,root,seed_cells=[seed],directional=True,strict_movement=True,rock_cells=rock,valor_rock=valor_rock)
    return w,t,trainers.reached_cells(i,r)

def add_event(data,mid,xy,key,sprite,cleared=False):
    rel="Data/Map%03d.rxdata"%mid
    world=conn.read_marshal(data[rel],"F12D_INTEGRATED_EVENT")
    events=world.attrs["@events"]
    if any((e.attrs["@x"],e.attrs["@y"])==xy for e in events.values()):raise ValueError("F12D_INTEGRATED_OCCUPIED")
    eid=max(max(events,default=0)+1,3001)
    page=event_page(script='BlueSinnohF12DIntegrated.interact("'+key+'")',sprite=sprite)
    pages=[page]
    if cleared:
        off=event_page(script="nil")
        off.attrs["@through"]=True
        off.attrs["@condition"].attrs["@self_switch_valid"]=True
        pages.append(off)
    events[eid]=ruby("RPG::Event",id=eid,name=("SN_F12D_INTEGRATED_"+key).encode("ascii"),x=xy[0],y=xy[1],pages=pages)
    out=dict(data);out[rel]=conn.serialize(world,EVENT_CLASSES)
    del events[eid]
    if conn.serialize(world,EVENT_CLASSES)!=data[rel]:raise ValueError("F12D_INTEGRATED_EVENT_DELTA")
    return out,{"map_id":mid,"event_id":eid,"position":list(xy)}

def protected(data,mapping,components,root):
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    result={tuple(r[3]) for r in tp.build(data,old,components,root) if r[3]}
    for mid in mapping.values():
        w=conn.read_marshal(data["Data/Map%03d.rxdata"%mid],"F12D_INTEGRATED_PROTECT")
        for e in w.attrs["@events"].values():
            a=e.attrs;result.add((mid,a["@x"],a["@y"]))
            tr,_=conn.classify_transfer(e)
            if tr:result.add((tr[2],tr[3],tr[4]))
    return result

def placement(data,mapping,components,root,mid,seed,rock=(),valor_rock=()):
    worlds,tiles,reached=graph(data,mapping,components,root,seed,rock,valor_rock)
    if mid not in worlds:return None
    world=worlds[mid];w,h=world.attrs["@width"],world.attrs["@height"]
    forbid=protected(data,mapping,components,root)|{seed}
    candidates={(x,y) for m,x,y in reached if m==mid and 1<x<w-2 and 1<y<h-2 and
        (m,x,y) not in forbid and (gates.cell_shape(world,tiles,(x,y))["ordinary_walkable"] or (m,x,y) in valor_rock)}
    for xy in sorted(candidates,key=lambda q:(abs(q[0]-w//2)+abs(q[1]-h//2),q)):
        stands=[q for q in tp.neighbours(*xy) if (mid,*q) in reached and (mid,*q) not in forbid]
        if not stands:continue
        trial,loc=add_event(data,mid,xy,"PLACEMENT_PROBE","")
        _,_,after=graph(trial,mapping,components,root,seed,rock,valor_rock)
        if reached-{(mid,*xy)}<=after:
            for q in sorted(stands):
                if (mid,*q) in after:return xy,q
    return None

def valor_rock_reference(blobs,mapping,source):
    """Pinned source 217 only; matching local Rock stacks, never conversion."""
    mid=mapping["SINNOH_VALOR_CAVERN"]
    world=conn.read_marshal(blobs["Data/Map%03d.rxdata"%mid],"F12D_VALOR_QA")
    tiles=conn.read_marshal(blobs["Data/Tilesets.rxdata"],"F12D_VALOR_TILES")
    with pv.verified_archive(source,"maps") as z:
        raw=pv.member(z,pv.MAP_ROOT+"Data/Map217.rxdata")
        if hashlib.sha256(raw).hexdigest()!="e7d80aa507ee7112ccf301d5cc441ad8184a50054a7cca5dcc027dd544cc35b6":
            raise ValueError("F12D_VALOR_SOURCE_HASH")
        src=conn.read_marshal(raw,"F12D_VALOR_SOURCE")
        st=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/Tilesets.rxdata"),"F12D_VALOR_SOURCE_TILES")
    ss,sh=corridor.grid(src,st);qs,qh=corridor.grid(world,tiles)
    if set(ss)!=set(qs):raise ValueError("F12D_VALOR_DIMENSIONS")
    w,h=world.attrs["@width"],world.attrs["@height"]
    guard=pv.movement_masks(blobs,mapping,extra_symbols={"SINNOH_VALOR_CAVERN"})[mid]
    def zero_priority(a,ts,stack):
        data=ts[a.attrs["@tileset_id"]].attrs["@priorities"].data
        return all(struct.unpack_from("<H",data,20+2*k)[0]==0 for k in stack if k)
    return {(mid,x,y):qs[x,y] for x,y in qs if 0<x<w-1 and 0<y<h-1 and
        sh[x,y]==qh[x,y] and 4 in qh[x,y][1] and all(k in (0,4) for k in qh[x,y][1])
        and all(k==0 for k in qh[x,y][0]) and guard[y][x]=="." and
        zero_priority(src,st,ss[x,y]) and zero_priority(world,tiles,qs[x,y])}

def lake_contract(key,types,species,existing):
    symbol,name,aliases,version,team=LAKES[key]
    if not team:return {"symbol":symbol,"name":name,"team":[],"kind":"scene"}
    kind=mars.choose(types,aliases)
    if not kind or any(s not in species for s,l in team) or (kind,name,version) in existing:return None
    return {"symbol":symbol,"name":name,"type":kind,"version":version,"team":[list(p) for p in team],"kind":"battle"}

def ruby_hash(mapping):
    return "{"+",".join(json.dumps(k)+"=>"+json.dumps(v) for k,v in sorted(mapping.items()))+"}"

def compile_story(blobs,mapping,components,cr,expanded,original,source,root,types,species,items,existing):
    chase.validate(blobs,mapping);before=chase.digest(blobs)
    prepared={}
    report=canonical.inspect(blobs,mapping,components,cr,expanded,original,source,root,
        directional_repair=True,rock_repair=True,rock_network=True,integrated_payload=prepared)
    sprites=assets.build()
    result={"geometry":report,"status":"F12D_INTEGRATED_BLOCKED","mission_prepared":False,
        "authored_sprite_hashes":{k:hashlib.sha256(v).hexdigest() for k,v in sprites.items()},
        "lake_contracts":{k:lake_contract(k,types,species,existing) for k in ORDER},
        "lake_placements":{},"lake_local_previews":{},"runtime_install_enabled":False,"native_verified":False,"new_maps":0,"new_portals":0}
    origin=cr["placements"][-1];seed=(origin["map_id"],*origin["stand"])
    # Compile local lake event previews independently. QA entry seeds
    # are local placement evidence, not proof of progression travel.
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    entries=tp.build(blobs,old,components,root)
    valor_rock=valor_rock_reference(blobs,mapping,source)
    result["valor_rock_reference_cells"]=len(valor_rock)
    for key in ORDER:
        contract=result["lake_contracts"][key]
        if not contract or contract["symbol"] not in mapping:continue
        mid=mapping[contract["symbol"]]
        local_seed=next((tuple(r[3]) for r in entries if r[3] and r[3][0]==mid),None)
        if local_seed:
            local=placement(blobs,mapping,components,root,mid,local_seed,valor_rock=valor_rock)
            if local:
                preview,loc=add_event(blobs,mid,local[0],key,"SNQA_F12D_"+key)
                loc.update(stand=list(local[1]),qa_seed=list(local_seed),walk_from_predecessor_proved=False,
                    candidate_map_sha256=hashlib.sha256(preview["Data/Map%03d.rxdata"%mid]).hexdigest())
                result["lake_local_previews"][key]=loc
        pos=placement(blobs,mapping,components,root,mid,seed,valor_rock=valor_rock)
        if pos:result["lake_placements"][key]={"map_id":mid,"position":list(pos[0]),"stand":list(pos[1]),"from_chase_only":True}
    if not prepared:
        result["reason"]="geometry_or_four_cell_cut_unproved";return {},result,b""
    if "SECRETPOTION" not in items:
        result["reason"]="local_secretpotion_catalog_missing";return {},result,b""
    opened=prepared["open_maps"];rock=prepared["rock_cells"];mid=prepared["cut_map_id"]
    value=placement(opened,mapping,components,root,origin["map_id"],seed,rock)
    if not value:result["reason"]="cynthia_no_noncut_position";return {},result,b""
    xy,stand=value
    out,loc=add_event(opened,origin["map_id"],xy,"CYNTHIA","SNQA_F12D_CYNTHIA")
    loc["stand"]=list(stand);locations={"CYNTHIA":loc};ducks=[]
    for i,xy in enumerate(prepared["cut_positions"],1):
        key="PSYDUCK_"+str(i)
        out,duck=add_event(out,mid,xy,key,"SNQA_F12D_PSYDUCK",cleared=True)
        locations[key]=duck;ducks.append(duck)
    _,_,baseline=graph(blobs,mapping,components,root,seed)
    _,_,closed=graph(out,mapping,components,root,seed,rock)
    town=mapping["SINNOH_CELESTIC_TOWN"];targets={(mid,*xy) for xy in prepared["exit_cells"]}
    removed={(loc["map_id"],*loc["position"])}
    if not (baseline-removed<=closed and not targets&closed and not any(p[0]==town for p in closed) and
            (loc["map_id"],*loc["stand"]) in closed and
            any((mid,*q) in closed for d in ducks for q in tp.neighbours(*d["position"]))):
        result["reason"]="final_mission_graph_failed";return {},result,b""
    reopened=dict(out);rel="Data/Map%03d.rxdata"%mid
    world=conn.read_marshal(reopened[rel],"F12D_INTEGRATED_REOPEN")
    for d in ducks:del world.attrs["@events"][d["event_id"]]
    reopened[rel]=conn.serialize(world,EVENT_CLASSES)
    _,_,restored=graph(reopened,mapping,components,root,seed,rock)
    if not targets<=restored or not any(p[0]==town for p in restored):
        result["reason"]="final_reopen_failed";return {},result,b""
    old={k:v for k,v in mapping.items() if k in chase.prior.ALL}
    if tp.build(out,old,components,root)!=tp.build(blobs,old,components,root):
        result["reason"]="qa_entries_changed";return {},result,b""
    specs={};pbs=[];lake_seed=(mid,*prepared["exit_cells"][0]);lake_ready=[]
    for key in ORDER:
        contract=result["lake_contracts"][key]
        if not contract or contract["symbol"] not in mapping:break
        lm=mapping[contract["symbol"]];pos=placement(reopened,mapping,components,root,lm,lake_seed,rock,valor_rock)
        if not pos:break
        xy,stand=pos;sprite="SNQA_F12D_"+key
        out,loc=add_event(out,lm,xy,key,sprite)
        reopened,_=add_event(reopened,lm,xy,key,sprite)
        loc["stand"]=list(stand);locations[key]=loc;lake_seed=(lm,*stand);lake_ready.append(key)
        if contract["kind"]=="battle":
            spec=[contract["type"],contract["name"],contract["version"],lm,contract["team"]]
            specs[key]=spec
            pbs.append("[%s,%s,%d]\nLoseText = Voce venceu!\n%s\n"%(spec[0],spec[1],spec[2],"\n".join("Pokemon = %s,%d"%tuple(p) for p in spec[4])))
        result["lake_placements"][key]=loc
    # Staging only until the private engine, sprites and pre-chase seam gate pass.
    template=(root/"scripts/regions/SinnohF12DIntegrated.rb").read_text("utf-8")
    literal={k:[v["map_id"],*v["position"],v["event_id"]] for k,v in locations.items()}
    worlds,_,index,_,_,_=gates.access_graph(opened,old,components,root,seed_cells=[seed],
        directional=True,strict_movement=True,rock_cells=rock)
    dims={m:(w.attrs["@width"],w.attrs["@height"]) for m,w in worlds.items()}
    def lane_keys(records):
        keys=[]
        for rec in records:
            for _,a,b in gated.all_lanes(rec,index,dims):
                left=[rec[0],*a];right=[rec[3],*b]
                keys.extend([left+right,right+left])
        return sorted(keys)
    edits=sorted([row["map_id"],*row["position"]] for row in prepared["edits"])
    chase_lanes=lane_keys(prepared["connections"]);celestic_lanes=lane_keys([prepared["exit_record"]])
    template=template.replace("__LOCATIONS__",ruby_hash(literal)).replace("__SPECS__",ruby_hash(specs))
    for key,value in (("__EDIT_CELLS__",edits),("__CHASE_LANES__",chase_lanes),("__CELESTIC_LANES__",celestic_lanes)):
        if template.count(key)!=1:raise ValueError("F12D_INTEGRATED_GATE_TEMPLATE")
        template=template.replace(key,json.dumps(value))
    result["progression_gate"]={"edited_cells":len(edits),"chase_directional_lanes":len(chase_lanes),
        "celestic_directional_lanes":len(celestic_lanes),"runtime_verified":False}
    plugin=(root/"scripts/regions/SinnohF12D3Transaction.rb").read_bytes()+b"\n"+template.encode("utf-8")
    if pbs:
        name="PBS/trainers_sinnoh_f12d_integrated.txt"
        if name in blobs:raise ValueError("F12D_INTEGRATED_PBS_COLLISION")
        out[name]=("\n"+"\n".join(pbs)).encode("ascii")
    if chase.digest(blobs)!=before:raise ValueError("F12D_INTEGRATED_INPUT_CHANGED")
    if set(sprites)&set(blobs):raise ValueError("F12D_INTEGRATED_SPRITE_COLLISION")
    out.update(sprites)
    delta={k:v for k,v in out.items() if blobs.get(k)!=v}
    result.update(status="F12D_INTEGRATED_GAMEPLAY_FIXTURE",mission_prepared=True,locations=locations,
        lake_payloads=lake_ready,new_events=len(locations),geometry_delta_count=len(prepared["edits"]),
        closed_cells=len(closed),reopened_cells=len(restored),requires_local_engine=True,
        requires_pre_chase_seam_gate=True,reason="local_engine_and_progression_activation_pending",
        payload_hashes={k:hashlib.sha256(v).hexdigest() for k,v in delta.items()})
    return delta,result,plugin

# Read-only local engine reference comparison. A matching script blob is NOT
# proof that plugins have not overridden it, or that native movement works.
ENGINE_REFS={
    "terrain_tag":"52ec76c28f718f6fc98a34e5069f28ea3275445c",
    "game_map":"3fda78303080bf7be450d110ecaf9df834bec691",
    "game_character":"d7f33659c6627b2bf08fff4e61d43886c76d7b6c",
    "game_player":"6c03a8b19c35d75163283c6121c062bf78ffd9c5",
}
def git_blob_id(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()

PLAYER_METHOD_REFS={"passable?":"977b23fd76fe77c4e1354afdd16c91a83503ec69","move_generic":"7f8264d1f61a9c5d39560e71ce5c979e1f3baf74","turn_generic":"1af790fbb2dc434267b0d65213733df9d784bb2f","jump":"e50b4e66179b41222ff406811078df8b988c9318","pbTerrainTag":"fc0c1f63f8766e8397276e0dd16ffef8def34cda","pbFacingTerrainTag":"affd58d712dc601b572ca564491aee86b69d176d","map":"18b03922821628a5827127991217889aae678de1","map_id":"e7520df7bf974bc7e29106a9f8090581fbe8227f","moveto":"4e353355950f307ae0cafc272545fa61eb24043d","update":"782cd09f1cc6d4d08e204082e1bbb1955893b293","update_command_new":"93431966887129b10736486956bb062b56a6217d","update_move":"26db92af0cdd30dd91be314ae44e5abd04fb7bf8","update_stop":"5ff90a8a99cc761065227f218abf3e254f208aeb","update_event_triggering":"00efca900d69a4d834e2378d2897866eb7c08e05"}
def player_method_receipt(raw,expected=PLAYER_METHOD_REFS):
    lines=raw.replace(b"\r\n",b"\n").split(b"\n")
    result={}
    for name,digest in expected.items():
        prefix=b"  def "+name.encode("ascii")
        starts=[i for i,line in enumerate(lines) if line==prefix or line.startswith(prefix+b"(")]
        if len(starts)!=1:result[name]="missing_or_duplicate";continue
        start=starts[0]
        end=next((i for i in range(start+1,len(lines)) if lines[i]==b"  end"),None)
        result[name]="match" if end is not None and hashlib.sha1(b"\n".join(lines[start:end+1])).hexdigest()==digest else "different"
    return result

def engine_reference_rows(rows,expected=ENGINE_REFS):
    found={k:0 for k in expected};player_rows=[]
    for row in rows:
        if not isinstance(row,list) or len(row)<3 or not isinstance(row[2],bytes):
            raise ValueError("F12D_ENGINE_SCRIPT_SHAPE")
        raw=zlib.decompress(row[2])
        if re.search(rb"(?m)^class Game_Player\b",raw):player_rows.append(raw)
        digests={git_blob_id(raw),git_blob_id(raw.replace(b"\r\n",b"\n"))}
        for k,v in expected.items():
            if v in digests:found[k]+=1
    return {"reference":"Essentials v21.1","matched_scripts":found,
        "game_player_script_count":len(player_rows),"game_player_methods":player_method_receipt(player_rows[0]) if len(player_rows)==1 else {},
        "reference_match":all(n==1 for n in found.values()),"local_engine_native_verified":False,
        "plugin_overrides_verified":False,"source_scripts_executed":False}

def local_engine(base):
    path=base/"Data/Scripts.rxdata"
    try:
        if path.is_symlink() or not path.is_file():raise ValueError("F12D_ENGINE_MISSING")
        return engine_reference_rows(conn.read_marshal(path.read_bytes(),"F12D_ENGINE_REFERENCE"))
    except (OSError,ValueError,TypeError,KeyError,zlib.error) as exc:
        return {"reference":"Essentials v21.1","reference_match":False,
            "local_engine_native_verified":False,"plugin_overrides_verified":False,
            "source_scripts_executed":False,"reason":type(exc).__name__}

def installer_preflight(blobs,mapping,components,cr,base,root,source):
    """Called by the isolated installer after F12D2. Only stage bytes, never
    publish an unproved corridor or mutate an existing save. The next native
    binding must use the exact proof and validate the runtime movement hooks."""
    result={"status":"F12D_INTEGRATED_INSTALLER_PREFLIGHT","runtime_install_enabled":False,
        "native_verified":False,"candidate_ready":False,"new_maps":0,"new_portals":0,
        "engine":local_engine(base),"item_catalogue":item_catalogue.audit(base)}
    try:
        if not secret_audit.chase_prepared(cr):raise ValueError("F12D_INTEGRATED_REQUIRES_CHASE")
        existing=set()
        for path in (base/"PBS").glob("trainers*.txt"):
            if path.is_symlink() or not path.is_file():raise ValueError("F12D_INTEGRATED_UNSAFE_PBS")
            for header in trainers.read_blocks(path):
                v=[x.strip() for x in header.split(",")]
                if len(v) in (2,3) and (len(v)==2 or v[2].isdigit()):
                    existing.add((v[0],v[1],int(v[2]) if len(v)==3 else 0))
        for path,raw in blobs.items():
            if path.startswith("PBS/trainers") and path.endswith(".txt"):
                for header in re.findall(r"^\s*\[([^\]]+)\]\s*$",raw.decode("utf-8-sig"),re.M):
                    v=[x.strip() for x in header.split(",")]
                    if len(v) in (2,3) and (len(v)==2 or v[2].isdigit()):
                        existing.add((v[0],v[1],int(v[2]) if len(v)==3 else 0))
        if any((base/path).exists() for path in assets.build()):raise ValueError("F12D_INTEGRATED_LOCAL_SPRITE_COLLISION")
        item_delta,item_report=item_catalogue.prepare_missing(base,blobs)
        result["item_catalogue"]=item_report
        audited=secret_audit.audit(blobs,mapping,components,cr,source,root)
        expanded=expanded_audit.inspect(blobs,mapping,components,cr,audited,source,root)
        original=original_audit.inspect(blobs,mapping,components,cr,expanded,source,root)
        delta,story,plugin=compile_story(blobs,mapping,components,cr,expanded,original,source,root,
            trainers.catalogue(base,"trainer_types"),trainers.catalogue(base,"pokemon"),
            {"SECRETPOTION"} if item_report["local_catalog_valid"] or item_delta else set(),existing)
        # Do not embed private map bytes or huge path reports in the manifest.
        result.update(story_status=story["status"],mission_prepared=story["mission_prepared"],
            lake_local_previews=story.get("lake_local_previews",{}),lake_payloads=story.get("lake_payloads",[]),
            reason=story.get("reason"),candidate_ready=bool(delta and plugin),
            payload_hashes=story.get("payload_hashes",{}),authored_sprite_hashes=story["authored_sprite_hashes"])
        if delta and plugin:
            delta.update(item_delta)
            result["payload_hashes"]={k:hashlib.sha256(v).hexdigest() for k,v in delta.items()}
            result["candidate_plugin_sha256"]=hashlib.sha256(plugin).hexdigest()
            result["reason"]="runtime_movement_binding_and_native_compatibility_pending"
        return result
    except (OSError,ValueError,TypeError,KeyError,UnicodeError) as exc:
        return {**result,"reason":"preflight_failed:"+type(exc).__name__}
