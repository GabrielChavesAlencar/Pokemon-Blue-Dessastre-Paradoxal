#!/usr/bin/env python3
"""A16: offline fail-closed receipt verification; no native asset or save IO.

SHA-256 validates internal metadata consistency, NOT source authenticity,
license, human approval, runtime QA or native installability. --verify-json
reads one explicitly selected and bounded sanitized .json only.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any
import audit_unova_a15_native_readiness as a15

ROOT=Path(__file__).resolve().parents[2]
CONTRACT="data/regions/unova-a16-receipt-contract.json"
SCHEMA="data/regions/unova-a16-receipt.schema.json"
REGIONS=("DECADES","KANTO","JOHTO","HOENN","SINNOH","UNOVA")
STAGES=a15.STAGES
MODES=("SYNTHETIC_FIXTURE","REDACTED_UNVERIFIED")
MAX_BUNDLE_BYTES=131072
HEX64=re.compile(r"^[0-9a-f]{64}$")
ROOT_KEYS={"schema_version","phase","region","campaign","mode","status",
 "source_baseline","regional_manifests","regional_manifests_sha256",
 "intro_map001","intro_map001_sha256","rights","receipts","protections",
 "native_technical_completed","native_playable_completed",
 "can_reserve_mapids","can_install","can_release","bundle_sha256"}
BASE_KEYS={"identity","evidence_origin","mapinfos_sha256","mapids_observed",
 "mapid_inventory_sha256","independent_recheck","source_revision",
 "unova_candidate_range","sinnoh_hold","assigned_mapids"}
MANIFEST_KEYS={"source_status","source_sha256","source_revision","native_claims"}
EVENT_KEYS={"map_id","event_id","page","destination_map_id","evidence_status"}
INTRO_KEYS={"events","mapid_3_resolved","computed_destinations_unresolved",
 "script_runtime_verified"}
RIGHTS_KEYS={"asset_review_status","source_rights_sha256","license_verified",
 "redistribution_approved","human_decision","approval_receipt_sha256"}
RECEIPT_KEYS={"schema_version","stage","mode","status","depends_on",
 "baseline_sha256","mapinfos_sha256","mapids_inventory_sha256",
 "source_revision","regional_manifests_sha256","map001_evidence_sha256",
 "previous_receipt_sha256","source_report_sha256","rights_status",
 "human_review","runtime_qa","mapids_reserved","installable",
 "receipt_sha256"}
PROTECTION_KEYS={"rights_verified","human_approved","mapids_reserved",
 "native_install_approved","windows_game_exe_qa","android_joiplay_qa",
 "saves_read","saves_written"}
CONTRACT_KEYS={"schema_version","phase","region","campaign","status","sources",
 "input_policy","next_step","evidence_absence","required_native_gates",
 "required_technical_receipts","native_technical_completed",
 "native_playable_completed","github_g_completed","region_status",
 "can_reserve_mapids","can_install","can_release","notes"}
SOURCES={"a15":a15.FILE,
 "a15_validator":"scripts/regions/audit_unova_a15_native_readiness.py",
 "a05":a15.SOURCES["historical_mapids"],
 "unova_region":a15.SOURCES["region_registry"],
 "progress":a15.SOURCES["github_tracker"],
 "g08":a15.SOURCES["prior_G08"],"schema":SCHEMA}
POLICY={"accepted_types":["application/json"],
 "max_bundle_bytes":MAX_BUNDLE_BYTES,"max_receipts":11,
 "exact_order":list(STAGES),"modes":list(MODES),
 "path_fields_allowed":False,"raw_asset_bytes_allowed":False,
 "raw_saves_allowed":False,"source_filenames_allowed":False,
 "operator_receipt_files_opened_automatically":False,
 "provenance_authenticated":False,"sha256_is_not_authenticity":True,
 "requires_source_baseline_reaudit_for_new_revision":True,
 "mapid3_unresolved":True,"preflight_only":True,
 "native_install_allowed":False}
NEXT={"id":"A17",
 "title":"Auditoria humana e conciliação de recibos A04–A14 independentes",
 "requires":["redacted receipts reviewed individually",
             "MapInfos recheck same snapshot",
             "regional manifest origin audit",
             "resolve Map001 intro destination 3",
             "rights evidence original reviewed off-GitHub"],
 "cannot_auto_approve":True,"cannot_reserve_mapids":True,
 "cannot_install_maps":True,"cannot_change_save_data":True}
ABSENT={"current_game_mapinfos_verified":False,
 "current_source_maps_verified":False,"current_mapid_ownership_verified":False,
 "source_licenses_verified":False,"game_exe_runtime_verified":False,
 "joiplay_runtime_verified":False,"assets_redistribution_approved":False,
 "independent_human_approved":False}

def deny(message:str)->None:
    raise ValueError("UNOVA_A16_BLOCKED: "+message)

def exact(obj:Any,fields:set[str],where:str)->dict:
    if type(obj) is not dict or set(obj)!=fields:
        deny(where+" has missing or unrecognized properties")
    return obj

def equal(actual:Any,expected:Any,where:str)->None:
    if type(actual) is not type(expected) or actual!=expected:
        deny(where+" inconsistent with A15 unverified source policy")

def sha(value:Any,where:str,allow_null:bool=False)->None:
    if value is None and allow_null:return
    if type(value) is not str or HEX64.fullmatch(value) is None:
        deny(where+" requires lowercase SHA-256"+(" or null" if allow_null else ""))

def canonical(obj:Any)->bytes:
    try:
        return json.dumps(obj,sort_keys=True,separators=(",",":"),
                          ensure_ascii=True,allow_nan=False).encode("ascii")
    except (TypeError,ValueError,RecursionError) as exc:
        deny("noncanonical JSON: "+type(exc).__name__)

def digest(obj:Any)->str:
    return hashlib.sha256(canonical(obj)).hexdigest()

def receipt_digest(obj:dict)->str:
    return digest({k:v for k,v in obj.items() if k!="receipt_sha256"})

def bundle_digest(obj:dict)->str:
    return digest({k:v for k,v in obj.items() if k!="bundle_sha256"})

def safe_decode(raw:bytes)->dict:
    if type(raw) is not bytes or not 2<=len(raw)<=MAX_BUNDLE_BYTES:
        deny("expected sanitized JSON metadata under 128 KiB")
    if raw.startswith(b"\xef\xbb\xbf"):deny("JSON BOM not allowed")
    def pairs(values):
        obj={}
        for k,v in values:
            if k in obj:deny("duplicate JSON key: "+str(k)[:40])
            obj[k]=v
        return obj
    def invalid(value):
        deny("invalid JSON nonfinite value: "+value)
    try:
        obj=json.loads(raw.decode("utf-8"),object_pairs_hook=pairs,
                       parse_constant=invalid)
    except (UnicodeError,json.JSONDecodeError,RecursionError) as e:
        deny("malformed sanitized JSON: "+type(e).__name__)
    if len(canonical(obj))>MAX_BUNDLE_BYTES:
        deny("canonical sanitized JSON too large")
    return obj

def safe_read_receipt_json(path:Path)->dict:
    """Never automatically reads source/report paths mentioned inside JSON."""
    file=Path(path)
    if file.suffix.lower()!=".json" or file.is_symlink() or not file.is_file():
        deny("explicit non-symlink .json metadata file required")
    if file.stat().st_size>MAX_BUNDLE_BYTES:
        deny("JSON metadata file exceeds size limit")
    return safe_decode(file.read_bytes())

def audit_catalog(root:Path=ROOT)->dict:
    root=Path(root)
    a15.validate_document(a15.read_json(root,a15.FILE),root)
    policy=a15.read_json(root,CONTRACT)
    exact(policy,CONTRACT_KEYS,"A16 policy")
    expected={"schema_version":1,"phase":"A16","region":"UNOVA",
      "campaign":"WHITE_BW","status":"REDACTED_RECEIPT_VALIDATION_ONLY",
      "sources":SOURCES,"input_policy":POLICY,"next_step":NEXT,
      "evidence_absence":ABSENT,"required_native_gates":8,
      "required_technical_receipts":11,"native_technical_completed":0,
      "native_playable_completed":0,"github_g_completed":32,
      "region_status":"planned","can_reserve_mapids":False,
      "can_install":False,"can_release":False}
    for key,val in expected.items():equal(policy[key],val,"contract."+key)
    if (type(policy["notes"]) is not list or len(policy["notes"])<6
        or any(type(n) is not str or len(n)<40 for n in policy["notes"])):
        deny("A16 source safety limitations missing")
    schema=a15.read_json(root,SCHEMA)
    if (schema.get("$schema")!="https://json-schema.org/draft/2020-12/schema"
        or schema.get("type")!="object"
        or schema.get("additionalProperties") is not False
        or set(schema.get("required",[]))!=ROOT_KEYS
        or set(schema.get("properties",{}))!=ROOT_KEYS):
        deny("A16 schema root mismatch")
    nested={"source_baseline":BASE_KEYS,
            "regional_manifests":set(REGIONS),"intro_map001":INTRO_KEYS,
            "rights":RIGHTS_KEYS,"protections":PROTECTION_KEYS}
    for k,keys in nested.items():
        p=schema["properties"][k]
        if (p.get("type")!="object"
            or p.get("additionalProperties") is not False
            or set(p.get("required",[]))!=keys
            or set(p.get("properties",{}))!=keys):
            deny("A16 schema child drift: "+k)
    receipt_schema=schema["properties"]["receipts"]
    row=receipt_schema.get("items",{})
    if (receipt_schema.get("minItems")!=11
        or receipt_schema.get("maxItems")!=11
        or row.get("additionalProperties") is not False
        or set(row.get("required",[]))!=RECEIPT_KEYS
        or set(row.get("properties",{}))!=RECEIPT_KEYS):
        deny("A16 receipt SHA chain schema drift")
    consts={"schema_version":1,"phase":"A16","region":"UNOVA",
      "status":"UNVERIFIED_OFFLINE_RECEIPT_CHAIN",
      "native_technical_completed":0,"native_playable_completed":0,
      "can_install":False,"can_reserve_mapids":False,"can_release":False}
    for k,v in consts.items():
        equal(schema["properties"][k].get("const"),v,"schema."+k)
    equal(schema["properties"]["source_baseline"]["properties"]
          ["mapinfos_sha256"].get("const"),
          a15.EXPECTED_HISTORY["mapinfos_sha256"],"schema historical MapInfos")
    return {"phase":"A16","status":"SCHEMA_SOURCE_GATES_VERIFIED_NOT_NATIVE_APPROVED",
      "schema_draft":"2020-12","stages":11,"native_gates_pending":8,
      "evidence_mode":"UNVERIFIED_METADATA_ONLY",
      "can_install":False,"can_reserve_mapids":False,
      "native_technical_completed":0,"native_playable_completed":0,
      "github_g_completed":32,"native_files_read":0,"saves_read":False}

def validate_bundle(bundle:Any,matrix:dict|None=None)->dict:
    """Pure metadata verification; NO native authenticity is claimed."""
    if matrix is None:matrix=a15.read_json(ROOT,a15.FILE)
    exact(bundle,ROOT_KEYS,"A16 receipt bundle")
    expected={"schema_version":1,"phase":"A16","region":"UNOVA",
      "campaign":"WHITE_BW","status":"UNVERIFIED_OFFLINE_RECEIPT_CHAIN",
      "native_technical_completed":0,"native_playable_completed":0,
      "can_reserve_mapids":False,"can_install":False,"can_release":False}
    for k,v in expected.items():equal(bundle[k],v,"bundle."+k)
    mode=bundle["mode"]
    if type(mode) is not str or mode not in MODES:deny("unknown receipt mode")
    baseline=exact(bundle["source_baseline"],BASE_KEYS,"baseline")
    history=matrix["historical_snapshot"]
    required={"identity":"B01_B04_B05_HISTORICAL_UNVERIFIED_2026_11_17",
      "evidence_origin":"USER_REPORTED_HISTORICAL_UNVERIFIED",
      "mapinfos_sha256":history["mapinfos_sha256"],
      "mapids_observed":history["physically_observed_mapids"],
      "independent_recheck":False,"source_revision":"HISTORICAL_UNVERIFIED",
      "assigned_mapids":[]}
    for k,v in required.items():equal(baseline[k],v,"baseline."+k)
    sha(baseline["mapid_inventory_sha256"],"baseline inventory",True)
    ranges=[
      ("unova_candidate_range",{"start":518,"end":599,"count":82,"reserved":False}),
      ("sinnoh_hold",{"start":442,"end":517,"count":76,"native_reservation":False}),
    ]
    for name,expected_range in ranges:
        d=exact(baseline[name],set(expected_range),name)
        for k,v in expected_range.items():equal(d[k],v,name+"."+k)
    base_hash=digest(baseline)
    manifests=exact(bundle["regional_manifests"],set(REGIONS),"regional manifests")
    for region,manifest in manifests.items():
        exact(manifest,MANIFEST_KEYS,"manifest "+region)
        for k,v in {"source_status":"UNVERIFIED_SOURCE_METADATA_ONLY",
                    "source_revision":"UNVERIFIED","native_claims":[]}.items():
            equal(manifest[k],v,"manifest "+region+"."+k)
        sha(manifest["source_sha256"],"manifest source digest",True)
    sha(bundle["regional_manifests_sha256"],"manifest metadata fingerprint")
    if bundle["regional_manifests_sha256"]!=digest(manifests):
        deny("regional manifest SHA-256 mismatched")
    intro=exact(bundle["intro_map001"],INTRO_KEYS,"intro Map001")
    if type(intro["events"]) is not list or len(intro["events"])!=2:
        deny("Map001 missing two historical intro events")
    for i,item in enumerate(intro["events"],1):
        exact(item,EVENT_KEYS,"intro event")
        for k,v in {"map_id":1,"event_id":i,"page":1,
                    "destination_map_id":3,
                    "evidence_status":"USER_REPORTED_UNVERIFIED"}.items():
            equal(item[k],v,"intro event "+str(i)+"."+k)
    for k,v in {"mapid_3_resolved":False,
                "computed_destinations_unresolved":20,
                "script_runtime_verified":False}.items():
        equal(intro[k],v,"intro."+k)
    sha(bundle["intro_map001_sha256"],"intro evidence fingerprint")
    if bundle["intro_map001_sha256"]!=digest(intro):
        deny("intro Map001 event SHA-256 mismatch")
    rights=exact(bundle["rights"],RIGHTS_KEYS,"rights and attribution")
    for k,v in {"asset_review_status":"REVIEW_REQUIRED_NOT_LICENSED",
                "license_verified":False,"redistribution_approved":False,
                "human_decision":"NOT_REVIEWED",
                "approval_receipt_sha256":None}.items():
        equal(rights[k],v,"rights."+k)
    sha(rights["source_rights_sha256"],"rights metadata",True)
    flags=exact(bundle["protections"],PROTECTION_KEYS,"native protections")
    for k in PROTECTION_KEYS:equal(flags[k],False,"protections."+k)
    receipts=bundle["receipts"]
    if type(receipts) is not list or len(receipts)!=len(STAGES):
        deny("eleven A04-A14 receipt stages required")
    previous=None
    for stage,item in zip(matrix["steps"],receipts):
        exact(item,RECEIPT_KEYS,"receipt "+stage["id"])
        wanted={"schema_version":1,"stage":stage["id"],
            "mode":mode,"status":"AWAITING_INDEPENDENT_REVIEW",
            "depends_on":stage["depends_on"],"baseline_sha256":base_hash,
            "mapinfos_sha256":baseline["mapinfos_sha256"],
            "mapids_inventory_sha256":baseline["mapid_inventory_sha256"],
            "source_revision":baseline["source_revision"],
            "regional_manifests_sha256":bundle["regional_manifests_sha256"],
            "map001_evidence_sha256":bundle["intro_map001_sha256"],
            "previous_receipt_sha256":previous,
            "rights_status":"NOT_VERIFIED","human_review":"NOT_REVIEWED",
            "runtime_qa":"NOT_EXECUTED","mapids_reserved":False,"installable":False}
        for k,v in wanted.items():equal(item[k],v,stage["id"]+"."+k)
        sha(item["source_report_sha256"],"source report metadata",True)
        sha(item["receipt_sha256"],"receipt hash")
        if item["receipt_sha256"]!=receipt_digest(item):
            deny("tampered receipt digest: "+stage["id"])
        previous=item["receipt_sha256"]
    sha(bundle["bundle_sha256"],"bundle hash")
    if bundle["bundle_sha256"]!=bundle_digest(bundle):
        deny("bundle SHA-256 mismatch")
    return {"phase":"A16",
        "status":"UNVERIFIED_RECEIPTS_AWAIT_INDEPENDENT_REVIEW",
        "mode":mode,"receipts_verified_for_internal_integrity":11,
        "mapinfos_baseline":"HISTORICAL_USER_REPORTED_NOT_RECHECKED",
        "mapid_3_unresolved":True,
        "regional_manifests_source_verified":False,
        "source_rights_verified":False,"human_approval_verified":False,
        "game_exe_qa_verified":False,"joiplay_qa_verified":False,
        "can_reserve_mapids":False,"can_install":False,"can_release":False,
        "native_technical_completed":0,"native_playable_completed":0}

def synthetic_fixture(matrix:dict|None=None,mode:str="SYNTHETIC_FIXTURE")->dict:
    """Positive fixture is entirely synthetic, never a native evidence receipt."""
    if matrix is None:matrix=a15.read_json(ROOT,a15.FILE)
    if mode not in MODES:deny("unknown fixture mode")
    baseline={"identity":"B01_B04_B05_HISTORICAL_UNVERIFIED_2026_11_17",
      "evidence_origin":"USER_REPORTED_HISTORICAL_UNVERIFIED",
      "mapinfos_sha256":matrix["historical_snapshot"]["mapinfos_sha256"],
      "mapids_observed":648,"mapid_inventory_sha256":None,
      "independent_recheck":False,"source_revision":"HISTORICAL_UNVERIFIED",
      "unova_candidate_range":{"start":518,"end":599,"count":82,"reserved":False},
      "sinnoh_hold":{"start":442,"end":517,"count":76,"native_reservation":False},
      "assigned_mapids":[]}
    manifests={name:{"source_status":"UNVERIFIED_SOURCE_METADATA_ONLY",
       "source_sha256":None,"source_revision":"UNVERIFIED","native_claims":[]}
       for name in REGIONS}
    intro={"events":[{"map_id":1,"event_id":event,"page":1,
          "destination_map_id":3,"evidence_status":"USER_REPORTED_UNVERIFIED"}
          for event in (1,2)],
       "mapid_3_resolved":False,"computed_destinations_unresolved":20,
       "script_runtime_verified":False}
    bundle={"schema_version":1,"phase":"A16","region":"UNOVA",
       "campaign":"WHITE_BW","mode":mode,
       "status":"UNVERIFIED_OFFLINE_RECEIPT_CHAIN",
       "source_baseline":baseline,"regional_manifests":manifests,
       "regional_manifests_sha256":digest(manifests),
       "intro_map001":intro,"intro_map001_sha256":digest(intro),
       "rights":{"asset_review_status":"REVIEW_REQUIRED_NOT_LICENSED",
         "source_rights_sha256":None,"license_verified":False,
         "redistribution_approved":False,"human_decision":"NOT_REVIEWED",
         "approval_receipt_sha256":None},
       "receipts":[],"protections":{key:False for key in PROTECTION_KEYS},
       "native_technical_completed":0,"native_playable_completed":0,
       "can_reserve_mapids":False,"can_install":False,"can_release":False}
    previous=None
    for stage in matrix["steps"]:
        row={"schema_version":1,"stage":stage["id"],"mode":mode,
           "status":"AWAITING_INDEPENDENT_REVIEW",
           "depends_on":stage["depends_on"],
           "baseline_sha256":digest(baseline),
           "mapinfos_sha256":baseline["mapinfos_sha256"],
           "mapids_inventory_sha256":None,
           "source_revision":"HISTORICAL_UNVERIFIED",
           "regional_manifests_sha256":bundle["regional_manifests_sha256"],
           "map001_evidence_sha256":bundle["intro_map001_sha256"],
           "previous_receipt_sha256":previous,
           "source_report_sha256":None,
           "rights_status":"NOT_VERIFIED","human_review":"NOT_REVIEWED",
           "runtime_qa":"NOT_EXECUTED","mapids_reserved":False,
           "installable":False}
        row["receipt_sha256"]=receipt_digest(row)
        previous=row["receipt_sha256"]
        bundle["receipts"].append(row)
    bundle["bundle_sha256"]=bundle_digest(bundle)
    return bundle

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    op=parser.add_mutually_exclusive_group(required=True)
    op.add_argument("--check",action="store_true")
    op.add_argument("--simulate-demo",action="store_true")
    op.add_argument("--print-synthetic-fixture",action="store_true")
    op.add_argument("--verify-json",type=Path,
                    help="explicit sanitized JSON bundle; no paths within payload")
    args=parser.parse_args(argv)
    try:
        result=audit_catalog()
        if args.check:
            print(json.dumps(result,sort_keys=True))
            return 0
        fixture=synthetic_fixture()
        if args.print_synthetic_fixture:
            print(json.dumps(fixture,sort_keys=True,indent=2))
            return 0
        if args.verify_json is not None:
            print(json.dumps(validate_bundle(
                safe_read_receipt_json(args.verify_json)),sort_keys=True))
            return 0
        positive=validate_bundle(fixture)
        negative=copy.deepcopy(fixture)
        negative["receipts"][6]["mapinfos_sha256"]="0"*64
        try:validate_bundle(negative)
        except ValueError:tamper_rejected=True
        else:deny("negative fixture improperly accepted")
        print(json.dumps({"phase":"A16",
          "status":"SYNTHETIC_RECEIPT_CHAIN_VALID_NOT_NATIVE",
          "positive":positive["status"],"tamper_rejected":tamper_rejected,
          "stages":11,"source_verified":False,"rights_verified":False,
          "can_install":False,"can_reserve_mapids":False,
          "native_technical_completed":0,"native_playable_completed":0},
          sort_keys=True))
        return 0
    except (ValueError,KeyError,IndexError,TypeError,OSError,RecursionError) as e:
        print("UNOVA_A16_BLOCKED: "+str(e)[:320])
        return 2

if __name__=="__main__":raise SystemExit(main())
