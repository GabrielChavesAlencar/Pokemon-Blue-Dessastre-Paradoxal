#!/usr/bin/env python3
"""G08.2 cross-contract integration audit for planned Unova.

Read-only source review + actual in-process G01-G07 synthetic flows.
No native Game.exe, Android updater, ZIP, save path, network or filesystem write.
"""
from __future__ import annotations

import argparse
import copy
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import audit_unova_g01_chapter_machine as g01
import audit_unova_g01_reentry_ledger as ledger
import audit_unova_g01_serialization as codec
import audit_unova_g02_gym_story as gyms
import audit_unova_g02_elite_finale as finale
import audit_unova_g02_postgame as postgame
import audit_unova_g03_leader_scaling as scaling
import audit_unova_g03_rivals_plasma as rivals
import audit_unova_g03_elite_alder as alder
import audit_unova_g04_encounter_methods as methods
import audit_unova_g04_wild_scaling as wild
import audit_unova_g04_encounter_validation as encounters
import audit_unova_g05_regional_items as items
import audit_unova_g05_badges_specials as specials
import audit_unova_g05_travel as travel
import audit_unova_g05_blackout_state as blackout
import audit_unova_g07_incremental_manifest as g72
import audit_unova_g07_transaction as g73
import audit_unova_g07_platform_compat as g74

ROOT=Path(__file__).resolve().parents[2]
FILE="data/regions/unova-g08-integrated-contract.json"
COVERAGE=("G01.1","G01.2","G01.3","G01.4","G02.2","G02.3","G02.4",
          "G03.2","G03.3","G03.4","G04.2","G04.3","G04.4",
          "G05.1","G05.2","G05.3","G05.4","G06.2","G06.3",
          "G07.2","G07.3","G07.4")
SOURCES={
 "areas":"data/regions/unova-u03-areas.json",
 "chapters":"data/regions/unova-g01-state-contract.json",
 "transitions":"data/regions/unova-g01-chapter-transitions.json",
 "gyms":"data/regions/unova-g02-gym-story-contracts.json",
 "finale":"data/regions/unova-g02-elite-finale-contracts.json",
 "postgame":"data/regions/unova-g02-postgame-contracts.json",
 "rivals":"data/regions/unova-g03-rivals-plasma-story-contracts.json",
 "leader_scaling":"data/regions/unova-g03-leader-scaling-contracts.json",
 "alder":"data/regions/unova-g03-elite-alder-rematch-contracts.json",
 "encounter_methods":"data/regions/unova-g04-encounter-methods-contract.json",
 "wild_scaling":"data/regions/unova-g04-wild-scaling-contract.json",
 "encounter_validation":"data/regions/unova-g04-encounter-validation-contract.json",
 "regional_items":"data/regions/unova-g05-regional-items-contract.json",
 "badges_specials":"data/regions/unova-g05-badges-specials-contract.json",
 "travel":"data/regions/unova-g05-travel-contract.json",
 "blackout":"data/regions/unova-g05-blackout-state-contract.json",
 "incremental":"data/regions/unova-g07-incremental-contract.json",
 "transaction":"data/regions/unova-g07-transaction-contract.json",
 "platform":"data/regions/unova-g07-platform-compatibility-contract.json",
 "registry":"site/public/data/regions.json",
 "board":"site/public/data/unova-github-progress.json",
}
CONSTRAINTS={
 "source_only":True,"fixture_only":True,"fail_closed":True,
 "cross_chapter_and_mission_references":True,"gym_eight_badges_synthetic_only":True,
 "elite_four_and_castle_synthetic_only":True,"rivals_plasma_unique_receipts":True,
 "native_trainer_teams_unverified":True,"native_encounter_rates_unverified":True,
 "native_wild_slots_unverified":True,"evolution_synthetic_only":True,
 "regional_hm_key_item_isolation":True,"tm_global_preserved":True,
 "blackout_fallback_current_region_only":True,"foreign_checkpoint_denied":True,
 "shared_money_boxes_state_unchanged":True,"travel_unova_not_installed":True,
 "portal_areas_74_planned":True,"portal_guides_only":True,
 "package_g072_validated_first":True,"g073_double_cas":True,
 "g073_full_rollback":True,"g074_windows_android_contract_only":True,
 "source_rights_unapproved":True,"not_native_installable":True,
 "no_game_exe_modification":True,"no_save_modification":True,
 "no_external_fetch":True,"native_technical_zero":True,"native_playable_zero":True,
}
EVIDENCE={
 "native_mapids":None,"native_encounter_tables":None,"native_teams":None,
 "native_runtime_windows":None,"native_runtime_android":None,
 "source_rights":None,
}
EXPECTED_COUNTS={"symbolic_areas":74,"chapters":12,"missions":12,"gyms":8,"elite_four":4}
TESTS={
 "python":"tests/test_unova_g08_integrated.py",
 "portal":"site/tests/unova-integration.test.mjs",
 "auditor":"scripts/regions/audit_unova_g08_integrated.py",
}
FIELDS={
 "schema_version","phase","region","campaign","status","source_contracts",
 "coverage","constraints","expected_counts","evidence","tests",
 "native_technical_completed","native_playable_completed","can_install",
 "can_write_saves","can_write_game_exe","notes",
}
def deny(message:str)->None:
    raise ValueError("UNOVA_G08_2_BLOCKED: "+message)

