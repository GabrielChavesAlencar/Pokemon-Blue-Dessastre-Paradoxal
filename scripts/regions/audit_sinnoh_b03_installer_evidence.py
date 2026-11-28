#!/usr/bin/env python3
"""B03 Sinnoh: fail-closed source-claim and tileset review, without allocation.

Reads repo-only metadata + reviewed installer source text, never game/, saves,
RXDATA or user paths, never executes installers or distributes donor assets.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from audit_sinnoh_b02_reservations import expected as expected_b02, read

B00=ROOT/"data/regions/sinnoh-b00-actual-source.json"
B01=ROOT/"data/regions/sinnoh-b01-actual-native.json"
B02=ROOT/"data/regions/sinnoh-b02-reservations.json"
CH05=ROOT/"data/regions/sinnoh-map-id-reservations.json"
B03=ROOT/"data/regions/sinnoh-b03-installer-evidence.json"
TEMPLATES=ROOT/"data/regions/sinnoh-b03-reservation-review-templates.json"
EXPECTED_FILES={
"KANTO":"scripts/regions/install_kanto.py",
"JOHTO":"scripts/regions/johto_main_preview.py",
"HOENN":"scripts/regions/pilot_hoenn.py",
"SINNOH_CONVERTER":"scripts/regions/convert_sinnoh_geometry.py",
}
EXPECTED_SNIPPETS={
"KANTO":(
  'mapping = {int(k): int(v) for k, v in info["maps"].items()}',
  'atomic(game / "Data/blue-kanto-install.json",',
  'raise ValueError("Kanto ja instalado: recusar IDs duplicados.")',
),
"JOHTO":(
  'PREVIEW_IDS = frozenset(range(600, 700))',
  'PROOF = "Data/blue-johto-main-preview.json"',
  'new_id = len(new_tiles)', 'remap[old_id] = new_id',
),
"HOENN":(
  'free = [n for n in range(700, 1000) if n not in reserved]',
  'occupied = set(native_infos) | disk_ids',
  'reserved |= foreign',
  'tile_ids[native_id] = len(native_tiles)',
),
"SINNOH_CONVERTER":(
  'new_id = len(output_tiles)',
  'new_attrs["@autotile_names"] = [',
  '"@tileset_id": tileset_map[old_tile]',
)
}
CLAIMS={
  "KANTO":"INSTALLED_DYNAMIC_MAPPING_ONLY",
  "JOHTO":"PREVIEW_600_TO_699_CODE_CONSTRAINT",
  "HOENN":"DYNAMIC_700_TO_999_WITH_PBS_OCCUPANCY",
  "SINNOH_CONVERTER":"APPEND_ONLY_TILESET_CONVERSION_NOT_RUN"
}
PROOFS={
 "KANTO":"game/Data/blue-kanto-install.json",
 "JOHTO":"game/Data/blue-johto-main-preview.json",
 "HOENN":"game/Data/blue-hoenn-install.json",
 "SINNOH_CONVERTER":None,
}

def blocked(message):
    raise ValueError("SINNOH_B03_BLOCKED: "+message)

def constructed_templates(native):
    baseline=native["mapinfos_sha256"]
    return {
      "schema":1,"region":"SINNOH","step":"B03",
      "kind":"LOCAL_FUTURE_RESERVATION_INPUT_TEMPLATES_ONLY",
      "baseline_mapinfos_sha256":baseline,
      "records":{region:{
          "schema":1,"region":region,
          "kind":"LOCAL_FUTURE_MAP_ID_RESERVATIONS",
          "baseline_mapinfos_sha256":baseline,
          "future_reserved_map_ids":[],
          "ownership_evidence":"","reviewed_locally":False,"read_only":True
      } for region in ("KANTO","JOHTO","HOENN")},
      "user_review_done":False,"can_use_as_r07_evidence":False,
      "auto_approval":False,
      "guidance":"These are unreviewed templates, not valid R07 evidence. Only actual future reserved IDs backed by installer/project files may be entered and locally reviewed. Empty arrays do not prove no future reservations."
    }

def constructed_evidence(b00,b01,b02,ch05,root=ROOT):
    expected_b02(b00,b01,ch05,root=Path(root))
    if (type(b02) is not dict
        or b02.get("status")!="DOCUMENTED_RESERVATIONS_REVIEWED_FUTURE_CLAIMS_UNVERIFIED"
        or b02.get("native_inventory_sha256")!=b01["inventory_archive_sha256"]
        or b02.get("native_mapinfos_sha256")!=b01["mapinfos_sha256"]
        or b02.get("sinnoh_destination_map_ids")!={}
        or b02.get("sinnoh_original_collision_count")!=72
        or b02.get("physical_vacant_1_to_599")!=250
        or b02.get("all_future_reservations_verified") is not False
        or b02.get("phase_b_approved")!=0):
        blocked("B02 nao corresponde ao inventario real recebido")
    claims=ch05["documented_shared_reservations"]
    expected_claims=[
      {"region":"JOHTO","start":600,"end":699,"kind":"PREVIEW_CODE_CLAIM"},
      {"region":"HOENN","start":700,"end":999,"kind":"INSTALLER_CODE_RANGE"},
    ]
    if ([(c["owner"],c["start"],c["end"]) for c in claims]!=
         [("JOHTO",600,699),("HOENN",700,999)]
        or b01["native_tileset_count"]!=70
        or b01["native_and_donor_tileset_names_match"] is not False
        or b01["conservative_1_to_599_physically_vacant_count"]!=250
        or b01["conservative_1_to_599_physically_vacant_ranges"][-1]!=
           {"first":442,"last":599,"count":158}
        or len(b00["terrain_filled_ids"])!=54
        or len(b00["empty_terrain_ids"])!=22):
        blocked("base B01/B00 divergiu ou mudou tileset")
    evidence=[]
    for region in ("KANTO","JOHTO","HOENN","SINNOH_CONVERTER"):
        evidence.append({
          "region":region,"file":EXPECTED_FILES[region],
          "entries":list(EXPECTED_SNIPPETS[region]),
          "proof_file":PROOFS[region],"claim":CLAIMS[region],
          "future_reservation_ids":[],"future_reviewed":False,
          "actual_mapping_available_in_upload":False
        })
    return {
      "schema":1,"region":"SINNOH","workstream":"B","stage":"B03",
      "status":"INSTALLER_EVIDENCE_AUDITED_REVIEW_TEMPLATES_READY_NOT_INSTALLABLE",
      "evidence_date":"2026-11-17",
      "donor_zip_sha256":b00["source_zip_sha256"],
      "native_inventory_sha256":b01["inventory_archive_sha256"],
      "native_mapinfos_sha256":b01["mapinfos_sha256"],
      "native_tilesets_sha256":b01["tilesets_sha256"],
      "source_tree_map_count":76,"source_with_terrain":54,
      "source_empty_terrain":22,"installed_physical_map_count":648,
      "source_original_id_collisions":72,
      "code_protected_ranges":expected_claims,
      "range_1_to_599_vacant_count":250,
      "illustrative_contiguous_window":{
         "start":442,"end":517,"length":76,
         "physical_snapshot_vacant_only":True,
         "future_claims_checked":False,"selected_as_destinations":False},
      "native_occupied_status":"OBSERVED_SNAPSHOT_NOT_OWNERSHIP_PROOF",
      "code_evidence":evidence,"future_reservations_reconciled":False,
      "installer_mapping_files_received":False,
      "reservation_review_templates":"data/regions/sinnoh-b03-reservation-review-templates.json",
      "confirmed_future_ids_kanto":[],
      "confirmed_future_ids_johto":[],
      "confirmed_future_ids_hoenn":[],
      "destination_mapping":{},
      "tileset_strategy":{
        "mode":"APPEND_WITH_NEW_NATIVE_IDS_AFTER_RIGHTS_AND_BASELINE_RECHECK_ONLY",
        "native_tileset_table_reported_length":70,
        "donor_to_native_index_mapping":{},"materialized_new_tilesets":0,
        "donor_tile_ids":[
         {"donor_id":i,"donor_name":b01["donor_tilesets"][str(i)],
          "current_native_name":b01["installed_tilesets"][str(i)],
          "new_native_id":None,"graphics_and_rights_verified":False}
         for i in (1,31)
        ],
        "must_rewrite_map_tileset_ids":True,
        "must_verify_autotile_names_and_files":True,
        "must_preserve_existing_native_tilesets":True,
        "may_reuse_numeric_source_ids":False,
        "rights_cleared":False,
        "dry_run_executed_against_real_donor":False,
      },
      "protect_other_regions":True,
      "audited_native_ownership_for_all_ids":False,
      "kanto_dynamic_mapping_verified_from_native_manifest":False,
      "johto_native_manifest_verified":False,
      "hoenn_native_manifest_verified":False,
      "r07_complete":False,"r08_complete":False,"r09_complete":False,
      "native_game_exe_tested":False,"joiplay_tested":False,
      "can_generate_installable_remap":False,"can_install":False,
      "can_mark_playable":False,
      "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
      "game_or_saves_modified":False,
      "note":"B03 is an offline review of source code claims and a hypothetical physical window, not a reservation or mapping. Installed provenance markers and per-asset rights are not in the B01 ZIP."
    }

def audit(manifest,templates,b00,b01,b02,ch05,*,root=ROOT):
    expected=constructed_evidence(b00,b01,b02,ch05,root=root)
    if type(manifest) is not dict or manifest!=expected:
        blocked("manifesto B03 nao corresponde a fontes; mapeamento ou aceite forjado")
    if type(templates) is not dict or templates!=constructed_templates(b01):
        blocked("modelos foram alterados: NENHUMA reserva futura foi validada")
    for item in manifest["code_evidence"]:
        file=Path(root)/item["file"]
        if file.is_symlink() or not file.is_file() or file.stat().st_size>600_000:
            blocked("fonte do instalador ausente/insegura: "+item["file"])
        content=file.read_text("utf-8")
        if any(marker not in content for marker in item["entries"]):
            blocked("contrato de instalador ou converter alterado: "+item["region"])
    # Explicitly reject copying the hypothetical block into a real mapping:
    # it is just 76 *physically vacant* slots, not protected future ownership.
    return {
       "region":"SINNOH","stage":"B03",
       "status":"INSTALLER_EVIDENCE_REVIEWED_R07_STILL_BLOCKED",
       "source_installer_evidence_files":len(manifest["code_evidence"]),
       "protected_johto_ids_by_code":100,
       "protected_hoenn_ids_by_code":300,
       "native_observed_occupied_map_ids":648,
       "physical_low_band_vacancies":250,
       "hypothetical_442_to_517_window_only":True,
       "future_reservation_manifests_verified":0,
       "new_tileset_id_assigned":False,
       "can_apply_mapping":False,"can_install":False,
       "r07_complete":False,"phase_b_approved":0,
       "game_or_saves_modified":False
    }

def run(root=ROOT):
    root=Path(root)
    return audit(
      read(root/"data/regions/sinnoh-b03-installer-evidence.json"),
      read(root/"data/regions/sinnoh-b03-reservation-review-templates.json"),
      read(root/"data/regions/sinnoh-b00-actual-source.json"),
      read(root/"data/regions/sinnoh-b01-actual-native.json"),
      read(root/"data/regions/sinnoh-b02-reservations.json"),
      read(root/"data/regions/sinnoh-map-id-reservations.json"),
      root=root
    )

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        print("SINNOH_B03_SOURCE_CLAIMS_AND_TILESET_PLAN_OK_OFFLINE")
        return 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError) as err:
        print(str(err),file=sys.stderr)
        return 2
if __name__=="__main__":raise SystemExit(main())
