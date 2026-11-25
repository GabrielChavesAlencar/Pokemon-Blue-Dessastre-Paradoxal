"""Install an explicitly authored, condensed private Galactic QA quest.
Mars is challenged in the exterior until an authored interior is reviewed.
Existing Meadow events, terrain, map IDs and portals are preserved; append
only three action NPCs there. Do not claim an original donor reconstruction.
"""
import hashlib
import json
import re
from pathlib import Path
import sinnoh_f12b4_windworks_access as access
import sinnoh_f12b2_windworks_evidence as source
import sinnoh_f10b_trainers as trainers
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10c_npcs as npc
import sinnoh_f11a_gym as gym
import sinnoh_qa_teleport as tp
import sinnoh_connection_expansion as conn
import sinnoh_private_visual as pv
from build_johto_events import EVENT_CLASSES,ruby,event_page

ROOT=Path(__file__).resolve().parents[2]
MEADOW="SINNOH_FLOAROMA_MEADOW"
ORDER=("WINDWORKS_GUARD","MEADOW_GRUNT_1","MEADOW_GRUNT_2","WORKS_KEY","MARS")
GRUNTS=("GALACTIC_GRUNT","GALACTICGRUNT","GALACTIC","GALACTIC_M","TEAMGALACTIC","TEAMGALACTIC_M","GALACTICGRUNT_M")
COMMANDERS=("COMMANDER_MARS","GALACTIC_MARS","GALACTIC_ADMIN","GALACTICADMIN","ADMIN_MARS","MARS","BLUE_SINNOH_BOSS_MARS")
KEYS=("WORKSKEY","WORKS_KEY")
PICKUP=re.compile(rb"\A\s*(?:Kernel\.)?pbItemBall\s*\(\s*(?:(?::|PBItems::)([A-Z][A-Z0-9_]*)|([0-9]+))\s*(?:,\s*([0-9]+))?\s*\)\s*\Z",re.I)

def pickup_candidates(path):
    result=[]
    with pv.verified_archive(path,"maps") as z:
        raw=pv.member(z,pv.MAP_ROOT+"Data/Map111.rxdata")
        if hashlib.sha256(raw).hexdigest()!=access.wind.HASH:raise ValueError("F12B5_PICKUP_SOURCE_HASH")
        events=conn.read_marshal(raw,"F12B5_PICKUP_SOURCE").attrs["@events"]
        for eid in (2,3,4,5):
            event=events[eid];matches=[]
            for p in event.attrs["@pages"]:
                for c in p.attrs["@list"]:
                    a=c.attrs;args=a.get("@parameters",[])
                    if a.get("@code")!=111 or len(args)!=2 or args[0]!=12 or not isinstance(args[1],bytes):continue
                    m=PICKUP.fullmatch(args[1])
                    if m:
                        matches.append({"symbol":m[1].decode("ascii").upper() if m[1] else None,
                            "legacy_numeric_id":int(m[2]) if m[2] else None,
                            "quantity":int(m[3]) if m[3] else 1,
                            "script_sha256":hashlib.sha256(args[1]).hexdigest()})
            result.append({"event_id":eid,"position":[event.attrs["@x"],event.attrs["@y"]],
                           "literal_candidates":matches,"grant_enabled":False,
                           "reason":"local_item_identity_and_acquisition_semantics_pending"})
    return result

def choose(catalog,aliases):
    values=[a for a in aliases if a in catalog]
    return values[0] if len(values)==1 else None

def contract(root):
    d=json.loads((root/"data/regions/sinnoh-f12b5-authored-quest.json").read_text("utf-8"))
    seq=d["sequence"]
    expected=([["GLAMEOW",13]],[["STUNKY",13]],[["ZUBAT",11],["ZUBAT",11]],None,[["ZUBAT",15],["PURUGLY",17]])
    if tuple(x["id"] for x in seq)!=ORDER or tuple(x.get("team") for x in seq)!=expected or tuple(x["area"] for x in seq)!=(access.SYMBOL,MEADOW,MEADOW,MEADOW,access.SYMBOL):
        raise ValueError("F12B5_REFERENCE_CONTRACT_CHANGED")
    return seq