@lru_cache(maxsize=2)
def source_state(root:Path=ROOT)->dict:
    root=Path(root)
    return {key:g72.j(root,path) for key,path in SOURCES.items()}

def validate_links(data:dict)->dict:
    """Join independently audited catalogs and refuse forged gameplay evidence."""
    if not isinstance(data,dict) or set(data)!=set(SOURCES):
        deny("contract catalog missing or unexpected")
    areas=data["areas"]["areas"]
    chapters=data["chapters"]["chapters"]
    missions=data["chapters"]["missions"]
    transitions=data["transitions"]["transitions"]
    gyms_catalog=data["gyms"]["gyms"]
    elite=data["finale"]["elite_members"]
    encounters_catalog=data["rivals"]["encounters"]
    area_keys=[a["key"] for a in areas]
    chapter_keys=[c["key"] for c in chapters]
    mission_keys=[m["key"] for m in missions]
    if (len(areas)!=74 or len(set(area_keys))!=74 or len(chapters)!=13
        or len(set(chapter_keys))!=13 or len(missions)!=12 or len(set(mission_keys))!=12
        or len(transitions)!=12 or len(gyms_catalog)!=8 or len(elite)!=4):
        deny("catalog counts, unique keys or story progression drift")
    akeys=set(area_keys)
    ckeys=set(chapter_keys)
    mkeys=set(mission_keys)
    if (chapters[0]["index"]!=0 or any(c["index"]!=i for i,c in enumerate(chapters))
        or any(c["map_id"] is not None or c["game_exe_verified"] is not False for c in chapters)):
        deny("invented chapter map/QA or broken order")
    for m in missions:
        if (m["chapter_key"] not in ckeys or m["reference_area_key"] not in akeys
            or m["planned_only"] is not True or m["real_event_id"] is not None):
            deny("orphan mission or falsely installed story event")
    for i,t in enumerate(transitions):
        if t["from"]!=chapters[i]["key"] or t["to"]!=chapters[i+1]["key"]:
            deny("chapter transition skips or cycles")
        if i and t["required_mission_key"]!=missions[i-1]["key"]:
            deny("chapter gate not backed by G01 mission")
    for i,g in enumerate(gyms_catalog):
        if (g["index"]!=i+1 or g["chapter_key"] not in ckeys
            or g["mission_key"] not in mkeys
            or g["gym_area_key"] not in akeys or g["city_area_key"] not in akeys
            or g["challenge_status"]!="PLANNED_NOT_PLAYABLE"
            or g["native_badge_item_id"] is not None
            or g["native_badge_switch_id"] is not None
            or g["trainer_party"] is not None or g["trainer_levels"] is not None):
            deny("gym/badge/level native evidence forged or disconnected")
        if any(e["native_event_id"] is not None or
               e["source_map_id"] is not None or
               e["trainer_id"] is not None for e in g["events"]):
            deny("native gym event forged")
    if [x["member_name"] for x in elite]!=["SHAUNTAL","GRIMSLEY","CAITLIN","MARSHAL"]:
        deny("Elite Four order/source drift")
    if any(e["area_key"] not in akeys or e["team"] is not None
           or e["levels"] is not None or e["native_trainer_id"] is not None for e in elite):
        deny("Elite has invented native trainer or map")
    if any(e["reference_area_key"] not in akeys or e["chapter_key"] not in ckeys
           or e["canonical_team"] is not None or e["canonical_levels"] is not None
           or e["native_event_id"] is not None or e["native_map_id"] is not None
           for e in encounters_catalog):
        deny("rival/Plasma fake trainer or orphan reference")
    if (len(data["encounter_validation"]["areas"])!=74 or
        len(data["encounter_methods"]["areas"])!=74 or
        len(data["wild_scaling"]["areas"])!=74):
        deny("G04 symbolic area coverage incomplete")
    if any(row["native_map_id"] is not None or
           row["native_species"] is not None or
           row["native_encounter_rate"] is not None or
           row["native_pbs_verified"] is not False or row["installable"] is not False
           for row in data["encounter_validation"]["areas"]):
        deny("G04 forged encounter rates, species, provenance or MapIDs")
    if {x["area_key"] for x in data["encounter_validation"]["areas"]}!=akeys:
        deny("G04 encounters have extra or missing areas")
    if any(x["source_map_id"] is not None or x["destination_map_id"] is not None
           or x["state"]!="planned" for x in areas):
        deny("G06 portal falsely lists installed area")
    for key in ("chapters","gyms","finale","postgame","rivals",
                "encounter_methods","wild_scaling","encounter_validation",
                "regional_items","badges_specials","travel","blackout",
                "incremental","transaction","platform"):
        obj=data[key]
        if obj.get("region")!="UNOVA":
            deny("foreign regional catalog in G01-G07: "+key)
        if obj.get("can_install") is not False:
            deny("native install falsely approved: "+key)
    for key in ("rivals","encounter_validation","travel","blackout"):
        if data[key].get("game_exe_tested") is not False:
            deny("Game.exe QA falsely approved: "+key)
    for key in ("incremental","transaction","platform"):
        if data[key].get("release_allowed", data[key].get("can_release")) is not False:
            deny("native package release falsely approved: "+key)
    if (data["registry"]["regions"]["UNOVA"]["status"]!="planned" or
        data["board"]["status"]!="PLANNED_NOT_NATIVE_PLAYABLE" or
        data["board"]["native_technical_bar"]!={"completed":0,"total":8} or
        data["board"]["native_playable_bar"]!={"completed":0,"total":32}):
        deny("physical region or native progress artificially promoted")
    return {"areas_joined":74,"chapters_joined":12,"mission_gates_joined":12,
            "gyms_joined":8,"elite_members":4,"rival_events":len(encounters_catalog),
            "game_exe_tested":False,"native_tables_verified":0,
            "native_teams_verified":0,"can_install":False}

