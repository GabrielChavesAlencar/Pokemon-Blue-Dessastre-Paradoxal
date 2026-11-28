from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts/regions"))
from build_k05_city import CITY_DOORS, CITY_SLOTS, mart_stock
from audit_k05_lavender import CITY


class K05CityTests(unittest.TestCase):
    def test_city_scope_has_reciprocal_doors_not_tower_or_rewards(self):
        self.assertEqual(set(CITY_SLOTS),set(CITY))
        self.assertEqual(list(CITY_SLOTS.values()),list(range(609,615)))
        self.assertEqual(len(CITY_DOORS),10)
        for sid in CITY[1:]:
            self.assertIn((93,sid),{(area,row[1]) for (area,eid),row in CITY_DOORS.items()})
            self.assertIn((sid,93),{(area,row[1]) for (area,eid),row in CITY_DOORS.items()})
        self.assertNotIn((93,8),CITY_DOORS)
        self.assertNotIn((98,3),CITY_DOORS)

    def test_mart_compiles_only_literal_known_catalog_not_raw_script(self):
        items={"GREATBALL","POTION"}
        self.assertEqual(mart_stock(["pbPokemonMart([:GREATBALL,", "  :POTION,])"],items),
                         ["GREATBALL","POTION"])
        for bad, error in (("pbPokemonMart(list)","literal catalog"),
                           ("pbPokemonMart([:POTION,:POTION])","native item"),
                           ("pbPokemonMart([:FAKE])","native item"),
                           ("pbPokemonMart([:POTION]); pbPokemonMart([:POTION])","literal catalog")):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(ValueError,error):
                    mart_stock([bad],items)
