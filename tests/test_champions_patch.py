import importlib.util,sys,tempfile,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/official_rules'))
from prepare_restore import Marshal,RubyString,dump
spec=importlib.util.spec_from_file_location('champions_patch',ROOT/'scripts/battle_polish/champions.py')
patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)
class ChampionsPatchTests(unittest.TestCase):
    def fixture(self,root,source):
        path=root/'Data/Scripts.rxdata';path.parent.mkdir()
        rows=[[1,RubyString(b'Main'),RubyString(zlib.compress(b'unchanged bootstrap'))],
              [2,RubyString(b'Battler_UseMoveSuccessChecks'),RubyString(zlib.compress(source.encode()))]]
        path.write_bytes(b'\x04\x08'+dump(rows));return path
    def test_only_paralysis_roll_changes_and_reapplication_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=Path(tmp);source='if '+patch.OLD+'\n  stop\nend\n# confusion and sleep are unrelated\n'
            path=self.fixture(game,source);before=path.read_bytes();plans=patch.plan(ROOT,game)
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(list(plans),[path]);rows=Marshal(plans[path]).read()
            self.assertEqual(zlib.decompress(rows[0][2]),b'unchanged bootstrap')
            self.assertEqual(zlib.decompress(rows[1][2]).decode(),source.replace(patch.OLD,patch.NEW))
            path.write_bytes(plans[path]);self.assertEqual(patch.plan(ROOT,game),{})
    def test_unrecognized_and_ambiguous_conditions_refuse_to_write(self):
        for source in ['changed engine',patch.OLD+'\n'+patch.OLD,patch.OLD+'\n'+patch.NEW]:
            with self.subTest(source=source),tempfile.TemporaryDirectory() as tmp:
                game=Path(tmp);path=self.fixture(game,source);before=path.read_bytes()
                with self.assertRaises(ValueError):patch.plan(ROOT,game)
                self.assertEqual(path.read_bytes(),before)
if __name__=='__main__':unittest.main()
