"""F09D: preserve exact source relative weights, no rounding or new slots.
Based on the existing Kanto non-100-weight convention in pbs.py. Native
compile verification remains mandatory; water and Radar are not enabled.
"""
import hashlib
import json
from pathlib import Path
import sinnoh_f09b_original as original
import sinnoh_f09c_refinement as refinement
import sinnoh_f08c_expansion as f08c
import sinnoh_connection_expansion as conn
import sinnoh_natural_expansion as natural
from pbs import catalogue

ROOT=Path(__file__).resolve().parents[2]
PIN="data/regions/sinnoh-f09c-relative-candidates.json"

def validate_relative(method,table,species):
    # The existing Blue PBS convention accepts bounded relative slot weights.
    # Validate all other constraints using the F09B validator. No change to
    # its strict default rule or to any earlier table.
    result=original.valid_table(method,table,species)
    if result!="weight_total_not_100":return result
    slots=table["slots"]
    if any(m in original.SPECIAL for w,m,lo,hi in slots):return "special_species"
    if any(m not in species for w,m,lo,hi in slots):return "missing_local_species"
    return None

def gaps(coverage):
    result=[]
    for sym,row in coverage.items():
        methods=set(row["methods"])
        for family,group in (("Land",original.LAND),("Cave",original.CAVE)):
            if methods&group and family not in methods and not {family+"Morning",family+"Day",family+"Night"}<=methods:
                result.append({"symbol":sym,"family":family,"methods":sorted(methods&group)})
    return result

def build(raw,prior,mapping,masks,donor,species,baseline,root=ROOT):
    if set(mapping)!=f08c.ALL or set(prior)!=set(mapping) or len(set(mapping.values()))!=131:
        raise ValueError("F09D_MAPIDS")
    if hashlib.sha256(donor).hexdigest()!=original.SHA256:raise ValueError("F09D_SOURCE_HASH")
    pin=json.loads((root/PIN).read_text("utf-8"))
    if pin["schema"]!=1 or pin["source_sha256"]!=original.SHA256 or len(pin["candidates"])!=20:
        raise ValueError("F09D_PIN")
    sections,_=original.parse(donor);old,_=original.parse(raw)
    # F09C's exact conversion remains immutable when local species permit it.
    for row in baseline["recovered"]:
        if row not in pin["recovered"]:raise ValueError("F09D_F09C_BASELINE")
        sym=next(r["symbol"] for r in pin["candidates"] if r["source_id"]==row["source_id"])
        table=sections[(row["source_id"],0)]["methods"][row["method"]]
        if old[(mapping[sym],0)]["methods"][row["method"]]!=refinement.exact_weights(table):
            raise ValueError("F09D_F09C_TABLE_CHANGED")
    source,_,_=conn.graph(root)
    source={**source,**{r["source_id"]:r for r in f08c.rows(root)}}
    cov={s:dict(r,methods=list(r["methods"])) for s,r in prior.items()}
    additions={};accepted=[];rejected=[];expected={}
    for row in pin["candidates"]:
        sid,sym,method=row["source_id"],row["symbol"],row["method"];mid=mapping[sym]
        sec=sections.get((sid,0),{})
        if source[sid]["symbol"]!=sym or sec.get("invalid") or method not in sec.get("methods",{}):
            raise ValueError("F09D_PINNED_SOURCE_CHANGED")
        table=sec["methods"][method]
        total=sum(w for w,m,lo,hi in table["slots"])
        if total!=row["total"] or len(table["slots"])!=row["slots"]:raise ValueError("F09D_WEIGHT_EVIDENCE_CHANGED")
        reason=validate_relative(method,table,species)
        if method in cov[sym]["methods"]:reason="baseline_preserved"
        elif sym in conn.city.OLD or method not in original.LAND|original.CAVE:reason="protected_or_unsupported"
        elif method in original.LAND and not any("g" in r for r in masks.get(mid,[])):reason="no_grass"
        elif method in original.CAVE and (sym not in natural.NATURAL-natural.OUTDOORS or not any("." in r for r in masks.get(mid,[]))):reason="no_cave"
        if reason:
            rejected.append({**row,"reason":reason});continue
        body=(method+","+str(table["rate"])+"\n"+"\n".join("    %d,%s,%d,%d"%slot for slot in table["slots"])+"\n").encode("ascii")
        additions[(mid,0)]=additions.get((mid,0),b"")+body
        cov[sym]["methods"].append(method)
        expected.setdefault(mid,{})[method]=[list(slot) for slot in table["slots"]]
        accepted.append(row)
    out=original.append_methods(raw,additions);new,_=original.parse(out)
    for key,row in old.items():
        for method,table in row["methods"].items():
            if new[key]["methods"][method]!=table:raise ValueError("F09D_PRIOR_TABLE_CHANGED")
    for mid,methods in expected.items():
        for method,slots in methods.items():
            if new[(mid,0)]["methods"][method]["slots"]!=[tuple(slot) for slot in slots]:
                raise ValueError("F09D_RELATIVE_SLOT_CHANGED")
    report={"maps_audited":131,"candidate_methods":20,"accepted":accepted,"rejected":rejected,
        "new_methods":len(accepted),"new_slots":sum(r["slots"] for r in accepted),
        "maps_with_encounters":sum(bool(r["methods"]) for r in cov.values()),
        "grass_without_land":sorted(s for s,r in cov.items() if r["grass_cells"] and not set(r["methods"])&original.LAND),
        "time_fallback_gaps":gaps(cov),"native_verified":False,"water_access_verified":False,
        "weight_policy":"EXACT_ORIGINAL_RELATIVE_WEIGHTS_PENDING_NATIVE_COMPILER"}
    return out,cov,report,expected

def append(raw,prior,base,mapping,masks,path,baseline,root=ROOT):
    out,cov,report,expected=build(raw,prior,mapping,masks,original.read_source(path),catalogue(base,"pokemon"),baseline,root)
    print("SINNOH_F09D_RELATIVE_REPORT "+json.dumps(report,sort_keys=True),flush=True)
    return out,cov,report,expected
