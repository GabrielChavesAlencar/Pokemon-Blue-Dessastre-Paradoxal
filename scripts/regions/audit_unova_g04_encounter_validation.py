#!/usr/bin/env python3
"""Unova G04.4: source-closed encounter integrity checks and synthetic table QA.

A complete percentage total is meaningful ONLY within a deterministic synthetic
area+method+time+season+campaign partition. No real Unova encounter is imported,
written, invented, or certified. G04.2 and G04.3 remain the source contracts.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import audit_unova_g04_encounter_methods as g042
import audit_unova_g04_wild_scaling as g043

ROOT = Path(__file__).resolve().parents[2]
FILE = ROOT / "data/regions/unova-g04-encounter-validation-contract.json"
SOURCES = {
    "g04_methods": "data/regions/unova-g04-encounter-methods-contract.json",
    "g04_scaling": "data/regions/unova-g04-wild-scaling-contract.json",
    "u03_areas": "data/regions/unova-u03-areas.json",
    "pbs_parser": "scripts/regions/pbs.py",
    "registry": "site/public/data/regions.json",
    "tracker": "site/public/data/unova-github-progress.json",
}
FIELDS = {"schema", "phase", "region", "campaign", "status", "sources",
          "native_evidence", "policy", "areas", "can_write_pbs",
          "can_allocate_map_ids", "can_install", "game_exe_tested",
          "android_tested", "native_encounters_verified", "notes"}
AREA_FIELDS = {"area_key", "u03_kind", "candidate_methods",
               "native_method_verified", "native_species", "native_slots",
               "native_encounter_rate", "native_weights", "native_levels",
               "native_map_id", "native_table_provenance",
               "native_pbs_verified", "installable"}
PARTITION_FIELDS = {"area_key", "method", "time_bucket", "season_bucket",
                    "campaign", "encounter_rate", "slots", "source"}
SLOT_FIELDS = {"species", "level_min", "level_max", "weight_percent",
               "source"}
PARTITION_KEYS = ("area_key", "method", "time_bucket", "season_bucket",
                  "campaign")
FIXTURE_SPECIES = re.compile(r"FIXTURE_[A-Z][A-Z0-9_]*\Z")
FLAGS = ("can_write_pbs", "can_allocate_map_ids", "can_install",
         "game_exe_tested", "android_tested", "native_encounters_verified")
UNKNOWN_EVIDENCE = {
    "encounters_pbs_path": None, "encounters_pbs_sha256": None,
    "native_table_provenance": None, "source_license_approval": None,
    "verified_source_mapids": None, "native_time_mapping": None,
    "native_season_mapping": None, "native_version_mapping": None,
    "native_level_ranges": None, "native_species": None,
    "native_weight_tables": None, "native_encounter_rates": None,
}
POLICY = {
    "partition_dimensions": list(PARTITION_KEYS),
    "weight_unit": "PERCENT_ONLY_FOR_SYNTHETIC_FIXTURES",
    "complete_fixture_weight_sum": 100,
    "incomplete_table_sum": None,
    "unknown_is_not_zero": True,
    "reject_duplicate_partition": True,
    "reject_duplicate_identical_slot": True,
    "same_species_different_levels_allowed": True,
    "unknown_native_method_not_no_encounters": True,
    "zero_native_rate_not_assumed": True,
    "native_source_authorization": False,
    "fixture_source": "SYNTHETIC_FIXTURE",
    "fixture_names_only": True,
    "no_native_probability_generation": True,
    "no_automatic_rate_normalization": True,
    "no_cross_time_season_method_sums": True,
    "encounter_rate_is_not_evolution_chance": True,
    "G04_3_evolution_chance_not_slot_weight": True,
    "scripted_events_never_synthetic_random_tables": True,
    "preserve_original_pbs_saves": True,
}

def deny(message: str) -> None:
    raise ValueError("UNOVA_G04_4_BLOCKED: " + message)

def exact(record: Any, keys: set[str], label: str) -> None:
    if not isinstance(record, dict) or set(record) != keys:
        deny(label + " has missing or unexpected fields")

def valid_percent(value: Any, field: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not 1 <= value <= 100:
        deny(field + " must be a synthetic 1..100 integer or null")
    return value

def valid_level(value: Any, maximum: int, label: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int or not 1 <= value <= maximum:
        deny(label + " must be a positive integer <= engine limit or null")
    return value

def validate_catalog(data: dict, g04: dict, g43: dict,
                     regions: dict, tracker: dict) -> dict:
    exact(data, FIELDS, "G04.4 contract")
    required = {
        "schema": 1, "phase": "G04.4", "region": "UNOVA",
        "campaign": "WHITE_BW", "status": "PLANNED_OFFLINE_ENCOUNTER_QA_ONLY",
        "sources": SOURCES, "native_evidence": UNKNOWN_EVIDENCE,
        "policy": POLICY,
    }
    for key, value in required.items():
        if data.get(key) != value or type(data[key]) is not type(value):
            deny("source identity, provenance or audit policy changed: " + key)
    if any(data.get(flag) is not False for flag in FLAGS):
        deny("native readiness, installs, or game execution cannot be claimed")
    if (regions.get("regions", {}).get("UNOVA", {}).get("status") != "planned"
        or tracker.get("status") != "PLANNED_NOT_NATIVE_PLAYABLE"
        or tracker.get("native_technical_bar", {}).get("completed") != 0
        or tracker.get("native_playable_bar", {}).get("completed") != 0):
        deny("region or technical/gameplay tracker falsely promoted")
    task = next((t for group in tracker.get("groups", [])
                 for t in group.get("tasks", [])
                 if t.get("id") == "G04.4"), None)
    if task is None or task.get("status") not in ("pending", "done"):
        deny("missing G04.4 GitHub tracker milestone")
    if (g04.get("phase") != "G04.2" or g43.get("phase") != "G04.3"
        or g04.get("native_encounters_verified") is not False
        or g43.get("native_encounters_verified") is not False
        or g04.get("source_evidence", {}).get("weight_evidence") is not None
        or g04.get("source_evidence", {}).get("encounter_rate_evidence") is not None
        or g43.get("source_evidence", {}).get("unova_encounters_pbs") is not None
        or g43.get("safety", {}).get("wild_chance_not_encounter_weight") is not True
        or g04.get("encounter_probability_policy", {}).get(
            "percentage_total_check") != "DEFER_UNTIL_G04_4_SOURCE_VERIFIED"):
        deny("G04.2/G04.3 source-closed encounter/evolution guard drift")
    method_rows = g04.get("method_registry", [])
    if (len(method_rows) != 20
        or len({m["pbs_method"] for m in method_rows}) != 20
        or len(g04.get("areas", [])) != 74
        or len(g43.get("areas", [])) != 74):
        deny("source contracts no longer cover 74 areas and 20 PBS methods")
    rows = data.get("areas")
    if not isinstance(rows, list) or len(rows) != 74:
        deny("exactly 74 unknown native area records required")
    methods_with_questions = 0
    for row, ref, evo in zip(rows, g04["areas"], g43["areas"]):
        exact(row, AREA_FIELDS, "G04.4 area")
        if (row["area_key"] != ref["area_key"]
            or row["area_key"] != evo["area_key"]
            or row["u03_kind"] != ref["u03_kind"]
            or row["candidate_methods"] != ref["candidate_methods"]):
            deny("U03 area order, identity or candidate methods drift")
        if ref["candidate_methods"]:
            methods_with_questions += 1
        for field in ("native_species", "native_encounter_rate",
                      "native_weights", "native_levels", "native_map_id",
                      "native_table_provenance"):
            if row[field] is not None:
                deny("fabricated source data in symbolic Unova area: " + field)
        if row["native_slots"] != [] or any(row[field] is not False for field in (
            "native_method_verified", "native_pbs_verified", "installable"
        )):
            deny("no native slots or method installations are authorized")
        if ref["encounter_slots"] != [] or ref["encounter_rate"] is not None:
            deny("G04.2 actual encounters must remain unknown")
    if methods_with_questions != 34:
        deny("expected 34 candidate-only areas, never verified assignments")
    if not isinstance(data.get("notes"), list) or len(data["notes"]) < 4 or any(
        not isinstance(s, str) or not s.strip() for s in data["notes"]
    ):
        deny("required warnings about native unknowns missing")
    return {
        "phase": "G04.4", "symbolic_areas": len(rows),
        "areas_with_candidate_method_questions": methods_with_questions,
        "areas_without_candidate_methods": len(rows)-methods_with_questions,
        "source_supported_pbs_methods": len(method_rows),
        "native_encounter_tables_verified": 0,
        "native_encounter_rates_verified": 0,
        "native_weight_partitions_verified": 0,
        "native_slots_verified": 0,
        "game_exe_tested": False, "can_install": False,
        "fixture_validation_available": True
    }

def load_project(root: Path = ROOT) -> tuple[dict, dict, dict, dict]:
    root = Path(root)
    wild, _, regions, _ = g042.load_project(root)
    scaling, _, _ = g043.load_project(root)
    data = g042.load_json(root / "data/regions/unova-g04-encounter-validation-contract.json")
    tracker = g042.load_json(root / data["sources"]["tracker"])
    report = validate_catalog(data, wild, scaling, regions, tracker)
    return data, wild, scaling, report

def evaluate_fixtures(data: dict, wild: dict, partitions: list[dict], *,
                      engine_max_level: int = 100,
                      input_source: str = "SYNTHETIC_FIXTURE") -> dict:
    """Validate sample encounter partitions without granting native provenance.

    Each partition is one fully-qualified area/method/time/season/White table.
    An unknown value remains null, and incomplete tables have NO verified sum.
    """
    if input_source != "SYNTHETIC_FIXTURE":
        deny("native encounter data cannot be accepted without verified source")
    if type(engine_max_level) is not int or not 1 <= engine_max_level <= 1000:
        deny("explicit synthetic engine_max_level required")
    if not isinstance(partitions, list) or len(partitions) > 200:
        deny("fixture partitions must be a bounded list")
    seen_groups: set[tuple[str, ...]] = set()
    results: list[dict] = []
    for group in partitions:
        exact(group, PARTITION_FIELDS, "synthetic table")
        if group["source"] != "SYNTHETIC_FIXTURE":
            deny("synthetic group cannot masquerade as native PBS")
        values = tuple(group[name] for name in PARTITION_KEYS)
        if any(type(v) is not str for v in values):
            deny("partition identifiers must be explicit strings")
        if values in seen_groups:
            deny("duplicate area/method/time/season/version table")
        seen_groups.add(values)
        # This is a candidate QUESTION, never a native method assignment.
        g042.plan_audit(wild, area_key=group["area_key"],
                        method=group["method"], time_bucket=group["time_bucket"],
                        season_bucket=group["season_bucket"],
                        version=group["campaign"])
        rate = group["encounter_rate"]
        if rate is not None and (type(rate) is not int or rate < 0 or rate > 10000):
            deny("synthetic encounter_rate must be nonnegative integer or null")
        # Encounter-rate units are deliberately left uninterpreted; only
        # slot WEIGHTS use an explicit percentage sum.
        slots = group["slots"]
        if not isinstance(slots, list) or len(slots) > 256:
            deny("fixture slots must be a bounded list")
        seen_slots: set[tuple] = set()
        unknown_fields = set()
        known_weight_sum = 0
        if not slots:
            unknown_fields.add("slots")
        if rate is None:
            unknown_fields.add("encounter_rate")
        for slot in slots:
            exact(slot, SLOT_FIELDS, "synthetic slot")
            if slot["source"] != "SYNTHETIC_FIXTURE":
                deny("synthetic slot cannot claim native source")
            species = slot["species"]
            if species is not None and (
                type(species) is not str or not FIXTURE_SPECIES.fullmatch(species)
            ):
                deny("real Pokémon species cannot be assigned without verified PBS")
            low = valid_level(slot["level_min"], engine_max_level, "level_min")
            high = valid_level(slot["level_max"], engine_max_level, "level_max")
            if low is not None and high is not None and low > high:
                deny("level_min cannot exceed level_max")
            weight = valid_percent(slot["weight_percent"], "weight_percent")
            identity = (species, low, high, weight)
            if identity in seen_slots:
                deny("exact duplicate slot within identical partition")
            seen_slots.add(identity)
            for key, value in (("species", species), ("level_min", low),
                               ("level_max", high), ("weight_percent", weight)):
                if value is None:
                    unknown_fields.add(key)
            if weight is not None:
                known_weight_sum += weight
                if known_weight_sum > 100:
                    deny("known slot weights exceed 100 in single partition")
        complete = not unknown_fields
        if complete and known_weight_sum != 100:
            deny("complete fixture partition weights must total 100")
        results.append({
            "partition": dict(zip(PARTITION_KEYS, values)),
            "status": "COMPLETE_SYNTHETIC_FIXTURE_NOT_NATIVE" if complete
                      else "INCOMPLETE_SYNTHETIC_FIXTURE_UNKNOWNS_PRESERVED",
            "slot_count": len(slots),
            "encounter_rate": rate,
            "weight_sum_percent": known_weight_sum if complete else None,
            "unknown_fields": sorted(unknown_fields),
            "duplicate_exact_slots": 0,
            "native_source_verified": False,
            "native_method_assignment_verified": False,
            "can_install": False,
        })
    return {
        "phase": "G04.4", "fixture_only": True,
        "partitions_checked": len(results),
        "complete_synthetic_partitions": sum(
            x["weight_sum_percent"] is not None for x in results
        ),
        "native_tables_checked": 0, "native_probabilities_confirmed": 0,
        "native_game_modified": False, "can_install": False,
        "partitions": results,
    }

def demo(data: dict, wild: dict) -> dict:
    def slot(name: str | None, weight: int | None, low: int | None = 2,
             high: int | None = 4) -> dict:
        return {"species": name, "weight_percent": weight,
                "level_min": low, "level_max": high, "source": "SYNTHETIC_FIXTURE"}
    def group(method: str, time: str, season: str, slots: list[dict],
              rate: int | None) -> dict:
        return {"area_key": "UNOVA_ROUTE_01", "method": method,
                "time_bucket": time, "season_bucket": season,
                "campaign": "WHITE_BW", "slots": slots, "encounter_rate": rate,
                "source": "SYNTHETIC_FIXTURE"}
    return evaluate_fixtures(data, wild, [
        group("Land", "DAY", "SPRING",
              [slot("FIXTURE_A", 80), slot("FIXTURE_B", 20)], 15),
        group("LandNight", "NIGHT", "WINTER",
              [slot(None, None, None, None)], None),
        group("Water", "ANY", "SUMMER",
              [slot("FIXTURE_FISH", 100, 5, 8)], 12),
    ])

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--check", action="store_true")
    actions.add_argument("--simulate-demo", action="store_true")
    args = parser.parse_args(argv)
    try:
        data, wild, _, report = load_project()
        print(json.dumps(report if args.check else demo(data, wild),
                         ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, TypeError, KeyError, IndexError,
            OSError, UnicodeError, RecursionError) as exc:
        print("UNOVA_G04_4_BLOCKED: " + str(exc))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
