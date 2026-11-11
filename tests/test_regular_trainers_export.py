import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
path=ROOT/'scripts/export_story_teams.py'
spec=importlib.util.spec_from_file_location('export_story_teams',path)
export=importlib.util.module_from_spec(spec)
spec.loader.exec_module(export)

class RegularTrainerExportTests(unittest.TestCase):
    def test_local_pbs_updates_known_and_new_trainers_without_tampering_with_bosses(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)
            roster=json.loads((ROOT/'site/public/data/story-trainers.json').read_text('utf8'))
            regular=json.loads((ROOT/'site/public/data/regular-trainers.json').read_text('utf8'))
            (output/'regular-trainers.json').write_text(json.dumps(regular),encoding='utf8')
            raw=('[SINNOHIAN_DPP_ARTIST,Pyotr]\n'
                 'Pokemon = PIKACHU,20\n\tMoves = THUNDERBOLT\n'
                 '[HOENNIAN_ORAS_AROMALADY,Marigold (2v2 Full Power)]\n'
                 'Pokemon = MEWTWO,50\n'
                 '[TEST_CLASS_NEW,New Tester]\n'
                 'Pokemon = EEVEE,12\n\tMoves = QUICKATTACK\n')
            changed=export.sync_regular_trainers(raw,output,roster)
            result=json.loads((output/'regular-trainers.json').read_text('utf8'))
            self.assertEqual(changed,2)
            pyotr=next(t for t in result['trainers'] if t['name']=='Pyotr')
            self.assertEqual(pyotr['team'][0]['species'],'PIKACHU')
            self.assertEqual(pyotr['teamOrigin'],'blue-pbs')
            self.assertEqual(pyotr['team'][0]['moves'],['THUNDERBOLT'])
            self.assertEqual(next(t for t in result['trainers'] if t['name']=='New Tester')['team'][0]['species'],'EEVEE')
            self.assertFalse(any(t['name'].startswith('Marigold') for t in result['trainers']))
            self.assertEqual(export.sync_regular_trainers(raw,output,roster),0)
            self.assertEqual(result['sourceCRC'],export.zlib.crc32(raw.encode()))
    def test_snapshot_is_unchanged_when_no_local_game_file_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)
            self.assertEqual(export.sync_regular_trainers('',target,{}),0)

if __name__=='__main__':
    unittest.main()
