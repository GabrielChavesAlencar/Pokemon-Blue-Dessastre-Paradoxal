#!/usr/bin/env python3
"""Hoenn QA05: pinned Aqua/Magma/Seafloor source audit. Public read-only CI.

Downloads 8 original RXDATA files from an immutable Git revision, checks
their exact Git blob hashes against the committed Hoenn source inventory,
extracts only metadata (map IDs, event names, coordinates and page counts),
never executes donor event code or redistributes binary maps.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts/regions"))
from pilot_hoenn import SOURCE_MAPS,UPSTREAM
from server.ruby_marshal import RubyObject,loads,text

MAPS=(81,189,213,217,227,228,235,236)
PATTERN=re.compile(r"aqua|magma|grunt|submarine|archie|matt|tabitha|"
                   r"maxie|groudon|kyogre|strength|dive|cavern|orb",re.I)
BASE=("https://raw.githubusercontent.com/SocomSeal/The-PMon-World-Project/"
      + UPSTREAM + "/" +
      quote("The Pokémon World Project - Hoenn/Data",safe="/"))


def pinned_shas()->dict[str,str]:
    j=json.loads((ROOT/"data/regions/hoenn-source.json").read_text("utf-8"))
    if j.get("revision")!=UPSTREAM or j.get("truncated") is not False:
        raise ValueError("Manifesto original Hoenn incompleto/não fixado")
    return {r["path"]:r["sha"] for r in j["tree"] if r.get("type")=="blob"}


def fetch_one(mid:int,shas:dict[str,str])->tuple[int,list[dict],int]:
    name=f"Data/Map{mid:03}.rxdata"
    sha=shas.get(name)
    if not sha or mid not in SOURCE_MAPS:
        raise ValueError(f"Mapa não autorizado no manifesto do doador: {name}")
    req=Request(f"{BASE}/Map{mid:03}.rxdata",
                headers={"User-Agent":"Blue-Hoenn-QA05-Immutable-Audit"})
    with urlopen(req,timeout=60) as response:
        blob=response.read(3_000_001)
    if len(blob)>3_000_000:
        raise ValueError(f"RXDATA fonte excede limite: {mid}")
    actual=hashlib.sha1(f"blob {len(blob)}\0".encode("ascii")+blob).hexdigest()
    if actual!=sha:
        raise ValueError(f"Hash do mapa original diverge da revisão pinada: {mid}")
    obj=loads(blob)
    if not isinstance(obj,RubyObject) or obj.name!="RPG::Map":
        raise ValueError(f"Map{mid:03} não é RPG::Map")
    events=obj.attrs.get("@events",{})
    names=[]
    for ev in events.values():
        name=text(ev.attrs.get("@name",b""))
        if not PATTERN.search(name):
            continue
        names.append({"map":mid,"name":name[:75],
                      "x":ev.attrs.get("@x"),"y":ev.attrs.get("@y"),
                      "pages":len(ev.attrs.get("@pages",[]))})
    names.sort(key=lambda x:(x["x"],x["y"],x["name"]))
    return mid,names,len(events)


def main()->int:
    shas=pinned_shas()
    records=[]
    counts={}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures=[pool.submit(fetch_one,mid,shas) for mid in MAPS]
        for future in as_completed(futures):
            mid,events,count=future.result()
            counts[str(mid)]=count
            records.extend(events)
    if len(counts)!=len(MAPS) or sum(counts.values())<20:
        raise ValueError("Oito mapas de origem incompletos")
    records.sort(key=lambda x:(x["map"],x["x"],x["y"]))
    result={
        "region":"HOENN","qa_phase":"05/12","pinned_commit":UPSTREAM,
        "donor_maps_verified_by_sha":len(MAPS),
        "source_event_count":dict(sorted(counts.items(),key=lambda x:int(x[0]))),
        "candidate_aqua_magma_seafloor_events":records,
        "candidate_count":len(records),
        "donor_scripts_executed":False,"donor_assets_committed":False,
        "game_exe_tested":False,
    }
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print("HOENN_QA5_PINNED_SOURCE_OK")
    return 0


if __name__=="__main__":
    try:raise SystemExit(main())
    except (OSError,ValueError,TypeError,KeyError,IndexError) as e:
        print("HOENN_QA5_PINNED_SOURCE_BLOCKED:",str(e),file=sys.stderr)
        raise SystemExit(2)
