"""S22 negative tests for Hall, destinations, NPC and regional inventory."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_s22_travel import (
    CONTRACT, STORY, SOURCE, REGISTRY, RUBY, TRAVEL,
    STORY_RUBY, REGIONS_RUBY, FIXTURE, audit,
)


class SinnohS22TravelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text("utf-8"))
        cls.story = json.loads(STORY.read_text("utf-8"))
        cls.source = json.loads(SOURCE.read_text("utf-8"))
        cls.registry = json.loads(REGISTRY.read_text("utf-8"))
        cls.adapter = RUBY.read_text("utf-8")
        cls.travel = TRAVEL.read_text("utf-8")
        cls.story_ruby = STORY_RUBY.read_text("utf-8")
        cls.regions_ruby = REGIONS_RUBY.read_text("utf-8")
        cls.fixture = FIXTURE.read_text("utf-8")

    def check(self, **kwargs):
        docs = {
            "contract": self.contract, "story": self.story,
            "source": self.source, "registry": self.registry,
            "adapter": self.adapter, "travel": self.travel,
            "story_ruby": self.story_ruby,
            "regions_ruby": self.regions_ruby, "fixture": self.fixture,
        }
        docs.update(kwargs)
        return audit(**copy.deepcopy(docs))

    def test_01_read_only_contract_and_two_proposed_destinations(self):
        r = self.check()
        self.assertEqual(
            r["status"], "POST_LEAGUE_TRAVEL_PREFLIGHT_AUDITED_NATIVE_SOURCE_PENDING")
        self.assertEqual(r["logical_post_league_destinations"], ["HOENN", "UNOVA"])
        self.assertEqual(r["physical_departure_sources_verified"], 0)
        self.assertEqual(r["physical_arrival_points_verified_for_sinnoh_travel"], 0)
        self.assertFalse(r["physical_npc_installed"])
        self.assertFalse(r["global_free_travel_changed"])
        self.assertFalse(r["game_exe_joiplay_executed"])
        self.assertFalse(r["native_items_or_saves_modified"])
        self.assertFalse(r["gameplay_certified"])

    def test_02_fake_game_exe_or_android_claim_is_rejected(self):
        for field in ("game_exe_tested", "joiplay_tested", "native_qa_passed",
                      "playable_verified", "can_install"):
            with self.subTest(field=field):
                doc = copy.deepcopy(self.contract)
                doc[field] = True
                with self.assertRaisesRegex(ValueError, "falsamente"):
                    self.check(contract=doc)

    def test_03_no_unverified_map_ids_departure_npc_or_arrival(self):
        for field, data in (
            ("verified_native_departures", [{"map_id": 778}]),
            ("verified_source_map_ids", [800]),
            ("verified_arrival_points", [{"region": "UNOVA", "point": [900, 1, 1, 2]}]),
        ):
            doc = copy.deepcopy(self.contract)
            doc[field] = data
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "inventados"):
                self.check(contract=doc)
        for field, data in (
            ("real_departure_npc_map_id", 778),
            ("real_departure_npc_event_id", 22),
            ("installed_unova_arrival", [900, 1, 1, 2]),
        ):
            doc = copy.deepcopy(self.contract)
            doc[field] = data
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "regras"):
                self.check(contract=doc)

    def test_04_no_remote_travel_or_premature_unlocks(self):
        for field in ("installed_sinnoh_portal", "allows_remote_map_travel",
                      "hall_of_fame_required_for_this_post_league_journey"):
            doc = copy.deepcopy(self.contract)
            doc[field] = not doc[field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "regras"):
                self.check(contract=doc)
        doc = copy.deepcopy(self.contract)
        doc["global_circuit_free_travel_policy_unchanged"] = False
        with self.assertRaisesRegex(ValueError, "regras"):
            self.check(contract=doc)

    def test_05_hoenn_unova_only_and_in_documented_order(self):
        for order in ([], ["UNOVA", "HOENN"], ["KANTO", "HOENN"],
                      ["HOENN", "UNOVA", "JOHTO"]):
            doc = copy.deepcopy(self.contract)
            doc["post_league_destinations"] = order
            with self.subTest(order=order), self.assertRaisesRegex(ValueError, "regras"):
                self.check(contract=doc)

    def test_06_bag_pc_regional_staging_must_remain_isolated(self):
        for field in self.contract["inventory_policy"]:
            doc = copy.deepcopy(self.contract)
            doc["inventory_policy"][field] = False
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "regras"):
                self.check(contract=doc)
        doc = copy.deepcopy(self.contract)
        doc["inventory_policy"]["regional_items"] = "all_items_global"
        with self.assertRaisesRegex(ValueError, "regras"):
            self.check(contract=doc)

    def test_07_npc_and_missing_map_safeguards_mandatory(self):
        for field in self.contract["checks"]:
            doc = copy.deepcopy(self.contract)
            doc["checks"][field] = False
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "regras"):
                self.check(contract=doc)

    def test_08_ch14_separate_engine_hall_cannot_be_skipped(self):
        for field in (
            "hall_of_fame_requires_separate_engine_confirmation",
            "physical_travel_requires_verified_source_map_and_arrival",
            "travel_without_verified_npc_context",
            "travel_does_not_use_league_as_install_proof",
            "native_hall_of_fame_verified",
            "native_events_installed",
            "can_install",
        ):
            doc = copy.deepcopy(self.story)
            doc[field] = not doc[field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "CH14"):
                self.check(story=doc)

    def test_09_source_import_must_stay_blocked(self):
        for field in ("imports_enabled", "gameplay_sinnoh_installed"):
            doc = copy.deepcopy(self.source)
            doc["import_control"][field] = True
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "fonte real"):
                self.check(source=doc)

    def test_10_unova_cannot_be_falsely_declared_playable(self):
        doc = copy.deepcopy(self.registry)
        doc["regions"]["UNOVA"]["status"] = "playable"
        with self.assertRaisesRegex(ValueError, "circuito"):
            self.check(registry=doc)
        doc = copy.deepcopy(self.registry)
        doc["circuit"].remove("HOENN")
        with self.assertRaisesRegex(ValueError, "circuito"):
            self.check(registry=doc)

    def test_11_inert_adapter_requires_real_npc_and_arrival(self):
        for token in (
            "BlueSinnohStoryContracts.league_cleared?(state)",
            "return :source_not_installed unless BlueRegionTravel.source_valid?(state)",
            "return :destination_not_installed unless valid_arrival?(point)",
            "return :npc_context_required unless npc_context.equal?(true)",
            "return :npc_context_unavailable unless BlueRegionTravel.available?(state)",
        ):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "adaptador"):
                self.check(adapter=self.adapter.replace(token, ""))

    def test_12_unverified_native_npc_registry_cannot_be_filled(self):
        modified = self.adapter.replace(
            "VERIFIED_NATIVE_DEPARTURES = {}.freeze",
            'VERIFIED_NATIVE_DEPARTURES = {"SINNOH" => "FAKE"}.freeze',
        )
        with self.assertRaisesRegex(ValueError, "adaptador|registro"):
            self.check(adapter=modified)

    def test_13_shared_engine_cannot_lose_local_key_item_storage(self):
        for token in (
            "def self.regional_item?(item)",
            "data.is_key_item? || data.is_HM?",
            "def self.stage_local_bag(state, destination)",
            'source_contents["pc_items"] = local_pc_contents(pc)',
            'next_state["region_key_items"][state["current"]] = source_items',
        ):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "motor de viagem"):
                self.check(travel=self.travel.replace(token, ""))

    def test_14_shared_engine_still_needs_physical_departure_and_npc(self):
        for token in (
            "def self.source_valid?(state)",
            'when "HOENN" then !!hoenn_installed?',
            "def self.at_departure_town?(state)",
            "return false unless @npc_event_context",
        ):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "motor de viagem"):
                self.check(travel=self.travel.replace(token, ""))

    def test_15_ch14_and_regions_cannot_remove_guards(self):
        for token in (
            "return :story_incomplete unless league_cleared?(state)",
            "return :source_not_installed unless BlueRegionTravel.source_valid?(state)",
            "hall_of_fame_verified.equal?(true)",
        ):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "CH14"):
                self.check(story_ruby=self.story_ruby.replace(token, ""))
        for token in ("available = circuit.dup",
                      'state["current"] == "SINNOH"',
                      "sinnoh_local_hms(state).include?(action)"):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "regra de viagem"):
                self.check(regions_ruby=self.regions_ruby.replace(token, ""))

    def test_16_synthetic_bag_pc_and_return_tests_mandatory(self):
        for token in (
            "SINNOH_S22_HOENN_UNOVA_NPC_ARRIVAL_LOCAL_ITEMS_NO_TELEPORT_OFFLINE_OK",
            'BlueRegionTravel.stage_local_bag(state, "HOENN")',
            'BlueRegionTravel.stage_local_bag(return_state, "SINNOH")',
            "Marshal.dump($PokemonGlobal.pcItemStorage)",
        ):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "fixture S22"):
                self.check(fixture=self.fixture.replace(token, ""))
        doc = copy.deepcopy(self.contract)
        doc["falsely_native_verified"] = True
        with self.assertRaisesRegex(ValueError, "campos inesperados"):
            self.check(contract=doc)


if __name__ == "__main__":
    unittest.main()
