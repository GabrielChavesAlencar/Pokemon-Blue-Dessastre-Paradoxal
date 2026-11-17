#!/usr/bin/env python3
"""S22: static fail-closed preflight for Sinnoh -> Hoenn/Unova.

The Ruby regression executes the genuine BlueRegionTravel inventory staging
with synthetic Bag/PC. Never use static contracts to certify physical maps.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/regions/sinnoh-travel-s22.json"
STORY = ROOT / "data/regions/sinnoh-story-ch14-contract.json"
SOURCE = ROOT / "data/regions/sinnoh-source.json"
REGISTRY = ROOT / "site/public/data/regions.json"
TRAVEL = ROOT / "scripts/battle_polish/RegionTravel.rb"
STORY_RUBY = ROOT / "scripts/regions/SinnohStoryContracts.rb"
REGIONS_RUBY = ROOT / "scripts/battle_polish/Regions.rb"
RUBY = ROOT / "scripts/regions/SinnohTravelContracts.rb"
FIXTURE = ROOT / "tests/sinnoh_s22_travel_runtime.rb"

SOURCES = {
    "regional_policy": "scripts/battle_polish/Regions.rb",
    "travel_engine": "scripts/battle_polish/RegionTravel.rb",
    "story_engine": "scripts/regions/SinnohStoryContracts.rb",
    "league_engine": "scripts/regions/SinnohLeagueContracts.rb",
    "travel_adapter": "scripts/regions/SinnohTravelContracts.rb",
    "original_ch14_contract": "data/regions/sinnoh-story-ch14-contract.json",
    "sinnoh_source": "data/regions/sinnoh-source.json",
    "registry": "site/public/data/regions.json",
    "fixture": "tests/sinnoh_s22_travel_runtime.rb",
}
INVENTORY = {
    "regional_items": "GameData::Item is_key_item? or is_HM?",
    "same_region_bag_and_pc_restored_on_return": True,
    "normal_items_remain_shared": True,
    "regional_hms_do_not_carry_between_regions": True,
    "preview_never_changes_bag_party_pc_or_save": True,
    "native_transfer_must_use_existing_BlueRegionTravel_stage_and_rollback": True,
}
CHECKS = {
    "only_verified_hall_of_fame_enables_post_league_preflight": True,
    "hoenn_requires_existing_installed_arrival": True,
    "unova_requires_existing_installed_arrival": True,
    "source_sinnoh_must_be_native_and_installed": True,
    "native_npc_context_required": True,
    "unverified_source_registry_fail_closed": True,
    "no_fallback_to_kanto_hoenn_or_decades_home_map": True,
    "no_map_ids_or_coordinates_inferred": True,
    "no_cross_region_item_transfer": True,
    "no_second_story_save_or_auto_unlock_flags": True,
    "no_game_exe_or_joiplay_claim": True,
}
STATICS = {
    "schema": 1,
    "region": "SINNOH",
    "stage": "S22",
    "status": "READ_ONLY_POST_LEAGUE_TRAVEL_PREFLIGHT_NO_NATIVE_SOURCE",
    "sources": SOURCES,
    "post_league_destinations": ["HOENN", "UNOVA"],
    "hall_of_fame_required_for_this_post_league_journey": True,
    "global_circuit_free_travel_policy_unchanged": True,
    "real_departure_npc_map_id": None,
    "real_departure_npc_event_id": None,
    "installed_unova_arrival": None,
    "installed_sinnoh_portal": False,
    "allows_remote_map_travel": False,
    "inventory_policy": INVENTORY,
    "checks": CHECKS,
}
MUST_BE_EMPTY = (
    "verified_native_departures", "verified_source_map_ids",
    "verified_arrival_points",
)
MUST_BE_FALSE = (
    "game_exe_tested", "joiplay_tested", "native_qa_passed",
    "playable_verified", "can_install",
)
EXPECTED_KEYS = set(STATICS) | set(MUST_BE_EMPTY) | set(MUST_BE_FALSE) | {"notes"}
ADAPTER_TOKENS = (
    "module BlueSinnohTravelContracts",
    "POST_LEAGUE_DESTINATIONS = %w[HOENN UNOVA].freeze",
    "VERIFIED_NATIVE_DEPARTURES = {}.freeze",
    "BlueSinnohStoryContracts.recorded(state)",
    "BlueSinnohStoryContracts.league_cleared?(state)",
    "BlueRegionTravel.destination(state, destination)",
    "return :destination_not_installed unless valid_arrival?(point)",
    "return :source_not_installed unless BlueRegionTravel.source_valid?(state)",
    "return :npc_context_required unless npc_context.equal?(true)",
    "return :npc_context_unavailable unless BlueRegionTravel.available?(state)",
    "return :departure_handler_not_verified unless",
    "def self.preview(state, destination, npc_context: false)",
    "def self.valid_arrival?(point)",
)
SHARED_TOKENS = (
    "def self.source_valid?(state)",
    'when "HOENN" then !!hoenn_installed?',
    "else false",
    "def self.available?(state = nil)",
    "source_valid?(state)",
    "def self.destination(state, key)",
    'elsif key == "HOENN"',
    "hoenn_town_point",
    "def self.regional_item?(item)",
    "data.is_key_item? || data.is_HM?",
    "def self.stage_local_bag(state, destination)",
    "source_contents[\"pc_items\"] = local_pc_contents(pc)",
    'next_state["region_key_items"][state["current"]] = source_items',
    "def self.perform(state, key, plan = nil)",
    "stage_local_bag(state, key)",
    "def self.at_departure_town?(state)",
    "def self.travel(key, quiet = false)",
    "return false unless @npc_event_context",
    "def self.agent(from_npc = false)",
)
FIXTURE_TOKENS = (
    "SINNOH_S22_HOENN_UNOVA_NPC_ARRIVAL_LOCAL_ITEMS_NO_TELEPORT_OFFLINE_OK",
    "BlueRegionTravel.stage_local_bag(state, \"HOENN\")",
    "BlueRegionTravel.stage_local_bag(return_state, \"SINNOH\")",
    "travel.preview(state, \"HOENN\", npc_context: true)",
    "travel.preview(state, \"UNOVA\", npc_context: true)",
    "BlueRegionTravel.source_valid?(state)",
    "Marshal.dump($bag)",
    "Marshal.dump($PokemonGlobal.pcItemStorage)",
)


def blocked(message: str) -> None:
    raise ValueError("SINNOH_S22_BLOCKED: " + message)


def audit(contract: dict, story: dict, source: dict, registry: dict,
          adapter: str, travel: str, story_ruby: str,
          regions_ruby: str, fixture: str) -> dict:
    if not isinstance(contract, dict) or set(contract) != EXPECTED_KEYS:
        blocked("contrato S22 com campos inesperados ou ausentes")
    for k, expected in STATICS.items():
        if type(contract.get(k)) is not type(expected) or contract[k] != expected:
            blocked("S22 mudou regras de Hoenn/Unova, Hall ou isolamento: " + k)
    if any(contract.get(key) != [] for key in MUST_BE_EMPTY):
        blocked("MapIDs, fontes de NPC ou pontos de chegada inventados")
    if any(contract.get(key) is not False for key in MUST_BE_FALSE):
        blocked("execucao Game.exe/JoiPlay ou QA nativa falsamente aprovada")
    if not isinstance(contract["notes"], str) or len(contract["notes"]) < 220:
        blocked("documentacao dos limites nativos ausente")
    if (not isinstance(story, dict) or story.get("region") != "SINNOH"
            or story.get("status") != "PLANNED_NATIVE_HOOKS_NOT_INSTALLED"
            or story.get("save_key") != "sinnoh_ch14"
            or story.get("destinations_post_cynthia") != ["HOENN", "UNOVA"]
            or story.get("hall_of_fame_requires_separate_engine_confirmation") is not True
            or story.get("native_hall_of_fame_verified") is not False
            or story.get("physical_travel_requires_verified_source_map_and_arrival") is not True
            or story.get("travel_without_verified_npc_context") is not False
            or story.get("travel_does_not_use_league_as_install_proof") is not True
            or story.get("native_events_installed") is not False
            or story.get("can_install") is not False):
        blocked("CH14 declarou viagem/HoF nativo sem prova")
    # A receipt proves only that the donor ZIP was read as inert RXDATA data.
    # It must NOT be mistaken for a compiled map, a native NPC or installation.
    status = source.get("status") if isinstance(source, dict) else None
    receipt = source.get("received_real_source", {}) if isinstance(source, dict) else {}
    if (not isinstance(source, dict) or source.get("region") != "SINNOH"
            or status not in ("REPO_BASELINE_PREPARED_SOURCE_PENDING",
                              "DONOR_RECEIVED_LOCAL_SOURCE_AUDITED_NOT_INSTALLABLE")
            or (status == "DONOR_RECEIVED_LOCAL_SOURCE_AUDITED_NOT_INSTALLABLE"
                and (not isinstance(receipt, dict)
                     or receipt.get("source_rights_verified") is not False
                     or receipt.get("editable_mapped_sinnoh_game_installed") is not False
                     or receipt.get("map_tree_count") != 76
                     or receipt.get("terrain_maps") != 54
                     or receipt.get("blank_maps") != 22))
            or source.get("import_control", {}).get("imports_enabled") is not False
            or source.get("import_control", {}).get("gameplay_sinnoh_installed") is not False):
        blocked("fonte real de Sinnoh marcada instalada sem auditoria")
    regions = registry.get("regions") if isinstance(registry, dict) else None
    circuit = registry.get("circuit") if isinstance(registry, dict) else None
    if (not isinstance(regions, dict) or not isinstance(circuit, list)
            or any(region not in circuit for region in ("SINNOH", "HOENN", "UNOVA"))
            or any(regions.get(key, {}).get("status") != "planned"
                   for key in ("SINNOH", "UNOVA"))
            or regions["SINNOH"].get("milestones") !=
               ["COAL", "FOREST", "COBBLE", "RELIC", "FEN", "MINE", "ICICLE", "BEACON"]):
        blocked("circuito de regioes alterado ou Unova marcada jogavel")
    if not isinstance(adapter, str) or any(x not in adapter for x in ADAPTER_TOKENS):
        blocked("adaptador S22 removeu fonte, NPC, Hall ou verificacao de chegada")
    if not re.search(r"VERIFIED_NATIVE_DEPARTURES\s*=\s*\{\}\.freeze", adapter):
        blocked("registro de NPC nativo preencheu fonte inexistente")
    if not isinstance(travel, str) or any(x not in travel for x in SHARED_TOKENS):
        blocked("motor de viagem perdeu isolamento de itens/NPC/origem")
    if not isinstance(story_ruby, str) or any(x not in story_ruby for x in (
        "def self.post_cynthia_destination(state, destination)",
        "return :story_incomplete unless league_cleared?(state)",
        "return :destination_not_installed unless point.is_a?(Array)",
        "return :source_not_installed unless BlueRegionTravel.source_valid?(state)",
        "return :npc_context_unavailable unless BlueRegionTravel.available?(state)",
        "hall_of_fame_verified.equal?(true)",
    )):
        blocked("CH14 eliminou confirmacao HoF ou fonte fisica")
    if not isinstance(regions_ruby, str) or any(x not in regions_ruby for x in (
        "def self.unlocked(state)", "available = circuit.dup",
        "def self.field_access(state, region, action, tool_ready = false)",
        "state[\"current\"] == \"SINNOH\"",
        "sinnoh_local_hms(state).include?(action)",
    )):
        blocked("regra de viagem livre/HM local entre regioes alterada")
    if not isinstance(fixture, str) or any(x not in fixture for x in FIXTURE_TOKENS):
        blocked("fixture S22 nao cobre Bag/PC, NPC e chegada falsa")
    return {
        "schema": 1, "region": "SINNOH", "stage": "S22",
        "status": "POST_LEAGUE_TRAVEL_PREFLIGHT_AUDITED_NATIVE_SOURCE_PENDING",
        "logical_post_league_destinations": ["HOENN", "UNOVA"],
        "physical_departure_sources_verified": 0,
        "physical_arrival_points_verified_for_sinnoh_travel": 0,
        "physical_npc_installed": False,
        "native_teleport_tested": False,
        "global_free_travel_changed": False,
        "native_items_or_saves_modified": False,
        "synthetic_inventory_staging_required": True,
        "game_exe_joiplay_executed": False,
        "gameplay_certified": False,
    }


def main() -> int:
    files = (CONTRACT, STORY, SOURCE, REGISTRY, RUBY, TRAVEL,
             STORY_RUBY, REGIONS_RUBY, FIXTURE)
    try:
        for file in files:
            if file.is_symlink() or not file.is_file():
                blocked("arquivo ausente/symlink: " + str(file))
        vals = [json.loads(p.read_text("utf-8")) for p in files[:4]]
        report = audit(*vals, *[p.read_text("utf-8") for p in files[4:]])
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
