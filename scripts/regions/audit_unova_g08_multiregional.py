#!/usr/bin/env python3
"""G08.3: six-region offline regression, no installs, saves, native engine or IO writes.

All actions return new Python dictionaries. Runtime routability is only a
synthetic G05.3 allowlist, never proof that a region is installed for a user.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

import audit_unova_g08_integrated as g82
import audit_unova_g05_travel as travel
import audit_unova_g05_regional_items as items
import audit_unova_g05_badges_specials as specials
import audit_unova_g05_blackout_state as blackout
import audit_unova_g07_incremental_manifest as g72
import audit_unova_g07_transaction as g73
import audit_unova_g07_platform_compat as g74

ROOT=Path(__file__).resolve().parents[2]
FILE="data/regions/unova-g08-multiregional-contract.json"
REGIONS=("DECADES","KANTO","JOHTO","HOENN","SINNOH","UNOVA")
ROUTE=("KANTO","HOENN","JOHTO","DECADES","KANTO")
BLOCKED=("SINNOH","UNOVA")
STATUSES={"DECADES":"playable","KANTO":"prototype","JOHTO":"planned",
          "HOENN":"planned","SINNOH":"planned","UNOVA":"planned"}
SOURCES={
 "G08.2":"data/regions/unova-g08-integrated-contract.json",
 "travel":"data/regions/unova-g05-travel-contract.json",
 "regional_items":"data/regions/unova-g05-regional-items-contract.json",
 "badges_specials":"data/regions/unova-g05-badges-specials-contract.json",
 "blackout":"data/regions/unova-g05-blackout-state-contract.json",
 "packages":"data/regions/unova-g07-incremental-contract.json",
 "transaction":"data/regions/unova-g07-transaction-contract.json",
 "platform":"data/regions/unova-g07-platform-compatibility-contract.json",
 "registry":"site/public/data/regions.json",
 "tracker":"site/public/data/unova-github-progress.json",
}
PROFILES=[
 {"id":key,"registry_status":STATUSES[key],
  "runtime_fixture_routable":key in travel.ROUTABLE,
  "native_qa_from_this_suite":False} for key in REGIONS
]
RESOURCES=[
 "regional_HMs","regional_key_items","shared_TMs","badge_achievements",
 "restricted_legendaries_mythicals_UB_paradox","Pokemon_party_and_Boxes",
 "gameplay_progress","center_ownership","remembered_checkpoint",
 "money","coins","mechanics","region_history","save_snapshot_integrity",
 "CAS_and_rollback",
]
FAULTS={
 "travel":list(travel.FAIL_POINTS),
 "blackout":list(blackout.FAULTS),
 "package":list(g73.FAULTS),
}
POLICY={key:True for key in (
 "source_grounded_runtime_allowlist","routable_fixture_never_implies_native_installed",
 "allow_only_synthetic_in_memory_fixtures","blocked_sinnoh_unova",
 "reject_cross_region_hm_and_key_items","preserve_global_tms_and_shared_money",
 "preserve_badges_as_regional_achievements","preserve_region_mechanics",
 "never_reuse_foreign_center","center_requires_verified_region_ownership",
 "preserve_boxes_and_special_restrictions","no_loss_of_user_progress",
 "snapshot_cas_before_commit","full_rollback_on_failure",
 "deny_unverified_payload_rights","no_native_mapids",
 "no_game_exe_or_joiplay_execution","no_save_reads_or_writes",
 "no_real_installer","no_network_requests",
 "native_technical_bar_remains_zero","native_playability_remains_zero",
)}
NATIVE_EVIDENCE={key:None for key in (
 "sinnoh_installed","unova_installed","unova_mapids",
 "unova_runtime_windows","unova_runtime_android",
 "unova_encounter_data","rights_approved","unova_save_qa",
)}
ARTIFACTS={
 "auditor":"scripts/regions/audit_unova_g08_multiregional.py",
 "tests":"tests/test_unova_g08_multiregional.py",
 "documentation":"docs/UNOVA_G08_3_MATRIZ_MULTIRREGIONAL_OFFLINE.md",
}
FIELDS={
 "schema_version","phase","region","campaign","status","sources",
 "regional_profiles","allowed_fixture_route","blocked_native_destinations",
 "covered_resources","failure_points","policy","runtime_evidence",
 "native_technical_completed","native_playable_completed","can_install",
 "can_execute_real_travel","can_read_user_saves","release_allowed",
 "artifacts","limitations",
}
WORLD_FIELDS={"scope","version","current","travel_state","shared",
              "checkpoints","protected"}
SHARED_FIELDS={"money","coins","tm_ledger","global_boxes",
               "world_progress","special_storage"}
SCOPE="G08_3_SYNTHETIC_MULTIREGIONAL_MEMORY_ONLY"
LABEL=re.compile(r"FIXTURE_[A-Z0-9_]+\Z")

def deny(msg:str)->None:
    raise ValueError("UNOVA_G08_3_BLOCKED: "+msg)

def load(root:Path=ROOT)->tuple[dict,dict]:
    return g72.j(root,FILE),g72.j(root,SOURCES["registry"])

def validate_claims(data:dict,registry:dict)->dict:
    """Pure fail-closed gate usable for synthetic tampering tests."""
    g72.strict(data,FIELDS,"G08.3 source contract")
    expected={
        "schema_version":1,"phase":"G08.3","region":"UNOVA",
        "campaign":"WHITE_BW","status":"PLANNED_MULTIREGIONAL_OFFLINE_REGRESSION_ONLY",
        "sources":SOURCES,"regional_profiles":PROFILES,
        "allowed_fixture_route":list(ROUTE),
        "blocked_native_destinations":list(BLOCKED),
        "covered_resources":RESOURCES,"failure_points":FAULTS,
        "policy":POLICY,"runtime_evidence":NATIVE_EVIDENCE,
        "native_technical_completed":0,"native_playable_completed":0,
        "can_install":False,"can_execute_real_travel":False,
        "can_read_user_saves":False,"release_allowed":False,
        "artifacts":ARTIFACTS,
    }
    for key,val in expected.items():
        if type(data[key]) is not type(val) or data[key]!=val:
            deny("source/protection/role changed: "+key)
    if not isinstance(data["limitations"],list) or len(data["limitations"])<7 or any(
        not isinstance(note,str) or not note.strip()
        for note in data["limitations"]
    ):
        deny("limitations cannot be omitted")
    if any(registry["regions"][key]["status"]!=STATUSES[key] for key in REGIONS):
        deny("registry state drift: never infer actual installation from circuit")
    if tuple(travel.ROUTABLE)!=("DECADES","KANTO","JOHTO","HOENN"):
        deny("G05.3 runtime fixture allowlist drift")
    if tuple(blackout.REGIONS)!=tuple(travel.ROUTABLE):
        deny("native respawn and travel fixtures disagree")
    return {"profiles":len(PROFILES),"native_evidence_verified":0,"can_install":False}

def audit_contract(root:Path=ROOT)->dict:
    g82.audit_contract(root)
    g73.audit_contract(root)
    g74.audit_contract(root)
    data,registry=load(root)
    validate_claims(data,registry)
    board=g72.j(root,SOURCES["tracker"])
    g08=next((group for group in board["groups"] if group["id"]=="G08"),{})
    tasks=g08.get("tasks",[])
    if not any(row.get("id")=="G08.2" and row.get("status")=="done" for row in tasks):
        deny("G08.2 prerequisite not complete")
    if not any(row.get("id")=="G08.3" and row.get("status") in ("pending","done") for row in tasks):
        deny("G08.3 task missing")
    for key,path in SOURCES.items():
        if key in ("registry","tracker"):continue
        value=g72.j(root,path)
        if value.get("region")!="UNOVA" or value.get("can_install") is not False:
            deny("predecessor falsely asserts native install: "+key)
    return {
        "phase":"G08.3","status":"SIX_REGION_FIXTURES_AUDITED_NOT_NATIVE",
        "regions":list(REGIONS),"fixture_routable":list(travel.ROUTABLE),
        "planned_blocked":list(BLOCKED),"route_hops":len(ROUTE)-1,
        "travel_injected_failures":len(travel.FAIL_POINTS),
        "blackout_injected_failures":len(blackout.FAULTS),
        "transaction_injected_failures":len(g73.FAULTS),
        "game_exe_invoked":False,"joiplay_invoked":False,
        "saves_read":False,"native_files_written":0,"can_install":False,
        "native_technical_completed":0,"native_playable_completed":0,
    }

def fixture(reg:dict)->dict:
    """Replicate G05.3's *documented* fixture, augmented with a shared ledger."""
    item=lambda key,kind:{"id":"FIXTURE_"+key,"kind":kind,"qty":1}
    mon=lambda key,flags:{"id":"FIXTURE_"+key,"flags":flags,
       "base_flags":[],"form":0,"egg":False,"fainted":False}
    bag={
        "scope":items.SCOPE,"current":"KANTO",
        "bag":[item("KANTO_HM","HM"),item("TM_GLOBAL","TM")],
        "pc":[item("KANTO_PC_KEY","KEY_ITEM"),item("POTION","CONSUMABLE")],
        "registered":["FIXTURE_KANTO_HM","FIXTURE_TM_GLOBAL"],
        "vault":{
            "HOENN":{"items":[item("HOENN_HM","HM")],
                     "registered":["FIXTURE_HOENN_HM"],
                     "pc_items":[item("HOENN_PC_KEY","KEY_ITEM")]},
            "JOHTO":{"items":[item("JOHTO_HM","HM")],
                     "registered":["FIXTURE_JOHTO_HM"],
                     "pc_items":[item("JOHTO_PC_KEY","KEY_ITEM")]},
        },"bag_capacity":16,"pc_capacity":16,"badges":[],
    }
    party={
        "scope":specials.SIMULATION["scope"],"version":1,
        "current":"KANTO",
        "achievements":{
            "KANTO":reg["regions"]["KANTO"]["milestones"][:3],
            "HOENN":reg["regions"]["HOENN"]["milestones"][:2],
            "JOHTO":reg["regions"]["JOHTO"]["milestones"][:1],
            "UNOVA":reg["regions"]["UNOVA"]["milestones"][:1],
        },"native_decades_badge_count":0,"hisui_complete":False,
        "party":[mon("COMMON",[]),mon("LEGEND",["Legendary"])],
        "free_box_slots":["FIXTURE_BOX_A","FIXTURE_BOX_B"],
    }
    trip={
        "scope":travel.SIMULATION["scope"],"version":1,
        "current":"KANTO","npc_event_context":True,
        "at_initial_town":True,"campaign_active":True,"arena_mode":False,
        "safe_context":{flag:flag in travel.SAFE_TRUE for flag in travel.SAFE_FLAGS},
        "install_proofs":{key:True for key in travel.ROUTABLE},
        "arrival_proofs":{key:True for key in travel.ROUTABLE},
        "position":travel.ORIGINS["KANTO"],"decades_return":None,
        "bag_state":bag,"party_state":party,"pc_boxes":{},
        "travel_history":[],
        "mechanics_by_region":{
            "DECADES":{"FIXTURE_MEGA":True,"FIXTURE_DYNAMAX":False},
            "HOENN":{"FIXTURE_MEGA":True,"FIXTURE_DYNAMAX":False},
            "JOHTO":{"FIXTURE_MEGA":False,"FIXTURE_ZMOVE":True},
        },
        "current_mechanics":{"FIXTURE_MEGA":True,"FIXTURE_DYNAMAX":True},
    }
    centers={
        "DECADES":"FIXTURE_DECADES_CHERRYHILL_CENTER",
        "KANTO":"FIXTURE_KANTO_VIRIDIAN_CENTER",
        "JOHTO":"FIXTURE_JOHTO_CHERRYGROVE_CENTER",
        "HOENN":"FIXTURE_HOENN_OLDALE_CENTER",
        "SINNOH":None,"UNOVA":None,
    }
    protected=copy.deepcopy(g73.base_fixture()["protected"])
    world={
        "scope":SCOPE,"version":1,"current":"KANTO","travel_state":trip,
        "shared":{
            "money":4500,"coins":125,
            "tm_ledger":["FIXTURE_TM_GLOBAL"],
            "global_boxes":{"FIXTURE_GLOBAL_BOX":"FIXTURE_GLOBAL_MON"},
            "world_progress":{"FIXTURE_DECADES_PROGRESS":"FIXTURE_UNCHANGED"},
            "special_storage":{"FIXTURE_SPECIAL_BOX":"FIXTURE_UNUSED"},
        },
        "checkpoints":centers,
        "protected":protected,
    }
    validate_world(world,reg)
    return world

