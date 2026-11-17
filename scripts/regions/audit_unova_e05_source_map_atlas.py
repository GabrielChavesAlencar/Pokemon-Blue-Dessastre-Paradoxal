#!/usr/bin/env python3
"""Verify source donor's 64-map atlas; does not imply geometry/rights verified."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ATLAS = ROOT / "data/regions/unova-e05-source-map-atlas.json"
OBSERVATION = ROOT / "data/regions/unova-e04-e05-observed-source.json"
SOURCE_SHA="ca6226a070026a8f269c927bfe9a30821b659e2629df26513be780fc34ceda35"
BIGGER={463:(67,44),464:(77,41),465:(109,64),466:(100,82),
        468:(150,200),490:(67,60),494:(73,28),495:(64,72)}


def fail(message):
    raise ValueError("UNOVA_E05_ATLAS_BLOQUEADO: " + message)


def validate(atlas, observation):
    if not isinstance(atlas,dict) or not isinstance(observation,dict):
        fail("documentos precisam ser objetos JSON")
    required={
        "schema":1,"region":"UNOVA","phase":"E05_ATLAS",
        "status":"DONOR_MAPINFO_AND_MAP_DIMENSION_INDEX_NO_INSTALL",
        "source_zip_sha256":SOURCE_SHA,"whole_donor_map_files":912,
        "unova_parent_map_files":64,"maps_with_20x15_dimensions":56,
        "maps_with_other_dimensions":8,"events_total":0,
        "dimensions_do_not_verify_tile_content":True,
        "may_import_assets":False,"native_map_ids_allocated":False,
        "game_or_saves_modified":False,
    }
    for key,val in required.items():
        if type(atlas.get(key)) is not type(val) or atlas[key]!=val:
            fail("campo falso ou incompleto: "+key)
    if atlas.get("source_evidence_run")!="https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44083797886":
        fail("referencia da coleta real ausente")
    if (observation.get("archive_sha256")!=SOURCE_SHA or
        observation.get("source_unova_map_dimensions_20x15")!=56 or
        observation.get("source_unova_map_dimensions_nondefault")!=8 or
        observation.get("source_unova_larger_map_ids")!=sorted(BIGGER) or
        observation.get("source_map_atlas")!="data/regions/unova-e05-source-map-atlas.json" or
        observation.get("source_map_tile_geometry_visually_verified") is not False):
        fail("observacao de origem nao confere com atlas")
    rows=atlas.get("maps")
    if not isinstance(rows,list) or len(rows)!=64:
        fail("exigidos 64 mapas")
    seen=set()
    normal=large=0
    for item in rows:
        if not isinstance(item,dict):
            fail("mapa malformado")
        mid=item.get("source_map_id")
        if type(mid) is not int or not 1<=mid<=99999 or mid in seen:
            fail("id de origem faltante/duplicado")
        seen.add(mid)
        for key in ("parent_source_map_id","width_tiles","height_tiles","event_count"):
            if type(item.get(key)) is not int:
                fail("campos inteiros obrigatorios")
        if (item["event_count"]!=0 or item.get("geometry_verified_visually") is not False
             or item.get("rights_verified") is not False
             or item.get("destination_map_id") is not None
             or item.get("game_exe_tested") is not False
             or item.get("source_region_context")!="Unova Region parent tree; not separately verified"):
            fail("mapa indevidamente aprovado")
        if not isinstance(item.get("name"),str) or not item["name"].strip():
            fail("nome de mapa ausente")
        dims=(item["width_tiles"],item["height_tiles"])
        if mid in BIGGER:
            if dims!=BIGGER[mid] or item.get("placeholder_dimensions_20x15") is not False:
                fail("dimensoes de mapa grande divergentes")
            large+=1
        elif dims==(20,15) and item.get("placeholder_dimensions_20x15") is True:
            normal+=1
        else:
            fail("metadado de dimensoes inesperado")
    if normal!=56 or large!=8:
        fail("contagem de dimensoes divergente")
    return {"schema":1,"region":"UNOVA","phase":"E05_ATLAS",
            "status":"SOURCED_MAP_DIMENSIONS_ONLY",
            "donor_branch_maps":len(rows),"maps_20x15":normal,
            "maps_larger":large,"events":0,
            "tiles_drawing_verified":False,"rights_verified":False,
            "may_install":False,"gameplay_verified":False}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--atlas",type=Path,default=ATLAS)
    p.add_argument("--observation",type=Path,default=OBSERVATION)
    args=p.parse_args(argv)
    try:
        for path in (args.atlas,args.observation):
            if path.is_symlink() or not path.is_file() or path.stat().st_size>200000:
                fail("evidencia nao existe/nao e segura")
        report=validate(json.loads(args.atlas.read_text("utf-8")),
                        json.loads(args.observation.read_text("utf-8")))
        print(json.dumps(report,indent=2,ensure_ascii=False))
        return 0
    except (ValueError,KeyError,OSError,TypeError) as exc:
        print(str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
