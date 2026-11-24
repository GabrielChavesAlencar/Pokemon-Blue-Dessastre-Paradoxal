"""F06: pinned natural-area maps in the isolated QA copy only."""
import json
from pathlib import Path
import sinnoh_city_expansion as city
import sinnoh_route_expansion as route

ROOT=Path(__file__).resolve().parents[2]
SOURCE_IDS=frozenset({33,76,82,89,92,93,98,117,121,145,152,153,159,161,162,173,174,182,183,184,189,190,197,207,208,209,210,211,212,213,214,215,216,217,221})
NATURAL=frozenset(["SINNOH_OREBURGH_MINE","SINNOH_OREBURGH_GATE","SINNOH_MT_CORONET_WEST_APPROACH","SINNOH_SOLACEON_RUINS","SINNOH_ETERNA_FOREST","SINNOH_ETERNA_FOREST_SOURCE_093","SINNOH_FLOAROMA_MEADOW","SINNOH_MT_CORONET_SOURCE_117","SINNOH_MT_CORONET_INTERIOR_ROUTES","SINNOH_RAVAGED_PATH","SINNOH_STARK_MOUNTAIN","SINNOH_STARK_MOUNTAIN_SOURCE_153","SINNOH_ACUITY_LAKEFRONT","SINNOH_LAKE_ACUITY","SINNOH_ACUITY_CAVERN","SINNOH_SNOWPOINT_TEMPLE","SINNOH_MT_CORONET_SOURCE_174","SINNOH_MT_CORONET_SOURCE_182","SINNOH_MT_CORONET_SOURCE_183","SINNOH_MT_CORONET_SOURCE_184","SINNOH_WAYWARD_CAVE","SINNOH_WAYWARD_CAVE_SOURCE_190","SINNOH_VERITY_CAVERN","SINNOH_MANIAC_TUNNEL","SINNOH_SPRING_PATH","SINNOH_SENDOFF_SPRING","SINNOH_TURNBACK_CAVE","SINNOH_TURNBACK_CAVE_SOURCE_211","SINNOH_TURNBACK_CAVE_SOURCE_212","SINNOH_TURNBACK_CAVE_SOURCE_213","SINNOH_VALOR_LAKEFRONT","SINNOH_LAKE_VALOR","SINNOH_LAKE_VALOR_SOURCE_216","SINNOH_VALOR_CAVERN","SINNOH_GREAT_MARSH"])
OUTDOORS=frozenset(["SINNOH_ETERNA_FOREST","SINNOH_ETERNA_FOREST_SOURCE_093","SINNOH_FLOAROMA_MEADOW","SINNOH_STARK_MOUNTAIN","SINNOH_ACUITY_LAKEFRONT","SINNOH_LAKE_ACUITY","SINNOH_SPRING_PATH","SINNOH_SENDOFF_SPRING","SINNOH_VALOR_LAKEFRONT","SINNOH_LAKE_VALOR","SINNOH_LAKE_VALOR_SOURCE_216","SINNOH_GREAT_MARSH"])
ALL=route.ALL|NATURAL
COUNT=91
# 518..599 are Unova's historical candidate space, NOT a shared Sinnoh claim.
# The isolated QA copy never shares a map or save namespace with Unova.
# Never reuse an actual native occupied ID or enter Johto/Hoenn/four-digit bands.
PRIVATE_MAX=599

def rows(root=ROOT):
    data=json.loads((root/"data/regions/sinnoh-f06-natural-sources.json").read_text("utf-8"))
    result=data["areas"]
    if (data["schema"]!=1 or data["scope"]!="PRIVATE_QA_ONLY" or len(result)!=len(NATURAL)
        or {r["symbol"] for r in result}!=NATURAL or {r["source_id"] for r in result}!=SOURCE_IDS
        or {r["symbol"] for r in result if r["outdoor"] is True}!=OUTDOORS
        or any(type(r["outdoor"]) is not bool for r in result)):
        raise ValueError("F06_INVALID_NATURAL_CATALOG")
    return result

def allocate(mapping,occupied,root=ROOT):
    if (set(mapping)!=route.ALL or len(set(mapping.values()))!=56
        or any(type(i) is not int or not 442<=i<=517 for i in mapping.values())
        or set(mapping.values())&occupied):
        raise ValueError("F06_PRIOR_MAPIDS_CHANGED")
    free=[i for i in range(442,PRIVATE_MAX+1) if i not in occupied and i not in mapping.values()]
    if len(free)<len(NATURAL):raise ValueError("F06_INSUFFICIENT_FREE_PRIVATE_MAPIDS")
    return {**mapping,**{r["symbol"]:mid for r,mid in zip(rows(root),free)}}

def append(blobs,mapping,components,path,occupied,root=ROOT):
    return city.append_exteriors(blobs,mapping,components,path,allocate(mapping,occupied,root),rows(root),"F06")

def extra_destinations(root=ROOT):
    catalog=json.loads((root/"data/regions/sinnoh-expansion-destinations.json").read_text("utf-8"))
    existing={r["symbol"] for r in catalog["destinations"]}
    return [{k:r[k] for k in ("symbol","label","category")} for r in rows(root) if r["symbol"] not in existing]
