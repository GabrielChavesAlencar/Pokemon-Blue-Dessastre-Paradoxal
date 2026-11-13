import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts/regions'))
sys.path.insert(0, str(ROOT/'tests'))
from test_johto_route29_cherrygrove import room
from johto_route31_violet import derive_violet

class VioletRoute31OfflineTests(unittest.TestCase):
    def test_violet_real_signature_offset_and_status(self):
        r=derive_violet(room(height=45,at=31), room(side='East',height=45,at=37),627,602)
        self.assertEqual(r['pbs_line'],'602,East,6,627,West,0')
        self.assertEqual(r['route31_west_road_start_y'],31)
        self.assertEqual(r['violet_east_road_start_y'],37)
        self.assertFalse(r['tested_in_game'])
        self.assertFalse(r['gameplay_playable'])

    def test_blocks_duplicate_violet_connection(self):
        with self.assertRaisesRegex(ValueError, 'ja possui conexao'):
            derive_violet(room(height=45,at=31),room(side='East',height=45,at=37),627,602,
                          '602,East,6,627,West,0\n')

    def test_blocks_unwalkable_road(self):
        with self.assertRaisesRegex(ValueError, 'Passagens'):
            derive_violet(room(height=45,at=31,blocked=True),room(side='East',height=45,at=37),627,602)

if __name__=='__main__': unittest.main()
