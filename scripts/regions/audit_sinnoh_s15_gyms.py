#!/usr/bin/env python3
"""S15: auditar contratos inertes dos oito ginasios, sem gameplay nativo."""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
GYMS=ROOT/"data/regions/sinnoh-gyms-s15.json"
TRAINERS=ROOT/"data/regions/sinnoh-trainer-teams-ch15.json"
BADGES=ROOT/"data/regions/sinnoh-badges-hms-contract.json"
REGISTRY=ROOT/"site/public/data/regions.json"
CAMPAIGN=ROOT/"scripts/battle_polish/Campaign.rb"
REGIONS=ROOT/"scripts/battle_polish/Regions.rb"
RUBY=ROOT/"scripts/regions/SinnohGymContracts.rb"
ORDER=("Roark","Gardenia","Fantina","Maylene","Crasher Wake","Byron","Candice","Volkner")
POLICY={
  "local_region_only": True,
  "sequenced_platinum_gym_victories": True,
  "battle_result_must_be_engine_confirmed": True,
  "award_only_once": True,
  "never_award_on_loss_or_escape": True,
  "deny_manual_injected_outcome": True,
  "no_native_decades_badge_change": True,
  "no_cross_region_key_items": True,
  "hm_pickup_requires_local_event": True,
  "maintain_dynamic_70_90_balance": True,
  "master_four_pokemon_policy_preserved": True,
  "no_fake_fixed_level_playback": True,
  "no_pbs_mutation": True
};
TOP={
 "schema":1,"region":"SINNOH","task":"S15",
 "status":"GYM_PIPELINE_CONTRACT_ONLY_NO_NATIVE_INSTALL",
 "sources":{
  "rosters":"data/regions/sinnoh-trainer-teams-ch15.json",
  "badges":"data/regions/sinnoh-badges-hms-contract.json",
  "region_registry":"site/public/data/regions.json",
  "balance":"scripts/battle_polish/Campaign.rb",
  "runtime":"scripts/battle_polish/Regions.rb",
  "approval":"docs/SINNOH_S15_OITO_GINASIOS_INSIGNIAS_ACEITE.md"
 },
 "gym_count":8,"native_source_count":0,"verified_native_sources":{},
 "approved_for_install":False,"battles_playable":False,
 "native_badges_awardable":False,"native_pbs_compiled":False,
 "game_exe_tested":False,"joiplay_tested":False,"native_qa_approved":False,
 "can_write_game":False,"policy":POLICY,
}
EXPECTED_GYM_FLAGS={
 "trainer_pbs_compiled":False,"physical_map_installed":False,
 "physical_event_installed":False,"battle_victory_verified":False,
 "badge_award_verified":False,"game_exe_verified":False
}
NIL_KEYS=("trainer_type","trainer_name","trainer_version",
          "physical_map_id","physical_event_id","source_sha256",
          "verified_native_callback")
RUNTIME_REQUIRED=(
 "module BlueSinnohGymContracts",
 "VERIFIED_NATIVE_SOURCES = {}.freeze",
 "def self.checkpoint(state, gym_id)",
 "def self.record_from_native(state, gym_id, result, source_id: nil)",
 "result == :engine_battle_won",
 "VERIFIED_NATIVE_SOURCES[gym_id] == source_id",
 "BlueRegions.award(state,'SINNOH',BADGES[GYMS.index(gym_id)])",
 "BlueRegions.valid_sinnoh_badges?(state)",
 "state['current']=='SINNOH'",
)
RUNTIME_FORBIDDEN=(
 "EventHandlers.add(","Game_Map.prepend(","BlueMusic.install",
 "File.write(","load_data(","pbMessage(","GameData::Trainer.register(",
 "def self.install","BlueRegions.award(state,'KANTO'"
)

def fail(msg):
    raise ValueError("SINNOH_S15_BLOCKED: "+msg)

