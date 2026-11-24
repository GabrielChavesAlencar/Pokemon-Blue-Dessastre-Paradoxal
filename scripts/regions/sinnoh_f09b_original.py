"""F09B: pinned donor PBS, conservative modern-format import into private QA.
Original map data is not published. Unsupported syntax remains pending.
"""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
import sinnoh_private_visual as pv
import sinnoh_connection_expansion as conn
import sinnoh_f08c_expansion as f08c
import sinnoh_natural_expansion as natural
from pbs import catalogue

SHA256="e812fb6413b410a8c9ce4380cd02c0e1f8a5d257f5793cf87182201d6e6d7990"
ROOT=Path(__file__).resolve().parents[2]
# Only methods with native compiler checks already supported by Blue.
LAND={"Land","LandMorning","LandDay","LandNight"}
CAVE={"Cave","CaveMorning","CaveDay","CaveNight"}
AQUATIC={"Water","WaterMorning","WaterDay","WaterNight","OldRod","GoodRod","SuperRod"}
HEADER=re.compile(r"^\[(\d+)(?:,(\d+))?\]$")
METHOD=re.compile(r"^([A-Za-z]+)(?:,\s*(\d+))?$")
SLOT=re.compile(r"^(\d+),\s*([A-Z][A-Z0-9_]*),\s*(\d+)(?:,\s*(\d+))?$")
# Static/special species remain separate from ordinary encounters.
SPECIAL={"ROTOM","DRIFLOON","DIALGA","PALKIA","GIRATINA","UXIE","MESPRIT","AZELF","HEATRAN","REGIGIGAS","CRESSELIA","DARKRAI","SHAYMIN","ARCEUS","MANAPHY","PHIONE"}

def read_source(path):
    with pv.verified_archive(path,"maps") as z:
        raw=pv.member(z,pv.MAP_ROOT+"PBS/encounters.txt")
    if hashlib.sha256(raw).hexdigest()!=SHA256:
        raise ValueError("F09B_DONOR_PBS_SHA256")
    return raw

def parse(raw):
    sections={};issues=[];key=None;method=None
    for line in raw.decode("utf-8-sig").splitlines():
        line=line.split("#",1)[0].strip()
        if not line:continue
        h=HEADER.fullmatch(line)
        if h:
            key=(int(h[1]),int(h[2] or 0));method=None
            if key in sections:
                issues.append({"source_id":key[0],"version":key[1],"reason":"duplicate_section"})
                sections[key]["invalid"]=True
            else:sections[key]={"invalid":False,"methods":{},"shapes":Counter()}
            continue
        if key is None:
            issues.append({"reason":"unscoped_line","field_count":len(line.split(","))})
            continue
        row=sections[key];m=METHOD.fullmatch(line);slot=SLOT.fullmatch(line)
        if m:
            method=m[1]
            row["shapes"]["method_header"]+=1
            if method in row["methods"]:
                row["invalid"]=True
                issues.append({"source_id":key[0],"version":key[1],"reason":"duplicate_method","method":method})
            else:row["methods"][method]={"rate":int(m[2]) if m[2] else None,"slots":[]}
        elif slot and method is not None:
            weight,mon,lo,hi=int(slot[1]),slot[2],int(slot[3]),int(slot[4] or slot[3])
            row["methods"][method]["slots"].append((weight,mon,lo,hi))
            row["shapes"]["weighted_slot"]+=1
        else:
            row["invalid"]=True
            row["shapes"]["unrecognized_fields_"+str(len(line.split(",")))]+=1
    return sections,issues

def valid_table(method,table,species):
    if method not in LAND|CAVE|AQUATIC:return "unsupported_method"
    rate=table["rate"]
    # Rod rates may be omitted in Essentials; every other method requires an
    # explicit rate to establish this source dialect unambiguously.
    if rate is None and method not in {"OldRod","GoodRod","SuperRod"}:return "missing_explicit_rate"
    if rate is not None and not 1<=rate<=100:return "invalid_rate"
    entries=table["slots"]
    if not entries or any(not 1<=w<=100 or not 1<=lo<=hi<=100 for w,m,lo,hi in entries):return "invalid_slot"
    if sum(w for w,m,lo,hi in entries)!=100:return "weight_total_not_100"
    if any(m in SPECIAL for w,m,lo,hi in entries):return "special_species"
    if any(m not in species for w,m,lo,hi in entries):return "missing_local_species"
    return None

