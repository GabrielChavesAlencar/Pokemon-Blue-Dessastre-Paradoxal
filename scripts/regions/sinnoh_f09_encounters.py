"""F09A: private QA encounter coverage using explicitly authored Blue balance.
Not original Platinum probability/level data. Never copy unknown donor scripts.
"""
import hashlib
import json
import re
from pathlib import Path
import sinnoh_private_visual as pv
import sinnoh_natural_expansion as natural
import sinnoh_f08c_expansion as f08c
from pbs import catalogue

ROOT=Path(__file__).resolve().parents[2]
REFERENCE="data/regions/sinnoh-symbolic-encounters.json"
# Explicit authorial QA level ranges (not measurements of the donor game).
# Species are validated against the reviewed reference, exact area, local
# species database and actual terrain. No guessed symbols or legendary slots.
BALANCE={
    "ROUTE_203":("Land",4,7),
    "OREBURGH_MINE":("Cave",5,9),
    "ETERNA_FOREST":("Land",10,15),
    "ROUTE_206":("Land",15,19),
    "WAYWARD_CAVE":("Cave",15,20),
    "ROUTE_208":("Land",17,22),
    "ROUTE_209":("Land",18,23),
    "ROUTE_210":("Land",20,25),
    "ROUTE_215":("Land",20,26),
    "ROUTE_213":("Land",20,25),
    "GREAT_MARSH":("Land",22,27),
    "ROUTE_216":("Land",30,35),
    "ROUTE_217":("Land",32,37),
    "ROUTE_222":("Land",38,43),
}

def source_inventory(path,root=ROOT):
    # The map archive is pinned; only inventory the encounter PBS, if any.
    # Do not interpret an unknown dialect or import unrelated donor maps.
    with pv.verified_archive(path,"maps") as z:
        names=[x.filename for x in z.infolist() if x.filename.casefold().endswith("/pbs/encounters.txt")]
        name=pv.MAP_ROOT+"PBS/encounters.txt"
        if name not in names:
            return {"status":"ABSENT_EXACT_MEMBER","candidate_members":len(names),"imported":False}
        raw=pv.member(z,name)
        ids=sorted({int(x) for x in re.findall(rb"(?m)^\s*\[(\d+)(?:,\d+)?\]",raw)})
        source,_,_=__import__("sinnoh_connection_expansion").graph(root)
        known=set(source)|set(f08c.SYMBOLS)
        return {"status":"PRESENT_REQUIRES_DIALECT_REVIEW","sha256":hashlib.sha256(raw).hexdigest(),
            "section_map_count":len(ids),"matched_source_ids":sorted(set(ids)&known),"imported":False}

def reviewed(root=ROOT):
    doc=json.loads((root/REFERENCE).read_text("utf-8"))
    if doc["region"]!="SINNOH" or doc["reference_game"]!="Platinum" or doc["encounter_weights_verified"] is not False:
        raise ValueError("F09_REFERENCE_SCOPE")
    rows={r["area_symbol"]:r for r in doc["areas"] if r["area_symbol"]}
    for sym,(method,lo,hi) in BALANCE.items():
        if sym not in rows or method not in rows[sym]["candidate_pbs_methods"] or not 1<=lo<=hi<=100:
            raise ValueError("F09_REFERENCE_MISMATCH:"+sym)
        species=rows[sym]["reference_species"]
        if not species or len(species)!=len(set(species)) or any(not re.fullmatch(r"[A-Z][A-Z0-9_]*",m) for m in species):
            raise ValueError("F09_REFERENCE_SPECIES:"+sym)
        special={r["species"] for r in rows[sym]["special_events"]}
        if special&set(species):raise ValueError("F09_STATIC_EVENT_SLOT:"+sym)
    return rows

def slots(species,lo,hi):
    # Equal authorial weights, deterministic remainder; not original odds.
    q,r=divmod(100,len(species))
    return [(q+(i<r),mon,lo,hi) for i,mon in enumerate(species)]

def build(raw,prior,mapping,masks,species,root=ROOT):
    if set(mapping)!=f08c.ALL or len(set(mapping.values()))!=131:
        raise ValueError("F09_INVALID_MAPIDS")
    reference=reviewed(root)
    headers=[int(x) for x in re.findall(rb"(?m)^\s*\[(\d+)(?:,\d+)?\]",raw)]
    occupied=set(headers)
    coverage={};report={};blocks=[]
    for sym,mid in mapping.items():
        grid=masks.get(mid,[])
        grass=sum(row.count("g") for row in grid)
        ground=sum(row.count(".") for row in grid)
        if sym in prior:
            coverage[sym]=dict(prior[sym])
            report[sym]={"status":"BASELINE_PRESERVED","grass_cells":grass,"methods":prior[sym]["methods"]}
            continue
        methods=[];reason="NO_REFERENCE_ASSIGNMENT"
        if sym.startswith("SINNOH_F07_INTERIOR_"):
            reason="INTERIOR_NO_NORMAL_ENCOUNTER"
        key=sym.removeprefix("SINNOH_")
        if key in BALANCE:
            method,lo,hi=BALANCE[key];mons=reference[key]["reference_species"]
            if mid in occupied:raise ValueError("F09_ENCOUNTER_ID_COLLISION:"+sym)
            if method=="Land" and not grass:reason="NO_GRASS_TERRAIN"
            elif method=="Cave" and (sym not in natural.NATURAL-natural.OUTDOORS or not ground):reason="NO_CAVE_TERRAIN"
            elif not set(mons)<=species:reason="MISSING_LOCAL_SPECIES"
            else:
                methods=[method];reason="AUTHORED_QA_TABLE"
                block=["[%03d] # %s"%(mid,sym),method+",21"]
                block.extend("    %d,%s,%d,%d"%row for row in slots(mons,lo,hi))
                blocks.append("\n".join(block))
                occupied.add(mid)
        coverage[sym]={"grass_cells":grass,"methods":methods,"water_access_not_verified":False}
        report[sym]={"status":reason,"grass_cells":grass,"ground_cells":ground,"methods":methods}
    if len(coverage)!=131:raise ValueError("F09_COVERAGE_COUNT")
    suffix=("\n# Blue Sinnoh F09A authored QA balance (not original odds)\n"+"\n".join(blocks)+"\n").encode("ascii") if blocks else b""
    stats={"maps_audited":131,"new_tables":len(blocks),"maps_with_encounters":sum(bool(x["methods"]) for x in coverage.values()),
        "grass_without_land":sorted(s for s,r in coverage.items() if r["grass_cells"] and not any(m.startswith("Land") for m in r["methods"])),
        "original_weights_verified":False,"native_verified":False,"areas":report}
    return raw+suffix,coverage,stats

def append(raw,prior,base,mapping,masks,path,root=ROOT):
    result,coverage,report=build(raw,prior,mapping,masks,catalogue(base,"pokemon"),root)
    report["donor_encounter_inventory"]=source_inventory(path,root)
    print("SINNOH_F09_ENCOUNTER_REPORT "+json.dumps(report,sort_keys=True),flush=True)
    return result,coverage,report
