"""Regression tests for lossless FRLG encounter slots (Essentials v21.1 PBS)."""
import sys
import tempfile
import unittest
from pathlib import Path

REGIONS=Path(__file__).resolve().parents[1]/"scripts"/"regions"
sys.path.insert(0,str(REGIONS))
try:
    from pbs import normalize_encounters
finally:
    sys.path.remove(str(REGIONS))


def normalize(contents):
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/"encounters.txt"
        path.write_text(contents,encoding="utf-8")
        return normalize_encounters(path,{16:427,209:429}, {"SPEAROW","RATTATA","NIDORAN_M"})


class KantoEncounterSourceTests(unittest.TestCase):
    def test_essentials_level_range_3_5_is_inclusive_not_discrete(self):
        result,count=normalize(
            "[016]\nLand,21\n45,SPEAROW,3,5\n55,RATTATA,4,4\n"
            "[209]\nLandMorning,18\n100,NIDORAN_M,7,9\n")
        self.assertEqual(count,2)
        self.assertIn("[427]",result)
        self.assertIn("45,SPEAROW,3,5",result)
        self.assertIn("55,RATTATA,4,4",result)
        self.assertIn("[429]",result)
        self.assertIn("100,NIDORAN_M,7,9",result)

    def test_single_level_keeps_min_equal_max(self):
        result,count=normalize("[016]\nLand,21\n100,SPEAROW,3\n")
        self.assertEqual(count,1)
        self.assertIn("100,SPEAROW,3,3",result)

    def test_map_versions_do_not_overwrite_base(self):
        result,count=normalize(
            "[016]\nLand\n100,SPEAROW,3,5\n"
            "[016,1]\nLand\n100,RATTATA,6,10\n")
        self.assertEqual(count,2)
        self.assertIn("[427,1]",result)
        self.assertIn("100,RATTATA,6,10",result)

    def test_preview_and_unsupported_map_cannot_be_imported(self):
        result,count=normalize("[016]\nLand\n100,SPEAROW,3,5\n"
                               "[100]\nLand\n100,RATTATA,3,5\n")
        self.assertEqual(count,1)
        self.assertNotIn("[100]",result)

    def test_invalid_min_greater_than_max_rejected(self):
        with self.assertRaisesRegex(ValueError,"Invalid encounter weight or level"):
            normalize("[016]\nLand\n100,SPEAROW,6,3\n")

    def test_invalid_level_0_and_over_100_rejected(self):
        for pair in ["0,3","1,101"]:
            with self.subTest(pair=pair):
                with self.assertRaises(ValueError):
                    normalize("[016]\nLand\n100,SPEAROW,"+pair+"\n")

    def test_extra_levels_rejected_instead_of_discarded(self):
        with self.assertRaisesRegex(ValueError,"Invalid encounter"):
            normalize("[016]\nLand\n100,SPEAROW,3,5,7\n")

    def test_unknown_species_rejected_instead_of_replaced(self):
        with self.assertRaisesRegex(ValueError,"Invalid encounter"):
            normalize("[016]\nLand\n100,NOT_A_POKEMON,3,5\n")

    def test_weight_total_exactly_100(self):
        with self.assertRaisesRegex(ValueError,"Encounter weights must total 100"):
            normalize("[016]\nLand\n45,SPEAROW,3,5\n50,RATTATA,4,6\n")

    def test_duplicate_method_rejected(self):
        with self.assertRaisesRegex(ValueError,"Unsupported encounter method"):
            normalize("[016]\nLand\n100,SPEAROW,3,5\nLand\n100,RATTATA,4,6\n")


if __name__=="__main__":
    unittest.main()
