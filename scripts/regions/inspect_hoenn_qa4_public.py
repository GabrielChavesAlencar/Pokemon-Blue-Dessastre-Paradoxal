#!/usr/bin/env python3
"""Hoenn QA04: read-only inspect field obstacles in pinned original RXDATA.

Reports geometry metadata only; never copies source event scripts/graphics.
Does not assert native Game.exe passability from RXDATA descriptions.
"""
from __future__ import annotations

import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts/regions"))
from server.ruby_marshal import loads,RubyObject,text
from pilot_hoenn import SOURCE_MAPS,UPSTREAM
from hoenn_qa_phase4 import classify_obstacle

# Key candidate maps; enough for cavern/gym/field-route coverage.
CHECK=(87,91,157,180,227,228,229,230,231,232,233,234,235,236,
       238,239,240,241,242,243,244,245,246,247,248,
       250,251,252,255,261,266,322)
BASE=("https://raw.githubusercontent.com/SocomSeal/The-PMon-World-Project/"
      + UPSTREAM+"/"+quote("The Pokémon World Project - Hoenn/Data",safe="/"))

def load_map(mid:int):
    request=Request(f"{BASE}/Map{mid:03}.rxdata",
                    headers={"User-Agent":"Blue-Hoenn-QA4-ReadOnly"})
    with urlopen(request,timeout=55) as response:
        blob=response.read(3_000_001)
    if len(blob)>3_000_000:
        raise ValueError(f"Mapa da fonte acima do tamanho de auditoria: {mid}")
    obj=loads(blob)
    if obj.name!="RPG::Map":
        raise ValueError(f"RPG::Map ausente para {mid}")
    found=[]
    for ev in obj.attrs.get("@events",{}).values():
        name=text(ev.attrs.get("@name",b""))[:100]
        pages=ev.attrs.get("@pages",[])
        scripts=[]
        for page in pages:
            for command in page.attrs.get("@list",[]):
                if (isinstance(command,RubyObject) and
                        command.attrs.get("@code") in (355,655)):
                    scripts.extend(text(p) for p in command.attrs.get("@parameters",[])
                                   if isinstance(p,(str,bytes)))
        code=" ".join(scripts)
        category=classify_obstacle(name,code)
        if category is not None:
            found.append({"source_map_id":mid,"x":ev.attrs.get("@x"),
                          "y":ev.attrs.get("@y"),"name":name,
                          "kind":category,
                          "pages":len(pages),
                          "native_script_calls":bool(code)})
    return mid,found,len(obj.attrs.get("@events",{}))

def main():
    if not set(CHECK)<=set(SOURCE_MAPS):
        raise ValueError("Auditoria fora dos 199 mapas de Hoenn")
    found=[]
    overview={}
    with ThreadPoolExecutor(max_workers=8) as pool:
        for future in as_completed({pool.submit(load_map,mid):mid for mid in CHECK}):
            mid,candidates,total=future.result()
            overview[mid]=total
            found.extend(candidates)
    found.sort(key=lambda x:(x["source_map_id"],x["x"],x["y"]))
    summary={"region":"HOENN","qa_phase":"04/12","source_pin":UPSTREAM,
             "maps_inspected":len(CHECK),"event_counts":dict(sorted(overview.items())),
             "field_obstacles":found,
             "source_code_copied":False,
             "native_game_exe_tested":False}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    print("HOENN_QA4_PINNED_FIELD_AUDIT_OK")
if __name__=="__main__":
    try: main()
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print("HOENN_QA4_BLOCKED:",repr(exc),file=sys.stderr)
        raise SystemExit(2)
