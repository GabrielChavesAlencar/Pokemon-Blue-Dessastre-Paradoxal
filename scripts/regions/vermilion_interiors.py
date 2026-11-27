"""K03-B: derive the four native Vermilion interiors from the pinned donor.

Only inert Map/Event/command metadata is read. Never execute a donor script.
Reject missing/ambiguous rewards or transfers rather than guess a coordinate.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from audit import ROOT, inventory, load
from server.ruby_marshal import text

INTERIORS = {68,69,70,71}
ITEMS = {"BIKEVOUCHER","OLDROD"}
GIFT = re.compile(r"\s*(?:pbReceiveItem|\$bag\.add)\s*\(\s*:(BIKEVOUCHER|OLDROD)\s*(?:,\s*1\s*)?\)\s*")

def inspect_source(source: Path):
    infos, files = inventory(source)
    rows = {}
    rewards = {}
    for mid in (64,*sorted(INTERIORS)):
        m = load(files[mid]).attrs
        entries = []
        for eid,event in sorted(m["@events"].items()):
            ev = event.attrs
            warps, gifts, hints = set(), set(), set()
            for page in ev["@pages"]:
                for op in page.attrs["@list"]:
                    c = op.attrs
                    args = c["@parameters"]
                    if c["@code"] == 201 and len(args) >= 6 and args[0] == 0:
                        warps.add(tuple(args[1:4]))
                    if c["@code"] in (355,655,111):
                        for raw in args:
                            if not isinstance(raw,(bytes,str)):
                                continue
                            value = text(raw)
                            match = GIFT.fullmatch(value)
                            if match:
                                gifts.add(match[1])
                            if any(key in value.upper() for key in ITEMS):
                                hints.update(key for key in ITEMS if key in value.upper())
            row = {"event":eid,"name":text(ev["@name"]),"xy":[ev["@x"],ev["@y"]],
                   "warps":sorted(warps),"gift":sorted(gifts),"item_mentions":sorted(hints)}
            entries.append(row)
            if mid in INTERIORS and gifts:
                if len(gifts) != 1 or not ev["@pages"][0].attrs["@graphic"].attrs["@character_name"]:
                    raise ValueError(f"K03-B ambiguous/non-NPC reward {mid}/{eid}")
                rewards[mid,eid] = next(iter(gifts))
        rows[mid] = {"name":text(infos[mid].attrs["@name"]),
                     "dimensions":[m["@width"],m["@height"]],"events":entries}
        print("KANTO_K03B_SOURCE_MAP:" + json.dumps({"map":mid,**rows[mid]},ensure_ascii=True),flush=True)
    for mid in INTERIORS:
        doors = [(e["event"],w) for e in rows[64]["events"] for w in e["warps"] if w[0] == mid]
        returns = [(e["event"],w) for e in rows[mid]["events"] for w in e["warps"] if w[0] == 64]
        if len(doors) != 1 or len(returns) != 1:
            raise ValueError(f"K03-B expected unique original door/return {mid}: {doors!r}/{returns!r}")
    if sorted(rewards.values()) != sorted(ITEMS):
        raise ValueError(f"K03-B expected exactly one source voucher and rod gift: {rewards!r}")
    print("KANTO_K03B_SOURCE_IDENTITY_OK:"+json.dumps([[m,e,i] for (m,e),i in rewards.items()]),flush=True)
    return {"maps":rows,"rewards":rewards}

if __name__ == "__main__":
    inspect_source(ROOT / ".blue-work/frlg-source/Essentials FRLG")
