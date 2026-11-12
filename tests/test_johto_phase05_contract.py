"""Validate symbolic Violet corridor: never invent physical map IDs or install status."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoPhase05ContractTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / "data/regions/johto-phase05.json").read_text("utf-8"))
        self.registry = json.loads((ROOT / "site/public/data/regions.json").read_text("utf-8"))
        self.source = json.loads((ROOT / "data/regions/johto-source.json").read_text("utf-8"))

    def test_expected_corridor_has_two_way_connections_without_fake_map_ids(self):
        required = [
            "JOHTO_NEW_BARK_TOWN", "JOHTO_ROUTE_29", "JOHTO_CHERRYGROVE_CITY",
            "JOHTO_ROUTE_30", "JOHTO_ROUTE_31", "JOHTO_VIOLET_CITY"
        ]
        self.assertEqual([m["key"] for m in self.data["corridor"]], required)
        edges = {(x["from"], x["to"]) for x in self.data["links"] if x["two_way"]}
        self.assertEqual(len(edges), len(self.data["links"]))
        for first, second in zip(required, required[1:]):
            self.assertIn((first, second), edges)
        nodes = {row["key"] for row in self.data["corridor"] + self.data["additional_required"]}
        for edge in self.data["links"]:
            self.assertIn(edge["from"], nodes)
            self.assertIn(edge["to"], nodes)
        for row in self.data["corridor"] + self.data["additional_required"]:
            self.assertNotIn("map_id", row)
            self.assertNotIn("source_id", row)

    def test_violet_badge_uses_existing_johto_registry(self):
        self.assertEqual(self.data["region"], "JOHTO")
        self.assertEqual(self.data["phase"], "05/16")
        self.assertEqual(self.data["badge"]["key"], "ZEPHYR")
        self.assertEqual(self.data["badge"]["region"], "JOHTO")
        self.assertEqual(self.data["badge"]["max_awards_per_save"], 1)
        self.assertIn("ZEPHYR", self.registry["regions"]["JOHTO"]["milestones"])
        self.assertEqual(self.registry["regions"]["JOHTO"]["field"]["ROCK_SMASH"]["badge"],
                         "JOHTO:ZEPHYR")

    def test_trainer_ids_match_uninstalled_ruby_events(self):
        code = (ROOT / "scripts/regions/JohtoViolet.rb").read_text("utf-8")
        for item in self.data["trainer_requirements"]:
            self.assertIn(":" + item["trainer_type"], code)
            self.assertEqual(item["version"], 0)
        self.assertIn('BlueRegions.award(state, REGION, BADGE)', code)
        self.assertIn('TrainerBattle.start(FALKNER_TYPE, FALKNER_NAME, 0)', code)

    def test_prevent_premature_release_without_real_maps_and_qa(self):
        self.assertEqual(self.data["status"], "SPECIFICATION_ONLY_NOT_INSTALLED")
        self.assertFalse(self.data["integrated"])
        self.assertEqual(set(self.data["validation"].values()), {False})
        self.assertFalse(self.source["import_enabled"])
        self.assertFalse(self.source["mapping_verified"])
        self.assertEqual(self.source["maps"], {})


if __name__ == "__main__":
    unittest.main()
