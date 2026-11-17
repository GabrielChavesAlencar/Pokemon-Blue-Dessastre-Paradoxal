#!/usr/bin/env python3
"""G04.2: White Unova encounter-method, time and season AUDIT CONTRACT.

The 74 U03 areas are symbolic, not executable spawn tables. Method names are
sourced from Blue's PBS parser; assigning any particular method to an area is
only a review question. No species, rates, MapIDs or seasons have source proof.
Never writes to or reads from native Game.exe, PBS, RXDATA, party or save files.
"""
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

import audit_unova_u03_catalog as u03

ROOT=Path(__file__).resolve().parents[2]
FILE=ROOT/"data/regions/unova-g04-encounter-methods-contract.json"
LAND=("Land","LandMorning","LandDay","LandAfternoon","LandEvening","LandNight")
CAVE=("Cave","CaveMorning","CaveDay","CaveAfternoon","CaveEvening","CaveNight")
WATER=("Water","WaterMorning","WaterDay","WaterNight")
FISH=("OldRod","GoodRod","SuperRod")
ROCK=("RockSmash",)
BUCKETS=("ANY","MORNING","DAY","AFTERNOON","EVENING","NIGHT")
SEASONS=("ANY","SPRING","SUMMER","AUTUMN","WINTER")
KINDS={
 "settlement":(),"route":LAND+WATER+FISH,"interior":(),"area":LAND,
 "gym":(),"cave":CAVE+ROCK,"forest":LAND,"bridge":(),"ruin":CAVE,
 "facility":(),"tower":(),"mountain":LAND+CAVE,"castle":(),
 "water":WATER+FISH}
SOURCES={
 "areas":"data/regions/unova-u03-areas.json",
 "blue_pbs_methods":"scripts/regions/pbs.py",
 "blue_habitat":"scripts/battle_polish/Habitat.rb",
 "native_wild_evolution":"scripts/battle_polish/EvolutionScaling.rb",
 "shared_sinnoh_reference":"data/regions/sinnoh-symbolic-encounters.json",
 "regional_progress":"site/public/data/unova-github-progress.json",
 "registry":"site/public/data/regions.json"}
EVIDENCE_KEYS={
 "unova_encounters_pbs_file","unova_encounters_pbs_sha256",
 "source_license_approval","source_table_provenance","season_mapping_evidence",
 "time_mapping_evidence","variant_mapping_evidence","encounter_rate_evidence",
 "weight_evidence","level_range_evidence","source_area_map_ids_verified"}
CONTRACT_KEYS={"schema","phase","region","reference_version","status",
 "sources","source_evidence","method_registry",
 "method_family_candidates_by_u03_kind","time_buckets","season_buckets",
 "supported_campaign_variants","encounter_probability_policy",
 "special_encounter_policy","areas","can_write_pbs","can_allocate_map_ids",
 "can_install","game_exe_tested","android_tested","native_encounters_verified",
 "notes"}
AREA_KEYS={"area_key","u03_kind","chapter_scope","source_status","source_map_id",
 "destination_map_id","candidate_methods","candidate_methods_are_questions_only",
 "time_windows_to_audit","season_variants_to_audit",
 "seasonal_species_assignment_verified","encounter_slots",
 "species_method_assignments","method_version_assignments",
 "method_time_assignments","method_season_assignments",
 "encounter_rate","weight_percentages","level_ranges","real_species",
 "actual_method_assignment_verified","actual_area_rates_verified",
 "native_pbs_verified","game_exe_tested","may_install"}
FLAGS=("can_write_pbs","can_allocate_map_ids","can_install",
       "game_exe_tested","android_tested","native_encounters_verified")

def deny(message:str)->None:
    raise ValueError("UNOVA_G04_2_BLOCKED: "+message)

def exact(obj:Any,keys:set[str],label:str)->None:
    if not isinstance(obj,dict) or set(obj)!=keys:
        deny(label+" has missing or unexpected fields")

def load_json(path:Path)->dict:
    if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<300_000:
        deny("invalid repository JSON source")
    return json.loads(path.read_text(encoding="utf-8"))

