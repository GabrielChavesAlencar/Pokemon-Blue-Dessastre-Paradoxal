"""F07: append pinned original interiors, never donor events or scripts."""
import json
from pathlib import Path
import sinnoh_city_expansion as city
import sinnoh_natural_expansion as natural

ROOT=Path(__file__).resolve().parents[2]
SOURCE_IDS=frozenset({32,43,48,81,86,87,88,97,107,115,120,124,125,129,130,131,132,133,134,135,136,137,138,143,148,149,158,167,168,169,170,171,172,187,188,220})
INTERIORS=frozenset("SINNOH_F07_INTERIOR_%03d"%mid for mid in SOURCE_IDS)
ALL=natural.ALL|INTERIORS
COUNT=127

def rows(root=ROOT):
    data=json.loads((root/"data/regions/sinnoh-f07-interior-sources.json").read_text("utf-8"))
    result=data["interiors"]
    if (data["schema"]!=1 or data["scope"]!="PRIVATE_QA_ONLY" or data["source_tileset_id"]!=25
        or len(result)!=36 or {r["source_id"] for r in result}!=SOURCE_IDS
        or any(r["symbol"]!="SINNOH_F07_INTERIOR_%03d"%r["source_id"] or r["source_tileset_id"]!=25
               or r["outdoor"] is not False or r["category"]!="Casas e interiores" for r in result)):
        raise ValueError("F07_INVALID_INTERIOR_CATALOG")
    return result

def allocate(mapping,occupied,root=ROOT):
    if (set(mapping)!=natural.ALL or len(set(mapping.values()))!=91
        or any(type(i) is not int or not 442<=i<=natural.PRIVATE_MAX for i in mapping.values())
        or set(mapping.values())&occupied):
        raise ValueError("F07_PRIOR_MAPIDS_CHANGED")
    free=[i for i in range(442,natural.PRIVATE_MAX+1) if i not in occupied and i not in mapping.values()]
    if len(free)<36:raise ValueError("F07_INSUFFICIENT_FREE_PRIVATE_MAPIDS")
    return {**mapping,**{r["symbol"]:mid for r,mid in zip(rows(root),free)}}

def append(blobs,mapping,components,path,occupied,root=ROOT):
    return city.append_exteriors(blobs,mapping,components,path,allocate(mapping,occupied,root),rows(root),"F07",source_tileset_id=25)

def extra_destinations(root=ROOT):
    return [{k:r[k] for k in ("symbol","label","category")} for r in rows(root)]
