"""Phase 10: symbolic Olivine/Jasmine plus still-blocked Whirl Islands contract."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class JohtoPhase10ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.phase = load("data/regions/johto-phase10.json")
        cls.previous = load("data/regions/johto-phase09.json")
        cls.source = load("data/regions/johto-source.json")
        cls.johto = load("site/public/data/regions.json")["regions"]["JOHTO"]
        cls.ruby = (ROOT / "scripts/regions/JohtoJasmine.rb").read_text(
            encoding="utf-8"
        )
        cls.phase09_ruby = (
            ROOT / "scripts/regions/JohtoOlivineCianwood.rb"
        ).read_text(encoding="utf-8")

    def test_phase_10_uses_existing_olivine_routes_and_lighthouse_without_fake_warps(self):
        self.assertEqual(self.phase["phase"], "10/16")
        self.assertEqual(self.phase["region"], "JOHTO")
        self.assertEqual(self.phase["requires_completed_phase"], "09/16")
        self.assertEqual(self.phase["entrance"], "JOHTO_OLIVINE_CITY")
        old = {x["key"] for x in self.previous["corridor"] +
               self.previous["required_interiors"]}
        nodes = [x["key"] for x in self.phase["return_corridor"]]
        self.assertTrue(set(nodes).issubset(old))
        self.assertEqual(len(nodes), len(set(nodes)))
        edge_set = {(x["from"], x["to"]) for x in self.phase["symbolic_links"]}
        for source, destination in edge_set:
            self.assertIn(source, nodes)
            self.assertIn(destination, nodes)
        for edge in self.phase["symbolic_links"]:
            self.assertTrue(edge["two_way"])
        self.assertNotIn(
            ("JOHTO_OLIVINE_LIGHTHOUSE_1F", "JOHTO_OLIVINE_LIGHTHOUSE_6F"),
            edge_set,
        )
        for node in self.phase["return_corridor"]:
            for forbidden in ("map_id", "source_id", "x", "y", "coordinates"):
                self.assertNotIn(forbidden, node)

    def test_ampharos_requires_prior_story_and_verified_item_removal(self):
        data = self.phase["item_consumption"]
        self.assertEqual(data["item_key"], "SECRETPOTION")
        self.assertEqual(data["status"], "CANDIDATE_UNVERIFIED")
        self.assertEqual(data["depends_on_phase"], "09/16")
        self.assertIn("quantity(item)", data["bag_api_requires"])
        self.assertIn("olivine_returned_with_medicine", data["preconditions"])
        self.assertIn("olivine_medicine_requested", data["preconditions"])
        self.assertIn("cianwood_medicine_received", data["preconditions"])
        self.assertIn('flags["olivine_medicine_delivered"] = true', self.ruby)
        self.assertIn('flags["olivine_ampharos_healed"] = true', self.ruby)
        self.assertIn("$bag.remove(item, 1)", self.ruby)
        self.assertIn("$bag.quantity(item) == quantity_before - 1", self.ruby)
        self.assertIn(
            "BlueJohtoOlivineCianwood::MEDICINE_ITEM", self.ruby
        )
        self.assertIn("MEDICINE_ITEM = :SECRETPOTION", self.phase09_ruby)
        self.assertIn("BLUE_JOHTO_AMPHAROS_CURE_V1_READY", self.ruby)

    def test_jasmine_mineral_is_sixth_badge_and_not_reused_by_kanto(self):
        self.assertEqual(
            self.johto["milestones"][:6],
            ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORM", "MINERAL"],
        )
        self.assertEqual(self.phase["badge"], {
            "key": "MINERAL",
            "region": "JOHTO",
            "ordinal": 6,
            "award_source": "BlueRegions.award",
            "max_awards_per_save": 1,
            "grants_field_action": None,
        })
        self.assertEqual(
            self.phase["jasmine"]["gym_ready_token"],
            "BLUE_JOHTO_JASMINE_V1_READY",
        )
        self.assertEqual(
            self.phase["trainer_requirements"][0]["trainer_type"],
            "BLUE_JOHTO_JASMINE",
        )
        self.assertIn('BlueRegions.award(state, REGION, BADGE)', self.ruby)
        self.assertIn('TrainerBattle.start(GYM_TRAINER, "Jasmine", 0)', self.ruby)
        self.assertNotIn('BlueRegions.award(state, REGION, "GLACIER")', self.ruby)

    def test_whirl_islands_and_lugia_remain_locked_even_if_glacier_is_awarded(self):
        islands = self.phase["whirl_islands"]
        self.assertEqual(islands["status"], "NOT_ENTERABLE_UNTIL_TRUE_MAP_AUDIT")
        self.assertEqual(islands["route41_portal"], "JOHTO_WHIRL_ISLANDS_GATE")
        self.assertIn(
            islands["route41_portal"],
            {x["key"] for x in self.previous["required_interiors"]},
        )
        self.assertEqual(len(islands["candidate_entrances"]), 4)
        self.assertEqual(islands["entrance_warps"], [])
        self.assertEqual(islands["exit_warps"], [])
        self.assertFalse(islands["all_entrances_verified"])
        self.assertFalse(islands["safe_return_verified"])
        self.assertFalse(islands["legendary_capture_enabled"])
        self.assertEqual(self.johto["field"]["WHIRLPOOL"]["badge"],
                         "JOHTO:GLACIER")
        self.assertIn(
            'BlueRegions.field_access(state, REGION, "WHIRLPOOL", tool_ready)',
            self.ruby,
        )
        self.assertIn("def self.whirl_islands_entry", self.ruby)

    def test_no_premature_acceptance_or_asset_guessing(self):
        self.assertEqual(self.phase["status"], "SPECIFICATION_ONLY_NOT_INSTALLED")
        self.assertFalse(self.phase["integrated"])
        self.assertEqual(set(self.phase["validation"].values()), {False})
        self.assertFalse(self.source["import_enabled"])
        self.assertFalse(self.source["mapping_verified"])
        self.assertEqual(self.source["maps"], {})
        self.assertIsNone(self.source["source"]["archive_sha256"])
        self.assertIn("LUGIA_ENCOUNTER", self.phase["future_not_implemented"])
        self.assertIn("JASMINE_PBS_TEAMS", self.phase["future_not_implemented"])


if __name__ == "__main__":
    unittest.main()
