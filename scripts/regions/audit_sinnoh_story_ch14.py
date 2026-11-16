#!/usr/bin/env python3
"""CH14 Sinnoh: validate ordered Galactic/League contract; read-only, fail-closed.

No native maps/PBS are installed. This checks documented symbolic references
against the pre-existing coverage + walkthrough. It does not certify a victory.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/regions/sinnoh-story-ch14-contract.json"
COVERAGE = ROOT / "data/regions/sinnoh-coverage.json"
WALKTHROUGH = ROOT / "docs/SINNOH_DETONADO_PLATINUM_REFERENCIA_ORGANIZADA.md"
RUNTIME = ROOT / "scripts/regions/SinnohStoryContracts.rb"
REGIONS = ROOT / "scripts/battle_polish/Regions.rb"
TRAVEL = ROOT / "scripts/battle_polish/RegionTravel.rb"
IDS = (
    "P05_TEAM_GALACTIC_WINDWORKS", "P05_COMMANDER_MARS",
    "P05_COMMANDER_JUPITER", "P06_TEAM_GALACTIC_PASTORIA_ENCOUNTER",
    "P07_TEAM_GALACTIC_LAKE_EVENTS", "P08_CYRUS",
    "P08_COMMANDER_SATURN", "P08_COMMANDER_MARS",
    "P08_COMMANDER_JUPITER", "P08_DIALGA_PALKIA_STORY_SCENE",
    "P08_DISTORTION_WORLD_PUZZLES", "SINNOH_DISTORTION_CYRUS_FINAL",
    "P08_GIRATINA_ENCOUNTER", "P08_SAFE_RETURN_FROM_DISTORTION_WORLD",
    "P09_VOLKNER_BEACON_BADGE", "SINNOH_LEAGUE_BARRY_GATE",
    "P09_AARON_BATTLE", "P09_BERTHA_BATTLE", "P09_FLINT_BATTLE",
    "P09_LUCIAN_BATTLE", "P09_CYNTHIA_BATTLE", "P09_HALL_OF_FAME",
)
PHASES = (5, 5, 5, 6, 7, *([8] * 9), *([9] * 8))
REFERENCE_SECTIONS = {11: "S39", 15: "S42"}
REQUIREMENTS = {
    2: ["FOREST"], 5: ["MINE", "ICICLE"], 14: ["BEACON"],
    15: ["COAL", "FOREST", "COBBLE", "RELIC",
         "FEN", "MINE", "ICICLE", "BEACON"],
}
TOP_KEYS = {
    "schema", "region", "status", "reference_game", "source",
    "story_reference", "regional_engine", "travel_engine",
    "runtime", "save_key", "version", "progress_semantics",
    "requires_explicit_confirmed_callback",
    "hall_of_fame_requires_separate_engine_confirmation",
    "no_auto_rewards_items_badges_or_maps", "can_install",
    "native_events_installed", "gameplay_verified",
    "native_hall_of_fame_verified", "destinations_post_cynthia",
    "physical_travel_requires_verified_source_map_and_arrival",
    "travel_without_verified_npc_context",
    "travel_does_not_use_league_as_install_proof", "steps", "notes",
}
STEP_KEYS = {
    "id", "phase", "source_event_key", "reference_section",
    "prerequisite_event", "requires_local_badges", "proof_kind",
    "checkpoint_only", "native_event_installed",
    "native_event_verified", "grants_item", "grants_badge", "grants_map",
}


def fail(reason: str) -> None:
    raise ValueError("SINNOH_CH14_BLOQUEADO: " + reason)


def read(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        fail("Fonte ausente ou symlink: " + str(path))
    return path.read_text(encoding="utf-8")


def audit(contract: dict, coverage: dict, walkthrough: str,
          runtime: str, regions: str, travel: str) -> dict:
    if not isinstance(contract, dict) or set(contract) != TOP_KEYS:
        fail("Campos de contrato ausentes ou desconhecidos")
    expected = {
        "schema": 1, "region": "SINNOH",
        "status": "PLANNED_NATIVE_HOOKS_NOT_INSTALLED",
        "reference_game": "Platinum",
        "source": "data/regions/sinnoh-coverage.json",
        "story_reference": "docs/SINNOH_DETONADO_PLATINUM_REFERENCIA_ORGANIZADA.md",
        "regional_engine": "scripts/battle_polish/Regions.rb",
        "travel_engine": "scripts/battle_polish/RegionTravel.rb",
        "runtime": "scripts/regions/SinnohStoryContracts.rb",
        "save_key": "sinnoh_ch14", "version": 1,
        "progress_semantics": "STRICT_ORDERED_PREFIX_WITHOUT_IMPLICIT_BATTLES",
        "requires_explicit_confirmed_callback": True,
        "hall_of_fame_requires_separate_engine_confirmation": True,
        "no_auto_rewards_items_badges_or_maps": True,
        "can_install": False, "native_events_installed": False,
        "gameplay_verified": False, "native_hall_of_fame_verified": False,
        "destinations_post_cynthia": ["HOENN", "UNOVA"],
        "physical_travel_requires_verified_source_map_and_arrival": True,
        "travel_without_verified_npc_context": False,
        "travel_does_not_use_league_as_install_proof": True,
    }
    if any(type(contract.get(k)) is not type(v) or contract[k] != v
           for k, v in expected.items()):
        fail("Identidade, instalação, provas ou política de viagem falsificadas")
    if not isinstance(contract.get("notes"), str) or len(contract["notes"]) < 120:
        fail("Aviso sobre provas nativas incompleto")
    if not isinstance(coverage, dict) or coverage.get("region") != "SINNOH" or (
        coverage.get("status") != "PLANNED_AUDIT_CHECKLIST_ONLY"
    ):
        fail("Cobertura Sinnoh não é planejamento seguro")
    source_events = {}
    for phase in coverage.get("phases", []):
        for row in phase.get("events", []):
            key = row.get("key")
            if key in source_events or row.get("verified") is not False:
                fail("Evento fonte duplicado ou declarado nativo")
            source_events[key] = phase["phase"]
    steps = contract.get("steps")
    if not isinstance(steps, list) or len(steps) != len(IDS):
        fail("Sequência Galactic, Cyrus, Liga e Cynthia incompleta")
    for i, (row, key, phase) in enumerate(zip(steps, IDS, PHASES)):
        if not isinstance(row, dict) or set(row) != STEP_KEYS:
            fail("Campos do checkpoint ausentes ou desconhecidos")
        section = REFERENCE_SECTIONS.get(i)
        required = REQUIREMENTS.get(i, [])
        exact = {
            "id": key, "phase": phase,
            "source_event_key": None if section else key,
            "reference_section": section,
            "prerequisite_event": IDS[i - 1] if i else None,
            "requires_local_badges": required,
            "proof_kind": ("ENGINE_HALL_OF_FAME_CONFIRMED" if i == len(IDS) - 1
                           else "TRUSTED_NATIVE_EVENT_CONFIRMED"),
            "checkpoint_only": True, "native_event_installed": False,
            "native_event_verified": False, "grants_item": False,
            "grants_badge": False, "grants_map": False,
        }
        if row != exact or type(row["phase"]) is not int:
            fail("Checkpoint fora de ordem, prémio fictício ou prova inexistente: " + key)
        if section:
            if not re.search(r"^### " + re.escape(section) + r"\s", walkthrough, re.M):
                fail("Referência narrativa indisponível: " + section)
        elif source_events.get(key) != phase:
            fail("Evento não existe na fase de cobertura: " + key)
    match = re.search(r"STEPS\s*=\s*%w\[([^\]]+)\]", runtime, re.S)
    if not match or tuple(match.group(1).split()) != IDS:
        fail("Runtime Ruby tem sequência diferente do contrato")
    required_ruby = (
        "SAVE_KEY = \"sinnoh_ch14\"",
        "HALL_OF_FAME = \"P09_HALL_OF_FAME\"",
        "return nil unless events.is_a?(Array)",
        "events == STEPS.first(events.length)",
        "state[\"leagues\"].include?(\"SINNOH\")",
        "def self.record(state, event, confirmed: false, hall_of_fame_verified: false)",
        "confirmed.equal?(true)", "hall_of_fame_verified.equal?(true)",
        "BlueRegions.complete_league(state, \"SINNOH\")",
        "def self.post_cynthia_destination(state, destination)",
        "BlueRegionTravel.destination(state, destination)",
        "BlueRegionTravel.source_valid?(state)",
        "BlueRegionTravel.available?(state)",
    )
    for snippet in required_ruby:
        if snippet not in runtime:
            fail("Guarda Ruby ausente: " + snippet)
    for name, badges in {
        "\"P05_COMMANDER_JUPITER\"": ["FOREST"],
        "\"P08_CYRUS\"": ["MINE", "ICICLE"],
        "BEACON_GATE": ["BEACON"],
        "ELITE_GATE": REQUIREMENTS[15],
    }.items():
        pattern = re.escape(name) + r"\s*=>\s*%w\[" + r"\s+".join(badges) + r"\]"
        if not re.search(pattern, runtime):
            fail("Proteção por insígnia Sinnoh não coincide: " + name)
    for snippet in (
        "def self.complete_league(state, region)",
        "return false if state[\"leagues\"].include?(region)",
        "def self.valid_sinnoh_badges?(state)",
    ):
        if snippet not in regions:
            fail("Ledger compartilhado de Liga/insígnias mudou: " + snippet)
    for snippet in (
        "def self.source_valid?(state)",
        "when \"HOENN\" then !!hoenn_installed?",
        "else false",
        "def self.destination(state, key)",
        "elsif key == \"HOENN\"",
    ):
        if snippet not in travel:
            fail("Bloqueio de origem/destino físico mudou: " + snippet)
    return {
        "schema": 1, "region": "SINNOH", "checkpoints": len(steps),
        "planned_native_hooks": len(steps), "native_hooks_installed": 0,
        "hall_of_fame_requires_engine_proof": True,
        "post_league_destinations": ["HOENN", "UNOVA"],
        "hoenn_unova_unconditionally_unlocked": False,
        "can_install": False, "gameplay_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name, default in (
        ("contract", CONTRACT), ("coverage", COVERAGE),
        ("walkthrough", WALKTHROUGH), ("runtime", RUNTIME),
        ("regions", REGIONS), ("travel", TRAVEL),
    ):
        parser.add_argument("--" + name, type=Path, default=default)
    options = parser.parse_args()
    try:
        result = audit(
            json.loads(read(options.contract)),
            json.loads(read(options.coverage)),
            read(options.walkthrough), read(options.runtime),
            read(options.regions), read(options.travel),
        )
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
