import importlib.util,json,shutil,sys,tempfile,unittest,zlib
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/official_rules'))
from prepare_restore import Marshal,RubyString,dump
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
setup=module('blue_setup','scripts/install_game.py');campaign=module('blue_launch','scripts/launch_game.py')
class InstallationTests(unittest.TestCase):
    def fixture(self,root):
        source=root/'scripts/battle_lab';source.mkdir(parents=True)
        for name in ['launch.py','BlueBattleLab.rb','Interface.rb','Teams.rb','HubData.rb','HubUI.rb','HubValidation.rb','Validation.rb','meta.txt']:shutil.copy2(ROOT/'scripts/battle_lab'/name,source/name)
        game=root/'game';(game/'Data').mkdir(parents=True);(game/'PBS').mkdir()
        (game/'Game.exe').write_bytes(b'synthetic exe');(game/'PBS/pokemon.txt').write_text('[PIKACHU]')
        rows=[[1,RubyString(b'Other'),RubyString(zlib.compress(b'original script'))],[2,RubyString(b'Main'),RubyString(zlib.compress(b'PluginManager.runPlugins\nCompiler.main'))]]
        (game/'Data/Scripts.rxdata').write_bytes(b'\x04\x08'+dump(rows))
        return game
    def test_campaign_launch_from_zip_has_no_root_git_dependency_or_lab_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            (game/'Data/blue-battle-lab-request.txt').write_text('play')
            result=campaign.prepare(root,game)
            self.assertTrue(result['compileRequested']);self.assertFalse((game/'Data/blue-battle-lab-request.txt').exists())
            self.assertTrue((game/'Data/blue-compile-request.txt').is_file())
            first=(game/'Data/Scripts.rxdata').read_bytes();campaign.prepare(root,game)
            self.assertEqual(first,(game/'Data/Scripts.rxdata').read_bytes())
            rows=Marshal(first).read();self.assertEqual(zlib.decompress(rows[0][2]),b'original script')
            code=zlib.decompress(rows[1][2]).decode();self.assertEqual(code.count('# BLUE_CAMPAIGN_COMPILE_REQUEST'),1)
            self.assertIn("File.delete('Data/blue-compile-request.txt')",code)
            self.assertFalse((root/'.git').exists())
    def test_resume_skips_completed_official_restore_and_refreshes_own_plugins(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            with patch.object(setup,'run') as run:
                setup.install(root,game);self.assertEqual(run.call_count,4)
                self.assertIn('official_rules/restore.py',str(run.call_args_list[0]))
                run.reset_mock();setup.install(root,game)
                self.assertEqual(run.call_count,3);self.assertNotIn('official_rules/restore.py',str(run.call_args_list))
    def test_unknown_partial_game_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=root/'game';game.mkdir();save=game/'Game.rxdata';save.write_bytes(b'private save')
            with patch.object(setup.shutil,'which',return_value='git'),patch.object(setup,'run') as run:
                with self.assertRaisesRegex(RuntimeError,'parcial'):setup.ensure_base(root,game)
                run.assert_not_called();self.assertEqual(save.read_bytes(),b'private save')
    def test_base_fetch_uses_the_pinned_commit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=root/'game';calls=[]
            def simulate(command,*args):
                calls.append(list(map(str,command)))
                if 'checkout' in command:(game/'Game.exe').write_bytes(b'synthetic download')
            with patch.object(setup.shutil,'which',return_value='git'),patch.object(setup,'run',side_effect=simulate):setup.ensure_base(root,game)
            self.assertTrue(any('fetch' in c and setup.BASE_COMMIT in c for c in calls))
            self.assertTrue(any('checkout' in c and setup.BASE_COMMIT in c for c in calls))
if __name__=='__main__':unittest.main()
