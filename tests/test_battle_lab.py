import importlib.util
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import zlib
from unittest.mock import patch,Mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'/'official_rules'))
from prepare_restore import Marshal, RubyString, dump
spec=importlib.util.spec_from_file_location('blue_lab_launch',ROOT/'scripts'/'battle_lab'/'launch.py')
lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)

class BattleLabTests(unittest.TestCase):
    def test_launcher_rejects_silent_early_exit_even_with_old_success_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            (game/'Data/blue-battle-lab.log').write_text('old MENU_READY\n')
            process=Mock();process.poll.return_value=0
            with patch.object(lab,'install',return_value=game),patch.object(lab.subprocess,'Popen',return_value=process):
                with self.assertRaisesRegex(RuntimeError,'nao confirmou'):
                    lab.launch(root,game)

    def test_launcher_waits_for_a_new_menu_ready_marker_and_detaches_windows_gui(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            process=Mock();process.poll.return_value=None
            def start(*args,**kwargs):
                self.assertEqual(kwargs['cwd'],game)
                self.assertEqual(kwargs['stdin'],lab.subprocess.DEVNULL)
                self.assertIsNotNone(kwargs['stdout'])
                if lab.os.name=='nt':self.assertTrue(kwargs['creationflags'] & lab.subprocess.DETACHED_PROCESS)
                (game/'Data/blue-battle-lab.log').write_text('new MENU_READY\n')
                return process
            with patch.object(lab,'install',return_value=game),patch.object(lab.subprocess,'Popen',side_effect=start):
                self.assertEqual(lab.launch(root,game),0)

    def fixture(self,root,main='PluginManager.runPlugins\nCompiler.main'):
        source=root/'scripts'/'battle_lab';source.mkdir(parents=True)
        for name in lab.PLUGIN_FILES:shutil.copy2(ROOT/'scripts'/'battle_lab'/name,source/name)
        game=root/'game';(game/'Data').mkdir(parents=True)
        (game/'Game.exe').write_bytes(b'fixture only')
        scripts=[[1,RubyString(b'Other'),RubyString(zlib.compress(b'untouched'))],[2,RubyString(b'Main'),RubyString(zlib.compress(main.encode()))]]
        (game/'Data'/'Scripts.rxdata').write_bytes(b'\x04\x08'+dump(scripts))
        return game

    def test_bootstrap_is_bounded_idempotent_and_backed_up(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root);original=(game/'Data'/'Scripts.rxdata').read_bytes()
            lab.install(root,game)
            first=(game/'Data'/'Scripts.rxdata').read_bytes();lab.install(root,game)
            self.assertEqual(first,(game/'Data'/'Scripts.rxdata').read_bytes())
            decoded=Marshal(first).read();self.assertEqual(zlib.decompress(decoded[0][2]),b'untouched')
            self.assertEqual(zlib.decompress(decoded[1][2]).count(b'BLUE_BATTLE_LAB_BOOTSTRAP'),1)
            backups=list((root/'.blue-backups').rglob('Scripts.rxdata'));self.assertEqual(len(backups),1);self.assertEqual(backups[0].read_bytes(),original)

    def test_unknown_main_is_not_rewritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root,'unexpected bootstrap');before=(game/'Data'/'Scripts.rxdata').read_bytes()
            with self.assertRaises(RuntimeError):lab.install(root,game)
            self.assertEqual(before,(game/'Data'/'Scripts.rxdata').read_bytes())

    def test_request_modes_are_explicit(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=Path(tmp);(game/'Data').mkdir();lab.prepare_request(game)
            self.assertEqual((game/'Data'/'blue-battle-lab-request.txt').read_text(),'play')
            lab.prepare_request(game,True);self.assertEqual((game/'Data'/'blue-battle-lab-request.txt').read_text(),'smoke')

    def test_upgrade_installs_team_and_mouse_modules_and_backs_up_old_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            plugin=game/'Plugins'/'ZZZZ Blue Battle Lab';plugin.mkdir(parents=True)
            (plugin/'BlueBattleLab.rb').write_bytes(b'previous plugin')
            lab.install(root,game)
            for name in lab.PLUGIN_FILES:
                self.assertEqual((plugin/name).read_bytes(),(root/'scripts/battle_lab'/name).read_bytes())
            backups=list((root/'.blue-backups').rglob('BlueBattleLab.rb'))
            self.assertEqual(len(backups),1)
            self.assertEqual(backups[0].read_bytes(),b'previous plugin')

if __name__=='__main__':unittest.main()
