"""F12A: inert discovery of story and regional item candidates.
No donor execution, event copying, installation, reward or save access.
"""
from collections import Counter
import hashlib
import json
import re
from pathlib import Path
import audit_sinnoh_expansion_f03 as f03
import sinnoh_connection_expansion as conn
import sinnoh_f08c_expansion as f08c
import sinnoh_f11a_gym as gym
import sinnoh_private_visual as pv

ROOT=Path(__file__).resolve().parents[2]
ACTORS=re.compile(rb"(?<![A-Za-z0-9])(?:TEAM[ _-]*GALACTIC|GALACTIC|MARS|JUPITER|SATURN|CYRUS|GIRATINA|DIALGA|PALKIA)(?![A-Za-z0-9])",re.I)
ITEMS=re.compile(rb"(?<![A-Za-z0-9_])(?:HM0[1-8]|WORKSKEY|GALACTICKEY|STORAGEKEY|SECRETKEY|OLDCHARM|SECRETPOTION|TOWNMAP|POKERADAR|OLDROD|GOODROD|SUPERROD|BICYCLE)(?![A-Za-z0-9_])",re.I)
ITEM_CALL=re.compile(rb"\b(?:pbReceiveItem|pbItemBall|pbGiveItem|pbAddItem)\s*\(\s*:([A-Za-z0-9_]+)",re.I)
AREA=re.compile(r"windworks|galactic|lake|spear pillar|distortion|veilstone|pastoria|eterna|coronet|celestic",re.I)

def markers(event):
    a=event.attrs
    actors=set();items=set();pickup=set();codes=Counter()
    fields=[a.get("@name")]
    for page in a.get("@pages",[]):
        p=page.attrs
        fields.append(getattr(p.get("@graphic"),"attrs",{}).get("@character_name"))
        for command in p.get("@list",[]):
            op=command.attrs;c=op.get("@code")
            if type(c) is not int:raise ValueError("F12A_INVALID_COMMAND")
            codes[c]+=1
            if c not in (355,655,101,401,108,408):continue
            for v in op.get("@parameters",[]):
                if not isinstance(v,bytes):continue
                fields.append(v)
                if c in (355,655):
                    pickup.update(x.decode("ascii").upper() for x in ITEM_CALL.findall(v) if ITEMS.fullmatch(x))
    for v in fields:
        if not isinstance(v,bytes):continue
        actors.update(re.sub(rb"[ _-]+",b"_",x.upper()).decode("ascii") for x in ACTORS.findall(v))
        items.update(x.decode("ascii").upper() for x in ITEMS.findall(v))
    return {"actors":sorted(actors),"item_markers":sorted(items),"literal_pickup_call_candidates":sorted(pickup),"command_codes":dict(sorted(codes.items()))}

def contract(root):
    story=json.loads((root/"data/regions/sinnoh-story-ch14-contract.json").read_text("utf-8"))
    galactic=json.loads((root/"data/regions/sinnoh-galactic-s19.json").read_text("utf-8"))
    hms=json.loads((root/"data/regions/sinnoh-hms-s16.json").read_text("utf-8"))
    steps=[s for s in story["steps"] if s["phase"] in (5,6,7,8)]
    if len(steps)!=14 or [s["id"] for s in steps[:5]]!=[s["id"] for s in galactic["steps"]]:raise ValueError("F12A_STORY_CONTRACT_CHANGED")
    if any(s["prerequisite_event"]!=(steps[i-1]["id"] if i else None) or s["native_event_installed"] or s["native_event_verified"] for i,s in enumerate(steps)):raise ValueError("F12A_STORY_ORDER_OR_NATIVE_STATE")
    if len(hms["hms"])!=8 or {s["hm_item"] for s in hms["hms"]}!={f"HM0{i}" for i in range(1,9)} or any(s["enabled"] for s in hms["hms"]):raise ValueError("F12A_HM_CONTRACT_CHANGED")
    return [{"id":s["id"],"prerequisite":s["prerequisite_event"],"badges":s["requires_local_badges"],"binding":None} for s in steps],[{"item":s["hm_item"],"badge":s["badge"],"action":s["action"],"binding":None} for s in hms["hms"]]

def audit(blobs,mapping,path,root=ROOT):
    if set(mapping)!=gym.GYM_SETS[7] or len(mapping)!=139 or len(set(mapping.values()))!=139:raise ValueError("F12A_REQUIRES_F11H_BASELINE")
    before={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}
    steps,hms=contract(root)
    source,_,_=conn.graph(root)
    source={**source,**{r["source_id"]:r for r in f08c.rows(root)}}
    if len(source)!=127 or any(r["symbol"] not in mapping for r in source.values()):raise ValueError("F12A_SOURCE_MAPPING")
    candidates=[];areas=[];scanned=0;events=0;seen=set()
    with pv.verified_archive(path,"maps") as z:
        ix=f03.index(z)
        infos=conn.read_marshal(pv.member(z,pv.MAP_ROOT+"Data/MapInfos.rxdata"),"F12A_INFOS")
        for name in sorted(ix.values()):
            if not name.startswith(pv.MAP_ROOT+"Data/"):continue
            match=f03.MAP_RE.fullmatch(name[len(pv.MAP_ROOT+"Data/"):])
            if not match:continue
            sid=int(match[1])
            if sid<=0 or sid in seen:raise ValueError("F12A_DUPLICATE_SOURCE_ID")
            seen.add(sid)
            raw=pv.member(z,name);digest=hashlib.sha256(raw).hexdigest()
            row=source.get(sid)
            if row and digest!=row["sha256"]:raise ValueError("F12A_SOURCE_HASH")
            a=conn.read_marshal(raw,"F12A_SOURCE").attrs
            scanned+=1
            mid=mapping[row["symbol"]] if row else None
            label=getattr(infos.get(sid),"attrs",{}).get("@name",b"")
            label=label.decode("utf-8",errors="replace") if isinstance(label,bytes) else ""
            if AREA.search(label):areas.append({"source_id":sid,"qa_map_id":mid,"source_sha256":digest})
            for eid,e in sorted(a["@events"].items()):
                if type(eid) is not int or eid<=0:raise ValueError("F12A_EVENT_ID")
                events+=1
                shape=markers(e)
                if not(shape["actors"] or shape["item_markers"]):continue
                x,y=e.attrs.get("@x"),e.attrs.get("@y")
                valid=type(x) is int and type(y) is int and 0<=x<a["@width"] and 0<=y<a["@height"]
                candidates.append({"source_id":sid,"source_event_id":eid,"source_sha256":digest,"qa_map_id":mid,"position":[x,y] if valid else None,**shape,"status":"CANDIDATE_NOT_BOUND","blockers":["identity_outcome_and_geometry_pending"]+([] if mid else ["map_not_mapped"])+([] if valid else ["invalid_coordinates"])})
    if not set(source)<=seen:raise ValueError("F12A_SOURCE_MAP_MISSING")
    if before!={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}:raise ValueError("F12A_BASELINE_MUTATED")
    return {"schema":1,"status":"SOURCE_CANDIDATES_ONLY","baseline_maps":len(mapping),"source_maps_scanned":scanned,"source_events_scanned":events,"source_area_candidates":areas,"event_candidates":candidates,"story_checkpoints":steps,"hm_contracts":hms,"candidate_events":len(candidates),"mapped_candidates":sum(r["qa_map_id"] is not None for r in candidates),"native_bindings":0,"items_granted":0,"new_maps":0,"new_portals":0,"baseline_preserved":True,"source_scripts_executed":False,"saves_accessed":False,"native_verified":False}
