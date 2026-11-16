#!/usr/bin/env python3
"""CH13: read-only Sinnoh encounter planning audit, never a PBS writer.

All species names are *reference candidates* in an existing reviewed document.
Terrain/encounter methods are candidate questions, NOT assignments or slots.
MapIDs, actual time windows, rates and encounter levels remain unknown until
an authorized source and compiled native PBS/map can be reviewed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/regions/sinnoh-symbolic-encounters.json"
REVIEW = ROOT / "data/regions/detonados-content-review.json"
COVERAGE = ROOT / "data/regions/sinnoh-coverage.json"
PBS = ROOT / "scripts/regions/pbs.py"
HABITAT = ROOT / "scripts/battle_polish/Habitat.rb"
EVOLUTION = ROOT / "scripts/battle_polish/EvolutionScaling.rb"

LAND = ("Land", "LandMorning", "LandDay", "LandNight")
CAVE = ("Cave", "CaveMorning", "CaveDay", "CaveNight")
COAST = ("Land", "Water", "OldRod", "GoodRod", "SuperRod")
WATER_CAVE = ("Cave", "Water", "OldRod", "GoodRod", "SuperRod")
# These are review tasks, not observed PBS data.
TERRAIN_AND_METHODS = (
    ("GRASS", LAND), ("GRASS", LAND), ("GRASS", LAND),
    ("CAVE", CAVE), ("GRASS", LAND), ("FOREST", LAND),
    ("GRASS", LAND), ("CAVE", CAVE), ("CAVE", CAVE),
    ("GRASS", LAND), ("GRASS", LAND), ("GRASS", LAND),
    ("GRASS", LAND), ("WETLAND", LAND), ("COAST", COAST),
    ("WETLAND", LAND), ("SNOW", LAND), ("SNOW", LAND),
    ("COAST", COAST), ("CAVE", WATER_CAVE), ("BUILDING", CAVE),
)
# Unambiguous entries in the pre-existing Sinnoh-coverage.json only.
AREA_SYMBOLS = (
    "ROUTE_201", "ROUTE_202", "ROUTE_203", "OREBURGH_MINE",
    "VALLEY_WINDWORKS", "ETERNA_FOREST", "ROUTE_206",
    "WAYWARD_CAVE", None, "ROUTE_208", "ROUTE_209",
    "ROUTE_210", "ROUTE_215", None, "ROUTE_213",
    "GREAT_MARSH", "ROUTE_216", "ROUTE_217", "ROUTE_222",
    "VICTORY_ROAD", None,
)
EVENT_KINDS = {
    "Valley Windworks": {"DRIFLOON": "STATIC_WEEKLY_EVENT"},
    "Old Chateau": {"ROTOM": "STATIC_SCRIPTED_EVENT"},
}
PROGRESS = {
    "reference": "BlueEvolutionScaling.progress_level",
    "reference_party": "highest_non_egg_party_level",
    "maximum": "GameData::GrowthRate.max_level",
    "regional_numeric_level_cap": None,
    "native_evolution_source": "GameData::Species#get_evolutions(true)",
    "level_evolution_grace": 5, "stone_level": 30,
    "trade_level": 40, "friendship_level": 45,
    "wild_chances_by_gap": [
        {"min_gap": 0, "max_gap": 4, "chance_percent": 15},
        {"min_gap": 5, "max_gap": 14, "chance_percent": 30},
        {"min_gap": 15, "max_gap": 24, "chance_percent": 45},
        {"min_gap": 25, "max_gap": None, "chance_percent": 60},
    ],
    "original_species_slot_retained": True,
    "never_rewrite_native_pbs": True,
}
RESTRICTIONS = {
    "time_method_species_attribution_verified": False,
    "candidate_methods_not_active": True,
    "no_fixed_spawn_weights": True,
    "special_events_not_normal_encounters": True,
    "no_guessed_maps_or_map_ids": True,
    "future_import_requires_native_pbs_and_map_audit": True,
}
AREA_KEYS = {
    "reference_area", "area_symbol", "symbol_resolution", "terrain",
    "candidate_pbs_methods", "time_windows_to_audit",
    "time_assignment_verified", "reference_species", "status",
    "species_method_assignments", "encounter_slots",
    "weight_percentages", "level_ranges", "map_id", "source_map_ids",
    "destination_map_ids", "native_pbs_verified", "installed",
    "special_events", "notes",
}
TOP_KEYS = {
    "schema", "region", "status", "reference_game", "source_of_truth",
    "coverage_source", "blue_method_source", "blue_habitat_source",
    "blue_evolution_source", "source_level", "may_write_pbs",
    "may_install", "can_allocate_map_ids", "gameplay_verified",
    "encounter_weights_verified", "global_progress", "restrictions",
    "areas", "notes",
}


def fail(message: str):
    raise ValueError("SINNOH_CH13_BLOQUEADO: " + message)


def read_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        fail("Arquivo ausente ou symlink: " + str(path))
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        fail("Documento JSON precisa ser objeto")
    return value


def read_text(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        fail("Código-fonte ausente ou symlink: " + str(path))
    return path.read_text(encoding="utf-8")


def check_runtime(catalog: dict, pbs: str, habitat: str,
                  evolution: str) -> None:
    # Validate against real Blue source rather than copying unsupported
    # encounter method names from a third-party game or inventing selectors.
    match = re.search(r"ENCOUNTER_TYPES\s*=\s*\{([^}]+)\}", pbs, re.S)
    if not match:
        fail("Métodos de encontros permitidos ausentes no PBS Blue")
    methods = set(re.findall(r'"([A-Za-z]+)"', match.group(1)))
    for area in catalog["areas"]:
        for method in area["candidate_pbs_methods"]:
            if method not in methods:
                fail("Método PBS desconhecido: " + str(method))
            if not re.search(r"\b" + re.escape(method) + r":", habitat):
                fail("Método ausente do Habitat Dex Blue: " + method)
    expected = (
        "TRAINER_GRACE = 5", "STONE_LEVEL = 30",
        "TRADE_LEVEL = 40", "FRIENDSHIP_LEVEL = 45",
        "def self.progress_level", "party.reject(&:egg?).map(&:level).max || 1",
        "GameData::GrowthRate.max_level",
        "source.get_evolutions(true)",
        "return 15 if gap < 5", "return 30 if gap < 15",
        "return 45 if gap < 25",
        "def self.wild_option", "def self.available_wild_species",
        "return [species, base_level] unless active?",
    )
    for token in expected:
        if token not in evolution:
            fail("BlueEvolutionScaling sem regra esperada: " + token)


def audit(catalog: dict, review: dict, coverage: dict, pbs: str,
          habitat: str, evolution: str) -> dict:
    if not isinstance(catalog, dict) or set(catalog) != TOP_KEYS:
        fail("Campos de catálogo ausentes ou não permitidos")
    meta = {
        "schema": 1, "region": "SINNOH",
        "status": "PLANNED_REFERENCE_ONLY_NOT_INSTALLED",
        "reference_game": "Platinum",
        "source_of_truth": "data/regions/detonados-content-review.json",
        "coverage_source": "data/regions/sinnoh-coverage.json",
        "blue_method_source": "scripts/regions/pbs.py",
        "blue_habitat_source": "scripts/battle_polish/Habitat.rb",
        "blue_evolution_source": "scripts/battle_polish/EvolutionScaling.rb",
        "source_level": "REFERENCE_NOT_NATIVE_VERIFIED",
        "may_write_pbs": False, "may_install": False,
        "can_allocate_map_ids": False, "gameplay_verified": False,
        "encounter_weights_verified": False,
    }
    if any(type(catalog.get(k)) is not type(v) or catalog[k] != v
           for k, v in meta.items()):
        fail("Status, fontes ou aprovação nativa de Sinnoh alterados")
    if catalog.get("global_progress") != PROGRESS:
        fail("Progressão/evolução Blue adulterada ou cap regional inventado")
    if catalog.get("restrictions") != RESTRICTIONS:
        fail("Proteções de horários, métodos ou instalação alteradas")
    if not isinstance(catalog.get("notes"), str) or len(catalog["notes"]) < 80:
        fail("Aviso de planejamento insuficiente")
    if (not isinstance(review, dict) or
            review.get("status") != "REFERENCE_ONLY_NEVER_AUTO_INSTALL" or
            not isinstance(review.get("regions"), dict) or
            not isinstance(review["regions"].get("SINNOH"), dict)):
        fail("Fonte de revisão Platinum ausente ou aprovada indevidamente")
    reference = review["regions"]["SINNOH"]
    if reference.get("game") != "Platinum":
        fail("Fonte de espécies não é Platinum")
    source_areas = reference.get("areas")
    if not isinstance(source_areas, list) or len(source_areas) != 21:
        fail("Fonte de referência não contém as 21 áreas revisadas")
    if (not isinstance(coverage, dict) or
            coverage.get("region") != "SINNOH" or
            coverage.get("status") != "PLANNED_AUDIT_CHECKLIST_ONLY" or
            not isinstance(coverage.get("phases"), list)):
        fail("Inventário de mapas Sinnoh não é a fonte planejada")
    physical = {}
    for phase in coverage["phases"]:
        for place in phase["areas"]:
            if place.get("symbol") in physical:
                fail("Símbolo duplicado no inventário Sinnoh")
            physical[place["symbol"]] = place
    entries = catalog.get("areas")
    if (not isinstance(entries, list) or len(entries) != len(source_areas)
            or len(TERRAIN_AND_METHODS) != len(entries)
            or len(AREA_SYMBOLS) != len(entries)):
        fail("Áreas de referência incompletas ou duplicadas")
    seen = set()
    unresolved = []
    species_count = 0
    for index, (row, source) in enumerate(zip(entries, source_areas)):
        if not isinstance(row, dict) or set(row) != AREA_KEYS:
            fail("Campos obrigatórios da área ausentes")
        area = source.get("area")
        if (not isinstance(area, str) or row["reference_area"] != area
                or area in seen):
            fail("Área inventada, fora de ordem ou duplicada")
        seen.add(area)
        if (row["status"] != "planned" or row["map_id"] is not None or
                row["source_map_ids"] != [] or row["destination_map_ids"] != [] or
                row["native_pbs_verified"] is not False or
                row["installed"] is not False):
            fail("Área não pode inventar MapID, importação ou instalação")
        symbol = AREA_SYMBOLS[index]
        if (row["area_symbol"] != symbol or
                row["symbol_resolution"] !=
                ("EXACT_COVERAGE_SYMBOL" if symbol is not None
                 else "UNRESOLVED_REFERENCE_AREA")):
            fail("Símbolo de mapa ambíguo, ausente ou inventado")
        if symbol:
            info = physical.get(symbol)
            if (not info or info.get("verified") is not False or
                    info.get("source_map_ids") != [] or
                    info.get("destination_map_ids") != []):
                fail("Símbolo sem respaldo de planejamento ou com MapID físico")
        else:
            unresolved.append(area)
        terrain, methods = TERRAIN_AND_METHODS[index]
        if (row["terrain"] != terrain or
                row["candidate_pbs_methods"] != list(methods)):
            fail("Terreno e método candidato PBS inconsistentes")
        if (row["time_windows_to_audit"] != ["morning", "day", "night"] or
                row["time_assignment_verified"] is not False or
                row["species_method_assignments"] != []):
            fail("Horário ou atribuição espécie/método inventada")
        if (row["encounter_slots"] != [] or
                row["weight_percentages"] is not None or
                row["level_ranges"] is not None):
            fail("Slots, taxas ou níveis fictícios não são permitidos")
        species = source.get("reference_species")
        if (not isinstance(species, list) or not species or
                row["reference_species"] != species or
                len(set(species)) != len(species) or
                any(not isinstance(pokemon, str) or
                    not re.fullmatch(r"[A-Z][A-Z0-9_]*", pokemon)
                    for pokemon in species)):
            fail("Espécies não conferem com revisão Platinum existente")
        species_count += len(species)
        expected_events = EVENT_KINDS.get(area, {})
        events = row["special_events"]
        if (not isinstance(events, list) or len(events) != len(expected_events)):
            fail("Eventos estáticos não podem virar slots selvagens")
        for event, (pokemon, kind) in zip(events, expected_events.items()):
            if (event != {"species": pokemon, "kind": kind,
                          "event_installed": False} or pokemon in species):
                fail("Encontro especial tratado como spawn comum")
        if (set(expected_events) != set(source.get("special_encounters", [])) or
                row["notes"] != source.get("note")):
            fail("Separação de eventos ou nota da fonte de revisão alterada")
    check_runtime(catalog, pbs, habitat, evolution)
    return {
        "schema": 1, "region": "SINNOH",
        "status": "PLANNED_REFERENCE_ONLY_NOT_INSTALLED",
        "areas": len(entries),
        "reference_species_mentions": species_count,
        "unique_reference_species": len({s for a in entries for s in a["reference_species"]}),
        "unresolved_area_symbols": unresolved,
        "static_events_not_in_wild_slots": 2,
        "method_and_time_assigned_to_species": False,
        "real_slots_verified": 0,
        "native_map_ids_assigned": 0,
        "can_install": False, "gameplay_verified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG)
    parser.add_argument("--review", type=Path, default=REVIEW)
    parser.add_argument("--coverage", type=Path, default=COVERAGE)
    parser.add_argument("--pbs", type=Path, default=PBS)
    parser.add_argument("--habitat", type=Path, default=HABITAT)
    parser.add_argument("--evolution", type=Path, default=EVOLUTION)
    args = parser.parse_args()
    try:
        output = audit(read_json(args.catalog), read_json(args.review),
                       read_json(args.coverage), read_text(args.pbs),
                       read_text(args.habitat), read_text(args.evolution))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
