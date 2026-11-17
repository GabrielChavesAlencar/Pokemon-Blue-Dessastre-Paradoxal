#!/usr/bin/env python3
"""B04 V2 receipt: verify recorded full 648 MapID set against the B01/B05 baseline.
Never infers future region ownership, tests the Game.exe, or assigns MapIDs.
The actual private Windows ZIP was reviewed when the receipt was created;
its contents are NOT checked by this repo-only metadata audit.
"""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from audit_sinnoh_b05_mapid_planning import expand

RECEIPT=ROOT/"data/regions/sinnoh-b04-v2-validated.json"
B01=ROOT/"data/regions/sinnoh-b01-actual-native.json"
B05=ROOT/"data/regions/sinnoh-b05-mapid-planning.json"
OLD=ROOT/"data/regions/sinnoh-b04-rerun-receipt.json"
ZIP_SHA="b7341ac4e457c6b1a8b8c7271357e23e5b3316df08387bd05e3ae4bb1e31a8a9"
JSON_SHA="8e5545f831df9927c19df078762da424a777c4c85cf68a71661d61e7b848934f"
EXPECTED_MANIFEST_HASHES={
  "KANTO":"cd4c07603222de90ba20cbe92befd100b90de617333f135f95993ac2d2d62372",
  "JOHTO":"bdce76a0d6d32c2d8f5ad7a1f9bb765dfd2e3ff748e7a2ea18a4f1cbbc737c0b",
  "HOENN":"78a13097149b5005dc3b014a9dc25eb61912bb36d159e84946127bce526494f7",
}
EXPECTED_CLAIMS={
  "KANTO":(300,441,142,"blue-kanto-install.json"),
  "JOHTO":(600,699,100,"blue-johto-main-preview.json"),
  "HOENN":(700,898,199,"blue-hoenn-install.json"),
}
LOW_MISSED=[1,22,32,33,42,43,48,*range(76,100)]

def blocked(why):
    raise ValueError("SINNOH_B04_V2_BLOCKED: "+why)

def read(path):
    p=Path(path)
    if p.is_symlink() or not p.is_file() or p.stat().st_size>2_000_000:
        blocked("metadata file missing/unsafe")
    value=json.loads(p.read_text("utf-8"))
    if type(value) is not dict:blocked("invalid metadata object")
    return value

def audit(receipt,b01,b05,old):
    if (receipt.get("schema")!=1 or receipt.get("region")!="SINNOH"
        or receipt.get("stage")!="B04_V2_WINDOWS_COLLECTOR_CONFIRMATION"
        or receipt.get("status")!="B04_V2_FULL_PHYSICAL_INVENTORY_CONFIRMED_MATCHES_B01"
        or receipt.get("uploaded_file_name")!="SINNOH_B04_PROVENIENCIA_REGIONAL_V2.zip"
        or receipt.get("uploaded_zip_sha256")!=ZIP_SHA
        or receipt.get("uploaded_json_canonical_sha256")!=JSON_SHA
        or receipt.get("mapinfos_sha256")!=b01.get("mapinfos_sha256")
        or receipt.get("tilesets_sha256")!=b01.get("tilesets_sha256")
        or receipt.get("reference_b01_inventory_sha256")!=b01.get("inventory_archive_sha256")
        or receipt.get("previous_incomplete_report_sha256")!=old.get("uploaded_zip_sha256")
        or receipt.get("new_report_physical_count")!=648
        or receipt.get("reference_b01_physical_count")!=648
        or b01.get("native_occupied_map_count")!=648
        or receipt.get("v2_report_exactly_equals_b01_occupied_set") is not True
        or receipt.get("missing_map_ids_in_v2")!=[]
        or receipt.get("extra_map_ids_in_v2")!=[]
        or receipt.get("recovered_31_omitted_low_ids")!=LOW_MISSED
        or receipt.get("low_ids_recovered_count")!=31
        or old.get("ids_missing_relative_to_b01")!=LOW_MISSED
        or old.get("current_report_physical_count")!=617
        or receipt.get("sinnoh_planning_hold")!=b05.get("sinnoh",{}).get("administrative_planning_hold")
        or receipt.get("unova_physical_candidates")!=b05.get("unova",{}).get("candidate_ids_not_occupied_or_sinnoh_held_1_to_599")
        or receipt.get("unova_largest_contiguous_candidate")!=b05.get("unova",{}).get("preferred_contiguous_candidate")):
        blocked("baseline, collector results, or planning hold changed")
    claimsets=[]
    claims=receipt.get("sources")
    if type(claims) is not dict or set(claims)!=set(EXPECTED_CLAIMS):
        blocked("regional claims missing")
    for region,(start,end,count,filename) in EXPECTED_CLAIMS.items():
        item=claims[region]
        pinned=b05["occupied"]["identified_from_regional_manifests"][region]
        if (type(item) is not dict
            or item.get("manifest_sha256")!=EXPECTED_MANIFEST_HASHES[region]
            or item["manifest_sha256"]!=pinned["manifest_sha256"]
            or item.get("reported_map_count")!=count
            or item.get("destination_ranges")!=[{"start":start,"end":end,"count":count}]
            or item.get("manifest_source")!=filename
            or item.get("report_matches_known_contract") is not True):
            blocked("region mapping changed or unverified")
        claimsets.append(set(range(start,end+1)))
    occupied=expand(b05["occupied"]["ranges"],limit=999)
    expected=set.union(*claimsets)|{1,22,32,33,42,43,48}|set(range(76,276))
    if (occupied!=expected or len(occupied)!=648
        or sum(len(x) for x in claimsets)!=441
        or len(set.union(*claimsets))!=441):
        blocked("648 physical MapIDs/regions do not match catalog")
    for key in ("future_region_reservations_verified","unova_ids_allocated",
                "game_exe_tested","joiplay_tested","r07_complete","r08_complete",
                "r09_complete","game_or_saves_modified"):
        if receipt.get(key) is not False:blocked("false gameplay/reservation approval: "+key)
    if (receipt.get("sinnoh_planning_only_not_natively_reserved") is not True
        or receipt.get("source_and_destination_mapids_not_assigned") is not True
        or receipt.get("installed_claims_are_self_reported_not_independently_attested") is not True):
        blocked("falsely claiming independent installation attestation")
    for key in ("phase_b_approved","phase_c_approved","phase_d_approved"):
        if receipt.get(key)!=0:blocked("bar falsely approved")
    return {
       "region":"SINNOH","stage":"B04_V2",
       "status":"FULL_INVENTORY_RECONCILED_TO_B01_NATIVE_INSTALL_NOT_APPROVED",
       "physical_map_id_count":648,"previously_missing_ids_now_reported":31,
       "regional_manifest_counts":{"KANTO":142,"JOHTO":100,"HOENN":199},
       "sinnoh_admin_hold":[442,517],
       "unova_candidate_count":174,"unova_candidate_contiguous":[518,599],
       "future_reservations_verified":False,
       "can_install":False,"r07_complete":False,
       "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0
    }

def run():
    return audit(read(RECEIPT),read(B01),read(B05),read(OLD))

def main():
    try:
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        print("SINNOH_B04_V2_FULL_INVENTORY_RECONCILED_NOT_NATIVE_APPROVED")
    except (OSError,ValueError,TypeError,KeyError,UnicodeError) as err:
        print(str(err),file=sys.stderr)
        return 2
    return 0

if __name__=="__main__":raise SystemExit(main())
