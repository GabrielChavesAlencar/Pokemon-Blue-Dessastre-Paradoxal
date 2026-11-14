#!/usr/bin/env python3
"""Read-only pinned Hoenn source PBS audit; never stores donor source in Git."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request,urlopen

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from pilot_hoenn import SOURCE_MAPS,UPSTREAM,LAND_ENCOUNTERS,CAVE_ENCOUNTERS
from hoenn_qa_phase3 import parse_reference_encounters,assemble_encounters

BASE=("https://raw.githubusercontent.com/SocomSeal/The-PMon-World-Project/"
      + UPSTREAM + "/" + quote("The Pokémon World Project - Hoenn/PBS",safe="/"))
BLOBS={
    "encounters.txt":"c915482b7206a6fa46380f301ef099ce07b81677",
    "trainers_region_03.txt":"e328da424ec8ff71bb5f658a44425caebd58b200",
}


def get_pinned_pbs(filename: str) -> str:
    if filename not in BLOBS:
        raise ValueError("Fonte PBS não autorizada")
    request=Request(BASE+"/"+filename,headers={"User-Agent":"Blue-Hoenn-QA3-ReadOnly"})
    with urlopen(request,timeout=60) as response:
        data=response.read(1_500_001)
    if len(data)>1_500_000:
        raise ValueError(f"Fonte PBS acima do limite: {filename}")
    digest=hashlib.sha1(f"blob {len(data)}\0".encode("ascii")+data).hexdigest()
    if digest!=BLOBS[filename]:
        raise ValueError(f"Fonte Hoenn diverge da revisão fixa: {filename}")
    return data.decode("utf-8-sig")


def main() -> int:
    source=get_pinned_pbs("encounters.txt")
    trainers=get_pinned_pbs("trainers_region_03.txt")
    profiles,reference=parse_reference_encounters(source,set(SOURCE_MAPS))
    mapping={mid:700+i for i,mid in enumerate(SOURCE_MAPS)}
    final,merged=assemble_encounters(profiles,mapping,
                                     LAND_ENCOUNTERS,CAVE_ENCOUNTERS)
    trainer_headers=sum(bool(re.match(r"^\[[A-Z][A-Z0-9_]+,[^]]+\]$",line.strip()))
                        for line in trainers.splitlines())
    if not trainer_headers:
        raise ValueError("PBS doador de treinadores não contém equipes")
    for method in ("Water","OldRod","GoodRod","SuperRod","RockSmash"):
        if merged["added_by_method"].get(method,0)<1:
            raise ValueError(f"Faltou método auditado de Hoenn: {method}")
    if len(final)==0:
        raise ValueError("PBS gerado de Hoenn vazio")
    result={
        "region":"HOENN","qa_phase":"03/12","pinned_commit":UPSTREAM,
        "source_default_maps_installed":reference["source_default_maps"],
        "source_alternate_profiles_ignored":len(reference["alternate_profiles_not_activated"]),
        "source_nonstandard_weight_tables_normalized":len(reference["normalized_weights"]),
        "native_blue_land_cave_profiles_kept":merged["authored_method_profiles_preserved"],
        "additional_method_profiles_from_source":merged["new_default_profiles_installed"],
        "added_by_method":merged["added_by_method"],
        "donor_trainer_pbs_profiles_for_manual_mapping":trainer_headers,
        "game_exe_tested":False,"trainer_npc_positions_verified":False,
        "copyrighted_assets_committed":False,
    }
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print("HOENN_QA3_PINNED_ENCOUNTERS_OK")
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (OSError,ValueError,UnicodeError,KeyError) as exc:
        print("HOENN_QA3_SOURCE_AUDIT_BLOCKED:",str(exc),file=sys.stderr)
        raise SystemExit(2)
