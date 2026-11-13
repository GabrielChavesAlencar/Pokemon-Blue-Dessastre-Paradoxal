"""Johto phase 13 geography/League contract: symbolic, never playable maps."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class JohtoPhase13ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = load("data/regions/johto-phase13.json")
        cls.previous = load("data/regions/johto-phase12.json")
        cls.source = load("data/regions/johto-source.json")
        cls.registry = load("site/public/data/regions.json")
        cls.script = (ROOT / "scripts/regions/JohtoLeague.rb").read_text(
            encoding="utf-8"
        )
        cls.regions_runtime = (
            ROOT / "scripts/battle_polish/Regions.rb"
        ).read_text(encoding="utf-8")
        cls.travel_runtime = (
            ROOT / "scripts/battle_polish/RegionTravel.rb"
        ).read_text(encoding="utf-8")

    def test_eight_badges_to_new_bark_route27_tohjo_route26_indigo(self):
        expected = [
            "JOHTO_NEW_BARK_TOWN", "JOHTO_ROUTE_27",
            "JOHTO_TOHJO_FALLS_ENTRANCE", "JOHTO_TOHJO_FALLS_INTERIOR",
            "JOHTO_ROUTE_26", "JOHTO_VICTORY_ROAD_ENTRANCE",
            "JOHTO_VICTORY_ROAD", "JOHTO_INDIGO_PLATEAU"
        ]
        self.assertEqual(self.phase["phase"], "13/16")
        self.assertEqual(self.phase["requires_completed_phase"], "12/16")
        self.assertEqual(self.phase["entrance"], expected[0])
        self.assertEqual([x["key"] for x in self.phase["corridor"]], expected)
        self.assertEqual(
            self.previous["league_handoff"]["status"],
            "PREVIEW_ONLY_NOT_TRAVEL",
        )
        self.assertEqual(
            self.previous["league_handoff"]["requires"],
            self.registry["regions"]["JOHTO"]["milestones"],
        )
        nodes = self.phase["corridor"] + self.phase["required_interiors"]
        keys = [x["key"] for x in nodes]
        self.assertEqual(len(keys), len(set(keys)))
        edges = {(x["from"], x["to"]) for x in self.phase["links"]}
        for start, end in zip(expected, expected[1:]):
            self.assertIn((start, end), edges)
        for edge in self.phase["links"]:
            self.assertEqual(edge["kind"], "symbolic_only_no_warp")
            self.assertIn(edge["from"], keys)
            self.assertIn(edge["to"], keys)
        for node in nodes:
            for invalid in ("map_id", "source_id", "coordinates", "x", "y"):
                self.assertNotIn(invalid, node)

    def test_elite_four_order_and_hall_of_fame_is_johto_only(self):
        req = self.phase["trainer_requirements"]
        self.assertEqual([x["trainer_type"] for x in req], [
            "BLUE_JOHTO_VICTORY_ROAD_RIVAL",
            "BLUE_JOHTO_ELITE_WILL",
            "BLUE_JOHTO_ELITE_KOGA",
            "BLUE_JOHTO_ELITE_BRUNO",
            "BLUE_JOHTO_ELITE_KAREN",
            "BLUE_JOHTO_CHAMPION_LANCE"
        ])
        self.assertEqual(req[0]["versions"], [0, 1, 2])
        self.assertTrue(all(x["compiled"] is False for x in req))
        for item in req:
            self.assertIn(":" + item["trainer_type"], self.script)
        self.assertIn("TrainerBattle.start(type, name, 0)", self.script)
        self.assertIn('TrainerBattle.start(CHAMPION, "Lance", 0)', self.script)
        self.assertIn('flags["johto_league_step"] = number + 1', self.script)
        self.assertIn("def self.reset_challenge", self.script)
        self.assertIn("def self.hall_of_fame_result(result)", self.script)
        self.assertIn("result == :recorded", self.script)
        self.assertIn("BlueRegions.complete_league(state, REGION)", self.script)
        self.assertIn('state["leagues"] << region', self.regions_runtime)
        self.assertNotIn("pbHallOfFame", self.script)
        self.assertNotIn("pbStartOver", self.script)

    def test_kanto_hoenn_unlock_only_in_state_not_transport(self):
        completion = self.phase["regional_completion"]
        self.assertEqual(completion["completed_entry"], "JOHTO")
        self.assertEqual(completion["unlocks_in_state"], ["KANTO", "HOENN"])
        self.assertEqual(
            completion["method"], "BlueRegions.complete_league(state, JOHTO)"
        )
        self.assertFalse(completion["native_kanto_league_switches_touched"])
        self.assertFalse(completion["native_badges_changed"])
        self.assertEqual(completion["new_badges_added"], 0)
        self.assertFalse(completion["playable_transport_hoenn"])
        self.assertFalse(completion["return_to_new_bark_implemented"])
        self.assertFalse(completion["travel_adapter_supports_johto_currently"])
        self.assertTrue('when "KANTO"' in self.travel_runtime)
        self.assertTrue('when "DECADES"' in self.travel_runtime)
        self.assertIn('source_valid?(state) && %w[DECADES KANTO]', self.travel_runtime)
        self.assertIn('BlueRegions.unlocked(state) & ["KANTO", "HOENN"]',
                      self.script)

    def test_unverified_markers_and_maps_remain_blocked(self):
        self.assertEqual(self.phase["status"], "SPECIFICATION_ONLY_NOT_INSTALLED")
        self.assertFalse(self.phase["integrated"])
        self.assertEqual(set(self.phase["validation"].values()), {False})
        self.assertEqual(len(self.phase["readiness_markers"]), 4)
        self.assertTrue(all(not x["installed"] for x in
                            self.phase["readiness_markers"]))
        for m in self.phase["readiness_markers"]:
            self.assertIn(m["token"], self.script)
        self.assertEqual(self.source["maps"], {})
        self.assertFalse(self.source["mapping_verified"])
        self.assertFalse(self.source["import_enabled"])
        self.assertIsNone(self.source["source"]["archive_sha256"])
        self.assertTrue({
            "JOHTO_NATIVE_HOF_ANIMATION_AND_SAVE",
            "JOHTO_POST_LEAGUE_NEW_BARK_NPC",
            "HOENN_MAPS_AND_TRAVEL",
        }.issubset(set(self.phase["future_not_implemented"])))


if __name__ == "__main__":
    unittest.main()
