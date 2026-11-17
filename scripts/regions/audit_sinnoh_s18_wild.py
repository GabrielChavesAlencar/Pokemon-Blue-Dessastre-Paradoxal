#!/usr/bin/env python3
"""S18 fail-closed proof: symbolic Sinnoh areas vs real shared wild evolution rules.

Static source and catalog audit only. The Ruby CI fixture runs actual
WildEncounters on synthetic Pokemon; no Sinnoh PBS/map/audio is installed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/regions/sinnoh-wild-s18.json"
ENCOUNTERS = ROOT / "data/regions/sinnoh-symbolic-encounters.json"
CH12 = ROOT / "data/regions/sinnoh-trainer-evolution-contract.json"
RUBY = ROOT / "tests/sinnoh_s18_wild_runtime.rb"
EVOLUTION = ROOT / "scripts/battle_polish/EvolutionScaling.rb"

SOURCES = {
    "runtime": "scripts/battle_polish/EvolutionScaling.rb",
    "progress": "scripts/battle_polish/Campaign.rb",
    "area_catalog": "data/regions/sinnoh-symbolic-encounters.json",
    "evolution_contract": "data/regions/sinnoh-trainer-evolution-contract.json",
    "ruby_fixture": "tests/sinnoh_s18_wild_runtime.rb",
}
S18_PROGRESS = {
    "reference": "highest_non_egg_party_level",
    "max_level": "GameData::GrowthRate.max_level",
    "regional_numeric_level_cap": None,
    "source_of_evolutions": "GameData::Species#get_evolutions(true)",
    "level_evolution_grace": 5,
    "stone_level": 30,
    "trade_level": 40,
    "friendship_level": 45,
    "wild_chances_by_gap": [
        {"min_gap": 0, "max_gap": 4, "chance_percent": 15},
        {"min_gap": 5, "max_gap": 14, "chance_percent": 30},
        {"min_gap": 15, "max_gap": 24, "chance_percent": 45},
        {"min_gap": 25, "max_gap": None, "chance_percent": 60},
    ],
    "original_species_slot_retained": True,
    "preserve_native_encounter_metadata": True,
    "preserve_original_pbs_weights": True,
    "invalid_level_or_cap_keeps_original_slot": True,
    "no_ambiguous_evolution": True,
    "special_or_legendary_forms_excluded": True,
    "time_dependent_methods_respected": True,
}
REFERENCE = {
    "all_areas_unverified": True,
    "candidate_methods_not_native_assignments": True,
    "species_are_historical_references_not_spawns": True,
    "no_fixed_spawn_weights": True,
    "no_fixed_level_ranges": True,
    "no_invented_map_ids": True,
    "static_special_events_not_random_encounters": True,
    "no_guessed_time_species_mapping": True,
}
NATIVE = {
    "native_encounter_pbs_compiled": False,
    "native_map_ids_verified": False,
    "actual_area_rates_verified": False,
    "native_evolution_observed": False,
    "game_exe_tested": False,
    "joiplay_tested": False,
    "playable_verified": False,
    "can_install": False,
    "may_write_pbs": False,
}
RUNTIME_TOKENS = (
    "def self.progress_level",
    "party.reject(&:egg?).map(&:level).max || 1",
    "source.get_evolutions(true)",
    "return [species, base_level] unless active?",
    "base_level.between?(1, maximum) && cap.between?(1, maximum)",
    "base_level <= cap",
    "return 15 if gap < 5",
    "return 30 if gap < 15",
    "return 45 if gap < 25",
    "60\n",
    "def self.wild_option(",
    "def self.available_wild_species(",
    "module WildEncounters",
    "result.dup.tap { |row| row[0], row[1] = changed }",
)
RUBY_TOKENS = (
    "BlueEvolutionScaling.wild_option(",
    "BlueEvolutionScaling.available_wild_species(",
    "S18SyntheticNativeEncounters.prepend(BlueEvolutionScaling::WildEncounters)",
    "SINNOH_S18_NATIVE_WILD_ADAPTER_THRESHOLDS_SLOTS_NO_PBS_MUTATION_OFFLINE_OK",
)


def blocked(message: str) -> None:
    raise ValueError("SINNOH_S18_BLOCKED: " + message)


def audit(contract: object, encounters: object, ch12: object,
          evolution: str, fixture: str) -> dict:
    if not isinstance(contract, dict) or any(
        contract.get(k) != v for k, v in {
            "schema": 1, "region": "SINNOH", "stage": "S18",
            "status": "SHARED_WILD_SCALING_TESTED_OFFLINE_NATIVE_ENCOUNTERS_PENDING",
            "sources": SOURCES, "reference_areas": 21,
            "progress": S18_PROGRESS, "reference_only": REFERENCE,
            "gameplay": NATIVE,
        }.items()
    ):
        blocked("contrato S18 mudou politica, referencia ou aprovacao nativa")
    if not isinstance(encounters, dict) or (
        encounters.get("region") != "SINNOH"
        or encounters.get("status") != "PLANNED_REFERENCE_ONLY_NOT_INSTALLED"
        or encounters.get("may_write_pbs") is not False
        or encounters.get("may_install") is not False
        or encounters.get("gameplay_verified") is not False
        or encounters.get("encounter_weights_verified") is not False
        or encounters.get("can_allocate_map_ids") is not False
    ):
        blocked("CH13 falsamente registrado como encontros jogaveis")
    areas = encounters.get("areas")
    if not isinstance(areas, list) or len(areas) != 21:
        blocked("21 areas simbolicas CH13 ausentes")
    seen = set()
    special = 0
    for area in areas:
        if not isinstance(area, dict):
            blocked("area CH13 invalida")
        ident = area.get("reference_area")
        if not isinstance(ident, str) or not ident or ident in seen:
            blocked("area simbolica ausente ou repetida")
        seen.add(ident)
        if any([
            area.get("status") != "planned",
            area.get("installed") is not False,
            area.get("native_pbs_verified") is not False,
            area.get("time_assignment_verified") is not False,
            area.get("map_id") is not None,
            area.get("source_map_ids") != [],
            area.get("destination_map_ids") != [],
            area.get("encounter_slots") != [],
            area.get("weight_percentages") is not None,
            area.get("level_ranges") is not None,
            area.get("species_method_assignments") != [],
        ]):
            blocked("area CH13 ganhou MapID/slot/horario/taxa nativa falsos")
        if not isinstance(area.get("candidate_pbs_methods"), list) or not area[
            "candidate_pbs_methods"
        ]:
            blocked("metodo candidato ausente")
        if not isinstance(area.get("reference_species"), list) or not area[
            "reference_species"
        ]:
            blocked("especies de referencia ausentes")
        for evt in area.get("special_events", []):
            if (not isinstance(evt, dict) or evt.get("event_installed") is not False
                    or evt.get("kind") not in
                    ("STATIC_WEEKLY_EVENT", "STATIC_SCRIPTED_EVENT")):
                blocked("evento estatico promovido falsamente a spawn")
            special += 1
    ch13_prog = encounters.get("global_progress")
    if (not isinstance(ch13_prog, dict)
            or ch13_prog.get("reference_party") != "highest_non_egg_party_level"
            or ch13_prog.get("regional_numeric_level_cap") is not None
            or ch13_prog.get("wild_chances_by_gap") !=
                S18_PROGRESS["wild_chances_by_gap"]
            or ch13_prog.get("level_evolution_grace") != 5
            or ch13_prog.get("stone_level") != 30
            or ch13_prog.get("trade_level") != 40
            or ch13_prog.get("friendship_level") != 45
            or ch13_prog.get("original_species_slot_retained") is not True
            or ch13_prog.get("never_rewrite_native_pbs") is not True):
        blocked("CH13 contradiz chances/evolucao/progresso do Blue")
    if (not isinstance(ch12, dict) or ch12.get("region") != "SINNOH"
            or ch12.get("gameplay_verified") is not False
            or ch12.get("can_install") is not False
            or ch12.get("level_cap", {}).get("regional_numeric_cap_in_save") is not None
            or ch12.get("level_cap", {}).get("reference") != "highest_non_egg_party_level"):
        blocked("CH12 falsamente introduziu cap regional de insignias")
    if (not isinstance(evolution, str)
            or any(part not in evolution for part in RUNTIME_TOKENS)):
        blocked("runtime compartilhado nao tem selector/protecao S18")
    if not isinstance(fixture, str) or any(
        part not in fixture for part in RUBY_TOKENS
    ):
        blocked("fixture Ruby que exerce WildEncounters nao encontrada")
    return {
        "schema": 1, "region": "SINNOH", "stage": "S18",
        "status": "SHARED_WILD_POLICY_VERIFIED_OFFLINE_NATIVE_PENDING",
        "reference_areas": len(areas),
        "special_static_events_not_installed": special,
        "reference_only": True,
        "chance_tiers": [row["chance_percent"] for row in
                         S18_PROGRESS["wild_chances_by_gap"]],
        "preserves_original_encounter_slots": True,
        "python_and_ruby_ci_required": True,
        "native_map_ids_verified": False,
        "native_pbs_edited": False,
        "game_exe_or_joiplay_tested": False,
        "gameplay_approved": False,
    }


def main() -> int:
    paths = (CONTRACT, ENCOUNTERS, CH12, EVOLUTION, RUBY)
    try:
        for file in paths:
            if file.is_symlink() or not file.is_file():
                blocked("fonte ausente ou symlink: " + str(file))
        contract, encounter, ch12 = [
            json.loads(file.read_text("utf-8")) for file in paths[:3]
        ]
        out = audit(contract, encounter, ch12,
                    evolution=EVOLUTION.read_text("utf-8"),
                    fixture=RUBY.read_text("utf-8"))
    except (ValueError, OSError, UnicodeError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
