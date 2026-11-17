#!/usr/bin/env python3
"""G09: reconcile Sinnoh gyms/HMs/League/postgame without native gameplay claims.

Use existing S15/S16/S21/S23 validators for full source checks. G09 adds
cross-stage checks and a deterministic, read-only, metadata-only release
checklist. No binary game, save, PBS, coordinates or user PC is inspected.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_s15_gyms as s15
import audit_sinnoh_s16_hms as s16
import audit_sinnoh_s21_league as s21
import audit_sinnoh_s23_postgame as s23

DOCUMENTS={
    "badges":"data/regions/sinnoh-badges-hms-contract.json",
    "gyms":"data/regions/sinnoh-gyms-s15.json",
    "hms":"data/regions/sinnoh-hms-s16.json",
    "teams":"data/regions/sinnoh-trainer-teams-ch15.json",
    "registry":"site/public/data/regions.json",
    "league":"data/regions/sinnoh-league-s21.json",
    "postgame":"data/regions/sinnoh-postgame-s23.json",
    "story":"data/regions/sinnoh-story-ch14-contract.json",
    "coverage":"data/regions/sinnoh-coverage.json",
}
SOURCES={
    "campaign":"scripts/battle_polish/Campaign.rb",
    "regions":"scripts/battle_polish/Regions.rb",
    "field_policy":"scripts/battle_polish/RegionalPolicy.rb",
    "travel":"scripts/battle_polish/RegionTravel.rb",
    "gym_adapter":"scripts/regions/SinnohGymContracts.rb",
    "hm_adapter":"scripts/regions/SinnohHMContracts.rb",
    "league_adapter":"scripts/regions/SinnohLeagueContracts.rb",
    "story_adapter":"scripts/regions/SinnohStoryContracts.rb",
    "postgame_adapter":"scripts/regions/SinnohPostgameContracts.rb",
    "blue_story":"scripts/battle_polish/Story.rb",
    "walkthrough":"docs/SINNOH_DETONADO_PLATINUM_REFERENCIA_ORGANIZADA.md",
    "league_fixture":"tests/sinnoh_s21_league_runtime.rb",
    "postgame_fixture":"tests/sinnoh_s23_postgame_runtime.rb",
}
NARRATIVE_BADGES=("COAL","FOREST","RELIC","COBBLE","FEN","MINE","ICICLE","BEACON")
CH11_BADGES=("COAL","FOREST","COBBLE","RELIC","FEN","MINE","ICICLE","BEACON")
POSTGAME_IDS=(
    "P10_BATTLE_ZONE_ENTRY","P10_HEATRAN_QUEST","P10_CRESSELIA_EVENT",
    "P10_DARKRAI_CONDITIONAL_QUEST","P10_SHAYMIN_CONDITIONAL_QUEST",
    "P10_OFFICIAL_STRONGEST_TEAM_REMATCHES",
)
NATIVE_FALSE=("approved_for_install","gameplay_verified","can_install","game_exe_tested","joiplay_tested")


def blocked(reason: str):
    raise ValueError("SINNOH_G09_BLOCKED: "+reason)


def safe_read(path:Path,*,source=False):
    if path.is_symlink() or not path.is_file() or path.stat().st_size>2_000_000:
        blocked("manifesto ou fonte local publica ausente/insegura")
    try:
        txt=path.read_text(encoding="utf-8-sig")
        return txt if source else json.loads(txt)
    except (OSError,UnicodeError,ValueError):
        blocked("conteudo publico malformado")


def audit(doc:dict,src:dict)->dict:
    if (type(doc) is not dict or set(doc)!=set(DOCUMENTS)
            or type(src) is not dict or set(src)!=set(SOURCES)
            or any(type(o) is not dict for o in doc.values())
            or any(type(s) is not str for s in src.values())):
        blocked("conjunto de manifestos ou fontes invalido")
    # Reuse the existing non-installing audits, not a replacement rule engine.
    # All mutations in the inputs are checked by the actual S15/S16/S21/S23
    # contract validators plus the additional G09 reconciliation below.
    try:
        a15=s15.audit(doc["gyms"],doc["teams"],doc["badges"],
                      doc["registry"],src["campaign"],src["regions"],src["gym_adapter"])
        a16=s16.audit(doc["hms"],doc["badges"],doc["gyms"],doc["teams"],
                      doc["registry"],src["campaign"],src["regions"],
                      src["field_policy"],src["travel"],src["gym_adapter"],src["hm_adapter"])
        a21=s21.audit(doc["league"],doc["story"],doc["coverage"],doc["teams"],
                      doc["badges"],src["league_adapter"],src["story_adapter"],
                      src["walkthrough"],src["league_fixture"])
        a23=s23.audit(doc["postgame"],doc["coverage"],doc["teams"],doc["story"],
                      doc["registry"],src["postgame_adapter"],src["story_adapter"],
                      src["regions"],src["campaign"],src["blue_story"],
                      src["postgame_fixture"])
    except (ValueError,TypeError,KeyError,AttributeError,IndexError):
        blocked("auditoria existente S15/S16/S21/S23 rejeitou a progressao")

    if (a15.get("gyms")!=8 or a15.get("can_install") is not False
            or a16.get("hm_contracts")!=8 or a16.get("can_install") is not False
            or a21.get("checkpoints")!=8 or a21.get("native_hall_of_fame_verified") is not False
            or a23.get("optional_events")!=6 or a23.get("gameplay_approved") is not False):
        blocked("provas offline alteradas para estado jogavel")
    gyms=doc["gyms"]["gyms"]
    hms=doc["hms"]["hms"]
    badge_rules=doc["badges"]["rules"]
    league=doc["league"]["steps"]
    postgame=doc["postgame"]["events"]
    story=doc["story"]["steps"]
    if ([g.get("badge") for g in gyms]!=list(NARRATIVE_BADGES)
            or [h.get("badge") for h in hms]!=list(CH11_BADGES)
            or [r.get("badge") for r in badge_rules]!=list(CH11_BADGES)):
        blocked("ordem narrativa S15 e ordem HM CH11 foram confundidas")

    hm_by_badge={}
    for h, original in zip(hms,badge_rules):
        badge=h["badge"]
        if badge in hm_by_badge or h["action"]!=original["field_move"] or h["hm_item"]!=original["hm_item"]:
            blocked("HM diferente do contrato CH11 ou badge duplicada")
        hm_by_badge[badge]=h
    if set(hm_by_badge)!=set(NARRATIVE_BADGES):
        blocked("permissao HM faltante ou duplicada")
    gym_report=[]
    for index,g in enumerate(gyms):
        previous=list(NARRATIVE_BADGES[:index])
        hm=hm_by_badge[g["badge"]]
        if (g["order"]!=index+1 or g["prerequisite_badges"]!=previous
                or g["field_move"]!=hm["action"] or g["hm_item"]!=hm["hm_item"]
                or g["name"]!=hm["leader"]):
            blocked("ginasios/HMs associados pela posicao e nao pela insignia")
        for field in ("trainer_pbs_compiled","physical_map_installed",
                      "physical_event_installed","battle_victory_verified",
                      "badge_award_verified","game_exe_verified"):
            if g.get(field) is not False:
                blocked("badge/times nativos de ginasio nao comprovados")
        for field in ("handler_compiled","pickup_event_verified",
                      "local_receipt_verified","enabled"):
            if hm.get(field) is not False:
                blocked("HM sem comprovante local declarado liberado")
        gym_report.append({
            "order":index+1,"leader":g["name"],"city_reference":g["reference_city"],
            "badge":g["badge"],"prior_badges_required":previous,
            "field_move":hm["action"],"hm_item":hm["hm_item"],
            "native_gym_battle_verified":False,"native_badge_verified":False,
            "local_hm_pickup_verified":False,
            "region_scoped_HM_gate":"BADGE_PLUS_LOCAL_PICKUP",
            "status":"PLANNED_NOT_NATIVE_INSTALLED",
        })

    ids=[s["id"] for s in league]
    if ids!=list(s21.IDS) or [s["previous"] for s in league]!=list(s21.PREVIOUS):
        blocked("sequencia ou precedentes da Liga mudou")
    by_story={e["id"]:e for e in story}
    for entry in league:
        prior=by_story.get(entry["id"])
        if (prior is None or prior["prerequisite_event"]!=entry["previous"]
                or entry["id"] not in s21.IDS
                or prior.get("native_event_installed") is not False
                or prior.get("grants_badge") is not False):
            blocked("CH14 e S21 divergem na Liga e callbacks")
    if (league[0]["previous"]!="P08_SAFE_RETURN_FROM_DISTORTION_WORLD"
            or league[0]["requires_local_badges"]!=["BEACON"]
            or set(league[1]["requires_local_badges"])!=set(NARRATIVE_BADGES)
            or league[-2]["id"]!="P09_CYNTHIA_BATTLE"
            or league[-1]["id"]!="P09_HALL_OF_FAME"
            or league[-1]["outcome"]!="engine_hall_of_fame_confirmed"
            or league[-2]["outcome"]!="battle_won"
            or doc["story"].get("hall_of_fame_requires_separate_engine_confirmation") is not True):
        blocked("Hall of Fame foi unido a Cynthia ou badges/Distortion ignorados")
    league_report=[{
        "order":i+1,"checkpoint":step["id"],"previous":step["previous"],
        "required_local_badges":step["requires_local_badges"],
        "outcome":step["outcome"],"native_event_verified":False,
        "engine_hall_of_fame_confirmation_required":i==7,
        "status":"PLANNED_NOT_NATIVE_INSTALLED",
    } for i,step in enumerate(league)]

    if ([x["id"] for x in postgame]!=list(POSTGAME_IDS)
            or doc["postgame"].get("requires_separate_hall_of_fame") is not True
            or doc["postgame"].get("global_world_champion_requires_all_ten_leagues") is not True
            or doc["postgame"].get("global_strongest_requires_verified_native_roster") is not True
            or doc["postgame"].get("elite_champion_historical_rematch_count")!=5
            or doc["postgame"].get("gym_historical_rematch_count")!=0):
        blocked("pós-jogo liberado cedo ou rematches historicos adulterados")
    optional=[]
    for row in postgame:
        if (row.get("requires_completed_sinnoh_hall_of_fame") is not True
                or row.get("native_callback_installed") is not False
                or row.get("native_quest_verified") is not False
                or row.get("physical_map_id") is not None
                or row.get("reference_only") is not True):
            blocked("quest de pos-jogo sem HoF ou fonte nativa verificada")
        if (row["id"]=="P10_HEATRAN_QUEST")!=(row.get("requires_previous_event")=="P10_BATTLE_ZONE_ENTRY"):
            blocked("Heatran sem Battle Zone ou dependência indevida")
        if row["id"] in ("P10_DARKRAI_CONDITIONAL_QUEST","P10_SHAYMIN_CONDITIONAL_QUEST"):
            if row.get("requires_event_item_verification") is not True:
                blocked("quest condicional sem item de evento verificado")
        if row["id"]=="P10_OFFICIAL_STRONGEST_TEAM_REMATCHES":
            if (row.get("requires_all_ten_leagues") is not True
                    or row.get("requires_native_strongest_team") is not True):
                blocked("Full Power sem dez ligas ou PBS verificado")
        optional.append({
            "checkpoint":row["id"],"reference_area":row["reference_area"],
            "requires_sinnoh_hall_of_fame":True,
            "requires_previous_event":row["requires_previous_event"],
            "requires_verified_event_item":row["requires_event_item_verification"],
            "requires_all_ten_leagues":row["requires_all_ten_leagues"],
            "requires_verified_native_strongest_roster":row["requires_native_strongest_team"],
            "native_quest_installed":False,"status":"REFERENCE_ONLY",
        })

    # Safety claims are deliberately derived from public *unapproved* manifests.
    if (doc["registry"]["regions"]["SINNOH"].get("status")!="planned"
            or any(doc["gyms"].get(k) is not False for k in (
                "approved_for_install","battles_playable","native_qa_approved"))
            or any(doc["hms"].get(k) is not False for k in (
                "approved_for_install","can_grant_hm","native_qa_approved"))
            or any(doc["league"].get(k) is not False for k in (
                "native_league_installed","native_hall_of_fame_verified","can_install"))
            or any(doc["postgame"]["verification"].get(k) is not False for k in (
                "gameplay_certified","native_qa_approved","can_install"))):
        blocked("aprovação fisica fabricada")

    return {
        "schema":1,"region":"SINNOH","stage":"G09",
        "status":"CROSS_STAGE_PROGRESSION_AUDITED_OFFLINE_NATIVE_GATES_PENDING",
        "mode":"PUBLIC_MANIFESTS_AND_OFFLINE_FIXTURES_ONLY",
        "gym_progression":gym_report,
        "badge_vs_hm_order":{
            "narrative_gym_badge_order":list(NARRATIVE_BADGES),
            "registry_and_hm_catalog_badge_order":list(CH11_BADGES),
            "mapping_by_badge_not_array_position":True,
        },
        "league_progression":league_report,
        "postgame_gates":optional,
        "counts":{
            "gyms":8,"local_hm_pickup_gates":8,
            "league_checkpoints":8,"elite_four_members":4,
            "champion_battles":1,"separate_hall_of_fame_confirmations":1,
            "optional_postgame_gates":6,
            "historical_elite_cynthia_rematch_references":5,
            "native_gym_battles_verified":0,
            "native_hm_pickup_events_verified":0,
            "native_league_battles_verified":0,
            "native_postgame_quests_verified":0,
        },
        "safety":{
            "s20_distortion_before_volkner_required":True,
            "league_barry_requires_eight_local_badges":True,
            "cynthia_victory_is_not_hall_of_fame":True,
            "postgame_requires_separate_hall_of_fame":True,
            "cross_region_hm_transfer_allowed":False,
            "physical_game_exe_tested":False,
            "android_joiplay_tested":False,
            "ready_to_install":False,"gameplay_approved":False,
            "r07_complete":False,"r08_complete":False,"r09_complete":False,
        },
        "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
    }


def run(root:Path=ROOT)->dict:
    return audit(
        {k:safe_read(Path(root)/v) for k,v in DOCUMENTS.items()},
        {k:safe_read(Path(root)/v,source=True) for k,v in SOURCES.items()},
    )


def main(argv=None)->int:
    try:
        if argv not in (None,[]):
            blocked("G09 nao aceita arquivos privados como entrada")
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        return 0
    except (OSError,UnicodeError,ValueError,KeyError,TypeError,IndexError,AttributeError):
        print("SINNOH_G09_BLOCKED: contratos de progressao inconsistentes",
              file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main(sys.argv[1:]))
