"""F09C: exact proportional weight repair and read-only aquatic terrain audit.
No new Surf, fishing, Radar or opening events until native regional access
and terrain semantics are proven. The 99 original F09B methods are immutable.
"""
import json
import hashlib
import struct
from collections import Counter
from pathlib import Path
import sinnoh_f09b_original as original
import sinnoh_f08c_expansion as f08c
import sinnoh_connection_expansion as conn
import sinnoh_natural_expansion as natural
from pbs import catalogue

ROOT=Path(__file__).resolve().parents[2]
PIN="data/regions/sinnoh-f09b-approved-methods.json"

def exact_weights(table):
    """Convert ratios to integer percentages only if mathematically exact.
    Preserve every slot and level range, never round or drop entries.
    This is Blue's explicitly chosen proportional interpretation.
    """
    entries=table["slots"]
    total=sum(w for w,m,lo,hi in entries)
    if not entries or total<=0 or any(not 1<=w<=100 for w,m,lo,hi in entries):return None
    if any((100*w)%total for w,m,lo,hi in entries):return None
    return {"rate":table["rate"],"slots":[(100*w//total,m,lo,hi) for w,m,lo,hi in entries]}

def terrain_summary(blobs,mapping,masks,symbols):
    # Raw numeric tag evidence only; do not infer water from a numeric tag.
    # Count adjacent passable land near each tagged stack using the real
    # remapped tile data. No movement changes and no executable source import.
    tiles=conn.read_marshal(blobs["Data/Tilesets.rxdata"],"F09C_TILES")
    result={}
    for sym in sorted(symbols):
        mid=mapping[sym]
        world=conn.read_marshal(blobs["Data/Map%03d.rxdata"%mid],"F09C_MAP").attrs
        w,h=world["@width"],world["@height"]
        attrs=tiles[world["@tileset_id"]].attrs
        passages=attrs["@passages"].data[20:];tags=attrs["@terrain_tags"].data[20:]
        p=struct.unpack("<%dH"%(len(passages)//2),passages)
        t=struct.unpack("<%dH"%(len(tags)//2),tags)
        data=struct.unpack_from("<%dH"%(w*h*3),world["@data"].data,20)
        grid=masks.get(mid,[])
        if len(grid)!=h or any(len(r)!=w for r in grid):
            result[sym]={"status":"MASK_UNAVAILABLE"};continue
        counts=Counter();shore=Counter();blocked=Counter()
        for y in range(h):
            for x in range(w):
                stack=[data[z*w*h+y*w+x] for z in range(3) if data[z*w*h+y*w+x]]
                if any(i>=len(p) or i>=len(t) for i in stack):raise ValueError("F09C_TILE_RANGE")
                for tag in {t[i] for i in stack if t[i]}:
                    counts[tag]+=1
                    if grid[y][x]=="#":blocked[tag]+=1
                    if any(0<=nx<w and 0<=ny<h and grid[ny][nx]=="." for nx,ny in conn.city.teleport.neighbours(x,y)):
                        shore[tag]+=1
        result[sym]={"status":"TAG_EVIDENCE_ONLY","cells_by_tag":dict(counts),
            "adjacent_ordinary_ground_by_tag":dict(shore),"blocked_cells_by_tag":dict(blocked)}
    return result

def build(raw,prior,mapping,masks,donor,species,baseline,root=ROOT):
    if set(mapping)!=f08c.ALL or set(prior)!=set(mapping) or len(set(mapping.values()))!=131:
        raise ValueError("F09C_MAPIDS")
    if hashlib.sha256(donor).hexdigest()!=original.SHA256:raise ValueError("F09C_SOURCE_HASH")
    pin=json.loads((root/PIN).read_text("utf-8"))
    if pin["schema"]!=1 or pin["source_sha256"]!=original.SHA256 or len(pin["methods"])!=99:raise ValueError("F09C_PIN")
    sections,_=original.parse(donor)
    old_sections,_=original.parse(raw)
    signatures={(r["source_id"],r["method"]):r for r in pin["methods"]}
    for row in baseline["accepted"]:
        key=(row["source_id"],row["method"])
        expected=signatures.get(key)
        if expected is None or any(row[k]!=expected[k] for k in ("symbol","slots","rate")):
            raise ValueError("F09C_BASELINE_UNRECOGNIZED")
        table=sections[(row["source_id"],0)]["methods"][row["method"]]
        if old_sections[(mapping[row["symbol"]],0)]["methods"][row["method"]]!=table:
            raise ValueError("F09C_BASELINE_TABLE_CHANGED")
    source,_,_=conn.graph(root)
    source={**source,**{r["source_id"]:r for r in f08c.rows(root)}}
    cov={s:dict(r,methods=list(r["methods"])) for s,r in prior.items()}
    additions={};recovered=[];pending=[];totals=[]
    # Only the 21 source methods identified by the approved live run.
    for sid,method in pin["weight_candidates"]:
        section=sections.get((sid,0),{})
        if section.get("invalid") or method not in section.get("methods",{}):raise ValueError("F09C_PINNED_SOURCE_CHANGED")
        table=section["methods"][method];sym=source[sid]["symbol"];mid=mapping[sym]
        total=sum(row[0] for row in table["slots"])
        totals.append({"source_id":sid,"method":method,"total":total,"slots":len(table["slots"])})
        exact=exact_weights(table)
        reason=None
        if method in cov[sym]["methods"]:reason="baseline_preserved"
        elif method not in original.LAND|original.CAVE or sym in conn.city.OLD:reason="protected_or_unsupported"
        elif method in original.LAND and not any("g" in row for row in masks.get(mid,[])):reason="no_grass"
        elif method in original.CAVE and (sym not in natural.NATURAL-natural.OUTDOORS or not any("." in row for row in masks.get(mid,[]))):reason="no_cave"
        elif exact is None:reason="non_integer_exact_percentages"
        elif original.valid_table(method,exact,species):reason=original.valid_table(method,exact,species)
        if reason:
            pending.append({"source_id":sid,"symbol":sym,"method":method,"reason":reason,"total":total});continue
        body=(method+","+str(exact["rate"])+"\n"+"\n".join("    %d,%s,%d,%d"%row for row in exact["slots"])+"\n").encode("ascii")
        additions[(mid,0)]=additions.get((mid,0),b"")+body
        cov[sym]["methods"].append(method)
        recovered.append({"source_id":sid,"symbol":sym,"method":method,"original_total":total,"slots":len(exact["slots"])})
    out=original.append_methods(raw,additions)
    new_sections,_=original.parse(out)
    for key,row in old_sections.items():
        for method,table in row["methods"].items():
            if new_sections[key]["methods"][method]!=table:raise ValueError("F09C_PRIOR_METHOD_CHANGED")
    gaps=[]
    for sym,row in cov.items():
        methods=set(row["methods"])
        for base,group in (("Land",original.LAND),("Cave",original.CAVE)):
            if methods&group and base not in methods and not {base+"Morning",base+"Day",base+"Night"}<=methods:
                gaps.append({"symbol":sym,"family":base,"methods":sorted(methods&group)})
    stats={"maps_audited":131,"baseline_original_methods":len(baseline["accepted"]),
        "weight_totals":totals,"recovered":recovered,"pending":pending,"new_methods":len(recovered),
        "maps_with_encounters":sum(bool(r["methods"]) for r in cov.values()),
        "grass_without_land":sorted(s for s,r in cov.items() if r["grass_cells"] and not set(r["methods"])&original.LAND),
        "time_fallback_gaps":gaps,"native_verified":False,"water_access_verified":False}
    return out,cov,stats

def append(raw,prior,base,mapping,masks,blobs,path,baseline,root=ROOT):
    donor=original.read_source(path)
    out,coverage,report=build(raw,prior,mapping,masks,donor,catalogue(base,"pokemon"),baseline,root)
    aquatic={r["symbol"] for r in baseline["rejected"] if r["reason"]=="water_access_pending"}
    report["aquatic_terrain_evidence"]=terrain_summary(blobs,mapping,masks,aquatic)
    report["aquatic_access_status"]="PENDING_NATIVE_HM_ROD_TERRAIN_AND_INTERACTION_PROOF"
    print("SINNOH_F09C_REFINEMENT_REPORT "+json.dumps(report,sort_keys=True),flush=True)
    return out,coverage,report