def read_text(path:Path)->str:
    if path.is_symlink() or not path.is_file() or not 0<path.stat().st_size<250_000:
        deny("invalid repository text source")
    return path.read_text(encoding="utf-8")

def expected_methods()->list[dict]:
    rows=[]
    for family,methods in (("LAND",LAND),("CAVE",CAVE),("WATER",WATER),
                           ("FISHING",FISH),("ROCK_SMASH",ROCK)):
        for method in methods:
            bucket=next((key for key in BUCKETS[1:]
                         if method.endswith(key.title())),"ANY")
            rows.append({"pbs_method":method,"method_family":family,
                         "time_bucket":bucket,
                         "source_status":"SUPPORTED_BLUE_PBS_METHOD_ONLY_NOT_UNOVA_ASSIGNMENT",
                         "native_method_assignment_verified":False})
    return rows

def _extract_pbs_methods(source:str)->set[str]:
    """AST literal only, no execution of Kanto's PBS writer."""
    root=ast.parse(source)
    for node in root.body:
        if isinstance(node,ast.Assign) and any(
            isinstance(target,ast.Name) and target.id=="ENCOUNTER_TYPES"
            for target in node.targets):
            value=ast.literal_eval(node.value)
            if not isinstance(value,set) or any(not isinstance(v,str) for v in value):
                deny("PBS methods must be a static string set")
            return value
    deny("PBS parser encounter-method registry not found")

def load_project(root:Path=ROOT)->tuple:
    root=Path(root)
    data=load_json(root/"data/regions/unova-g04-encounter-methods-contract.json")
    u03areas=load_json(root/data["sources"]["areas"])
    regions=load_json(root/data["sources"]["registry"])
    pbs=read_text(root/data["sources"]["blue_pbs_methods"])
    habitat=read_text(root/data["sources"]["blue_habitat"])
    wild=read_text(root/data["sources"]["native_wild_evolution"])
    sinnoh=load_json(root/data["sources"]["shared_sinnoh_reference"])
    report=validate_catalog(data,u03areas,regions,pbs,habitat,wild,sinnoh)
    return data,u03areas,regions,report

