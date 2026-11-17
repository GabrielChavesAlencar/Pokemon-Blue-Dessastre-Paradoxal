#!/usr/bin/env python3
"""G05.1: regional HM/key-item isolation QA. Fixtures only; no game/save writes.

Mirrors stable observable invariants from BlueRegionTravel and BlueRegions,
not a playable Unova integration or a replacement for Essentials' Bag/PC.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

import audit_unova_g01_chapter_machine as g01

ROOT = Path(__file__).resolve().parents[2]
FILE = ROOT / "data/regions/unova-g05-regional-items-contract.json"
SOURCES = {
    "registry": "site/public/data/regions.json",
    "state": "data/regions/unova-g01-state-contract.json",
    "sinnoh_reference": "data/regions/sinnoh-hms-s16.json",
    "travel_runtime": "scripts/battle_polish/RegionTravel.rb",
    "field_runtime": "scripts/battle_polish/RegionalPolicy.rb",
    "regions_runtime": "scripts/battle_polish/Regions.rb",
    "tracker": "site/public/data/unova-github-progress.json",
}
ACTIONS = ("CUT", "FLY", "SURF", "STRENGTH", "WATERFALL", "DIVE")
KINDS = ("HM", "KEY_ITEM", "TM", "CONSUMABLE", "MEGA_STONE")
LOCAL_KINDS = ("HM", "KEY_ITEM")
GLOBAL_KINDS = ("TM", "CONSUMABLE", "MEGA_STONE")
IDENT = re.compile(r"FIXTURE_[A-Z][A-Z0-9_]*\Z")
FIELDS = {"schema", "phase", "region", "campaign", "status", "sources",
          "unova_field_rules", "native_evidence", "classification",
          "regional_vault_policy", "legacy_policy", "simulation_policy",
          "native_pbs_verified", "native_pickups_verified",
          "native_saves_modified", "game_exe_tested", "android_tested",
          "can_install", "notes"}
EVIDENCE = {
    "unova_hm_item_ids": None, "unova_hm_pickup_events": None,
    "unova_key_item_list": None, "unova_key_item_event_ids": None,
    "unova_game_source_sha256": None, "unova_native_field_tests": None,
    "unova_map_ids": None, "unova_asset_license": None,
}
CLASSIFICATION = {
    "regional": ["HM", "KEY_ITEM"], "global": ["TM", "CONSUMABLE", "MEGA_STONE"],
    "runtime_source": "GameData::Item.try_get + is_HM? / is_key_item?",
    "never_classify_by_display_name": True,
}
VAULT = {
    "state_key": "region_key_items",
    "contents": ["items", "registered", "pc_items"],
    "save_source_before_travel": True,
    "restore_destination_only": True,
    "registered_must_be_locally_owned": True,
    "stale_source_shortcuts_discarded": True,
    "validate_all_destination_quantities": True,
    "no_foreign_hm_or_key_item": True,
    "pc_item_storage_not_pokemon_boxes": True,
    "never_copy_hms_on_travel": True,
    "preserve_global_tm_consumable_mega_items": True,
    "preview_before_commit": True,
    "rollback_if_capacity_or_transfer_fails": True,
}
LEGACY = {
    "untravelled_decades_uses_native_rules": True,
    "do_not_migrate_legacy_saves": True,
    "native_badges_unmodified": True,
    "regional_pokemon_boxes_out_of_scope": True,
    "regional_route_npc_out_of_scope": True,
    "unova_destination_not_installed": True,
}
SIMULATION = {
    "identity_prefix": "FIXTURE_", "require_explicit_item_kind": True,
    "no_pbs_or_real_item_ids": True, "no_real_mapids": True,
    "no_real_save_adapter": True, "no_native_item_grants": True,
    "no_runtime_field_effect_activation": True,
    "fixture_slot_capacity_only_not_essentials_equivalence": True,
}
ENTRY_FIELDS = {"id", "qty", "kind"}
STATE_FIELDS = {"scope", "current", "bag", "pc", "registered", "vault",
                "bag_capacity", "pc_capacity", "badges"}
SCOPE = "SYNTHETIC_FIXTURE_NOT_NATIVE_SAVE"
MAX_ENTRIES = 128

def deny(reason: str) -> None:
    raise ValueError("UNOVA_G05_1_BLOCKED: " + reason)

def exact(value: Any, keys: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != keys:
        deny(label + " must contain exactly versioned keys")

def load_json(root: Path, path: str) -> dict:
    target = root / path
    if target.is_symlink() or not target.is_file() or not 0 < target.stat().st_size < 300_000:
        deny("invalid repository source path")
    return json.loads(target.read_text(encoding="utf-8"))

def read_source(root: Path, path: str) -> str:
    target = root / path
    if target.is_symlink() or not target.is_file() or not 0 < target.stat().st_size < 150_000:
        deny("invalid repository Ruby source")
    return target.read_text(encoding="utf-8")

def validate_runtime(travel: str, fields: str, regions_code: str) -> None:
    travel_signatures = (
        "def self.regional_item?(item)",
        "data.is_key_item? || data.is_HM?",
        "def self.local_bag_contents(bag)",
        "def self.local_pc_contents(storage)",
        'state["region_key_items"] || {}',
        'target_contents.fetch("pc_items", [])',
        'source_contents["pc_items"] = local_pc_contents(pc)',
        'staged.registered_items.delete_if { |id| regional_item?(id) }',
        'source_contents = local_bag_contents(staged)',
        'next_state["region_key_items"][state["current"]] = source_items',
        'pc_storage.items.replace(staged_pc.items) if pc_storage && staged_pc',
        'pc_storage.items.replace(old_pc_items) if pc_storage && old_pc_items',
        '$bag.pockets.replace(old_bag.pockets)',
        '$bag.registered_items.replace(old_bag.registered_items)',
    )
    field_signatures = (
        "module BlueRegionalPolicy",
        "def self.hm_owned?(move)",
        "def self.field_result(move, selected = nil)",
        "prerequisite = BlueRegions.field_access",
        "return hm_owned?(move_id) ? :allowed : :hm",
        'current["current"] == "DECADES"',
    )
    regions_signatures = (
        "module BlueRegions", "def self.field_access(state, region, action, tool_ready = false)",
        'state["field_events"].fetch(region, []).include?(rule["event"])',
        "return :tool if rule[\"tool\"] && !tool_ready",
        "def self.sinnoh_local_hms(state)",
        "def self.record_sinnoh_hm(state, action, item, bag, pickup_confirmed = false)",
    )
    for code, needles in ((travel, travel_signatures),
                          (fields, field_signatures),
                          (regions_code, regions_signatures)):
        if not all(s in code for s in needles):
            deny("regional Ruby isolation changed: re-audit contract before use")

def validate_catalog(contract: dict, registry: dict, state_contract: dict,
                     sinnoh: dict, tracker: dict, travel: str, fields: str,
                     regions_code: str) -> dict:
    exact(contract, FIELDS, "G05.1 contract")
    expected = {
        "schema": 1, "phase": "G05.1", "region": "UNOVA",
        "campaign": "WHITE_BW",
        "status": "OFFLINE_ONLY_NO_NATIVE_ITEM_INSTALLATION",
        "sources": SOURCES, "native_evidence": EVIDENCE,
        "classification": CLASSIFICATION, "regional_vault_policy": VAULT,
        "legacy_policy": LEGACY, "simulation_policy": SIMULATION,
        "native_pbs_verified": False, "native_pickups_verified": False,
        "native_saves_modified": False, "game_exe_tested": False,
        "android_tested": False, "can_install": False,
    }
    for key, want in expected.items():
        if contract.get(key) != want or type(contract[key]) is not type(want):
            deny("unsupported source, policy or native proof: " + key)
    if (registry.get("regions", {}).get("UNOVA", {}).get("status") != "planned"
        or state_contract.get("status") != "VERSIONED_SCHEMA_ONLY_NOT_NATIVE_SAVE"
        or state_contract.get("region") != "UNOVA"
        or state_contract.get("game_exe_tested") is not False
        or sinnoh.get("region") != "SINNOH"
        or sinnoh.get("approved_for_install") is not False
        or sinnoh.get("no_cross_region_key_item_or_hm_transfer", True) is not True
        or tracker.get("status") != "PLANNED_NOT_NATIVE_PLAYABLE"
        or tracker.get("native_technical_bar", {}).get("completed") != 0
        or tracker.get("native_playable_bar", {}).get("completed") != 0):
        deny("source regional planning or native-safety flags changed")
    task = next((t for group in tracker.get("groups", [])
                 for t in group.get("tasks", [])
                 if t.get("id") == "G05.1"), None)
    if not task or task.get("status") not in ("pending", "done"):
        deny("G05.1 progress tracker missing")
    rules = registry["regions"]["UNOVA"].get("field", {})
    if set(rules) != set(ACTIONS):
        deny("registry has changed Unova field-action set")
    expected_rules = [
        {"action": action, "event": action+"_LOCAL",
         "requires_local_hm": True, "requires_local_event": True,
         "native_hm_id": None, "native_event_id": None,
         "pickup_source_proven": False, "implemented": False}
        for action in ACTIONS
    ]
    if contract.get("unova_field_rules") != expected_rules:
        deny("Unova field action, native ID, or pickup status invented")
    for action in ACTIONS:
        if rules[action] != {"event": action+"_LOCAL", "tool": True}:
            deny("Unova field event requires exact registry source")
    validate_runtime(travel, fields, regions_code)
    if not isinstance(contract.get("notes"), list) or len(contract["notes"]) < 5 or any(
        not isinstance(v, str) or not v.strip() for v in contract["notes"]
    ):
        deny("missing source limitations")
    return {
        "phase": "G05.1", "unova_field_actions": 6,
        "regional_item_classes": list(LOCAL_KINDS),
        "globally_preserved_classes": list(GLOBAL_KINDS),
        "native_item_ids": 0, "native_pickup_events": 0,
        "simulation_only": True, "game_exe_tested": False,
        "can_install": False,
    }

def load_project(root: Path = ROOT) -> tuple[dict, dict, dict]:
    root = Path(root)
    data = load_json(root, "data/regions/unova-g05-regional-items-contract.json")
    src = data["sources"]
    registry = load_json(root, src["registry"])
    state = load_json(root, src["state"])
    sinnoh = load_json(root, src["sinnoh_reference"])
    tracker = load_json(root, src["tracker"])
    report = validate_catalog(
        data, registry, state, sinnoh, tracker,
        read_source(root, src["travel_runtime"]),
        read_source(root, src["field_runtime"]),
        read_source(root, src["regions_runtime"]),
    )
    return data, registry, report

def validate_entries(rows: Any, label: str) -> list[dict]:
    if not isinstance(rows, list) or len(rows) > MAX_ENTRIES:
        deny(label + " must be a bounded item list")
    seen: set[str] = set()
    for item in rows:
        exact(item, ENTRY_FIELDS, label + " entry")
        identifier = item["id"]
        if type(identifier) is not str or not IDENT.fullmatch(identifier):
            deny("only explicitly synthetic fixture IDs accepted")
        if identifier in seen:
            deny("duplicate item ID in " + label)
        seen.add(identifier)
        if type(item["qty"]) is not int or not 1 <= item["qty"] <= 999:
            deny("item quantity must be positive integer")
        if item["kind"] not in KINDS:
            deny("unknown or real runtime item classification")
    return rows

def is_local(item: dict) -> bool:
    return item["kind"] in LOCAL_KINDS

def validate_saved(saved: Any, label: str) -> dict:
    exact(saved, {"items", "registered", "pc_items"}, label)
    bag = validate_entries(saved["items"], label + " bag")
    pc = validate_entries(saved["pc_items"], label + " pc")
    if any(not is_local(item) for item in bag + pc):
        deny("regional vault may hold only classified HM/key items")
    regs = saved["registered"]
    if not isinstance(regs, list) or len(regs) != len(set(map(str, regs))):
        deny("duplicate saved shortcut")
    local_bag_ids = {item["id"] for item in bag}
    if any(type(key) is not str or key not in local_bag_ids for key in regs):
        deny("shortcut must be owned in the saved region Bag")
    return saved

def validate_state(state: Any, registry: dict) -> dict:
    exact(state, STATE_FIELDS, "fixture state")
    if state["scope"] != SCOPE:
        deny("cannot inspect native or user save snapshots")
    regions = registry.get("regions", {})
    if type(state["current"]) is not str or state["current"] not in regions:
        deny("unknown source region")
    for cap, label in (("bag_capacity", "bag"), ("pc_capacity", "pc")):
        if type(state[cap]) is not int or not 0 <= state[cap] <= MAX_ENTRIES:
            deny(label + " capacity invalid")
    bag = validate_entries(state["bag"], "active bag")
    pc = validate_entries(state["pc"], "active item PC")
    registered = state["registered"]
    if not isinstance(registered, list) or len(registered) > MAX_ENTRIES:
        deny("invalid registered items")
    if any(type(name) is not str or not IDENT.fullmatch(name) for name in registered):
        deny("registered IDs must be synthetic")
    if len(registered) != len(set(registered)):
        deny("duplicate active shortcut")
    # A stale current shortcut is tolerated, but never imported into the vault.
    vault = state["vault"]
    if not isinstance(vault, dict) or any(
        type(region) is not str or region not in regions
        for region in vault
    ):
        deny("invalid vault region")
    for region, saved in vault.items():
        validate_saved(saved, region)
    if (type(state["badges"]) is not list or
        any(type(b) is not str or not b.startswith("FIXTURE_") for b in state["badges"])):
        deny("native badges out of fixture scope")
    if len(bag) > state["bag_capacity"] or len(pc) > state["pc_capacity"]:
        deny("invalid current fixture slot capacity")
    return state

def plan_travel(data: dict, registry: dict, state: dict, destination: str, *,
                input_source: str = SCOPE) -> dict:
    if input_source != SCOPE:
        deny("no native travel or save adapter")
    validate_state(state, registry)
    if type(destination) is not str or destination not in registry["regions"]:
        deny("unknown destination")
    if destination == state["current"]:
        deny("same-region travel cannot transfer inventory")
    source = state["current"]
    before = copy.deepcopy(state)
    # Read, validate and stage all destinations before changing any snapshot.
    to_save = {
        "items": [copy.deepcopy(item) for item in state["bag"] if is_local(item)],
        "pc_items": [copy.deepcopy(item) for item in state["pc"] if is_local(item)],
        "registered": [],
    }
    ids = {item["id"] for item in to_save["items"]}
    to_save["registered"] = [
        name for name in state["registered"] if name in ids
    ]
    validate_saved(to_save, "source")
    target = copy.deepcopy(state["vault"].get(destination, {
        "items": [], "registered": [], "pc_items": []
    }))
    validate_saved(target, "destination")
    bag = [copy.deepcopy(item) for item in state["bag"] if not is_local(item)]
    pc = [copy.deepcopy(item) for item in state["pc"] if not is_local(item)]
    # Fixture IDs are global in this demo. Real item metadata is authoritative.
    for channel, current, incoming, capacity in (
        ("bag", bag, target["items"], state["bag_capacity"]),
        ("pc", pc, target["pc_items"], state["pc_capacity"]),
    ):
        if {x["id"] for x in current} & {x["id"] for x in incoming}:
            deny("destination local ID conflicts with global " + channel + " item")
        if len(current) + len(incoming) > capacity:
            deny("destination " + channel + " item capacity exceeded; no commit")
    bag.extend(copy.deepcopy(target["items"]))
    pc.extend(copy.deepcopy(target["pc_items"]))
    globals_registered = [
        name for name in state["registered"]
        if name not in {item["id"] for item in to_save["items"]}
        and name in {item["id"] for item in bag if not is_local(item)}
    ]
    shortcuts = globals_registered + target["registered"]
    if len(shortcuts) != len(set(shortcuts)):
        deny("duplicate shortcut on arrival")
    output = copy.deepcopy(state)
    output["current"] = destination
    output["bag"] = bag
    output["pc"] = pc
    output["registered"] = shortcuts
    output["vault"][source] = to_save
    validate_state(output, registry)
    if before != state:
        deny("input state mutated during planning")
    return {
        "phase": "G05.1", "status": "PLANNED_FIXTURE_ONLY_NO_NATIVE_TRAVEL",
        "source": source, "destination": destination,
        "fixture": output, "native_save_modified": False,
        "field_use_unlocked": False, "game_exe_tested": False,
        "can_install": False,
    }

def plan_field_access(data: dict, registry: dict, state: dict, *,
                      action: str, local_event: bool,
                      hm_item_id: str | None = None) -> dict:
    validate_state(state, registry)
    if state["current"] != "UNOVA":
        deny("not in Unova: cannot borrow its field permissions")
    if type(action) is not str or action not in ACTIONS or type(local_event) is not bool:
        deny("unknown action or non-boolean event proof")
    if hm_item_id is not None and (
        type(hm_item_id) is not str or not IDENT.fullmatch(hm_item_id)
    ):
        deny("native HM identity cannot be inferred")
    matching = [item for item in state["bag"]
                if item["id"] == hm_item_id and item["kind"] == "HM"]
    if not local_event:
        reason = "MISSING_LOCAL_EVENT"
    elif hm_item_id is None or not matching:
        reason = "MISSING_LOCAL_HM"
    else:
        reason = "SIMULATED_GATES_PASS_NOT_NATIVE_AUTHORIZED"
    return {
        "action": action, "field_event": action+"_LOCAL",
        "status": reason, "native_event_id": None,
        "native_hm_item_id": None, "runtime_authorized": False,
        "installed": False, "simulation_only": True,
    }

def demo(data: dict, registry: dict) -> dict:
    entry = lambda name, kind: {"id": "FIXTURE_"+name, "kind": kind, "qty": 1}
    original = {
        "scope": SCOPE, "current": "KANTO",
        "bag": [entry("CUT_KANTO", "HM"), entry("TM_GLOBAL", "TM"),
                entry("KEY_KANTO", "KEY_ITEM")],
        "pc": [entry("KEY_PC_KANTO", "KEY_ITEM"), entry("POTION", "CONSUMABLE")],
        "registered": ["FIXTURE_CUT_KANTO", "FIXTURE_TM_GLOBAL"],
        "vault": {"UNOVA": {"items": [entry("SURF_UNOVA", "HM")],
                            "registered": ["FIXTURE_SURF_UNOVA"],
                            "pc_items": [entry("KEY_PC_UNOVA", "KEY_ITEM")]}},
        "bag_capacity": 16, "pc_capacity": 16, "badges": [],
    }
    arrived = plan_travel(data, registry, original, "UNOVA")
    denied = plan_field_access(data, registry, arrived["fixture"], action="SURF",
                               local_event=False, hm_item_id="FIXTURE_SURF_UNOVA")
    simulated_gate = plan_field_access(
        data, registry, arrived["fixture"], action="SURF",
        local_event=True, hm_item_id="FIXTURE_SURF_UNOVA")
    returned = plan_travel(data, registry, arrived["fixture"], "KANTO")
    return {
        "phase": "G05.1", "fixture_only": True,
        "unova_arrival_bag_ids": [x["id"] for x in arrived["fixture"]["bag"]],
        "unova_arrival_pc_ids": [x["id"] for x in arrived["fixture"]["pc"]],
        "local_event_denied": denied["status"],
        "simulated_gate": simulated_gate["status"],
        "returned_kanto_hm": any(x["id"] == "FIXTURE_CUT_KANTO"
                                  for x in returned["fixture"]["bag"]),
        "unova_hm_preserved_in_vault": any(
            x["id"] == "FIXTURE_SURF_UNOVA"
            for x in returned["fixture"]["vault"]["UNOVA"]["items"]
        ),
        "native_saves_modified": False, "can_install": False,
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--simulate-demo", action="store_true")
    args = parser.parse_args(argv)
    try:
        data, registry, report = load_project()
        result = report if args.check else demo(data, registry)
        print(json.dumps(result, sort_keys=True, ensure_ascii=False))
        return 0
    except (ValueError, TypeError, KeyError, OSError, IndexError,
            RecursionError, UnicodeError) as exc:
        print("UNOVA_G05_1_BLOCKED: "+str(exc))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
