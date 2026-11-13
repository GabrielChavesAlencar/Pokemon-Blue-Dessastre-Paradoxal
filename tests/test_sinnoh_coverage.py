"""Check Sinnoh's symbolic coverage stays a plan, never fake imported maps."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SinnohCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scope = json.loads((ROOT / "data/regions/sinnoh-coverage.json").read_text("utf-8"))
        cls.registry = json.loads((ROOT / "site/public/data/regions.json").read_text("utf-8"))
        cls.source = json.loads((ROOT / "data/regions/sinnoh-source.json").read_text("utf-8"))

    def test_plan_is_not_a_playable_installed_region(self):
        self.assertEqual(self.scope["status"], "PLANNED_AUDIT_CHECKLIST_ONLY")
        self.assertEqual(self.registry["regions"]["SINNOH"]["status"], "planned")
        self.assertFalse(self.source["import_control"]["imports_enabled"])
        self.assertFalse(self.source["import_control"]["public_assets_allowed"])
        self.assertEqual(self.source["progress"]["technical_approved"], 0)
        self.assertEqual(self.source["progress"]["native_playable_approved"], 0)

    def test_badge_order_and_field_rules_match_registry(self):
        badges = self.scope["badges"]
        self.assertEqual([x["key"] for x in badges],
                         self.registry["regions"]["SINNOH"]["milestones"])
        fields = self.registry["regions"]["SINNOH"]["field"]
        for item in badges:
            self.assertEqual(fields[item["field"]]["badge"], "SINNOH:" + item["key"])
        self.assertEqual(fields["DEFOG"]["badge"], "SINNOH:RELIC")
        self.assertEqual(fields["SURF"]["badge"], "SINNOH:FEN")

    def test_all_areas_are_symbolic_and_unverified(self):
        self.assertEqual([stage["phase"] for stage in self.scope["phases"]], list(range(3, 11)))
        areas = [area for phase in self.scope["phases"] for area in phase["areas"]]
        events = [event for phase in self.scope["phases"] for event in phase["events"]]
        self.assertEqual(len(areas), len({x["symbol"] for x in areas}))
        self.assertEqual(len(events), len({x["key"] for x in events}))
        self.assertGreaterEqual(len(areas), 60)
        self.assertGreaterEqual(len(events), 30)
        for area in areas:
            self.assertEqual(area["source_map_ids"], [])
            self.assertEqual(area["destination_map_ids"], [])
            self.assertIs(area["verified"], False)
        for event in events:
            self.assertIs(event["verified"], False)
        names = {area["label"] for area in areas}
        self.assertTrue({"Twinleaf Town", "Distortion World", "Champion Cynthia Chamber"} <= names)

    def test_league_contract_and_combat_engine_remain_unchanged(self):
        self.assertEqual(self.scope["main_engine"], "Blue/Decades")
        self.assertEqual(self.scope["elite_four"], ["Aaron", "Bertha", "Flint", "Lucian"])
        self.assertEqual(self.scope["champion"], "Cynthia")
        circuit = self.registry["circuit"]
        index = circuit.index("SINNOH")
        self.assertEqual([circuit[index - 1], circuit[index + 1]], ["HOENN", "UNOVA"])


if __name__ == "__main__":
    unittest.main()
