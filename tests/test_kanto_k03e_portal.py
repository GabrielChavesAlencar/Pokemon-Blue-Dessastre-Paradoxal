"""K03-E portal preview must be additive, never release or replace existing facts."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/regions"))
from export_kanto import k03e_portal_delta, slug
from k03e_contract import MAPS, TRAINERS


class K03EPortalTests(unittest.TestCase):
    def fixture(self):
        before = {"locations": [{"id": "kanto-pallet-town"}], "trainers": [{"id": "kanto-brock"}]}
        roster = [slug(f"route-11-{name}") for _, name in TRAINERS.values()]
        after = copy.deepcopy(before)
        after["trainers"] += [{"id": key} for key in roster]
        for source, key in MAPS.items():
            after["locations"].append({
                "id": slug(key), "status": "experimental",
                "methods": list(range(6 if source == 79 else 2 if source == 82 else 0)),
                "trainers": roster if source == 79 else [],
            })
        return before, after

    def test_only_four_new_maps_and_ten_trainers(self):
        before, after = self.fixture()
        delta = k03e_portal_delta(before, after)
        self.assertEqual(delta["status"], "CANDIDATE_NOT_PUBLISHED")
        self.assertEqual(len(delta["locations"]), 4)
        self.assertEqual(len(delta["trainers"]), 10)

    def test_changed_historical_map_and_incomplete_encounters_fail(self):
        before, after = self.fixture()
        after["locations"][0]["name"] = "changed"
        with self.assertRaisesRegex(ValueError, "historic locations"):
            k03e_portal_delta(before, after)
        before, after = self.fixture()
        after["locations"][-1]["methods"].pop()
        with self.assertRaisesRegex(ValueError, "incomplete"):
            k03e_portal_delta(before, after)


if __name__ == "__main__":
    unittest.main()
