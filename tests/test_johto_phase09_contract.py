"""Phase 09 symbolic geography, story gates and STORM/Fly contracts."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


class JohtoPhase09ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = read_json("data/regions/johto-phase09.json")
        cls.previous = read_json("data/regions/johto-phase08.json")
        cls.source = read_json("data/regions/johto-source.json")
        cls.region = read_json("site/public/data/regions.json")["regions"]["JOHTO"]
        cls.script = (ROOT / "scripts/regions/JohtoOlivineCianwood.rb").read_text(
            encoding="utf-8"
        )

    def test_contiguous_ecruteak_route38_route39_olivine_route40_41_cianwood(self):
        expected = [
            "JOHTO_ECRUTEAK_CITY", "JOHTO_ROUTE_38_GATE", "JOHTO_ROUTE_38",
            "JOHTO_ROUTE_39", "JOHTO_OLIVINE_CITY",
            "JOHTO_ROUTE_40", "JOHTO_ROUTE_41", "JOHTO_CIANWOOD_CITY"
        ]
        self.assertEqual(self.current["region"], "JOHTO")
        self.assertEqual(self.current["phase"], "09/16")
        self.assertEqual(self.current["requires_completed_phase"], "08/16")
        self.assertEqual(self.current["entrance"], expected[0])
        self.assertEqual([x["key"] for x in self.current["corridor"]], expected)
        older = {x["key"] for x in self.previous["corridor"] +
                 self.previous["required_interiors"]}
        self.assertIn("JOHTO_ECRUTEAK_CITY", older)
        self.assertIn("JOHTO_ROUTE_38_GATE", older)
        nodes = self.current["corridor"] + self.current["required_interiors"]
        keys = [x["key"] for x in nodes]
        self.assertEqual(len(keys), len(set(keys)))
        edges = {(x["from"], x["to"]) for x in self.current["links"]}
        for first, second in zip(expected, expected[1:]):
            self.assertIn((first, second), edges)
        for edge in self.current["links"]:
            self.assertTrue(edge["two_way"])
            self.assertEqual(edge["kind"], "symbolic_only_no_warp")
            self.assertIn(edge["from"], keys)
            self.assertIn(edge["to"], keys)
        for item in nodes:
            for forbidden in ("map_id", "source_id", "coordinates", "x", "y"):
                self.assertNotIn(forbidden, item)

    def test_lighthouse_six_floors_gym_pharmacy_and_ocean_all_required(self):
        interior = {x["key"] for x in self.current["required_interiors"]}
        for floor in range(1, 7):
            self.assertIn(f"JOHTO_OLIVINE_LIGHTHOUSE_{floor}F", interior)
        self.assertTrue({
            "JOHTO_CIANWOOD_PHARMACY", "JOHTO_CIANWOOD_GYM",
            "JOHTO_CIANWOOD_CHUCK_WIFE", "JOHTO_CIANWOOD_POKEMON_CENTER",
            "JOHTO_OLIVINE_GYM", "JOHTO_ROUTE_39_MOOMOO_FARM",
            "JOHTO_WHIRL_ISLANDS_GATE", "JOHTO_OLIVINE_PORT"
        }.issubset(interior))
        links = {(x["from"], x["to"]) for x in self.current["links"]}
        for floor in range(1, 6):
            self.assertIn((f"JOHTO_OLIVINE_LIGHTHOUSE_{floor}F",
                           f"JOHTO_OLIVINE_LIGHTHOUSE_{floor+1}F"), links)

    def test_chuck_storm_uses_regional_badge_fly_and_single_reward(self):
        self.assertEqual(
            self.region["milestones"][:5],
            ["ZEPHYR", "HIVE", "PLAIN", "FOG", "STORM"]
        )
        self.assertEqual(self.region["field"]["FLY"]["badge"], "JOHTO:STORM")
        self.assertTrue(self.region["field"]["FLY"]["tool"])
        self.assertEqual(self.current["badge"], {
            "key": "STORM", "region": "JOHTO",
            "award_source": "BlueRegions.award", "max_awards_per_save": 1,
            "grants_field_action": "FLY"
        })
        self.assertIn('BlueRegions.award(state, REGION, BADGE)', self.script)
        self.assertIn('BlueRegions.field_access(state, REGION, "FLY", tool_ready)',
                      self.script)
        self.assertIn('BlueRegions.field_access(state, REGION, "SURF", tool_ready)',
                      self.script)
        self.assertIn('TrainerBattle.start(CHUCK_TRAINER, "Chuck", 0)', self.script)
        self.assertIn('BLUE_JOHTO_CIANWOOD_V1_READY', self.script)
        self.assertIn('BLUE_JOHTO_MEDICINE_V1_READY', self.script)
        self.assertIn('BLUE_JOHTO_FLY_V1_READY', self.script)

    def test_only_chuck_event_defined_and_future_pbs_not_compiled(self):
        trainers = self.current["trainer_requirements"]
        self.assertEqual(trainers[0]["trainer_type"], "BLUE_JOHTO_CHUCK")
        self.assertEqual(trainers[0]["versions"], [0])
        self.assertEqual(trainers[0]["implemented"], "ruby_gate_only_no_pbs")
        self.assertIn(":BLUE_JOHTO_CHUCK", self.script)
        self.assertTrue(all(x["implemented"] is False for x in trainers[1:]))
        self.assertIn("OLIVINE_JASMINE_BATTLE",
                      self.current["future_not_implemented"])
        self.assertIn("AMPHAROS_CURE",
                      self.current["future_not_implemented"])
        self.assertNotIn('BlueRegions.award(state, REGION, "MINERAL")', self.script)
        self.assertIn('flags["cianwood_medicine_received"] = true', self.script)
        self.assertNotIn('flags["olivine_ampharos_healed"] = true', self.script)

    def test_unverified_items_and_maps_do_not_satisfy_gameplay_acceptance(self):
        self.assertEqual([x["key"] for x in self.current["items"]],
                         ["SECRETPOTION", "HM02"])
        self.assertTrue(all(x["status"] == "CANDIDATE_UNVERIFIED"
                            for x in self.current["items"]))
        self.assertEqual(self.current["status"],
                         "SPECIFICATION_ONLY_NOT_INSTALLED")
        self.assertFalse(self.current["integrated"])
        self.assertEqual(set(self.current["validation"].values()), {False})
        self.assertFalse(self.source["import_enabled"])
        self.assertFalse(self.source["mapping_verified"])
        self.assertEqual(self.source["maps"], {})
        self.assertIsNone(self.source["source"]["archive_sha256"])


if __name__ == "__main__":
    unittest.main()
