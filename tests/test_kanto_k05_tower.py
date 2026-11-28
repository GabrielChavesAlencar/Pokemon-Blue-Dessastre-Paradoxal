import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts/regions"))
from build_k05_tower import FUJI_RETURN, GHOST_CONTACTS, SLOTS, STAIRS, SUMMIT_GATE, compile_stair


class K05TowerStageTests(unittest.TestCase):
    def test_native_stair_destinations_are_unchanged_except_deferred_summit_and_fuji(self):
        self.assertEqual(list(SLOTS),list(range(100,107)))
        self.assertEqual(list(SLOTS.values()),list(range(615,622)))
        self.assertNotIn(FUJI_RETURN, STAIRS)
        self.assertEqual(GHOST_CONTACTS,{6:(9,15),10:(10,16)})
        self.assertEqual(STAIRS[SUMMIT_GATE],((8,16),106,(9,16),6))
        self.assertEqual(compile_stair(STAIRS[SUMMIT_GATE],SLOTS,True)[0].attrs["@code"],355)
        floor_5_to_6=compile_stair(STAIRS[(104,10)],SLOTS)[0].attrs
        self.assertEqual(floor_5_to_6["@parameters"],[0,620,16,10,4,0])
        with self.assertRaisesRegex(ValueError,"Only the original summit"):
            compile_stair(STAIRS[(104,10)],SLOTS,True)
