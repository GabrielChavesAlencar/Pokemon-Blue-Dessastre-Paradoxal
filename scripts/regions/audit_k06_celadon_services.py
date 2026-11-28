"""Record Celadon's department store and four interiors without exporting donor code."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from audit import KANTO, ROOT, json_file
from audit_cerulean_interiors import inspect_events, transfers
from audit_k06_rocket import audit_conditions, selectors
from k04_corridor import publication_catalog

STORE=tuple(range(117,124))
INTERIORS=(125,126,127,128)
SCOPE=(114,*STORE,*INTERIORS)
DEFERRED={124,129,130,131,132,133,134,135}
CITY_DOORS={4:125,14:117,15:117,24:128,26:127,27:126,34:128}
MART_PREFIX=re.compile(r"(?<!\w)pbPokemonMart\s*\(")
MART_LIST=re.compile(r"\s*\[([^\]]*)\]")
SYMBOL=re.compile(r":([A-Z][A-Z0-9_]*)")
RECEIVE=re.compile(r"(?<!\w)(pbReceiveItem|pbItemBall|pbReceivePokemon|pbAddPokemon)\s*\(?\s*(:[A-Z][A-Z0-9_]*)")
TYPED_ARGS=re.compile(r"(?<!\w)(pbAddPokemon|pbReceiveItem|has\?|remove|add)\s*\(\s*:([A-Z][A-Z0-9_]*)(?:\s*,\s*([0-9]{1,3})(?![0-9]))?")
HOUSE_CALL=re.compile(r"(?<!\w)(pbSetSelfSwitch|pbChoosePokemon|pbChooseItem|pbMessageChooseNumber|pbNicknameAndStore|has\?|remove|add)\s*\(")


def script_groups(commands):
    """Reassemble contiguous Ruby continuations; ignore messages and comments."""
    current=None
    for command in commands:
        kind=command["code"]
        args=command["parameters"]
        if kind==655 and current is not None and isinstance(args[0] if args else None,str):
            current += "\n"+args[0]
            continue
        if current is not None:
            yield current
        current=None
        if kind==355 and args and isinstance(args[0],str):
            current=args[0]
        elif kind==111 and len(args)==2 and args[0]==12 and isinstance(args[1],str):
            yield args[1]
    if current is not None:
        yield current


def typed_services(code):
    stocks=[]
    for prefix in MART_PREFIX.finditer(code):
        literal=MART_LIST.match(code,prefix.end())
        if literal is None:
            stocks.append({"literal":False,"items":[]})
            continue
        tokens=[part.strip() for part in literal[1].split(",") if part.strip()]
        decoded=[SYMBOL.fullmatch(x) for x in tokens]
        if tokens and all(decoded):
            stocks.append({"literal":True,"items":[x[1] for x in decoded]})
        else:
            stocks.append({"literal":False,"items":[]})
    return {"shops":stocks,
            "rewards":[{"operation":call,"item_or_species":item[1:]} for call,item in RECEIVE.findall(code)],
            "item_arguments":[{"operation":op,"item_or_species":item,"quantity":int(qty) if qty else None}
                              for op,item,qty in TYPED_ARGS.findall(code)],
            "interaction_calls":sorted(set(HOUSE_CALL.findall(code)))}


# One observed vending-machine page. Read only typed amounts and opcodes;
# never persist source dialogue, choices or expressions.
MONEY_EXPRESSION = re.compile(
    r"\$(?:player|Trainer)\.money\s*(>=|<=|==|>|<|-=|\+=|=)\s*([0-9]{1,6})(?![0-9])")


def vending_controls(page, scripts):
    out = []
    for cmd in page["commands"]:
        code, args = cmd["code"], cmd["parameters"]
        if (code == 125 and len(args) == 3 and args[0] in (0, 1)
                and args[1] == 0 and type(args[2]) is int and 0 < args[2] <= 1_000_000):
            out.append({"operation": "native_gold_change", "indent": cmd["indent"],
                        "operand": args[2], "increase": args[0] == 0})
        if (code == 111 and len(args) == 3 and args[0] == 7
                and type(args[1]) is int and 0 < args[1] <= 1_000_000 and args[2] in (0, 1)):
            out.append({"operation": "native_gold_condition", "indent": cmd["indent"],
                        "operand": args[1], "at_least": args[2] == 0})
    out += [{"operation": "typed_money_operand", "operator": op, "amount": int(n)}
            for script in scripts for op, n in MONEY_EXPRESSION.findall(script)]
    return out


def summarize(source,catalog):
    old=set(map(int,catalog["maps"]))
    if publication_catalog(catalog["maps"])!=178 or not {114,*STORE}<=old or old&set(INTERIORS):
        raise ValueError("Celadon interiors require the exact published approach baseline")
    if set(STORE)-set(catalog["preview_only"]):
        raise ValueError("The department store is no longer a protected preview")
    pages=inspect_events(source,list(SCOPE))
    warps,services,summary=[],[],[]
    for sid in SCOPE:
        region=pages[str(sid)]
        summary.append({"source":sid,"sha256":region["source_sha256"],"dimensions":region["dimensions"]})
        for event in region["events"]:
            eid=event["id"]
            for warp in transfers(event):
                if sid==114 and eid not in CITY_DOORS:
                    continue
                if warp["destination"] not in SCOPE:
                    raise ValueError(f"Celadon interior opens an unapproved map: {sid}/{eid}")
                warps.append({"source":sid,"event":eid,"at":event["xy"],**warp})
            for page in event["pages"]:
                effects=[{"op":op["code"],"indent":op["indent"],**typed} for op in page["commands"]
                         if (typed:=selectors(op))]
                scripts=list(script_groups(page["commands"]))
                parts=[typed_services(code) for code in scripts]
                shops=[x for part in parts for x in part["shops"]]
                rewards=[x for part in parts for x in part["rewards"]]
                calls=sorted({x for part in parts for x in part["interaction_calls"]})
                if shops or rewards or (sid in {122,123,*INTERIORS} and (effects or calls)):
                    services.append({"source":sid,"event":eid,"at":event["xy"],"page":page["page"],
                                     "trigger":page["trigger"],"conditions":audit_conditions(page["condition"]),
                                     "effects":effects,"shops":shops,"rewards":rewards,"calls":calls,
                                     "item_arguments":[arg for part in parts for arg in part["item_arguments"]],
                                     **({"money":vending_controls(page,scripts)} if (sid,eid)==(122,2) else {})})
    if {x["event"]:x["destination"] for x in warps if x["source"]==114}!=CITY_DOORS:
        raise ValueError("Native Celadon entrances changed")
    if {x["destination"] for x in warps if x["source"]==123 and x["event"]==1}!=set(range(117,122)):
        raise ValueError("Native department store elevator returns changed")
    if not all(any(x["source"]==sid and x["destination"]==114 for x in warps) for sid in INTERIORS):
        raise ValueError("Celadon interior has no original exit")
    return {"status":"K06_CELADON_INTERIORS_SOURCE_ONLY","maps":summary,"warps":warps,"services":services,
            "deferred":sorted(DEFERRED),"map_ids_allocated":0,"game_files_written":False}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",type=Path,default=ROOT/".blue-work/frlg-source/Essentials FRLG")
    p.add_argument("--output",type=Path,default=ROOT/"k06-services-receipts/celadon-services.json")
    args=p.parse_args()
    evidence=summarize(args.source,json_file(KANTO))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(evidence,indent=2)+"\n",encoding="utf8")
    print("KANTO_K06_CELADON_SERVICES_SOURCE_OK:"+json.dumps(
        {k:len(evidence[k]) for k in ("maps","warps","services")}))
