#!/usr/bin/env python3
"""Sinnoh B04: validate privacy-minimized Windows regional provenance ZIP.

READ-ONLY and fail-closed: never execute programs, load raw manifest
contents or games; never infer ownership of future reservations.
"""
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
SPEC_PATH=ROOT/"data/regions/sinnoh-b04-collector-contract.json"
B01_PATH=ROOT/"data/regions/sinnoh-b01-actual-native.json"
B03_PATH=ROOT/"data/regions/sinnoh-b03-installer-evidence.json"
SHA=re.compile(r"[0-9a-f]{64}\Z")
SAFE_STATUS=re.compile(r"[A-Za-z0-9_-]{1,90}\Z")
KEY=re.compile(r"[1-9][0-9]{0,4}\Z")
FILES={"native_provenance.json","LEIA_ME.txt"}
REGIONS=("KANTO","JOHTO","HOENN")
REPORT_KEYS={
 "schema","mode","region","reference_mapinfos_sha256",
 "reference_tilesets_sha256","mapinfos_sha256","tilesets_sha256",
 "same_b01_baseline","physical_map_ids","regions",
 "future_reservation_manifests_included","future_reservations_fully_verified",
 "may_allocate_sinnoh_ids","can_install","game_or_saves_modified",
 "native_gameplay_tested","source_paths_included","raw_manifests_included"
}
ENTRY_KEYS={
 "presence","source_file","sha256","reported_schema","reported_region",
 "manifest_status","source_map_count","destination_map_ids",
 "source_to_destination","invalid_map_entries","duplicate_destination_ids",
 "source_id_mapping_is_complete_proof","future_reservations_proven",
 "native_gameplay_tested"
}
NEVER_TRUE={
 "future_reservation_manifests_included","future_reservations_fully_verified",
 "may_allocate_sinnoh_ids","can_install","game_or_saves_modified",
 "native_gameplay_tested","source_paths_included","raw_manifests_included"
}

def blocked(message):
    raise ValueError("SINNOH_B04_BLOCKED: "+message)

