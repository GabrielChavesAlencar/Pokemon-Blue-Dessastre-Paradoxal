"""Conditional append-only private QA activation. Never touches native saves."""
import hashlib
import sinnoh_f12c2_eterna_preview as preview
import sinnoh_f12c3_jupiter_candidate as quest
import sinnoh_f12b4_windworks_access as access
import sinnoh_qa_teleport as tp
import sinnoh_f10b7_field_audit as gates
import sinnoh_f10b_trainers as trainers
import sinnoh_connection_expansion as conn
ALL=access.ALL|set(preview.SYMBOLS)

def append(blobs,mapping,components,delta,report,base,root,mars_report):
    def blocked(reason):
        return blobs,mapping,components,{"status":"F12C4_BLOCKED","reason":reason,"runtime_install_enabled":False,"native_verified":False},b""
    if set(mapping)!=access.ALL or len(mapping)!=140:return blocked("requires_140_baseline")
    if mars_report.get("candidate_runtime_handlers")!=5:return blocked("requires_mars_quest")
    payload,qr,plugin=quest.local_preview(blobs,mapping,delta,report,base,root,return_payload=True)
    if not payload or not plugin:return blocked(qr.get("reason","local_catalog_blocked"))
    if "HM01" not in trainers.catalogue(base,"items"):return blocked("local_HM01_missing")
    rooms=report["rooms"]
    ids={r["symbol"]:r["map_id"] for r in rooms}
    if set(ids)!=set(preview.SYMBOLS) or set(ids.values())&set(mapping.values()) or len(set(ids.values()))!=4:return blocked("mapid_collision")
    city=report["city_entry_candidate"]["map_id"]
    allowed={"Data/MapInfos.rxdata","Data/Tilesets.rxdata","Data/Map%03d.rxdata"%city}
    if any(k in blobs and k not in allowed for k in payload):return blocked("existing_file_collision")
    out={**blobs,**payload}
    if any(out["Data/Map%03d.rxdata"%m]!=blobs["Data/Map%03d.rxdata"%m] for m in mapping.values() if m!=city):return blocked("prior_map_changed")
    if tp.build(out,mapping,components,root)!=tp.build(blobs,mapping,components,root):return blocked("prior_teleport_changed")
    _,_,idx,_,reach,_=gates.access_graph(blobs,mapping,components,root,directional=True)
    _,_,post,_,reached,_=gates.access_graph(out,mapping,components,root,directional=True)
    xy=report["city_entry_candidate"]["position"]
    if not (trainers.reached_cells(idx,reach)-{(city,*xy)})<=trainers.reached_cells(post,reached):return blocked("prior_access_changed")
    meta=blobs["PBS/map_metadata.txt"]
    for i,symbol in enumerate(preview.SYMBOLS,1):
        meta+=("\n# F12C4 authored QA\n[%03d]\nName = Galactic Eterna Building %dF\nOutdoor = false\nShowArea = true\nBicycle = false\nSnapEdges = true\n"%(ids[symbol],i)).encode("ascii")
    out["PBS/map_metadata.txt"]=meta
    expanded={**mapping,**ids}
    comps={**components,**{symbol:preview.layout(i) for i,symbol in enumerate(preview.SYMBOLS,1)}}
    rooms=[dict(r,sha256=hashlib.sha256(out["Data/Map%03d.rxdata"%r["map_id"]]).hexdigest()) for r in rooms]
    return out,expanded,comps,{"status":"F12C4_INSTALL_PREPARED","runtime_install_enabled":True,
        "maps_before":140,"maps_after":144,"rooms":rooms,"baseline_preserved":True,
        "entry_event_additive":True,"new_portals":8,"new_seams":0,"new_events":qr["new_events"]+1,
        "entry":report["city_entry_candidate"],"quest":qr,"hm_award":"PROJECT_AUTHORED_ETERNA_GUIDE_AFTER_MARS_AND_FOREST",
        "qa_teleport_excluded":list(preview.SYMBOLS),"native_verified":False,"items_granted":0},plugin