def validate_catalog(data:dict,areas:dict,regions:dict,pbs:str,habitat:str,
                     wild:str,sinnoh:dict)->dict:
    exact(data,CONTRACT_KEYS,"G04.2 catalog")
    expected={
        "schema":1,"phase":"G04.2","region":"UNOVA",
        "reference_version":"WHITE_BW",
        "status":"PLANNED_METHOD_AUDIT_ONLY_NO_REAL_ENCOUNTERS",
        "sources":SOURCES,
        "time_buckets":list(BUCKETS),
        "season_buckets":list(SEASONS),
        "supported_campaign_variants":["WHITE_BW"],
        "encounter_probability_policy":{
            "verified_area_rate_provided":False,
            "verified_species_weights_provided":False,
            "allow_fixed_numeric_weights":False,
            "allow_generated_percentages":False,
            "zero_is_not_proof_of_absence":True,
            "no_seasonal_or_time_derived_probabilities":True,
            "percentage_total_check":"DEFER_UNTIL_G04_4_SOURCE_VERIFIED",
            "evolution_chance_is_not_spawn_weight":True},
        "special_encounter_policy":{
            "scripted_events_are_not_random_slots":True,
            "legendary_and_distribution_events_separate":True,
            "can_infer_special_species_from_area_name":False}}
    for field,val in expected.items():
        if data.get(field)!=val or type(data[field]) is not type(val):
            deny("version/source/method/weight policy drift: "+field)
    exact(data["source_evidence"],EVIDENCE_KEYS,"evidence")
    for name,value in data["source_evidence"].items():
        if name=="source_area_map_ids_verified":
            if value is not False:deny("source MapIDs not verified")
        elif value is not None:deny("unsupported source evidence for "+name)
    for name in FLAGS:
        if data[name] is not False:deny("cannot promote native or installation flag")
    if not isinstance(data["notes"],list) or len(data["notes"])<5 or any(
            not isinstance(note,str) or not note.strip() for note in data["notes"]):
        deny("safety notes must explain candidate-only status")
    regional=regions.get("regions",{}).get("UNOVA")
    if not isinstance(regional,dict):
        deny("White region not present")
    original=u03.validate(areas,regional)
    if original["catalog_areas"]!=74:
        deny("expected complete U03 list of 74 symbolic areas")
    if (sinnoh.get("region")!="SINNOH" or
        sinnoh.get("source_level")!="REFERENCE_NOT_NATIVE_VERIFIED" or
        sinnoh.get("may_write_pbs") is not False or
        sinnoh.get("encounter_weights_verified") is not False):
        deny("shared Sinnoh reference falsely claims verified native encounters")
    if not isinstance(pbs,str) or _extract_pbs_methods(pbs)!={
        x["pbs_method"] for x in expected_methods()}:
        deny("PBS source and candidate methods diverged")
    if ("module BlueHabitat" not in habitat or
        "GameData::Encounter" not in habitat or
        any(token not in habitat for token in ("OldRod","GoodRod","SuperRod","RockSmash"))):
        deny("Habitat methods are not grounded in Blue's read-only runtime")
    if not all(token in wild for token in (
            "module BlueEvolutionScaling","def self.wild_chance",
            "Never edits PBS encounter probabilities")):
        deny("existing Blue evolution must not rewrite encounter weights")
    if data["method_registry"]!=expected_methods():
        deny("methods are unsupported or claim proven Unova assignment")
    kind_methods={key:list(methods) for key,methods in KINDS.items()}
    if data["method_family_candidates_by_u03_kind"]!=kind_methods:
        deny("terrain questions changed or became false area assignments")
    entries=data["areas"]
    if not isinstance(entries,list) or len(entries)!=74:
        deny("74 symbolic area rows required, no extra/missing areas")
    count=0;empty=0
    for row,reference in zip(entries,areas["areas"]):
        exact(row,AREA_KEYS,"area audit row")
        methods=kind_methods.get(reference["kind"])
        if methods is None:deny("new U03 terrain requires explicit review")
        expected_row={
            "area_key":reference["key"],"u03_kind":reference["kind"],
            "chapter_scope":reference["chapter"],
            "source_status":"PLANNED_U03_AREA_ONLY",
            "source_map_id":None,"destination_map_id":None,
            "candidate_methods":methods,
            "candidate_methods_are_questions_only":True,
            "time_windows_to_audit":list(BUCKETS[1:]) if methods else [],
            "season_variants_to_audit":list(SEASONS[1:]) if methods else [],
            "seasonal_species_assignment_verified":False,
            "encounter_slots":[],"species_method_assignments":[],
            "method_version_assignments":[],"method_time_assignments":[],
            "method_season_assignments":[],
            "encounter_rate":None,"weight_percentages":None,
            "level_ranges":None,"real_species":None,
            "actual_method_assignment_verified":False,
            "actual_area_rates_verified":False,"native_pbs_verified":False,
            "game_exe_tested":False,"may_install":False}
        if row!=expected_row:
            deny("unsupported area data/weights/probabilities/MapIDs or changed U03 ordering")
        if methods:count+=1
        else:empty+=1
    if count+empty!=74 or not count:deny("area review coverage incomplete")
    return {"phase":"G04.2","status":"PLANNED_ENCOUNTER_AUDIT_VERIFIED_NOT_PLAYABLE",
        "u03_area_references":74,"areas_with_candidate_review_methods":count,
        "areas_without_proven_wild_method":empty,
        "pbs_method_names":len(expected_methods()),
        "supported_season_review_buckets":4,
        "native_area_assignments":0,"verified_species_slots":0,
        "verified_probability_tables":0,
        "game_exe_tested":False,"can_install":False}

def area_record(data:dict,area_key:str)->dict:
    if not isinstance(area_key,str):
        deny("area key must be a string")
    for row in data["areas"]:
        if row["area_key"]==area_key:return row
    deny("area missing from U03 — no automatic map or source assignment")

