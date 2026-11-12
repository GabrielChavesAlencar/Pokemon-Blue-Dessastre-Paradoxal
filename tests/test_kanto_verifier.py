"""Pure graph and guard tests for the read-only Kanto pilot audit."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

REGIONS = Path(__file__).resolve().parents[1] / "scripts" / "regions"
sys.path.insert(0, str(REGIONS))
try:
    from verify_pilot import reachable
    from pilot import PILOT_META, build_signature, pilot_is_current
    from audit import PILOT_V1_SOURCE_IDS, stable_source_order
finally:
    sys.path.remove(str(REGIONS))


class KantoPilotAuditTests(unittest.TestCase):
    def test_phase08_preserves_all_previous_25_map_slots(self):
        root = REGIONS.parents[1]
        manifest = json.loads((root / "data/regions/kanto-source.json").read_text("utf-8"))
        order = stable_source_order({int(k) for k in manifest["maps"]})
        self.assertEqual(len(order), 40)
        self.assertEqual(tuple(order[:13]), PILOT_V1_SOURCE_IDS)
        self.assertEqual(len(set(order)), 40)
        self.assertEqual(order[13:25], [26,27,32,33,34,36,37,38,39,40,41,42])
        self.assertEqual(order[25:], [56,59,60,61,63,64,65,66,67,72,74,75,76,77,78])
        self.assertIn(42, order[13:])

    def test_portal_matches_audited_cerulean_roster(self):
        root = REGIONS.parents[1]
        data = json.loads((root / "site/public/data/kanto.json").read_text("utf-8"))
        self.assertEqual(len(data["locations"]), 40)
        self.assertGreaterEqual(len(data["trainers"]), 54)
        misty = next(t for t in data["trainers"] if t["id"] == "kanto-misty")
        self.assertTrue(misty["leader"])
        self.assertEqual(misty["location"], "kanto-cerulean-gym")
        self.assertEqual(
            [(p["species"], p["level"]) for p in misty["variants"][0]["team"]],
            [("STARYU", 18), ("STARMIE", 21)]
        )
        surge = next(t for t in data["trainers"] if t["id"] == "kanto-lt. surge")
        self.assertTrue(surge["leader"])
        self.assertEqual(surge["location"], "kanto-vermilion-gym")
        self.assertEqual(
            [(p["species"], p["level"]) for p in surge["variants"][0]["team"]],
            [("VOLTORB", 21), ("PIKACHU", 18), ("RAICHU", 24)]
        )

    def test_reachability_follows_bidirectional_corridor(self):
        graph = {300: {301}, 301: {300, 302}, 302: {301}}
        self.assertEqual(reachable(graph, 300), {300, 301, 302})

    def test_isolated_map_is_not_silently_accepted(self):
        graph = {300: {301}, 301: {300}, 302: set()}
        self.assertEqual(reachable(graph, 300), {300, 301})
        self.assertNotEqual(reachable(graph, 300), set(graph))

    def test_one_way_transfer_does_not_create_a_fictitious_return_route(self):
        graph = {300: {301}, 301: {302}, 302: set()}
        self.assertEqual(reachable(graph, 300), {300, 301, 302})
        # The reverse direction is not automatically available:
        self.assertEqual(reachable(graph, 302), {302})

    def test_explicit_return_transfer_restores_bidirectional_access(self):
        graph = {300: {301}, 301: {302}, 302: {300}}
        self.assertEqual(reachable(graph, 302), {300, 301, 302})

    def test_pilot_signature_detects_obsolete_build_without_deleting_it(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            marker = folder / PILOT_META
            self.assertFalse(pilot_is_current(folder))
            marker.write_text(json.dumps({"build_signature": build_signature()}), encoding="utf-8")
            self.assertTrue(pilot_is_current(folder))
            marker.write_text(json.dumps({"build_signature": "old-release"}), encoding="utf-8")
            self.assertFalse(pilot_is_current(folder))


if __name__ == "__main__":
    unittest.main()
