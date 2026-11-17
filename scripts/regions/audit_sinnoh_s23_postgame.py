#!/usr/bin/env python3
"""S23 fail-closed contract auditor; no native map, quest, item, roster or playtest."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"data/regions/sinnoh-postgame-s23.json"
COVERAGE=ROOT/"data/regions/sinnoh-coverage.json"
TEAMS=ROOT/"data/regions/sinnoh-trainer-teams-ch15.json"
STORY=ROOT/"data/regions/sinnoh-story-ch14-contract.json"
REGISTRY=ROOT/"site/public/data/regions.json"
RUNTIME=ROOT/"scripts/regions/SinnohPostgameContracts.rb"
STORY_RUBY=ROOT/"scripts/regions/SinnohStoryContracts.rb"
REGIONS=ROOT/"scripts/battle_polish/Regions.rb"
CAMPAIGN=ROOT/"scripts/battle_polish/Campaign.rb"
BLUE_STORY=ROOT/"scripts/battle_polish/Story.rb"
FIXTURE=ROOT/"tests/sinnoh_s23_postgame_runtime.rb"

EVENT_IDS=("P10_BATTLE_ZONE_ENTRY","P10_HEATRAN_QUEST","P10_CRESSELIA_EVENT",
           "P10_DARKRAI_CONDITIONAL_QUEST","P10_SHAYMIN_CONDITIONAL_QUEST",
           "P10_OFFICIAL_STRONGEST_TEAM_REMATCHES")
EVENT_OUTCOMES=("arrival_confirmed","quest_completed","event_resolved",
                "conditional_event_resolved","conditional_event_resolved","rematch_won")
EVENT_AREAS=("FIGHT_AREA","STARK_MOUNTAIN","FULLMOON_ISLAND",
             "NEWMOON_ISLAND","FLOWER_PARADISE","BATTLE_FRONTIER")
ELITE=("SINNOH_AARON","SINNOH_BERTHA","SINNOH_FLINT","SINNOH_LUCIAN","SINNOH_CYNTHIA")
SOURCE_FIELDS={
    "source_coverage":"data/regions/sinnoh-coverage.json",
    "source_teams":"data/regions/sinnoh-trainer-teams-ch15.json",
    "ch14_source":"data/regions/sinnoh-story-ch14-contract.json",
    "runtime":"scripts/regions/SinnohPostgameContracts.rb",
    "source_engine":"scripts/battle_polish/Regions.rb",
    "source_story_engine":"scripts/battle_polish/Story.rb",
    "source_campaign_engine":"scripts/battle_polish/Campaign.rb",
}
RESTRICTIONS={
    "does_not_inject_npc_or_portals":True,
    "never_autogrants_legendary":True,
    "never_creates_event_items":True,
    "no_unverified_historical_level_as_runtime_level":True,
    "no_unverified_rematch_team_as_installed":True,
    "no_strongest_until_global_ten_leagues":True,
    "no_automatic_hall_or_badges":True,
    "no_duplicate_quest_rewards_or_save_records":True,
    "no_repeatable_battle_claim_without_native_handler":True,
    "no_foreign_region_saves_changed":True,
    "special_party_requires_eight_local_badges":True,
    "never_autoloads_into_game_exe":True,
}
FALSE_FLAGS=(
    "postgame_native_maps_installed","heatran_native_event_verified",
    "cresselia_native_event_verified","darkrai_native_event_verified",
    "shaymin_native_event_verified","gym_strongest_native_teams_verified",
    "elite_champion_native_rematches_verified","game_exe_executed",
    "joiplay_executed","native_qa_approved","gameplay_certified","can_install",
)
EMPTY_FIELDS=("verified_native_sources","installed_postgame_map_ids",
              "compiled_rematch_pbs","verified_event_items",
              "verified_static_legendary_events")
BASE={
    "schema":1,"region":"SINNOH","stage":"S23",
    "status":"POSTGAME_OPTIONAL_GATES_OFFLINE_NO_NATIVE_ASSETS",
    **SOURCE_FIELDS,
    "save_key":"sinnoh_s23",
    "requires_separate_hall_of_fame":True,
    "global_world_champion_requires_all_ten_leagues":True,
    "local_historical_rematches_not_blue_full_power":True,
    "global_strongest_requires_verified_native_roster":True,
    "original_level_numbers_never_native":True,
    "reference_areas_count":14,"reference_event_count":6,
    "elite_champion_historical_rematch_count":5,
    "gym_historical_rematch_count":0,
    "historical_elite_refs":list(ELITE),
    "restrictions":RESTRICTIONS,
    "verification":{key:False for key in FALSE_FLAGS},
}
EXPECTED_KEYS=set(BASE)|set(EMPTY_FIELDS)|{"events","note"}
RUBY_TOKENS=(
    "module BlueSinnohPostgameContracts",
    'SAVE_KEY = "sinnoh_s23".freeze',
    "VERIFIED_NATIVE_SOURCES = {}.freeze",
    "BlueSinnohStoryContracts.recorded(state)",
    "BlueSinnohStoryContracts.league_cleared?(state)",
    "BlueRegions.world_champion?(state)",
    "BlueRegions.profile(state, verified_roster) == :world_champion_rematch",
    "return :hall_of_fame_required unless valid_postleague?(state)",
    "return :battle_zone_entry_required",
    "return :special_event_item_not_verified",
    "return :all_ten_leagues_required",
    "return :native_strongest_roster_not_verified",
    "return :already_recorded if history.include?(event)",
    "record_with_sources(state, event, outcome, source, VERIFIED_NATIVE_SOURCES,",
    "private_class_method :record_with_sources",
)
REGION_TOKENS=(
    "def self.world_champion?(state)",
    '(circuit - state["leagues"]).empty?',
    "def self.profile(state, verified_rematch)",
    "world_champion?(state) && verified_rematch ? :world_champion_rematch : :first_clear",
    "def self.allow_specials?(state, region, native_badges = [])",
    "local_achievements(state, region, native_badges).length >= 8",
    "def self.valid_sinnoh_badges?(state)",
)
CAMPAIGN_TOKENS=("master? ? 90 : 70","def self.boss?(trainer)",
                 "def self.trainer_level(trainer,party=$player.party)")
STORY_TOKENS=("def self.regional_first_boss?(trainers)",
              "def self.rematches","def self.replay(row)")
FIXTURE_TOKENS=(
    "SINNOH_S23_POSTGAME_QUESTS_HISTORICAL_VS_GLOBAL_REMATCH_IDEMPOTENT_OFFLINE_OK",
    "post.record_from_native(state, event, outcome: kind, source: source,",
    "send(:record_with_sources,",
    "BlueRegions.allow_specials?(limited, \"SINNOH\")",
    "BlueRegions.world_champion?(state)",
    "BlueSinnohStoryContracts",
)
def blocked(reason:str)->None:
    raise ValueError("SINNOH_S23_BLOCKED: "+reason)

def audit(contract:dict, coverage:dict, teams:dict, story:dict, registry:dict,
          ruby:str, story_ruby:str, regions:str, campaign:str,
          blue_story:str, fixture:str)->dict:
    if not isinstance(contract,dict) or set(contract)!=EXPECTED_KEYS:
        blocked("campos S23 ausentes ou nao previstos")
    for key,expected in BASE.items():
        if type(contract.get(key)) is not type(expected) or contract[key]!=expected:
            blocked("politica S23 adulterada: "+key)
    if any(contract.get(k)!=[] for k in EMPTY_FIELDS):
        blocked("MapIDs/PBS/fontes/event items nativos inventados")
    if not isinstance(contract.get("note"),str) or len(contract["note"])<240:
        blocked("limites de QA nativa omitidos")
    if (not isinstance(story,dict) or story.get("region")!="SINNOH"
        or story.get("status")!="PLANNED_NATIVE_HOOKS_NOT_INSTALLED"
        or story.get("save_key")!="sinnoh_ch14"
        or story.get("hall_of_fame_requires_separate_engine_confirmation") is not True
        or story.get("native_hall_of_fame_verified") is not False
        or story.get("gameplay_verified") is not False):
        blocked("CH14 declarando Hall de Sinnoh nativo sem prova")
    steps=story.get("steps")
    if not isinstance(steps,list) or len(steps)!=22 or steps[-1].get("id")!="P09_HALL_OF_FAME":
        blocked("ultima etapa real CH14 nao e Hall of Fame")
    if (not isinstance(registry,dict) or
        registry.get("regions",{}).get("SINNOH",{}).get("status")!="planned"
        or len(registry.get("circuit",[]))!=10):
        blocked("circuito/10 ligas ou Sinnoh planned falsificados")
    if (not isinstance(coverage,dict) or coverage.get("region")!="SINNOH"
        or coverage.get("status")!="PLANNED_AUDIT_CHECKLIST_ONLY"):
        blocked("cobertura CH01 alterada ou promovida a nativo")
    phase=next((p for p in coverage.get("phases",[]) if p.get("phase")==10),None)
    if not isinstance(phase,dict):
        blocked("fase 10 Battle Zone inexistente")
    areas=phase.get("areas")
    if not isinstance(areas,list) or len(areas)!=14 or len({a.get("symbol") for a in areas})!=14:
        blocked("14 areas de referencia pós-jogo inconsistentes")
    for area in areas:
        if area.get("verified") is not False or area.get("source_map_ids")!=[] or area.get("destination_map_ids")!=[]:
            blocked("mapa da Battle Zone declarado instalado")
    reference_events=phase.get("events")
    if not isinstance(reference_events,list) or len(reference_events)!=6 or (
        [item.get("key") for item in reference_events]!=list(EVENT_IDS)
        or any(item.get("verified") is not False for item in reference_events)
    ):
        blocked("seis eventos de pos-jogo CH01 divergentes ou falsamente jogaveis")
    steps=contract.get("events")
    if not isinstance(steps,list) or len(steps)!=6:
        blocked("contrato com quantidade errada de eventos opcionais")
    for i,(key,outcome,area) in enumerate(zip(EVENT_IDS,EVENT_OUTCOMES,EVENT_AREAS)):
        expected={
            "id":key,"outcome":outcome,"reference_area":area,
            "reference_only":True,"physical_map_id":None,
            "native_callback_installed":False,"native_quest_verified":False,
            "requires_completed_sinnoh_hall_of_fame":True,
            "requires_previous_event":EVENT_IDS[0] if i==1 else None,
            "requires_event_item_verification":i in (3,4),
            "requires_all_ten_leagues":i==5,
            "requires_native_strongest_team":i==5,
            "no_granted_species":True,"no_rewards_or_items":True,
            "repeatable_battles_not_falsely_implemented":True,
        }
        if not isinstance(steps[i],dict) or steps[i]!=expected:
            blocked("checkpoints de Battle Zone/lendarios adulterados: "+key)
        if area not in {row["symbol"] for row in areas}:
            blocked("local opcional sem area de referencia: "+area)
    if not isinstance(teams,dict) or teams.get("region")!="SINNOH" or (
        teams.get("status")!="HISTORICAL_REFERENCE_ONLY_NOT_INSTALLED"
        or teams.get("native_pbs_compilation_verified") is not False
        or teams.get("native_event_battle_bindings_verified") is not False
        or teams.get("gameplay_verified") is not False
        or teams.get("can_install") is not False
        or teams.get("may_write_pbs") is not False
    ):
        blocked("CH15 time de rematch falsamente instalado")
    rows=teams.get("trainers")
    if not isinstance(rows,list) or len(rows)!=13:
        blocked("13 treinadores CH15 nao encontrados")
    index={x.get("id"):x for x in rows if isinstance(x,dict)}
    if len(index)!=13:
        blocked("id de treinador CH15 duplicado")
    for i,(key,row) in enumerate(index.items()):
        if (row.get("native_pbs",{}).get("compiled") is not False or
            row.get("native_pbs",{}).get("event_bound") is not False or
            row.get("native_pbs",{}).get("team") is not None or
            row.get("blue_strongest",{}).get("game_exe_verified") is not False or
            row.get("blue_strongest",{}).get("species") is not None):
            blocked("time Full Power ou native PBS falsamente certificado: "+key)
        hist=row.get("historical_rematch")
        if key in ELITE:
            if not isinstance(hist,dict) or hist.get("status")!="HISTORICAL_REFERENCE_ONLY" or (
                hist.get("source")!="PLATINUM_LEAGUE_REMATCH" or
                hist.get("levels_are_not_runtime_levels") is not True or
                not isinstance(hist.get("species"),list) or
                len(hist["species"])!=len(hist.get("historical_levels",[]))
            ):
                blocked("revanche historica Elite/Cynthia corrompida: "+key)
        elif hist is not None:
            blocked("revanche historica de ginasio foi inventada: "+key)
    if not isinstance(ruby,str) or any(t not in ruby for t in RUBY_TOKENS):
        blocked("runtime S23 perdeu gates de Hall/event item/world champion")
    matched=re.search(r"EVENTS\s*=\s*%w\[([^\]]+)\]",ruby,re.S)
    if not matched or tuple(matched.group(1).split())!=EVENT_IDS:
        blocked("sequencia Ruby da Battle Zone divergente")
    if not isinstance(story_ruby,str) or any(t not in story_ruby for t in (
        'SAVE_KEY = "sinnoh_ch14"','HALL_OF_FAME = "P09_HALL_OF_FAME"',
        "hall_of_fame_verified.equal?(true)",
    )):
        blocked("CH14 perdeu confirmacao separada de Hall")
    if not isinstance(regions,str) or any(t not in regions for t in REGION_TOKENS):
        blocked("BlueRegions perdeu as 10 ligas ou regra de 8 insígnias")
    if not isinstance(campaign,str) or any(t not in campaign for t in CAMPAIGN_TOKENS):
        blocked("Campanha Normal/Master do Blue foi alterada")
    if not isinstance(blue_story,str) or any(t not in blue_story for t in STORY_TOKENS):
        blocked("engine de bosses/revanches do Blue foi alterada")
    if not isinstance(fixture,str) or any(t not in fixture for t in FIXTURE_TOKENS):
        blocked("fixture S23 sem HoF idempotencia e 10 Ligas")
    return {
        "schema":1,"region":"SINNOH","stage":"S23",
        "status":"POSTGAME_OPTIONAL_GATES_VERIFIED_OFFLINE_NATIVE_PENDING",
        "reference_areas":14,"optional_events":6,
        "historical_elite_champion_reference_rematches":5,
        "verified_native_rematch_teams":0,"physical_map_ids_verified":0,
        "native_quests_installed":0,"no_granted_species":True,
        "normal_master_balance_preserved":True,
        "game_exe_or_joiplay_tested":False,"gameplay_approved":False
    }

def main()->int:
    files=(CONTRACT,COVERAGE,TEAMS,STORY,REGISTRY,RUNTIME,STORY_RUBY,
           REGIONS,CAMPAIGN,BLUE_STORY,FIXTURE)
    try:
        for f in files:
            if f.is_symlink() or not f.is_file():
                blocked("arquivo obrigatorio ausente/symlink: "+str(f))
        data=[json.loads(p.read_text("utf-8")) for p in files[:5]]
        report=audit(*data,*[p.read_text("utf-8") for p in files[5:]])
    except (OSError,ValueError,KeyError,TypeError,UnicodeError) as error:
        print(str(error),file=sys.stderr)
        return 2
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0
if __name__=="__main__":
    raise SystemExit(main())
