#!/usr/bin/env python3
"""G05.4: auditable OFFLINE blackout and state-isolation fixtures only.

Real native source: BlueRegionalRespawn (checkpoint + pbStartOver), BlueRegionTravel
(item/Box/mechanics) and BlueRegions (badges/progression). This NEVER writes game,
maps, saves or any real player/PC data. A missing safe Center remains a documented
native risk; synthetic QA blocks instead of inventing a Unova destination.
"""
from __future__ import annotations
import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any
import audit_unova_g05_regional_items as items
import audit_unova_g05_badges_specials as badges

ROOT=Path(__file__).resolve().parents[2]
FILE="data/regions/unova-g05-blackout-state-contract.json"
REGIONS=("DECADES","KANTO","JOHTO","HOENN")
SOURCES={
 "registry":"site/public/data/regions.json",
 "items":"data/regions/unova-g05-regional-items-contract.json",
 "specials":"data/regions/unova-g05-badges-specials-contract.json",
 "travel":"data/regions/unova-g05-travel-contract.json",
 "respawn":"scripts/battle_polish/RegionalRespawn.rb",
 "travel_runtime":"scripts/battle_polish/RegionTravel.rb",
 "regions_runtime":"scripts/battle_polish/Regions.rb",
 "economy":"scripts/battle_polish/Economy.rb",
 "campaign":"scripts/battle_polish/Campaign.rb",
 "respawn_tests":"tests/regional_respawn_runtime.rb",
 "tracker":"site/public/data/unova-github-progress.json",
}
EVIDENCE={k:None for k in (
 "unova_center_mapids","unova_center_ownership","unova_healing_spot_metadata",
 "unova_installed_fallback","unova_nurse_event","unova_save_qa",
 "unova_game_exe_qa","unova_android_qa","unova_source_rights")}
POLICY={
 "native_hook":"BlueRegionalRespawn.NativeCheckpoints",
 "native_blackout":"pbStartOver",
 "native_engine_performs_real_healing_and_transfer":True,
 "nurse_registration_requires_real_local_center":True,
 "native_current_center_first":True,
 "remembered_current_region_center_second":True,
 "verified_current_region_fallback_third":True,
 "never_use_foreign_checkpoint":True,
 "no_safe_center_fixture_blocks":True,
 "native_no_fallback_may_leave_stale_checkpoint":True,
 "native_owner_only_check_may_accept_foreign_point":True,
 "fixture_stricter_than_native_risk_is_documented":True,
 "unova_center_not_installed":True,
 "no_extra_engine_heal":True,
 "preserve_money_and_coins":True,
 "preserve_global_boxes_and_party":True,
 "preserve_global_tms_and_consumables":True,
 "preserve_local_hms_and_key_items":True,
 "preserve_native_badges_and_regional_progress":True,
 "preserve_mechanics_by_region":True,
 "rollback_failure_before_commit":True,
 "legacy_decades_does_not_migrate":True,
 "no_native_game_or_save_write":True,
}
SIM={"scope":"G05_4_SYNTHETIC_NOT_NATIVE_SAVE",
     "only_fixture_ids":True,"labels_not_mapids":True,
     "no_native_save_adapter":True,"no_real_healing":True,
     "no_real_economy_logic":True,"unova_not_playable":True}
CONTRACT_FIELDS={"schema","phase","region","campaign","status","sources",
 "native_evidence","runtime_regions","policy","simulation",
 "native_game_modified","native_saves_modified","native_badges_modified",
 "native_center_installed","game_exe_tested","android_tested","can_install","notes"}
STATE_FIELDS={"scope","version","current","position","native_checkpoint","checkpoint_owner",
 "remembered","verified_centers","fallbacks","nurse_map","money","coins",
 "bag","party","boxes","native_badges","leagues","field_events",
 "mechanics_by_region","active_mechanics","heals","blackouts"}