def load(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>2_000_000:
        blocked("contrato de metadados ausente ou inseguro")
    obj=json.loads(p.read_text("utf-8"))
    if type(obj) is not dict:blocked("JSON de contrato invalido")
    return obj

def checked_contract(spec,b01,b03):
    if (spec.get("schema")!=1 or spec.get("region")!="SINNOH"
        or spec.get("step")!="B04"
        or spec.get("status")!="ONE_CLICK_COLLECTOR_READY_LOCAL_PROVENANCE_NOT_RECEIVED"
        or spec.get("format")!="SINNOH_B04_LOCAL_REGIONAL_PROVENANCE_READ_ONLY"
        or spec.get("reference_mapinfos_sha256")!=b01["mapinfos_sha256"]
        or spec.get("reference_tilesets_sha256")!=b01["tilesets_sha256"]
        or spec.get("reference_b01_inventory_sha256")!=b01["inventory_archive_sha256"]
        or b01.get("native_occupied_map_count")!=648
        or b01.get("phase_b_technically_approved")!=0
        or b03.get("native_mapinfos_sha256")!=b01["mapinfos_sha256"]
        or b03.get("native_tilesets_sha256")!=b01["tilesets_sha256"]
        or b03.get("r07_complete") is not False
        or b03.get("can_install") is not False
        or set(spec.get("expected_regions",{}))!=set(REGIONS)
        or spec.get("input_files")!=["native_provenance.json","LEIA_ME.txt"]
        or spec.get("future_reservations_verified") is not False
        or spec.get("ownership_by_region_verified") is not False):
        blocked("contrato de origem B01/B03 ou status de reservas divergente")
    if (spec["expected_regions"]["KANTO"].get("expected_map_count")!=142
        or spec["expected_regions"]["JOHTO"].get("expected_map_count")!=100
        or spec["expected_regions"]["HOENN"].get("expected_map_count")!=199):
        blocked("contagens dos instaladores nao conferem")
    for name,row in spec["expected_regions"].items():
        if (row.get("schema")!=1 or row.get("source_key")!=("map_ids" if name=="JOHTO" else "maps")
            or row.get("filename")!={"KANTO":"blue-kanto-install.json",
                                     "JOHTO":"blue-johto-main-preview.json",
                                     "HOENN":"blue-hoenn-install.json"}[name]
            or not (Path(ROOT)/row.get("documented_source","")).is_file()):
            blocked("origem de manifesto desconhecida: "+name)
    for key in ("input_contains_raw_manifests","input_contains_saved_games",
                "input_contains_map_bytes","input_contains_images_or_audio",
                "can_allocate_sinnoh_map_ids","can_install",
                "game_exe_tested","joiplay_tested","can_mark_playable",
                "r07_complete","r08_complete","r09_complete",
                "main_game_or_saves_modified"):
        if spec.get(key) is not False:blocked("aprovacao/arquivo proibido no contrato: "+key)
    for key in ("phase_b_approved","phase_c_approved","phase_d_approved"):
        if spec.get(key)!=0:blocked("barra nativa falsamente aprovada")
    return spec

def checked_ids(values,label):
    if (type(values) is not list or len(values)>5000
        or any(type(v) is not int or not 1<=v<=99999 for v in values)
        or values!=sorted(set(values))):
        blocked("MapIDs invalidos/duplicados/desordenados: "+label)
    return set(values)

def read_zip(path):
    path=Path(path).expanduser().absolute()
    if path.is_symlink() or not path.is_file() or path.suffix.lower()!=".zip":
        blocked("pacote ZIP B04 inexistente ou symlink")
    if path.stat().st_size>3_000_000:blocked("ZIP B04 grande demais")
    with zipfile.ZipFile(path) as z:
        seen=set()
        for info in z.infolist():
            if (info.is_dir() or info.filename not in FILES or
                info.filename in seen or info.flag_bits & 1
                or stat.S_IFMT(info.external_attr>>16)==stat.S_IFLNK
                or not 0<info.file_size<=2_000_000):
                blocked("arquivo ZIP extra/duplicado, diretório, symlink ou grande demais")
            seen.add(info.filename)
        if seen!=FILES:blocked("ZIP B04 deve conter apenas relatório e LEIA_ME")
        raw=z.read("native_provenance.json")
    if len(raw)>1_000_000:blocked("relatorio muito grande")
    obj=json.loads(raw.decode("utf-8-sig"))
    if type(obj) is not dict or set(obj)!=REPORT_KEYS:
        blocked("JSON B04 de formato desconhecido")
    return obj

def checked_region(name,row,spec,physical):
    if type(row) is not dict or set(row)!=ENTRY_KEYS:
        blocked("campos de manifesto invalido: "+name)
    kind=row["presence"]
    if kind not in ("MISSING","FOUND_INVALID","FOUND_PARSED"):
        blocked("estado de manifesto desconhecido: "+name)
    if row["source_file"]!=spec["expected_regions"][name]["filename"]:
        blocked("manifesto incorreto para "+name)
    for field in ("source_id_mapping_is_complete_proof",
                  "future_reservations_proven","native_gameplay_tested"):
        if row[field] is not False:blocked("aprovacao falsa de manifesto "+name)
    sha=row["sha256"]
    if (sha is not None and (type(sha) is not str or not SHA.fullmatch(sha))
        or kind=="MISSING" and sha is not None
        or kind!="MISSING" and sha is None):
        blocked("SHA do manifesto invalido: "+name)
    if (row["reported_schema"] is not None
        and type(row["reported_schema"]) is not int
        or row["reported_region"] is not None
        and (type(row["reported_region"]) is not str
             or not re.fullmatch("[A-Z]{3,15}",row["reported_region"]))
        or row["manifest_status"] is not None
        and (type(row["manifest_status"]) is not str
             or not SAFE_STATUS.fullmatch(row["manifest_status"]))):
        blocked("campos de status do manifesto inseguros: "+name)
    ids=checked_ids(row["destination_map_ids"],name)
    mapping=row["source_to_destination"]
    if (type(mapping) is not dict or len(mapping)>5000
        or any(type(k) is not str or not KEY.fullmatch(k) or
               type(v) is not int or not 1<=v<=99999 for k,v in mapping.items())):
        blocked("MapIDs origem/destino invalidos: "+name)
    if (type(row["source_map_count"]) is not int
        or not 0<=row["source_map_count"]<=5000
        or type(row["invalid_map_entries"]) is not int
        or not 0<=row["invalid_map_entries"]<=5000
        or type(row["duplicate_destination_ids"]) is not bool):
        blocked("contagem de mapas invalida: "+name)
    if kind!="FOUND_PARSED":
        if ids or mapping or row["source_map_count"]!=0 or row["invalid_map_entries"]!=0:
            blocked("dados de mapa inventados em manifesto ausente/invalido")
    else:
        if name=="JOHTO":
            if mapping or row["source_map_count"]!=len(ids) and not row["duplicate_destination_ids"]:
                blocked("Johto exige lista, sem mapa de origem")
        elif (row["source_map_count"]!=len(mapping)
              or ids!=set(mapping.values())):
            blocked("destinos nao coincidem com o mapeamento numérico")
        if (row["duplicate_destination_ids"] !=
            (row["source_map_count"]>len(ids))):
            blocked("marcador de destino duplicado inconsistente")
        if row["source_map_count"]<1:blocked("manifesto vazio")
    valid=(kind=="FOUND_PARSED"
           and row["reported_schema"]==1
           and row["invalid_map_entries"]==0
           and not row["duplicate_destination_ids"]
           and row["source_map_count"]==spec["expected_regions"][name]["expected_map_count"]
           and (name=="KANTO" or row["reported_region"]==name)
           and (name=="KANTO" or row["manifest_status"]==
                spec["expected_regions"][name]["required_manifest_status"])
           and (name!="JOHTO" or ids==set(range(600,700)))
           and (name!="HOENN" or all(700<=mid<=999 for mid in ids))
           and ids.issubset(physical))
    return {"presence":kind,"manifest_sha256_reported":sha,
            "source_map_count":row["source_map_count"],
            "destination_map_count":len(ids),
            "installed_claim_matches_known_contract":valid,
            "future_reservations_confirmed":False,
            "missing_physical_map_ids":sorted(ids-physical)}

def audit_zip(path,spec,b01,b03):
    checked_contract(spec,b01,b03)
    report=read_zip(path)
    if (report["schema"]!=1 or report["region"]!="SINNOH"
        or report["mode"]!=spec["format"]
        or report["reference_mapinfos_sha256"]!=spec["reference_mapinfos_sha256"]
        or report["reference_tilesets_sha256"]!=spec["reference_tilesets_sha256"]
        or any(report[x] is not False for x in NEVER_TRUE)
        or set(report["regions"])!=set(REGIONS)):
        blocked("relatorio de origem falsa ou flag proibida")
    for field in ("mapinfos_sha256","tilesets_sha256"):
        if type(report[field]) is not str or not SHA.fullmatch(report[field]):
            blocked("hash nativo invalido: "+field)
    baseline=(report["mapinfos_sha256"]==b01["mapinfos_sha256"]
              and report["tilesets_sha256"]==b01["tilesets_sha256"])
    if type(report["same_b01_baseline"]) is not bool or report["same_b01_baseline"]!=baseline:
        blocked("alegacao de baseline divergente")
    physical=checked_ids(report["physical_map_ids"],"instalacao local")
    # Collector v1 required 3-5 digits in MapNNN.rxdata and accidentally omitted
    # all 31 native map files with IDs < 100. Do not count the 31 as free,
    # forge a physical re-scan or silently mark the inventory complete.
    expected_legacy=(
        set(range(100,276)) | set(range(300,442))
        | set(range(600,899))
    )
    legacy_short_id_bug=(baseline and physical==expected_legacy)
    if baseline and not legacy_short_id_bug and (len(physical)!=648
        or sum(x<=599 for x in physical)!=349
        or sum(600<=x<=699 for x in physical)!=100
        or sum(700<=x<=999 for x in physical)!=199):
        blocked("mapas fisicos divergem do snapshot B01 sem hash novo")
    region_results={reg:checked_region(reg,report["regions"][reg],spec,physical)
                    for reg in REGIONS}
    claims={reg:set(report["regions"][reg]["destination_map_ids"]) for reg in REGIONS
            if region_results[reg]["installed_claim_matches_known_contract"]}
    overlaps=sorted(set().union(*(claims[a]&claims[b]
       for a,b in (("KANTO","JOHTO"),("KANTO","HOENN"),("JOHTO","HOENN"))
       if a in claims and b in claims))) if len(claims)>1 else []
    if not baseline:
        status="BASELINE_CHANGED_REQUIRES_NEW_B01"
    elif legacy_short_id_bug:
        status="LEGACY_B04_COLLECTOR_OMITTED_SHORT_MAP_IDS_RESCAN_REQUIRED"
    elif overlaps:
        status="INSTALLED_REGIONAL_ID_COLLISIONS_NEED_REVIEW"
    elif len(claims)!=3:
        status="PARTIAL_OR_INVALID_REGIONAL_PROVENANCE"
    else:
        status="THREE_INSTALLED_MANIFESTS_REPORTED_FUTURE_RESERVATIONS_STILL_UNKNOWN"
    return {
       "schema":1,"region":"SINNOH","step":"B04","status":status,
       "local_report_sha256":hashlib.sha256(Path(path).read_bytes()).hexdigest(),
       "b01_baseline_matches_current_hashes":baseline,
       "physical_map_ids_reported":len(physical),
       "legacy_collector_short_ids_omitted":legacy_short_id_bug,
       "legacy_b01_known_omitted_ids":(
          [1,22,32,33,42,43,48,*range(76,100)] if legacy_short_id_bug else []),
       "b01_reference_physical_map_count":b01["native_occupied_map_count"],
       "regional_installation_claims":region_results,
       "installed_region_claims_matching_contract":len(claims),
       "conflicting_installed_destination_ids":overlaps,
       "future_reservations_proven":False,
       "rights_proven":False,"native_gameplay_proven":False,
       "r07_complete":False,"may_allocate_sinnoh_ids":False,
       "can_install":False,"game_or_saves_modified":False,
       "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
       "limits":[
           "O ZIP contém apenas resumo autodeclarado e hashes, nao provas binarias brutas",
           "Instalacao atual nao prova reservas de mapas ainda nao instalados",
           "MapInfos atualizado exige novo inventario B01 antes do remapeamento",
       ]
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=Path,help="SINNOH_B04_PROVENIENCIA_REGIONAL.zip gerado no Windows")
    args=p.parse_args(argv)
    try:
        spec=load(SPEC_PATH);b01=load(B01_PATH);b03=load(B03_PATH)
        checked_contract(spec,b01,b03)
        if args.input:
            result=audit_zip(args.input,spec,b01,b03)
        else:
            result={"schema":1,"region":"SINNOH","step":"B04",
                    "status":"AWAITING_LOCAL_B04_ZIP",
                    "collector_ready":True,
                    "regional_installation_claims":None,
                    "r07_complete":False,"can_install":False,
                    "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0}
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            zipfile.BadZipFile,zipfile.LargeZipFile) as ex:
        print(str(ex),file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
