#!/usr/bin/env python3
"""B06 read-only source→candidate MapID preview based on the ACTUAL donor ZIP.

When supplied, independently rechecks donor source ZIP and native B01 archive.
No Ruby code execution, extraction, image redistribution, game writes, approved
MapIDs, native testing, future reservation proof, or stages.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import stat
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from audit_sinnoh_b01_inventory import unpack as unpack_b01
from audit_sinnoh_b05_mapid_planning import expand

B00=ROOT/"data/regions/sinnoh-b00-actual-source.json"
B01=ROOT/"data/regions/sinnoh-b01-actual-native.json"
B04=ROOT/"data/regions/sinnoh-b04-v2-validated.json"
B05=ROOT/"data/regions/sinnoh-b05-mapid-planning.json"
B06=ROOT/"data/regions/sinnoh-b06-technical-candidate.json"
EXPECTED_SOURCE_TILESETS_SHA="ddd1e57f033e9ad061870d2cb72288e17ab4f28bb2ace7cea69336a95f8cd1f1"
EXPECTED_MAP_HASH_DIGEST="55799526a92740134b81575c5c731193e985d6abdf0ee363e4b2ce1899c8778e"
ORDER_RULE="TERRAIN_IDS_ASC_THEN_EMPTY_PLACEHOLDERS_ASC"
ALLOWED_STATUS="REAL_SOURCE_HASHES_RECHECKED_CANDIDATE_REMAP_NOT_APPROVED"

def blocked(message):
    raise ValueError("SINNOH_B06_BLOCKED: "+message)

def load(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>2_000_000:
        blocked("metadata ausente ou insegura")
    obj=json.loads(path.read_text("utf-8"))
    if type(obj) is not dict:blocked("metadata invalida")
    return obj

def candidate_rows(b00,hold):
    terrain=sorted(b00["terrain_filled_ids"])
    empty=sorted(b00["empty_terrain_ids"])
    if (len(terrain)!=54 or len(empty)!=22
        or set(terrain)&set(empty)
        or set(terrain)|set(empty)!=set(b00["sinnoh_map_ids"])
        or len(set(b00["sinnoh_map_ids"]))!=76
        or hold!={"start":442,"end":517,"count":76}):
        blocked("fonte e retencao administrativa inconsistentes")
    return [
      {"source_map_id":source,"candidate_destination_map_id":442+index,
       "category":"TERRAIN" if index<54 else "EMPTY_PLACEHOLDER"}
      for index,source in enumerate(terrain+empty)
    ]

def audit(candidate,b00,b01,b04,b05):
    hold=b05["sinnoh"]["administrative_planning_hold"]
    expected=candidate_rows(b00,hold)
    if (candidate.get("schema")!=1 or candidate.get("region")!="SINNOH"
        or candidate.get("stage")!="B06"
        or candidate.get("status")!=ALLOWED_STATUS
        or candidate.get("source_zip_sha256")!=b00.get("source_zip_sha256")
        or candidate.get("source_mapinfos_sha256")!=b00.get("mapinfos_sha256")
        or candidate.get("source_tilesets_sha256")!=EXPECTED_SOURCE_TILESETS_SHA
        or candidate.get("source_76_map_sha256_list_digest")!=EXPECTED_MAP_HASH_DIGEST
        or candidate.get("source_zip_internal_root")!="Pokemon Journeys V18"
        or candidate.get("native_b01_inventory_zip_sha256")!=b01.get("inventory_archive_sha256")
        or candidate.get("native_mapinfos_sha256")!=b01.get("mapinfos_sha256")
        or candidate.get("native_tilesets_sha256")!=b01.get("tilesets_sha256")
        or candidate.get("native_b04v2_provenance_zip_sha256")!=b04.get("uploaded_zip_sha256")
        or b04.get("status")!="B04_V2_FULL_PHYSICAL_INVENTORY_CONFIRMED_MATCHES_B01"
        or b04.get("new_report_physical_count")!=648
        or b04.get("missing_map_ids_in_v2")!=[]
        or b04.get("extra_map_ids_in_v2")!=[]
        or b04.get("mapinfos_sha256")!=b01.get("mapinfos_sha256")
        or b04.get("tilesets_sha256")!=b01.get("tilesets_sha256")
        or b05["sinnoh"].get("native_reserved_or_allocated") is not False
        or b05["sinnoh"].get("future_region_reservations_verified") is not False
        or b05["unova"].get("already_allocated_shared_map_ids") is not False
        or b01.get("native_occupied_map_count")!=648
        or candidate.get("candidate_rule")!=ORDER_RULE
        or candidate.get("candidate_range")!=hold
        or candidate.get("remap_preview")!=expected
        or candidate.get("counts")!={"total":76,"terrain":54,"empty_placeholders":22,
            "static_transfer_commands_found_in_donor":0}
        or b00.get("sinnoh_standard_transfer_commands")!=0
        or candidate.get("source_tileset_references")!=[1,31]
        or b00.get("tileset_ids_used")!=[1,31]
        or candidate.get("source_to_native_tileset_mapping")!={}
        or candidate.get("source_tile_31_conflicts_with_native_tile_31") is not True
        or b01.get("native_and_donor_tileset_names_match") is not False
        or b01.get("donor_tilesets",{}).get("31")!="SinnohCompleteTileset"
        or candidate.get("scanned_donor_map_file_hashes_against_real_archive") is not True):
        blocked("manifesto real B06 divergente ou candidato falso")
    for flag in ("existing_native_tilesets_must_not_change",):
        if candidate.get(flag) is not True:blocked("tilesets nativos nao podem mudar")
    for flag in ("source_binary_redistribution_allowed",
                 "source_per_asset_rights_verified",
                 "future_kanto_johto_hoenn_reservations_approved",
                 "native_destinations_allocated","stage_written",
                 "game_data_or_saves_modified","game_exe_tested","joiplay_tested",
                 "can_install","r07_complete","r08_complete","r09_complete"):
        if candidate.get(flag) is not False:blocked("aprovacao falsa: "+flag)
    for key in ("phase_b_technically_approved","phase_c_playable_approved",
                "phase_d_native_approved"):
        if candidate.get(key)!=0:blocked("barra tecnicamente aprovada sem teste")
    occupied=expand(b05["occupied"]["ranges"],limit=999)
    unova=expand(b05["unova"]["candidate_ranges"],limit=599)
    proposed={row["candidate_destination_map_id"] for row in expected}
    if (proposed&occupied or proposed&unova
        or proposed!=set(range(442,518))
        or len(unova)!=174
        or b05["unova"]["preferred_contiguous_candidate"]!={"start":518,"end":599,"count":82}):
        blocked("destinos candidatos colidem com Decades ou Unova")
    return {
      "region":"SINNOH","stage":"B06",
      "status":"CANDIDATE_MAPPING_76_SOURCE_MAPS_NOT_ALLOCATED",
      "candidate_total":76,"real_terrain":54,
      "empty_placeholders":22,
      "twinleaf_candidate":next(x["candidate_destination_map_id"] for x in expected
                               if x["source_map_id"]==209),
      "source_tilesets_requiring_new_native_indices":[1,31],
      "unova_candidate_map_ids_preserved":174,
      "r07_complete":False,"may_install":False,
      "game_data_modified":False,"phase_b_approved":0
    }

def sha256_file(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as file:
        for block in iter(lambda:file.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()

def verify_source_zip(path,candidate,b00):
    path=Path(path).expanduser().absolute()
    if (path.is_symlink() or not path.is_file()
        or path.stat().st_size>400_000_000
        or sha256_file(path)!=candidate["source_zip_sha256"]):
        blocked("ZIP doador real nao coincide com hash B00")
    archive_root=candidate["source_zip_internal_root"]
    with zipfile.ZipFile(path) as z:
        selected=[(f"{archive_root}/Data/Map{m:03d}.rxdata",m)
                  for m in sorted(b00["sinnoh_map_ids"])]
        selected+=[(f"{archive_root}/Data/MapInfos.rxdata",None),
                   (f"{archive_root}/Data/Tilesets.rxdata",None)]
        hashes={}
        for member,source_id in selected:
            found=[f for f in z.infolist() if f.filename==member]
            if (len(found)!=1 or found[0].is_dir()
                or stat.S_IFMT(found[0].external_attr>>16)==stat.S_IFLNK
                or found[0].file_size>32_000_000):
                blocked("arquivo RXDATA ausente, duplicado ou inseguro: "+member)
            data=z.read(found[0])
            hashes[source_id if source_id is not None else member]=hashlib.sha256(data).hexdigest()
        if hashes[f"{archive_root}/Data/MapInfos.rxdata"]!=candidate["source_mapinfos_sha256"]:
            blocked("indice MapInfos do doador mudou")
        if hashes[f"{archive_root}/Data/Tilesets.rxdata"]!=candidate["source_tilesets_sha256"]:
            blocked("indice Tilesets do doador mudou")
        rows=[{"source_id":mid,"sha256":hashes[mid]} for mid in sorted(b00["sinnoh_map_ids"])]
        packed=json.dumps(rows,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode("ascii")
        if hashlib.sha256(packed).hexdigest()!=candidate["source_76_map_sha256_list_digest"]:
            blocked("um dos 76 mapas difere da auditoria real B00")
    return {"source_zip_verified":True,"real_map_hashes_verified":76,
            "terrain_source_maps_count":54,"placeholder_source_maps_count":22}

def verify_native_zip(path,candidate,b05):
    path=Path(path).expanduser().absolute()
    if (path.is_symlink() or not path.is_file()
        or sha256_file(path)!=candidate["native_b01_inventory_zip_sha256"]):
        blocked("ZIP do inventario Decades difere da B01")
    report,_=unpack_b01(path)
    if (report["mapinfos_sha256"]!=candidate["native_mapinfos_sha256"]
        or report["tilesets_sha256"]!=candidate["native_tilesets_sha256"]
        or set(report["physical_map_ids"])!=expand(b05["occupied"]["ranges"],limit=999)):
        blocked("MapIDs reais da instalacao diferem do planejamento B05")
    return {"native_b01_zip_verified":True,"native_occupied_map_ids_verified":648}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip",type=Path)
    parser.add_argument("--native-inventory",type=Path)
    args=parser.parse_args(argv)
    try:
        candidate,b00,b01,b04,b05=(load(p) for p in (B06,B00,B01,B04,B05))
        result=audit(candidate,b00,b01,b04,b05)
        result["source_zip_verification_run"]=False
        result["native_inventory_verification_run"]=False
        if args.source_zip:
            result.update(verify_source_zip(args.source_zip,candidate,b00))
            result["source_zip_verification_run"]=True
        if args.native_inventory:
            result.update(verify_native_zip(args.native_inventory,candidate,b05))
            result["native_inventory_verification_run"]=True
        print(json.dumps(result,ensure_ascii=False,indent=2))
        print("SINNOH_B06_REAL_SOURCE_CANDIDATE_AUDITED_NOT_INSTALLABLE")
        return 0
    except (OSError,ValueError,KeyError,TypeError,IndexError,OverflowError,
            UnicodeError,zipfile.BadZipFile) as err:
        print(str(err),file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
