"""Inventory source-only encounter tables before applying any migration.

The editable FRLG kit uses explicit per-slot level lists. Duplicate method
headers and source tables with unusual weights are reported, not normalized.
"""
import argparse
import json
from collections import Counter
from pathlib import Path

from audit import ROOT,KANTO,json_file
from pbs import ENCOUNTER_TYPES,read_blocks


def audit(source):
    manifest=json_file(KANTO)
    active={int(k) for k in manifest["maps"]}-set(manifest["preview_only"])
    tables=read_blocks(source/"PBS/encounters.txt")
    count=Counter()
    problem=[]
    all_entries=[]
    for key,lines in tables.items():
        map_id=int(key.split(",")[0])
        if map_id not in active:
            continue
        method=None
        used=set()
        for line in lines:
            fields=[x.strip() for x in line.split("#",1)[0].split(",")]
            if fields[0].isdigit():
                if method is None:
                    problem.append({"map":key,"error":"slot before method","line":line})
                else:
                    count[method]+=1
                    levels=[int(x) for x in fields[2:]]
                    if len(levels)>1 and levels!=list(range(levels[0],levels[-1]+1)):
                        all_entries.append({"map":key,"method":method,"weight":int(fields[0]),
                                            "species":fields[1],"levels":levels[:60]})
            else:
                method=fields[0]
                if method in used:
                    problem.append({"map":key,"error":"duplicate method","method":method,
                                    "line":line})
                if method not in ENCOUNTER_TYPES:
                    problem.append({"map":key,"error":"unknown method","method":method})
                used.add(method)
    return {"active_tables":len({h for h in tables if int(h.split(",")[0]) in active}),
            "slot_counts_by_method":dict(sorted(count.items())),
            "problems":problem,"nonconsecutive_samples":all_entries[:40],
            "nonconsecutive_total":len(all_entries)}


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source",type=Path,default=ROOT/".blue-work/frlg-source/Essentials FRLG")
    p.add_argument("--output",type=Path,default=ROOT/".blue-work/kanto-phase-15-source-audit.json")
    a=p.parse_args()
    r=audit(a.source)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+"\n",encoding="utf8")
    print("KANTO_SOURCE_ENCOUNTERS:"+json.dumps(r,ensure_ascii=True))


if __name__=="__main__":
    main()
