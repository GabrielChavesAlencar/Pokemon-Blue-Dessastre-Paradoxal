"""Independent, lossless PBS comparison with the SHA256-pinned FRLG source.

This source kit lists explicit allowed levels in each encounter slot (it is NOT
the vanilla Essentials min/max syntax). The pilot compiler represents these as
ranges when consecutive and exact integer-weight single-level slots otherwise.
No foreign scripts are executed. An FRLG fan adaptation is not definitive
evidence of official FireRed/LeafGreen version exclusivities.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

from audit import ROOT, KANTO, json_file
from pbs import ENCOUNTER_TYPES, TRAINERS, ENCOUNTER_REVIEW_SOURCE_IDS, read_blocks


def read_slot(raw, section, method, source_explicit):
    fields=[v.strip() for v in raw.split("#",1)[0].split(",")]
    if len(fields)<3 or not fields[0].isdecimal():
        raise ValueError(f"Invalid PBS slot [{section}]/{method}: {raw}")
    weight=int(fields[0])
    species=fields[1]
    if not species or weight<1 or weight>100:
        raise ValueError(f"Invalid species/weight [{section}]/{method}: {raw}")
    levels=[int(n) for n in fields[2:]]
    if not levels or any(not 1<=level<=100 for level in levels):
        raise ValueError(f"Invalid level list [{section}]/{method}: {raw}")
    if not source_explicit:
        if len(levels) != 2 or levels[0]>levels[1]:
            raise ValueError(f"Compiled PBS must specify inclusive min/max: {raw}")
        levels=list(range(levels[0],levels[1]+1))
    return weight,species,levels


def parse_methods(lines, section, source_explicit):
    methods={}
    active=None
    for raw in lines:
        fields=[s.strip() for s in raw.split("#",1)[0].split(",")]
        if fields[0].isdecimal():
            if active is None:
                raise ValueError(f"Encounter without a method [{section}]")
            methods[active]["slots"].append(read_slot(raw,section,active,source_explicit))
        else:
            active=fields[0]
            if active not in ENCOUNTER_TYPES or active in methods or len(fields)>2:
                raise ValueError(f"Unsupported/duplicate method [{section}]: {raw}")
            rate=int(fields[1]) if len(fields)==2 else None
            methods[active]={"step_chance":rate,"slots":[]}
    for method, table in methods.items():
        total=sum(weight for weight,_,_ in table["slots"])
        if not total:
            raise ValueError(f"Empty encounter method [{section}]/{method}")
        table["weight_total"]=total
    return methods


def weighted_distribution(method):
    total=method["weight_total"]
    frequencies=defaultdict(Fraction)
    for weight,species,levels in method["slots"]:
        for level in levels:
            frequencies[(species,level)]+=Fraction(weight,total*len(levels))
    return dict(frequencies)


def source_to_dest(header, mapping):
    key,*variant=header.split(",")
    ident=int(key)
    if ident not in mapping:return None
    if len(variant)>1 or any(not v.isdecimal() for v in variant):
        raise ValueError(f"Unknown source encounter version [{header}]")
    return f"{mapping[ident]:03d}"+(f",{variant[0]}" if variant else "")


def audit(source:Path,pilot:Path):
    source=source/"PBS"
    installed=pilot/"PBS"
    manifest=json_file(KANTO)
    preview=set(manifest.get("preview_only",[]))
    info=json_file(pilot/"Kanto pilot.json")
    mapping={int(key):value for key,value in info["maps"].items()}
    active={key:value for key,value in mapping.items()
            if key not in preview and key not in ENCOUNTER_REVIEW_SOURCE_IDS}

    original_file=source/"encounters.txt"
    compiled_file=installed/"encounters_kanto.txt"
    original=read_blocks(original_file)
    compiled=read_blocks(compiled_file)
    expected={}
    source_by_dest={}
    for header,lines in original.items():
        translated=source_to_dest(header,active)
        if translated is None:
            continue
        if translated in expected:
            raise ValueError(f"Encounter map/version collision: [{translated}]")
        expected[translated]=parse_methods(lines,header,True)
        source_by_dest[translated]=header
    produced={head:parse_methods(lines,head,False) for head,lines in compiled.items()}
    if set(produced)!=set(expected):
        raise ValueError("Encounter tables differ: missing "+str(sorted(set(expected)-set(produced)))+
                         "; unexpected "+str(sorted(set(produced)-set(expected))))
    for header, source_methods in expected.items():
        dest_methods=produced[header]
        if set(source_methods)!=set(dest_methods):
            raise ValueError(f"Encounter methods changed in [{header}]")
        for method, original_data in source_methods.items():
            new_data=dest_methods[method]
            if original_data["step_chance"]!=new_data["step_chance"]:
                raise ValueError(f"Encounter step chance was modified [{header}]/{method}")
            if weighted_distribution(original_data)!=weighted_distribution(new_data):
                raise ValueError(f"Species, weight, or allowed level changed [{header}]/{method}")
    preview_ids={mapping[n] for n in preview}
    if any(int(key.split(",")[0]) in preview_ids for key in produced):
        raise ValueError("A geometry-only map received wild encounters")

    original_trainers=read_blocks(source/"trainers.txt", TRAINERS)
    actual_trainers=read_blocks(installed/"trainers_kanto.txt")
    if set(original_trainers)!=set(TRAINERS):
        raise ValueError("Missing original trainer identity: "+
                         str(sorted(set(TRAINERS)-set(original_trainers))))
    expected_trainers={}
    for old,(kind,name,version) in TRAINERS.items():
        target=f"BLUE_KANTO_{kind},{name},{version}"
        if target in expected_trainers:
            raise ValueError(f"Trainer ID collision: {old} -> {target}")
        expected_trainers[target]=[line.strip() for line in original_trainers[old]]
    # The original source teams are verified byte-for-byte as before.
    # Full Power rematches are distinct, explicitly-authored version IDs.
    # Validate their exact content against the 15-profile manifest instead
    # of misclassifying these new sections as source-trainer drift.
    fp_manifest = json_file(ROOT / "data/kanto-full-power.json")
    expected_full_power = {
        f"BLUE_KANTO_{entry['kind']},{entry['name']},{entry['version']+100}":
            [f"Pokemon = {ident},{level}" for ident,level in
             zip(entry["species"],entry["levels"])]
        for entry in fp_manifest["teams"]
    }
    if set(actual_trainers)!=set(expected_trainers)|set(expected_full_power):
        raise ValueError("Trainer catalog drift: missing "+
                         str(sorted((set(expected_trainers)|set(expected_full_power))-set(actual_trainers)))+
                         "; added "+str(sorted(set(actual_trainers)-
                         (set(expected_trainers)|set(expected_full_power)))))
    for header, lines in expected_full_power.items():
        if [line.strip() for line in actual_trainers[header]] != lines:
            raise ValueError(f"Full Power team differs from reviewed manifest: [{header}]")
    for header,source_lines in expected_trainers.items():
        if [line.strip() for line in actual_trainers[header]]!=source_lines:
            raise ValueError(f"Trainer species/level/move/item drift: [{header}]")

    original_slots=0
    compiled_slots=0
    explicit_gaps=0
    collapsed_ranges=0
    unique_species=set()
    method_counts=Counter()
    source_non_100=[]
    map_counts=Counter()
    versioned_tables=0
    for dest,methods in expected.items():
        head=source_by_dest[dest]
        map_counts[head.split(",")[0]]+=1
        versioned_tables+=int("," in head)
        for method,table in methods.items():
            method_counts[method]+=1
            if table["weight_total"]!=100:
                source_non_100.append([head,method,table["weight_total"]])
            original_slots+=len(table["slots"])
            compiled_slots+=len(produced[dest][method]["slots"])
            for _,species,levels in table["slots"]:
                unique_species.add(species)
                contiguous=levels==list(range(levels[0],levels[-1]+1))
                collapsed_ranges+=int(contiguous and len(levels)>1)
                explicit_gaps+=int(not contiguous)
    return {
        "source":"Essentials FRLG 1.1, pinned archive; GBA version exclusivity not independently proven",
        "source_scripts_executed":False,
        "source_encounter_file_sha256":hashlib.sha256(original_file.read_bytes()).hexdigest(),
        "compiled_encounter_file_sha256":hashlib.sha256(compiled_file.read_bytes()).hexdigest(),
        "source_original_encounter_tables":len(original),
        "active_source_tables_imported":len(expected),
        "variant_tables_imported":versioned_tables,
        "source_slots":original_slots,
        "compiled_exact_distribution_slots":compiled_slots,
        "contiguous_source_level_lists_collapsed":collapsed_ranges,
        "discontinuous_or_repeated_level_lists_preserved_exactly":explicit_gaps,
        "species_with_active_encounters":len(unique_species),
        "method_tables":dict(sorted(method_counts.items())),
        "source_non_100_relative_weight_tables":source_non_100,
        "trainer_source_rosters_verified_exactly":len(expected_trainers),
        "author_owned_full_power_rosters_verified":len(expected_full_power),
        "preview_maps_kept_without_encounters":len(preview),
        "source_maps_with_ambiguous_encounters_kept_disabled":sorted(ENCOUNTER_REVIEW_SOURCE_IDS),
        "audited_source_map_tables":dict(sorted(map_counts.items(),key=lambda p:int(p[0]))),
        "independent_gba_red_green_exclusivity_check":"PENDING",
        "independent_sprites_sounds_rights_check":"PENDING",
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,default=ROOT/".blue-work/frlg-source/Essentials FRLG")
    parser.add_argument("--pilot",type=Path,default=ROOT/".blue-work/kanto-pilot")
    parser.add_argument("--output",type=Path,default=ROOT/".blue-work/kanto-phase-15-audit.json")
    args=parser.parse_args()
    report=audit(args.source,args.pilot)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("KANTO_CANONICAL_AUDIT:"+json.dumps(report,ensure_ascii=True))


if __name__=="__main__":
    main()
