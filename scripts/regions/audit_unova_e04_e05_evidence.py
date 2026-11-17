#!/usr/bin/env python3
"""Validate recorded real donor-source observations without approving gameplay.

This document is an evidence snapshot from GitHub Actions, NOT independent
cryptographic attestation from the fangame author and not an asset license.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DEFAULT=ROOT/"data/regions/unova-e04-e05-observed-source.json"
HEX=re.compile(r"[0-9a-f]{64}\Z")

EXPECTED={
    "schema":1,
    "region":"UNOVA",
    "phase":"E04_E05",
    "status":"DONOR_SOURCE_AUDITED_GEOMETRY_ONLY_NOT_INSTALLED",
    "narrative_target":"WHITE_BW",
    "source_published_by_author":"https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr/",
    "mediafire_source_url":"https://www.mediafire.com/file/tq5w0in2xt2peb1/Pokemon_World_V18.zip/file",
    "provider_filename":"Pokemon World V18.zip",
    "source_wrapper":"pokemon journeys v18",
    "archive_size_bytes":208057674,
    "archive_sha256":"ca6226a070026a8f269c927bfe9a30821b659e2629df26513be780fc34ceda35",
    "source_sha256_published_by_author":False,
    "source_bytes_committed_to_git":False,
    "credits_provider_url":"https://www.mediafire.com/file/gdtsjg5lbnstzo1/Credits.txt/file",
    "credits_size_bytes":2425,
    "credits_sha256":"42433e84a3bb8d462ce86d7a7245a23fefe7602ba707f3ea6139aefe4aff5240",
    "credits_line_count":174,
    "credits_are_permission":False,
    "mapinfos_sha256":"a5de4d870ae08aa3730942496734c7a0917505a6d435ff178ce5a10f73fc6495",
    "all_donor_map_files":912,
    "all_donor_mapinfo_entries":911,
    "unova_parent_source_map_id":32,
    "unova_parent_map_files":64,
    "unova_parent_maps_parsed":64,
    "unova_parent_maps_unparsed":0,
    "unova_parent_event_containers":0,
    "unova_parent_script_command_count":0,
    "source_unova_map_dimensions_20x15":56,
    "source_unova_map_dimensions_nondefault":8,
    "source_map_atlas":"data/regions/unova-e05-source-map-atlas.json",
    "source_map_tile_geometry_visually_verified":False,
    "audit_20x15_not_proof_of_blank_map":True,
    "source_area_matches_inside_unova_parent":20,
    "source_area_name_matches_outside_unova_parent":19,
    "symbolic_areas_without_same_name":35,
    "symbolic_areas_total":74,
    "source_unova_route_names":"Route 301–323 (nao equivalem automaticamente a Route 1–18 de Black/White)",
    "original_mapids_are_donor_only":True,
    "destination_mapids_assigned":False,
    "sprite_assets_verified_for_reuse":False,
    "music_rights_verified":False,
    "map_geometry_rights_verified":False,
    "story_events_imported":0,
    "npc_events_imported":0,
    "game_exe_tested":False,
    "android_tested":False,
    "game_or_saves_modified":False,
    "can_install":False,
    "e04_source_inventory_completed":True,
    "e05_source_map_and_event_audit_completed":True,
    "e06_asset_rights_completed":False,
    "e08_native_gameplay_qa_completed":False,
}
AREAS={
    "Nuvema_Town":463,"Accumula_Town":464,"Striaton_City":465,
    "Nacrene_City":466,"Castelia_City":468,"Nimbasa_City":469,
    "Driftveil_City":471,"Mistralton_City":472,"Icirrus_City":473,
    "Opelucid_City":474,"Pinwheel_Forest":908,"Desert_Resort":907,
    "Relic_Castle":527,"Chargestone_Cave":523,"Dragonspiral_Tower":529,
    "Wellspring_Cave":522,"Giant_Chasm":531,
}


def validate(data):
    if not isinstance(data,dict):
        raise ValueError("E04/E05: evidencia precisa ser JSON")
    for key,expected in EXPECTED.items():
        value=data.get(key)
        if type(value) is not type(expected) or value!=expected:
            raise ValueError("E04/E05: evidencia divergente ou falsa no campo "+key)
    if data.get("source_unova_larger_map_ids") != [463,464,465,466,468,490,494,495]:
        raise ValueError("E04/E05: dimensoes de mapas maiores divergentes")
    if data.get("source_map_examples")!=AREAS:
        raise ValueError("E04/E05: MapIDs da fonte não correspondem ao relatório real")
    if data.get("source_unova_b2w2_anime_areas_detected")!=[
        "Aspertia City","Virbank City","Floccesy Town",
        "Vertress Conference","Black City","Reversal Mountain",
    ]:
        raise ValueError("E04/E05: referências BW2/anime ausentes")
    ev=data.get("evidence")
    if not isinstance(ev,dict) or (
        ev.get("source_audit_run") !=
        "https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/actions/runs/44083797886"
        or ev.get("artifact_name")!="unova-e04-metadata-only"
        or ev.get("artifact_retention_days")!=7
        or not isinstance(ev.get("summary_disclaimer"),str)
        or len(ev["summary_disclaimer"])<30
    ):
        raise ValueError("E04/E05: referência de execução auditável ausente")
    if not isinstance(data.get("blockers"),list) or len(data["blockers"])<5:
        raise ValueError("E04/E05: bloqueios de uso inadequadamente omitidos")
    if any(not isinstance(x,str) or len(x)<40 for x in data["blockers"]):
        raise ValueError("E04/E05: descrição dos bloqueios insuficiente")
    return {
        "status":"E04_E05_SOURCE_AUDITED_NOT_INSTALLED",
        "source_maps_all_regions":data["all_donor_map_files"],
        "source_mapinfos":data["all_donor_mapinfo_entries"],
        "unova_candidate_maps_read":data["unova_parent_maps_parsed"],
        "unova_events_found":data["unova_parent_event_containers"],
        "unova_maps_20x15":data["source_unova_map_dimensions_20x15"],
        "unova_maps_larger":data["source_unova_map_dimensions_nondefault"],
        "unova_area_name_matches_in_donor_branch":data["source_area_matches_inside_unova_parent"],
        "e04_completed":True,"e05_completed":True,
        "e06_completed":False,"e08_completed":False,
        "native_mapids_verified":False,"gameplay_verified":False,
        "redistribution_allowed":False,"can_install":False,
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--evidence",type=Path,default=DEFAULT)
    args=p.parse_args(argv)
    try:
        if args.evidence.is_symlink() or not args.evidence.is_file() or args.evidence.stat().st_size>200000:
            raise ValueError("evidencia ausente ou insegura")
        result=validate(json.loads(args.evidence.read_text("utf-8-sig")))
        print(json.dumps(result,indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print("UNOVA_EVIDENCE_BLOQUEADA: "+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main())
