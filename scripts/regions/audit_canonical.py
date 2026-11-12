"""Lossless, independent checks of the installed Kanto PBS against pinned FRLG.

Reads the unmodified source Essentials FRLG 1.1 and the disposable compiled
pilot. It never executes source event scripts, edits a ROM, or grants a reward.
The source is a FRLG adaptation, not proof of exact GBA Red/Green exclusives.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

from audit import ROOT, KANTO, json_file
from pbs import ENCOUNTER_TYPES, TRAINERS, read_blocks

def canonical_slot(raw, section, method):
    values=[x.strip() for x in raw.split("#",1)[0].split(",")]
    if len(values) not in (3,4) or not values[0].isdigit():
        raise ValueError(f"Unsupported PBS slot in [{section}]/{method}: {raw}")
    chance=int(values[0]); species=values[1]
    low=int(values[2]); high=int(values[3]) if len(values)==4 else low
    if not (1<=chance<=100 and species and 1<=low<=high<=100):
        raise ValueError(f"Invalid species/weight/inclusive level range in [{section}]: {raw}")
    return [chance,species,low,high]

def parse_methods(lines, section):
    methods={}
    active=None
    for raw in lines:
        values=[x.strip() for x in raw.split("#",1)[0].split(",")]
        if values[0].isdecimal():
            if active is None:raise ValueError(f"Encounter slot without method: [{section}]")
            methods[active]["slots"].append(canonical_slot(raw,section,active))
        else:
            active=values[0]
            if active not in ENCOUNTER_TYPES or active in methods or len(values)>2:
                raise ValueError(f"Unsupported or duplicate encounter method in [{section}]: {raw}")
            rate=int(values[1]) if len(values)==2 else None
            methods[active]={"step_chance":rate,"slots":[]}
    for method, table in methods.items():
        total=sum(row[0] for row in table["slots"])
        if not total:
            raise ValueError(f"Empty encounter method [{section}]/{method}")
        table["source_weight_total"]=total
    return methods

def source_to_dest(header, mapping):
    key,*variant=header.split(",")
    ident=int(key)
    if ident not in mapping:return None
    if len(variant)>1 or any(not n.isdecimal() for n in variant):
        raise ValueError(f"Invalid original encounter section header: [{header}]")
    return f'{mapping[ident]:03d}' + (f',{variant[0]}' if variant else "")

def audit(source:Path, pilot:Path):
    source=(source/"PBS")
    installed=(pilot/"PBS")
    map_manifest=json_file(KANTO)
    preview=set(map_manifest.get("preview_only",[]))
    pilot_info=json_file(pilot/"Kanto pilot.json")
    mapping={int(k):v for k,v in pilot_info["maps"].items()}
    active={key:value for key,value in mapping.items() if key not in preview}

    src_path=source/"encounters.txt"
    dst_path=installed/"encounters_kanto.txt"
    source_tables=read_blocks(src_path)
    installed_tables=read_blocks(dst_path)
    expected={}
    source_map_by_table={}
    for header, lines in source_tables.items():
        dest=source_to_dest(header,active)
        if dest is None: continue
        if dest in expected:raise ValueError(f"Duplicate translated encounter table: [{dest}]")
        expected[dest]=parse_methods(lines,header)
        source_map_by_table[dest]=header
    produced={header:parse_methods(lines,header) for header,lines in installed_tables.items()}
    if set(produced)!=set(expected):
        raise ValueError("Encounter import mismatch: missing "+str(sorted(set(expected)-set(produced)))+
                         "; foreign "+str(sorted(set(produced)-set(expected))))
    for header,methods in expected.items():
        if produced[header]!=methods:
            raise ValueError(f"Encounter table drift for [{source_map_by_table[header]}] -> [{header}]")
    if any(int(k.split(",")[0]) in {mapping[p] for p in preview} for k in produced):
        raise ValueError("A preview-only map was assigned wild encounters")

    src_trainer=read_blocks(source/"trainers.txt", TRAINERS)
    compiled=read_blocks(installed/"trainers_kanto.txt")
    if set(src_trainer)!=set(TRAINERS):
        raise ValueError("Pinned FRLG trainer source is incomplete: "+
                         str(sorted(set(TRAINERS)-set(src_trainer))))
    expected_trainer={}
    for original,(kind,name,version) in TRAINERS.items():
        dest=f"BLUE_KANTO_{kind},{name},{version}"
        if dest in expected_trainer:
            raise ValueError(f"Trainer identity collision: {original} -> {dest}")
        expected_trainer[dest]=[row.strip() for row in src_trainer[original]]
    if set(compiled)!=set(expected_trainer):
        raise ValueError("Original trainer identities drifted: missing "+str(sorted(set(expected_trainer)-set(compiled)))+
                         "; unexpected "+str(sorted(set(compiled)-set(expected_trainer))))
    for header,orig_lines in expected_trainer.items():
        if [row.strip() for row in compiled[header]]!=orig_lines:
            raise ValueError(f"FRLG trainer moves/stats/held items changed during import: [{header}]")

    per_map=Counter()
    distribution=Counter()
    method_counts=Counter()
    non_percent=[]
    range_count=0
    slots_count=0
    for imported,methods in expected.items():
        original=source_map_by_table[imported]
        per_map[original.split(",")[0]]+=1
        for method,table in methods.items():
            method_counts[method]+=1
            if table["source_weight_total"]!=100:
                non_percent.append([original,method,table["source_weight_total"]])
            for chance,species,low,high in table["slots"]:
                distribution[species]+=1
                range_count+=int(high>low)
                slots_count+=1
    return {
        "source": "Essentials FRLG 1.1 (pinned SHA256 archive), not official GBA exclusivity proof",
        "runtime_scripts_executed": False,
        "source_encounters_sha256": hashlib.sha256(src_path.read_bytes()).hexdigest(),
        "imported_encounters_sha256": hashlib.sha256(dst_path.read_bytes()).hexdigest(),
        "source_original_tables":len(source_tables),
        "active_imported_tables":len(produced),
        "preview_maps_kept_without_encounters":len(preview),
        "source_trainer_rosters_verified_exactly":len(expected_trainer),
        "species_with_active_encounters":len(distribution),
        "wild_slots_verified_exactly":slots_count,
        "inclusive_level_ranges":range_count,
        "methods":dict(sorted(method_counts.items())),
        "non_percent_weight_tables": non_percent,
        "validated_original_maps":dict(sorted(per_map.items(),key=lambda pair:int(pair[0]))),
        "independent_gba_firered_leafgreen_exclusivity_check":"PENDING",
        "credits_and_graphics_independent_rights_check":"PENDING",
    }

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,default=ROOT/".blue-work/frlg-source/Essentials FRLG")
    parser.add_argument("--pilot",type=Path,default=ROOT/".blue-work/kanto-pilot")
    parser.add_argument("--output",type=Path,default=ROOT/".blue-work/kanto-phase-15-audit.json")
    a=parser.parse_args()
    result=audit(a.source,a.pilot)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("KANTO_CANONICAL_AUDIT:"+json.dumps(result,ensure_ascii=True))

if __name__=="__main__":
    main()
