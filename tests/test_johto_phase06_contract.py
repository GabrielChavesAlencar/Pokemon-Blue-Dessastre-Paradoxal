"""Johto phase 06 graph and gating contract; these are not executable maps."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class JohtoPhase06ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = json.loads((ROOT / "data/regions/johto-phase06.json").read_text("utf-8"))
        cls.previous = json.loads((ROOT / "data/regions/johto-phase05.json").read_text("utf-8"))
        cls.registry = json.loads((ROOT / "site/public/data/regions.json").read_text("utf-8"))
        cls.azalea_ruby = (ROOT / "scripts/regions/JohtoAzalea.rb").read_text("utf-8")

    def test_real_world_path_is_symbolic_and_connected_to_violet(self):
        self.assertEqual(self.phase["phase"], "06/16")
        self.assertEqual(self.phase["region"], "JOHTO")
        expected = ["JOHTO_VIOLET_CITY", "JOHTO_ROUTE_32",
                    "JOHTO_UNION_CAVE_1F", "JOHTO_ROUTE_33",
                    "JOHTO_AZALEA_TOWN"]
        self.assertEqual([row["key"] for row in self.phase["corridor"]], expected)
        self.assertEqual(expected[0], self.phase["entrance"])
        prev = {row["key"] for row in self.previous["corridor"]}
        self.assertIn(self.phase["entrance"], prev)
        edges = {(edge["from"], edge["to"]) for edge in self.phase["links"]}
        self.assertTrue(all(edge["two_way"] is True for edge in self.phase["links"]))
        for start, end in zip(expected, expected[1:]):
            self.assertIn((start, end), edges)
        nodes = {row["key"] for row in self.phase["corridor"] + self.phase["required_interiors"]}
        for edge in self.phase["links"]:
            self.assertIn(edge["from"], nodes)
            self.assertIn(edge["to"], nodes)
        for row in self.phase["corridor"] + self.phase["required_interiors"]:
            self.assertNotIn("map_id", row)
            self.assertNotIn("source_id", row)
            self.assertNotIn("x", row)
            self.assertNotIn("y", row)

    def test_town_well_cave_kurt_bugsy_and_ilex_gate_all_required(self):
        required = {
            "JOHTO_UNION_CAVE_B1F", "JOHTO_AZALEA_SLOWPOKE_WELL",
            "JOHTO_AZALEA_SLOWPOKE_WELL_B1F",
            "JOHTO_AZALEA_KURT_HOUSE", "JOHTO_AZALEA_GYM",
            "JOHTO_AZALEA_POKEMON_CENTER", "JOHTO_AZALEA_MART",
            "JOHTO_ILEX_FOREST_GATE", "JOHTO_ROUTE_32_POKEMON_CENTER"
        }
        self.assertEqual({x["key"] for x in self.phase["required_interiors"]}, required)
        self.assertTrue(self.phase["story_requirements"])

    def test_hive_uses_shared_regional_badge_and_cut_not_an_independent_badge(self):
        badge = self.phase["badge"]
        self.assertEqual(badge["key"], "HIVE")
        self.assertEqual(badge["region"], "JOHTO")
        self.assertEqual(badge["award_source"], "BlueRegions.award")
        self.assertEqual(badge["max_awards_per_save"], 1)
        self.assertEqual(badge["grants_field_action"], "CUT")
        self.assertEqual(
            self.registry["regions"]["JOHTO"]["milestones"][:2], ["ZEPHYR", "HIVE"]
        )
        self.assertEqual(
            self.registry["regions"]["JOHTO"]["field"]["CUT"]["badge"], "JOHTO:HIVE"
        )
        self.assertIn('BlueRegions.award(state, REGION, BADGE)', self.azalea_ruby)
        self.assertIn('BlueRegions.field_access(state, REGION, "CUT", tool_ready)', self.azalea_ruby)

    def test_trainer_requirements_match_ruby_types_and_version_guards(self):
        expected = {
            "BLUE_JOHTO_ROCKET_GRUNT": [0, 1],
            "BLUE_JOHTO_ROCKET_PROTON": [0],
            "BLUE_JOHTO_BUGSY": [0],
            "BLUE_JOHTO_AZALEA_RIVAL": [0, 1, 2]
        }
        self.assertEqual(
            {v["trainer_type"]: v["versions"] for v in self.phase["trainer_requirements"]},
            expected
        )
        for name in expected:
            self.assertIn(":" + name, self.azalea_ruby)
        self.assertIn("TrainerBattle.start(GRUNT_TYPE", self.azalea_ruby)
        self.assertIn("TrainerBattle.start(EXECUTIVE_TYPE", self.azalea_ruby)
        self.assertIn("TrainerBattle.start(BUGSY_TYPE", self.azalea_ruby)
        self.assertIn("TrainerBattle.start(RIVAL_TYPE", self.azalea_ruby)

    def test_cannot_pass_real_integration_with_unverified_assets(self):
        self.assertEqual(self.phase["status"], "SPECIFICATION_ONLY_NOT_INSTALLED")
        self.assertEqual(self.phase["requires_completed_phase"], "05/16")
        self.assertFalse(self.phase["integrated"])
        self.assertEqual(set(self.phase["validation"].values()), {False})
        self.assertIn("Data/blue-johto-azalea-ready.txt", self.azalea_ruby)
        self.assertIn("BLUE_JOHTO_AZALEA_V1_READY", self.azalea_ruby)


if __name__ == "__main__":
    unittest.main()