def audit(spec,teams,hms,regions,campaign,runtime,adapter):
    if not isinstance(spec,dict) or set(spec)!=set(TOP)|{"gyms","notes"}:
        fail("manifesto incompleto ou com chaves inesperadas")
    for key,wanted in TOP.items():
        if type(spec[key]) is not type(wanted) or spec[key]!=wanted:
            fail("status/fonte/instalacao/balanceamento falso: "+key)
    if not isinstance(spec["notes"],str) or len(spec["notes"])<130:
        fail("falta aviso de limites")
    gyms=spec["gyms"]
    historical=[x for x in teams.get("trainers",[]) if x.get("role")=="GYM_LEADER"]
    hm_rules=hms.get("rules",[])
    hm_by_badge={x["badge"]:x for x in hm_rules}
    if (not isinstance(gyms,list) or len(gyms)!=8 or
        len(historical)!=8 or len(hm_rules)!=8 or len(hm_by_badge)!=8):
        fail("oito ginasios e oito permissoes HM obrigatorios")
    expected_order=[x["name"] for x in historical]
    if expected_order!=list(ORDER):
        fail("ordem Platinum ou fonte CH15 adulterada")
    if [x.get("badge") for x in historical]!=["COAL","FOREST","RELIC","COBBLE","FEN","MINE","ICICLE","BEACON"]:
        fail("badge da lideranca historica divergente")
    registry=regions.get("regions",{}).get("SINNOH",{})
    if registry.get("status")!="planned":
        fail("Sinnoh falsely playable")
    milestones=registry.get("milestones")
    if milestones!=[x["badge"] for x in hm_rules]:
        fail("ordem CH11 HMs foi alterada")
    if set(milestones)!={x["badge"] for x in historical}:
        fail("ordem narrativa e badges CH11 divergem")
    for i,(g,t) in enumerate(zip(gyms,historical)):
        if not isinstance(g,dict) or set(g)!={
            "id","order","name","reference_city","badge","field_move","hm_item",
            "prerequisite_badges","reference_team_species","reference_team_source",
            *NIL_KEYS,*EXPECTED_GYM_FLAGS,"status"
        }:
            fail("campos de ginasio invalidos")
        rule=hm_by_badge[t["badge"]]
        wanted={
            "id":t["id"],"order":i+1,"name":t["name"],
            "reference_city":t["reference_city"],"badge":t["badge"],
            "field_move":rule["field_move"],"hm_item":rule["hm_item"],
            "prerequisite_badges":[x["badge"] for x in historical[:i]],
            "reference_team_species":t["first_battle"]["species"],
            "reference_team_source":"CH15_PLATINUM_ONLY",
            **{k:None for k in NIL_KEYS},**EXPECTED_GYM_FLAGS,
            "status":"GYM_REFERENCE_NOT_INSTALLED"
        }
        if any(type(g[k]) is not type(v) or g[k]!=v for k,v in wanted.items()):
            fail("ginasio, badges, PBS, mapa ou resultados fabricados: "+t["name"])
        if rule["verified_gym_event"] is not False:
            fail("CH11 nao comprova evento fisico")
        if t["native_pbs"]["compiled"] is not False or t["native_pbs"]["event_bound"] is not False:
            fail("CH15 nao comprova PBS fisico")
    if ("master? ? 90 : 70" not in campaign or
        "!BlueCampaign.boss?(trainer)" not in campaign or
        "def self.award(state, region, key)" not in runtime or
        "def self.valid_sinnoh_badges?(state)" not in runtime):
        fail("protecoes de nivel ou insigias em runtime alteradas")
    if any(k not in adapter for k in RUNTIME_REQUIRED):
        fail("Ruby S15 sem guarda obrigatoria")
    executable="\n".join(x for x in adapter.splitlines() if not x.lstrip().startswith("#"))
    if any(k in executable for k in RUNTIME_FORBIDDEN):
        fail("S15 tenta instalar mapa/treinador/evento global")
    return {"region":"SINNOH","task":"S15","status":TOP["status"],
            "gyms":8,"historical_order":list(ORDER),
            "native_map_ids_verified":0,"native_pbs_compiled":0,
            "native_badge_awards":0,"game_exe_tested":False,
            "joiplay_tested":False,"can_install":False}

def run():
    return audit(*[json.loads(p.read_text("utf-8")) for p in
                  (GYMS,TRAINERS,BADGES,REGISTRY)],
                 CAMPAIGN.read_text("utf-8"),REGIONS.read_text("utf-8"),
                 RUBY.read_text("utf-8"))

if __name__=="__main__":
    try:
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        print("SINNOH_S15_GYMS_OK_OFFLINE_ONLY")
    except (ValueError,KeyError,TypeError,OSError) as e:
        print(str(e),file=sys.stderr);sys.exit(2)