def audit_contract(root:Path=ROOT)->dict:
    root=Path(root)
    obj=g72.j(root,FILE)
    g72.strict(obj,FIELDS,"G08.2 cross-contract")
    expected={
        "schema_version":1,"phase":"G08.2","region":"UNOVA","campaign":"WHITE_BW",
        "status":"PLANNED_CROSS_CONTRACT_REGRESSION_ONLY",
        "source_contracts":SOURCES,"coverage":list(COVERAGE),
        "constraints":CONSTRAINTS,"expected_counts":EXPECTED_COUNTS,
        "evidence":EVIDENCE,"tests":TESTS,
        "native_technical_completed":0,"native_playable_completed":0,
        "can_install":False,"can_write_saves":False,"can_write_game_exe":False,
    }
    for key,val in expected.items():
        if type(obj[key]) is not type(val) or obj[key]!=val:
            deny("integration source/constraints drift: "+key)
    if not isinstance(obj["notes"],list) or len(obj["notes"])<5:
        deny("required offline limitations absent")
    # Existing validation is mandatory: each has its own native-source
    # signatures, scope, rights and catalogue checks. Do not bypass them.
    g01.load_project(root)
    gyms.load_project(root)
    finale.load_project(root)
    postgame.load_project(root)
    rivals.load_project(root)
    alder.load_project(root)
    methods.load_project(root)
    wild.load_project(root)
    encounters.load_project(root)
    items.load_project(root)
    specials.load_project(root)
    travel.load_project(root)
    blackout.load_project(root)
    g72.validate_catalog(root)
    g73.audit_contract(root)
    g74.audit_contract(root)
    report=validate_links(source_state(root))
    board=source_state(root)["board"]
    g08=next((x for x in board["groups"] if x["id"]=="G08"),{})
    if not any(t["id"]=="G08.2" and t["status"] in ("pending","done")
               for t in g08.get("tasks",[])):
        deny("G08.2 missing from progress board")
    for path in ("site/scripts/unova-guide.mjs",
                 "site/src/assets/unova-guide.js",
                 "site/src/assets/unova-search.js",
                 "site/tests/unova-guide.test.mjs",
                 "site/tests/unova-search.test.mjs"):
        text=g72.body(root,path)
        if "UNOVA" not in text and "unova" not in text:
            deny("G06/portal source not found: "+path)
    return {**report,"phase":"G08.2",
            "status":"ALL_G01_TO_G07_SOURCE_CONTRACTS_VERIFIED_OFFLINE",
            "coverage":len(COVERAGE),"native_files_written":0,
            "native_saves_modified":False,
            "native_technical_completed":0,"native_playable_completed":0}

