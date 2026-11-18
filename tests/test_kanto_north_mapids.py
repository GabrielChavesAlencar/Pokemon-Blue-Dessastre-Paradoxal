"""No Kanto save may change its existing MapID when the north bridge ships."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "regions"))
from audit import stable_source_order

class KantoNorthMapIDContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ROOT / "data/regions/kanto-source.json").read_text("utf8"))
        cls.wanted = set(map(int, cls.manifest["maps"]))
        cls.old = cls.wanted - {53,54,55}

    def test_stable_142_source_slots_are_identical(self):
        before = stable_source_order(self.old)
        after = stable_source_order(self.wanted)
        self.assertEqual(len(before),142)
        self.assertEqual(after[:142],before)
        self.assertEqual(after[142:],[53,54,55])
        self.assertEqual(len(after),len(set(after)))

    def test_three_new_regions_are_not_previews(self):
        self.assertEqual([self.manifest["maps"][str(i)] for i in (53,54,55)],
                         ["ROUTE_24","ROUTE_25","BILLS_COTTAGE"])
        self.assertTrue({53,54,55}.isdisjoint(self.manifest["preview_only"]))

    def test_missing_map_id_cannot_reassign_old_source_slots(self):
        for missing in (53,54,55):
            reduced = self.wanted - {missing}
            self.assertEqual(stable_source_order(reduced)[:142],stable_source_order(self.old))

if __name__ == "__main__":
    unittest.main()
