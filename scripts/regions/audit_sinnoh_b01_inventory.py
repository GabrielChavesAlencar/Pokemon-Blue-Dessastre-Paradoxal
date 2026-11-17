#!/usr/bin/env python3
"""Sinnoh B01: read-only Decades MapID inventory. Never allocate or install maps."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from server.ruby_marshal import loads

SOURCE=ROOT/"data/regions/sinnoh-b00-actual-source.json"
REQUIRED={"native_inventory.json","MapInfos.rxdata","Tilesets.rxdata"}
SHA=re.compile(r"[0-9a-f]{64}\Z")

def blocked(msg):
    raise ValueError("SINNOH_B01_BLOCKED: "+msg)

def unpack(path):
    path=Path(path).expanduser().absolute()
    if path.is_symlink() or not path.is_file() or path.suffix.lower()!=".zip":
        blocked("ZIP de inventario ausente ou inseguro")
    if path.stat().st_size>80_000_000:
        blocked("ZIP de inventario muito grande")
    with zipfile.ZipFile(path) as z:
        seen=set()
        for m in z.infolist():
            if (m.is_dir() or m.filename not in REQUIRED or m.filename in seen or
                stat.S_IFMT(m.external_attr>>16)==stat.S_IFLNK or
                m.flag_bits & 1 or not 0<m.file_size<=33_554_432):
                blocked("ZIP contem arquivo extra/duplicado/inseguro")
            seen.add(m.filename)
        if seen!=REQUIRED:blocked("ZIP deve ter MapInfos, Tilesets e native_inventory")
        raw={name:z.read(name) for name in REQUIRED}
    if len(raw["native_inventory.json"])>2_000_000:blocked("JSON muito grande")
    record=json.loads(raw["native_inventory.json"].decode("utf-8-sig"))
    keys={"schema","mode","project","mapinfos_sha256","tilesets_sha256",
          "physical_map_file_count","physical_map_ids","scan_only",
          "game_or_saves_modified","future_region_reservations_verified",
          "manually_executed_native_qa","full_local_path_exported"}
    if (type(record) is not dict or set(record)!=keys or record["schema"]!=1 or
        record["mode"]!="DECADES_LOCAL_MAPID_INVENTORY_READ_ONLY" or
        record["project"]!="Pokemon Blue Dessastre Paradoxal / Decades" or
        record["scan_only"] is not True or
        any(record[k] is not False for k in ("game_or_saves_modified",
             "future_region_reservations_verified","manually_executed_native_qa",
             "full_local_path_exported"))):
        blocked("dados inventados ou conclusao falsa")
    for key,file in (("mapinfos_sha256","MapInfos.rxdata"),
                     ("tilesets_sha256","Tilesets.rxdata")):
        if (not isinstance(record[key],str) or not SHA.fullmatch(record[key]) or
            record[key]!=hashlib.sha256(raw[file]).hexdigest()):
            blocked("hash divergente: "+file)
    ids=record["physical_map_ids"]
    if (type(ids) is not list or len(ids)>5000 or
        any(type(x) is not int or not 1<=x<=99_999 for x in ids) or
        ids!=sorted(set(ids)) or record["physical_map_file_count"]!=len(ids)):
        blocked("MapIDs fisicos invalidos")
    return record,raw

def compare(path,source=SOURCE):
    record,raw=unpack(path)
    infos=loads(raw["MapInfos.rxdata"])
    if (type(infos) is not dict or len(infos)>5000 or
        any(type(x) is not int or not 1<=x<=99_999 for x in infos)):
        blocked("MapInfos nao e indice RMXP de MapIDs")
    source=Path(source)
    if source.is_symlink() or not source.is_file():
        blocked("recibo da fonte Sinnoh ausente")
    donor=json.loads(source.read_text("utf-8"))
    source_ids=donor.get("sinnoh_map_ids")
    if (donor.get("status")!="USER_SOURCE_RECEIVED_REAL_MAP_TREE_AUDITED_NOT_INSTALLABLE"
        or donor.get("sinnoh_map_count")!=76 or type(source_ids) is not list
        or len(source_ids)!=76 or any(type(x) is not int for x in source_ids)
        or len(set(source_ids))!=76 or donor.get("phase_b_technically_approved")!=0):
        blocked("recibo Sinnoh adulterado ou nao auditado")
    physical=set(record["physical_map_ids"])
    registered=set(infos)
    used=physical|registered
    low=set(range(1,600))
    return {
      "schema":1,"stage":"B01","region":"SINNOH",
      "status":"LOCAL_ID_CONFLICTS_IDENTIFIED_DESTINATION_PLAN_BLOCKED",
      "native_mapinfos_sha256":record["mapinfos_sha256"],
      "native_tilesets_sha256":record["tilesets_sha256"],
      "native_map_id_count_union":len(used),
      "native_mapinfos_ids_count":len(registered),
      "native_physical_map_files_count":len(physical),
      "native_indexed_maps_missing_files":sorted(registered-physical),
      "native_physical_maps_missing_index":sorted(physical-registered),
      "sinnoh_source_map_count":76,
      "sinnoh_original_ids_colliding_with_decades":sorted(set(source_ids)&used),
      "sinnoh_original_ids_outside_conservative_destination_band":
         sorted(set(source_ids)-low),
      "conservative_unoccupied_1_to_599_count":len(low-used),
      "conservative_unoccupied_1_to_599_ids_review_only":sorted(low-used),
      "enough_physical_slots_for_all_76":len(low-used)>=76,
      "other_region_future_reservations_verified":False,
      "can_select_destinations":False,"can_install":False,
      "map_or_save_written":False,"game_exe_tested":False,"joiplay_tested":False,
      "phase_b_approved":0,
      "next":"Revisar reservas Kanto/Johto/Hoenn antes de planejar destinos; vaga fisica nao prova propriedade."
    }

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inventory",type=Path,required=True)
    args=ap.parse_args(argv)
    try:
        print(json.dumps(compare(args.inventory),ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,zipfile.BadZipFile) as e:
        print(str(e),file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
