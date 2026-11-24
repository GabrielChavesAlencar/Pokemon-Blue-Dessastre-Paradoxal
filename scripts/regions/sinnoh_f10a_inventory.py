"""F10A: inert source event and trainer PBS inventory for private Sinnoh QA.
No source script execution, event copying, map mutation or save access.
Only sanitized shapes, coordinates, hashes and counts leave the archive.
"""
from collections import Counter
import hashlib
import re
from pathlib import Path

import sinnoh_connection_expansion as conn
import sinnoh_f08c_expansion as f08c
import sinnoh_private_visual as pv

ROOT=Path(__file__).resolve().parents[2]
TRAINER_NAME=re.compile(rb"^(?:Trainer|TrainerSight)\s*\(",re.I)
BATTLE=re.compile(rb"\b(?:pbTrainerBattle(?:100)?|TrainerBattle\s*\.\s*start)\s*\(",re.I)
TRAINER_FILE=re.compile(r"Sinnoh Maps/PBS/trainers(?:_[A-Za-z0-9_-]+)?\.txt")
TEXT_CODES={0,101,401,108,408}

def classify(event):
    a=event.attrs
    pages=a.get("@pages",[])
    codes=Counter()
    sprite=False
    conditions=False
    moving=False
    action=False
    battle=False
    nested=False
    for page in pages:
        p=page.attrs
        c=getattr(p.get("@condition"),"attrs",{})
        conditions |= any(c.get("@"+k) is not False for k in ("switch1_valid","switch2_valid","variable_valid","self_switch_valid"))
        moving |= p.get("@move_type")!=0
        action |= p.get("@trigger")==0
        graphic=getattr(p.get("@graphic"),"attrs",{})
        sprite |= bool(graphic.get("@character_name"))
        for command in p.get("@list",[]):
            op=command.attrs;code=op.get("@code")
            if type(code) is not int:raise ValueError("F10A_INVALID_COMMAND")
            codes[code]+=1
            nested |= op.get("@indent")!=0
            if code in (355,655):
                battle |= any(isinstance(v,bytes) and BATTLE.search(v) is not None for v in op.get("@parameters",[]))
    name=a.get("@name",b"")
    trainer=battle or (isinstance(name,bytes) and TRAINER_NAME.search(name) is not None)
    if 201 in codes:kind="transfer_or_story"
    elif trainer:kind="trainer_candidate"
    elif (len(pages)==1 and action and not conditions and not moving and not nested and sprite
          and 101 in codes and set(codes)<=TEXT_CODES):kind="simple_dialogue_candidate"
    elif sprite:kind="other_sprite_event"
    else:kind="other_event"
    return {"kind":kind,"pages":len(pages),"codes":dict(sorted(codes.items())),
            "sprite":sprite,"conditions":conditions,"moving":moving,
            "battle_script_marker":battle,"trainer_name_marker":bool(trainer and not battle)}

def pbs_inventory(z):
    names=sorted(i.filename for i in z.infolist() if TRAINER_FILE.fullmatch(i.filename))
    result=[]
    for name in names:
        raw=pv.member(z,name)
        counts=Counter()
        for line in raw.decode("utf-8-sig",errors="replace").splitlines():
            line=line.split("#",1)[0].strip()
            if not line:continue
            if re.fullmatch(r"\[[^\[\]]+\]",line):
                counts["section_headers"]+=1
            elif re.match(r"^Pokemon\s*=",line,re.I):
                counts["pokemon_properties"]+=1
            elif "=" in line:counts["other_properties"]+=1
            else:counts["other_lines"]+=1
        result.append({"file":name.rsplit("/",1)[-1],"sha256":hashlib.sha256(raw).hexdigest(),
                       "shapes":dict(counts)})
    return result

def audit(blobs,mapping,masks,components,path,root=ROOT):
    if set(mapping)!=f08c.ALL or len(set(mapping.values()))!=131:
        raise ValueError("F10A_MAPIDS")
    source,_,_=conn.graph(root)
    source={**source,**{r["source_id"]:r for r in f08c.rows(root)}}
    if len(source)!=127 or len({r["symbol"] for r in source.values()})!=127:
        raise ValueError("F10A_SOURCE_MAPPING")
    totals=Counter();queue=[];maps=[]
    with pv.verified_archive(path,"maps") as z:
        pbs=pbs_inventory(z)
        for sid,row in sorted(source.items()):
            sym=row["symbol"];mid=mapping[sym]
            raw=pv.member(z,pv.MAP_ROOT+"Data/Map%03d.rxdata"%sid)
            if hashlib.sha256(raw).hexdigest()!=row["sha256"]:raise ValueError("F10A_SOURCE_MAP_HASH")
            old=conn.read_marshal(raw,"F10A_SOURCE").attrs
            target=conn.read_marshal(blobs["Data/Map%03d.rxdata"%mid],"F10A_QA").attrs
            occupied={(e.attrs["@x"],e.attrs["@y"]) for e in target["@events"].values()}
            if conn.static_targets(old["@events"])!=set(row["targets"]):raise ValueError("F10A_SOURCE_GRAPH")
            local=Counter()
            for eid,event in sorted(old["@events"].items()):
                if type(eid) is not int or eid<=0:raise ValueError("F10A_EVENT_ID")
                shape=classify(event);kind=shape["kind"];local[kind]+=1
                if kind not in ("trainer_candidate","simple_dialogue_candidate"):continue
                x,y=event.attrs.get("@x"),event.attrs.get("@y")
                grid=masks.get(mid,[])
                reasons=[]
                if sym in conn.city.OLD:reasons.append("protected_opening")
                if type(x) is not int or type(y) is not int or not (0<=y<len(grid) and 0<=x<len(grid[y])):
                    reasons.append("invalid_or_unmapped_coordinate")
                else:
                    if grid[y][x]!=".":reasons.append("not_plain_ground")
                    if (x,y) in occupied:reasons.append("existing_event_cell")
                    if (x,y) not in components.get(sym,set()):reasons.append("outside_known_component")
                if shape["moving"]:reasons.append("moving_event")
                if not shape["sprite"]:reasons.append("sprite_missing")
                # Even geometry candidates need explicit identity, sprite,
                # local PBS and blocking/route tests before any reconstruction.
                queue.append({"source_id":sid,"symbol":sym,"source_event_id":eid,
                              "qa_map_id":mid,"position":[x,y] if type(x) is int and type(y) is int else None,
                              **shape,"geometry_blockers":reasons,
                              "identity_and_runtime_pending":True})
            totals.update(local)
            maps.append({"source_id":sid,"symbol":sym,"qa_map_id":mid,
                         "source_events":sum(local.values()),"existing_qa_events":len(target["@events"]),
                         "categories":dict(local)})
    if sum(totals.values())!=sum(m["source_events"] for m in maps):
        raise ValueError("F10A_COUNT_MISMATCH")
    if len({(q["source_id"],q["source_event_id"]) for q in queue})!=len(queue):
        raise ValueError("F10A_DUPLICATE_CANDIDATE")
    return {"maps_audited":131,"source_maps_audited":127,
            "without_direct_source_event_mapping":sorted(set(mapping)-{r["symbol"] for r in source.values()}),
            "source_events":sum(totals.values()),"categories":dict(totals),
            "geometry_candidates":sum(not q["geometry_blockers"] for q in queue),
            "trainer_pbs_files":pbs,"maps":maps,"queue":queue,
            "new_trainers":0,"new_npcs":0,"native_verified":False,
            "source_scripts_executed":False,"saves_accessed":False}
