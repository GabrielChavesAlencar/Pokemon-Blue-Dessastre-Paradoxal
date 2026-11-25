"""F12B1: private in-memory Windworks geometry preview and evidence gate.
No runtime integration, story flags, item grants, fabricated connections,
donor event copying or saves. F12B remains incomplete if evidence is missing.
"""
import hashlib
import json
from pathlib import Path
import sinnoh_city_expansion as city
import sinnoh_connection_expansion as conn
import sinnoh_f11a_gym as gym
import sinnoh_private_visual as pv
import sinnoh_qa_teleport as teleport
import sinnoh_f12a_story_audit as story

ROOT=Path(__file__).resolve().parents[2]
SYMBOL="SINNOH_VALLEY_WINDWORKS"
HASH="62646bd742809cf4ad65760e812f58c34169933d2dc26a0128853609a8cf9dac"

def source_row(root):
    d=json.loads((root/"data/regions/sinnoh-f12b-windworks-source.json").read_text("utf-8"))
    rows=d["source_maps"]
    if d["schema"]!=1 or d["scope"]!="PRIVATE_QA_PREVIEW_ONLY" or len(rows)!=1:raise ValueError("F12B_SOURCE_CONTRACT")
    r=rows[0]
    if (r["symbol"],r["source_id"],r["sha256"],r["width"],r["height"],r["source_tileset_id"],r["parent_id"],r["source_events"],r["source_script_commands"],r["static_transfer_targets"])!=(SYMBOL,111,HASH,33,29,24,0,5,3,[]):raise ValueError("F12B_SOURCE_CONTRACT")
    return r

def evidence_gate(report):
    if report.get("baseline_maps")!=139 or report.get("baseline_preserved") is not True or report.get("native_verified") is not False:raise ValueError("F12B_BASELINE_REPORT")
    rows=[r for r in report["event_candidates"] if r["source_id"]==111]
    if any(r["source_sha256"]!=HASH or r["qa_map_id"] is not None for r in rows):raise ValueError("F12B_SOURCE_EVIDENCE")
    return {"mars_candidates":[r["source_event_id"] for r in rows if "MARS" in r["actors"]],
            "works_key_candidates":[r["source_event_id"] for r in rows if "WORKSKEY" in r["item_markers"]],
            "literal_works_key_candidates":[r["source_event_id"] for r in rows if "WORKSKEY" in r["literal_pickup_call_candidates"]],
            "native_bindings":0,"items_granted":0,"story_checkpoints_installed":0,
            "blockers":["exact_battle_identity_team_and_outcome_not_verified","source_item_acquisition_and_regional_receipt_not_verified","no_source_transfer_witness"]}

def preview(blobs,mapping,components,path,occupied,root=ROOT,report=None):
    if set(mapping)!=gym.GYM_SETS[7] or len(mapping)!=139 or len(set(mapping.values()))!=139:raise ValueError("F12B_REQUIRES_F11H")
    row=source_row(root)
    report=story.audit(blobs,mapping,path,root) if report is None else report
    gates=evidence_gate(report)
    before={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}
    infos=conn.read_marshal(blobs["Data/MapInfos.rxdata"],"F12B_INFOS")
    mid=gym.allocate(mapping,occupied,infos)
    if mid is None:raise ValueError("F12B_NO_FREE_MAPID")
    with pv.verified_archive(path,"maps") as z:
        raw=pv.member(z,pv.MAP_ROOT+"Data/Map111.rxdata")
        if hashlib.sha256(raw).hexdigest()!=HASH:raise ValueError("F12B_SOURCE_HASH")
        events=conn.read_marshal(raw,"F12B_SOURCE").attrs["@events"]
        scripts=sum(c.attrs.get("@code") in (355,655) for e in events.values() for p in e.attrs["@pages"] for c in p.attrs["@list"])
        if len(events)!=5 or scripts!=3 or conn.static_targets(events):raise ValueError("F12B_SOURCE_EVENT_SHAPE")
    expanded={**mapping,SYMBOL:mid}
    out,ids,comps,geometry=city.append_exteriors(blobs,mapping,components,path,expanded,[row],"F12B")
    old=teleport.build(blobs,mapping,components,root)
    new=teleport.build(out,ids,comps,root)
    if [r for r in old if r[0]!=SYMBOL]!=[r for r in new if r[0]!=SYMBOL]:raise ValueError("F12B_PRIOR_TELEPORT_CHANGED")
    if conn.read_marshal(out["Data/Map%03d.rxdata"%mid],"F12B_PREVIEW").attrs["@events"]:raise ValueError("F12B_DONOR_EVENT_COPIED")
    mutable={"Data/MapInfos.rxdata","Data/Tilesets.rxdata","PBS/map_metadata.txt"}
    if any(out.get(k)!=v for k,v in blobs.items() if k not in mutable):raise ValueError("F12B_PRIOR_BYTES_CHANGED")
    if before!={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}:raise ValueError("F12B_INPUT_MUTATED")
    return {"status":"ISOLATED_GEOMETRY_PREVIEW_ONLY","baseline_maps":139,"preview_maps":140,
            "preview_map_id":mid,"geometry":geometry[SYMBOL],"new_portals":0,"baseline_preserved":True,
            "runtime_install_enabled":False,"native_verified":False,"saves_accessed":False,**gates}