def plan_audit(data:dict,*,area_key:str,method:str,time_bucket:str,
               season_bucket:str,version:str="WHITE_BW")->dict:
    """Review an explicitly suggested method, NEVER a real encounter spawn."""
    row=area_record(data,area_key)
    if version!="WHITE_BW":
        deny("no Black/BW2 encounter variants verified in White-only catalog")
    if type(method) is not str or method not in row["candidate_methods"]:
        deny("unsupported/unreviewed method for area; no assumption of native spawns")
    if type(time_bucket) is not str or time_bucket not in BUCKETS:
        deny("time bucket must be explicit and supported")
    if type(season_bucket) is not str or season_bucket not in SEASONS:
        deny("season bucket must be explicit and supported")
    registry=next(m for m in data["method_registry"] if m["pbs_method"]==method)
    named=registry["time_bucket"]
    if named!="ANY" and named!=time_bucket:
        deny("a time-specific method cannot be attributed to a different time")
    return {"phase":"G04.2","area_key":area_key,
        "source_u03_kind":row["u03_kind"],"version":version,
        "method_question":method,"time_question":time_bucket,
        "season_question":season_bucket,"method_family":registry["method_family"],
        "status":"AUDIT_QUESTION_NOT_AN_ENCOUNTER_ASSIGNMENT",
        "actual_method_assignment_verified":False,
        "actual_area_rates_verified":False,"seasonal_species_assignment_verified":False,
        "species_method_assignments":[],"encounter_slots":[],
        "encounter_rate":None,"weight_percentages":None,"level_ranges":None,
        "source_map_id":None,"destination_map_id":None,
        "native_pbs_verified":False,"native_encounter_loaded":False,
        "game_exe_tested":False,"can_install":False}

def reject_unverified_slots(data:dict,*,area_key:str,method:str,
                            proposed_slots:list[dict])->dict:
    """G04.2 is source-closed: numerical weights need later G04.4 evidence."""
    area_record(data,area_key)
    if not isinstance(proposed_slots,list) or proposed_slots:
        deny("source-less slot, species or percentage cannot be accepted at G04.2")
    if method not in [x["pbs_method"] for x in data["method_registry"]]:
        deny("method is not recognized by Blue PBS parser")
    return {"status":"NO_NATIVE_SLOTS_IMPORTED", "area_key":area_key,
        "slots":[],"weight_percentages":None,"game_exe_tested":False,
        "can_install":False}

def demo(data:dict)->dict:
    questions=[
        ("UNOVA_ROUTE_01","LandMorning","MORNING","SPRING"),
        ("UNOVA_WELLSPRING_CAVE","Cave","ANY","WINTER"),
        ("UNOVA_UNDELLA_BAY","OldRod","ANY","SUMMER"),
        ("UNOVA_GIANT_CHASM","CaveNight","NIGHT","AUTUMN")]
    details=[plan_audit(data,area_key=a,method=m,time_bucket=t,
                        season_bucket=s) for a,m,t,s in questions]
    if not all(x["status"]=="AUDIT_QUESTION_NOT_AN_ENCOUNTER_ASSIGNMENT" and
               x["weight_percentages"] is None and x["encounter_rate"] is None and
               x["encounter_slots"]==[] for x in details):
        deny("candidate-only regression introduced invented encounters")
    return {"phase":"G04.2","audit_questions":len(details),
        "route_grass":True,"cave":True,"fishing":True,
        "times":["MORNING","ANY","ANY","NIGHT"],
        "seasons":["SPRING","WINTER","SUMMER","AUTUMN"],
        "native_encounters":0,"verified_probabilities":0,
        "game_exe_tested":False,"can_install":False}

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    actions=parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check",action="store_true")
    actions.add_argument("--simulate-demo",action="store_true")
    args=parser.parse_args(argv)
    try:
        data,areas,regions,report=load_project()
        print(json.dumps(report if args.check else demo(data),
                         ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,TypeError,KeyError,IndexError,OSError,RecursionError,
            SyntaxError,UnicodeError) as exc:
        print("UNOVA_G04_2_BLOCKED: "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