def append_methods(raw,additions):
    # Existing section content and slot lines are kept verbatim. Add methods
    # to the same section; never create duplicate map/version headers.
    chunks=raw.splitlines(keepends=True);out=[];current=None;seen=set()
    def flush():
        if current in additions:
            out.append(b"\n"+additions[current]);seen.add(current)
    for line in chunks:
        h=HEADER.fullmatch(line.decode("utf-8-sig").split("#",1)[0].strip())
        if h:
            flush();current=(int(h[1]),int(h[2] or 0))
            if current in seen:raise ValueError("F09B_DUPLICATE_BASE_SECTION")
        out.append(line)
    flush()
    for key,body in sorted(additions.items()):
        if key not in seen:
            if key[1]!=0:raise ValueError("F09B_UNSUPPORTED_VERSION")
            out.append(("\n[%03d] # F09B original source\n"%key[0]).encode("ascii")+body)
    return b"".join(out)

def build(raw,prior,mapping,masks,donor,species,root=ROOT):
    if set(mapping)!=f08c.ALL or len(set(mapping.values()))!=131 or set(prior)!=set(mapping):
        raise ValueError("F09B_MAPIDS")
    source,_,_=conn.graph(root)
    source={**source,**{r["source_id"]:r for r in f08c.rows(root)}}
    sections,issues=parse(donor)
    coverage={s:dict(r,methods=list(r["methods"])) for s,r in prior.items()}
    accepted=[];rejected=[];additions={};shapes=Counter();methods=Counter()
    for (sid,version),section in sorted(sections.items()):
        shapes.update(section["shapes"]);methods.update(section["methods"].keys())
        if sid not in source:continue
        sym=source[sid]["symbol"];mid=mapping[sym]
        if version!=0 or section["invalid"]:
            rejected.append({"source_id":sid,"symbol":sym,"version":version,"reason":"unsupported_version_or_dialect",
                "shapes":dict(section["shapes"])})
            continue
        for method,table in section["methods"].items():
            reason=valid_table(method,table,species)
            if method in coverage[sym]["methods"]:reason="baseline_method_preserved"
            elif sym in conn.city.OLD:reason="protected_opening"
            elif method in LAND and not any("g" in r for r in masks.get(mid,[])):reason="no_grass"
            elif method in CAVE and (sym not in natural.NATURAL-natural.OUTDOORS or not any("." in r for r in masks.get(mid,[]))):reason="no_validated_cave"
            elif method in AQUATIC:
                # Existing movement masks do not prove Surf or fishing access.
                # Keep the original method recorded but disabled pending HM,
                # terrain tags, rod and native water interaction verification.
                reason="water_access_pending"
            if reason:
                rejected.append({"source_id":sid,"symbol":sym,"method":method,"reason":reason})
                continue
            header=method+(","+str(table["rate"]) if table["rate"] is not None else "")
            body=(header+"\n"+"\n".join("    %d,%s,%d,%d"%row for row in table["slots"])+"\n").encode("ascii")
            additions[(mid,0)]=additions.get((mid,0),b"")+body
            coverage[sym]["methods"].append(method)
            accepted.append({"source_id":sid,"symbol":sym,"map_id":mid,"method":method,"slots":len(table["slots"]),"rate":table["rate"]})
    out=append_methods(raw,additions)
    stats={"maps_audited":131,"donor_sections":len(sections),"donor_methods":dict(methods),"dialect_shapes":dict(shapes),
        "parse_issues":issues,"accepted":accepted,"rejected":rejected,"new_methods":len(accepted),"new_maps":len({r["symbol"] for r in accepted if not prior[r["symbol"]]["methods"]}),
        "maps_with_encounters":sum(bool(r["methods"]) for r in coverage.values()),
        "grass_without_land":sorted(s for s,r in coverage.items() if r["grass_cells"] and not any(m in LAND for m in r["methods"])),
        "native_verified":False,"water_access_verified":False,"original_file_sha256":hashlib.sha256(donor).hexdigest()}
    return out,coverage,stats

def append(raw,prior,base,mapping,masks,path,root=ROOT):
    out,coverage,stats=build(raw,prior,mapping,masks,read_source(path),catalogue(base,"pokemon"),root)
    print("SINNOH_F09B_ORIGINAL_REPORT "+json.dumps(stats,sort_keys=True),flush=True)
    return out,coverage,stats