def validate_world(world:Any,reg:dict)->dict:
    g72.strict(world,WORLD_FIELDS,"multiregional synthetic envelope")
    if world["scope"]!=SCOPE or type(world["version"]) is not int or world["version"]!=1:
        deny("native save or unexpected regional envelope")
    if world["current"] not in REGIONS or world["current"]!=world["travel_state"]["current"]:
        deny("region and G05.3 travel snapshot disagree")
    travel.validate_fixture(world["travel_state"],reg)
    if world["checkpoints"]!={key:(
        "FIXTURE_DECADES_CHERRYHILL_CENTER" if key=="DECADES" else
        "FIXTURE_KANTO_VIRIDIAN_CENTER" if key=="KANTO" else
        "FIXTURE_JOHTO_CHERRYGROVE_CENTER" if key=="JOHTO" else
        "FIXTURE_HOENN_OLDALE_CENTER" if key=="HOENN" else None)
        for key in REGIONS}:
        deny("cross-region checkpoint ownership or unverified planned center")
    shared=g72.strict(world["shared"],SHARED_FIELDS,"synthetic shared state")
    for key in ("money","coins"):
        if type(shared[key]) is not int or not 0<=shared[key]<=1_000_000:
            deny("shared money/coins invalid")
    if shared["tm_ledger"]!=["FIXTURE_TM_GLOBAL"]:
        deny("globally shared TM missing, duplicated or imported regionally")
    for key in ("global_boxes","world_progress","special_storage"):
        val=shared[key]
        if not isinstance(val,dict) or not 0<len(val)<=24 or any(
            type(k) is not str or not LABEL.fullmatch(k)
            or type(v) is not str or not LABEL.fullmatch(v)
            for k,v in val.items()
        ):
            deny("non-synthetic global Box, special or progress data")
    protected=world["protected"]
    g72.strict(protected,set(g73.PROTECTED),"protected G07.3 namespaces")
    for region,records in protected.items():
        if not isinstance(records,dict) or not 0<len(records)<=24 or any(
            type(k) is not str or not LABEL.fullmatch(k)
            or type(v) is not str or not LABEL.fullmatch(v)
            for k,v in records.items()
        ):
            deny("non-synthetic protected data: "+region)
    return world

