#!/usr/bin/env python3
"""S21 fail-closed integrity audit of the eight League gates.

Static contracts + Ruby fixture are NOT evidence of actual native Elite
battles, Giratina/Sinnoh map imports or Hall of Fame execution.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/regions/sinnoh-league-s21.json"
STORY = ROOT / "data/regions/sinnoh-story-ch14-contract.json"
COVERAGE = ROOT / "data/regions/sinnoh-coverage.json"
TEAMS = ROOT / "data/regions/sinnoh-trainer-teams-ch15.json"
BADGES = ROOT / "data/regions/sinnoh-badges-hms-contract.json"
RUBY = ROOT / "scripts/regions/SinnohLeagueContracts.rb"
STORY_RUBY = ROOT / "scripts/regions/SinnohStoryContracts.rb"
WALKTHROUGH = ROOT / "docs/SINNOH_DETONADO_PLATINUM_REFERENCIA_ORGANIZADA.md"
FIXTURE = ROOT / "tests/sinnoh_s21_league_runtime.rb"

IDS = (
    "P09_VOLKNER_BEACON_BADGE", "SINNOH_LEAGUE_BARRY_GATE",
    "P09_AARON_BATTLE", "P09_BERTHA_BATTLE", "P09_FLINT_BATTLE",
    "P09_LUCIAN_BATTLE", "P09_CYNTHIA_BATTLE", "P09_HALL_OF_FAME",
)
PREVIOUS = ("P08_SAFE_RETURN_FROM_DISTORTION_WORLD", *IDS[:-1])
OUTCOMES = (
    "beacon_badge_confirmed", "battle_won", "battle_won", "battle_won",
    "battle_won", "battle_won", "battle_won",
    "engine_hall_of_fame_confirmed",
)
TEAM_REFS = (
    "SINNOH_VOLKNER", None, "SINNOH_AARON", "SINNOH_BERTHA",
    "SINNOH_FLINT", "SINNOH_LUCIAN", "SINNOH_CYNTHIA", None,
)
SOURCES = (
    "VOLKNER_BEACON", "BARRY_LEAGUE_GATE", "ELITE_AARON",
    "ELITE_BERTHA", "ELITE_FLINT", "ELITE_LUCIAN",
    "CHAMPION_CYNTHIA", "ENGINE_HALL_OF_FAME",
)
EIGHT = ("COAL", "FOREST", "COBBLE", "RELIC",
         "FEN", "MINE", "ICICLE", "BEACON")
RESTRICTIONS = {
    "requires_s20_completed_before_volkner": True,
    "beacon_badge_must_be_awarded_separately": True,
    "barry_gate_requires_all_eight_local_badges": True,
    "requires_confirmed_barry_and_elite_battle_wins": True,
    "preserves_authored_elite_champion_teams": True,
    "levels_follow_shared_dynamic_scaling_no_fixed_numbers": True,
    "requires_cynthia_victory_before_hall_of_fame": True,
    "hall_of_fame_requires_separate_engine_confirmation": True,
    "cynthia_victory_alone_never_completes_league": True,
    "no_autocomplete_of_past_battles": True,
    "no_auto_items_badges_maps_or_teleport": True,
    "no_cross_region_league_or_save_writes": True,
    "verified_native_sources_absent": True,
}
NATIVE_FLAGS = (
    "game_exe_executed", "joiplay_executed", "native_league_installed",
    "native_hall_of_fame_verified", "gameplay_verified", "can_install",
)
NATIVE_LISTS = (
    "verified_native_sources", "installed_map_ids",
    "installed_native_trainers", "compiled_native_pbs",
    "native_hall_of_fame_callbacks",
)
STATIC = {
    "schema": 1, "region": "SINNOH", "stage": "S21",
    "status": "EIGHT_LEAGUE_CHECKPOINTS_CODE_GATES_ONLY",
    "ch14_contract": "data/regions/sinnoh-story-ch14-contract.json",
    "ch14_save_key": "sinnoh_ch14",
    "reference_coverage": "data/regions/sinnoh-coverage.json",
    "team_catalog": "data/regions/sinnoh-trainer-teams-ch15.json",
    "badge_contract": "data/regions/sinnoh-badges-hms-contract.json",
    "ruby_adapter": "scripts/regions/SinnohLeagueContracts.rb",
    "previous_checkpoint": "P08_SAFE_RETURN_FROM_DISTORTION_WORLD",
    "next_after_s21": None,
    "restrictions": RESTRICTIONS,
}
ALLOWED_KEYS = set(STATIC) | set(NATIVE_FLAGS) | set(NATIVE_LISTS) | {"steps", "note"}


def blocked(message: str) -> None:
    raise ValueError("SINNOH_S21_BLOCKED: " + message)


def audit(contract: dict, story: dict, coverage: dict,
          teams: dict, badges: dict,
          ruby: str, story_ruby: str, walkthrough: str, fixture: str) -> dict:
    if not isinstance(contract, dict) or set(contract) != ALLOWED_KEYS:
        blocked("campos S21 ausentes ou inesperados")
    if any(contract.get(k) != v or type(contract.get(k)) is not type(v)
           for k, v in STATIC.items()):
        blocked("politica S21 de oito insignias/Hall of Fame adulterada")
    if any(contract.get(k) is not False for k in NATIVE_FLAGS):
        blocked("alegacao falsa de Game.exe/Hall nativo")
    if any(contract.get(k) != [] for k in NATIVE_LISTS):
        blocked("MapIDs, PBS, treinadores e handlers nativos inventados")
    if not isinstance(contract["note"], str) or len(contract["note"]) < 180:
        blocked("aviso de limites nativos insuficiente")
    if (not isinstance(story, dict) or story.get("region") != "SINNOH"
            or story.get("status") != "PLANNED_NATIVE_HOOKS_NOT_INSTALLED"
            or story.get("save_key") != "sinnoh_ch14"
            or story.get("hall_of_fame_requires_separate_engine_confirmation") is not True
            or story.get("native_hall_of_fame_verified") is not False
            or story.get("native_events_installed") is not False
            or story.get("gameplay_verified") is not False
            or story.get("can_install") is not False):
        blocked("CH14 falsamente promovido a Liga nativa")
    original = story.get("steps")
    steps = contract.get("steps")
    if (not isinstance(original, list) or len(original) != 22
            or not isinstance(steps, list) or len(steps) != len(IDS)):
        blocked("8 checkpoints S21 / 22 CH14 incompletos")
    if original[13].get("id") != PREVIOUS[0]:
        blocked("conclusao do Mundo Distorcido S20 divergente")
    if (not isinstance(coverage, dict) or coverage.get("region") != "SINNOH"
            or coverage.get("status") != "PLANNED_AUDIT_CHECKLIST_ONLY"):
        blocked("cobertura CH01 nao esta planned")
    found = {}
    for phase in coverage.get("phases", []):
        for entry in phase.get("events", []):
            key = entry.get("key")
            if key in found or entry.get("verified") is not False:
                blocked("evento de cobertura duplicado ou marcado jogavel")
            found[key] = phase.get("phase")
    if (not isinstance(teams, dict) or teams.get("region") != "SINNOH"
            or teams.get("status") != "HISTORICAL_REFERENCE_ONLY_NOT_INSTALLED"
            or any(teams.get(k) is not False for k in (
                "native_source_available_in_repository",
                "native_pbs_compilation_verified", "native_event_battle_bindings_verified",
                "gameplay_verified", "can_install", "may_write_pbs",
            ))):
        blocked("CH15 rosters historicos promovidos a PBS nativos")
    trainers = teams.get("trainers")
    if not isinstance(trainers, list) or len(trainers) != 13:
        blocked("catalogo de 13 treinadores historicos CH15 incompleto")
    trainer_index = {item.get("id"): item for item in trainers}
    if len(trainer_index) != 13:
        blocked("duplicatas no catalogo CH15")
    for ref in (x for x in TEAM_REFS if x is not None):
        row = trainer_index.get(ref)
        if (not isinstance(row, dict) or
                row.get("native_pbs", {}).get("compiled") is not False or
                row.get("native_pbs", {}).get("event_bound") is not False or
                row.get("native_pbs", {}).get("game_exe_verified") is not False or
                row.get("native_pbs", {}).get("team") is not None or
                row.get("first_battle", {}).get("verified_in_blue_pbs") is not False):
            blocked("treinador historico CH15 apresentado como instalado: " + ref)
    if (not isinstance(badges, dict) or badges.get("region") != "SINNOH"
            or badges.get("native_gym_events_verified") is not False
            or badges.get("approved_for_install") is not False
            or badges.get("native_map_ids_assigned") is not False):
        blocked("insignias CH11 falsamente aprovadas no Game.exe")
    badge_rows = badges.get("rules")
    if (not isinstance(badge_rows, list) or
            tuple(row.get("badge") for row in badge_rows) != EIGHT or
            any(row.get("verified_gym_event") is not False
                or row.get("verified_hm_pickup_event") is not False
                for row in badge_rows)):
        blocked("8 insignias locais diferentes ou eventos fabricados")
    for i, (key, prev, outcome, source, ref) in enumerate(zip(
            IDS, PREVIOUS, OUTCOMES, SOURCES, TEAM_REFS)):
        local_badges = ["BEACON"] if i == 0 else list(EIGHT) if i == 1 else []
        section = "S42" if i == 1 else None
        expected = {
            "id": key, "phase": 9, "previous": prev, "outcome": outcome,
            "reference_section": section, "source_key": source,
            "trainer_catalog_reference": ref, "requires_local_badges": local_badges,
            "reference_only": True, "physical_map_id": None,
            "native_handler_installed": False, "native_handler_verified": False,
            "native_trainer_pbs_compiled": False,
            "native_battle_result_verified": False,
            "native_engine_hall_of_fame_verified": False,
            "grants_badge": False, "grants_item": False, "grants_map": False,
            "teleport_destination": None,
        }
        if type(steps[i]) is not dict or steps[i] != expected:
            blocked("etapa da Liga adulterada ou nao instalada indevidamente: " + key)
        ch14 = original[i + 14]
        if (ch14.get("id") != key or ch14.get("phase") != 9
                or ch14.get("prerequisite_event") != prev
                or ch14.get("source_event_key") != (None if section else key)
                or ch14.get("reference_section") != section
                or ch14.get("requires_local_badges") != local_badges
                or ch14.get("native_event_installed") is not False
                or ch14.get("native_event_verified") is not False
                or ch14.get("checkpoint_only") is not True
                or ch14.get("proof_kind") != (
                    "ENGINE_HALL_OF_FAME_CONFIRMED" if i == 7
                    else "TRUSTED_NATIVE_EVENT_CONFIRMED")
                or ch14.get("grants_item") is not False
                or ch14.get("grants_badge") is not False
                or ch14.get("grants_map") is not False):
            blocked("contrato CH14 diverge do gate de Liga: " + key)
        if not section and found.get(key) != 9:
            blocked("checkpoint da fase 9 ausente na cobertura: " + key)
    if (not re.search(r"^### S42\s", walkthrough, re.M)
            or not re.search(r"^### S43\s", walkthrough, re.M)):
        blocked("referencias S42/S43 de Victory Road e Liga ausentes")
    ruby_tokens = (
        "module BlueSinnohLeagueContracts",
        "VERIFIED_NATIVE_SOURCES = {}.freeze",
        "START_AT = 14",
        "BlueSinnohStoryContracts.recorded(state)",
        "BlueSinnohStoryContracts.next_event(state)",
        "REQUIRED_BADGES = %w[",
        "return :missing_eight_badges",
        "BlueSinnohStoryContracts.record(state, event, confirmed: true)",
        "hall_of_fame_verified: true",
        "private_class_method :record_with_sources",
        "record_with_sources(state, event, outcome, source, VERIFIED_NATIVE_SOURCES)",
    )
    if not isinstance(ruby, str) or any(t not in ruby for t in ruby_tokens):
        blocked("Ruby nao preserva integridade das oito etapas e HoF separado")
    event_block = re.search(r"EVENTS\s*=\s*%w\[([^\]]+)\]", ruby, re.S)
    if not event_block or tuple(event_block.group(1).split()) != IDS:
        blocked("ordem de checkpoints Ruby divergente")
    if not isinstance(story_ruby, str) or any(t not in story_ruby for t in (
        'SAVE_KEY = "sinnoh_ch14"',
        "events == STEPS.first(events.length)",
        "hall_of_fame_verified.equal?(true)",
        'BlueRegions.complete_league(state, "SINNOH")',
        "confirmed.equal?(true)",
    )):
        blocked("CH14 guardas de save, Hall ou liga removidas")
    if not isinstance(fixture, str) or any(t not in fixture for t in (
        "SINNOH_S21_EIGHT_BADGES_ELITE_CYNTHIA_HOF_SEPARATE_OFFLINE_OK",
        "league.record_from_native(state, id, outcome: outcome, source: source)",
        "send(:record_with_sources,",
        "P09_HALL_OF_FAME",
        "post_cynthia_destination",
    )):
        blocked("runner Ruby S21 nao cobre bloqueio nativo/HoF independente")
    return {
        "schema": 1, "region": "SINNOH", "stage": "S21",
        "status": "LEAGUE_EIGHT_GATES_AUDITED_NATIVE_BATTLES_PENDING",
        "checkpoints": len(steps), "required_local_badges": len(EIGHT),
        "historical_teams": 13,
        "elite_and_champion_reference_teams": 5,
        "native_map_ids_verified": 0, "native_trainers_installed": 0,
        "native_hall_of_fame_verified": False,
        "uses_existing_ch14_save_and_league_ledgers": True,
        "python_and_ruby_regression_required": True,
        "game_exe_joiplay_tested": False,
        "gameplay_certified": False,
    }


def main() -> int:
    files = (CONTRACT, STORY, COVERAGE, TEAMS, BADGES,
             RUBY, STORY_RUBY, WALKTHROUGH, FIXTURE)
    try:
        for file in files:
            if file.is_symlink() or not file.is_file():
                blocked("arquivo ausente ou symlink: " + str(file))
        values = [json.loads(file.read_text("utf-8")) for file in files[:5]]
        report = audit(*values, *[p.read_text("utf-8") for p in files[5:]])
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
