"""Read-only F12C source audit; no allocation, event execution or rewards."""
import hashlib
import re
import audit_sinnoh_expansion_f03 as f03
import sinnoh_connection_expansion as conn
import sinnoh_f12b2_windworks_evidence as evidence
import sinnoh_f12b4_windworks_access as access
import sinnoh_private_visual as pv

PINNED={90:"b28d2a456cc4cb4218fa1c4387cd3159ed84ef8b945585597ee98ac10be4139e",
        119:"047e275d9cfb93a43b152bdc16b09f8808e3e2d17426893a616a0c92dee5c83e"}
def classify(rows):
    named=[r["source_id"] for r in rows if re.search(r"galactic|team[ _-]*galaxy",r["name"],re.I)]
    anonymous=[r["source_id"] for r in rows if not r["name"] or re.fullmatch(r"MAP\s*\d+",r["name"],re.I)]
    nearby=[r["source_id"] for r in rows if r["source_id"] in (90,119,129,130,149) or r["parent_id"]==90]
    return named,anonymous,nearby

def audit(blobs,mapping,path):
    if set(mapping)!=access.ALL or len(set(mapping.values()))!=140:raise ValueError("F12C_REQUIRES_140_BASELINE")
    before={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}
    with pv.verified_archive(path,"maps") as z:
        rows,tiles=f03.audit_maps(z)
        byid={r["source_id"]:r for r in rows}
        if len(byid)!=238 or any(byid.get(i,{}).get("sha256")!=h for i,h in PINNED.items()):
            raise ValueError("F12C_SOURCE_INVENTORY_CHANGED")
        named,anonymous,nearby=classify(rows)
        relevant=set(named+anonymous+nearby)
        inspected=[]; candidates=[]; anchors=[]; scanned=0
        for name in sorted(f03.index(z).values()):
            if not name.startswith(pv.MAP_ROOT+"Data/"):continue
            m=f03.MAP_RE.fullmatch(name[len(pv.MAP_ROOT+"Data/"):])
            if not m:continue
            sid=int(m[1]); raw=pv.member(z,name); digest=hashlib.sha256(raw).hexdigest()
            if digest!=byid[sid].get("sha256"):raise ValueError("F12C_SOURCE_HASH")
            events=conn.read_marshal(raw,"F12C_SOURCE").attrs["@events"]
            scanned+=1
            if sid in relevant:inspected.append(sid)
            for eid,event in sorted(events.items()):
                row=evidence.event_evidence(event,eid)
                actor=set(row["markers"]["actors"])|set(row["script_actor_markers"])
                items=set(row["markers"]["item_markers"])|set(row["script_item_markers"])
                targets=row["source_transfer_targets"]
                if sid in (90,119) or 90 in targets or 119 in targets:
                    anchors.append({"source_id":sid,"event_id":eid,"position":row["position"],
                                    "targets":targets,"actor_markers":sorted(actor),"item_markers":sorted(items)})
                if actor&{"GALACTIC","TEAM_GALACTIC","JUPITER"} or "BICYCLE" in items:
                    candidates.append({"source_id":sid,"source_sha256":digest,"event_id":eid,
                                       "position":row["position"],"actors":sorted(actor),"items":sorted(items),
                                       "targets":targets,"identity_approved":False})
        if scanned!=238 or not set(anonymous)<=set(inspected):raise ValueError("F12C_SCAN_INCOMPLETE")
    if before!={k:hashlib.sha256(v).hexdigest() for k,v in blobs.items()}:raise ValueError("F12C_BASELINE_MUTATED")
    return {"status":"SOURCE_CANDIDATES_ONLY","baseline_maps":140,"baseline_preserved":True,
            "source_maps_scanned":scanned,"named_candidates":named,"anonymous_maps_scanned":anonymous,
            "nearby_maps":[byid[i] for i in nearby],"access_anchors":anchors,"event_candidates":candidates,
            "historical_jupiter_team":[["ZUBAT",21],["SKUNTANK",23]],
            "new_maps":0,"new_portals":0,"native_bindings":0,"items_granted":0,
            "source_scripts_executed":False,"native_verified":False,"saves_accessed":False}
