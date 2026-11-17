#!/usr/bin/env python3
"""G05.2 Unova badges, additive regional crystals and special-Pokemon gates.

This tool audits the *existing* BlueRegions/BlueRegionTravel Ruby contracts.
All scenarios use explicitly marked synthetic fixtures. There is no adapter
for a native save, no game installation, no item/badge award or Pokemon move.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

import audit_unova_g05_regional_items as g051

ROOT = Path(__file__).resolve().parents[2]
FILE = ROOT / "data/regions/unova-g05-badges-specials-contract.json"
SOURCES = {
    "registry": "site/public/data/regions.json",
    "gym_contract": "data/regions/unova-g02-gym-story-contracts.json",
    "regional_items": "data/regions/unova-g05-regional-items-contract.json",
    "regions_runtime": "scripts/battle_polish/Regions.rb",
    "travel_runtime": "scripts/battle_polish/RegionTravel.rb",
    "field_runtime": "scripts/battle_polish/RegionalPolicy.rb",
    "tracker": "site/public/data/unova-github-progress.json",
}
BADGES = ("TRIO", "BASIC", "INSECT", "BOLT", "QUAKE", "JET", "FREEZE", "LEGEND")
SPECIAL = ("Legendary", "Mythical", "UltraBeast", "Paradox")
FIELDS = {
    "schema", "phase", "region", "campaign", "status", "sources",
    "badges", "native_evidence", "progress_policy", "special_policy",
    "simulation_policy", "native_game_modified", "native_badges_modified",
    "native_items_granted", "native_saves_modified", "game_exe_tested",
    "android_tested", "can_install", "notes"
}
BADGE_FIELDS = {
    "index", "badge", "gym_contract_id", "native_badge_index",
    "native_switch_id", "native_reward_item_id", "native_event_id",
    "gym_battle_verified", "installed", "source_status"
}
EVIDENCE = {
    "source_unova_badge_indices": None,
    "source_unova_gym_event_ids": None,
    "source_unova_badge_switch_ids": None,
    "source_unova_badge_reward_items": None,
    "source_unova_gym_map_ids": None,
    "source_unova_native_provenance_sha256": None,
    "source_unova_licensed_assets": None,
    "native_special_box_qa": None,
}
PROGRESS = {
    "regional_badge_source": "site/public/data/regions.json",
    "regional_contributions": "UNIQUE_MILESTONES_IN_EACH_NON_DECADES_CIRCUIT_REGION",
    "decades_contribution": "NATIVE_BADGE_COUNT_PARAMETER_NOT_REWRITTEN",
    "total_formula": "NATIVE_DECADES_COUNT_PLUS_DISTINCT_REGIONAL_MILESTONES",
    "reject_duplicate_regional_claims": True,
    "foreign_badges_never_unlock_local_specials": True,
    "hisui_not_counted_in_circuit_total": True,
    "native_badge_array_unmodified": True,
    "offline_badge_awards_never_real": True,
}
SPECIAL_POLICY = {
    "metadata_source": "species_data.flags_and_base_species_flags_for_nonzero_form",
    "special_flags": list(SPECIAL),
    "ignore_bst_and_name_heuristics": True,
    "unova_local_milestones_required": 8,
    "local_region_not_global_crystals": True,
    "hisui_uses_hisui_complete_not_badge_count": True,
    "move_specials_to_pc_only_after_verified_native_commit": True,
    "preview_reserves_one_slot_per_restricted_party_pokemon": True,
    "preview_requires_one_non_egg_non_fainted_survivor": True,
    "preview_rejects_insufficient_box_slots": True,
    "no_release_or_overwrite_of_pokemon": True,
    "no_cross_region_badge_or_special_permission": True,
}
SIMULATION = {
    "scope": "FIXTURE_ONLY_G05_2_NOT_NATIVE_SAVE",
    "pokemon_id_prefix": "FIXTURE_",
    "allow_preview_for_planned_region_not_native_travel": True,
    "no_native_badge_awards": True,
    "no_box_writes": True,
    "no_native_qa_claims": True,
    "no_installation_or_field_access": True,
    "reject_unknown_achievements_and_flags": True,
}
STATE_FIELDS = {
    "scope", "version", "current", "achievements", "native_decades_badge_count",
    "hisui_complete", "party", "free_box_slots"
}
POKEMON_FIELDS = {"id", "flags", "base_flags", "form", "egg", "fainted"}
IDENTITY = re.compile(r"FIXTURE_[A-Z][A-Z0-9_]*\Z")
NEUTRAL_FLAGS = frozenset({"FIXTURE_NON_SPECIAL", "FIXTURE_HIGH_BST"})
ALL_FLAGS = frozenset(SPECIAL) | NEUTRAL_FLAGS

def deny(reason: str) -> None:
    raise ValueError("UNOVA_G05_2_BLOCKED: " + reason)

def exact(value: Any, keys: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        deny(label + " keys must match the audited schema")

def read_source(root: Path, path: str) -> str:
    return g051.read_source(root, path)

def load_json(root: Path, path: str) -> dict:
    return g051.load_json(root, path)

def validate_runtime(regions_rb: str, travel_rb: str, field_rb: str) -> None:
    regions_signatures = (
        "def self.award(state, region, key)",
        'state["current"] == region',
        'info(region)["milestones"].include?(key)',
        "return false if list.include?(key)",
        "list << key",
        "def self.local_achievements(state, region, native_badges = [])",
        'info(region)["milestones"] & state["achievements"].fetch(region, [])',
        "def self.crystal_total(state, native_total)",
        'native_total + (circuit - ["DECADES"]).sum',
        "def self.allow_specials?(state, region, native_badges = [])",
        'return state["hisui_complete"] if region == "HISUI"',
        "local_achievements(state, region, native_badges).length >= 8",
        "def self.transfer_plan(state, destination, party, slots, native_badges = [], &classify)",
        "return [:no_usable_party, []] unless party.any?",
        "return [:box_full, []] if slots.length < deposit.length",
    )
    travel_signatures = (
        "SPECIAL_FLAGS = %w[Legendary Mythical UltraBeast Paradox].freeze",
        "def self.special?(pkmn)",
        "data = pkmn.species_data",
        "flags = data.flags",
        "flags = flags + GameData::Species.get(data.species).flags",
        "!(flags & SPECIAL_FLAGS).empty?",
        "def self.free_storage_slots(limit)",
        "def self.preview(state, key)",
        "BlueRegions.allow_specials?(state, key, $player.badges)",
        "BlueRegions.transfer_plan(state, key, $player.party,",
        "def self.restricted?(pkmn)",
        "return false unless pkmn && BlueRegions.active? && installed?",
    )
    field_signatures = (
        "module BlueRegionalPolicy",
        "def self.restricted?(pkmn)",
        "BlueRegionTravel.restricted?(pkmn)",
        "def self.auto_deposit",
        "return false unless slots.length == forbidden.length",
    )
    for source, required in ((regions_rb, regions_signatures),
                             (travel_rb, travel_signatures),
                             (field_rb, field_signatures)):
        if any(token not in source for token in required):
            deny("native Ruby contract drift; do not infer changed badges/special behavior")

def validate_catalog(data: dict, registry: dict, gym: dict, items: dict,
                     tracker: dict, regions_rb: str, travel_rb: str,
                     field_rb: str) -> dict:
    exact(data, FIELDS, "G05.2 catalog")
    expected = {
        "schema": 1, "phase": "G05.2", "region": "UNOVA",
        "campaign": "WHITE_BW",
        "status": "PLANNED_OFFLINE_BADGE_AND_SPECIALS_AUDIT_ONLY",
        "sources": SOURCES, "native_evidence": EVIDENCE,
        "progress_policy": PROGRESS, "special_policy": SPECIAL_POLICY,
        "simulation_policy": SIMULATION, "native_game_modified": False,
        "native_badges_modified": False, "native_items_granted": False,
        "native_saves_modified": False, "game_exe_tested": False,
        "android_tested": False, "can_install": False,
    }
    for key, value in expected.items():
        if data.get(key) != value or type(data[key]) is not type(value):
            deny("native evidence, progress rule, source or safety flag drift: " + key)
    reg = registry.get("regions", {})
    if (reg.get("UNOVA", {}).get("status") != "planned"
        or reg.get("UNOVA", {}).get("milestones") != list(BADGES)
        or registry.get("circuit", []).count("UNOVA") != 1
        or len(registry.get("circuit", [])) != len(set(registry["circuit"]))
        or registry["circuit"].count("DECADES") != 1
        or gym.get("phase") != "G02.2" or gym.get("region") != "UNOVA"
        or gym.get("game_exe_tested") is not False
        or gym.get("badge_items_granted") is not False
        or gym.get("can_install") is not False
        or items.get("phase") != "G05.1"
        or items.get("can_install") is not False
        or tracker.get("status") != "PLANNED_NOT_NATIVE_PLAYABLE"
        or tracker.get("native_technical_bar", {}).get("completed") != 0
        or tracker.get("native_playable_bar", {}).get("completed") != 0):
        deny("source registry, G02/G05.1 or planned safety state invalid")
    if not isinstance(data.get("badges"), list) or len(data["badges"]) != 8:
        deny("exactly eight symbolic badges are required")
    if len(gym.get("gyms", [])) != 8:
        deny("exactly eight G02.2 gym receipts required")
    for i, (record, source) in enumerate(zip(data["badges"], gym["gyms"]), 1):
        exact(record, BADGE_FIELDS, "G05.2 symbolic badge")
        if record != {
            "index": i, "badge": BADGES[i-1],
            "gym_contract_id": source["id"],
            "native_badge_index": None, "native_switch_id": None,
            "native_reward_item_id": None, "native_event_id": None,
            "gym_battle_verified": False, "installed": False,
            "source_status": "G02_SYMBOLIC_ONLY_NOT_NATIVE_GYM",
        } or source["badge"] != BADGES[i-1] or source["index"] != i or any(
            source.get(key) is not None for key in
            ("native_badge_item_id", "native_badge_switch_id")
        ):
            deny("badge order, G02 source or native identifier forged")
    task = next((t for group in tracker.get("groups", [])
                 for t in group.get("tasks", []) if t.get("id") == "G05.2"), None)
    if not task or task.get("status") not in ("pending", "done"):
        deny("G05.2 tracker milestone missing")
    validate_runtime(regions_rb, travel_rb, field_rb)
    if not isinstance(data.get("notes"), list) or len(data["notes"]) < 5 or any(
        not isinstance(x, str) or not x.strip() for x in data["notes"]
    ):
        deny("source and native-safety warnings missing")
    return {
        "phase": "G05.2", "unova_badges": 8,
        "special_flags": list(SPECIAL),
        "regional_circuit_count_excluding_decades": len(registry["circuit"])-1,
        "native_badges_granted": 0, "native_gym_events_verified": 0,
        "native_special_pc_qa_verified": 0, "simulation_only": True,
        "can_install": False, "game_exe_tested": False,
    }

def load_project(root: Path = ROOT) -> tuple[dict, dict, dict]:
    root = Path(root)
    data = load_json(root, "data/regions/unova-g05-badges-specials-contract.json")
    sources = data["sources"]
    registry = load_json(root, sources["registry"])
    gym = load_json(root, sources["gym_contract"])
    items = load_json(root, sources["regional_items"])
    tracker = load_json(root, sources["tracker"])
    report = validate_catalog(
        data, registry, gym, items, tracker,
        read_source(root, sources["regions_runtime"]),
        read_source(root, sources["travel_runtime"]),
        read_source(root, sources["field_runtime"]),
    )
    return data, registry, report

def validate_fixture(state: Any, registry: dict) -> dict:
    exact(state, STATE_FIELDS, "badge/special fixture")
    if state["scope"] != SIMULATION["scope"] or type(state["version"]) is not int or state["version"] != 1:
        deny("native/future save cannot be treated as synthetic v1 fixture")
    regions = registry["regions"]
    if type(state["current"]) is not str or state["current"] not in regions:
        deny("unknown active region")
    if type(state["native_decades_badge_count"]) is not int or not (
        0 <= state["native_decades_badge_count"] <= 100
    ):
        deny("synthetic native badge count must be a bounded nonnegative integer")
    if type(state["hisui_complete"]) is not bool:
        deny("Hisui completion proof must be explicit bool")
    achievements = state["achievements"]
    if not isinstance(achievements, dict) or len(achievements) > len(regions):
        deny("invalid per-region achievement ledger")
    for region, badges in achievements.items():
        if type(region) is not str or region not in regions or region == "DECADES":
            deny("native Decades/unknown achievements cannot be forged")
        allowed = regions[region].get("milestones", [])
        if not isinstance(badges, list) or len(badges) > len(allowed) or any(
            type(b) is not str or b not in allowed for b in badges
        ) or len(set(badges)) != len(badges):
            deny("duplicate or foreign badge in region ledger")
    party = state["party"]
    if not isinstance(party, list) or len(party) > 6:
        deny("synthetic party is limited to six Pokemon")
    ids: set[str] = set()
    for pkmn in party:
        exact(pkmn, POKEMON_FIELDS, "fixture Pokemon")
        identifier = pkmn["id"]
        if type(identifier) is not str or not IDENTITY.fullmatch(identifier) or identifier in ids:
            deny("real/duplicate Pokemon identity in synthetic party")
        ids.add(identifier)
        if type(pkmn["form"]) is not int or not 0 <= pkmn["form"] <= 99:
            deny("synthetic form index must be a nonnegative integer")
        for label in ("flags", "base_flags"):
            value = pkmn[label]
            if not isinstance(value, list) or len(value) != len(set(value)) or any(
                type(v) is not str or v not in ALL_FLAGS for v in value
            ):
                deny("special species metadata flags must be explicit")
        if type(pkmn["egg"]) is not bool or type(pkmn["fainted"]) is not bool:
            deny("Pokemon usability flags must be explicit bool")
    slots = state["free_box_slots"]
    if not isinstance(slots, list) or len(slots) > 180 or any(
        type(v) is not str or not IDENTITY.fullmatch(v) for v in slots
    ) or len(slots) != len(set(slots)):
        deny("verified distinct synthetic empty box slots required")
    return state

def local_badges(state: dict, registry: dict, region: str) -> list[str]:
    validate_fixture(state, registry)
    if type(region) is not str or region not in registry["regions"]:
        deny("unknown regional achievement lookup")
    if region == "DECADES":
        deny("native Decades badges require separate verified game metadata")
    allowed = registry["regions"][region].get("milestones", [])
    entries = state["achievements"].get(region, [])
    return [key for key in allowed if key in entries]

def crystal_total(state: dict, registry: dict) -> int:
    validate_fixture(state, registry)
    return state["native_decades_badge_count"] + sum(
        len(local_badges(state, registry, region))
        for region in registry["circuit"] if region != "DECADES"
    )

def award_fixture(state: dict, registry: dict, *, region: str, badge: str) -> dict:
    validate_fixture(state, registry)
    if type(region) is not str or region not in registry["circuit"] or region == "DECADES":
        deny("invalid synthetic regional badge source")
    if region != state["current"]:
        deny("foreign-region badge cannot be awarded")
    allowed = registry["regions"][region].get("milestones", [])
    if type(badge) is not str or badge not in allowed:
        deny("not an authored badge of active region")
    before = crystal_total(state, registry)
    out = copy.deepcopy(state)
    list_for_region = out["achievements"].setdefault(region, [])
    if badge in list_for_region:
        result = "ALREADY_RECORDED_SYNTHETIC_NO_OP"
    else:
        list_for_region.append(badge)
        result = "SIMULATED_CLAIM_NO_NATIVE_AWARD"
    after = crystal_total(out, registry)
    if before == after and result == "SIMULATED_CLAIM_NO_NATIVE_AWARD":
        deny("duplicate badge or regression in additive crystals")
    return {"phase": "G05.2", "status": result, "fixture": out,
            "before_crystals": before, "after_crystals": after,
            "native_badges_modified": False,
            "native_saves_modified": False, "can_install": False}

def allow_specials(state: dict, registry: dict, region: str) -> bool:
    validate_fixture(state, registry)
    if type(region) is not str or region not in registry["regions"]:
        deny("unknown special destination")
    if region == "HISUI":
        return state["hisui_complete"]
    if region == "DECADES":
        # Decades' own verified native badge data is not supplied to fixtures.
        deny("Decades special unlock needs verified native badge array")
    return len(local_badges(state, registry, region)) >= 8

def special_pokemon(pkmn: dict) -> bool:
    # The actual Ruby module reads species_data.flags and, for forms != 0,
    # the base species' flags. It does NOT infer Legendary from high BST.
    flags = list(pkmn["flags"])
    if pkmn["form"] != 0:
        flags += pkmn["base_flags"]
    return bool(set(flags).intersection(SPECIAL))

def preview_transfer(data: dict, state: dict, registry: dict, destination: str) -> dict:
    validate_fixture(state, registry)
    if type(destination) is not str or destination not in registry["regions"]:
        deny("invalid destination")
    if destination == state["current"]:
        deny("same-region non-travel cannot reclassify party")
    if destination == "DECADES":
        deny("native Decades badge rules are not available offline")
    can_use_specials = allow_specials(state, registry, destination)
    restricted = [] if can_use_specials else [
        p for p in state["party"] if special_pokemon(p)
    ]
    eligible = [p for p in state["party"] if p not in restricted
                and not p["egg"] and not p["fainted"]]
    if not eligible:
        status = "NO_USABLE_PARTY_BLOCKED"
    elif len(restricted) > len(state["free_box_slots"]):
        status = "INSUFFICIENT_BOX_SLOTS_BLOCKED"
    else:
        status = "SYNTHETIC_PREVIEW_ONLY_NEVER_NATIVE_TRAVEL"
    if status != "SYNTHETIC_PREVIEW_ONLY_NEVER_NATIVE_TRAVEL":
        reserves: list[dict] = []
    else:
        reserves = [
            {"pokemon_id": p["id"], "slot": state["free_box_slots"][i]}
            for i, p in enumerate(restricted)
        ]
    return {
        "phase": "G05.2", "source": state["current"],
        "destination": destination, "status": status,
        "local_badge_count": None if destination == "HISUI"
            else len(local_badges(state, registry, destination)),
        "global_crystals": crystal_total(state, registry),
        "specials_unlocked": can_use_specials,
        "restricted_party_ids": [p["id"] for p in restricted],
        "usable_party_after_preview": [p["id"] for p in eligible],
        "reservations": reserves,
        "native_party_modified": False, "native_boxes_modified": False,
        "native_badges_modified": False, "game_exe_tested": False,
        "can_install": False,
    }

def demo(data: dict, registry: dict) -> dict:
    def pkmn(key: str, flags: list[str]) -> dict:
        return {"id": "FIXTURE_"+key, "flags": flags, "base_flags": [],
                "form": 0, "egg": False, "fainted": False}
    all_unova = list(BADGES)
    st = {
        "scope": SIMULATION["scope"], "version": 1, "current": "KANTO",
        "achievements": {
            "KANTO": registry["regions"]["KANTO"]["milestones"][:3],
            "UNOVA": all_unova[:7],
        },
        "native_decades_badge_count": 4, "hisui_complete": False,
        "party": [
            pkmn("COMMON", ["FIXTURE_NON_SPECIAL"]),
            pkmn("LEGEND", ["Legendary"]),
            pkmn("PARADOX", ["Paradox"]),
        ],
        "free_box_slots": ["FIXTURE_BOX_A", "FIXTURE_BOX_B"],
    }
    blocked = preview_transfer(data, st, registry, "UNOVA")
    local_unova = copy.deepcopy(st)
    local_unova["current"] = "UNOVA"
    awarded = award_fixture(local_unova, registry, region="UNOVA", badge=BADGES[7])
    cleared = preview_transfer(data, awarded["fixture"], registry, "KANTO")
    # The destination Kanto still has fewer than eight badges; its two
    # specials remain restricted although Unova has all eight.
    return {
        "phase": "G05.2", "native_save_modified": False,
        "can_install": False, "fixture_only": True,
        "before": {"crystals": crystal_total(st, registry),
                   "unova_badges": 7,
                   "restricted_when_entering_unova": blocked["restricted_party_ids"]},
        "after": {"crystals": awarded["after_crystals"], "unova_badges": 8,
                  "specials_unlocked_in_unova": allow_specials(awarded["fixture"], registry, "UNOVA"),
                  "restricted_when_entering_kanto": cleared["restricted_party_ids"]},
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group(required=True)
    options.add_argument("--check", action="store_true")
    options.add_argument("--simulate-demo", action="store_true")
    args = parser.parse_args(argv)
    try:
        data, registry, report = load_project()
        print(json.dumps(report if args.check else demo(data, registry),
                         ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, TypeError, KeyError, OSError, UnicodeError,
            RecursionError, IndexError) as exc:
        print("UNOVA_G05_2_BLOCKED: " + str(exc))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