RUBY={
 "respawn":(
  "REGIONS = %w[DECADES KANTO JOHTO HOENN SINNOH].freeze",
  'when "SINNOH" then sinnoh_map_ids.include?(map_id)',
  "def self.state","def self.checkpoint","def self.region_map?(region, map_id)",
  "def self.real_center?(region, id)","def self.remember!",
  "def self.before_blackout!","fallback(current)","return unless valid?(candidate)",
  "return if valid?(native) && (owner == current ||",
  'stored["regional_pokecenters"] ||= {}',
  'stored["regional_pokecenter_owner"] = current',
  "def pbSetPokemonCenter(*args, &block)","def pbStartOver(*args, &block)",
  "BlueRegionalRespawn.before_blackout!","Object.prepend(NativeCheckpoints)"),
 "travel_runtime":(
  "def self.stage_local_bag(state, destination)",
  'next_state["region_key_items"]',
  'next_state["mechanics_by_region"]',
  "$player.party.replace(old_party)",
  "pc_storage.items.replace(old_pc_items) if pc_storage && old_pc_items"),
 "regions_runtime":(
  "def self.crystal_total(state, native_total)",
  'native_total + (circuit - ["DECADES"]).sum'),
 "economy":("$player.money",),
 "campaign":("def self.default_mechanics_for(region)",
             'rules["dynamax"] = false if region == "DECADES"'),
 "respawn_tests":("BlueRegionalRespawn.install","pbStartOver",
                  "regional_pokecenters",
                  "blackout did not use the native engine exactly once"),
}
LABEL=re.compile(r"FIXTURE_[A-Z][A-Z0-9_]*\Z")
FAULTS=("after_checkpoint","after_owner","after_heal","after_transfer")
def deny(x:str)->None: raise ValueError("UNOVA_G05_4_BLOCKED: "+x)
def exact(x:Any,keys:set[str],name:str)->None:
    if not isinstance(x,dict) or set(x)!=keys: deny(name+" schema changed")
def load(root:Path,path:str)->dict: return items.load_json(root,path)
def read(root:Path,path:str)->str: return items.read_source(root,path)
def ident(x:Any,name:str,nullable:bool=False)->None:
    if x is None and nullable:return
    if type(x) is not str or not LABEL.fullmatch(x):deny(name+" must be synthetic ID")
def validate_catalog(d:dict,reg:dict,prior:list[dict],board:dict,ruby:dict)->dict:
    exact(d,CONTRACT_FIELDS,"G05.4 contract")
    expected={"schema":1,"phase":"G05.4","region":"UNOVA","campaign":"WHITE_BW",
      "status":"PLANNED_OFFLINE_RESPAWN_SHARED_STATE_AUDIT_ONLY",
      "sources":SOURCES,"native_evidence":EVIDENCE,"runtime_regions":list(REGIONS),
      "policy":POLICY,"simulation":SIM,"native_game_modified":False,
      "native_saves_modified":False,"native_badges_modified":False,
      "native_center_installed":False,"game_exe_tested":False,
      "android_tested":False,"can_install":False}
    for k,v in expected.items():
        if d.get(k)!=v or type(d.get(k)) is not type(v):deny("source/proof/policy changed: "+k)
    rr=reg.get("regions",{})
    if (rr.get("UNOVA",{}).get("status")!="planned"
        or not set(REGIONS).issubset(rr)
        or any(p.get("can_install") is not False for p in prior)
        or [p.get("phase") for p in prior]!=["G05.1","G05.2","G05.3"]
        or board.get("status")!="PLANNED_NOT_NATIVE_PLAYABLE"
        or board.get("native_technical_bar",{}).get("completed")!=0
        or board.get("native_playable_bar",{}).get("completed")!=0):
        deny("planned region/source predecessor/native bars changed")
    if not any(t.get("id")=="G05.4" and t.get("status") in ("done","pending")
       for g in board.get("groups",[]) for t in g.get("tasks",[])):
        deny("G05.4 milestone missing")
    for k,s in RUBY.items():
        if k not in ruby or any(q not in ruby[k] for q in s):
            deny("native Ruby/fixture source drift: "+k)
    if not isinstance(d.get("notes"),list) or len(d["notes"])<5 or any(
      not isinstance(x,str) or not x.strip() for x in d["notes"]):
        deny("native limitations missing")
    return {"phase":"G05.4","native_routable_regions":list(REGIONS),
       "native_unova_centers":0,"fixture_only":True,
       "native_fallback_risks_documented":2,
       "native_saves_modified":False,"game_exe_tested":False,"can_install":False}

