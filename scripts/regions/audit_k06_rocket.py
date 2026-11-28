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

# This is a read-only source witness. Foreign numeric switches, Ruby, dialogue,
# and event pages are never embedded in the playable import.
DEPENDENCY_MAPS={*range(117,125),129,131,132,133,134,135}
POSITIONS={(124,1),(129,52),(129,54),(131,9),(132,5),(134,1),(134,2),(134,3),
           (134,4),(134,6),(134,12),(134,21),(135,1),(135,2)}
CONDITION_FIELDS={
    "@switch1_valid": ("@switch1_id",),
    "@switch2_valid": ("@switch2_id",),
    "@variable_valid": ("@variable_id","@variable_value"),
    "@self_switch_valid": ("@self_switch_ch",),
}
BAG_SYMBOLS=re.compile(r"(?<!\w):(LIFT_?KEY|SILPH_?SCOPE|TEA|TM\d{2,3}|HM\d{2}|CUT)\b",re.I)
STOCK=re.compile(r'(?i)\bpbPokemonMart\s*\(\s*\[\s*((?::[A-Z][A-Z0-9_]*\s*,?\s*)+)\]')
KNOWN_CALLS=re.compile(r"(?<!\w)(TrainerBattle\.start|pbTrainerBattle|pbItemBall|pbReceiveItem|pbPokemonMart|"
                       r"pbCanUseCut|pbCut|pbBadge\w*|pbSetSelfSwitch|pbMoveRoute|pbSetEventTime|"
                       r"pbBattleAnimation|pbSet|pbGet|pbPushThisEvent)\s*\(")
FLAG_READS=re.compile(r"\$game_(switches|variables)\s*\[\s*(\d+)\s*\]")


def audit_conditions(condition):
    return {field:condition[field] for valid,fields in CONDITION_FIELDS.items() if condition.get(valid)
             for field in fields if field in condition}


def selectors(command):
    code, params = command["code"], command["parameters"]
    lengths={121:3,122:5,123:2,201:6}
    if code in lengths and len(params)>=lengths[code]:
        n=lengths[code]
        if all(type(val) is int for val in params[:n]):
            return {"numeric_control":params[:n]}
        if code==123 and params[0] in ("A","B","C","D") and type(params[1]) is int:
            return {"self_switch":params[:2]}
    if code==111 and params:
        kind=params[0]
        if kind in (0,1) and len(params)>=3 and all(type(v) is int for v in params[:5]):
            return {"native_condition":params[:5]}
        if kind==2 and len(params)==3 and params[1] in ("A","B","C","D") and type(params[2]) is int:
            return {"native_self_switch":params[:3]}
    if code==102 and params and isinstance(params[0],list):
        return {"option_count":len(params[0])}
    if code==402 and params and type(params[0]) is int:
        return {"option_index":params[0]}
    return {}


def progression_witness(report):
    # Include the Game Corner's full control graph, whose poster can be named
    # generically. Discard dialogue and strings, even from conditional pages.
    out=[]
    for sid in sorted(DEPENDENCY_MAPS):
        for event in report[str(sid)]["events"]:
            for page in event["pages"]:
                scripts=list(page_scripts(page))
                calls={m for _,_,line in scripts for m in KNOWN_CALLS.findall(line)}
                conditions=audit_conditions(page["condition"])
                effects=[dict(op=c["code"],indent=c["indent"],**r) for c in page["commands"] if (r:=selectors(c))]
                symbols=sorted({key.upper() for _,_,line in scripts for key in BAG_SYMBOLS.findall(line)})
                flags=sorted({(kind,int(idx)) for _,_,line in scripts for kind,idx in FLAG_READS.findall(line)})
                stocks=[re.findall(r":([A-Z][A-Z0-9_]*)",row,re.I) for _,_,line in scripts for row in STOCK.findall(line)]
                if (sid,event["id"]) not in POSITIONS and not (effects or conditions or calls or symbols or flags):
                    continue
                out.append({"source":sid,"event":event["id"],"at":event["xy"],"page":page["page"],
                            "trigger":page["trigger"],"through":page["through"],"conditions":conditions,
                            "effects":effects,"calls":sorted(calls),"item_symbols":symbols,
                            "foreign_flag_reads":flags,"mart_stock":stocks})
    if not POSITIONS<={(row["source"],row["event"]) for row in out}:
        raise ValueError("Expected Celadon progression anchors missing from source")
    return out


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
            "maps":maps,"warps":warps,"actors":actors,"progression":progression_witness(report),
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