def etag(world:dict,reg:dict)->str:
    validate_world(world,reg)
    return g72.digest(g72.canonical(world))

def refused(world:dict,status:str)->dict:
    return {"phase":"G08.3","status":status,"state":copy.deepcopy(world),
            "no_partial_state":True,"native_transfer":False,
            "native_saves_modified":False,"can_install":False}

def travel_step(world:dict,destination:str,reg:dict,tc:dict,ic:dict,sc:dict,
                *,expected_snapshot_sha256:str,observed_after_staging:dict|None=None,
                fail_at:str|None=None)->dict:
    """Full-world CAS + G05.3 atomic travel. Never persist a candidate state."""
    validate_world(world,reg)
    g72.sha(expected_snapshot_sha256,"expected full-world CAS")
    original=copy.deepcopy(world)
    if expected_snapshot_sha256!=etag(world,reg):
        return refused(world,"CONFLICT_WORLD_CAS_STALE")
    if observed_after_staging is not None:
        validate_world(observed_after_staging,reg)
        if etag(observed_after_staging,reg)!=expected_snapshot_sha256:
            return refused(world,"CONFLICT_WORLD_CAS_CONCURRENT_EDIT")
    if destination not in REGIONS:
        deny("foreign or unknown destination")
    status=travel.simulate(tc,reg,ic,sc,world["travel_state"],
                           destination,fail_at=fail_at)
    if status["status"]!="SIMULATED_SUCCESS_NOT_NATIVE_TRAVEL":
        if world!=original:deny("world mutated on rejected or failed G05 travel")
        return refused(world,status["status"])
    staged=copy.deepcopy(world)
    staged["current"]=destination
    staged["travel_state"]=status["fixture"]
    validate_world(staged,reg)
    if (staged["shared"]!=original["shared"]
        or staged["checkpoints"]!=original["checkpoints"]
        or staged["protected"]!=original["protected"]):
        deny("cross-region money, box, checkpoint, progress or CAS guard mutated")
    if (world!=original or expected_snapshot_sha256!=etag(world,reg)):
        deny("world changed during simulated atomic travel")
    return {
        "phase":"G08.3","status":"SYNTHETIC_TRAVEL_COMMIT_NOT_INSTALLED",
        "source":world["current"],"destination":destination,
        "state":staged,"source_etag":expected_snapshot_sha256,
        "candidate_etag":etag(staged,reg),
        "native_transfer":False,"native_saves_modified":False,
        "can_install":False,
    }

