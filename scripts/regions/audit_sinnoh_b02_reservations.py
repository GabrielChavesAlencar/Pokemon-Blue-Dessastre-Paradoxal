#!/usr/bin/env python3
"""Sinnoh B02: reconcile observed Decades MapIDs and GitHub code claims.

Do not treat physical vacancy as regional ownership. No allocation, imports,
Game.exe/JoiPlay tests, save edits or native acceptance in this tool.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from audit_region_map_id_reservations import validate as validate_ch05
from audit_sinnoh_b01_inventory import unpack as unpack_b01
from server.ruby_marshal import loads,text

SOURCE=ROOT/"data/regions/sinnoh-b00-actual-source.json"
NATIVE=ROOT/"data/regions/sinnoh-b01-actual-native.json"
CH05=ROOT/"data/regions/sinnoh-map-id-reservations.json"
B02=ROOT/"data/regions/sinnoh-b02-reservations.json"
LABEL_SAMPLES={
    "439":"Elite Four — sala de Lance",
    "441":"Hall of Fame — Kanto",
    "600":"[Johto preview] New Bark Town",
    "699":"Casa em Ecruteak",
    "700":"Vila Littleroot",
    "800":"Museu de Lilycove",
    "805":"Rota 119",
    "898":"Cidade de Ever Grande Norte",
}

def blocked(reason):
    raise ValueError("SINNOH_B02_BLOCKED: "+reason)

def read(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>3_000_000:
        blocked("fonte de metadados ausente/insegura")
    data=json.loads(p.read_text("utf-8"))
    if type(data) is not dict:blocked("metadados nao sao objeto JSON")
    return data

def expected(b00,b01,ch05,*,root=ROOT):
    validate_ch05(ch05,Path(root))
    if (b00.get("region")!="SINNOH"
        or b00.get("status")!="USER_SOURCE_RECEIVED_REAL_MAP_TREE_AUDITED_NOT_INSTALLABLE"
        or b00.get("phase_b_technically_approved")!=0
        or b00.get("rights_per_asset_verified") is not False
        or b00.get("sinnoh_map_count")!=76):
        blocked("recibo real do doador nao esta seguro")
    source_ids=b00.get("sinnoh_map_ids")
    if (type(source_ids) is not list or len(source_ids)!=76
        or any(type(x) is not int or x<=0 for x in source_ids)
        or len(set(source_ids))!=76):
        blocked("76 MapIDs do doador nao conferem")
    if (b01.get("status")!="NATIVE_INVENTORY_RECEIVED_AND_MATCHED_REMAP_NOT_ALLOCATED"
        or b01.get("source_sinnoh_archive_sha256")!=b00["source_zip_sha256"]
        or b01.get("native_occupied_map_count")!=648
        or b01.get("native_registered_map_count")!=648
        or b01.get("native_physical_map_count")!=648
        or b01.get("native_indexed_without_physical_map")!=[]
        or b01.get("native_physical_without_index")!=[]
        or b01.get("sinnoh_source_map_count")!=76
        or b01.get("native_occupied_by_range")!={
            "1-599":349,"600-699":100,"700-799":100,
            "800-899":99,"900-999":0}
        or b01.get("conservative_1_to_599_physically_vacant_count")!=250):
        blocked("contagens do inventario Decades foram adulteradas")
    ranges=b01.get("conservative_1_to_599_physically_vacant_ranges")
    if (type(ranges) is not list or len(ranges)!=7
        or any(type(x) is not dict or set(x)!={"first","last","count"}
               or any(type(x[k]) is not int for k in x)
               or x["count"]!=x["last"]-x["first"]+1
               or x["first"]<1 or x["last"]>599 for x in ranges)
        or sum(x["count"] for x in ranges)!=250
        or ranges[-1]!={"first":442,"last":599,"count":158}
        or any(ranges[i]["last"]>=ranges[i+1]["first"]
               for i in range(len(ranges)-1))):
        blocked("blocos fisicamente vagos inconsistentes")
    source_collisions=b01.get("sinnoh_original_ids_colliding_with_decades")
    source_empty=b01.get("sinnoh_original_ids_not_physically_occupied")
    if (type(source_collisions) is not list or type(source_empty) is not list
        or len(source_collisions)!=72 or len(source_empty)!=4
        or set(source_collisions)&set(source_empty)
        or set(source_collisions)|set(source_empty)!=set(source_ids)
        or b01.get("individual_asset_rights_verified") is not False
        or b01.get("future_kanto_johto_hoenn_reservations_verified") is not False
        or b01.get("destination_ids_allocated") is not False
        or b01.get("can_install") is not False
        or b01.get("phase_b_technically_approved")!=0):
        blocked("ocupacoes ou aprovacoes B01 invalidas")
    claims=ch05["documented_shared_reservations"]
    if ([x["owner"] for x in claims]!=["JOHTO","HOENN"]
        or [(x["start"],x["end"]) for x in claims] !=[(600,699),(700,999)]
        or ch05["native_snapshot"]["status"]!="NOT_PROVIDED"
        or ch05["allocation"]["can_allocate"] is not False
        or ch05["allocation"]["can_install"] is not False):
        blocked("reivindicacoes CH05 nao verificadas")
    return {
      "schema":1,"region":"SINNOH","step":"B02",
      "status":"DOCUMENTED_RESERVATIONS_REVIEWED_FUTURE_CLAIMS_UNVERIFIED",
      "evidence_date":"2026-11-17",
      "native_inventory_sha256":b01["inventory_archive_sha256"],
      "native_mapinfos_sha256":b01["mapinfos_sha256"],
      "source_sinnoh_zip_sha256":b00["source_zip_sha256"],
      "static_reservations_manifest":"data/regions/sinnoh-map-id-reservations.json",
      "observation_scope":"MAPINFOS_NAMES_AND_DOCUMENTED_CODE_CLAIMS_ONLY",
      "physical_occupied_total":648,
      "physical_occupied_1_to_599":349,"physical_vacant_1_to_599":250,
      "physical_vacant_ranges_1_to_599":ranges,
      "maximal_vacant_span_1_to_599":{
          "start":442,"end":599,"count":158,"ownership_verified":False},
      "protected_code_claims":claims,
      "protected_code_claims_total_slots":400,
      "protected_claimed_johto_600_to_699":{
          "occupied_snapshot":100,"source_mapids_assigned":0,
          "actual_map_ownership_proven":False},
      "protected_claimed_hoenn_700_to_999":{
          "occupied_snapshot":199,"source_mapids_assigned":0,
          "actual_map_ownership_proven":False},
      "claimed_bands_physically_unoccupied":101,
      "native_label_samples":LABEL_SAMPLES,
      "sinnoh_original_map_count":76,
      "sinnoh_original_collision_count":72,
      "sinnoh_destination_map_ids":{},
      "kanto_installer_mapping_status":"DYNAMIC_NO_FUTURE_RESERVATION_MANIFEST",
      "johto_future_reservation_evidence":False,
      "hoenn_future_reservation_evidence":False,
      "kanto_future_reservation_evidence":False,
      "all_future_reservations_verified":False,
      "reservation_manifest_reviewed_by_user":False,
      "per_asset_rights_verified":False,
      "source_mapids_reused_as_destinations":False,
      "native_playtest_performed":False,
      "can_allocate":False,"can_install":False,
      "r07_complete":False,"r08_complete":False,"r09_complete":False,
      "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
      "note":"Claimed installer regions do not prove installed owners; native labels are observed but cannot certify ownership. 442-599 is physically vacant only, and Kanto future reservations below 600 are unknown. No map IDs allocated, no assets imported, user saves intact."
    }

def verify_inventory(inventory,b01,b00):
    path=Path(inventory).expanduser().absolute()
    if (path.is_symlink() or not path.is_file()
        or hashlib.sha256(path.read_bytes()).hexdigest()!=b01["inventory_archive_sha256"]):
        blocked("ZIP local difere do inventario real B01")
    snapshot,raw=unpack_b01(path)
    if (snapshot["mapinfos_sha256"]!=b01["mapinfos_sha256"]
        or snapshot["tilesets_sha256"]!=b01["tilesets_sha256"]):
        blocked("MapInfos/Tilesets nao coincidem com o inventario B01")
    infos=loads(raw["MapInfos.rxdata"])
    if (type(infos) is not dict or len(infos)!=648
        or set(infos)!=set(snapshot["physical_map_ids"])):
        blocked("MapInfos e arquivos fisicos divergentes")
    for string_id,name in LABEL_SAMPLES.items():
        obj=infos.get(int(string_id))
        if obj is None or text(obj.attrs.get("@name"))!=name:
            blocked("nome do mapa nativo divergiu: "+string_id)
    used=set(infos)
    if (sum(i<=599 for i in used)!=349 or
        sum(600<=i<=699 for i in used)!=100 or
        sum(700<=i<=999 for i in used)!=199 or
        len(set(b00["sinnoh_map_ids"])&used)!=72 or
        sum(i not in used for i in range(1,600))!=250):
        blocked("inventario original e metadados B01 divergentes")
    return True

def reconcile(b02,b00,b01,ch05,*,root=ROOT,inventory=None):
    calculated=expected(b00,b01,ch05,root=root)
    if type(b02) is not dict or b02!=calculated:
        blocked("manifesto B02 ou aprovacao adulterados")
    local=verify_inventory(inventory,b01,b00) if inventory else False
    return {
       "region":"SINNOH","step":"B02",
       "status":b02["status"],"real_inventory_revalidated_now":local,
       "claimed_joh_to_range":[600,699],
       "claimed_hoenn_range":[700,999],
       "occupied_joh_to_range":100,"occupied_hoenn_range":199,
       "unoccupied_low_range_count":250,
       "largest_unoccupied_run":[442,599,158],
       "original_sinnoh_id_collisions":72,
       "future_region_reservations_complete":False,
       "native_owner_verified":False,
       "candidate_destinations":[],
       "r07_complete":False,"phase_b_approved":0,"can_install":False
    }

def run(*,root=ROOT,inventory=None):
    root=Path(root)
    return reconcile(
      read(root/"data/regions/sinnoh-b02-reservations.json"),
      read(root/"data/regions/sinnoh-b00-actual-source.json"),
      read(root/"data/regions/sinnoh-b01-actual-native.json"),
      read(root/"data/regions/sinnoh-map-id-reservations.json"),
      root=root,inventory=inventory)

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--inventory",type=Path,
                   help="ZIP real B01 do usuario, opcional, para revalidar hashes e nomes")
    a=p.parse_args(argv)
    try:
        result=run(inventory=a.inventory)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        print("SINNOH_B02_RESERVATIONS_AUDITED_NOT_APPROVED")
        return 0
    except (OSError,ValueError,KeyError,TypeError,AttributeError,
            zipfile.BadZipFile,UnicodeError) as e:
        print(str(e),file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
