#!/usr/bin/env python3
"""G04.3: read-only Unova wild-level/evolution contract and synthetic simulator.

This is deliberately NOT an encounter editor or a Python port installed in-game.
The authoritative native behavior remains BlueEvolutionScaling in Essentials.
No real Unova encounter species, rates, slot weights, map IDs or levels are known.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

import audit_unova_g04_encounter_methods as g042

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "data/regions/unova-g04-wild-scaling-contract.json"
SOURCES = {
    "g04_methods": "data/regions/unova-g04-encounter-methods-contract.json",
    "g03_scaling": "data/regions/unova-g03-leader-scaling-contracts.json",
    "shared_evolution": "data/regions/sinnoh-trainer-evolution-contract.json",
    "native_evolution": "scripts/battle_polish/EvolutionScaling.rb",
    "registry": "site/public/data/regions.json",
    "tracker": "site/public/data/unova-github-progress.json",
}
LEVEL = ("Level", "LevelMale", "LevelFemale", "LevelDay", "LevelNight",
         "LevelMorning", "LevelAfternoon", "LevelEvening")
STONE = ("Item", "ItemMale", "ItemFemale", "ItemDay", "ItemNight")
TRADE = ("Trade", "TradeMale", "TradeFemale", "TradeDay", "TradeNight", "TradeItem")
FRIEND = ("Happiness", "HappinessMale", "HappinessFemale",
          "HappinessDay", "HappinessNight")
SPECIAL = ("Legendary", "Mythical", "UltraBeast", "Paradox", "Pending",
           "DessastreParadoxal", "Regional", "RegionalForm",
           "Convergent", "Mega", "Gigantamax")
METHODS = set(LEVEL + STONE + TRADE + FRIEND)
FIELDS = {"schema", "phase", "region", "campaign", "status", "sources",
          "source_evidence", "progress", "method_families", "thresholds",
          "chance_bands", "safety", "areas", "can_install",
          "native_encounters_verified", "game_exe_tested", "android_tested",
          "notes"}
AREA_FIELDS = {"area_key", "native_level_min", "native_level_max",
               "native_species", "native_encounter_rate", "native_slot_weights",
               "native_map_id", "native_pbs_verified", "scaling_installed"}
IDENT = re.compile(r"FIXTURE_[A-Z0-9_]+\Z")

def deny(reason: str) -> None:
    raise ValueError("UNOVA_G04_3_BLOCKED: " + reason)

def exact(value: Any, keys: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        deny(label + " field set mismatch")

def positive_integer(value: Any, label: str, upper: int) -> int:
    if type(value) is not int or not 1 <= value <= upper:
        deny(label + " must be integer within engine limit")
    return value

def check_runtime(source: str) -> None:
    signatures = (
        "module BlueEvolutionScaling", "TRAINER_GRACE = 5",
        "STONE_LEVEL = 30", "TRADE_LEVEL = 40", "FRIENDSHIP_LEVEL = 45",
        "def self.progress_level", "reject(&:egg?).map(&:level).max || 1",
        "def self.wild_chance(cap, threshold)", "return 15 if gap < 5",
        "return 30 if gap < 15", "return 45 if gap < 25",
        "def self.wild_option(species, base_level, cap, roll = nil)",
        "return [species, base_level] unless active?",
        "base_level <= cap", "3.times do",
        "choices = options(current, cap, :wild)",
        "return [] unless targets.length == 1",
        "evolved_level = [evolved_level, minimum].max",
        "break if evolved_level > cap", "result.dup.tap",
        "PokemonEncounters.prepend(WildEncounters)",
    )
    if not all(s in source for s in signatures) or not re.search(
        r"def self.wild_chance\(cap, threshold\)[\s\S]*?^\s*60\s*$",
        source, re.MULTILINE
    ):
        deny("native evolution algorithm drifted; re-audit before use")

def validate_catalog(data: dict, g04: dict, g03: dict, shared: dict,
                     native: str, registry: dict, tracker: dict) -> dict:
    exact(data, FIELDS, "G04.3 catalog")
    required = {"schema": 1, "phase": "G04.3", "region": "UNOVA",
                "campaign": "WHITE_BW",
                "status": "OFFLINE_ONLY_NO_NATIVE_WILD_LEVELS",
                "sources": SOURCES, "can_install": False,
                "native_encounters_verified": False,
                "game_exe_tested": False, "android_tested": False}
    for key, expected in required.items():
        if data.get(key) != expected or type(data[key]) is not type(expected):
            deny("catalog identity or native readiness drift: " + key)
    evidence = {"unova_encounters_pbs": None, "unova_native_species": None,
                "unova_native_level_ranges": None, "unova_source_map_ids": None,
                "unova_source_license_approval": None}
    progress = {
        "signal": "HIGHEST_NON_EGG_PARTY_LEVEL",
        "fallback_without_non_egg": 1,
        "native_max": "GameData::GrowthRate.max_level",
        "regional_badge_numeric_level_cap": None,
        "native_slot_level_is_authoritative": True,
        "do_not_scale_trainer_levels_as_wild": True,
    }
    families = {"level": list(LEVEL), "stone": list(STONE),
                "trade": list(TRADE), "friendship": list(FRIEND)}
    thresholds = {"level_plus_grace": 5, "stone_level": 30,
                  "trade_level": 40, "friendship_level": 45}
    chances = [{"min_gap": 0, "max_gap_exclusive": 5, "chance_percent": 15},
               {"min_gap": 5, "max_gap_exclusive": 15, "chance_percent": 30},
               {"min_gap": 15, "max_gap_exclusive": 25, "chance_percent": 45},
               {"min_gap": 25, "max_gap_exclusive": None, "chance_percent": 60}]
    safety = {
        "max_evolution_steps": 3,
        "branching_requires_single_unique_eligible_target": True,
        "gender_and_time_require_verified_context": True,
        "never_guess_unsupported_evolution_methods": True,
        "no_special_species_or_nonzero_forms": True,
        "only_synthetic_fixtures_without_native_source": True,
        "preserve_original_slot_weight": True,
        "preserve_original_encounter_rate": True,
        "do_not_modify_original_pbs_or_saves": True,
        "wild_chance_not_encounter_weight": True,
        "G04_4_owns_real_probability_validation": True,
    }
    for key, value in (("source_evidence", evidence),
                       ("progress", progress), ("method_families", families),
                       ("thresholds", thresholds), ("chance_bands", chances),
                       ("safety", safety)):
        if data.get(key) != value or type(data[key]) is not type(value):
            deny("policy mismatch: " + key)
    if (g04.get("phase") != "G04.2" or g04.get("region") != "UNOVA"
        or g04.get("native_encounters_verified") is not False
        or g04.get("can_install") is not False
        or not isinstance(g04.get("areas"), list)
        or len(g04["areas"]) != 74):
        deny("G04.2 is not the verified source of 74 planned references")
    if (g03.get("phase") != "G03.2"
        or g03.get("level_cap", {}).get("source_signal") != progress["signal"]
        or g03["level_cap"]["regional_numeric_cap_in_save"] is not None
        or g03.get("evolution", {}).get("method_thresholds") != {
            "LEVEL_PLUS_GRACE": 5, "STONE": 30, "TRADE": 40, "FRIENDSHIP": 45
        } or g03["evolution"].get("max_steps") != 3
        or shared.get("level_cap", {}).get("regional_numeric_cap_in_save") is not None
        or shared.get("evolution", {}).get("stone_level") != 30):
        deny("G03.2 or shared Sinnoh scaling rules changed")
    check_runtime(native)
    if registry.get("regions", {}).get("UNOVA", {}).get("status") != "planned":
        deny("false playable region state")
    if (tracker.get("status") != "PLANNED_NOT_NATIVE_PLAYABLE"
        or tracker.get("native_technical_bar", {}).get("completed") != 0
        or tracker.get("native_playable_bar", {}).get("completed") != 0):
        deny("native tracker cannot be promoted by fixture simulations")
    task = next((t for group in tracker.get("groups", [])
                 for t in group.get("tasks", []) if t.get("id") == "G04.3"), None)
    if not task or task.get("status") not in ("pending", "done"):
        deny("G04.3 tracker missing")
    if not isinstance(data["areas"], list) or len(data["areas"]) != 74:
        deny("exactly 74 U03-area evidence records required")
    keys = [a["area_key"] for a in g04["areas"]]
    if len(keys) != len(set(keys)):
        deny("duplicate G04.2 area key")
    for expected_key, area in zip(keys, data["areas"]):
        exact(area, AREA_FIELDS, "area evidence")
        if area["area_key"] != expected_key:
            deny("area key mismatch/order drift")
        if any(area[k] is not None for k in
               ("native_level_min", "native_level_max", "native_species",
                "native_encounter_rate", "native_slot_weights", "native_map_id")):
            deny("invented native Unova encounter or level")
        if area["native_pbs_verified"] is not False or area["scaling_installed"] is not False:
            deny("false native installation approval")
    if not isinstance(data["notes"], list) or len(data["notes"]) < 4 or not all(
        isinstance(note, str) and note for note in data["notes"]
    ):
        deny("missing planned-only warnings")
    return {"phase": "G04.3", "areas": 74, "native_slots": 0,
            "native_levels": 0, "native_probabilities": 0,
            "regional_badge_cap": None, "native_approved": False,
            "fixture_simulation_only": True}

def load_project(root: Path = ROOT) -> tuple[dict, dict, dict]:
    root = Path(root)
    # G04.2 independently validates PBS methods, all 74 symbolic areas and sources.
    wild, _, registry, _ = g042.load_project(root)
    data = g042.load_json(root / "data/regions/unova-g04-wild-scaling-contract.json")
    g03 = g042.load_json(root / data["sources"]["g03_scaling"])
    shared = g042.load_json(root / data["sources"]["shared_evolution"])
    native = g042.read_text(root / data["sources"]["native_evolution"])
    tracker = g042.load_json(root / data["sources"]["tracker"])
    report = validate_catalog(data, wild, g03, shared, native, registry, tracker)
    return data, wild, report

def progress_level(party: list[dict], maximum: int) -> int:
    positive_integer(maximum, "engine maximum", 1000)
    if not isinstance(party, list):
        deny("party fixture must be a list")
    levels = []
    for member in party:
        exact(member, {"level", "egg"}, "fixture party member")
        positive_integer(member["level"], "party member level", maximum)
        if type(member["egg"]) is not bool:
            deny("egg state must be explicit bool")
        if not member["egg"]:
            levels.append(member["level"])
    return max(levels, default=1)

def validate_graph(graph: dict) -> None:
    if not isinstance(graph, dict) or not graph or len(graph) > 50:
        deny("synthetic evolution graph required")
    for species, record in graph.items():
        if type(species) is not str or not IDENT.fullmatch(species):
            deny("only FIXTURE_* identities accepted")
        exact(record, {"special_flags", "form", "evolutions"}, "fixture species")
        if (not isinstance(record["special_flags"], list)
            or any(flag not in SPECIAL for flag in record["special_flags"])
            or len(record["special_flags"]) != len(set(record["special_flags"]))
            or type(record["form"]) is not int or record["form"] < 0
            or not isinstance(record["evolutions"], list)):
            deny("invalid fixture species flags or form")
        for edge in record["evolutions"]:
            exact(edge, {"target", "method", "parameter"}, "fixture evolution")
            if edge["target"] not in graph or edge["method"] not in METHODS:
                deny("unsupported/unresolved evolution edge")
            if edge["method"] in LEVEL:
                positive_integer(edge["parameter"], "level evolution threshold", 1000)
            elif edge["parameter"] is not None:
                deny("stone/trade/friendship fixture parameter must be null")

def condition_ok(method: str, gender: str | None, time_bucket: str | None) -> bool:
    if method.endswith("Male") and gender != "MALE":
        return False
    if method.endswith("Female") and gender != "FEMALE":
        return False
    for suffix, bucket in (("Morning", "MORNING"), ("Afternoon", "AFTERNOON"),
                           ("Evening", "EVENING"), ("Night", "NIGHT"),
                           ("Day", "DAY")):
        if method.endswith(suffix) and time_bucket != bucket:
            return False
    return True

def method_threshold(edge: dict) -> int:
    method = edge["method"]
    if method in LEVEL:
        return edge["parameter"] + 5
    if method in STONE:
        return 30
    if method in TRADE:
        return 40
    if method in FRIEND:
        return 45
    deny("unsupported evolution method")

def wild_chance(cap: int, threshold: int) -> int:
    if cap < threshold:
        return 0
    gap = cap - threshold
    if gap < 5:
        return 15
    if gap < 15:
        return 30
    if gap < 25:
        return 45
    return 60

def simulate_fixture(data: dict, wild: dict, *, area_key: str, method: str,
                     party: list[dict], engine_max_level: int,
                     slot: dict, graph: dict, rolls: list[int],
                     gender: str | None = None, time_bucket: str | None = None,
                     input_source: str = "SYNTHETIC_FIXTURE") -> dict:
    if input_source != "SYNTHETIC_FIXTURE":
        deny("real encounters cannot be simulated as verified Unova data")
    if gender not in (None, "MALE", "FEMALE") or time_bucket not in (
        None, "MORNING", "DAY", "AFTERNOON", "EVENING", "NIGHT"
    ):
        deny("invalid/assumed gender or time context")
    g042.area_record(wild, area_key)
    entry = g042.area_record(wild, area_key)
    if method not in entry["candidate_methods"]:
        deny("area/method not even a candidate audit question")
    exact(slot, {"species", "level", "weight_percent", "encounter_rate",
                 "source"}, "synthetic slot")
    if slot["source"] != "SYNTHETIC_FIXTURE":
        deny("native encounter slots lack provenance")
    positive_integer(engine_max_level, "engine maximum", 1000)
    positive_integer(slot["level"], "fixture wild level", engine_max_level)
    if (type(slot["weight_percent"]) is not int
        or not 0 <= slot["weight_percent"] <= 100
        or type(slot["encounter_rate"]) is not int
        or not 0 <= slot["encounter_rate"] <= 100):
        deny("fixture-only percentages out of range")
    if not isinstance(rolls, list) or len(rolls) > 3 or any(
        type(v) is not int or not 0 <= v < 100 for v in rolls
    ):
        deny("rolls must be explicit 0..99; no implicit random calls")
    validate_graph(graph)
    if slot["species"] not in graph:
        deny("fixture slot species missing in evolution graph")
    cap = progress_level(party, engine_max_level)
    current, level = slot["species"], slot["level"]
    trace = []
    if level <= cap:
        for step in range(data["safety"]["max_evolution_steps"]):
            source = graph[current]
            if source["special_flags"] or source["form"] != 0:
                break
            options = []
            for edge in source["evolutions"]:
                target = graph[edge["target"]]
                if target["special_flags"] or target["form"] != 0:
                    continue
                threshold = method_threshold(edge)
                if cap >= threshold and condition_ok(edge["method"], gender, time_bucket):
                    options.append((edge["target"], threshold))
            # Multiple methods reaching the same target are unambiguous.
            if len({target for target, _ in options}) != 1:
                break
            target = options[0][0]
            if target == current:
                break
            threshold = min(t for s, t in options if s == target)
            chance = wild_chance(cap, threshold)
            if len(rolls) <= step:
                deny("explicit deterministic roll missing for eligible step")
            success = rolls[step] < chance
            trace.append({"step": step + 1, "from": current, "to": target,
                          "threshold": threshold, "chance_percent": chance,
                          "roll": rolls[step], "passed": success})
            if not success:
                break
            level = max(level, threshold)
            if level > cap:
                break
            current = target
    return {"phase": "G04.3", "fixture_only": True, "area_question": area_key,
            "method_question": method, "source": "SYNTHETIC_FIXTURE",
            "progress_level": cap, "regional_badge_cap": None,
            "original_species": slot["species"], "resolved_species": current,
            "original_level": slot["level"], "resolved_level": level,
            "original_weight_percent": slot["weight_percent"],
            "preserved_weight_percent": slot["weight_percent"],
            "preserved_encounter_rate": slot["encounter_rate"],
            "native_species": None, "native_level_ranges": None,
            "native_encounter_rate": None, "native_slot_weights": None,
            "applied_to_native": False, "trace": trace}

def demo(data: dict, wild: dict) -> dict:
    graph = {
        "FIXTURE_RATTATA": {"special_flags": [], "form": 0, "evolutions": [
            {"target": "FIXTURE_RATICATE", "method": "Level", "parameter": 20}]},
        "FIXTURE_RATICATE": {"special_flags": [], "form": 0, "evolutions": []},
    }
    slot = {"species": "FIXTURE_RATTATA", "level": 12,
            "weight_percent": 20, "encounter_rate": 15,
            "source": "SYNTHETIC_FIXTURE"}
    return {"synthetic_early": simulate_fixture(data, wild,
                area_key="UNOVA_ROUTE_01", method="Land",
                party=[{"level": 20, "egg": False}], engine_max_level=100,
                slot=slot, graph=graph, rolls=[0]),
            "synthetic_late": simulate_fixture(data, wild,
                area_key="UNOVA_ROUTE_01", method="Land",
                party=[{"level": 30, "egg": False}], engine_max_level=100,
                slot=slot, graph=graph, rolls=[0]),
            "native_evidence": None, "game_exe_tested": False,
            "can_install": False}

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--simulate-demo", action="store_true")
    args = p.parse_args(argv)
    try:
        catalog, wild, report = load_project()
        print(json.dumps(report if args.check else demo(catalog, wild),
                         ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, TypeError, KeyError, OSError, UnicodeError,
            RecursionError, IndexError) as exc:
        print("UNOVA_G04_3_BLOCKED: " + str(exc))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
