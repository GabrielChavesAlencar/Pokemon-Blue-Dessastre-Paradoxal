"""Phase 08 topology and Ruby event contract. No map or game installation."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class JohtoPhase08ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = read_json("data/regions/johto-phase08.json")
        cls.previous = read_json("data/regions/johto-phase07.json")
        cls.source = read_json("data/regions/johto-source.json")
        cls.regions = read_json("site/public/data/regions.json")["regions"]
        cls.ruby = (ROOT / "scripts/regions/JohtoEcruteak.rb").read_text("utf-8")

    def test_route35_36_37_ecruteak_connects_to_goldenrod(self):
        expected = [
            "JOHTO_GOLDENROD_CITY", "JOHTO_ROUTE_35", "JOHTO_ROUTE_36",
            "JOHTO_ROUTE_37", "JOHTO_ECRUTEAK_CITY"
        ]
        self.assertEqual(self.current["region"], "JOHTO")
        self.assertEqual(self.current["phase"], "08/16")
        self.assertEqual(self.current["requires_completed_phase"], "07/16")
        self.assertEqual(self.current["entrance"], expected[0])
        self.assertEqual([x["key"] for x in self.current["corridor"]], expected)
        previous_nodes = self.previous["corridor"] + self.previous["required_interiors"]
        self.assertIn(expected[0], {x["key"] for x in previous_nodes})
        links = {(x["from"], x["to"]) for x in self.current["links"]}
        for start, end in zip(expected, expected[1:]):
            self.assertIn((start, end), links)
        all_nodes = self.current["corridor"] + self.current["required_interiors"]
        keys = [x["key"] for x in all_nodes]
        self.assertEqual(len(keys), len(set(keys)))
        for item in all_nodes:
            self.assertNotIn("map_id", item)
            self.assertNotIn("source_id", item)
            self.assertNotIn("coordinates", item)
        for edge in self.current["links"]:
            self.assertTrue(edge["two_way"])
            self.assertIn(edge["from"], keys)
            self.assertIn(edge["to"], keys)

    def test_national_park_towers_and_interiors_are_required_not_fabricated(self):
        interiors = {x["key"] for x in self.current["required_interiors"]}
        self.assertTrue({
            "JOHTO_NATIONAL_PARK", "JOHTO_ROUTE_36_SUDOWOODO",
            "JOHTO_ECRUTEAK_BURNED_TOWER_1F",
            "JOHTO_ECRUTEAK_BURNED_TOWER_B1F",
            "JOHTO_ECRUTEAK_DANCE_THEATER",
            "JOHTO_ECRUTEAK_GYM",
            "JOHTO_ECRUTEAK_POKEMON_CENTER",
            "JOHTO_ECRUTEAK_MART",
        }.issubset(interiors))
        self.assertTrue({
            "BUG_CATCHING_CONTEST", "RUINS_OF_ALPH", "MT_MORTAR",
            "BELL_TOWER_LEGENDARY_EVENTS",
        }.issubset(set(self.current["optional_not_implemented"])))

    def test_fog_and_surf_are_existing_local_badge_rules_not_global_emeralds(self):
        self.assertEqual(self.current["badge"], {
            "key": "FOG", "region": "JOHTO", "award_source": "BlueRegions.award",
            "max_awards_per_save": 1, "grants_field_action": "SURF"
        })
        johto = self.regions["JOHTO"]
        self.assertEqual(johto["milestones"][:4], ["ZEPHYR", "HIVE", "PLAIN", "FOG"])
        self.assertEqual(johto["field"]["SURF"]["badge"], "JOHTO:FOG")
        self.assertTrue(johto["field"]["SURF"]["tool"])
        self.assertIn('BlueRegions.award(state, REGION, BADGE)', self.ruby)
        self.assertIn('BlueRegions.field_access(state, REGION, "SURF", tool_ready)', self.ruby)
        self.assertIn('TrainerBattle.start(MORTY_TYPE, "Morty", 0)', self.ruby)

    def test_trainer_types_match_implemented_ruby_guards(self):
        trainers = self.current["trainer_requirements"]
        self.assertEqual([x["trainer_type"] for x in trainers[:3]], [
            "BLUE_JOHTO_BURNED_TOWER_RIVAL",
            "BLUE_JOHTO_DANCE_ROCKET",
            "BLUE_JOHTO_MORTY"
        ])
        self.assertEqual([x["versions"] for x in trainers[:3]], [[0, 1, 2], [0], [0]])
        for item in trainers[:3]:
            self.assertIn(":" + item["trainer_type"], self.ruby)
        self.assertFalse(trainers[3]["implemented"])
        self.assertIn("BLUE_JOHTO_ECRUTEAK_V1_READY", self.ruby)
        self.assertIn("BLUE_JOHTO_ECRUTEAK_SURF_V1_READY", self.ruby)

    def test_unverified_maps_and_items_cannot_be_marked_implemented(self):
        self.assertEqual(self.current["status"], "SPECIFICATION_ONLY_NOT_INSTALLED")
        self.assertFalse(self.current["integrated"])
        self.assertEqual(set(self.current["validation"].values()), {False})
        self.assertFalse(self.source["import_enabled"])
        self.assertTrue(self.source["mapping_verified"])
        self.assertEqual(len(self.source["maps"]), 74)
        self.assertEqual(self.source["maps"]["79"], "JOHTO_NEW_BARK_TOWN")
        self.assertEqual(self.source["maps"]["104"], "JOHTO_ROUTE_29")
        self.assertFalse(self.source["source"]["distribution_approved"])

        self.assertRegex(self.source["source"]["archive_sha256"], r"^[a-f0-9]{64}$")

if __name__ == "__main__":
    unittest.main()
