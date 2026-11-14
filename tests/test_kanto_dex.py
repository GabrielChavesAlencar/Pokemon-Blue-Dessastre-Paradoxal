"""Static regression contracts for independent National Dex and KantoDex."""
import json
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class KantoDexContracts(unittest.TestCase):
    def test_exact_first_generation_numbering(self):
        source=json.loads((ROOT/"data/national-species.json").read_text("utf8"))
        desired={name:number for name,number in source.items()
                 if isinstance(number,int) and 1<=number<=151}
        self.assertEqual(len(desired),151)
        rb=(ROOT/"scripts/battle_polish/KantoDex.rb").read_text("utf8")
        found={key:int(value) for key,value in re.findall(
            r":([A-Z0-9_]+)\s*=>\s*(\d+)",rb)}
        self.assertEqual(found,desired)
        self.assertEqual(found["BULBASAUR"],1)
        self.assertEqual(found["MEW"],151)

    def test_national_dex_remains_independent(self):
        code=(ROOT/"scripts/battle_polish/DexControls.rb").read_text("utf8")
        self.assertIn("blue_toggle_kanto_dex",code)
        self.assertIn("BlueKantoDex.number(row[:species])",code)
        self.assertIn("National Dex [K]",code)
        self.assertIn("KantoDex [K]",code)
        self.assertIn("@searchResults=false",code)
        self.assertIn("pbRefreshDexList(0)",code)
        self.assertNotIn("set_seen(",code)
        self.assertNotIn("set_owned(",code)

    def test_dex_loaded_both_in_main_and_isolated_pilot(self):
        installer=(ROOT/"scripts/battle_polish/install.py").read_text("utf8")
        pilot=(ROOT/"scripts/regions/pilot.py").read_text("utf8")
        self.assertIn("'KantoDex.rb','DexControls.rb'",installer)
        self.assertIn('"KantoDex.rb", "DexControls.rb"',pilot)
        self.assertIn('"scripts/battle_polish/KantoDex.rb"',pilot)


if __name__=="__main__":
    unittest.main()