def blackout_step(world:dict,region:str,reg:dict,*,fail_at:str|None=None)->dict:
    """G05.4 independent synthetic Center owner, money and Box regression."""
    validate_world(world,reg)
    if region not in REGIONS:deny("unknown blackout region")
    st=blackout.fixture(reg)
    st["current"]=region
    st["bag"]["current"]=region
    st["party"]["current"]=region
    st["position"]="FIXTURE_"+region+"_ROUTE"
    original=copy.deepcopy(st)
    result=blackout.blackout(st,reg,fail_at=fail_at)
    if st!=original:deny("source blackout mutated its input")
    if region in BLOCKED:
        if result["status"]!="PLANNED_REGION_RESPAWN_UNVERIFIED" or result["fixture"]!=original:
            deny("planned Sinnoh/Unova must not use a foreign Center")
    elif fail_at is not None:
        if result["status"]!="SYNTHETIC_FAILURE_ROLLED_BACK" or result["fixture"]!=original:
            deny("partial blackout changed native checkpoint or shared state")
    else:
        if (result["status"]!="SYNTHETIC_BLACKOUT_ONCE_NOT_NATIVE" or
            result["fixture"]["position"] not in st["verified_centers"][region]
            or result["fixture"]["checkpoint_owner"]!=region):
            deny("native or foreign checkpoint erroneously used in blackout")
        for key in ("money","coins","bag","party","boxes","native_badges",
                    "leagues","field_events","mechanics_by_region","active_mechanics"):
            if result["fixture"][key]!=original[key]:
                deny("blackout modified regional/global protected state: "+key)
    return {
        "region":region,"status":result["status"],
        "before":original,"after":result["fixture"],
        "no_native_healing":True,"native_save_modified":False,
    }

