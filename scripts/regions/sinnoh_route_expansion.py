"""F05: append all 34 verified route exteriors without remapping F04."""
import json
from pathlib import Path
import sinnoh_city_expansion as city

ROOT=Path(__file__).resolve().parents[2]
SEGMENTS=frozenset({205,210,212,224,225,228})
ROUTES=frozenset("SINNOH_ROUTE_%d"%n for n in range(203,231))|frozenset("SINNOH_ROUTE_%d_SEGMENT_2"%n for n in SEGMENTS)
PRIOR=city.OLD|city.CITIES
ALL=PRIOR|ROUTES

def rows(root=ROOT):
    data=json.loads((root/"data/regions/sinnoh-f05-route-sources.json").read_text("utf-8"))
    result=data["routes"]
    if data["schema"]!=1 or len(result)!=34 or {r["symbol"] for r in result}!=ROUTES or len({r["source_id"] for r in result})!=34:
        raise ValueError("F05_INVALID_ROUTE_CATALOG")
    if {r["route"] for r in result}!=set(range(203,231)):
        raise ValueError("F05_INCOMPLETE_ROUTES")
    # ASCII names for PBS; keep original donor labels separately.
    return [{**r,"label":r["label"].replace(" — "," - ")} for r in result]

def allocate(mapping,occupied,root=ROOT):
    if set(mapping)!=PRIOR or len(set(mapping.values()))!=22 or set(mapping.values())&occupied:
        raise ValueError("F05_PRIOR_MAPIDS_CHANGED")
    free=[i for i in range(442,518) if i not in occupied and i not in mapping.values()]
    if len(free)<34:raise ValueError("F05_INSUFFICIENT_FREE_MAPIDS")
    return {**mapping,**{r["symbol"]:mid for r,mid in zip(rows(root),free)}}

def append(blobs,mapping,components,path,occupied,root=ROOT):
    return city.append_exteriors(blobs,mapping,components,path,allocate(mapping,occupied,root),rows(root),"F05")

def extra_destinations(root=ROOT):
    return [{"symbol":r["symbol"],"label":r["label"],"category":"Rotas"} for r in rows(root) if "_SEGMENT_" in r["symbol"]]