def load_project(root:Path=ROOT)->tuple[dict,dict,dict]:
    root=Path(root);d=load(root,FILE);s=d["sources"]
    reg=load(root,s["registry"])
    prior=[load(root,s[k]) for k in ("items","specials","travel")]
    board=load(root,s["tracker"])
    ruby={k:read(root,s[k]) for k in RUBY}
    return d,reg,validate_catalog(d,reg,prior,board,ruby)

def validate_state(st:Any,reg:dict)->dict:
    exact(st,STATE_FIELDS,"blackout fixture")
    if st["scope"]!=SIM["scope"] or type(st["version"]) is not int or st["version"]!=1:
        deny("native/future save not accepted")
    current=st["current"]
    if type(current) is not str or current not in reg["regions"]:
        deny("unknown current region")
    for k in ("position","native_checkpoint","nurse_map"):
        ident(st[k],k,nullable=k!="position")
    owner=st["checkpoint_owner"]
    if owner is not None and (type(owner) is not str or owner not in reg["regions"]):
        deny("invalid checkpoint owner")
    for k in ("verified_centers","fallbacks"):
        exact(st[k],set(REGIONS),k)
    seen=[]
    for name,centers in st["verified_centers"].items():
        if not isinstance(centers,list) or len(centers)>32 or len(centers)!=len(set(map(str,centers))):
            deny("invalid local Center list")
        for center in centers:ident(center,name)
        seen+=centers
    if len(seen)!=len(set(seen)):deny("same Center assigned to multiple regions")
    for name,p in st["fallbacks"].items():
        ident(p,"fallback",nullable=True)
        if p is not None and p not in st["verified_centers"][name]:
            deny("fallback must be locally verified")
    if not isinstance(st["remembered"],dict) or any(x not in REGIONS for x in st["remembered"]):
        deny("invalid regional remembered checkpoints")
    for p in st["remembered"].values():ident(p,"remembered",nullable=True)
    for k in ("money","coins","heals","blackouts"):
        v=st[k]
        if type(v) is not int or not 0<=v<=10_000_000:deny("invalid currency/counter "+k)
    if (items.validate_state(st["bag"],reg)["current"]!=current
      or badges.validate_fixture(st["party"],reg)["current"]!=current):
        deny("Bag, party and game regions differ")
    boxes=st["boxes"]
    if not isinstance(boxes,dict) or len(boxes)>180:deny("invalid Boxes")
    for slot,mon in boxes.items():ident(slot,"Box slot");ident(mon,"Box Pokemon")
    if (len(set(boxes.values()))!=len(boxes)
       or set(boxes.values()) & {x["id"] for x in st["party"]["party"]}):
        deny("duplicate Pokemon between party and Box")
    if not isinstance(st["native_badges"],list) or any(type(x) is not bool for x in st["native_badges"]):
        deny("badges must remain native boolean fixture")
    if not isinstance(st["leagues"],list) or len(st["leagues"])!=len(set(st["leagues"])) or any(
        type(x) is not str or x not in reg["regions"] for x in st["leagues"]):
        deny("regional league progress invalid")
    events=st["field_events"]
    if not isinstance(events,dict) or any(
       x not in reg["regions"] or not isinstance(v,list) or len(v)!=len(set(v)) or
       any(type(a) is not str or not a.startswith("FIXTURE_") for a in v)
       for x,v in events.items()):deny("field events invalid")
    for k in ("mechanics_by_region","active_mechanics"):
        if not isinstance(st[k],dict):deny("mechanics snapshot invalid")
    if any(x not in reg["regions"] or not isinstance(v,dict) for x,v in st["mechanics_by_region"].items()):
        deny("regional mechanics ledger invalid")
    settings=[st["active_mechanics"],*st["mechanics_by_region"].values()]
    if any(type(k) is not str or not k.startswith("FIXTURE_") or type(v) is not bool
           for d in settings for k,v in d.items()):deny("mechanics flags invalid")
    return st

def local(st:dict,r:str,p:Any)->bool:
    return type(p) is str and p in st["verified_centers"][r]

