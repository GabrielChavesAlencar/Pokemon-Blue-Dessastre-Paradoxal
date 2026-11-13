"""Phase 11 Mahogany symbolic geography and gates; no playable map claims."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


class JohtoPhase11ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = load("data/regions/johto-phase11.json")
        cls.previous = load("data/regions/johto-phase10.json")
        cls.source = load("data/regions/johto-source.json")
        cls.region = load("site/public/data/regions.json")["regions"]["JOHTO"]
        cls.code = (ROOT / "scripts/regions/JohtoMahogany.rb").read_text(
            encoding="utf-8"
        )

    def test_mahogany_lake_of_rage_and_route44_all_symbolic(self):
        contract = self.current
        self.assertEqual(contract["region"], "JOHTO")
        self.assertEqual(contract["phase"], "11/16")
        self.assertEqual(contract["requires_completed_phase"], "10/16")
        expected = [
            "JOHTO_ECRUTEAK_CITY", "JOHTO_ROUTE_42",
            "JOHTO_MAHOGANY_TOWN", "JOHTO_ROUTE_43", "JOHTO_LAKE_OF_RAGE"
        ]
        self.assertEqual([x["key"] for x in contract["corridor"]], expected)
        self.assertEqual(contract["entrance"], expected[0])
        # Ecruteak was present in phase 09, which phase 10 returns to Olivine.
        phase09 = load("data/regions/johto-phase09.json")
        self.assertIn(expected[0], {x["key"] for x in phase09["corridor"]})
        keys = [x["key"] for x in
                contract["corridor"] + contract["required_interiors"]]
        self.assertEqual(len(set(keys)), len(keys))
        graph = {(x["from"], x["to"]) for x in contract["links"]}
        for a, b in zip(expected, expected[1:]):
            self.assertIn((a, b), graph)
        for link in contract["links"]:
            self.assertEqual(link["kind"], "symbolic_only_no_warp")
            self.assertTrue(link["two_way"])
            self.assertIn(link["from"], keys)
            self.assertIn(link["to"], keys)
        for node in contract["corridor"] + contract["required_interiors"]:
            for name in ("map_id", "source_id", "x", "y", "coordinates"):
                self.assertNotIn(name, node)

    def test_rocket_hq_radio_tower_and_ice_gym_exist_in_plan_only(self):
        nodes = {x["key"] for x in self.current["required_interiors"]}
        self.assertTrue({
            "JOHTO_MAHOGANY_GYM", "JOHTO_MAHOGANY_ROCKET_SHOP",
            "JOHTO_ROCKET_HQ_B1F", "JOHTO_ROCKET_HQ_B2F",
            "JOHTO_ROCKET_HQ_B3F", "JOHTO_GOLDENROD_RADIO_TOWER",
            "JOHTO_GOLDENROD_RADIO_TOWER_5F",
            "JOHTO_GOLDENROD_UNDERGROUND_WAREHOUSE",
            "JOHTO_ROUTE_44_GATE",
        }.issubset(nodes))
        self.assertGreaterEqual(len(self.current["story_requirements"]), 14)
        self.assertTrue(self.current["future_not_installed"])
        self.assertFalse(self.current["integrated"])

    def test_pryce_glacier_is_seventh_badge_and_whirlpool_needs_glacier(self):
        badge = self.current["badge"]
        self.assertEqual(badge, {
            "key": "GLACIER", "region": "JOHTO", "ordinal": 7,
            "award_source": "BlueRegions.award",
            "max_awards_per_save": 1,
            "grants_field_action": "WHIRLPOOL"
        })
        self.assertEqual(
            self.region["milestones"][:7],
            ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORM",
             "MINERAL", "GLACIER"]
        )
        self.assertEqual(self.region["field"]["WHIRLPOOL"]["badge"],
                         "JOHTO:GLACIER")
        self.assertTrue(self.region["field"]["WHIRLPOOL"]["tool"])
        self.assertIn('BlueRegions.award(state, REGION, BADGE)', self.code)
        self.assertIn(
            'BlueRegions.field_access(state, REGION, "WHIRLPOOL", tool_ready)',
            self.code,
        )
        self.assertIn('TrainerBattle.start(kind, name, version)', self.code)

    def test_battles_require_audited_items_events_and_pbs(self):
        self.assertEqual(len(self.current["species_events"]), 2)
        self.assertEqual(
            {x["species"] for x in self.current["species_events"]},
            {"GYARADOS", "ELECTRODE"}
        )
        self.assertTrue(all(x["requires_audited_battle_result"]
                            for x in self.current["species_events"]))
        self.assertEqual({x["key"] for x in self.current["items"]},
                         {"REDSCALE", "HM06"})
        self.assertTrue(all(x["status"] == "CANDIDATE_UNVERIFIED"
                            for x in self.current["items"]))
        self.assertTrue(all(not x["compiled"]
                            for x in self.current["trainer_requirements"]))
        for entry in self.current["trainer_requirements"]:
            self.assertIn(":" + entry["trainer_type"], self.code)
        self.assertIn('[:caught, :defeated].include?(result)', self.code)
        self.assertIn("BLUE_JOHTO_ROCKET_HQ_V1_READY", self.code)
        self.assertIn("BLUE_JOHTO_PRYCE_V1_READY", self.code)
        self.assertIn("BLUE_JOHTO_RADIO_TOWER_V1_READY", self.code)

    def test_unverified_source_cannot_enable_maps_or_lugia(self):
        self.assertEqual(self.current["status"],
                         "SPECIFICATION_ONLY_NOT_INSTALLED")
        self.assertFalse(self.current["integrated"])
        self.assertEqual(set(self.current["validation"].values()), {False})
        self.assertFalse(self.source["import_enabled"])
        self.assertFalse(self.source["mapping_verified"])
        self.assertEqual(self.source["maps"], {})
        self.assertIsNone(self.source["source"]["archive_sha256"])
        self.assertIn("WHIRL_ISLANDS_AND_LUGIA",
                      self.current["future_not_installed"])
        self.assertIn("CARD_KEY_AND_BASEMENT_KEY_ITEMS",
                      self.current["future_not_installed"])


if __name__ == "__main__":
    unittest.main()
