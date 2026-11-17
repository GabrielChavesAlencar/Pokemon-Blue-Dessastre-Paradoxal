#!/usr/bin/env python3
"""S19 read-only contract audit: Galactic phases 5-7, no fake native events.

The Ruby regression executes synthetic callbacks and the real CH14 ledger.
This auditor only proves that the symbolic S19 contract follows the
previously audited CH14 source and CH01 coverage; it never edits a save/map.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/regions/sinnoh-galactic-s19.json"
STORY = ROOT / "data/regions/sinnoh-story-ch14-contract.json"
COVERAGE = ROOT / "data/regions/sinnoh-coverage.json"
RUBY = ROOT / "scripts/regions/SinnohGalacticContracts.rb"
STORY_RUBY = ROOT / "scripts/regions/SinnohStoryContracts.rb"
FIXTURE = ROOT / "tests/sinnoh_s19_galactic_runtime.rb"

IDS = (
    "P05_TEAM_GALACTIC_WINDWORKS",
    "P05_COMMANDER_MARS",
    "P05_COMMANDER_JUPITER",
    "P06_TEAM_GALACTIC_PASTORIA_ENCOUNTER",
    "P07_TEAM_GALACTIC_LAKE_EVENTS",
)
PHASES = (5, 5, 5, 6, 7)
OUTCOMES = ("scene_completed", "battle_won", "battle_won",
            "scene_completed", "scene_completed")
SOURCES = ("WINDWORKS_SCENE", "WINDWORKS_MARS_BATTLE",
           "ETERNA_JUPITER_BATTLE", "PASTORIA_GALACTIC_SCENE",
           "LAKES_GALACTIC_SCENE")
PROHIBITIONS = {
    "no_native_hook_installed": True,
    "no_map_ids_assigned": True,
    "no_event_rewards_or_badges": True,
    "no_teleport": True,
    "no_cross_region_writes": True,
    "no_skipping_checkpoints": True,
    "no_auto_mark_on_talk_or_approach": True,
    "no_false_battle_victory": True,
}
MUST_FALSE = (
    "native_runtime_verified", "game_exe_tested", "joiplay_tested",
    "can_install", "gameplay_verified",
)


def blocked(reason: str) -> None:
    raise ValueError("SINNOH_S19_BLOCKED: " + reason)


def audit(contract: dict, story: dict, coverage: dict,
          ruby: str, story_ruby: str, fixture: str) -> dict:
    if (not isinstance(contract, dict) or contract.get("schema") != 1
            or contract.get("region") != "SINNOH"
            or contract.get("stage") != "S19"
            or contract.get("status") != "GALACTIC_FIVE_CHECKPOINTS_CODE_GATES_ONLY"
            or contract.get("save_ledger") != "sinnoh_ch14"
            or contract.get("source_contract") !=
                "data/regions/sinnoh-story-ch14-contract.json"
            or contract.get("coverage") != "data/regions/sinnoh-coverage.json"
            or contract.get("ruby_adapter") !=
                "scripts/regions/SinnohGalacticContracts.rb"
            or contract.get("prohibitions") != PROHIBITIONS):
        blocked("identidade/guardas do contrato S19 alteradas")
    if any(contract.get(k) is not False for k in MUST_FALSE):
        blocked("aprovação de evento, Game.exe ou JoiPlay falsificada")
    if any(contract.get(k) != [] for k in
           ("already_verified_native_sources", "physical_map_ids",
            "spawned_trainers", "native_pbs_files")):
        blocked("MapIDs, fontes nativas ou times não instalados inventados")
    if (not isinstance(story, dict) or story.get("region") != "SINNOH"
            or story.get("status") != "PLANNED_NATIVE_HOOKS_NOT_INSTALLED"
            or story.get("save_key") != "sinnoh_ch14"
            or story.get("native_events_installed") is not False
            or story.get("can_install") is not False
            or story.get("gameplay_verified") is not False):
        blocked("contrato de história CH14 foi promovido a nativo sem prova")
    ch14 = story.get("steps")
    steps = contract.get("steps")
    if (not isinstance(steps, list) or len(steps) != len(IDS)
            or not isinstance(ch14, list) or len(ch14) != 22):
        blocked("cinco etapas Galactic e/ou 22 checkpoints CH14 ausentes")
    if not isinstance(coverage, dict) or coverage.get("region") != "SINNOH" or (
            coverage.get("status") != "PLANNED_AUDIT_CHECKLIST_ONLY"):
        blocked("cobertura de Sinnoh não é planejamento auditado")
    events = {}
    for group in coverage.get("phases", []):
        for entry in group.get("events", []):
            key = entry.get("key")
            if key in events or entry.get("verified") is not False:
                blocked("evento de referência duplicado ou declarado instalado")
            events[key] = group.get("phase")
    for i, (key, phase, outcome, source) in enumerate(
            zip(IDS, PHASES, OUTCOMES, SOURCES)):
        expected = {
            "id": key, "phase": phase,
            "previous": IDS[i - 1] if i else None,
            "outcome": outcome, "source_key": source,
            "requires_local_badges": ["FOREST"] if i == 2 else [],
            "reference_only": True, "map_id": None,
            "native_event_installed": False,
            "native_event_verified": False,
            "compiled_battle_verified": False,
            "reward_items": [], "reward_badges": [],
            "teleport_destination": None, "save_flag": "sinnoh_ch14",
        }
        if type(steps[i]) is not dict or steps[i] != expected:
            blocked("etapa S19 adulterada, recompensa/mapa falso: " + key)
        row = ch14[i]
        if (row.get("id") != key or row.get("phase") != phase
                or row.get("prerequisite_event") != expected["previous"]
                or row.get("requires_local_badges") !=
                    expected["requires_local_badges"]
                or row.get("native_event_installed") is not False
                or row.get("native_event_verified") is not False
                or row.get("checkpoint_only") is not True
                or row.get("source_event_key") != key
                or events.get(key) != phase):
            blocked("contrato CH14/cobertura diverge da sequência Galactic: " + key)
    if not isinstance(ruby, str) or any(token not in ruby for token in (
        "module BlueSinnohGalacticContracts",
        "VERIFIED_NATIVE_SOURCES = {}.freeze",
        "BlueSinnohStoryContracts.recorded(state)",
        "BlueSinnohStoryContracts.next_event(state)",
        '["FOREST"]',
        "BlueRegions.local_achievements(state, \"SINNOH\")",
        "BlueSinnohStoryContracts.record(state, event, confirmed: true)",
        "def self.record_from_native(state, event, outcome:, source:)",
        "record_with_sources(state, event, outcome, source, VERIFIED_NATIVE_SOURCES)",
    )):
        blocked("adaptador Ruby não contém guardas obrigatórias")
    found = re.search(r"EVENTS\s*=\s*\[([^\]]+)\]", ruby, re.S)
    if not found or re.findall(r'"([A-Z0-9_]+)"', found.group(1)) != list(IDS):
        blocked("Ruby possui sequência Galactic divergente")
    if (not isinstance(story_ruby, str) or
            'SAVE_KEY = "sinnoh_ch14"' not in story_ruby or
            "events == STEPS.first(events.length)" not in story_ruby or
            'BADGE_REQUIREMENTS' not in story_ruby or
            'confirmed.equal?(true)' not in story_ruby):
        blocked("CH14 save/ordem/prova de callbacks foi alterada")
    if (not isinstance(fixture, str) or
            "SINNOH_S19_GALACTIC_FIVE_PHASES_BADGE_ORDER_SAVE_ISOLATION_OFFLINE_OK"
            not in fixture or
            "galactic.record_from_native(state, event, outcome: kind, source: source)"
            not in fixture or
            "galactic.fixture_record(state, event, outcome: kind, source: source,"
            not in fixture):
        blocked("teste Ruby S19 incompleto ou sem fontes bloqueadas")
    return {
        "schema": 1, "region": "SINNOH", "stage": "S19",
        "status": "FIVE_GALACTIC_GATES_AUDITED_NATIVE_EVENTS_PENDING",
        "planned_steps": len(steps),
        "reference_phases": list(sorted(set(PHASES))),
        "physical_map_ids_verified": 0,
        "native_event_handlers_installed": 0,
        "native_battles_verified": 0,
        "separate_save_key_created": False,
        "auto_rewards_or_map_travel": False,
        "ruby_runtime_fixture_required": True,
        "game_exe_or_joiplay_tested": False,
        "gameplay_certified": False,
    }


def main() -> int:
    files = (CONTRACT, STORY, COVERAGE, RUBY, STORY_RUBY, FIXTURE)
    try:
        for file in files:
            if file.is_symlink() or not file.is_file():
                blocked("arquivo obrigatório ausente ou symlink: " + str(file))
        values = [json.loads(file.read_text("utf-8")) for file in files[:3]]
        result = audit(*values,
                       ruby=RUBY.read_text("utf-8"),
                       story_ruby=STORY_RUBY.read_text("utf-8"),
                       fixture=FIXTURE.read_text("utf-8"))
    except (ValueError, OSError, TypeError, KeyError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
