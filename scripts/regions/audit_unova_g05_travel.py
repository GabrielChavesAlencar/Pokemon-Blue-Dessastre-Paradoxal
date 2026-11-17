#!/usr/bin/env python3
"""G05.3 Unova NPC travel audit. Synthetic-only, no native destinations added.

The BlueRegionTravel/BlueRegions source remains authoritative. This module
proves *offline* invariant behavior and fail-safe simulation only, never
invokes a game event, edits a native save, or approves a map installation.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
from pathlib import Path
from typing import Any

import audit_unova_g05_regional_items as items
import audit_unova_g05_badges_specials as specials

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = "data/regions/unova-g05-travel-contract.json"
SOURCES = {
    "registry": "site/public/data/regions.json",
    "items": "data/regions/unova-g05-regional-items-contract.json",
    "specials": "data/regions/unova-g05-badges-specials-contract.json",
    "runtime_travel": "scripts/battle_polish/RegionTravel.rb",
    "runtime_regions": "scripts/battle_polish/Regions.rb",
    "runtime_start": "scripts/battle_polish/RegionStart.rb",
    "tracker": "site/public/data/unova-github-progress.json",
}
ROUTABLE = ("DECADES", "KANTO", "JOHTO", "HOENN")
ORIGINS = {
    "DECADES": "FIXTURE_DECADES_CHERRYHILL",
    "KANTO": "FIXTURE_KANTO_PALLET",
    "JOHTO": "FIXTURE_JOHTO_NEW_BARK",
    "HOENN": "FIXTURE_HOENN_LITTLEROOT",
}
DECADES_SAFE = "FIXTURE_DECADES_CHERRYHILL_SAFE"
OTHER_PLANNED = ("SINNOH", "UNOVA", "KALOS", "ALOLA", "GALAR", "PALDEA", "HISUI")
EVIDENCE = {
    "unova_verified_source_map_id": None,
    "unova_npc_event_id": None,
    "unova_native_installer_proof": None,
    "unova_approved_arrival_point": None,
    "unova_native_return_event": None,
    "unova_game_exe_qa_receipt": None,
    "unova_android_qa_receipt": None,
    "unova_source_license": None,
}
POLICY = {
    "npc_must_be_interacted_with": True,
    "agent_must_be_at_initial_town": True,
    "campaign_not_arena": True,
    "safe_context_required": True,
    "source_installation_required": True,
    "destination_installed_and_safe_point_required": True,
    "regional_circuit_is_not_install_proof": True,
    "league_victory_not_required_by_current_runtime": True,
    "no_hall_of_fame_gate": True,
    "no_menu_or_route_teleport": True,
    "same_region_not_destination": True,
    "hisui_requires_separate_quest_and_install_proof": True,
    "decades_return_not_native_intro": True,
    "decades_stored_return_must_match_verified_town": True,
    "decades_fallback_verified_safe_town_only": True,
    "preview_hm_keyitem_pc_before_commit": True,
    "preview_special_party_and_box_slots_before_commit": True,
    "require_non_egg_non_fainted_survivor": True,
    "recheck_at_final_commit_boundary": True,
    "atomic_rollback_party_boxes_bag_pc_region_mechanics_and_position": True,
    "quiet_only_suppresses_messages": True,
    "unova_native_travel_forbidden": True,
    "never_map_planned_area_to_native": True,
    "no_game_or_save_writes": True,
}
SIMULATION = {
    "scope": "G05_3_SYNTHETIC_TRAVEL_NOT_GAME_SAVE",
    "synthetic_install_proof_is_not_native_evidence": True,
    "fixture_location_prefix": "FIXTURE_",
    "destination_points_are_labels_not_map_ids": True,
    "no_native_transfer_or_installer_calls": True,
    "no_npc_spawn": True,
    "no_pokemon_held_in_native_pc": True,
    "no_real_badge_or_level_change": True,
    "no_native_save_adapter": True,
    "no_claim_real_johto_or_hoenn_ready": True,
}
CONTRACT_KEYS = {
    "schema", "phase", "region", "campaign", "status", "sources",
    "native_evidence", "routable_runtime_regions", "planned_only_regions",
    "origin_labels", "decades_safe_fallback", "policy", "simulation",
    "native_map_ids_allocated", "native_npc_installed",
    "native_saves_modified", "game_exe_tested", "android_tested",
    "can_install", "notes",
}
STATE_KEYS = {
    "scope", "version", "current", "npc_event_context", "at_initial_town",
    "campaign_active", "arena_mode", "safe_context", "install_proofs",
    "arrival_proofs", "position", "decades_return", "bag_state",
    "party_state", "pc_boxes", "travel_history", "mechanics_by_region",
    "current_mechanics",
}
SAFE_FLAGS = {
    "player_present", "game_map_present", "game_player_present",
    "scene_present", "game_temp_present", "scene_can_transfer",
    "in_battle", "player_transferring", "message_window_showing",
    "transition_processing", "interpreter_running",
}
SAFE_TRUE = {
    "player_present", "game_map_present", "game_player_present",
    "scene_present", "game_temp_present", "scene_can_transfer",
}
RUNTIME_SIGNATURES = {
    "runtime_travel": (
        "def self.installed?", "def self.johto_installed?",
        "def self.hoenn_installed?", "def self.safe_context?",
        "def self.source_valid?(state)", "def self.available?(state = nil)",
        "def self.destination(state, key)", "def self.preview(state, key)",
        "def self.perform(state, key, plan = nil)",
        "def self.at_departure_town?(state)",
        "def self.travel(key, quiet = false)", "def self.agent(from_npc = false)",
        'return false unless @npc_event_context',
        "return false unless available?(state) && at_departure_town?(state)",
        "return nil if key == state[\"current\"]",
        'when "DECADES" then installed?',
        'when "KANTO" then installed?',
        'when "JOHTO" then !!johto_installed?',
        'when "HOENN" then !!hoenn_installed?',
        "BlueRegionStart.johto_town_point",
        "decades_town_point", 'position = state["decades_return"]',
        "position[0] == city_id",
        "return nil unless safe.length >= 2",
        'return [:locked, []] unless destination(state, key)',
        "BlueRegions.transfer_plan(state, key, $player.party,",
        "stage_local_bag(state, key)",
        "raise message_for(status) unless status == :ok",
        "reservations.each do |pkmn, pos|",
        'next_state["travel_history"] <<',
        'next_state["region_key_items"]',
        'next_state["mechanics_by_region"]',
        "old_party = $player.party.dup",
        "old_slots = reservations.map",
        "old_bag = Marshal.load(Marshal.dump($bag))",
        "old_pc_items = pc_storage && Marshal.load(Marshal.dump(pc_storage.items))",
        'pc_storage.items.replace(old_pc_items) if pc_storage && old_pc_items',
        '$player.party.replace(old_party)',
        'old_slots.each { |pos, previous| $PokemonStorage[pos[0],pos[1]] = previous }',
        "pbFadeOutIn { move_to(before) }",
        "raise error",
        "previous_event_context = @npc_event_context",
        "@npc_event_context = previous_event_context",
    ),
    "runtime_regions": (
        "def self.unlocked(state)",
        "available = circuit.dup",
        "def self.transfer_plan(state, destination, party, slots, native_badges = [], &classify)",
        "return [:no_usable_party, []] unless party.any?",
        "return [:box_full, []] if slots.length < deposit.length",
    ),
    "runtime_start": (
        "def self.johto_install_proof",
        "def self.johto_town_point",
        "def self.johto_agent_point",
        "def self.hoenn_town_point",
    ),
}
FIXTURE_ID = re.compile(r"FIXTURE_[A-Z][A-Z0-9_]*\Z")
FAIL_POINTS = ("after_party", "after_region", "after_bag", "after_pc", "after_position")

def deny(msg: str) -> None:
    raise ValueError("UNOVA_G05_3_BLOCKED: " + msg)

def exact(obj: Any, keys: set[str], label: str) -> None:
    if not isinstance(obj, dict) or set(obj) != keys:
        deny(label + " has unexpected/missing fields")

def load_json(root: Path, path: str) -> dict:
    return items.load_json(root, path)

def source(root: Path, path: str) -> str:
    return items.read_source(root, path)

def validate_catalog(data: dict, registry: dict, items_contract: dict,
                     specials_contract: dict, tracker: dict, runtime: dict) -> dict:
    exact(data, CONTRACT_KEYS, "travel contract")
    expected = {
        "schema": 1, "phase": "G05.3", "region": "UNOVA",
        "campaign": "WHITE_BW", "status": "PLANNED_OFFLINE_TRAVEL_AUDIT_ONLY",
        "sources": SOURCES, "native_evidence": EVIDENCE,
        "routable_runtime_regions": list(ROUTABLE),
        "planned_only_regions": list(OTHER_PLANNED),
        "origin_labels": ORIGINS, "decades_safe_fallback": DECADES_SAFE,
        "policy": POLICY, "simulation": SIMULATION,
        "native_map_ids_allocated": False, "native_npc_installed": False,
        "native_saves_modified": False, "game_exe_tested": False,
        "android_tested": False, "can_install": False,
    }
    for field, expected_value in expected.items():
        if data.get(field) != expected_value or type(data[field]) is not type(expected_value):
            deny("policy, native evidence or source changed: " + field)
    regions = registry.get("regions", {})
    circuit = registry.get("circuit")
    if (not isinstance(regions, dict) or not isinstance(circuit, list)
        or not set(ROUTABLE).issubset(set(circuit))
        or set(OTHER_PLANNED) != set(regions) - set(ROUTABLE)
        or any(regions[key]["status"] != "planned" for key in OTHER_PLANNED)
        or len(circuit) != len(set(circuit)) or "UNOVA" not in circuit):
        deny("planned regional registry or circuit drift")
    if (items_contract.get("phase") != "G05.1"
        or items_contract.get("can_install") is not False
        or specials_contract.get("phase") != "G05.2"
        or specials_contract.get("can_install") is not False
        or specials_contract.get("native_saves_modified") is not False
        or tracker.get("status") != "PLANNED_NOT_NATIVE_PLAYABLE"
        or tracker.get("native_technical_bar", {}).get("completed") != 0
        or tracker.get("native_playable_bar", {}).get("completed") != 0):
        deny("unverified native readiness in G05.1/G05.2 or tracker")
    milestone = next((t for group in tracker.get("groups", [])
                      for t in group.get("tasks", [])
                      if t.get("id") == "G05.3"), None)
    if milestone is None or milestone.get("status") not in ("pending", "done"):
        deny("missing G05.3 task in tracker")
    for key, needed in RUNTIME_SIGNATURES.items():
        content = runtime.get(key)
        if not isinstance(content, str) or any(token not in content for token in needed):
            deny("native Ruby route guard/rollback changed; re-audit required: " + key)
    if not isinstance(data.get("notes"), list) or len(data["notes"]) < 6 or any(
        not isinstance(note, str) or not note.strip() for note in data["notes"]
    ):
        deny("native and synthetic safety warnings missing")
    return {
        "phase": "G05.3", "runtime_routable_regions": list(ROUTABLE),
        "planned_only_regions": list(OTHER_PLANNED),
        "native_unova_npc_installed": False,
        "native_unova_arrival_verified": False,
        "fixture_preflight_available": True, "fixture_rollback_available": True,
        "native_saves_modified": False, "game_exe_tested": False,
        "can_install": False,
    }

def load_project(root: Path = ROOT) -> tuple[dict, dict, dict, dict, dict]:
    root = Path(root)
    data = load_json(root, CONTRACT_PATH)
    s = data["sources"]
    registry = load_json(root, s["registry"])
    items_contract = load_json(root, s["items"])
    specials_contract = load_json(root, s["specials"])
    tracker = load_json(root, s["tracker"])
    ruby_sources = {key: source(root, s[key]) for key in RUNTIME_SIGNATURES}
    report = validate_catalog(
        data, registry, items_contract, specials_contract, tracker, ruby_sources
    )
    return data, registry, items_contract, specials_contract, report

def validate_fixture(snapshot: dict, registry: dict) -> dict:
    exact(snapshot, STATE_KEYS, "synthetic travel state")
    if snapshot["scope"] != SIMULATION["scope"] or type(snapshot["version"]) is not int or snapshot["version"] != 1:
        deny("native or future save cannot enter synthetic travel")
    current = snapshot["current"]
    if type(current) is not str or current not in registry["regions"]:
        deny("unknown source region")
    for flag in ("npc_event_context", "at_initial_town", "campaign_active", "arena_mode"):
        if type(snapshot[flag]) is not bool:
            deny("travel context flag must be boolean: " + flag)
    safety = snapshot["safe_context"]
    exact(safety, SAFE_FLAGS, "scene safety")
    if any(type(x) is not bool for x in safety.values()):
        deny("scene/context proof must be explicit booleans")
    for label in ("install_proofs", "arrival_proofs"):
        facts = snapshot[label]
        exact(facts, set(ROUTABLE), "synthetic "+label)
        if any(type(x) is not bool for x in facts.values()):
            deny("only synthetic boolean installation/arrival proofs are allowed")
    if type(snapshot["position"]) is not str or not FIXTURE_ID.fullmatch(snapshot["position"]):
        deny("native MapID/coordinate may not be smuggled in as fixture position")
    back = snapshot["decades_return"]
    if back is not None and back != ORIGINS["DECADES"]:
        deny("Decades return must be a verified Cherryhill fixture, never INTRO")
    if not isinstance(snapshot["travel_history"], list) or len(snapshot["travel_history"]) > 100:
        deny("travel history over limit or malformed")
    for record in snapshot["travel_history"]:
        exact(record, {"source", "destination", "from_point", "to_point"}, "fixture travel history")
        if (record["source"] not in ROUTABLE or record["destination"] not in ROUTABLE
            or any(type(record[k]) is not str or not FIXTURE_ID.fullmatch(record[k])
                   for k in ("from_point", "to_point"))):
            deny("invalid synthetic travel history entry")
    for name in ("mechanics_by_region", "current_mechanics"):
        value = snapshot[name]
        if not isinstance(value, dict) or len(value) > 16:
            deny("malformed synthetic mechanics")
    if any(k not in registry["regions"] or not isinstance(v, dict)
           or any(type(a) is not str or not a.startswith("FIXTURE_")
                  or type(b) is not bool for a, b in v.items())
           for k, v in snapshot["mechanics_by_region"].items()):
        deny("foreign or real regional mechanics key")
    if any(type(a) is not str or not a.startswith("FIXTURE_") or type(b) is not bool
           for a, b in snapshot["current_mechanics"].items()):
        deny("native mechanics cannot be changed by fixtures")
    pc_boxes = snapshot["pc_boxes"]
    if not isinstance(pc_boxes, dict) or len(pc_boxes) > 180 or any(
        type(slot) is not str or not FIXTURE_ID.fullmatch(slot)
        or type(name) is not str or not FIXTURE_ID.fullmatch(name)
        for slot, name in pc_boxes.items()
    ):
        deny("native/duplicate synthetic Pokemon box identifiers")
    if snapshot["position"] == "FIXTURE_DECADES_INTRO":
        deny("never return to native Decades introduction")
    bag = items.validate_state(snapshot["bag_state"], registry)
    party = specials.validate_fixture(snapshot["party_state"], registry)
    if bag["current"] != current or party["current"] != current:
        deny("Bag/PC, Pokemon party and campaign must have same active region")
    if {p["id"] for p in party["party"]}.intersection(pc_boxes.values()):
        deny("same Pokemon cannot occupy party and box")
    if any(slot in pc_boxes for slot in party["free_box_slots"]):
        deny("advertised free PC slot already occupied")
    return snapshot

def _safe(scene: dict) -> bool:
    return (all(scene[key] for key in SAFE_TRUE)
            and not any(scene[key] for key in SAFE_FLAGS - SAFE_TRUE))

def _return_point(snapshot: dict, destination: str) -> str:
    if destination == "DECADES":
        return snapshot["decades_return"] or DECADES_SAFE
    return ORIGINS[destination]

def _rejection(state: dict, code: str, destination: str) -> dict:
    return {
        "phase": "G05.3", "status": code, "source": state["current"],
        "destination": destination, "fixture": copy.deepcopy(state),
        "simulated_install_proof_only": True, "native_transfer": False,
        "native_save_modified": False, "can_install": False,
    }

def preflight(data: dict, registry: dict, it: dict, sp: dict,
              snapshot: dict, destination: str, *,
              npc_from_event: bool = True, quiet: bool = False) -> dict:
    validate_fixture(snapshot, registry)
    if type(npc_from_event) is not bool or type(quiet) is not bool:
        deny("npc and quiet flags must be explicit booleans")
    if type(destination) is not str or destination not in registry["regions"]:
        deny("unknown destination")
    current = snapshot["current"]
    if destination == current:
        return _rejection(snapshot, "SAME_REGION_NO_TRAVEL", destination)
    if not snapshot["campaign_active"] or snapshot["arena_mode"]:
        return _rejection(snapshot, "MAIN_CAMPAIGN_REQUIRED", destination)
    if not _safe(snapshot["safe_context"]):
        return _rejection(snapshot, "UNSAFE_SCENE_BLOCKED", destination)
    if not npc_from_event or not snapshot["npc_event_context"]:
        return _rejection(snapshot, "NPC_EVENT_REQUIRED", destination)
    if not snapshot["at_initial_town"] or (
        current in ROUTABLE and snapshot["position"] != ORIGINS[current]
    ):
        return _rejection(snapshot, "INITIAL_TOWN_REQUIRED", destination)
    if current not in ROUTABLE or not snapshot["install_proofs"].get(current):
        return _rejection(snapshot, "SOURCE_NOT_INSTALLED_OR_SUPPORTED", destination)
    if destination not in ROUTABLE:
        return _rejection(snapshot, "DESTINATION_NOT_INSTALLED_OR_SUPPORTED", destination)
    if not snapshot["install_proofs"][destination] or not snapshot["arrival_proofs"][destination]:
        return _rejection(snapshot, "DESTINATION_INSTALL_OR_POINT_UNVERIFIED", destination)
    if destination == "DECADES" and snapshot["decades_return"] not in (
        None, ORIGINS["DECADES"]
    ):
        return _rejection(snapshot, "UNSAFE_DECADES_RETURN_BLOCKED", destination)
    # A shortcut or a player level never grants native region installation.
    # G05.1 stages the Bag/PC, G05.2 reserves restricted Pokemon.
    try:
        staged_items = items.plan_travel(
            it, registry, snapshot["bag_state"], destination
        )
    except (ValueError, KeyError, TypeError) as exc:
        return _rejection(snapshot, "BAG_OR_ITEM_PC_PREVIEW_BLOCKED", destination)
    if destination != "DECADES":
        preview = specials.preview_transfer(
            sp, snapshot["party_state"], registry, destination
        )
        if preview["status"] != "SYNTHETIC_PREVIEW_ONLY_NEVER_NATIVE_TRAVEL":
            code = {
                "NO_USABLE_PARTY_BLOCKED": "NO_USABLE_PARTY_BLOCKED",
                "INSUFFICIENT_BOX_SLOTS_BLOCKED": "BOX_CAPACITY_BLOCKED",
            }.get(preview["status"], "SPECIAL_PREVIEW_BLOCKED")
            return _rejection(snapshot, code, destination)
        reservations = preview["reservations"]
    else:
        # Offline fixture has NO verified Decades native badges. Conservatively
        # refuse moving any special Pokemon there, rather than simulate a
        # Decades-specific badge unlock that has not been proven here.
        party = snapshot["party_state"]["party"]
        if any(specials.special_pokemon(p) for p in party):
            return _rejection(snapshot, "DECADES_NATIVE_SPECIAL_GATE_UNKNOWN", destination)
        if not any(not p["egg"] and not p["fainted"] for p in party):
            return _rejection(snapshot, "NO_USABLE_PARTY_BLOCKED", destination)
        reservations = []
    return {
        "phase": "G05.3", "status": "SIMULATED_PREFLIGHT_NOT_NATIVE",
        "source": current, "destination": destination,
        "point": _return_point(snapshot, destination),
        "staged_items": staged_items["fixture"],
        "reservations": reservations,
        "quiet_permission_unchanged": True,
        "native_install_evidence": None, "native_transfer": False,
        "native_save_modified": False, "can_install": False,
    }

def simulate(data: dict, registry: dict, it: dict, sp: dict,
             snapshot: dict, destination: str, *, fail_at: str | None = None,
             npc_from_event: bool = True, quiet: bool = False) -> dict:
    if fail_at is not None and fail_at not in FAIL_POINTS:
        deny("unknown synthetic failure injection")
    before = copy.deepcopy(snapshot)
    check = preflight(data, registry, it, sp, snapshot, destination,
                      npc_from_event=npc_from_event, quiet=quiet)
    if check["status"] != "SIMULATED_PREFLIGHT_NOT_NATIVE":
        return check
    staged = copy.deepcopy(snapshot)
    try:
        reservations = check["reservations"]
        party = staged["party_state"]["party"]
        to_box = {row["pokemon_id"]: row["slot"] for row in reservations}
        for mon in party:
            if mon["id"] in to_box:
                slot = to_box[mon["id"]]
                if slot in staged["pc_boxes"]:
                    raise RuntimeError("reserved Pokemon Box slot became occupied")
                staged["pc_boxes"][slot] = mon["id"]
        staged["party_state"]["party"] = [
            mon for mon in party if mon["id"] not in to_box
        ]
        staged["party_state"]["free_box_slots"] = [
            slot for slot in staged["party_state"]["free_box_slots"]
            if slot not in set(to_box.values())
        ]
        if fail_at == "after_party":
            raise RuntimeError("fixture simulated box/party failure")
        staged["current"] = destination
        staged["party_state"]["current"] = destination
        staged["travel_history"].append({
            "source": snapshot["current"], "destination": destination,
            "from_point": snapshot["position"], "to_point": check["point"],
        })
        staged["mechanics_by_region"][snapshot["current"]] = copy.deepcopy(
            snapshot["current_mechanics"]
        )
        staged["current_mechanics"] = copy.deepcopy(
            staged["mechanics_by_region"].get(destination, {})
        )
        if snapshot["current"] == "DECADES":
            staged["decades_return"] = ORIGINS["DECADES"]
        if fail_at == "after_region":
            raise RuntimeError("fixture simulated regional state failure")
        staged["bag_state"] = copy.deepcopy(check["staged_items"])
        if fail_at == "after_bag":
            raise RuntimeError("fixture simulated Bag failure")
        # The staged Bag contains the staged item PC as an independent
        # collection. Failure after staging both rolls everything back.
        if fail_at == "after_pc":
            raise RuntimeError("fixture simulated item PC failure")
        staged["position"] = check["point"]
        if fail_at == "after_position":
            raise RuntimeError("fixture simulated map transfer failure")
        validate_fixture(staged, registry)
    except (RuntimeError, ValueError, TypeError, KeyError, IndexError):
        # Synthetic atomic rollback: original was never modified; return a
        # full deep-copy of the snapshot from before ANY staged changes.
        if snapshot != before:
            deny("input mutated despite transactional synthetic failure")
        return {
            "phase": "G05.3", "status": "SIMULATED_TRANSFER_FAILED_ROLLED_BACK",
            "source": snapshot["current"], "destination": destination,
            "fixture": before, "restored_position": before["position"],
            "all_staged_changes_rolled_back": True,
            "native_transfer": False, "native_save_modified": False,
            "can_install": False,
        }
    if snapshot != before:
        deny("input modified by synthetic travel")
    return {
        "phase": "G05.3", "status": "SIMULATED_SUCCESS_NOT_NATIVE_TRAVEL",
        "source": snapshot["current"], "destination": destination,
        "fixture": staged, "position": check["point"],
        "deposited_specials": len(check["reservations"]),
        "native_transfer": False, "native_save_modified": False,
        "can_install": False,
    }

def demo(data: dict, registry: dict, it: dict, sp: dict) -> dict:
    item = lambda key, kind: {"id": "FIXTURE_"+key, "kind": kind, "qty": 1}
    mon = lambda key, flags: {
        "id": "FIXTURE_"+key, "flags": flags, "base_flags": [],
        "form": 0, "egg": False, "fainted": False
    }
    bag = {
        "scope": items.SCOPE, "current": "KANTO",
        "bag": [item("KANTO_HM", "HM"), item("TM_GLOBAL", "TM")],
        "pc": [item("KANTO_KEY_PC", "KEY_ITEM")],
        "registered": ["FIXTURE_KANTO_HM", "FIXTURE_TM_GLOBAL"],
        "vault": {
            "HOENN": {"items": [item("HOENN_HM", "HM")],
                      "registered": ["FIXTURE_HOENN_HM"],
                      "pc_items": [item("HOENN_KEY_PC", "KEY_ITEM")]},
        },
        "bag_capacity": 16, "pc_capacity": 16, "badges": [],
    }
    party = {
        "scope": specials.SIMULATION["scope"], "version": 1,
        "current": "KANTO",
        "achievements": {"HOENN": registry["regions"]["HOENN"]["milestones"][:2]},
        "native_decades_badge_count": 0,
        "hisui_complete": False,
        "party": [mon("COMMON", []), mon("LEGEND", ["Legendary"])],
        "free_box_slots": ["FIXTURE_BOX_A"],
    }
    snapshot = {
        "scope": SIMULATION["scope"], "version": 1, "current": "KANTO",
        "npc_event_context": True, "at_initial_town": True,
        "campaign_active": True, "arena_mode": False,
        "safe_context": {key: key in SAFE_TRUE for key in SAFE_FLAGS},
        "install_proofs": {key: True for key in ROUTABLE},
        "arrival_proofs": {key: True for key in ROUTABLE},
        "position": ORIGINS["KANTO"], "decades_return": None,
        "bag_state": bag, "party_state": party, "pc_boxes": {},
        "travel_history": [], "mechanics_by_region": {},
        "current_mechanics": {"FIXTURE_MEGA": True},
    }
    blocked = preflight(data, registry, it, sp, snapshot, "UNOVA")
    planned = preflight(data, registry, it, sp, snapshot, "HOENN")
    failed = simulate(data, registry, it, sp, snapshot, "HOENN", fail_at="after_pc")
    travelled = simulate(data, registry, it, sp, snapshot, "HOENN")
    returned = simulate(data, registry, it, sp, travelled["fixture"], "KANTO")
    return {
        "phase": "G05.3", "fixture_only": True,
        "unova_native_entry": blocked["status"],
        "hoenn_fixture_preflight": planned["status"],
        "simulated_failure": failed["status"],
        "rollback_preserved": failed["fixture"] == snapshot,
        "hoenn_fixture_arrival": travelled["status"],
        "hoenn_specials_deposited": travelled["deposited_specials"],
        "return_status": returned["status"],
        "kanto_hm_restored": any(
            x["id"] == "FIXTURE_KANTO_HM"
            for x in returned["fixture"]["bag_state"]["bag"]
        ),
        "native_saves_modified": False, "native_npc_installed": False,
        "can_install": False,
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--simulate-demo", action="store_true")
    args = parser.parse_args(argv)
    try:
        data, registry, it, sp, report = load_project()
        print(json.dumps(report if args.check else demo(data, registry, it, sp),
                         ensure_ascii=False, sort_keys=True))
        return 0
    except (ValueError, TypeError, OSError, KeyError, IndexError,
            UnicodeError, RecursionError) as exc:
        print("UNOVA_G05_3_BLOCKED: "+str(exc))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