def remember(st:dict,reg:dict)->dict:
    validate_state(st,reg)
    out=copy.deepcopy(st);r=st["current"]
    if r not in REGIONS or st["native_checkpoint"]!=st["nurse_map"] or not local(st,r,st["nurse_map"]):
        return {"status":"UNVERIFIED_NURSE_NO_RECORD","fixture":out,"native_save_modified":False}
    out["remembered"][r]=st["native_checkpoint"]
    out["checkpoint_owner"]=r
    return {"status":"SYNTHETIC_LOCAL_CENTER_RECORDED","fixture":out,"native_save_modified":False}

def refused(st:dict,status:str)->dict:
    return {"status":status,"fixture":copy.deepcopy(st),
            "native_engine_invoked":False,"native_save_modified":False,"can_install":False}

def blackout(st:dict,reg:dict,*,fail_at:str|None=None)->dict:
    validate_state(st,reg)
    if fail_at is not None and fail_at not in FAULTS:deny("unknown fault injection")
    original=copy.deepcopy(st);r=st["current"]
    if r not in REGIONS:return refused(st,"PLANNED_REGION_RESPAWN_UNVERIFIED")
    # Unlike the native hook, the fixture insists on proven Center OWNERSHIP.
    if local(st,r,st["native_checkpoint"]) and st["checkpoint_owner"] in (None,r):
        target=st["native_checkpoint"];origin="CURRENT_LOCAL_CHECKPOINT"
    elif local(st,r,st["remembered"].get(r)):
        target=st["remembered"][r];origin="REMEMBERED_LOCAL_CENTER"
    elif local(st,r,st["fallbacks"][r]):
        target=st["fallbacks"][r];origin="VERIFIED_LOCAL_FALLBACK"
    else:return refused(st,"BLOCKED_NO_VERIFIED_LOCAL_CENTER")
    try:
        staged=copy.deepcopy(st)
        staged["native_checkpoint"]=target
        if fail_at=="after_checkpoint":raise RuntimeError("simulated checkpoint error")
        staged["checkpoint_owner"]=r
        if fail_at=="after_owner":raise RuntimeError("simulated owner error")
        staged["heals"]+=1
        staged["blackouts"]+=1
        if fail_at=="after_heal":raise RuntimeError("simulated engine error")
        staged["position"]=target
        if fail_at=="after_transfer":raise RuntimeError("simulated position error")
        validate_state(staged,reg)
    except (ValueError,RuntimeError,TypeError,KeyError,IndexError):
        if st!=original:deny("input mutated during simulated rollback")
        return {"status":"SYNTHETIC_FAILURE_ROLLED_BACK",
                "fixture":original,"all_fields_preserved":True,
                "native_engine_invoked":False,"native_save_modified":False,"can_install":False}
    if st!=original:deny("input mutated during simulated blackout")
    return {"status":"SYNTHETIC_BLACKOUT_ONCE_NOT_NATIVE",
            "checkpoint_source":origin,"fixture":staged,
            "heals_added":1,"blackouts_added":1,"native_engine_invoked":False,
            "native_save_modified":False,"can_install":False}