def demo(root:Path=ROOT)->dict:
    audit_contract(root)
    # G08.2 is a mandatory cross-contract runtime prerequisite, not an unused import.
    g82.synthetic_chain(root)
    tc,reg,ic,sc,_=travel.load_project(root)
    baseline=fixture(reg)
    world=baseline
    denied={}
    for region in BLOCKED:
        reply=travel_step(world,region,reg,tc,ic,sc,
                          expected_snapshot_sha256=etag(world,reg))
        if (reply["status"]!="DESTINATION_NOT_INSTALLED_OR_SUPPORTED"
            or reply["state"]!=world):
            deny("planned destination was promoted to native travel")
        denied[region]=reply["status"]
    hops=[]
    for target in ROUTE[1:]:
        prev=copy.deepcopy(world)
        response=travel_step(world,target,reg,tc,ic,sc,
                             expected_snapshot_sha256=etag(world,reg))
        if (response["status"]!="SYNTHETIC_TRAVEL_COMMIT_NOT_INSTALLED"
            or response["state"]["shared"]!=prev["shared"]):
            deny("G05.3 fixture hop "+prev["current"]+" -> "+target+" blocked: "+response["status"])
        world=response["state"]
        hops.append({"source":prev["current"],"destination":target,
                     "deposited_pokemon":len(world["travel_state"]["pc_boxes"])})
    bag=world["travel_state"]["bag_state"]
    if (world["current"]!="KANTO"
        or not any(x["id"]=="FIXTURE_KANTO_HM" for x in bag["bag"])
        or not any(x["id"]=="FIXTURE_TM_GLOBAL" for x in bag["bag"])
        or world["travel_state"]["current_mechanics"]!=baseline["travel_state"]["current_mechanics"]
        or world["travel_state"]["party_state"]["achievements"]!=baseline["travel_state"]["party_state"]["achievements"]
        or not any(v=="FIXTURE_LEGEND" for v in world["travel_state"]["pc_boxes"].values())
        or world["shared"]!=baseline["shared"]):
        deny("cross-region inventory/party/boxes/mechanics/progress isolation regressed")
    travel_rollback={}
    for failure in travel.FAIL_POINTS:
        failed=travel_step(baseline,"HOENN",reg,tc,ic,sc,
                           expected_snapshot_sha256=etag(baseline,reg),fail_at=failure)
        if failed["state"]!=baseline or failed["status"]!="SIMULATED_TRANSFER_FAILED_ROLLED_BACK":
            deny("travel rollback lost shared or regional state")
        travel_rollback[failure]=True
    blackouts={}
    for region in REGIONS:
        preview=blackout_step(baseline,region,reg)
        if region in travel.ROUTABLE:
            for failure in blackout.FAULTS:
                blackout_step(baseline,region,reg,fail_at=failure)
        blackouts[region]=preview["status"]
    package=g74.demo(root)
    if (package["can_install"] or
        any(item["can_install"] for item in package["platforms"].values())):
        deny("G07 package wrongly allowed native installation")
    return {
        "phase":"G08.3","status":"MULTIREGIONAL_FIXTURES_ONLY_NOT_NATIVE",
        "regions":list(REGIONS),"hops":hops,"blocked_destinations":denied,
        "travel_rollbacks":len(travel_rollback),
        "blackout_failure_points_each":len(blackout.FAULTS),
        "blackouts":blackouts,"shared_money_unchanged":True,
        "global_tm_preserved":True,"regional_hm_restored":True,
        "badges_preserved":True,"special_box_preserved":True,
        "mechanics_restored":True,"world_state_sha256":etag(world,reg),
        "platforms":list(package["platforms"]),"native_files_written":0,
        "native_saves_modified":False,"game_exe_tested":False,
        "unova_playable":False,"can_install":False,
        "native_technical_completed":0,"native_playable_completed":0,
    }

def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    mode=p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check",action="store_true")
    mode.add_argument("--simulate-demo",action="store_true")
    args=p.parse_args(argv)
    try:
        output=audit_contract() if args.check else demo()
        print(json.dumps(output,ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,OSError,TypeError,KeyError,IndexError,RecursionError) as exc:
        print("UNOVA_G08_3_BLOCKED: "+str(exc)[:300])
        return 2
if __name__=="__main__":raise SystemExit(main())
