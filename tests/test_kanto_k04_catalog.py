"""Promoted/legacy Android catalogs must fail closed on partial append."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.regions.k03e_contract import MAPS as K03E
from scripts.regions.k04_corridor import MAPS as K04, publication_catalog, published_destinations


class PublicationCatalogTests(unittest.TestCase):
    def test_full_legacy_and_candidate_appends_and_partial_refusal(self):
        historical = {str(i): f"FIXTURE_{i}" for i in range(300,456)}
        former = {**historical, **{str(k):v for k,v in K03E.items()}}
        current = {**former, **{str(k):v for k,v in K04.items()}}
        for data,count in ((historical,156),(former,160),(current,165)):
            self.assertEqual(publication_catalog(data), count)
        for data in ({**former,"86":K04[86]}, {**current,"91":"WRONG"}, {**current,"79":"WRONG"}):
            with self.assertRaisesRegex(ValueError,"Unknown Kanto"):
                publication_catalog(data)
        self.assertEqual(published_destinations(), {"86":604,"87":605,"88":606,"90":607,"91":608})


    def test_install_namespace_ignores_high_foreign_ids_but_refuses_collisions(self):
        from scripts.regions.audit import allocate_kanto_ids

        old = {5:300, 7:302}
        wanted = set(old) | K04.keys()
        forward = allocate_kanto_ids(wanted, {1,300,302,898}, old)
        self.assertEqual(forward, {**old, **{int(k): v for k,v in published_destinations().items()}})
        with self.assertRaisesRegex(ValueError, "reserved map ID 604 is already occupied"):
            allocate_kanto_ids(wanted, {1,300,302,604,898}, old)
        with self.assertRaisesRegex(ValueError, "not at its reserved map ID 604"):
            allocate_kanto_ids(wanted, {1,300,302,898}, {**old, 86:898})
        self.assertEqual(allocate_kanto_ids(wanted, set(forward.values()) | {898}, forward), forward)
