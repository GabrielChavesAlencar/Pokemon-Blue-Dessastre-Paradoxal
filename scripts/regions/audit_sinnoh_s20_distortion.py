#!/usr/bin/env python3
"""S20 fail-closed audit: Cyrus, Spear Pillar, Distortion World and Giratina.

This validates only planning contracts and source code. No MapID, PBS, map,
story battle, native teleport, licensed asset or Game.exe execution is implied.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/regions/sinnoh-distortion-s20.json"
STORY = ROOT / "data/regions/sinnoh-story-ch14-contract.json"
COVERAGE = ROOT / "data/regions/sinnoh-coverage.json"
RUBY = ROOT / "scripts/regions/SinnohDistortionContracts.rb"
STORY_RUBY = ROOT / "scripts/regions/SinnohStoryContracts.rb"
WALKTHROUGH = ROOT / "docs/SINNOH_DETONADO_PLATINUM_REFERENCIA_ORGANIZADA.md"
FIXTURE = ROOT / "tests/sinnoh_s20_distortion_runtime.rb"

IDS = (
    "P08_CYRUS", "P08_COMMANDER_SATURN", "P08_COMMANDER_MARS",
    "P08_COMMANDER_JUPITER", "P08_DIALGA_PALKIA_STORY_SCENE",
    "P08_DISTORTION_WORLD_PUZZLES", "SINNOH_DISTORTION_CYRUS_FINAL",
    "P08_GIRATINA_ENCOUNTER", "P08_SAFE_RETURN_FROM_DISTORTION_WORLD",
)
PREVIOUS = ("P07_TEAM_GALACTIC_LAKE_EVENTS", *IDS[:-1])
OUTCOMES = ("battle_won", "battle_won", "battle_won", "battle_won",
            "scene_completed", "puzzles_solved", "battle_won",
            "encounter_resolved", "safe_return_confirmed")
SOURCE_KEYS = (
    "CYRUS_BATTLE", "SATURN_BATTLE", "MARS_BATTLE", "JUPITER_BATTLE",
    "SPEAR_PILLAR_SCENE", "DISTORTION_PUZZLES", "DISTORTION_CYRUS_FINAL",
    "GIRATINA_RESOLUTION", "DISTORTION_RETURN",
)
LOCATIONS = (
    "galactic_hq", "galactic_hq", "spear_pillar_reference",
    "spear_pillar_reference", "spear_pillar_reference",
    "distortion_world_reference", "distortion_world_reference",
    "distortion_world_reference", "return_reference",
)
RESTRICTIONS = {
    "requires_s19_before_s20": True,
    "requires_mine_and_icicle_before_first_cyrus": True,
    "requires_explicit_battle_victory_for_cyrus_and_commanders": True,
    "requires_distortion_puzzles_solved": True,
    "giratina_resolution_is_not_forced_capture": True,
    "requires_explicit_safe_return": True,
    "no_claim_of_installed_spear_pillar_or_distortion_world": True,
    "no_giratina_grant": True,
    "no_reward_bag_or_badge_write": True,
    "no_auto_teleport": True,
    "no_cross_region_save_write": True,
    "no_skipping_or_replaying": True,
    "all_native_sources_unknown": True,
}
UNVERIFIED_FLAGS = (
    "game_exe_executed", "joiplay_executed", "events_native_installed",
    "gameplay_verified", "can_install",
)
UNVERIFIED_LISTS = (
    "native_verified_source_registry", "installed_map_ids",
    "installed_native_pbs", "native_teleport_points",
)
EXPECTED_KEYS = {
    "schema", "region", "stage", "status", "ch14_contract",
    "ch14_save_key", "runtime", "source_coverage", "prerequisite_s19",
    "next_after_s20", "native_verified_source_registry",
    "installed_map_ids", "installed_native_pbs", "native_teleport_points",
    "restrictions", "steps", *UNVERIFIED_FLAGS, "note",
}


def blocked(message: str) -> None:
    raise ValueError("SINNOH_S20_BLOCKED: " + message)


def audit(contract: dict, story: dict, coverage: dict,
          ruby: str, story_ruby: str, walkthrough: str, fixture: str) -> dict:
    if not isinstance(contract, dict) or set(contract) != EXPECTED_KEYS:
        blocked("contrato S20 com campos desconhecidos/ausentes")
    fixed = {
        "schema": 1, "region": "SINNOH", "stage": "S20",
        "status": "NINE_DISTORTION_CHECKPOINTS_CODE_GATES_ONLY",
        "ch14_contract": "data/regions/sinnoh-story-ch14-contract.json",
        "ch14_save_key": "sinnoh_ch14",
        "runtime": "scripts/regions/SinnohDistortionContracts.rb",
        "source_coverage": "data/regions/sinnoh-coverage.json",
        "prerequisite_s19": "P07_TEAM_GALACTIC_LAKE_EVENTS",
        "next_after_s20": "P09_VOLKNER_BEACON_BADGE",
        "restrictions": RESTRICTIONS,
    }
    if any(type(contract.get(k)) is not type(v) or contract[k] != v
           for k, v in fixed.items()):
        blocked("protecao S20, ordem ou chave do save alterada")
    if any(contract.get(k) is not False for k in UNVERIFIED_FLAGS):
        blocked("prova nativa Game.exe/JoiPlay/callback falsamente aprovada")
    if any(contract.get(k) != [] for k in UNVERIFIED_LISTS):
        blocked("MapIDs, PBS, teleporte ou fontes nativas inventados")
    if not isinstance(contract["note"], str) or len(contract["note"]) < 150:
        blocked("limites de prova nativa ausentes")
    if (not isinstance(story, dict) or story.get("region") != "SINNOH"
            or story.get("status") != "PLANNED_NATIVE_HOOKS_NOT_INSTALLED"
            or story.get("save_key") != "sinnoh_ch14"
            or story.get("can_install") is not False
            or story.get("native_events_installed") is not False
            or story.get("gameplay_verified") is not False):
        blocked("CH14 falsamente marcado como jogavel")
    story_steps = story.get("steps")
    steps = contract.get("steps")
    if (not isinstance(steps, list) or len(steps) != len(IDS)
            or not isinstance(story_steps, list) or len(story_steps) != 22):
        blocked("sequencia S20 9 ou CH14 22 incompleta")
    if (not isinstance(coverage, dict)
            or coverage.get("region") != "SINNOH"
            or coverage.get("status") != "PLANNED_AUDIT_CHECKLIST_ONLY"):
        blocked("inventario de fases Sinnoh nao esta planned")
    source_events = {}
    for p in coverage.get("phases", []):
        for row in p.get("events", []):
            key = row.get("key")
            if key in source_events or row.get("verified") is not False:
                blocked("cobertura com callback verificado/fonte duplicada")
            source_events[key] = p.get("phase")
    for i, (key, prev, outcome, token, location) in enumerate(
        zip(IDS, PREVIOUS, OUTCOMES, SOURCE_KEYS, LOCATIONS)
    ):
        local_badges = ["MINE", "ICICLE"] if i == 0 else []
        section = "S39" if i == 6 else None
        expected = {
            "id": key, "phase": 8, "previous": prev, "outcome": outcome,
            "source_key": token, "reference_location": location,
            "requires_local_badges": local_badges,
            "reference_section": section, "reference_only": True,
            "native_map_id": None,
            "native_callback_installed": False,
            "native_callback_verified": False,
            "native_battle_verified": False,
            "native_puzzle_verified": False,
            "native_giratina_resolution_verified": False,
            "native_return_verified": False, "grants_badge": False,
            "grants_item": False, "grants_species": False,
            "teleport_destination": None,
        }
        if not isinstance(steps[i], dict) or steps[i] != expected:
            blocked("evento, resultado, mapa ou premio S20 forjado: " + key)
        original = story_steps[i + 5]
        if (original.get("id") != key or original.get("phase") != 8
                or original.get("prerequisite_event") != prev
                or original.get("requires_local_badges") != local_badges
                or original.get("reference_section") != section
                or original.get("source_event_key") !=
                    (None if section else key)
                or original.get("native_event_installed") is not False
                or original.get("native_event_verified") is not False
                or original.get("checkpoint_only") is not True):
            blocked("checkpoint S20 difere do CH14: " + key)
        if section:
            if not re.search(r"^### S39\s", walkthrough, re.M):
                blocked("S39 sem narrativa de Cyrus final")
        elif source_events.get(key) != 8:
            blocked("evento fase 8 nao encontrado na cobertura: " + key)
    if story_steps[4].get("id") != PREVIOUS[0] or (
        story_steps[14].get("id") != "P09_VOLKNER_BEACON_BADGE"
    ):
        blocked("limites de S19/S20/S21 quebrados")
    if not isinstance(ruby, str) or any(token not in ruby for token in (
        "module BlueSinnohDistortionContracts",
        "VERIFIED_NATIVE_SOURCES = {}.freeze",
        "REQUIRED_FIRST_BADGES = %w[MINE ICICLE].freeze",
        "BlueSinnohStoryContracts.recorded(state)",
        "BlueSinnohStoryContracts.next_event(state)",
        "BlueRegions.local_achievements(state, \"SINNOH\")",
        "BlueSinnohStoryContracts.record(state, event, confirmed: true)",
        "private_class_method :record_with_sources",
        "def self.record_from_native(state, event, outcome:, source:)",
        "sources[event] == source",
    )):
        blocked("guardas do adapter S20 nao estao no Ruby")
    found = re.search(r"EVENTS\s*=\s*%w\[([^\]]+)\]", ruby, re.S)
    if not found or tuple(found.group(1).split()) != IDS:
        blocked("sequencia de eventos S20 divergente no Ruby")
    if not isinstance(story_ruby, str) or any(t not in story_ruby for t in (
        'SAVE_KEY = "sinnoh_ch14"',
        "events == STEPS.first(events.length)",
        "confirmed.equal?(true)", "BADGE_REQUIREMENTS",
    )):
        blocked("guarda CH14 de save/ordem/insignias ausente")
    if not isinstance(fixture, str) or any(t not in fixture for t in (
        "SINNOH_S20_DISTORTION_PUZZLES_GIRATINA_SAFE_RETURN_OFFLINE_OK",
        "record_from_native(",
        "send(:record_with_sources,",
        "P08_SAFE_RETURN_FROM_DISTORTION_WORLD",
    )):
        blocked("runtime S20 sem teste de retorno ou fonte nativa bloqueada")
    return {
        "schema": 1, "region": "SINNOH", "stage": "S20",
        "status": "DISTORTION_NINE_GATES_AUDITED_NATIVE_PENDING",
        "checkpoint_count": len(steps),
        "phase": 8, "native_map_ids": 0, "native_callbacks": 0,
        "native_battles_verified": 0, "native_teleports_verified": 0,
        "native_giratina_encounter_verified": False,
        "uses_existing_sinnoh_ch14_ledger": True,
        "synthetic_ruby_test_required": True,
        "game_exe_and_joiplay_tested": False,
        "gameplay_certified": False,
    }


def main() -> int:
    files = (CONTRACT, STORY, COVERAGE, RUBY, STORY_RUBY, WALKTHROUGH, FIXTURE)
    try:
        for f in files:
            if f.is_symlink() or not f.is_file():
                blocked("arquivo ausente/symlink: " + str(f))
        c, s, area = (json.loads(p.read_text("utf-8")) for p in files[:3])
        report = audit(
            c, s, area, RUBY.read_text("utf-8"),
            STORY_RUBY.read_text("utf-8"),
            WALKTHROUGH.read_text("utf-8"),
            FIXTURE.read_text("utf-8"),
        )
    except (ValueError, OSError, TypeError, KeyError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
