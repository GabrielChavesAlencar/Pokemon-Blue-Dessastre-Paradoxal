"""Read-only one-shot audit of pinned public donor's Hoenn MapInfos/events.

Prints an event/connection report to GitHub Actions logs. NEVER caches,
redistributes, commits or installs donor RXDATA. For implementation planning
only; the actual source ZIP and native game are still needed for acceptance.
"""
from __future__ import annotations
import re
import sys
from urllib.request import urlopen
from urllib.parse import quote
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from server.ruby_marshal import loads,text,RubyObject
PIN="c59233bdbaac4fbfeca6aa01c7f05be628da2a92"
BASE=f"https://raw.githubusercontent.com/SocomSeal/The-PMon-World-Project/{PIN}/"+quote("The Pokémon World Project - Hoenn/Data",safe="/")
IDS=list(range(76,100))+list(range(181,190))+list(range(205,218))+[141,144,146,147,149]
def read(filename):
    url=f"{BASE}/{filename}"
    with urlopen(url,timeout=30) as response:
        blob=response.read()
    return loads(blob)
def safe(value):
    try: return text(value) if not isinstance(value,str) else value
    except Exception:return str(value)
def main():
    infos=read("MapInfos.rxdata")
    print("STAGE9_MAPPINGS_BEGIN",flush=True)
    for mid in IDS:
        mi=infos.get(mid)
        if not mi: continue
        print("MAP",mid,safe(mi.attrs.get("@name")), "PARENT",mi.attrs.get("@parent_id"),flush=True)
    print("STAGE9_EVENTS_BEGIN",flush=True)
    for mid in IDS:
        if mid not in infos: continue
        try: obj=read(f"Map{mid:03}.rxdata")
        except Exception as exc:
            print("MAP_ERROR",mid,type(exc).__name__,str(exc)[:100],flush=True)
            continue
        print("EVENT_MAP",mid,safe(infos[mid].attrs.get("@name")),
              "SIZE",obj.attrs.get("@width"),obj.attrs.get("@height"),
              "EVENT_COUNT",len(obj.attrs.get("@events",{})),flush=True)
        for event in obj.attrs.get("@events",{}).values():
            name=safe(event.attrs.get("@name",b""))
            x,y=event.attrs.get("@x"),event.attrs.get("@y")
            cmds=[cmd for page in event.attrs.get("@pages",[])[:2] for cmd in page.attrs.get("@list",[])
                  if getattr(cmd,"name",None)=="RPG::EventCommand"]
            transfers=[]
            for cmd in cmds:
                code=cmd.attrs.get("@code")
                if code==201:
                    transfers.append("WARP="+repr(cmd.attrs.get("@parameters",[])[:5]))
            if mid in (76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,181,182,183,184,185,186,187,188,189,205,206,207,208,209,210,211,212,213,215,216,217) or re.search("Door|Exit|Warp|Steven|Gym|Aqua|Magma|Mossdeep|Submarine|Tate|Liza|Space|Grunt",name,re.I):
                if len(name)>100: name=name[:100]
                print("EV",mid,x,y,repr(name), " ".join(transfers)[:170],flush=True)
    print("STAGE9_AUDIT_END",flush=True)
if __name__=="__main__":main()