def build(blobs,mapping,components,types,species,items,existing,root=ROOT):
    def blocked(reason):
        return blobs,{"status":"AUTHORED_QUEST_BLOCKED","reason":reason,"new_events":0,"native_bindings":0,"items_granted":0,"native_verified":False},b""
    if set(mapping)!=access.ALL:return blocked("windworks_exploration_not_prepared")
    seq=contract(root)
    grunt=choose(types,GRUNTS);mars=choose(types,COMMANDERS);key=choose(items,KEYS)
    if not grunt or not mars or grunt==mars or not key:return blocked("local_trainer_types_or_works_key_missing_or_ambiguous")
    if any(s not in species for row in seq for s,l in row.get("team",[])):return blocked("local_species_missing")
    specs={}
    for i,row in enumerate(seq):
        k=row["id"];mid=mapping[row["area"]]
        if k=="WORKS_KEY":specs[k]=[None,None,None,mid,[]];continue
        identity=(mars if k=="MARS" else grunt,"Mars" if k=="MARS" else "Grunt",12001+i)
        if identity in existing:return blocked("trainer_pbs_collision")
        specs[k]=[*identity,mid,row["team"]]
    out=dict(blobs);locations=[];original_entries=tp.build(blobs,mapping,components,root)
    _,_,idx,_,reach,_=gates.access_graph(blobs,mapping,components,root,directional=True)
    old_reached=trainers.reached_cells(idx,reach)
    positions=set()
    for row in seq:
        k=row["id"];sym=row["area"];mid=mapping[sym];rel="Data/Map%03d.rxdata"%mid
        role="galactic_mars" if k=="MARS" else "galactic_honey_man" if k=="WORKS_KEY" else "galactic_grunt"
        sprite="SNQA_F12B5_"+role.upper()
        accepted=False
        for world,xy,land in gym.city_entrance(out,mapping,components,root,sym):
            ev=world.attrs["@events"];eid=max(max(ev,default=0)+1,3001)
            ev[eid]=ruby("RPG::Event",id=eid,name=("SN_F12B5_"+k).encode("ascii"),
                         x=xy[0],y=xy[1],pages=[event_page(script='BlueSinnohF12B5.interact("'+k+'")',sprite=sprite)])
            trial=dict(out);trial[rel]=conn.serialize(world,EVENT_CLASSES)
            try:
                if tp.build(trial,mapping,components,root)!=original_entries:continue
                _,_,post,_,reached,_=gates.access_graph(trial,mapping,components,root,directional=True)
                if not (old_reached-positions-{(mid,*xy)})<=trainers.reached_cells(post,reached):continue
            except ValueError:continue
            finally:
                del ev[eid]
            out=trial;positions.add((mid,*xy));locations.append({"id":k,"map_id":mid,"event_id":eid,"position":list(xy),
                "source":"PROJECT_AUTHORED_CONDENSED_QA"})
            out["Graphics/Characters/"+sprite+".png"]=npc.authored_sheet(role)
            accepted=True;break
        if not accepted:return blocked("no_safe_additive_event_position:"+k)
    # All existing serialized event data and all non-event map attributes
    # remain identical when the new events are removed.
    changed={mapping[MEADOW],mapping[access.SYMBOL]}
    for mid in mapping.values():
        rel="Data/Map%03d.rxdata"%mid
        if mid not in changed:
            if out[rel]!=blobs[rel]:raise ValueError("F12B5_PRIOR_MAP_CHANGED")
            continue
        prior=conn.read_marshal(blobs[rel],"F12B5_PRIOR")
        current=conn.read_marshal(out[rel],"F12B5_NEW")
        for loc in locations:
            if loc["map_id"]==mid:del current.attrs["@events"][loc["event_id"]]
        if conn.serialize(prior,EVENT_CLASSES)!=conn.serialize(current,EVENT_CLASSES):
            raise ValueError("F12B5_EXISTING_MAP_CONTENT_CHANGED")
    pbs="PBS/trainers_sinnoh_f12b5.txt"
    if pbs in out:return blocked("authored_pbs_path_collision")
    out[pbs]="".join("\n[%s,%s,%d]\nLoseText = Voce venceu!\n"%(s[0],s[1],s[2])+
                  "".join("Pokemon = %s,%d\n"%(mon,lv) for mon,lv in s[4])
                  for s in specs.values() if s[0]).encode("ascii")
    template=(root/"scripts/regions/SinnohF12B5.rb").read_text("utf-8")
    if template.count("__F12B5_SPECS__")!=1 or template.count("__F12B5_KEY__")!=1:raise ValueError("F12B5_TEMPLATE")
    plugin=template.replace("__F12B5_SPECS__",json.dumps(specs,ensure_ascii=True).replace("null","nil")).replace("__F12B5_KEY__",json.dumps(key)).encode("utf-8")
    return out,{"status":"AUTHORED_QUEST_PREPARED","new_events":5,"native_bindings":0,"items_granted":0,
         "candidate_runtime_handlers":5,"native_verified":False,"placements":locations,"teams":{k:s[4] for k,s in specs.items() if s[0]},
         "local_key_id":key,"source_layout":"PROJECT_AUTHORED_CONDENSED_EXTERIOR_MARS",
         "source_pbs_present":False,"official_story_flags_written":False,"existing_map_content_preserved":True,
         "new_portals":0},plugin

def append(blobs,mapping,components,base,root=ROOT):
    if set(mapping)!=access.ALL:return build(blobs,mapping,components,(),(),(),set(),root)
    existing=set()
    for p in (base/"PBS").glob("trainers*.txt"):
        if p.is_symlink():raise ValueError("F12B5_UNSAFE_PBS")
        for header in trainers.read_blocks(p):
            v=[s.strip() for s in header.split(",")]
            if len(v) in (2,3) and (len(v)==2 or v[2].isdigit()):existing.add((v[0],v[1],int(v[2]) if len(v)==3 else 0))
    # Item PBS must be locally present; this never fabricates a database entry.
    if not (base/"PBS/items.txt").is_file():return build(blobs,mapping,components,(),(),(),existing,root)
    return build(blobs,mapping,components,trainers.catalogue(base,"trainer_types"),trainers.catalogue(base,"pokemon"),trainers.catalogue(base,"items"),existing,root)