def fixture(reg:dict)->dict:
    item=lambda n,k:{"id":"FIXTURE_"+n,"qty":1,"kind":k}
    mon=lambda n,flags:{"id":"FIXTURE_"+n,"flags":flags,"base_flags":[],
             "form":0,"egg":False,"fainted":False}
    centers={
      "DECADES":["FIXTURE_DECADES_CHERRYHILL_CENTER"],
      "KANTO":["FIXTURE_KANTO_VIRIDIAN_CENTER","FIXTURE_KANTO_CERULEAN_CENTER"],
      "JOHTO":["FIXTURE_JOHTO_CHERRYGROVE_CENTER"],
      "HOENN":["FIXTURE_HOENN_OLDALE_CENTER"],
    }
    return {
     "scope":SIM["scope"],"version":1,"current":"KANTO",
     "position":"FIXTURE_KANTO_ROUTE",
     "native_checkpoint":"FIXTURE_DECADES_CHERRYHILL_CENTER",
     "checkpoint_owner":"DECADES",
     "remembered":{"KANTO":"FIXTURE_KANTO_CERULEAN_CENTER",
                   "DECADES":"FIXTURE_DECADES_CHERRYHILL_CENTER"},
     "verified_centers":centers,
     "fallbacks":{k:v[0] for k,v in centers.items()},
     "nurse_map":None,
     "money":4500,"coins":125,
     "bag":{"scope":items.SCOPE,"current":"KANTO",
            "bag":[item("KANTO_HM","HM"),item("KANTO_KEY","KEY_ITEM"),
                   item("TM_GLOBAL","TM"),item("POTION","CONSUMABLE")],
            "pc":[item("KANTO_PC_KEY","KEY_ITEM"),item("MEGA_STONE","MEGA_STONE")],
            "registered":["FIXTURE_KANTO_HM","FIXTURE_TM_GLOBAL"],
            "vault":{"DECADES":{"items":[item("DECADES_HM","HM")],
                                 "registered":["FIXTURE_DECADES_HM"],
                                 "pc_items":[item("DECADES_KEY","KEY_ITEM")]}},
            "bag_capacity":16,"pc_capacity":16,"badges":[]},
     "party":{"scope":badges.SIMULATION["scope"],"version":1,"current":"KANTO",
              "achievements":{"KANTO":reg["regions"]["KANTO"]["milestones"][:2],
                              "UNOVA":reg["regions"]["UNOVA"]["milestones"][:1]},
              "native_decades_badge_count":3,"hisui_complete":False,
              "party":[mon("NORMAL",[]),mon("PARADOX",["Paradox"])],
              "free_box_slots":["FIXTURE_BOX_A","FIXTURE_BOX_B"]},
     "boxes":{"FIXTURE_BOX_OCCUPIED":"FIXTURE_BOXED_MON"},
     "native_badges":[False,True,False],
     "leagues":["KANTO"],"field_events":{"KANTO":["FIXTURE_LOCAL_CUT"]},
     "mechanics_by_region":{"DECADES":{"FIXTURE_MEGA":True,"FIXTURE_DYNAMAX":False},
                             "KANTO":{"FIXTURE_MEGA":True,"FIXTURE_DYNAMAX":True}},
     "active_mechanics":{"FIXTURE_MEGA":True,"FIXTURE_DYNAMAX":True},
     "heals":2,"blackouts":1,
    }

def demo(d:dict,reg:dict)->dict:
    st=fixture(reg)
    ok=blackout(st,reg)
    failure=blackout(st,reg,fail_at="after_heal")
    planned=copy.deepcopy(st);planned["current"]="UNOVA"
    planned["bag"]["current"]="UNOVA";planned["party"]["current"]="UNOVA"
    no=copy.deepcopy(st);no["verified_centers"]["KANTO"]=[]
    no["fallbacks"]["KANTO"]=None
    local_record=copy.deepcopy(ok["fixture"])
    local_record["native_checkpoint"]="FIXTURE_KANTO_CERULEAN_CENTER"
    local_record["nurse_map"]="FIXTURE_KANTO_CERULEAN_CENTER"
    return {"phase":"G05.4","fixture_only":True,"source":ok["checkpoint_source"],
     "healed_exactly_once":ok["fixture"]["heals"]==st["heals"]+1,
     "money_preserved":ok["fixture"]["money"]==st["money"],
     "coins_preserved":ok["fixture"]["coins"]==st["coins"],
     "items_preserved":ok["fixture"]["bag"]==st["bag"],
     "boxes_preserved":ok["fixture"]["boxes"]==st["boxes"],
     "progress_preserved":ok["fixture"]["party"]==st["party"],
     "rollback_preserved":failure["fixture"]==st,
     "no_safe_center":blackout(no,reg)["status"],
     "unova_not_native":blackout(planned,reg)["status"],
     "nurse_record":remember(local_record,reg)["status"],
     "native_saves_modified":False,"can_install":False}

def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--simulate-demo",action="store_true")
    args=p.parse_args(argv)
    try:
        d,reg,report=load_project()
        print(json.dumps(report if args.check else demo(d,reg),ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,TypeError,KeyError,IndexError,RecursionError,UnicodeError,OSError) as exc:
        print("UNOVA_G05_4_BLOCKED: "+str(exc));return 2
if __name__=="__main__":raise SystemExit(main())
