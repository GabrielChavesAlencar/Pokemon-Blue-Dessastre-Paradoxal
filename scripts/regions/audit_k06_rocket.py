"""Read-only K06 intake: native Celadon connections, guard anchors and trainer identities."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from audit import KANTO, ROOT, inventory, json_file
from audit_cerulean_interiors import inspect_events, transfers
from audit_k04_rock_tunnel import read_blocks
from audit_k05_lavender import page_scripts
from k04_corridor import publication_catalog

ADD=(*range(125,130),*range(131,136))
EXISTING=tuple(range(107,125))
NEAR={93,107,111,114,168}
KEYS=re.compile(r"(?i)\b(?:LIFT_?KEY|SILPH_?SCOPE|GIOVANNI|RAINBOW|CUT|TM28|POSTER|GAMECORNER|HIDEOUT)\b")
CALL=re.compile(r'(?:TrainerBattle\.start|pbTrainerBattle)\(\s*:(\w+)\s*,\s*"([^"\r\n]+)"(?:\s*,\s*(\d+)(?=\s*[,)]))?')
ROCKET=re.compile(r"(?:POSTER|LIFT_?KEY|SILPH_?SCOPE|GIOVANNI|TEAMROCKET|ELEVATOR)",re.I)


def source_connections(path,scope):
    out=[]
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        text=raw.split("#",1)[0].strip()
        if not text:
            continue
        a,side,o,b,reverse,z=map(str.strip,text.split(","))
        if {int(a),int(b)} & scope:
            out.append([int(a),side,int(o),int(b),reverse,int(z)])
    return out


def summarize(source,catalog):
    if publication_catalog(catalog["maps"])!=178:
        raise ValueError("K06 read-only intake requires the exact published K05 manifest")
    active={int(k) for k in catalog["maps"]}
    if set(ADD)&active:
        raise ValueError("K06 source-only audit must not activate new maps")
    infos,files=inventory(source)
    present=set(EXISTING)&active&infos.keys()&files.keys()
    if not set(ADD)<=infos.keys()&files.keys() or not {107,111,114,115,117,124}<=present:
        raise ValueError("K06 source or audited Celadon baseline map is absent")
    scope=present|set(ADD)
    report=inspect_events(source,sorted(scope))
    pbs=read_blocks(source/"PBS/trainers.txt")
    actors,warps,maps=[],[],[]
    for sid in sorted(scope):
        m=report[str(sid)]
        maps.append({"source":sid,"name":m["name"],"dimensions":m["dimensions"],
                     "sha256":m["source_sha256"],"events":len(m["events"]),
                     "currently_active":sid in active,"preview":sid in catalog["preview_only"]})
        for ev in m["events"]:
            warps.extend({"source":sid,"event":ev["id"],"at":ev["xy"],**w,
                          "destination_in_k06":w["destination"] in scope}
                         for w in transfers(ev))
            anchor=bool(ROCKET.search(ev["name"]))
            for page in ev["pages"]:
                scripts=list(page_scripts(page))
                keys=sorted({m.group().upper() for _,_,s in scripts for m in KEYS.finditer(s)})
                calls=sorted({(kind,name,version) for _,_,s in scripts for kind,name,version in CALL.findall(s)})
                if not (anchor or keys or calls):
                    continue
                profiles={}
                for kind,name,version in calls:
                    key=f"{kind},{name}"
                    identity=f"{key},{version}" if version else key
                    blocks=pbs.get(identity,[])
                    profiles[identity]={"matching_rows":len(blocks),"teams":[re.findall(
                        r"(?m)^Pokemon\s*=\s*([A-Za-z0-9_]+)\s*,\s*(\d+)\s*$",row)
                        for row in blocks]}
                actors.append({"source":sid,"event":ev["id"],"page":page["page"],"at":ev["xy"],
                   "trigger":page["trigger"],"story_anchor":anchor,"references":keys,
                   "profiles":profiles,"opcodes":sorted({o["code"] for o in page["commands"]}),
                   "active_conditions":{k:v for k,v in page["condition"].items() if k.endswith("_valid") and v}})
    return {"status":"K06_SOURCE_ONLY","published":False,"native_gameplay":False,
            "maps":maps,"warps":warps,"actors":actors,
            "connections":source_connections(source/"PBS/map_connections.txt",scope|NEAR),
            "deferred": ["Marowak, Fuji and Poké Flute (K07)","Route 12 (K07)"]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=ROOT/".blue-work/frlg-source/Essentials FRLG")
    p.add_argument("--output",type=Path,default=ROOT/"k06-source-receipts/kanto-k06-source.json")
    a=p.parse_args()
    report=summarize(a.source,json_file(KANTO))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("KANTO_K06_SOURCE_ONLY_OK:"+json.dumps({k:len(report[k]) for k in ("maps","warps","actors","connections")}))


if __name__=="__main__":
    main()