def synthetic_chain(root:Path=ROOT)->dict:
    audit_contract(root)
    ctx,gym_catalog,finale_catalog,postgame_catalog,policy,rival_catalog=rivals.load_project(root)
    contract,rules=g01.load_project(root)
    chapter=g01.demo(contract,rules)
    gym=gyms.demo(ctx,gym_catalog)
    league=finale.demo(ctx,gym_catalog,finale_catalog)
    rival=rivals.demo(ctx,gym_catalog,finale_catalog,postgame_catalog,policy,rival_catalog)
    balance=scaling.demo(policy)
    wdata,wild_data,_,_=encounters.load_project(root)
    encounter=encounters.demo(wdata,wild_data)
    it,reg,_=items.load_project(root)
    itresult=items.demo(it,reg)
    tr,reg2,it2,sp2,_=travel.load_project(root)
    trip=travel.demo(tr,reg2,it2,sp2)
    bo,reg3,_=blackout.load_project(root)
    faint=blackout.demo(bo,reg3)
    pkg,manifest,old,new=g73.multi_file_fixture()
    snapshot=g73.base_fixture(pkg,manifest,old)
    before=copy.deepcopy(snapshot)
    platform={}
    for profile in g74.PLATFORMS:
        req=g74.fixture_request(profile,pkg,snapshot)
        ok=g74.preview(profile,req,pkg,manifest,old,new,snapshot)
        errors=[
            g74.preview(profile,req,pkg,manifest,old,new,snapshot,fail_at=f)
            for f in g73.FAULTS
        ]
        if (any(e["transaction_status"]!="SIMULATED_ROLLBACK_COMPLETE" or
                e["state"]!=before for e in errors)
            or ok["state"]["protected"]!=before["protected"]
            or snapshot!=before or ok["install_allowed"]):
            deny("cross-platform G07 rollback or immutable snapshot drift")
        platform[profile]={"committed_docs":len(new),"faults_rolled_back":len(errors)}
    if (chapter["final_chapter"]!=contract["chapters"][12]["key"]
        or gym["badge_claims"]!=8 or league["elite_wins"]!=4
        or rival["planned_battles_recorded"]!=9
        or balance["scaled_synthetic_target_level"]!=36
        or encounter["native_tables_checked"]!=0
        or not itresult["returned_kanto_hm"]
        or not trip["rollback_preserved"]
        or not trip["kanto_hm_restored"]
        or not faint["money_preserved"]
        or not faint["boxes_preserved"]
        or not faint["items_preserved"]
        or not faint["rollback_preserved"]):
        deny("integrated fixtures across G01–G07 regressed")
    return {
        "phase":"G08.2",
        "status":"CROSS_CONTRACT_SYNTHETIC_ONLY_NOT_GAMEPLAY",
        "chapter":chapter["final_chapter"],"gym_badges_simulated":gym["badge_claims"],
        "elite_four_simulated":league["elite_wins"],
        "plasma_rival_battles_simulated":rival["planned_battles_recorded"],
        "synthetic_master_scaled_level":balance["scaled_synthetic_target_level"],
        "native_encounter_tables":0,"regional_hm_restored":trip["kanto_hm_restored"],
        "unova_travel_denied":trip["unova_native_entry"],
        "blackout_money_preserved":faint["money_preserved"],
        "blackout_boxes_preserved":faint["boxes_preserved"],
        "blackout_checkpoint":faint["source"],
        "platform_dry_runs":platform,
        "native_game_files_modified":False,
        "native_saves_modified":False,"can_install":False,
        "native_technical_completed":0,"native_playable_completed":0,
    }

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check",action="store_true")
    group.add_argument("--simulate-demo",action="store_true")
    args=parser.parse_args(argv)
    try:
        out=audit_contract() if args.check else synthetic_chain()
        print(json.dumps(out,sort_keys=True,ensure_ascii=False))
        return 0
    except (ValueError,OSError,TypeError,KeyError,IndexError,RecursionError) as exc:
        print("UNOVA_G08_2_BLOCKED: "+str(exc)[:350])
        return 2
if __name__=="__main__":raise SystemExit(main())
