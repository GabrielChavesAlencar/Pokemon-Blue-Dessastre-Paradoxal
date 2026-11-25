"""F12B2: all Windworks event pages, original access and PBS evidence.
Only sanitized metadata; no donor scripts, dialogue or asset publication.
No source execution, runtime install, grants, battle flags or save access.
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
import audit_sinnoh_expansion_f03 as f03
import sinnoh_connection_expansion as conn
import sinnoh_f10a_inventory as inventory
import sinnoh_f10b_trainers as trainers
import sinnoh_f12a_story_audit as story
import sinnoh_f12b_windworks as wind
import sinnoh_private_visual as pv

ROOT=Path(__file__).resolve().parents[2]
SOURCES={
    91:("dc05139df997cdbbb2d77ab13d844c5fb7865bbe94e4b873c47540cc2cc5ec04",7,[93]),
    94:("0624b353d4b1e0817b8b735714e314aa778a234c3dfe011b2ef60473543d9b2a",15,[93]),
    96:("d2c2c8dcf61a987908dd390a596766f814dee726aacb17e8b9aea4d9bb1bfabf",7,[97,98,131,132]),
    98:("42d4f8d816a6060826d267f88370634d487e3b7404f302ba661b02ce2e9d96ee",17,[96]),
    111:(wind.HASH,5,[])}
# Match exact known item tokens only, including conditional script parameters.
ITEMS=re.compile(rb"(?<![A-Za-z0-9_])(?:WORKS_?KEY|GALACTIC_?KEY|STORAGE_?KEY|HM0[1-8])(?![A-Za-z0-9_])",re.I)
ACTORS=re.compile(rb"(?<![A-Za-z0-9])(?:GALACTIC|MARS|JUPITER|SATURN|CYRUS)(?![A-Za-z0-9])",re.I)
BATTLE=re.compile(rb"\b(?:pbTrainerBattle(?:100)?|TrainerBattle\s*\.\s*start)\s*\(",re.I)
REWARD=re.compile(rb"\b(?:pbReceiveItem|pbItemBall|pbGiveItem|pbAddItem|pbStoreItem|pbHasItem|pbDeleteItem|pbRemoveItem)\s*\(",re.I)
TRANSFER=re.compile(rb"\b(?:pbTransferPlayer|pbWarp|reserve_transfer|transfer_player)\b|\$game_temp\s*\.\s*player_new_map_id",re.I)
PBS=re.compile(r"Sinnoh Maps/PBS/(?:trainers|trainer_types|trainertypes|items)(?:_[A-Za-z0-9_-]+)?\.txt",re.I)

def event_evidence(event,eid):
    a=event.attrs;pages=[];actor=set();item=set()
    for pi,p in enumerate(a["@pages"]):
        pa=p.attrs;script=[];codes=Counter()
        for ci,c in enumerate(pa["@list"]):
            ca=c.attrs;op=ca.get("@code")
            if type(op) is not int:raise ValueError("F12B2_INVALID_CODE")
            codes[op]+=1
            params=ca.get("@parameters",[])
            conditional=op==111 and len(params)>=2 and params[0]==12
            if op not in (355,655) and not conditional:continue
            for value in params:
                if not isinstance(value,bytes):continue
                actor.update(x.decode("ascii").upper() for x in ACTORS.findall(value))
                item.update(x.decode("ascii").upper().replace("_","") for x in ITEMS.findall(value))
                script.append({"command_index":ci,"code":op,"sha256":hashlib.sha256(value).hexdigest(),
                    "battle_call_marker":bool(BATTLE.search(value)),"item_call_marker":bool(REWARD.search(value)),
                    "transfer_call_marker":bool(TRANSFER.search(value))})
        pages.append({"page_index":pi,"codes":dict(sorted(codes.items())),
                      "shape":conn.event_shape(event)[pi],"script_parameters":script})
    literal,reason=trainers.literal_identity(event)
    known_mars=literal is not None and literal[1].casefold()=="mars"
    return {"event_id":eid,"position":[a["@x"],a["@y"]],"pages":pages,
            "markers":story.markers(event),"script_actor_markers":sorted(actor),"script_item_markers":sorted(item),
            "literal_mars_identity":known_mars,"literal_identity_status":"recognized_mars_candidate" if known_mars else reason or "other_identity",
            "source_transfer_targets":sorted(conn.static_targets({eid:event})),"binding_approved":False}

def pbs_evidence(z):
    result=[]
    for name in sorted(f03.index(z).values()):
        if not PBS.fullmatch(name):continue
        raw=pv.member(z,name)
        lines=raw.splitlines()
        result.append({"file":name.rsplit("/",1)[-1],"sha256":hashlib.sha256(raw).hexdigest(),
            "mars_marker_lines":sum(bool(re.search(rb"(?<![A-Za-z0-9])MARS(?![A-Za-z0-9])",v,re.I)) for v in lines),
            "works_key_marker_lines":sum(bool(re.search(rb"(?<![A-Za-z0-9_])WORKS_?KEY(?![A-Za-z0-9_])",v,re.I)) for v in lines)})
    return result

def audit(blobs,mapping,path,root=ROOT):
    if len(mapping)!=139 or set(mapping)!=wind.gym.GYM_SETS[7]:raise ValueError("F12B2_BASELINE")
    before={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}
    rows=[];incoming=[];target_events=[]
    with pv.verified_archive(path,"maps") as z:
        ix=f03.index(z)
        for name in sorted(ix.values()):
            if not name.startswith(pv.MAP_ROOT+"Data/"):continue
            m=f03.MAP_RE.fullmatch(name[len(pv.MAP_ROOT+"Data/"):])
            if not m:continue
            sid=int(m[1]);raw=pv.member(z,name);digest=hashlib.sha256(raw).hexdigest()
            events=conn.read_marshal(raw,"F12B2_SOURCE").attrs["@events"]
            targets=sorted(conn.static_targets(events))
            if 111 in targets:incoming.extend({"source_id":sid,"event_id":eid} for eid,e in events.items() if 111 in conn.static_targets({eid:e}))
            if sid not in SOURCES:continue
            expected,n,dest=SOURCES[sid]
            if (digest,len(events),targets)!=(expected,n,dest):raise ValueError("F12B2_SOURCE_CHANGED:"+str(sid))
            if sid==111:target_events=[event_evidence(e,eid) for eid,e in sorted(events.items())]
            rows.append({"source_id":sid,"source_sha256":digest,"event_count":n,"static_targets":targets})
        if {r["source_id"] for r in rows}!=set(SOURCES) or len(target_events)!=5:raise ValueError("F12B2_SOURCE_INCOMPLETE")
        seams=pv.parse_connections(pv.member(z,pv.MAP_ROOT+"PBS/map_connections.txt"))
        pbs=pbs_evidence(z)
    relevant=[list(r) for r in seams if 111 in (r[0],r[3])]
    if before!={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}:raise ValueError("F12B2_BASELINE_MUTATED")
    return {"status":"EVIDENCE_ONLY","baseline_maps":139,"windworks_events":target_events,
        "nearby_source_maps":rows,"incoming_static_transfers":incoming,"windworks_source_seams":relevant,
        "source_pbs_files":pbs,"mars_literal_candidates":[r["event_id"] for r in target_events if r["literal_mars_identity"]],
        "works_key_script_candidates":[r["event_id"] for r in target_events if "WORKSKEY" in r["script_item_markers"]],
        "native_bindings":0,"new_portals":0,"items_granted":0,"native_verified":False,
        "baseline_preserved":True,"saves_accessed":False}
