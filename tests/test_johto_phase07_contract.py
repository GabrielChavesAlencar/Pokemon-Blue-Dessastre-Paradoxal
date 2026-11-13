"""Symbolic Goldenrod route / Whitney quest contract (no playable-map claims)."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class JohtoPhase07ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = load("data/regions/johto-phase07.json")
        cls.previous = load("data/regions/johto-phase06.json")
        cls.registry = load("site/public/data/regions.json")["regions"]["JOHTO"]
        cls.source = load("data/regions/johto-source.json")
        cls.runtime = (ROOT / "scripts/regions/JohtoGoldenrod.rb").read_text("utf-8")

    def test_symbolic_ilex_route34_goldenrod_connect_to_azalea(self):
        self.assertEqual(self.current["phase"], "07/16")
        self.assertEqual(self.current["requires_completed_phase"], "06/16")
        expected = [
            "JOHTO_AZALEA_TOWN", "JOHTO_ILEX_FOREST_GATE",
            "JOHTO_ILEX_FOREST", "JOHTO_ROUTE_34", "JOHTO_GOLDENROD_CITY"
        ]
        self.assertEqual([row["key"] for row in self.current["corridor"]], expected)
        previous = {row["key"] for row in self.previous["corridor"] +
                    self.previous["required_interiors"]}
        self.assertIn("JOHTO_AZALEA_TOWN", previous)
        self.assertIn("JOHTO_ILEX_FOREST_GATE", previous)
        links = {(row["from"], row["to"]) for row in self.current["links"]}
        for source, destination in zip(expected, expected[1:]):
            self.assertIn((source, destination), links)
        nodes = self.current["corridor"] + self.current["required_interiors"]
        keys = [row["key"] for row in nodes]
        self.assertEqual(len(keys), len(set(keys)))
        for row in nodes:
            self.assertNotIn("map_id", row)
            self.assertNotIn("source_id", row)
            self.assertNotIn("coordinates", row)
        for row in self.current["links"]:
            self.assertTrue(row["two_way"])
            self.assertIn(row["from"], keys)
            self.assertIn(row["to"], keys)

    def test_mandatory_scenarios_and_previews_are_defined(self):
        interiors = {x["key"] for x in self.current["required_interiors"]}
        self.assertTrue({
            "JOHTO_ILEX_FOREST_SHRINE", "JOHTO_ROUTE_34_DAY_CARE",
            "JOHTO_GOLDENROD_GYM", "JOHTO_GOLDENROD_RADIO_TOWER",
            "JOHTO_GOLDENROD_DEPARTMENT_STORE", "JOHTO_GOLDENROD_BIKE_SHOP",
            "JOHTO_GOLDENROD_UNDERGROUND_NORTH",
            "JOHTO_GOLDENROD_UNDERGROUND_SOUTH",
            "JOHTO_GOLDENROD_FLOWER_SHOP",
        }.issubset(interiors))
        self.assertGreaterEqual(len(self.current["story_requirements"]), 10)
        self.assertFalse(self.current["integrated"])
        self.assertEqual(self.current["status"], "SPECIFICATION_ONLY_NOT_INSTALLED")
        self.assertEqual(set(self.current["validation"].values()), {False})

    def test_whitney_plain_badge_uses_existing_johto_registry_once(self):
        self.assertEqual(self.registry["status"], "planned")
        self.assertEqual(self.registry["milestones"][:3], ["ZEPHYR", "HIVE", "PLAIN"])
        self.assertEqual(self.registry["field"]["STRENGTH"]["badge"], "JOHTO:PLAIN")
        self.assertEqual(self.current["badge"], {
            "key": "PLAIN",
            "region": "JOHTO",
            "award_source": "BlueRegions.award",
            "max_awards_per_save": 1,
            "grants_field_action": "STRENGTH"
        })
        self.assertIn('BlueRegions.award(state, REGION, BADGE)', self.runtime)
        self.assertIn('BlueRegions.field_access(state, REGION, "STRENGTH", tool_ready)',
                      self.runtime)
        self.assertIn('TrainerBattle.start(GYM_TRAINER, "Whitney", 0)', self.runtime)

    def test_future_trainer_ids_are_not_marked_installed(self):
        trainers = self.current["trainer_requirements"]
        self.assertEqual(trainers[0]["trainer_type"], "BLUE_JOHTO_WHITNEY")
        self.assertEqual(trainers[0]["versions"], [0])
        self.assertEqual(trainers[0]["name"], "Whitney")
        self.assertIn(":BLUE_JOHTO_WHITNEY", self.runtime)
        for entry in trainers[1:]:
            self.assertFalse(entry["implemented"])
        self.assertIn("BLUE_JOHTO_GOLDENROD_V1_READY", self.runtime)
        self.assertIn("BLUE_JOHTO_ILEX_CUT_V1_READY", self.runtime)
        self.assertIn("BLUE_JOHTO_FLOWER_SHOP_V1_READY", self.runtime)
        self.assertIn("BLUE_JOHTO_SUDOWOODO_V1_READY", self.runtime)

    def test_johto_remains_uninstalled_and_source_missing(self):
        self.assertFalse(self.source["import_enabled"])
        self.assertTrue(self.source["mapping_verified"])
        self.assertEqual(len(self.source["maps"]), 74)
        self.assertEqual(self.source["maps"]["79"], "JOHTO_NEW_BARK_TOWN")
        self.assertEqual(self.source["maps"]["104"], "JOHTO_ROUTE_29")
        self.assertFalse(self.source["source"]["distribution_approved"])

        self.assertRegex(self.source["source"]["archive_sha256"], r"^[a-f0-9]{64}$")
        self.assertFalse(self.current["integrated"])

if __name__ == "__main__":
    unittest.main()
