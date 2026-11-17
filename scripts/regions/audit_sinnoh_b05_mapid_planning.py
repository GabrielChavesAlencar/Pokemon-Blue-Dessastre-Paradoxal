#!/usr/bin/env python3
"""B05: cross-check MapID planning holds with native B01/B04 derived evidence.

No MapIDs are installed or finalized here. This enforces a planning hold for
Sinnoh, excludes it from Unova candidates, and retains the R07 safety gate.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
CATALOG=ROOT/"data/regions/sinnoh-b05-mapid-planning.json"
B01=ROOT/"data/regions/sinnoh-b01-actual-native.json"
B03=ROOT/"data/regions/sinnoh-b03-installer-evidence.json"
UNOVA=ROOT/"data/regions/unova-u03-areas.json"

def blocked(message):
    raise ValueError("SINNOH_B05_BLOCKED: "+message)

def load(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>2_000_000:
        blocked("fonte de metadados ausente/insegura")
    j=json.loads(p.read_text("utf-8"))
    if type(j) is not dict:blocked("JSON nao e objeto")
    return j

def expand(rows,*,limit=99999):
    if type(rows) is not list or len(rows)>2000:blocked("faixas invalidas")
    output=set()
    last=0
    for row in rows:
        if (type(row) is not dict or set(row)!={"start","end","count"}
            or any(type(row[k]) is not int for k in row)
            or not 1<=row["start"]<=row["end"]<=limit
            or row["count"]!=row["end"]-row["start"]+1
            or row["start"]<=last):
            blocked("faixa incompleta, duplicada ou fora de ordem")
        output.update(range(row["start"],row["end"]+1))
        last=row["end"]
    return output

def audit(cat,b01,b03,unova):
    if (cat.get("schema")!=1 or cat.get("region")!="MULTIREGION"
        or cat.get("stage")!="SINNOH_B05_UNOVA_MAPID_PLANNING"
        or cat.get("status")!="B04_REGIONAL_MANIFESTS_RECONCILED_SINNOH_ADMIN_HOLD_UNOVA_CANDIDATES_ONLY"
        or b01.get("native_occupied_map_count")!=648
        or b01.get("mapinfos_sha256")!=cat.get("evidence",{}).get("mapinfos_sha256")
        or b01.get("tilesets_sha256")!=cat.get("evidence",{}).get("tilesets_sha256")
        or b01.get("inventory_archive_sha256")!=cat["evidence"]["b01_inventory_zip_sha256"]
        or b03.get("native_mapinfos_sha256")!=b01["mapinfos_sha256"]
        or b03.get("r07_complete") is not False
        or b03.get("destination_mapping")!={}):
        blocked("baseline B01/B03 ou status de planejamento adulterado")
    ev=cat["evidence"]
    if (ev.get("b04_provenance_zip_sha256")!="7e8a696a650034f85d397bb3fc8ccd9dcd116f9d100b2aae7e7cbe070d1396e7"
        or ev.get("b04_same_b01_baseline") is not True
        or ev.get("b04_current_manifest_summaries_are_self_reported") is not True
        or ev.get("b04_reported_physical_count")!=617
        or ev.get("b01_verified_physical_count")!=648
        or ev.get("b04_reported_ids_are_subset_of_b01") is not True
        or ev.get("short_id_collector_fixed_package_available") is not True
        or ev.get("b04_collector_regex_bug")!="Map([0-9]{3,5}) excludes Map IDs with 1-2 digits"
        or ev.get("b04_unreported_b01_map_ids")!=[1,22,32,33,42,43,48,*range(76,100)]):
        blocked("divergencia B04 617/648 foi ocultada ou adulterada")
    occupied=expand(cat["occupied"]["ranges"],limit=999)
    observed_base={1,22,32,33,42,43,48}|set(range(76,276))
    claims={
       "KANTO":set(range(300,442)),
       "JOHTO":set(range(600,700)),
       "HOENN":set(range(700,899))
    }
    if (occupied != (observed_base | set.union(*claims.values()))
        or len(occupied)!=648
        or cat["occupied"]["total"]!=648
        or b01.get("conservative_1_to_599_physically_vacant_count")!=250
        or b01.get("native_occupied_by_range")!={"1-599":349,"600-699":100,
              "700-799":100,"800-899":99,"900-999":0}):
        blocked("MapIDs ocupados nao correspondem ao inventario B01")
    for name,ids in claims.items():
        item=cat["occupied"]["identified_from_regional_manifests"][name]
        expected_hash={
          "KANTO":"cd4c07603222de90ba20cbe92befd100b90de617333f135f95993ac2d2d62372",
          "JOHTO":"bdce76a0d6d32c2d8f5ad7a1f9bb765dfd2e3ff748e7a2ea18a4f1cbbc737c0b",
          "HOENN":"78a13097149b5005dc3b014a9dc25eb61912bb36d159e84946127bce526494f7"
        }[name]
        if (expand(item["ranges"],limit=999)!=ids or item["count"]!=len(ids)
            or item["manifest_sha256"]!=expected_hash):
            blocked("proveniencia instalada divergente: "+name)
    other=cat["occupied"]["base_or_other_manifest_unattributed"]
    if expand(other["ranges"])!=observed_base or other["count"]!=207:
        blocked("base ou mapas nao classificados omitidos")
    sinnoh=cat["sinnoh"]
    hold=sinnoh["administrative_planning_hold"]
    if (hold!={"start":442,"end":517,"count":76}
        or sinnoh["id_holds_only"] is not True
        or sinnoh["native_reserved_or_allocated"] is not False
        or sinnoh["source_to_destination_mapping_done"] is not False
        or sinnoh["future_region_reservations_verified"] is not False
        or sinnoh["can_install"] is not False
        or sinnoh["source_maps_with_terrain"]!=54
        or sinnoh["source_maps_empty_terrain"]!=22):
        blocked("retencao administrativa de Sinnoh nao e instalacao")
    hold_ids=set(range(hold["start"],hold["end"]+1))
    if hold_ids&occupied:blocked("reserva de planejamento Sinnoh conflita com base")
    low=set(range(1,600))
    vacant=low-occupied
    if len(vacant)!=250:blocked("250 vagas fisicas B01 nao conferem")
    allowed=vacant-hold_ids
    row=cat["unova"]
    if (expand(row["candidate_ranges"])!=allowed
        or len(allowed)!=174
        or row["candidate_ids_not_occupied_or_sinnoh_held_1_to_599"]!=174
        or row["preferred_contiguous_candidate"]!={"start":518,"end":599,"count":82}
        or row["already_allocated_shared_map_ids"] is not False
        or row["reservation_confirmed"] is not False
        or row["can_install"] is not False
        or row["requires_review_of_future_claims"] is not True):
        blocked("Unova colide com Sinnoh/outros mapas ou foi aprovada indevidamente")
    if (cat["excluded"]!={"johto_protected":{"start":600,"end":699,"count":100},
        "hoenn_protected":{"start":700,"end":999,"count":300,"currently_occupied":199},
        "four_digit_mapids":"NOT_HOMOLOGATED"}):
        blocked("blocos protegidos Johto/Hoenn/1000+ alterados")
    if (cat["constraints"]!={"cannot_claim_all_future_reservations_verified":True,
        "do_not_override_other_regions":True,"no_native_gameplay_test":True,
        "r07_complete":False,"b_approved":0,"c_approved":0,"d_approved":0}):
        blocked("barras/provas nativas forjadas")
    if (unova.get("region")!="UNOVA"
        or unova.get("state")!="PLANNED_REFERENCE_ONLY"
        or unova.get("may_install") is not False
        or any(a.get("destination_map_id") is not None for a in unova.get("areas",[]))):
        blocked("Unova ja possui MapID instalado ou catalogo alterado")
    return {
      "schema":1,"region":"MULTIREGION","stage":"SINNOH_B05_UNOVA_MAPID_PLANNING",
      "status":"PLANNING_HOLD_ONLY_NATIVE_RESERVATION_UNVERIFIED",
      "occupied_count":648,"b04_legacy_omissions":31,
      "sinnoh_admin_hold_count":76,"sinnoh_hold":[442,517],
      "unova_physical_candidates_count":174,"unova_largest_contiguous":[518,599],
      "future_reservations_verified":False,"unova_allocated":False,
      "sinnoh_installed":False,"r07_complete":False,
      "can_install":False,"native_gameplay_tested":False,
      "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0
    }

def run(root=ROOT):
    root=Path(root)
    return audit(
      load(root/"data/regions/sinnoh-b05-mapid-planning.json"),
      load(root/"data/regions/sinnoh-b01-actual-native.json"),
      load(root/"data/regions/sinnoh-b03-installer-evidence.json"),
      load(root/"data/regions/unova-u03-areas.json")
    )

if __name__=="__main__":
    try:
        print(json.dumps(run(),indent=2,ensure_ascii=False))
        print("SINNOH_B05_UNOVA_MAPID_PLANNING_OK_NOT_NATIVE_APPROVED")
    except (OSError,ValueError,TypeError,KeyError,IndexError) as exc:
        print(str(exc),file=sys.stderr)
        sys.exit(2)
