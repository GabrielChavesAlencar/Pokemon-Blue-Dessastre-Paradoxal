"""Read-only discovery of endgame Hoenn map IDs, event anchors and static warps.

Triggered by its dedicated CI workflow. Pinned donor revision only; neither source binaries nor third-party scripts
are committed, distributed, installed or executed in the game. Logs are
planning evidence, NOT proof of playable Game.exe acceptance.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from server.ruby_marshal import loads, text

PIN = "c59233bdbaac4fbfeca6aa01c7f05be628da2a92"
BASE = ("https://raw.githubusercontent.com/SocomSeal/The-PMon-World-Project/"
        + PIN + "/" + quote("The Pokémon World Project - Hoenn/Data", safe="/"))
KEYWORDS = re.compile(
    r"sootopolis|ever grande|league|elite four|sidney|phoebe|glacia|"
    r"drake|champion|hall of fame|victory road|seafloor|sky pillar|"
    r"origin|pacifidlog|underwater|route 12[5-9]|route 13[0-4]",
    re.I,
)
EVENTS = re.compile(
    r"juan|sidney|phoebe|glacia|drake|wallace|steven|rayquaza|"
    r"kyogre|groudon|archie|maxie|wally|crisis|puzzle|"
    r"weather|league|champion|ladder|exit|door|entrance|"
    r"submarine|grunts?|elite|teleport|waterfall|div(e|ing)|origin",
    re.I,
)

def read(name: str):
    with urlopen(BASE + "/" + name, timeout=35) as response:
        return loads(response.read())

def safe(value):
    try:
        return value if isinstance(value, str) else text(value)
    except (TypeError, UnicodeError):
        return repr(value)

def main():
    infos = read("MapInfos.rxdata")
    chosen = {}
    print("HOENN_STAGE10_SOURCE_PIN", PIN, flush=True)
    for mid, info in sorted(infos.items()):
        name = safe(info.attrs.get("@name", ""))
        if KEYWORDS.search(name) or mid in list(range(83, 100)) + list(range(146, 156)):
            print("S10_MAP", mid, repr(name), flush=True)
            if KEYWORDS.search(name) or 83 <= mid <= 99:
                chosen[mid] = name

    print("S10_EVENT_AUDIT_BEGIN", len(chosen), flush=True)
    for mid, name in chosen.items():
        try:
            obj = read(f"Map{mid:03}.rxdata")
        except Exception as err:
            print("S10_MISSING", mid, type(err).__name__, flush=True)
            continue
        evs = obj.attrs.get("@events", {})
        print("S10_SIZE", mid, repr(name), obj.attrs.get("@width"),
              obj.attrs.get("@height"), len(evs), flush=True)
        for event in evs.values():
            ev_name = safe(event.attrs.get("@name", ""))
            if not EVENTS.search(ev_name):
                continue
            transfers = set()
            page_count = len(event.attrs.get("@pages", []))
            for page in event.attrs.get("@pages", [])[:3]:
                for cmd in page.attrs.get("@list", []):
                    if cmd.attrs.get("@code") == 201:
                        params = cmd.attrs.get("@parameters", [])
                        if len(params) >= 4 and params[0] == 0:
                            transfers.add(tuple(params[:5]))
            print("S10_EVENT", mid, event.attrs.get("@x"), event.attrs.get("@y"),
                  repr(ev_name[:75]), "PAGES", page_count,
                  "WARP", sorted(transfers), flush=True)
    print("HOENN_STAGE10_SOURCE_AUDIT_COMPLETE", flush=True)

if __name__ == "__main__":
    main()
